# API Error Standard

## Format

{
  "code": "ERROR_CODE",
  "message": "Safe user-facing message",
  "request_id": "request_identifier",
  "details": {}
}

## Never Expose

- Stack traces
- Raw database errors
- Internal hostnames
- Secrets
- Provider credentials
- Cross-tenant resource existence
