<div align="center">

# 🎬 <a href="https://titleseeker.com" target="_blank">Title Seeker</a>

**A powerful title discovery platform built with modern technologies**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)

</div>

---

## 🛠️ Tech Stack

<table>
<tr>
<td>

**Backend Frameworks**

- 🌶️ **<a href="https://flask.palletsprojects.com/en/stable/" target="_blank">Flask</a>** - Web application framework
- 🐍 **<strong><a href="https://fastapi.tiangolo.com/" target="_blank">FastAPI</a></strong>** - Modern API framework

**Database & ORM**

- 🐘 **<a href="https://www.postgresql.org/" target="_blank">PostgreSQL</a>** - Primary database
- 🔗 **<a href="https://www.sqlalchemy.org/" target="_blank">SQLAlchemy</a>** - ORM and database toolkit

</td>
<td>

**Development Tools**

- 📦 **<a href="https://python-poetry.org/" target="_blank">Poetry</a>** - Dependency management
- 🐳 **<a href="https://www.docker.com/" target="_blank">Docker</a>** - Containerization
- 🔍 **<a href="https://docs.pydantic.dev/latest/" target="_blank">Pydantic</a>** - Data validation
- 🧹 **<a href="https://docs.astral.sh/ruff/" target="_blank">Ruff</a>** - Fast Python linter
- 🔧 **<a href="https://mypy-lang.org/" target="_blank">Mypy</a>** - Static type checking
- 🧪 **<a href="https://docs.pytest.org/en/stable/" target="_blank">Pytest</a>** - Testing framework

</td>
</tr>
</table>

## 📋 Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Node.js 18+ (for frontend assets)
- Poetry

## 🚀 Quick Start

### 1. **Clone & Install Dependencies**

```bash
git clone <repository-url>
cd title-seeker-backend
```

```bash
poetry install
```

### 2. **Environment Configuration**

Create a `.env` file in the root directory with the following configuration:

```bash
⚠️ Ask the owner for credentials ⚠️
```

### 3. **Database Setup**

```bash
docker compose up -d db
```

```bash
flask db upgrade
```

```bash
flask create-admin
```

Add `credentials.json` file to the root directory

Fill the database with content from Google Sheets:

```bash
flask execute-all
```

⚠️ Ask the owner for the authorization code ⚠️

Add `uploads` folder with posters and avatars to the root directory (ask the owner)

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run API tests only
poetry run pytest test_api/

# Run Flask tests only
poetry run pytest test_flask/
```

## 🔧 Code Quality

```bash
# Format code with Ruff
poetry run ruff format .

# Lint code
poetry run ruff check .

# Type checking with Mypy
poetry run mypy .
```

## 🐳 Docker Deployment

Changes are pushed to the docker hub repository and then pulled on the server.
For hotfixes there is a quick script, and after significant changes it is better to use git actions. To do this, you need to update the project version using a script.

---

## 🔢 Versioning

After changes in the project, the version should be updated. This is done with a script:

```bash
sh version.sh patch/minor/major
```

---

## 📚 API Documentation

Once the FastAPI server is running, visit:

- **Interactive API Docs (Swagger)**: http://127.0.0.1:5002/docs
- **Alternative Docs (ReDoc)**: http://127.0.0.1:5002/redoc
- **OpenAPI JSON**: http://127.0.0.1:5002/openapi.json
