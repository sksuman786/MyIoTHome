# 🎯 MyHome IoT - cPanel Hosting Setup Guide

## ✅ Before You Start

Make sure your cPanel hosting has:
- ✓ Python 3.8+ (check in cPanel > Terminal or ask host)
- ✓ PostgreSQL OR MySQL/MariaDB
- ✓ SSH access enabled
- ✓ 512MB+ free space
- ✓ pip package manager

---

## 📋 Step 1: Prepare Your cPanel Account

### 1.1 Create Database in cPanel
```
1. Login to cPanel
2. Go to "Databases" > "MySQL Databases"
3. Create database:
   - Database name: myhome_db
   - Username: myhome_user
   - Password: strong_password_here
4. Add user to database with ALL privileges
```

### 1.2 Create Database for SQLite (Optional)
If MySQL isn't available, we can use SQLite instead.

### 1.3 Note Your Database Details
```
Database Host: Usually localhost or 127.0.0.1
Database Name: myhome_db (or your actual name)
Database User: myhome_user
Database Password: your_password
```

---

## 📦 Step 2: Upload Project Files

### 2.1 Connect via SFTP/FTP
Using FileZilla or similar:
1. Connect to your cPanel server via SFTP
2. Navigate to the folder where you want to host
3. Upload these files:
```
myhome/                    (entire project folder)
   ├── accounts/
   ├── devices/
   ├── api/
   ├── dashboard/
   ├── notifications/
   ├── websocket/
   ├── templates/
   ├── static/
   ├── myhome/
   ├── manage.py
   ├── requirements.txt
   └── .env
```

### 2.2 Typical Upload Location
Ask your host where to upload - common options:
- `/home/username/public_html/` (main domain)
- `/home/username/public_html/myhome/` (subdomain)

---

## 🔧 Step 3: Install Python Packages via SSH

### 3.1 Connect via SSH
```bash
# Open Terminal or SSH into your server
ssh username@your-domain.com
```

### 3.2 Navigate to Project
```bash
cd /path/to/your/myhome/project
```

### 3.3 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.4 Upgrade pip
```bash
pip install --upgrade pip
```

### 3.5 Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- Django 5.0
- Django REST Framework
- All other required packages

**Note**: If MySQL is used, also install:
```bash
pip install mysqlclient
```

---

## 📝 Step 4: Configure Settings for cPanel

### 4.1 Create .env File

In cPanel File Manager or via SSH:
```bash
nano .env
```

