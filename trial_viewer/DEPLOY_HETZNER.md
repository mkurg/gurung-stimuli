# Hetzner Review Site Deployment

This optional deployment serves the exported viewer through the existing Nginx on the Hetzner server and stores picture comments in one JSON file:

```text
/home/apazent/gurung-trial-viewer/reviews.json
```

The app backend is intentionally tiny: `review_server.py` serves the exported `docs/` site and exposes the review endpoints.

By default, anyone who can open the site can submit a text comment. Add a password or VPN later if the URL should not be publicly writable.

## Current Server Shape

Observed on `204.168.154.216`:

- SSH user: `apazent`
- Domain: `gurung.duckdns.org`
- Nginx is already active on ports `80` and `443`
- Caddy is inactive
- Certbot is installed
- `apazent` does not currently have passwordless sudo

The review server is designed to run as `apazent` on localhost port `8780`, and Nginx should proxy `gurung.duckdns.org` to it.

## 1. Prepare The Export Locally

From the repo root:

```sh
python3 trial_viewer/export_static.py
```

This refreshes `docs/` with the current UI, `data/datasets.json`, and lightweight WebP images.
By default, image URLs in `datasets.json` are relative `assets/...` paths for GitHub Pages.
To make this optional Hetzner deployment serve images from `https://gurung.duckdns.org/assets/...`,
export with:

```sh
GURUNG_ASSET_BASE_URL="https://gurung.duckdns.org" python3 trial_viewer/export_static.py
```

## 2. Upload The Site And Review Server

From the repo root:

```sh
ssh apazent@204.168.154.216 'mkdir -p /home/apazent/gurung-trial-viewer/site /home/apazent/gurung-trial-viewer/logs'
rsync -av --delete docs/ apazent@204.168.154.216:/home/apazent/gurung-trial-viewer/site/
rsync -av trial_viewer/review_server.py trial_viewer/reviews.py apazent@204.168.154.216:/home/apazent/gurung-trial-viewer/
```

## Fast Picture Updates From The Local Viewer

Dragging a picture onto a local viewer slot saves the PNG to Google Drive, runs:

```sh
python3 trial_viewer/export_static.py
```

and then rsyncs only the live data and image cache:

```sh
rsync -az --delete docs/data/ apazent@204.168.154.216:/home/apazent/gurung-trial-viewer/site/data/
rsync -az --delete docs/assets/ apazent@204.168.154.216:/home/apazent/gurung-trial-viewer/site/assets/
```

This means collaborators see new images on `gurung.duckdns.org` immediately, without waiting for a
Git commit or GitHub Pages deploy. To disable either step while running locally:

```sh
GURUNG_STATIC_EXPORT_ON_UPLOAD=0 ./start.sh
GURUNG_STATIC_PUBLISH_ON_UPLOAD=0 ./start.sh
```

Create `reviews.json` only if it does not exist:

```sh
ssh apazent@204.168.154.216 'test -e /home/apazent/gurung-trial-viewer/reviews.json || printf "{\n  \"version\": 1,\n  \"updatedAt\": \"\",\n  \"reviews\": {}\n}\n" > /home/apazent/gurung-trial-viewer/reviews.json'
```

## 3. Start Or Restart The Review Server

This does not touch other services:

```sh
ssh apazent@204.168.154.216 '
set -eu
if test -f /home/apazent/gurung-trial-viewer/review_server.pid; then
  old_pid=$(cat /home/apazent/gurung-trial-viewer/review_server.pid)
  if kill -0 "$old_pid" 2>/dev/null; then
    kill "$old_pid"
  fi
fi
cd /home/apazent/gurung-trial-viewer
nohup python3 review_server.py \
  --host 0.0.0.0 \
  --port 8780 \
  --site-root /home/apazent/gurung-trial-viewer/site \
  --reviews-file /home/apazent/gurung-trial-viewer/reviews.json \
  > /home/apazent/gurung-trial-viewer/logs/review_server.log 2>&1 &
echo $! > /home/apazent/gurung-trial-viewer/review_server.pid
'
```

Check internally:

```sh
ssh apazent@204.168.154.216 'curl -sS http://127.0.0.1:8780/api/reviews'
```

## 4. Final Nginx And HTTPS Step

This step needs sudo on the server. It is the only global system change.

First copy the prepared vhost file:

```sh
sudo cp /home/apazent/gurung-trial-viewer/nginx-gurung.duckdns.org.conf /etc/nginx/sites-available/gurung.duckdns.org
sudo ln -sf /etc/nginx/sites-available/gurung.duckdns.org /etc/nginx/sites-enabled/gurung.duckdns.org
sudo nginx -t
sudo systemctl reload nginx
```

Then request the certificate and let Certbot edit the vhost:

```sh
sudo certbot --nginx -d gurung.duckdns.org
sudo nginx -t
sudo systemctl reload nginx
```

The prepared Nginx vhost is:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name gurung.duckdns.org;

    client_max_body_size 2M;

    location / {
        proxy_pass http://127.0.0.1:8780;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 5. Check It Publicly

```sh
curl -I https://gurung.duckdns.org/
curl https://gurung.duckdns.org/api/reviews
```

The local viewer defaults to reading remote reviews from:

```text
https://gurung.duckdns.org/api/reviews
```

To override that in your local browser console:

```js
localStorage.setItem("gurungReviewApiBase", "https://gurung.duckdns.org")
```

Then refresh the local viewer.

## 6. Back Up Or Collect Reviews

From your local machine:

```sh
scp apazent@204.168.154.216:/home/apazent/gurung-trial-viewer/reviews.json ./reviews.json
```

The file is grouped by picture key:

```text
dataset:set:stem
```

For example:

```text
12:2:coh_1
```

## 7. Updating Pictures Later

After changing images locally:

```sh
python3 trial_viewer/export_static.py
rsync -av --delete docs/ apazent@204.168.154.216:/home/apazent/gurung-trial-viewer/site/
```

Static file updates do not require restarting the review server.
