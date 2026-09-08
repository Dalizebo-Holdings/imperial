# API Gateway

## Responsibilities

- API routing
- Authentication
- Authorization
- Request validation
- Rate limiting
- Payload limits
- Correlation IDs
- Timeouts
- Structured errors

## API Version

/api/v1

## Error Format

{
  "code": "ERROR_CODE",
  "message": "Safe error message",
  "request_id": "request_identifier",
  "details": {}
}