Add this content (modify as needed):
```
# Django
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-here-change-this
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-cpanel-domain.com

# Database (MySQL)
DB_ENGINE=django.db.backends.mysql
DB_NAME=myhome_db
DB_USER=myhome_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306

# OR Database (SQLite - simpler)
# DB_ENGINE=django.db.backends.sqlite3
# DB_NAME=/path/to/db.sqlite3

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=email_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Redis (skip if not available)
# REDIS_URL=redis://localhost:6379/0

# Security
SECURE_SSL_REDIRECT=False  # Set to True after HTTPS is set up
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

### 4.2 Update Django Settings for cPanel

Edit `myhome/settings.py`:

**Find this section** (around line 30):
```python
DEBUG = os.getenv('DEBUG', 'True') == 'True'
```

**Change to**:
```python
DEBUG = os.getenv('DEBUG', 'False') == 'True'
```

**Find DATABASES section** (around line 80):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Replace with MySQL**:
```python
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.getenv('DB_NAME', 'myhome_db'),
        'USER': os.getenv('DB_USER', 'myhome_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}
```

**OR keep SQLite** (simpler, no extra config):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
```

---

## 🗄️ Step 5: Initialize Database

### 5.1 Run Migrations (SSH)
```bash
# Activate venv first
source venv/bin/activate

# Run migrations
python manage.py migrate
```

This creates all database tables.

### 5.2 Create Admin User (SSH)
```bash
python manage.py createsuperuser
```

Follow the prompts:
```
Username: admin
Email: your-email@example.com
Password: strong_password
```

### 5.3 Collect Static Files (SSH)
```bash
python manage.py collectstatic --noinput
```

This copies CSS, JS, images to a static folder.

---

## 🌐 Step 6: Set Up Web Server

### Option A: Using Passenger (Recommended for cPanel)

#### 6A.1 In cPanel Setup Passenger
```
1. Login to cPanel
2. Go to "Setup Python App" (under Software)
3. Click "Create Application"
4. Fill in:
   - Python version: 3.8+ (highest available)
   - Application root: /path/to/your/myhome
   - Application URL: yourdomain.com or subdomain
   - Passenger log file: logs/passenger.log
5. Application startup file: myhome/wsgi.py
```

#### 6A.2 Configure Passenger
Create file: `.htaccess` in your public_html folder:
```apache
<IfModule mod_passenger.c>
  PassengerPython /path/to/venv/bin/python
  PassengerAppRoot /path/to/myhome
</IfModule>

# Don't process these files through Django
<FilesMatch "^(favicon\.ico|robots\.txt)$">
  SetHandler default-handler
</FilesMatch>
```

### Option B: Using uWSGI (Advanced)

If cPanel doesn't have Passenger, use uWSGI:

#### 6B.1 Install uWSGI
```bash
source venv/bin/activate
pip install uWSGI
```

#### 6B.2 Create uWSGI Config
Create file: `uwsgi.ini`
```ini
[uwsgi]
project = myhome
base = /path/to/myhome

chdir = %(base)
module = %(project).wsgi:application
master = true
processes = 4
socket = %(base)/uwsgi.sock
vacuum = true
die-on-term = true
```

#### 6B.3 Setup in cPanel
In cPanel Terminal:
```bash
# Create startup script
nano start_uwsgi.sh

# Add:
#!/bin/bash
source /path/to/venv/bin/activate
uwsgi --ini /path/to/uwsgi.ini
```

---

## 🔒 Step 7: Configure HTTPS/SSL

### 7.1 Enable SSL in cPanel
```
1. Go to cPanel > SSL/TLS
2. Look for "AutoSSL" or "Let's Encrypt"
3. Click to install free SSL certificate
4. Wait for installation (5-10 minutes)
```

### 7.2 Force HTTPS in Django
Edit `.env`:
```
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## 📧 Step 8: Configure Email

### 8.1 Create Email Account in cPanel
```
1. Go to cPanel > Email Accounts
2. Create new account:
   - Email: noreply@yourdomain.com
   - Password: strong_password
3. Copy the SMTP settings
```

### 8.2 Update .env
```
EMAIL_HOST=mail.yourdomain.com
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=the_password_you_set
```

---

## ✅ Step 9: Verify Installation

### 9.1 Check Django Admin
Visit: `https://yourdomain.com/admin/`

You should see the login page.

### 9.2 Login
Use the superuser credentials you created in Step 5.2

### 9.3 Add Test Device
In admin panel:
```
1. Click "Devices"
2. Add a device
3. Copy the API key
```

### 9.4 Access Dashboard
Visit: `https://yourdomain.com/dashboard/`

---

## 🐛 Troubleshooting

### Issue: "500 Internal Server Error"

**Check error logs**:
```bash
# cPanel error log
cat /home/username/public_html/error_log

# Django error log
cat logs/debug.log
```

### Issue: "Database connection error"

**Verify credentials**:
```bash
# SSH - test MySQL connection
mysql -h localhost -u myhome_user -p

# Enter password when prompted
# Type: USE myhome_db;
# Should say "Database changed"
```

### Issue: "Static files not loading"

**Collect static files**:
```bash
python manage.py collectstatic --noinput --clear
```

### Issue: "Email not sending"

**Test email in Django shell**:
```bash
python manage.py shell
```

Then:
```python
from django.core.mail import send_mail
send_mail('Test', 'This is a test', 'noreply@yourdomain.com', ['your-email@gmail.com'])
```

---

## 🔄 Common Commands for cPanel

```bash
# Activate virtual environment
source /path/to/venv/bin/activate

# Install new package
pip install package_name

# Run migrations
python manage.py migrate

# Create new superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Backup database
mysqldump -u myhome_user -p myhome_db > backup.sql

# Check Django version
python manage.py --version
```

---

## 📦 Additional Requirements for cPanel

### If Email Isn't Working
Use Gmail SMTP:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587
```

**Note**: Generate app password in Gmail settings > Security

### If MySQL Connection Fails
Make sure you installed:
```bash
pip install mysqlclient
```

### If WebSockets Needed
WebSockets may not work on shared cPanel hosting. This is normal - the app will still work fine without real-time updates.

---

## 🎯 Final Checklist

- [ ] Database created in cPanel
- [ ] Files uploaded via SFTP
- [ ] Virtual environment created
- [ ] Packages installed
- [ ] .env file created with credentials
- [ ] Migrations run successfully
- [ ] Superuser created
- [ ] Static files collected
- [ ] Web server configured (Passenger/uWSGI)
- [ ] SSL certificate installed
- [ ] Email account created and configured
- [ ] Admin page loads at /admin/
- [ ] Dashboard accessible

---

## ✨ You're Done!

Your cPanel-hosted MyHome IoT platform is now running!

**Access Points**:
- Admin: `https://yourdomain.com/admin/`
- Dashboard: `https://yourdomain.com/dashboard/`
- API: `https://yourdomain.com/api/`

---

## 📞 cPanel Host Support

If you get stuck, contact your cPanel host's support:
- Ask about: Python version, MySQL, SSH access
- They can help with: Creating databases, Passenger setup, SSL
- You handle: Django code and configuration

---

**Questions? Check DEPLOYMENT.md for more advanced setup options.**
