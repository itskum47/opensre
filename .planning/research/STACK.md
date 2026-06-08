# Research: Stack Additions

This document details the stack additions required to implement the target features for milestone v1.1 (Slack/PagerDuty notifications, Neo4j graph storage, historical memory RCA, and a dashboard UI).

## Recommended Additions

### Slack Notifications
* **Package**: `slack-sdk`
* **Version**: `3.42.0+`
* **Purpose**: Send real-time investigation alerts, timeline updates, and interactive block kit messages for incident routing.
* **Integration**: Python Slack WebClient configured with `SLACK_BOT_TOKEN`.

### PagerDuty Status Sync
* **Package**: `pagerduty`
* **Version**: `1.0.0+` (modern, thread-safe PagerDuty SDK replacing deprecated `pdpyras`)
* **Purpose**: Automatically trigger, acknowledge, and synchronize status transitions of PagerDuty incidents from OpenSRE pipeline.
* **Integration**: API Client configured with `PAGERDUTY_API_KEY`.

### Neo4j Persistent Graph Store
* **Package**: `neo4j`
* **Version**: `5.x+` (uses official driver)
* **Purpose**: Persist dependency graphs, trace root causes, and run graph algorithms (like PageRank or Shortest Path) across investigations.
* **Integration**: `Neo4jProvider` implementing `GraphProvider` interface.

### Historical Memory RCA
* **Method**: In-Memory / SQLite BLOB Vector Storage + Cosine Similarity
* **Package**: Pure Python standard library (`math`) + standard SQLite BLOB storage (optionally `numpy` if already available).
* **Rationale**: Keep dependencies minimal. An in-memory or SQLite BLOB storage with a pure Python cosine similarity utility is lightweight, robust, fast enough for thousands of historical incidents, and does not require complex vector database deployment (like Pinecone/ChromaDB).

### Dashboard UI
* **Stack**: Vite + React + TypeScript + Vanilla CSS
* **Purpose**: Web-based dashboard for starting investigations, viewing real-time pipeline status, interactive timelines, and dependency graph visualization.
* **Integration**: Communicates with the FastAPI backend over REST APIs and WebSockets.

---

## What NOT to Add

* **`slackclient`**: Deprecated; replaced by `slack-sdk`.
* **`pdpyras`**: Deprecated; replaced by official `pagerduty` library.
* **`neo4j-driver`**: Deprecated; use `neo4j` package.
* **Heavy Vector Databases (ChromaDB / Milvus / Pinecone)**: Overkill for incident memory storage. A lightweight SQLite-based or in-memory vector storage keeps the platform self-contained and easy to deploy.
