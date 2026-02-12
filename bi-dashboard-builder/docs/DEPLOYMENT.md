# Deployment Guide

This guide covers all deployment options for the BI Dashboard Builder,
from local development to production-grade containerized deployments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Production with Gunicorn](#production-with-gunicorn)
4. [Docker Deployment](#docker-deployment)
5. [Environment Variables](#environment-variables)
6. [Reverse Proxy (Nginx)](#reverse-proxy-nginx)
7. [Cloud Deployment](#cloud-deployment)
8. [Security Considerations](#security-considerations)
9. [Monitoring & Logging](#monitoring--logging)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- 512 MB RAM minimum (1 GB recommended for large datasets)
- Disk space for uploaded files (configurable, default 50 MB limit per file)

---

## Local Development

### Quick Start

```bash
# Clone or navigate to the project directory
cd bi-dashboard-builder

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
python -m app.main
```

The application will be available at `http://localhost:5000`.

### Development Mode

Flask's debug mode enables auto-reload on code changes:

```bash
export FLASK_DEBUG=1    # Linux/macOS
set FLASK_DEBUG=1       # Windows CMD
$env:FLASK_DEBUG="1"    # Windows PowerShell

python -m app.main
```

### Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Production with Gunicorn

For production, use Gunicorn as the WSGI server (Linux/macOS):

```bash
pip install gunicorn

# Basic single-worker setup
gunicorn "app.main:create_app()" --bind 0.0.0.0:8000

# Production multi-worker setup
gunicorn "app.main:create_app()" \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile /var/log/bi-dashboard/access.log \
    --error-logfile /var/log/bi-dashboard/error.log \
    --max-requests 1000 \
    --max-requests-jitter 50
```

### Worker Configuration

Rule of thumb for worker count: `(2 * CPU_CORES) + 1`

| CPUs | Workers | Threads | Total Concurrent |
|------|---------|---------|------------------|
| 1    | 3       | 2       | 6                |
| 2    | 5       | 2       | 10               |
| 4    | 9       | 2       | 18               |
| 8    | 17      | 2       | 34               |

### Windows Production (Waitress)

Gunicorn does not support Windows. Use Waitress instead:

```bash
pip install waitress

waitress-serve --port=8000 --threads=4 app.main:app
```

---

## Docker Deployment

### Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p uploads

# Set environment variables
ENV FLASK_DEBUG=0
ENV PORT=8000
ENV SECRET_KEY=change-this-in-production

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["gunicorn", "app.main:create_app()", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120"]
```

### Docker Compose

```yaml
version: "3.9"

services:
  bi-dashboard:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - uploads:/app/uploads
      - ./data:/app/data:ro
      - ./templates:/app/templates:ro
    environment:
      - SECRET_KEY=${SECRET_KEY:-your-secret-key}
      - FLASK_DEBUG=0
      - PORT=8000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  uploads:
```

### Build and Run

```bash
# Build the image
docker build -t bi-dashboard-builder .

# Run the container
docker run -d \
    --name bi-dashboard \
    -p 8000:8000 \
    -v bi-uploads:/app/uploads \
    -e SECRET_KEY=my-secure-key \
    bi-dashboard-builder

# Using Docker Compose
docker compose up -d
```

---

## Environment Variables

| Variable      | Default                | Description                          |
|---------------|------------------------|--------------------------------------|
| `SECRET_KEY`  | (random dev key)       | Flask session secret (set in prod!)  |
| `PORT`        | `5000`                 | Server listening port                |
| `FLASK_DEBUG` | `1`                    | Debug mode (set to `0` in prod)      |

### Setting Environment Variables

```bash
# Linux/macOS
export SECRET_KEY="your-secure-random-key-here"
export FLASK_DEBUG=0
export PORT=8000

# Windows PowerShell
$env:SECRET_KEY="your-secure-random-key-here"
$env:FLASK_DEBUG="0"
$env:PORT="8000"
```

---

## Reverse Proxy (Nginx)

For production, place Nginx in front of Gunicorn:

```nginx
upstream bi_dashboard {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name dashboard.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dashboard.example.com;

    ssl_certificate     /etc/ssl/certs/dashboard.pem;
    ssl_certificate_key /etc/ssl/private/dashboard.key;

    # File upload size limit
    client_max_body_size 50M;

    # Static files
    location /static/ {
        alias /path/to/bi-dashboard-builder/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Application proxy
    location / {
        proxy_pass http://bi_dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }
}
```

---

## Cloud Deployment

### AWS (Elastic Beanstalk)

1. Install the EB CLI: `pip install awsebcli`
2. Initialize: `eb init -p python-3.12 bi-dashboard`
3. Create an environment: `eb create bi-dashboard-prod`
4. Deploy: `eb deploy`

Create a `Procfile`:
```
web: gunicorn app.main:create_app() --bind 0.0.0.0:8000 --workers 4
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/bi-dashboard

# Deploy
gcloud run deploy bi-dashboard \
    --image gcr.io/PROJECT_ID/bi-dashboard \
    --port 8000 \
    --memory 1Gi \
    --allow-unauthenticated
```

### Azure App Service

```bash
az webapp create \
    --resource-group myResourceGroup \
    --plan myAppServicePlan \
    --name bi-dashboard \
    --runtime "PYTHON:3.12"

az webapp config set \
    --resource-group myResourceGroup \
    --name bi-dashboard \
    --startup-file "gunicorn app.main:create_app() --bind 0.0.0.0:8000"
```

### Heroku

Create a `Procfile`:
```
web: gunicorn app.main:create_app() --bind 0.0.0.0:$PORT --workers 2
```

```bash
heroku create bi-dashboard
heroku config:set SECRET_KEY=your-key FLASK_DEBUG=0
git push heroku main
```

---

## Security Considerations

1. **Set a strong `SECRET_KEY`** in production. Generate one:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Disable debug mode** (`FLASK_DEBUG=0`).

3. **Use HTTPS** in production via reverse proxy or cloud load balancer.

4. **Limit file uploads** - The default 50 MB limit is set in `main.py`.

5. **Validate uploaded files** - Only CSV, XLSX, and JSON are accepted.

6. **Session management** - In-memory sessions are suitable for single-server
   deployments. For multi-server, switch to Redis-backed sessions.

7. **CORS** - If exposing the API externally, configure Flask-CORS.

---

## Monitoring & Logging

### Gunicorn Logging

```bash
gunicorn "app.main:create_app()" \
    --access-logfile /var/log/bi-dashboard/access.log \
    --error-logfile /var/log/bi-dashboard/error.log \
    --log-level info
```

### Health Check Endpoint

The root URL (`/`) serves as a health check. For dedicated monitoring:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
```

### Recommended Monitoring Stack

- **Application metrics:** Prometheus + Grafana
- **Log aggregation:** ELK Stack or Loki
- **Uptime monitoring:** UptimeRobot, Pingdom, or AWS CloudWatch

---

## Troubleshooting

### Common Issues

| Issue                          | Solution                                        |
|--------------------------------|-------------------------------------------------|
| `ModuleNotFoundError`          | Activate venv and run `pip install -r requirements.txt` |
| Port already in use            | Change PORT env var or kill the existing process |
| File upload fails              | Check `MAX_CONTENT_LENGTH` and disk space        |
| Charts not rendering           | Ensure Plotly JS CDN is accessible               |
| Slow performance               | Increase Gunicorn workers, add caching           |
| Session lost after restart     | Expected for in-memory sessions; use Redis       |

### Debug Mode

For development debugging:

```bash
FLASK_DEBUG=1 python -m app.main
```

This enables:
- Auto-reload on code changes
- Interactive debugger in the browser
- Detailed error pages
