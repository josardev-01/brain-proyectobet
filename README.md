# Proyecto Bet — Motor de estadísticas de fútbol

Sistema para analizar partidos de fútbol en vivo, evaluar reglas configurables y generar alertas explicables cuando se cumplan condiciones estadísticas.

## Estado

Fase inicial de descubrimiento técnico. El primer objetivo es validar la disponibilidad y calidad de los datos necesarios para detectar escenarios donde el favorito pre-partido va perdiendo y existe presión compatible con un gol en los próximos 10 minutos.

## Próximo hito

Realizar un spike comparativo de proveedores de datos, comenzando por API-Football y SportMonks, y medir:

- cobertura y estadísticas disponibles;
- frecuencia de actualización y latencia;
- disponibilidad de cuotas pre-partido;
- estabilidad de identificadores;
- límites y coste;
- capacidad de reconstruir ventanas temporales.

No se considera validada ninguna fórmula o regla hasta evaluarla mediante datos históricos y backtesting.

## Documentación del proyecto

- [`CEREBRO_ESTADISTICAS_FUTBOL.md`](CEREBRO_ESTADISTICAS_FUTBOL.md): principios, decisiones y dirección del producto.
- [`.agents/skills/football-live-statistics/SKILL.md`](.agents/skills/football-live-statistics/SKILL.md): habilidad local para aplicar esos criterios durante el desarrollo.

## Stack previsto

- Backend: Python y FastAPI.
- Base de datos: PostgreSQL.
- Frontend: Next.js y TypeScript, decisión provisional.
- Notificaciones iniciales: Telegram.

La implementación crecerá de manera incremental después de seleccionar el proveedor de datos.
