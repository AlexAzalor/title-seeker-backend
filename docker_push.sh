#!/bin/bash

# Push to docker hub
# Add docker login?
# Variables?

echo "Have you checked that the new changes don't write unnecessary data to the Audit log? (yes/no):"
read -r answer

case "$answer" in
    yes|y)
        echo "Audit log check passed."
        ;;
    *)
        echo "Script aborted. Please check Audit log changes first."
        exit 1
        ;;
esac

echo "Have you checked Quick Movies? (yes/no):"
read -r answer

case "$answer" in
    yes|y)
        echo "Quick Movies check passed."
        ;;
    *)
        echo "Script aborted. Please check Quick Movies first."
        exit 1
        ;;
esac

echo "Proceeding with Docker build and push..."

poetry run ruff check .
poetry run mypy
poetry run ruff format .

docker build -t azalor/title-hunter-backend .
docker push azalor/title-hunter-backend
