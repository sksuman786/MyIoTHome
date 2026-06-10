# cPanel Deployment Guide (Quick)

This guide explains how to deploy the project on a cPanel shared hosting account
using the cPanel Python App (Passenger) feature. The repository has been
simplified for single-server use (no Celery, Redis, or Channels/WebSockets).

1) Prepare your app files

- Upload the project files to your cPanel account (for example: ~/myhome/).
- Ensure `passenger_wsgi.py` is in the project root (next to `manage.py`).
- Copy `.env.example` to `.env` and edit environment values.

2) Create Python App in cPanel

- In cPanel, open "Setup Python App" (or "Python App").
- Create a new app with a Python version that matches your environment (e.g., 3.11).
- Set the application root to the folder containing `manage.py` (for example `myhome`).
- Set the application startup file to `passenger_wsgi.py` and the entry point to `application`.

3) Install dependencies

Use the virtualenv cPanel created for the app and install requirements. Example (via cPanel Terminal or SSH):

    source /home/USERNAME/virtualenv/<APP>/3.11/bin/activate
    pip install -r /home/USERNAME/myhome/requirements.txt

Notes:
- If your host doesn't provide compilation support for `psycopg2-binary`, consider using MySQL (install `mysqlclient`) or use SQLite for small single-user deployments.

4) Database

- cPanel typically provides MySQL/MariaDB. Create a database and user in the MySQL Databases panel and update `.env` with credentials.
- In `myhome/settings.py`, set `DB_ENGINE` to `django.db.backends.mysql` (or adjust via `.env`). Install `mysqlclient` into the virtualenv if using MySQL.

5) Run migrations & collect static

Activate the virtualenv and run:

    source /home/USERNAME/virtualenv/<APP>/3.11/bin/activate
    cd /home/USERNAME/myhome
    python manage.py migrate
    python manage.py collectstatic --noinput
    python manage.py createsuperuser

6) Static files and media

- Serve `staticfiles` and `media` via cPanel's document root mappings or configure an Alias pointing `/static/` to the `staticfiles` directory.

7) Email

- Update `.env` SMTP settings with your provider credentials (cPanel often provides SMTP settings).

8) Logs & debugging

- Use cPanel error logs and the project's `logs/` directory to troubleshoot.

9) Notes & recommendations

- For small personal deployments you can keep using SQLite to avoid DB setup.
- WebSocket features were removed for cPanel compatibility — if you need real-time features later, consider a VPS or cloud host and re-enable Channels/Redis.
- Celery/Redis removed — for background tasks use cron jobs or simple synchronous calls on low scale.

If you want, I can update `requirements.txt` to include `mysqlclient` and add example `DATABASES` entries in `myhome/settings.py` for MySQL. Tell me if you want that.
