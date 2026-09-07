# Modelo de datos

## Entidades iniciales

| Tabla | Propósito | Identidad estable |
|---|---|---|
| `users` | Identidades, roles y revisión administrativa | correo único |
| `matches` | Partido normalizado y estado reciente | proveedor + id externo |
| `snapshots` | Serie temporal de estadísticas | partido + instante de captura |
| `strategies` | Configuración inmutable y versionada | clave + versión |
| `alerts` | Trigger explicable y estado de entrega | id de deduplicación |
| `notification_endpoints` | Destinos Telegram habilitados por usuario | usuario + canal + destino |
| `notification_deliveries` | Intentos y recibos por alerta/destino | alerta + destino |
| `backtest_results` | Evidencia experimental por versión | id de replay |

Los campos estadísticos ausentes son nulos. Esto distingue “cero observado” de “dato no disponible”. `JSON` conserva configuración extensible y explicación, pero los campos usados para buscar, ordenar o relacionar están tipados como columnas.

## Reglas de integridad

- Un proveedor no puede insertar dos veces el mismo partido.
- Un snapshot no se duplica para el mismo partido e instante.
- Una versión de estrategia no se sobrescribe: el cambio crea otra versión.
- Una estrategia creada desde el API queda vinculada a su propietario.
- Un registro público comienza pendiente; solo un administrador aprobado puede registrar su revisión.
- Una alerta conserva la identidad ya usada por `trigger once`.
- Una entrega exitosa no vuelve a enviarse al mismo destino; los fallos quedan reintentables.
- El resultado de backtesting es único por partido, objetivo y versiones.

La migración inicial se encuentra en `migrations/versions/`. Cambios posteriores deben generar otra revisión de Alembic; nunca se editará el esquema productivo manualmente.
