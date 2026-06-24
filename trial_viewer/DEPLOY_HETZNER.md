# Hetzner Review Site Deployment

This deployment serves the exported viewer at `https://gurung.duckdns.org` and stores picture comments in one JSON file:

```text
/var/lib/gurung-trial-viewer/reviews.json
```

The site backend is intentionally tiny: `review_server.py` serves `docs/` and exposes `GET/POST /api/reviews`.

By default, anyone who can open the site can submit a text comment. Add a password or VPN later if the URL should not be publicly writable.

## 1. Prepare The Export Locally

From the repo root:

```sh
python3 trial_viewer/export_static.py
```

This refreshes `docs/` with the current UI, `data/datasets.json`, and lightweight WebP images.

## 2. Prepare The Ubuntu Server

Replace `YOUR_USER` with your SSH username.

```sh
ssh YOUR_USER@204.168.154.216
sudo apt update
sudo apt install -y python3 caddy rsync
sudo mkdir -p /opt/gurung-trial-viewer/site /var/lib/gurung-trial-viewer
sudo chown -R YOUR_USER:YOUR_USER /opt/gurung-trial-viewer /var/lib/gurung-trial-viewer
sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw enable
exit
```

Make sure DuckDNS points `gurung.duckdns.org` to:

```text
204.168.154.216
```

## 3. Upload The Site And Review Server

From the repo root:

```sh
rsync -av --delete docs/ YOUR_USER@204.168.154.216:/opt/gurung-trial-viewer/site/
rsync -av trial_viewer/review_server.py trial_viewer/reviews.py YOUR_USER@204.168.154.216:/opt/gurung-trial-viewer/
```

## 4. Install The Systemd Service

On the server:

```sh
ssh YOUR_USER@204.168.154.216
sudo tee /etc/systemd/system/gurung-review.service >/dev/null <<'EOF'
[Unit]
Description=Gurung picture review site
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/opt/gurung-trial-viewer
Environment=GURUNG_SITE_ROOT=/opt/gurung-trial-viewer/site
Environment=GURUNG_REVIEWS_FILE=/var/lib/gurung-trial-viewer/reviews.json
ExecStart=/usr/bin/python3 /opt/gurung-trial-viewer/review_server.py --host 127.0.0.1 --port 8780
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
sudo sed -i 's/User=YOUR_USER/User='"$USER"'/g' /etc/systemd/system/gurung-review.service
sudo systemctl daemon-reload
sudo systemctl enable --now gurung-review
```

## 5. Configure Caddy

On the server:

```sh
sudo tee /etc/caddy/Caddyfile >/dev/null <<'EOF'
gurung.duckdns.org {
    reverse_proxy 127.0.0.1:8780
}
EOF
sudo systemctl reload caddy
```

Caddy will request HTTPS certificates automatically once DNS points to the server and ports 80/443 are reachable.

## 6. Check It

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

## 7. Back Up Or Collect Reviews

From your local machine:

```sh
scp YOUR_USER@204.168.154.216:/var/lib/gurung-trial-viewer/reviews.json ./reviews.json
```

The file is grouped by picture key:

```text
dataset:set:stem
```

For example:

```text
12:2:coh_1
```

## 8. Updating Pictures Later

After changing images locally:

```sh
python3 trial_viewer/export_static.py
rsync -av --delete docs/ YOUR_USER@204.168.154.216:/opt/gurung-trial-viewer/site/
```

Then, on the server:

```sh
ssh YOUR_USER@204.168.154.216
sudo systemctl restart gurung-review
exit
```

The restart is optional for static files, but it is harmless and keeps the process fresh.
