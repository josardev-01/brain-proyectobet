# Despliegue en Oracle Cloud

Objetivo: ejecutar PostgreSQL, FastAPI, Next.js, el entregador Telegram y Caddy con HTTPS en una instancia Ubuntu ARM64. Solamente Caddy publica puertos; PostgreSQL, API y web permanecen en la red interna de Docker.

## Requisitos

- Una instancia Ubuntu con Docker Engine, Compose y Git.
- Reglas de entrada TCP para `80` y `443`; restringir `22` a la IP del administrador cuando sea posible.
- Un dominio o subdominio cuyo registro `A` apunte a la IPv4 pública de la instancia.
- `API_FOOTBALL_KEY`, `TELEGRAM_BOT_TOKEN`, `JWT_SECRET` y contraseña PostgreSQL.

No se debe publicar `5432`, `8000` ni `3000` en la VCN ni en el firewall del host.

## Instalación

```bash
git clone https://github.com/josardev-01/brain-proyectobet.git
cd brain-proyectobet
cp .env.production.example .env.production
chmod 600 .env.production
```

Editar `.env.production` y reemplazar todos los valores. Para generar secretos compatibles con una URL:

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

El valor de `APP_DOMAIN` no incluye `https://`. Ejemplo: `alertas.example.com`.

## Inicio y verificación

```bash
docker compose --env-file .env.production -f compose.production.yaml up -d --build
docker compose --env-file .env.production -f compose.production.yaml ps
curl --fail https://DOMINIO/health
curl --fail https://DOMINIO/ready
```

Caddy solicita y renueva automáticamente el certificado cuando el DNS y los puertos `80/443` son accesibles.

## Administrador inicial

```bash
docker compose --env-file .env.production -f compose.production.yaml run --rm api \
  python backend/scripts/bootstrap_admin.py \
  --email mendez.josar87@gmail.com \
  --display-name Administrador \
  --telegram-chat-id 1631763640
```

La contraseña se solicita dos veces sin mostrarse. Después se puede iniciar sesión y aprobar solicitudes desde **Cuenta**.

## Actualizaciones

```bash
git pull --ff-only
docker compose --env-file .env.production -f compose.production.yaml up -d --build
```

Las migraciones Alembic se ejecutan al iniciar el contenedor API. Antes de cambios relevantes se debe respaldar el volumen PostgreSQL.
