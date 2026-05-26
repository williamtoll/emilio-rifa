# Despliegue en producción — VPS Hetzner

Guía para publicar **La Rifa** en un servidor Ubuntu en Hetzner con Docker, Nginx y HTTPS (Let's Encrypt).

## Arquitectura

```
Internet
    │
    ▼
[Nginx en el VPS :443]  ← SSL con Certbot
    │
    ▼
[Docker: frontend :8080]  ← React compilado + proxy /api
    │
    ├──► [Docker: backend :8000]  ← FastAPI
    │
    └──► [Docker: PostgreSQL]  ← solo red interna Docker
```

El puerto **8080** solo escucha en `127.0.0.1` (no expuesto a internet). Nginx del sistema termina SSL y hace proxy.

---

## Requisitos

| Recurso | Mínimo recomendado |
|---------|-------------------|
| VPS Hetzner | CX22 o superior (2 vCPU, 4 GB RAM) |
| SO | Ubuntu 24.04 LTS |
| Dominio | Apuntando al IP del VPS (registro A) |

---

## 1. Crear el VPS en Hetzner

1. Entrá a [Hetzner Cloud Console](https://console.hetzner.cloud/).
2. **Add Server** → ubicación cercana (ej. Falkenstein o Ashburn).
3. Imagen: **Ubuntu 24.04**.
4. Tipo: **CX22** (suficiente para esta app).
5. SSH key: agregá tu clave pública (recomendado).
6. Creá el servidor y anotá la **IP pública**.

### DNS del dominio

En tu proveedor de dominio, creá un registro **A**:

| Tipo | Nombre | Valor |
|------|--------|-------|
| A | `rifa` (o `@`) | `IP_DEL_VPS` |

Ejemplo: `rifa.tudominio.com` → `123.45.67.89`

---

## 2. Acceso inicial y seguridad

```bash
ssh root@IP_DEL_VPS
```

### Usuario no-root (recomendado)

```bash
adduser deploy
usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

Salí y volvé a entrar:

```bash
ssh deploy@IP_DEL_VPS
```

### Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 3. Instalar Docker

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Cerrá sesión y volvé a entrar para aplicar el grupo `docker`.

Verificá:

```bash
docker --version
docker compose version
```

---

## 4. Clonar el proyecto

```bash
cd ~
git clone https://github.com/TU_USUARIO/emilio-rifa.git larifa
cd larifa
```

(Reemplazá la URL por tu repositorio real.)

---

## 5. Configurar variables de entorno

```bash
cp .env.production.example .env
nano .env
```

**Obligatorio cambiar en producción:**

| Variable | Descripción |
|----------|-------------|
| `POSTGRES_PASSWORD` | Contraseña fuerte de la base de datos |
| `ADMIN_PASSWORD` | Contraseña del panel de administración |
| `JWT_SECRET` | Secreto aleatorio largo |
| `CORS_ORIGINS` | Tu dominio con `https://` |
| `APP_BASE_URL` | Mismo dominio con `https://` |

Generar `JWT_SECRET`:

```bash
openssl rand -hex 32
```

Ejemplo de `.env`:

```env
APP_BASE_URL=https://rifa.tudominio.com
CORS_ORIGINS=https://rifa.tudominio.com
POSTGRES_USER=sorteos
POSTGRES_PASSWORD=una_clave_muy_segura_123
POSTGRES_DB=sorteos_db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=otra_clave_muy_segura
JWT_SECRET=a1b2c3d4e5f6...
JWT_EXPIRE_MINUTES=1440
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=app_password_gmail
SMTP_FROM=La Rifa <tu_correo@gmail.com>
```

Protegé el archivo:

```bash
chmod 600 .env
```

---

## 6. Levantar la aplicación

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Verificá que todo esté corriendo:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

Prueba local en el servidor:

```bash
curl -s http://127.0.0.1:8080/api/health
# Debe responder: {"status":"ok"}
```

---

## 7. Nginx + HTTPS (Certbot)

### Instalar Nginx y Certbot

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Configurar el sitio

```bash
sudo cp deploy/nginx-larifa.conf.example /etc/nginx/sites-available/larifa
sudo nano /etc/nginx/sites-available/larifa
```

Cambiá `rifa.tudominio.com` por tu dominio real.

```bash
sudo ln -s /etc/nginx/sites-available/larifa /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### Certificado SSL

```bash
sudo certbot --nginx -d rifa.tudominio.com
```

Seguí las preguntas (email, aceptar términos, redirigir HTTP → HTTPS).

Renovación automática (ya viene configurada):

```bash
sudo certbot renew --dry-run
```

---

## 8. Verificar en producción

1. Abrí `https://rifa.tudominio.com`
2. Iniciá sesión con `ADMIN_USERNAME` / `ADMIN_PASSWORD`
3. Creá un sorteo de prueba y un ticket
4. Probá WhatsApp y la imagen del ticket con QR

---

## 9. Comandos útiles

### Ver logs

```bash
cd ~/larifa
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Actualizar después de un `git pull`

```bash
cd ~/larifa
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

### Reiniciar servicios

```bash
docker compose -f docker-compose.prod.yml restart
```

### Detener todo

```bash
docker compose -f docker-compose.prod.yml down
```

---

## 10. Backup de PostgreSQL

Script manual de respaldo:

```bash
cd ~/larifa
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U sorteos sorteos_db > backup_$(date +%Y%m%d).sql
```

Restaurar:

```bash
cat backup_20260526.sql | docker compose -f docker-compose.prod.yml exec -T db \
  psql -U sorteos sorteos_db
```

### Backup automático diario (cron)

```bash
mkdir -p ~/backups
crontab -e
```

Agregá:

```cron
0 3 * * * cd /home/deploy/larifa && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U sorteos sorteos_db > /home/deploy/backups/larifa_$(date +\%Y\%m\%d).sql
```

---

## 11. Checklist de seguridad

- [ ] Cambiar `ADMIN_PASSWORD` y `POSTGRES_PASSWORD` por defecto
- [ ] `JWT_SECRET` único y largo (32+ caracteres)
- [ ] `.env` con permisos `600`
- [ ] Firewall: solo SSH, 80 y 443
- [ ] PostgreSQL **no** expuesto al exterior (sin puerto público en `docker-compose.prod.yml`)
- [ ] HTTPS activo con Certbot
- [ ] Acceso SSH solo con clave (deshabilitar password si es posible)

---

## Solución de problemas

### `502 Bad Gateway` en Nginx

```bash
curl http://127.0.0.1:8080/api/health
docker compose -f docker-compose.prod.yml ps
```

Si el frontend no está arriba, revisá logs: `docker compose -f docker-compose.prod.yml logs frontend`.

### Error CORS en el navegador

`CORS_ORIGINS` en `.env` debe coincidir **exactamente** con la URL del navegador (incluyendo `https://` y sin barra final).

```env
CORS_ORIGINS=https://rifa.tudominio.com
```

Reiniciá el backend después de cambiar `.env`:

```bash
docker compose -f docker-compose.prod.yml up -d --build backend
```

### No envía correos

Verificá `SMTP_*` en `.env` y que Gmail tenga contraseña de aplicación activa.

### Certbot falla

- El dominio debe apuntar al IP del VPS antes de ejecutar certbot.
- El puerto 80 debe estar abierto: `sudo ufw allow 'Nginx Full'`.

---

## Costos estimados (Hetzner)

| Recurso | Costo aprox. |
|---------|----------------|
| CX22 | ~€5–6 / mes |
| Dominio | según registrador |
| SSL | gratis (Let's Encrypt) |

---

## Resumen rápido

```bash
# En el VPS (una vez configurado Docker y el repo)
cp .env.production.example .env && nano .env
docker compose -f docker-compose.prod.yml up -d --build
sudo cp deploy/nginx-larifa.conf.example /etc/nginx/sites-available/larifa
# editar dominio, habilitar sitio, certbot --nginx
```

Listo: **La Rifa** en producción en tu VPS Hetzner.
