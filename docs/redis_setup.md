# Redis Setup and Configuration Notes

## 1. Overview

Redis will be used in the n8n-workflow-analyzer project primarily for caching and potentially for other microservice-related functionalities like session management or task queueing, as per the "Microservices Layer - Creative Phase decision."

## 2. Installation and Running Redis

Redis needs to be installed and running on a server accessible to the application. Installation methods vary by operating system:

-   **Linux (apt):** `sudo apt update && sudo apt install redis-server`
-   **Linux (yum):** `sudo yum install redis`
-   **macOS (Homebrew):** `brew install redis`
-   **Docker:** A Redis Docker image is a common way to run Redis: `docker run -d -p 6379:6379 redis`

After installation, ensure Redis is running (e.g., `redis-cli ping` should return `PONG`).

## 3. Configuration Parameters

The application will need the following parameters to connect to Redis. These should be managed through the project's configuration system (e.g., environment variables, configuration file).

-   **`REDIS_HOST`**: The hostname or IP address of the Redis server (e.g., `localhost`, `127.0.0.1`, or a remote IP).
    -   Default: `localhost`
-   **`REDIS_PORT`**: The port Redis is listening on.
    -   Default: `6379`
-   **`REDIS_PASSWORD`**: The password for Redis, if authentication is enabled (recommended for production).
    -   Default: `None` (or empty string)
-   **`REDIS_DB`**: The Redis database number to use. Redis supports multiple databases (0-15 by default).
    -   Default: `0`

These parameters will be used by the Python `redis` library to establish a connection.

## 4. Python Client Library

The project uses the `redis` Python library, which is listed in `requirements.txt`.

Example connection in Python (actual implementation will be in `n8n_analyzer/infrastructure/cache.py` or similar):

```python
# import redis
#
# # Example: Reading from config
# REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
# REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
# REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
# REDIS_DB = int(os.getenv('REDIS_DB', 0))
#
# try:
#     r = redis.Redis(
#         host=REDIS_HOST,
#         port=REDIS_PORT,
#         password=REDIS_PASSWORD,
#         db=REDIS_DB,
#         charset="utf-8",
#         decode_responses=True # Important for string encoding
#     )
#     r.ping()
#     print("Successfully connected to Redis!")
# except redis.exceptions.ConnectionError as e:
#     print(f"Could not connect to Redis: {e}")
```

## 5. Potential Use Cases in This Project

-   **Caching Database Queries:** Store results of expensive or frequent database queries (e.g., aggregated statistics, common patterns).
-   **Caching Analysis Results:** Cache intermediate or final results of workflow analysis to speed up repeated requests.
-   **Session Management:** If the Flask web application requires user sessions.
-   **Task Queues:** For managing long-running analysis tasks asynchronously if the Hybrid Pipeline Architecture involves background workers.
-   **Rate Limiting:** For API endpoints, if needed.

This document provides a basic guide. Specific Redis configurations (e.g., persistence, memory limits) should be tuned based on production needs.
