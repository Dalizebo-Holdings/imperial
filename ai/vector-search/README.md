# Vector Search

## Initial Technology

PostgreSQL + pgvector where practical.

## Responsibilities

- Embeddings
- Vector indexing
- Similarity search
- Metadata filtering
- Tenant-aware retrieval

## Requirements

Every vector record must include:

- id
- organization_id
- source_type
- source_id
- embedding_model
- embedding_version
- metadata
- created_at

## Rule

Vector search must enforce the same authorization rules as the source data.
