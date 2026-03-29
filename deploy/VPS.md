# BulkGame on Ubuntu VPS — full setup from scratch

Gunicorn listens on **`127.0.0.1:8002`** (only on the server). Nginx on **port 80/443** is what the internet hits; it proxies to `8002`.

Default app directory: **`/var/www/bulkgame`**. You can be logged in as **root** in `~` — the steps below create and use `/var/www/bulkgame`.

---

## 0) Your VPS public IP

On the server:

```bash
curl -4 -s ifconfig.me
```

Use that IP in **`ALLOWED_HOSTS`** and **`CSRF_TRUSTED_ORIGINS`** (with `http://` until you add SSL, then `https://`).

---

## 1) Packages

```bash
apt update
apt install -y python3-venv python3-dev nginx git build-essential redis-server \
  postgresql postgresql-contrib libpq-dev ufw
```

Skip Postgres packages if you will use SQLite only.

Firewall (SSH first, then web):

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
ufw status
```

---

## 2) App directory and code

```bash
mkdir -p /var/www/bulkgame
cd /var/www/bulkgame
git clone https://github.com/YOUR_USERNAME/BulkGame.git .
# If the repo is private, use SSH URL or a deploy token.
```

---

## 3) Python virtualenv

```bash
cd /var/www/bulkgame
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
deactivate
```

---

## 4) Environment (`.env`)

```bash
cd /var/www/bulkgame
cp deploy/env.vps.example .env
nano .env
```

Set at least:

| Variable | Example |
|----------|---------|
| `SECRET_KEY` | Long random string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `YOUR_VPS_IP,127.0.0.1,localhost` (add domain later) |
| `CSRF_TRUSTED_ORIGINS` | `http://YOUR_VPS_IP` → after SSL use `https://yourdomain.com` |
| `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` |
| `CELERY_RESULT_BACKEND` | same as broker |
| `CELERY_TASK_ALWAYS_EAGER` | Omit or `False` if you run **Celery** (step 10) |
| `FACEBOOK_REDIRECT_URI` | Must match how users reach `/channels/facebook/callback/` |

**Subpath only** (site at `http://104.236.1.98/bulkgame/`): set `FORCE_SCRIPT_NAME=/bulkgame` and use **Option B** Nginx below.  
**Domain root** (e.g. `http://IP/` or a subdomain): leave `FORCE_SCRIPT_NAME` unset; use **Option A** Nginx.

---

## 5) Database (optional Postgres)

```bash
sudo -u postgres psql -c "CREATE USER bulkgame WITH PASSWORD 'STRONG_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE bulkgame OWNER bulkgame;"
```

In `.env`:

```env
DATABASE_URL=postgres://bulkgame:STRONG_PASSWORD@127.0.0.1:5432/bulkgame
```

Skip this section to use SQLite (file `db.sqlite3` in the project folder).

---

## 6) Django: migrate, static, media

```bash
cd /var/www/bulkgame
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
mkdir -p media
deactivate
```

---

## 7) Ownership (Gunicorn runs as `www-data`)

```bash
chown -R www-data:www-data /var/www/bulkgame
chmod 640 /var/www/bulkgame/.env
```

---

## 8) Nginx

**Option A — Django at site root** (`http://YOUR_IP/` or `https://domain/`)

```bash
cp /var/www/bulkgame/deploy/nginx-vps-root.conf /etc/nginx/sites-available/bulkgame
sed -i 's/YOUR_DOMAIN_OR_IP/YOUR_VPS_IP/g' /etc/nginx/sites-available/bulkgame
# Or nano and set server_name to your domain + IP
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/bulkgame /etc/nginx/sites-enabled/bulkgame
nginx -t && systemctl reload nginx
```

**Option B — Django under `/bulkgame`**, welcome page on `/`

```bash
cp /var/www/bulkgame/deploy/nginx-bulkgame.conf /etc/nginx/sites-available/bulkgame
nano /etc/nginx/sites-available/bulkgame   # server_name, paths if not /var/www/bulkgame
cp /var/www/bulkgame/deploy/welcome.html /var/www/html/welcome.html
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/bulkgame /etc/nginx/sites-enabled/bulkgame
nginx -t && systemctl reload nginx
```

Nginx is configured to **`proxy_pass` → `http://127.0.0.1:8002`**.

---

## 9) Gunicorn (port **8002**)

```bash
cp /var/www/bulkgame/deploy/gunicorn.service /etc/systemd/system/gunicorn-bulkgame.service
systemctl daemon-reload
systemctl enable --now gunicorn-bulkgame
systemctl status gunicorn-bulkgame --no-pager
```

Check app directly (on the server):

```bash
curl -sI http://127.0.0.1:8002/ | head -5
```

---

## 10) Redis + Celery (recommended for Facebook bulk delete)

```bash
systemctl enable --now redis-server
cp /var/www/bulkgame/deploy/celery.service /etc/systemd/system/celery-bulkgame.service
# If Redis unit is not redis-server.service:
#   systemctl list-units '*redis*'
#   nano /etc/systemd/system/celery-bulkgame.service  → fix After= line
systemctl daemon-reload
systemctl enable --now celery-bulkgame
systemctl status celery-bulkgame --no-pager
```

---

## 11) HTTPS (when you have a domain)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```

Then update `.env`: `CSRF_TRUSTED_ORIGINS` and `FACEBOOK_REDIRECT_URI` to **`https://`**, and restart:

```bash
systemctl restart gunicorn-bulkgame celery-bulkgame
```

---

## 12) After `git pull`

```bash
cd /var/www/bulkgame
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
deactivate
systemctl restart gunicorn-bulkgame celery-bulkgame
```

---

## Port summary

| Port | Role |
|------|------|
| **80 / 443** | Nginx (public) |
| **8002** | Gunicorn (**localhost only** — do not expose in firewall) |
| **6379** | Redis (**localhost** — do not expose) |

---

## Troubleshooting

```bash
journalctl -u gunicorn-bulkgame -n 80 --no-pager
journalctl -u celery-bulkgame -n 80 --no-pager
tail -50 /var/log/nginx/error.log
```

| Problem | What to check |
|---------|----------------|
| 502 Bad Gateway | `systemctl status gunicorn-bulkgame`, `curl 127.0.0.1:8002` |
| Deletes stuck | `celery-bulkgame` running, Redis up, `CELERY_TASK_ALWAYS_EAGER=False` |
| 400 CSRF / DisallowedHost | `.env` `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, scheme `http` vs `https` |

---

## Files in `deploy/`

| File | Role |
|------|------|
| `nginx-vps-root.conf` | Nginx → `127.0.0.1:8002`, app at URL root |
| `nginx-bulkgame.conf` | Nginx → `8002`, app under `/bulkgame/` |
| `gunicorn.service` | **`--bind 127.0.0.1:8002`** |
| `celery.service` | Celery worker |
| `env.vps.example` | `.env` template |
| `welcome.html` | Landing for `/` when using subpath config |
