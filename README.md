# Proyecto Bet — Motor de estadísticas de fútbol

Sistema para analizar partidos de fútbol en vivo, evaluar reglas configurables y generar alertas explicables cuando se cumplan condiciones estadísticas.

## Estructura del repositorio

```text
backend/             API, dominio, proveedores, workers, migraciones y pruebas
data/                Capturas y artefactos operativos locales, ignorados por Git
deploy/caddy/        Entrada HTTPS para producción
docs/                Cerebro, arquitectura, modelo de datos y guías
frontend/            Aplicación Next.js
.agents/skills/      Habilidades especializadas reutilizables
compose.yaml         Entorno local
compose.production.yaml  Entorno de producción
```

La raíz conserva únicamente coordinación, configuración de entornos y documentación de entrada. `data/` permanece fuera de `backend/` porque es un volumen operativo compartido por los workers y Docker, no código fuente.

## Estado

MVP integrado en desarrollo: adquisición y reglas operativas, base SQL versionada, API REST, autenticación multiusuario, estrategias declarativas, entregas Telegram y dashboard Next.js. La heurística deportiva sigue pendiente de validación; esto no bloquea el desarrollo de producto.

## Próximo hito

Validar el despliegue completo con PostgreSQL y conectar el primer canal Telegram mientras el worker reúne la muestra necesaria para medir:

- cobertura y estadísticas disponibles;
- frecuencia de actualización y latencia;
- disponibilidad de cuotas pre-partido;
- estabilidad de identificadores;
- límites y coste;
- capacidad de reconstruir ventanas temporales.

No se considera validada ninguna fórmula o regla hasta evaluarla mediante datos históricos y backtesting.

## Documentación del proyecto

- [`docs/CEREBRO_ESTADISTICAS_FUTBOL.md`](docs/CEREBRO_ESTADISTICAS_FUTBOL.md): principios, decisiones y dirección del producto.
- [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md): decisiones duraderas y su contexto.
- [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md): componentes y límites del MVP.
- [`docs/MODELO_DATOS.md`](docs/MODELO_DATOS.md): tablas e invariantes de persistencia.
- [`docs/DEPLOY_ORACLE.md`](docs/DEPLOY_ORACLE.md): despliegue seguro con Docker y HTTPS en Oracle Cloud.
- [`.agents/skills/football-live-statistics/SKILL.md`](.agents/skills/football-live-statistics/SKILL.md): habilidad local para aplicar esos criterios durante el desarrollo.
- [`.agents/skills/project-architecture-auditor/SKILL.md`](.agents/skills/project-architecture-auditor/SKILL.md): auditoría de límites, dependencias y flujo del sistema.
- [`.agents/skills/project-testing-engineer/SKILL.md`](.agents/skills/project-testing-engineer/SKILL.md): diseño y ejecución de pruebas por riesgo.
- [`.agents/skills/project-quality-auditor/SKILL.md`](.agents/skills/project-quality-auditor/SKILL.md): control de calidad y preparación de entrega.

## Stack previsto

- Backend: Python y FastAPI.
- Base de datos: PostgreSQL.
- Frontend: Next.js y TypeScript, decisión provisional.
- Notificaciones iniciales: Telegram.

La implementación crecerá de manera incremental. API-Football aporta
actualmente las cuotas pre-partido. APIFootball.com aporta el reloj y las
estadísticas live mediante un adaptador normalizado; GOAL API se mantiene como
respaldo experimental. Los IDs externos se reconcilian antes de guardar un
snapshot y una coincidencia ambigua se rechaza.

## Spike de proveedores

El contrato extensible del objetivo inicial y los clientes exploratorios están documentados en [`docs/PROVIDER_SPIKE.md`](docs/PROVIDER_SPIKE.md).

Flujo actual:

```powershell
$env:PYTHONPATH = "backend/src"
python backend/scripts/discover_candidates.py --date AAAA-MM-DD
python backend/scripts/reconcile_live_providers.py --registry data/raw/eligible/AAAA-MM-DD.json
python backend/scripts/reconcile_live_providers.py --registry data/raw/eligible/AAAA-MM-DD.json --write-snapshots
python backend/scripts/monitor_hybrid_candidates.py --registry data/raw/eligible/AAAA-MM-DD.json --cycles 1
python backend/scripts/monitor_candidates.py --cycles 1
python backend/scripts/run_matchday.py --registry data/raw/eligible/AAAA-MM-DD.json --dry-run
python backend/scripts/finalize_matches.py --registry data/raw/eligible/AAAA-MM-DD.json
python backend/scripts/summarize_backtests.py
python backend/scripts/audit_data_quality.py
python backend/scripts/audit_scenario_exposure.py --registry data/raw/eligible/AAAA-MM-DD.json
python backend/scripts/send_pending_alerts.py --dry-run
python backend/scripts/send_database_alerts.py --maximum 20
```

