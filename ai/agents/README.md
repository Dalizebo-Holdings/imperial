# Governed AI Agents

## Purpose

Agents execute bounded, authorized workflows using platform capabilities.

## Execution Model

Goal
→ Context
→ Authorization
→ Pillars OS
→ Plan
→ Tool Selection
→ Kernel Authorization
→ Action
→ Observation
→ Audit
→ Completion

## Agent Requirements

Every agent must define:

- Agent ID
- Owner
- Purpose
- Allowed tools
- Allowed resources
- Tenant scope
- Maximum runtime
- Maximum actions
- Cost budget
- Approval requirements
- Failure behavior
- Audit policy

## Rules

Agents may not:

- Bypass authorization
- Bypass tenant boundaries
- Execute unbounded loops
- Hide material actions
- Modify critical state without required approval
