# Deployments

## Deployment Flow

Source
→ Build
→ Validate
→ Deploy
→ Health Check
→ Activate

Failure:

Deploy
→ Failed Validation
→ Rollback

## Requirements

- Immutable deployment ID
- Environment target
- Build logs
- Release metadata
- Health checks
- Rollback
- Audit
