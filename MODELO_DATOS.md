# Modelo de datos

## Entidades iniciales

| Tabla | Propósito | Identidad estable |
|---|---|---|
| `users` | Propietarios futuros de estrategias | correo único |
| `matches` | Partido normalizado y estado reciente | proveedor + id externo |
| `snapshots` | Serie temporal de estadísticas | partido + instante de captura |
| `strategies` | Configuración inmutable y versionada | clave + versión |
| `alerts` | Trigger explicable y estado de entrega | id de deduplicación |
| `backtest_results` | Evidencia experimental por versión | id de replay |

Los campos estadísticos ausentes son nulos. Esto distingue “cero observado” de “dato no disponible”. `JSON` conserva configuración extensible y explicación, pero los campos usados para buscar, ordenar o relacionar están tipados como columnas.

## Reglas de integridad

- Un proveedor no puede insertar dos veces el mismo partido.
- Un snapshot no se duplica para el mismo partido e instante.
- Una versión de estrategia no se sobrescribe: el cambio crea otra versión.
- Una alerta conserva la identidad ya usada por `trigger once`.
- El resultado de backtesting es único por partido, objetivo y versiones.

La migración inicial se encuentra en `migrations/versions/`. Cambios posteriores deben generar otra revisión de Alembic; nunca se editará el esquema productivo manualmente.
