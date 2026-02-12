# Deployment Guide

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Network access to authorized target systems
- Sufficient permissions for socket operations

## Local Development Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd security-assessment-platform

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation
python -m src.cli --help

# 5. Run tests
python -m pytest tests/ -v
```

## Production Deployment

### Dashboard Deployment

For production dashboard deployment, use a WSGI server:

```bash
# Using Gunicorn (Linux/macOS)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "dashboard.app:create_app()"

# Using Waitress (Windows/Linux)
pip install waitress
waitress-serve --port=8000 dashboard.app:create_app
```

### Behind a Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl;
    server_name secureaudit.internal.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "-m", "src.cli", "start-dashboard", "--host", "0.0.0.0"]
```

```bash
docker build -t secureaudit-pro .
docker run -p 5000:5000 secureaudit-pro
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| FLASK_SECRET_KEY | Dashboard session secret | Random |
| SA_LOG_LEVEL | Logging level | INFO |
| SA_SCAN_TIMEOUT | Default scan timeout | 2.0 |
| SA_MAX_THREADS | Maximum scan threads | 50 |

### Configuration Files

- `config/targets.yaml` - Scan target definitions
- `config/thresholds.yaml` - Risk scoring parameters

Copy to `.local.yaml` variants for environment-specific settings.

## Security Hardening

1. **Access Control**: Restrict dashboard access to authorized personnel
2. **TLS**: Always use HTTPS in production
3. **Authentication**: Add authentication middleware for the dashboard
4. **Network**: Run scans from a dedicated assessment network
5. **Data**: Encrypt assessment data at rest
6. **Logging**: Enable audit logging for all dashboard access
7. **Updates**: Keep all dependencies updated for security patches
