# Push to docker hub
# Add docker login?
# Variables?
poetry run ruff check .
poetry run mypy
poetry run ruff format .

docker build -t azalor/title-hunter-backend .
docker push azalor/title-hunter-backend
