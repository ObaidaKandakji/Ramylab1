# DATABASE_CHOICE.md

## Your Choice
Azure Cosmos DB for NoSQL (serverless)

## Justification
Cosmos DB stores JSON documents natively and fits serverless workloads well because it can run in a consumption-based serverless mode billed by request usage plus storage. It also supports querying and sorting historical results using SQL-like queries, which makes building a history endpoint straightforward. Python integration is mature via the `azure-cosmos` SDK.

## Alternatives Considered
- Azure Table Storage: cheaper and simple, but more limited query patterns and not a true document store.
- Azure SQL Database: powerful relational querying, but adds schema + operational complexity for simple JSON document history.
- Azure Blob Storage: good for storing files, but poor fit for querying a history feed.

## Cost Considerations
Serverless Cosmos DB charges for the request units consumed by operations and for stored data size. If available on the subscription, Cosmos DB free tier can reduce cost further for small student workloads.
