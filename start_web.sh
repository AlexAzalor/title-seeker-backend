sleep 2
echo Run db upgrade
poetry run flask db upgrade
# echo Run app
# flask run -h 0.0.0.0
echo Run app server
# poetry run gunicorn -w 4 -b 0.0.0.0 'wsgi:app'
poetry run gunicorn -w 4 -b 0.0.0.0:8001 'wsgi:app'


# uvicorn and gunicorn are both servers used to run Python web applications, but they are designed for different types of applications and have different features:

# uvicorn
# Type: ASGI server
# Use Case: Designed for asynchronous web applications
# Protocols: Supports HTTP/1.1, HTTP/2, and WebSockets
# Performance: Built on uvloop and httptools for high performance
# Asynchronous Support: Fully supports async and await syntax, making it suitable for applications that require non-blocking I/O operations
# Typical Frameworks: FastAPI, Starlette, Django (with channels)

# gunicorn
# Type: WSGI server
# Use Case: Designed for synchronous web applications
# Protocols: Supports HTTP/1.1
# Performance: Uses multiple worker processes to handle concurrent requests
# Asynchronous Support: Limited, primarily designed for synchronous applications
# Typical Frameworks: Flask, Django (without channels), Pyramid

# Key Differences
# Asynchronous vs. Synchronous: uvicorn is designed for asynchronous applications, while gunicorn is designed for synchronous applications.
# Protocols: uvicorn supports HTTP/2 and WebSockets, while gunicorn primarily supports HTTP/1.1.
# Performance: uvicorn leverages uvloop and httptools for high performance in asynchronous applications, while gunicorn uses multiple worker processes to handle concurrency in synchronous applications.

# In summary, choose uvicorn for asynchronous applications that require non-blocking I/O and support for modern protocols like HTTP/2 and WebSockets. Choose gunicorn for traditional synchronous applications that can benefit from multiple worker processes to handle concurrent requests.
