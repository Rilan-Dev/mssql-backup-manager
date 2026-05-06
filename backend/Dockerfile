
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for SQL Server ODBC driver
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc-dev \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies from requirements.txt (if exists) or manual
# We'll copy requirements first to leverage cache
COPY requirements.txt .

# Since we might not have a full requirements.txt, we install known deps
RUN pip install --no-cache-dir fastapi uvicorn pyodbc python-dotenv paramiko

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run commands`
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# Run commands Manualy on container:
# uvicorn main:app --host 0.0.0.0 --port 8000
