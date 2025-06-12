# Dockerfile for n8n-workflow-analyzer

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any are found to be needed later, e.g., for psycopg2)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     libpq-dev \
#  && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This includes n8n_analyzer, config, scripts (if needed by app)
COPY ./n8n_analyzer /app/n8n_analyzer
COPY ./config /app/config
# Add other directories if they become part of the core app runtime

# Expose the port the app runs on (e.g., Flask default port)
# This will be mapped in docker-compose.yml
EXPOSE 5000

# Define the command to run the application
# This is a placeholder and will likely be adjusted once the Flask app entry point is defined.
# For example, it might be: CMD ["python", "n8n_analyzer/api/app.py"] or CMD ["flask", "run", "--host=0.0.0.0"]
# Or using gunicorn: CMD ["gunicorn", "-b", "0.0.0.0:5000", "n8n_analyzer.api.wsgi:app"]
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
# Ensure that if you use `flask run`, the FLASK_APP environment variable is set,
# or the entry point is correctly specified.
# For now, assuming FLASK_APP will be set in docker-compose.yml or .env
