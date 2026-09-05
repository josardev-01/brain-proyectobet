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
```

El primero registra favoritos claros mediante consenso de al menos tres casas. El segundo consulta estadísticas solo cuando esos partidos están en vivo desde el minuto 35, evalúa la heurística v2 y guarda alertas sin duplicarlas.
