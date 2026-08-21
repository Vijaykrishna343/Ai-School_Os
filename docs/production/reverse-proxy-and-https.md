# Production Reverse Proxy, TLS, and HTTPS Configuration Guide

**Project**: AI School OS / School ERP  
**Architecture Topology**:  
Client → Cloudflare / AWS ALB → NGINX Reverse Proxy (Port 443 TLS) → FastAPI Uvicorn (Port 8000)

---

## 1. NGINX Reverse Proxy Configuration (`/etc/nginx/sites-available/school_erp.conf`)

```nginx
server {
    listen 80;
    server_name app.schoolos.com api.schoolos.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.schoolos.com api.schoolos.com;

    ssl_certificate /etc/letsencrypt/live/app.schoolos.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.schoolos.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # HSTS & Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend Static Assets
    location / {
        root /var/www/school-erp/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # FastAPI Backend Reverse Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Request Size Limit
        client_max_body_size 15M;
    }
}
```

---

## 2. Trusted Proxy Configuration in FastAPI (`TRUST_PROXY=True`)

When running behind NGINX or ALB, set `TRUST_PROXY=True` in production environment variables so FastAPI and `InMemoryRateLimiter` extract client IP from `X-Forwarded-For`.
