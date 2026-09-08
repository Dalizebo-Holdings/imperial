# AI Observability

## Metrics

- Requests
- Latency
- Tokens
- Cost
- Provider
- Model
- Errors
- Retries
- Tool calls
- Retrieval quality
- User feedback

## Required Context

- request_id
- organization_id
- project_id
- model
- provider
- operation
- latency
- usage
- status

## Security

Never log:

- Provider secrets
- Authentication tokens
- Sensitive raw credentials
