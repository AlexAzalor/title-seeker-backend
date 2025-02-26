echo Run API server
# poetry run uvicorn --workers 4 --host 0.0.0.0 --port 8000 api:app
poetry run uvicorn --workers 4 --host 0.0.0.0 --port 8002 api:app

# The active selection is a shell script that is used to start an API server. The script consists of two commands.

# The first command, echo Run API server, is a simple echo command that outputs the text "Run API server" to the terminal. This is typically used to inform the user that the process of starting the API server is about to begin.

# The second command, poetry run uvicorn --workers 4 --host 0.0.0.0 --port 8002 api:app, is the main command that starts the API server. It uses poetry, a dependency management and packaging tool for Python, to run uvicorn, an ASGI server for Python web applications.
# - The --workers 4 option specifies that the server should use 4 worker processes to handle incoming requests, which can improve performance by allowing multiple requests to be processed concurrently.
# - The --host 0.0.0.0 option tells the server to listen on all available network interfaces, making it accessible from any IP address.
# - The --port 8002 option specifies that the server should listen on port 8002.
# - Finally, api:app indicates the ASGI application to run, where api is the module name and app is the application instance within that module.
