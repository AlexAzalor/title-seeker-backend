#!/bin/bash

# Push to docker hub
# Add docker login?
# Variables?

echo "Do you check Quick Movies? (yes/no):"
read -r answer

if [[ "$answer" != "yes" && "$answer" != "y" ]]; then
    echo "Script stopped. Please check Quick Movies first."
    exit 1
fi

echo "Proceeding with Docker build and push..."

poetry run ruff check .
poetry run mypy
poetry run ruff format .

docker build -t azalor/title-hunter-backend .
docker push azalor/title-hunter-backend