El flujo descubre favoritos claros, monitorea únicamente los escenarios relevantes, finaliza partidos con eventos exactos, registra resultados para backtesting y conserva las alertas en una bandeja entregable por Telegram.

El descubrimiento enriquece cada candidato con nombres e IDs de equipos usando
el catálogo de fixtures de API-Football. `reconcile_live_providers.py` compara
esos nombres con APIFootball.com. Sin `--write-snapshots` solo informa el cruce;
la escritura explícita conserva el ID canónico de API-Football y registra el
proveedor e ID de origen dentro de la metadata.

`run_matchday.py` es el ejecutor persistente y reiniciable. Empieza a consultar en el minuto 35 para llegar con línea base al minuto 45, agrupa partidos solapados en una sola ventana, consulta cada diez minutos y finaliza la jornada tres horas después del último comienzo. Diez minutos conserva el intervalo temporal exacto que evalúa la heurística y deja margen suficiente en la cuota actual; puede ajustarse con `--interval-seconds`. `--dry-run` permite revisar el horario sin consumir cuota y `--once` ejecuta solo la acción que corresponde al momento actual, útil para un programador externo.

Por defecto `run_matchday.py` usa APIFootball.com para el reloj y las
estadísticas live, sin consumir API-Football en cada ciclo. `--live-provider
api-football` conserva el monitor anterior como respaldo. Docker incluye el
servicio `monitor`: crea el registro diario si falta, observa cada 120 segundos
dentro de las ventanas, sincroniza PostgreSQL y ejecuta la finalización para
alimentar backtesting. El `notifier` entrega a Telegram las alertas persistidas.

La definición activa está en [`backend/config/strategies/favorite_losing_pressure_v2.json`](backend/config/strategies/favorite_losing_pressure_v2.json). Los comandos aceptan `--strategy` para ejecutar otra versión sin modificar el motor.

## Aplicación local

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".\backend[dev]"
.\.venv\Scripts\alembic -c backend\alembic.ini upgrade head
$env:PYTHONPATH = "backend/src"
.\.venv\Scripts\python backend\scripts\sync_database.py
.\.venv\Scripts\uvicorn brain_projectbet.api.main:app --reload
```

En otra terminal:

```powershell
cd frontend
pnpm install
pnpm dev
```

API: `http://localhost:8000`, documentación OpenAPI: `http://localhost:8000/docs`, frontend: `http://localhost:3000`.

Cada usuario aprobado puede registrar uno o más `chat_id` de Telegram desde **Cuenta**. El token del bot es global y permanece en `TELEGRAM_BOT_TOKEN`; `send_database_alerts.py` entrega cada alerta una sola vez por destino y conserva los reintentos en la base.

El registro público crea solicitudes pendientes. El administrador inicial se crea o promueve de forma interactiva, sin exponer su contraseña:

```powershell
$env:PYTHONPATH = "backend/src"
.\.venv\Scripts\python backend\scripts\bootstrap_admin.py --email administrador@ejemplo.com --display-name "Administrador" --telegram-chat-id 123456789
```

Con Docker instalado, `docker compose up --build` inicia PostgreSQL, API y web. SQLite (`data/projectbet.db`) es únicamente el valor predeterminado local.

El constructor de estrategias para usuarios registrados se encuentra en
**Estrategias**. Permite objetivo, horizonte, alcance por liga/país, ventanas de
5/10/15 minutos, condiciones múltiples y contenido de la alerta. Consulta
[`docs/STRATEGY_BUILDER.md`](docs/STRATEGY_BUILDER.md) para el contrato y sus
límites actuales.

Las métricas se eligen por local/visitante y el periodo total/últimos N minutos se
configura por separado. Las estrategias activas de cada usuario generan alertas privadas
dirigidas únicamente a sus endpoints Telegram.

Cada push y pull request ejecuta en GitHub Actions las pruebas del backend, verifica las migraciones, comprueba TypeScript y compila el frontend. `/health` confirma que el proceso API responde y `/ready` comprueba además la conexión con la base de datos.
