# Deployment Guide

Production deployment guide for the Enhanced Clinical-Grade Lung Cancer Classifier.

## Pre-Deployment Checklist

### Security
- [ ] Change `FLASK_SECRET_KEY` to a strong random value
- [ ] Set `FLASK_ENV=production` in .env
- [ ] Remove or secure default admin credentials
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Implement rate limiting
- [ ] Add CSRF protection for forms

### Database
- [ ] Migrate from SQLite to PostgreSQL
- [ ] Set up database backups
- [ ] Configure connection pooling
- [ ] Set up database monitoring
- [ ] Create database indexes

### Application
- [ ] Test all features thoroughly
- [ ] Set up error monitoring (Sentry, etc.)
- [ ] Configure proper logging
- [ ] Set up log rotation
- [ ] Optimize model loading
- [ ] Configure caching (Redis)

### Infrastructure
- [ ] Set up reverse proxy (Nginx)
- [ ] Configure WSGI server (Gunicorn)
- [ ] Set up process manager (Systemd/Supervisor)
- [ ] Configure auto-restart on failure
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure alerts

## Deployment Options

### Option 1: Traditional Server (Ubuntu/Debian)

#### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3.10 python3-pip python3-venv nginx postgresql
```

#### 2. Create Application User

```bash
sudo useradd -m -s /bin/bash lungcancer
sudo su - lungcancer
```

#### 3. Clone and Setup Application

```bash
cd /home/lungcancer
git clone <repository-url> app
cd app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

#### 4. Configure PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE lungcancer_db;
CREATE USER lungcancer_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE lungcancer_db TO lungcancer_user;
\q
```

#### 5. Update .env for Production

```env
FLASK_ENV=production
FLASK_SECRET_KEY=<generate-strong-random-key>
DATABASE_URL=postgresql://lungcancer_user:strong_password_here@localhost/lungcancer_db
OPENAI_API_KEY=<your-api-key>
```

#### 6. Initialize Database

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### 7. Create Gunicorn Service

Create `/etc/systemd/system/lungcancer.service`:

```ini
[Unit]
Description=Lung Cancer Classifier
After=network.target

[Service]
User=lungcancer
Group=lungcancer
WorkingDirectory=/home/lungcancer/app
Environment="PATH=/home/lungcancer/app/venv/bin"
ExecStart=/home/lungcancer/app/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /home/lungcancer/app/logs/access.log \
    --error-logfile /home/lungcancer/app/logs/error.log \
    app:app

[Install]
WantedBy=multi-user.target
```

#### 8. Configure Nginx

Create `/etc/nginx/sites-available/lungcancer`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Max upload size
    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /static {
        alias /home/lungcancer/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 9. Enable and Start Services

```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/lungcancer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Enable and start application
sudo systemctl enable lungcancer
sudo systemctl start lungcancer
sudo systemctl status lungcancer
```

#### 10. Set Up SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn psycopg2-binary

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads logs models

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "app:app"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: lungcancer_db
      POSTGRES_USER: lungcancer_user
      POSTGRES_PASSWORD: strong_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://lungcancer_user:strong_password_here@db/lungcancer_db
    volumes:
      - ./models:/app/models
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - db
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
```

#### 3. Build and Run

```bash
docker-compose up -d
docker-compose logs -f
```

### Option 3: Cloud Platform (AWS/GCP/Azure)

#### AWS Elastic Beanstalk

1. Install EB CLI:
```bash
pip install awsebcli
```

2. Initialize EB:
```bash
eb init -p python-3.10 lungcancer-classifier
```

3. Create environment:
```bash
eb create production-env
```

4. Deploy:
```bash
eb deploy
```

#### Google Cloud Platform (App Engine)

1. Create `app.yaml`:
```yaml
runtime: python310
entrypoint: gunicorn -b :$PORT app:app

env_variables:
  FLASK_ENV: production
  DATABASE_URL: postgresql://...

automatic_scaling:
  min_instances: 1
  max_instances: 10
```

2. Deploy:
```bash
gcloud app deploy
```

## Post-Deployment

### 1. Verify Deployment

```bash
# Check application status
curl https://your-domain.com/

# Check logs
sudo journalctl -u lungcancer -f

# Monitor resources
htop
```

### 2. Set Up Monitoring

#### Application Monitoring (Sentry)

```python
# Add to app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

#### Server Monitoring (Prometheus)

Install Prometheus and configure metrics endpoint.

### 3. Set Up Backups

#### Database Backup Script

```bash
#!/bin/bash
# /home/lungcancer/backup.sh

BACKUP_DIR="/home/lungcancer/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -U lungcancer_user lungcancer_db > "$BACKUP_DIR/db_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /home/lungcancer/backup.sh
```

### 4. Set Up Log Rotation

Create `/etc/logrotate.d/lungcancer`:

```
/home/lungcancer/app/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 lungcancer lungcancer
    sharedscripts
    postrotate
        systemctl reload lungcancer
    endscript
}
```

## Maintenance

### Update Application

```bash
cd /home/lungcancer/app
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart lungcancer
```

### Database Migrations

```bash
# Backup first
pg_dump -U lungcancer_user lungcancer_db > backup.sql

# Run migrations
python migrate.py

# Verify
python -c "from app import app, db; app.app_context().push(); print(db.engine.table_names())"
```

### Monitor Performance

```bash
# Check application logs
sudo journalctl -u lungcancer -n 100

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check system resources
htop
df -h
free -m
```

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u lungcancer -n 50

# Check configuration
sudo systemctl status lungcancer

# Test manually
cd /home/lungcancer/app
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 app:app
```

### Database Connection Issues

```bash
# Test connection
psql -U lungcancer_user -d lungcancer_db -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql
```

### High Memory Usage

```bash
# Reduce Gunicorn workers
# Edit /etc/systemd/system/lungcancer.service
--workers 2  # Instead of 4

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart lungcancer
```

## Security Best Practices

1. **Keep Software Updated**
   ```bash
   sudo apt update && sudo apt upgrade
   pip install --upgrade -r requirements.txt
   ```

2. **Use Strong Passwords**
   - Database passwords
   - Admin accounts
   - API keys

3. **Enable Firewall**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

4. **Regular Backups**
   - Database backups daily
   - Model files weekly
   - Configuration files

5. **Monitor Logs**
   - Set up alerts for errors
   - Review access logs regularly
   - Monitor for suspicious activity

## Performance Optimization

1. **Enable Caching**
   - Use Redis for session storage
   - Cache model predictions
   - Cache static assets

2. **Optimize Database**
   - Add indexes on frequently queried columns
   - Use connection pooling
   - Regular VACUUM and ANALYZE

3. **CDN for Static Assets**
   - Use CloudFlare or AWS CloudFront
   - Serve images from CDN
   - Enable compression

4. **Load Balancing**
   - Use multiple application servers
   - Configure Nginx load balancing
   - Implement health checks

## Support

For deployment issues:
1. Check logs first
2. Review this guide
3. Consult README.md
4. Open an issue on repository

---

**Remember:** Always test in a staging environment before deploying to production!
