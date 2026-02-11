# CST8917 Lab 1 — Azure Functions Text Analyzer (Python)

## What this is
Azure Functions app with 2 endpoints:
- `GET/POST /api/TextAnalyzer` — analyzes text and stores results in Cosmos DB
- `GET /api/GetAnalysisHistory?limit=10` — returns recent stored results

## Requirements
- Python 3.12
- Azure Functions Core Tools v4
- Azurite (VS Code extension or `npm i -g azurite`)

## Setup
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Create local.settings.json (gitignored):

```

{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "COSMOS_ENDPOINT": "https://<account>.documents.azure.com:443/",
    "COSMOS_KEY": "<primary-key>",
    "COSMOS_DATABASE": "<db-name>",
    "COSMOS_CONTAINER": "<container-name>"
  }
}

```
Start Azurite, then:

```
func host start
```
