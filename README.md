# Proyecto Bet — Motor de estadísticas de fútbol

Sistema para analizar partidos de fútbol en vivo, evaluar reglas configurables y generar alertas explicables cuando se cumplan condiciones estadísticas.

## Estado

Fase inicial de descubrimiento técnico. El primer objetivo es validar la disponibilidad y calidad de los datos necesarios para detectar escenarios donde el favorito pre-partido va perdiendo y existe presión compatible con un gol en los próximos 10 minutos.

## Próximo hito

Ejecutar el monitor automático sobre partidos reales y reunir una muestra suficiente para medir:

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
python scripts/finalize_matches.py --registry data/raw/eligible/AAAA-MM-DD.json
python scripts/summarize_backtests.py
python scripts/send_pending_alerts.py --dry-run
```

El flujo descubre favoritos claros, monitorea únicamente los escenarios relevantes, finaliza partidos con eventos exactos, registra resultados para backtesting y conserva las alertas en una bandeja entregable por Telegram.

La definición activa está en [`config/strategies/favorite_losing_pressure_v2.json`](config/strategies/favorite_losing_pressure_v2.json). Los comandos aceptan `--strategy` para ejecutar otra versión sin modificar el motor.
