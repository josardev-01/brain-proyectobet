# Proyecto Bet — Motor de estadísticas de fútbol

Sistema para analizar partidos de fútbol en vivo, evaluar reglas configurables y generar alertas explicables cuando se cumplan condiciones estadísticas.

## Estado

MVP integrado en desarrollo: adquisición y reglas operativas, base SQL versionada, API REST y dashboard Next.js. La heurística deportiva sigue pendiente de validación; esto no bloquea el desarrollo de producto.

## Próximo hito

Completar autenticación, administración multiusuario y ejecución de más tipos de objetivo mientras el worker reúne la muestra necesaria para medir:

- cobertura y estadísticas disponibles;
- frecuencia de actualización y latencia;
- disponibilidad de cuotas pre-partido;
- estabilidad de identificadores;
- límites y coste;
- capacidad de reconstruir ventanas temporales.

No se considera validada ninguna fórmula o regla hasta evaluarla mediante datos históricos y backtesting.

## Documentación del proyecto

- [`CEREBRO_ESTADISTICAS_FUTBOL.md`](CEREBRO_ESTADISTICAS_FUTBOL.md): principios, decisiones y dirección del producto.
- [`DECISION_LOG.md`](DECISION_LOG.md): decisiones duraderas y su contexto.
- [`ARQUITECTURA.md`](ARQUITECTURA.md): componentes y límites del MVP.
- [`MODELO_DATOS.md`](MODELO_DATOS.md): tablas e invariantes de persistencia.
- [`.agents/skills/football-live-statistics/SKILL.md`](.agents/skills/football-live-statistics/SKILL.md): habilidad local para aplicar esos criterios durante el desarrollo.

## Stack previsto

- Backend: Python y FastAPI.
- Base de datos: PostgreSQL.
- Frontend: Next.js y TypeScript, decisión provisional.
- Notificaciones iniciales: Telegram.

La implementación crecerá de manera incremental. API-Football es el proveedor operativo del spike; su adopción definitiva sigue pendiente de medir cobertura, latencia y coste con partidos reales.

## Spike de proveedores

El contrato extensible del objetivo inicial y los clientes exploratorios están documentados en [`docs/PROVIDER_SPIKE.md`](docs/PROVIDER_SPIKE.md).

Flujo actual:

```powershell
$env:PYTHONPATH = "src"
python scripts/discover_candidates.py --date AAAA-MM-DD
python scripts/monitor_candidates.py --cycles 1
python scripts/run_matchday.py --registry data/raw/eligible/AAAA-MM-DD.json --dry-run
python scripts/finalize_matches.py --registry data/raw/eligible/AAAA-MM-DD.json
python scripts/summarize_backtests.py
python scripts/audit_data_quality.py
python scripts/audit_scenario_exposure.py --registry data/raw/eligible/AAAA-MM-DD.json
python scripts/send_pending_alerts.py --dry-run
python scripts/send_database_alerts.py --maximum 20
```

El flujo descubre favoritos claros, monitorea únicamente los escenarios relevantes, finaliza partidos con eventos exactos, registra resultados para backtesting y conserva las alertas en una bandeja entregable por Telegram.

`run_matchday.py` es el ejecutor persistente y reiniciable. Empieza a consultar en el minuto 35 para llegar con línea base al minuto 45, agrupa partidos solapados en una sola ventana, consulta cada diez minutos y finaliza la jornada tres horas después del último comienzo. Diez minutos conserva el intervalo temporal exacto que evalúa la heurística y deja margen suficiente en la cuota actual; puede ajustarse con `--interval-seconds`. `--dry-run` permite revisar el horario sin consumir cuota y `--once` ejecuta solo la acción que corresponde al momento actual, útil para un programador externo.

La definición activa está en [`config/strategies/favorite_losing_pressure_v2.json`](config/strategies/favorite_losing_pressure_v2.json). Los comandos aceptan `--strategy` para ejecutar otra versión sin modificar el motor.

## Aplicación local

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\alembic upgrade head
$env:PYTHONPATH = "src"
.\.venv\Scripts\python scripts\sync_database.py
.\.venv\Scripts\uvicorn brain_projectbet.api.main:app --reload
```

En otra terminal:

```powershell
cd frontend
pnpm install
pnpm dev
```

API: `http://localhost:8000`, documentación OpenAPI: `http://localhost:8000/docs`, frontend: `http://localhost:3000`.

Cada usuario puede registrar uno o más `chat_id` de Telegram desde **Cuenta**. El token del bot es global y permanece en `TELEGRAM_BOT_TOKEN`; `send_database_alerts.py` entrega cada alerta una sola vez por destino y conserva los reintentos en la base.

Con Docker instalado, `docker compose up --build` inicia PostgreSQL, API y web. SQLite (`data/projectbet.db`) es únicamente el valor predeterminado local.

Cada push y pull request ejecuta en GitHub Actions las pruebas del backend, verifica las migraciones, comprueba TypeScript y compila el frontend.
