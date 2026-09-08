# Audit System

## Purpose

Audit records provide durable evidence of sensitive or material platform actions.

## Required Fields

- audit_id
- organization_id
- actor_type
- actor_id
- action
- resource_type
- resource_id
- timestamp
- correlation_id
- metadata

## Rules

- Application logs are not a replacement for audit records.
- Sensitive actions must generate an audit record.
- Audit records must be tamper-resistant.
