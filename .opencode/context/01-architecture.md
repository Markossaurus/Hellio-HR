# System Architecture

The system consists of:

- FastAPI backend
- PostgreSQL as the system of record
- Vector store for semantic retrieval
- Agent layer (Strands + MCP)
- Managed runtime on AWS AgentCore

High-level flow:
1. CV ingestion (PDF/DOC/Excel)
2. Structured extraction + enrichment
3. Storage in relational + vector stores
4. Query via deterministic SQL or semantic search
5. Agent-driven workflows for HR tasks
