# BulkGame on Ubuntu VPS (Nginx + Gunicorn + Celery + Redis)

Paths below use **`/var/www/bulkgame`** as the app directory. Change if yours differs.

## 1. Server packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev nginx git build-essential redis-server \
  postgresql postgresql-contrib libpq-dev
```

SQLite-only: you can skip `postgresql` packages.

## 2. Code and virtualenv

```bash
sudo mkdir -p /var/www/bulkgame
sudo chown $USER:$USER /var/www/bulkgame
cd /var/www/bulkgame
git clone <YOUR_REPO_URL> .
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 3. Environment

```bash
cp deploy/env.vps.example .env
nano .env
```

- Set **`SECRET_KEY`**, **`ALLOWED_HOSTS`**, **`CSRF_TRUSTED_ORIGINS`** (with `https://` after SSL).
- **`FORCE_SCRIPT_NAME`**: leave unset for a **subdomain at root**; use **`/bulkgame`** only if the site is served under `https://IP/bulkgame/`.
- **`CELERY_TASK_ALWAYS_EAGER`**: leave **`False`** (or omit) when running **`celery.service`**. Set **`True`** only if you intentionally skip the Celery worker.
- Set **`DATABASE_URL`** for Postgres, or omit for SQLite.

## 4. Django

```bash
source /var/www/bulkgame/venv/bin/activate
cd /var/www/bulkgame
python manage.py migrate
python manage.py collectstatic --noinput
mkdir -p media
```

Create admin if needed: `python manage.py createsuperuser`

## 5. Permissions

```bash
sudo chown -R www-data:www-data /var/www/bulkgame
sudo chmod 640 /var/www/bulkgame/.env
```

## 6. Nginx

**Option A — app at domain root** (e.g. `https://fbtools.example.com/`):

```bash
sudo cp deploy/nginx-vps-root.conf /etc/nginx/sites-available/bulkgame
sudo nano /etc/nginx/sites-available/bulkgame   # set server_name
sudo ln -sf /etc/nginx/sites-available/bulkgame /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default   # if it conflicts (duplicate listen)
sudo nginx -t && sudo systemctl reload nginx
```

**Option B — app under `/bulkgame` on same IP** (welcome page on `/`):

```bash
sudo cp deploy/nginx-bulkgame.conf /etc/nginx/sites-available/bulkgame
# Edit paths/server_name if not using /var/www/bulkgame
sudo ln -sf /etc/nginx/sites-available/bulkgame /etc/nginx/sites-enabled/
sudo cp deploy/welcome.html /var/www/html/welcome.html
sudo nginx -t && sudo systemctl reload nginx
```

Use **Option B** only with `.env`: `FORCE_SCRIPT_NAME=/bulkgame`.

## 7. Gunicorn (systemd)

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/gunicorn-bulkgame.service
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-bulkgame
sudo systemctl status gunicorn-bulkgame --no-pager
```

## 8. Redis + Celery (recommended for FB bulk delete)

```bash
sudo systemctl enable --now redis-server
sudo cp deploy/celery.service /etc/systemd/system/celery-bulkgame.service
sudo systemctl daemon-reload
sudo systemctl enable --now celery-bulkgame
sudo systemctl status celery-bulkgame --no-pager
```

If your distro names Redis differently, edit `After=` / `Requires=` in `celery.service` or run `systemctl list-units | grep redis`.

## 9. HTTPS (Let’s Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Update **`.env`**: `CSRF_TRUSTED_ORIGINS` and **`FACEBOOK_REDIRECT_URI`** must use **`https://`**.

## 10. After each `git pull`

```bash
cd /var/www/bulkgame
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn-bulkgame celery-bulkgame
```

## Troubleshooting

| Issue | Check |
|--------|--------|
| 500 errors | `sudo journalctl -u gunicorn-bulkgame -n 80 --no-pager` |
| Deletes never finish | `sudo systemctl status celery-bulkgame`, Redis running, `CELERY_TASK_ALWAYS_EAGER=False` |
| Static 404 | `collectstatic`, Nginx `alias` paths, `FORCE_SCRIPT_NAME` matches Nginx |
| CSRF / login | `CSRF_TRUSTED_ORIGINS`, `ALLOWED_HOSTS`, correct scheme in `.env` |

## Files in `deploy/`

| File | Role |
|------|------|
| `nginx-vps-root.conf` | Nginx when Django is at site root |
| `nginx-bulkgame.conf` | Nginx when Django is under `/bulkgame/` |
| `gunicorn.service` | WSGI app |
| `celery.service` | Background worker |
| `welcome.html` | Optional landing for `/` (subpath setup) |
| `env.vps.example` | `.env` template |
