# La Rifa

Aplicación para gestionar sorteos, generar tickets y enviarlos por WhatsApp o correo electrónico.

## Características

- **Sorteos agrupados** con nombre (ej: "Día de la madre"), descripción y precio por ticket
- **Generación automática** de números de ticket secuenciales (0001, 0002, …)
- **Estado de pago** por ticket (pagado / pendiente)
- **Envío por WhatsApp** mediante enlace `wa.me` con el mensaje del ticket prellenado
- **Envío por correo** con plantilla HTML (requiere configuración SMTP)

## Stack

| Capa       | Tecnología              |
|------------|-------------------------|
| Backend    | Python 3.12 + FastAPI   |
| Frontend   | React 18 + Vite         |
| Base datos | PostgreSQL 16           |

## Inicio rápido con Docker

```bash
cp .env.example .env
# Edita .env con tus credenciales SMTP si quieres enviar correos

docker compose up --build
```

- **Frontend:** http://localhost:5173
- **API:** http://localhost:8000/docs

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
| GET | `/api/raffles` | Listar sorteos |
| POST | `/api/raffles` | Crear sorteo |
| GET | `/api/tickets?raffle_id=1` | Tickets de un sorteo |
| POST | `/api/tickets` | Generar ticket |
| POST | `/api/tickets/{id}/mark-paid` | Marcar como pagado |
| POST | `/api/tickets/{id}/send-email` | Enviar por correo |
| GET | `/api/tickets/{id}/whatsapp-link` | Obtener enlace WhatsApp |

## WhatsApp

El botón **WhatsApp** abre WhatsApp Web/App con el mensaje del ticket listo para enviar al número registrado. No requiere API de pago; usa el formato estándar `https://wa.me/52XXXXXXXXXX`.

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
├── docker-compose.yml
└── README.md
```
