# Backend Project Instructions

## Project Overview

Title Seeker is a personal title discovery and management platform. The backend provides REST APIs for movies, ratings, filtering, recommendations, collections, audit history, and other application features.

## Technology Stack

- Python and FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- PostgreSQL 14 (production)
- SQLite (testing)
- Poetry (dependency and environment management)
- Ruff (linting and formatting)
- mypy (static type checking)

## General Guidelines

- Inspect existing implementations before making changes. Follow established architecture, directory structure, naming conventions, and coding patterns.
- Reuse existing models, schemas, services, dependencies, and utilities before creating new ones.
- Keep implementations focused, maintainable, and appropriately typed. Avoid unnecessary abstractions and overengineering.
- Keep business logic centralized on the backend. Do not rely on client-side validation for data integrity, authorization, or business constraints.
- Preserve existing behavior and API contracts unless the task explicitly requires changes.

## API and Database

- Follow existing FastAPI routing, Pydantic schema, validation, and error-handling conventions.
- Reuse existing authentication and authorization mechanisms. Enforce access restrictions on the backend.
- Follow existing SQLAlchemy query, session, and transaction patterns.
- Avoid unnecessary database queries and N+1 query patterns.
- Consider data integrity, transaction boundaries, and compatibility with existing records when modifying database models or business logic.
- Preserve existing localization and translation conventions when handling multilingual content.

## Testing

- Follow the existing testing framework, fixtures, and conventions.
- Add focused tests for substantial features, complex business logic, critical endpoints, and changes that affect other parts of the application.
- Prioritize meaningful validation, authorization, data integrity, and important edge cases where relevant.
- Do not add redundant tests for trivial functionality or solely to increase coverage.
- Run relevant existing and newly added tests after implementation.

## Code Validation and Command Permissions

After completing code changes, ALWAYS run the following commands using Poetry:

```bash
poetry run ruff check .
poetry run mypy
poetry run ruff format .
```

- The three commands above and execution of existing project test commands are explicitly pre-approved by the project owner. Run them automatically without asking for confirmation when permitted by the IDE and execution environment.
- Fix linting, typing, formatting, and test failures caused by the implementation. Re-run the relevant checks until they pass.
- Do not modify unrelated code or suppress errors merely to make checks pass. Report unrelated pre-existing failures separately.
- Report any checks or tests that could not be executed. Never claim that validation passed without running it.
- This pre-approval does not extend to other commands that require approval and does not override IDE permission or sandbox policies.

## Frontend Integration Summary

When completing a feature, adding or modifying an API endpoint, or changing backend behavior that requires frontend integration, include a separate **Frontend Integration Context** section in the final implementation summary.

Provide a concise, self-contained handoff that a frontend developer or agent can use without access to the backend repository.

Include, where applicable:

- What changed and why, including relevant business rules and constraints.
- New or modified endpoints, HTTP methods, paths, and required permissions.
- Request parameters and payloads, response fields, and relevant error codes or error response structures.
- A concrete request/response example or an example illustrating the changed behavior.
- Required frontend changes, including validation, UI states, or error handling where relevant.
- Whether the OpenAPI contract changed and the frontend API client needs to be regenerated.

Keep this section concise and based on the actual implementation. Do not invent API fields, error codes, or behavior. Omit this section for backend-only changes that have no frontend impact.

## Restrictions

- Do not install, remove, or upgrade dependencies without explicit approval.
- Do not introduce alternative frameworks, architectural patterns, or libraries without a demonstrated need and explicit approval.
- Do not modify unrelated files or perform unrelated refactoring.
- Do not bypass validation, authorization, typing, linting, or testing to hide errors.
- Do not expose secrets, credentials, or sensitive internal data in API responses or logs.
- Do not execute destructive database operations, apply migrations to production, or modify production data without explicit approval.
- Do not change deployment or infrastructure configuration unless required by the task and explicitly authorized.
