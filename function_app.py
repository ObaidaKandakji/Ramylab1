import azure.functions as func
import logging
import json
import re
import os
import uuid
from datetime import datetime

from azure.cosmos import CosmosClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ----------------------------
# Cosmos DB helper (reuse client across executions)
# ----------------------------
_cosmos_container = None

def get_container():
    global _cosmos_container
    if _cosmos_container is not None:
        return _cosmos_container

    endpoint = os.environ.get("COSMOS_ENDPOINT")
    key = os.environ.get("COSMOS_KEY")
    db_name = os.environ.get("COSMOS_DATABASE")
    container_name = os.environ.get("COSMOS_CONTAINER")

    if not all([endpoint, key, db_name, container_name]):
        raise ValueError("Missing one or more Cosmos settings: COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE, COSMOS_CONTAINER")

    client = CosmosClient(endpoint, credential=key)
    db = client.get_database_client(db_name)
    _cosmos_container = db.get_container_client(container_name)
    return _cosmos_container


@app.route(route="TextAnalyzer", methods=["GET", "POST"])
def TextAnalyzer(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Text Analyzer API was called!")

    # 1) Get input text (querystring or JSON body)
    text = req.params.get("text")
    if not text:
        try:
            req_body = req.get_json()
            text = req_body.get("text")
        except ValueError:
            pass

    if not text:
        instructions = {
            "error": "No text provided",
            "howToUse": {
                "option1": "Add ?text=YourText to the URL",
                "option2": "Send a POST request with JSON body: {\"text\": \"Your text here\"}"
            }
        }
        return func.HttpResponse(json.dumps(instructions, indent=2), mimetype="application/json", status_code=400)

    # 2) Analyze
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    char_count_no_spaces = len(text.replace(" ", ""))
    sentence_count = len(re.findall(r"[.!?]+", text)) or 1
    paragraph_count = len([p for p in text.split("\n\n") if p.strip()])
    reading_time_minutes = round(word_count / 200, 1)
    avg_word_length = round(char_count_no_spaces / word_count, 1) if word_count > 0 else 0
    longest_word = max(words, key=len) if words else ""

    analyzed_at = datetime.utcnow().isoformat()

    response_data = {
        "analysis": {
            "wordCount": word_count,
            "characterCount": char_count,
            "characterCountNoSpaces": char_count_no_spaces,
            "sentenceCount": sentence_count,
            "paragraphCount": paragraph_count,
            "averageWordLength": avg_word_length,
            "longestWord": longest_word,
            "readingTimeMinutes": reading_time_minutes
        },
        "metadata": {
            "analyzedAt": analyzed_at,
            "textPreview": (text[:100] + "...") if len(text) > 100 else text
        }
    }

    # 3) Persist to Cosmos DB
    try:
        container = get_container()
        doc_id = str(uuid.uuid4())

        document = {
            "id": doc_id,
            "pk": "analysis",          # must match partition key path /pk in your container
            "analysis": response_data["analysis"],
            "metadata": response_data["metadata"],
            "originalText": text
        }

        container.upsert_item(document)
        response_data["id"] = doc_id

    except Exception as ex:
        logging.exception("Failed to store analysis in Cosmos DB.")
        return func.HttpResponse(
            json.dumps({"error": "Failed to store analysis", "details": str(ex)}, indent=2),
            mimetype="application/json",
            status_code=500
        )

    return func.HttpResponse(json.dumps(response_data, indent=2), mimetype="application/json", status_code=200)


@app.route(route="GetAnalysisHistory", methods=["GET"])
def GetAnalysisHistory(req: func.HttpRequest) -> func.HttpResponse:
    # Optional limit param
    limit_raw = req.params.get("limit", "10")
    try:
        limit = int(limit_raw)
        limit = max(1, min(limit, 100))  # safety cap
    except ValueError:
        limit = 10

    try:
        container = get_container()

        query = "SELECT c.id, c.analysis, c.metadata FROM c WHERE c.pk = @pk ORDER BY c.metadata.analyzedAt DESC"
        params = [{"name": "@pk", "value": "analysis"}]

        items_iter = container.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=False
        )
        items = []
        for item in items_iter:
            items.append(item)
            if len(items) >= limit:
                break

        payload = {"count": len(items), "results": items}
        return func.HttpResponse(json.dumps(payload, indent=2), mimetype="application/json", status_code=200)

    except Exception as ex:
        logging.exception("Failed to query history from Cosmos DB.")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve history", "details": str(ex)}, indent=2),
            mimetype="application/json",
            status_code=500
        )
