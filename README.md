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

## Movie tournament pool

`POST /api/movies/tournament/` generates a pool without saving a tournament. For example:

```json
{
  "size": 16,
  "include_genres": ["action", "drama"],
  "genre_threshold": 60,
  "exclude_genres": [],
  "include_specifications": [],
  "specification_threshold": 100,
  "exclude_specifications": [],
  "collection_type": "base",
  "exclude_movies": ["movie-key"],
  "exclude_shared_universes": ["star-wars"]
}
```

Only `size` (16 or 32) is required. Thresholds range from 60 to 100 and default to 100;
each is the minimum stored match percentage for an individual selected genre or specification,
inclusive. As in super search's default mode, a movie is included if it matches **any** selected
genre or specification at its respective threshold. Empty include lists add no filter; exclusions
always apply. `exclude_movies` contains movie keys (excluding the selected movie and its collection
members); `exclude_shared_universes` contains shared-universe keys (for example, `star-wars`) and
excludes all movies assigned to any selected universe. Omit `collection_type` for no collection
filter. `base` selects designated collection bases, while `standalone` excludes collection
members and shared-universe movies. The optional `lang` and `user_uuid` query parameters
work as on the movie list. The response contains `movies` (movie previews) and `total`
(the count before sampling). If there are too few matches, HTTP 400 returns
`{"detail": {"message": "Not enough matching movies", "available_movies": 15}}`.

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
