# Production Deployment Guide

## Prerequisites

- Server with Ubuntu 20.04+
- PostgreSQL 12+
- Redis
- Python 3.10+
- Nginx
- Supervisor or systemd

## 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3.10 python3.10-venv python3-pip
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y redis-server
sudo apt install -y nginx supervisor
sudo apt install -y git curl wget
```

## 2. Database Setup

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE myhome_db;
CREATE USER myhome_user WITH PASSWORD 'secure_password_here';

ALTER ROLE myhome_user SET client_encoding TO 'utf8';
ALTER ROLE myhome_user SET default_transaction_isolation TO 'read_committed';
ALTER ROLE myhome_user SET default_transaction_deferrable TO on;
ALTER ROLE myhome_user SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE myhome_db TO myhome_user;
\q
```

## 3. Application Setup

```bash
# Create app directory
sudo mkdir -p /var/www/myhome
sudo chown -R $USER:$USER /var/www/myhome

# Clone repository
cd /var/www/myhome
git clone your_repo_url .

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy settings
cp .env.example .env
# Edit .env with production settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## 4. Gunicorn Configuration

```bash
# Create systemd service file
sudo nano /etc/systemd/system/myhome-gunicorn.service
```

Add:
```ini
[Unit]
Description=MyHome IoT Gunicorn
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/myhome
ExecStart=/var/www/myhome/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    myhome.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Create systemd service for Daphne (WebSockets)
sudo nano /etc/systemd/system/myhome-daphne.service
```

Add:
```ini
[Unit]
Description=MyHome IoT Daphne
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/myhome
ExecStart=/var/www/myhome/venv/bin/daphne \
    -b 127.0.0.1 \
    -p 8001 \
    myhome.asgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable myhome-gunicorn
sudo systemctl enable myhome-daphne
sudo systemctl start myhome-gunicorn
sudo systemctl start myhome-daphne
```

## 5. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/myhome
```

Add:
```nginx
upstream myhome_gunicorn {
    server 127.0.0.1:8000;
}

upstream myhome_daphne {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 20M;

    # Static files
    location /static/ {
        alias /var/www/myhome/staticfiles/;
    }

    # Media files
    location /media/ {
        alias /var/www/myhome/media/;
    }

    # WebSocket
    location /ws {
        proxy_pass http://myhome_daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API and web
    location / {
        proxy_pass http://myhome_gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/myhome /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx config
sudo nginx -t

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 6. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Update Nginx config for HTTPS
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

## 7. Redis Configuration

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## 8. Monitoring and Logging

```bash
# View logs
sudo journalctl -u myhome-gunicorn -f
sudo journalctl -u myhome-daphne -f
sudo tail -f /var/www/myhome/logs/debug.log

# Monitor services
sudo systemctl status myhome-gunicorn
sudo systemctl status myhome-daphne
```

## 9. Backups

```bash
# Create backup script
sudo nano /usr/local/bin/myhome-backup.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/backups/myhome"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump -U myhome_user myhome_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/myhome/media

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/myhome-backup.sh

# Add to crontab
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/myhome-backup.sh
```

## 10. Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

## Troubleshooting

### Service won't start
```bash
sudo systemctl status myhome-gunicorn -l
journalctl -xe
```

### Permission denied
```bash
sudo chown -R www-data:www-data /var/www/myhome
sudo chmod -R 755 /var/www/myhome
```

### Database connection error
```bash
sudo -u postgres psql -c "SELECT version();"
```

### WebSocket connection issues
```bash
# Check Daphne
sudo systemctl status myhome-daphne
netstat -tlnp | grep 8001
```

## Production Checklist

- [ ] DEBUG = False in settings
- [ ] ALLOWED_HOSTS configured
- [ ] SECRET_KEY changed
- [ ] Database backup strategy
- [ ] SSL certificate installed
- [ ] Email configured
- [ ] Redis running
- [ ] Static files collected
- [ ] Logs monitored
- [ ] Firewall configured
- [ ] Backups automated
