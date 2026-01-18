# Clinic Management System - Server Deployment Guide
# Domain: cliniccmsbyzain.cloud
# Server: 72.62.246.73

## Quick Deployment Steps

### 1. SSH into server
```bash
ssh root@72.62.246.73
```

### 2. Install required packages
```bash
apt update && apt upgrade -y
apt install python3 python3-pip python3-venv nginx git -y
```

### 3. Clone/Pull the repository
```bash
cd /var/www
git clone https://github.com/YOUR_USERNAME/clinic-app.git clinic
# OR if already cloned:
cd /var/www/clinic && git pull origin main
```

### 4. Setup Python virtual environment
```bash
cd /var/www/clinic
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_production.txt
```

### 5. Configure Django for production
```bash
export DJANGO_SETTINGS_MODULE=core.settings_production
export DJANGO_SECRET_KEY='your-super-secret-key-here'

python manage.py collectstatic --noinput
python manage.py migrate
```

### 6. Create Gunicorn systemd service
```bash
nano /etc/systemd/system/clinic.service
```

Paste this content:
```ini
[Unit]
Description=Clinic Management System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/clinic
Environment="DJANGO_SETTINGS_MODULE=core.settings_production"
Environment="DJANGO_SECRET_KEY=your-super-secret-key-here"
ExecStart=/var/www/clinic/venv/bin/gunicorn --workers 3 --bind unix:/var/www/clinic/clinic.sock core.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 7. Configure Nginx
```bash
nano /etc/nginx/sites-available/clinic
```

Paste this content:
```nginx
server {
    listen 80;
    server_name cliniccmsbyzain.cloud www.cliniccmsbyzain.cloud;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/clinic/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/clinic/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/clinic/clinic.sock;
    }
}
```

### 8. Enable site and start services
```bash
ln -s /etc/nginx/sites-available/clinic /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
systemctl start clinic
systemctl enable clinic
```

### 9. Set proper permissions
```bash
chown -R www-data:www-data /var/www/clinic
chmod -R 755 /var/www/clinic
```

### 10. (Optional) Setup SSL with Let's Encrypt
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d cliniccmsbyzain.cloud -d www.cliniccmsbyzain.cloud
```

## Updating the App

After pushing changes to GitHub:
```bash
cd /var/www/clinic
git pull origin main
source venv/bin/activate
pip install -r requirements_production.txt
python manage.py collectstatic --noinput
python manage.py migrate
sudo systemctl restart clinic
```

## Useful Commands

- Check service status: `systemctl status clinic`
- View logs: `journalctl -u clinic -f`
- Restart app: `systemctl restart clinic`
- Restart nginx: `systemctl restart nginx`
