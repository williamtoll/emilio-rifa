# La Rifa

Aplicación para gestionar sorteos, generar tickets y enviarlos por WhatsApp o correo electrónico.

## Características

- **Sorteos agrupados** con nombre (ej: "Día de la madre"), descripción y precio por ticket
- **Generación automática** de números de ticket secuenciales (0001, 0002, …)
- **Estado de pago** por ticket (pagado / pendiente)
- **Envío por WhatsApp** mediante enlace `wa.me` con el mensaje del ticket prellenado
- **Envío por correo** con plantilla HTML (requiere configuración SMTP)
- **Autenticación** con usuario/contraseña y token JWT

## Stack

| Capa       | Tecnología              |
|------------|-------------------------|
| Backend    | Python 3.12 + FastAPI   |
| Frontend   | React 18 + Vite         |
| Base datos | PostgreSQL 16           |

## Despliegue en producción (VPS Hetzner)

Guía completa paso a paso: **[DEPLOY-HETZNER.md](./DEPLOY-HETZNER.md)**

Incluye: Docker en Ubuntu, Nginx, HTTPS con Certbot, variables de entorno, backups y checklist de seguridad.

Resumen:

```bash
cp .env.production.example .env   # editar contraseñas y dominio
docker compose -f docker-compose.prod.yml up -d --build
# Configurar Nginx + certbot en el VPS (ver guía)
```

## Inicio rápido con Docker (desarrollo)

```bash
cp .env.example .env
# Edita .env con tus credenciales SMTP si quieres enviar correos

docker compose up --build
```

- **Frontend:** http://localhost:5173
- **API:** http://localhost:8000/docs

Credenciales por defecto: `admin` / `admin123` (configúralas en `.env`).

## Autenticación

Todas las rutas de la API (excepto `/api/health` y `/api/auth/login`) requieren un token JWT.

Variables en `.env`:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=tu_contraseña_segura
JWT_SECRET=un-secreto-largo-y-aleatorio
JWT_EXPIRE_MINUTES=1440
```

## Desarrollo local (sin Docker)

### 1. Base de datos

```bash
docker compose up db -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuración de correo (Gmail)

1. Activa verificación en 2 pasos en tu cuenta Google.
2. Crea una **contraseña de aplicación** en https://myaccount.google.com/apppasswords
3. Configura en `.env`:

```
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM=La Rifa <tu_correo@gmail.com>
```

## API principal

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/login` | Iniciar sesión |
| GET | `/api/auth/me` | Usuario actual (requiere token) |
| GET | `/api/raffles` | Listar sorteos |
| POST | `/api/raffles` | Crear sorteo |
| GET | `/api/tickets?raffle_id=1` | Tickets de un sorteo |
| POST | `/api/tickets` | Generar ticket |
| POST | `/api/tickets/{id}/mark-paid` | Marcar como pagado |
| POST | `/api/tickets/{id}/send-email` | Enviar por correo |
| GET | `/api/tickets/{id}/whatsapp-link` | Obtener enlace WhatsApp |

## WhatsApp

El botón **WhatsApp** abre WhatsApp Web/App con el mensaje del ticket listo para enviar al número registrado. Usa números de Paraguay (`09XXXXXXXX` → `+595` en el enlace `wa.me`).

## Estructura del proyecto

```
emilio-sorteos/
├── backend/
│   └── app/
│       ├── main.py
│       ├── models.py
│       ├── routers/
│       └── services/
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
├── docker-compose.yml          # desarrollo local
├── docker-compose.prod.yml   # producción en VPS
├── deploy/                     # configuración Nginx ejemplo
├── DEPLOY-HETZNER.md           # guía de despliegue
└── README.md
```
