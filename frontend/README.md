# La Rifa — Frontend

Interfaz web de **La Rifa**: gestión de sorteos para el organizador y flujo de compra público para los clientes. Construida con **React 18** y **Vite**.

## Rutas

| Ruta | Acceso | Descripción |
|------|--------|-------------|
| `/` | Admin (login) | Panel de gestión de sorteos y tickets |
| `/comprar` | Público | Listado de sorteos disponibles |
| `/comprar/{id}` | Público | Elegir número y reservar ticket |
| `/comprobante/{public_id}` | Público | Subir comprobante de pago |
| `/t/{public_id}` | Público | Ver ticket pagado (imagen + premios) |

Las rutas públicas no requieren autenticación. El panel admin usa JWT guardado en el navegador.

---

## Funcionalidades públicas (clientes)

### Elegir y reservar un ticket (`/comprar`)

- Listado de sorteos activos con imagen, precio y cantidad de números disponibles.
- Al entrar a un sorteo, el cliente ve:
  - Imagen, descripción y premios del sorteo.
  - Grilla de números (0001–9999 según configuración del sorteo).
  - Búsqueda por número y filtro “solo disponibles”.
  - Números ya tomados deshabilitados en tiempo real.
- Formulario con nombre, teléfono móvil (Paraguay) y correo opcional.
- Tras reservar, muestra confirmación con el número elegido y enlace para enviar el comprobante.

### Subir comprobante de pago (`/comprobante/{public_id}`)

- Pantalla accesible después de reservar o con el enlace único del ticket.
- Muestra datos de la reserva: sorteo, número, nombre y monto.
- Permite subir una imagen (JPG, PNG, WEBP, GIF) o PDF (máx. 5 MB).
- Vista previa del archivo antes de enviar.
- Si ya se envió un comprobante, se puede ver y reemplazar hasta que el organizador confirme el pago.
- Cuando el ticket ya está marcado como pagado, la pantalla indica que el pago fue confirmado.

### Ver ticket pagado (`/t/{public_id}`)

- Muestra la imagen PNG del ticket generada por el sistema.
- Datos del participante, precio y lista de premios del sorteo.
- Opción de compartir el ticket en Facebook e Instagram.

### Compartir sorteo en redes

- En la página de compra y en el listado de sorteos hay una sección **Compartir sorteo**.
- Enlace directo a `/comprar/{id}` para que otros ingresen y elijan su número.
- Botón **Copiar** enlace.
- **Facebook**: abre el diálogo de compartir con el enlace de compra.
- **Instagram**: copia el texto con el enlace (y descarga la imagen del sorteo si existe). Instagram no permite publicar links directamente desde el navegador; el usuario pega el texto en historia, bio o mensaje.

---

## Panel de administración

Requiere iniciar sesión con usuario y contraseña configurados en el backend.

### Sorteos

- Crear, editar y listar sorteos desde la barra lateral.
- Campos: nombre, descripción, precio por ticket, cantidad máxima de tickets, estado activo/inactivo.
- Imagen del sorteo (aparece en el ticket PNG y en la página pública de compra).
- Contador de tickets vendidos y pagados por sorteo.

### Premios

- Gestionar premios por sorteo: nombre, descripción, orden e imagen.
- Los premios aparecen en el ticket PNG y en la vista pública del ticket.

### Tickets

- Generar tickets manualmente desde el panel (asignación automática de número).
- Marcar como **pagado** o **pendiente**.
- Ver comprobante de pago enviado por el cliente (tickets pendientes con comprobante).
- Ver imagen del ticket, descargar y compartir (nativo, Facebook, Instagram).
- Enviar ticket por **WhatsApp** (enlace `wa.me` con mensaje prellenado al teléfono del comprador).
- Enviar ticket por **correo** (requiere SMTP configurado en el backend).
- Copiar enlace público corto del ticket pagado.

### Compra pública (enlace para clientes)

- En sorteos activos, sección **Compartir sorteo** con enlace `/comprar/{id}`.
- Mismos botones de Facebook, Instagram y copiar enlace que en la página pública.

### Sorteo en vivo (`Sortear`)

- Vista a pantalla completa pensada para grabar o proyectar el sorteo.
- Un premio a la vez, en orden descendente (mayor premio primero).
- Animación de números aleatorios antes de revelar el ganador.
- No repite ganadores ya sorteados.
- Historial de resultados sorteados.
- Deshacer el último premio sorteado o reiniciar todo el sorteo.
- **Cerrar sorteo** de forma definitiva (bloquea nuevos sorteos y cambios).

---

## Estructura del código

```
src/
├── Root.jsx              # Enrutamiento por pathname (público vs admin)
├── App.jsx               # Layout admin: tickets / sortear
├── api.js                # Cliente HTTP hacia /api
├── pages/
│   ├── PublicBuyPage.jsx       # Compra pública
│   ├── PublicPaymentPage.jsx   # Comprobante de pago
│   └── PublicTicketPage.jsx    # Ticket pagado
├── components/
│   ├── LoginPage.jsx
│   ├── RaffleSidebar.jsx       # CRUD sorteos
│   ├── TicketPanel.jsx         # Tickets + premios + enlace compra
│   ├── TicketCard.jsx
│   ├── DrawView.jsx            # Sorteo en vivo
│   ├── PrizesManager.jsx
│   ├── RaffleShareSection.jsx  # Compartir sorteo
│   ├── SocialShareButtons.jsx  # Facebook / Instagram
│   └── PaymentProofModal.jsx   # Ver comprobante (admin)
└── utils/
    ├── socialShare.js    # URLs y texto para compartir
    ├── clipboard.js      # Copiar al portapapeles (con fallback HTTP)
    ├── shareTicket.js    # Compartir imagen del ticket
    ├── currency.js       # Formato guaraníes
    └── phone.js          # Validación teléfono Paraguay
```

---

## Desarrollo local

```bash
cd frontend
npm install
npm run dev
```

El servidor de desarrollo corre en **http://localhost:5173** y hace proxy de `/api` al backend (ver `vite.config.js`).

```bash
npm run build   # Genera dist/ para producción
```

En producción, Nginx sirve `dist/` y proxea `/api`, `/uploads` y `/s` al backend.
