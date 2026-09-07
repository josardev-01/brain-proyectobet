# Arquitectura del MVP

## Componentes

```text
API-Football
    ↓ adaptador + normalización
worker de jornada → archivos JSON/JSONL (evidencia cruda reiniciable)
    ↓ sincronización idempotente
PostgreSQL / SQLite local
    ↓
FastAPI REST
    ↓
Next.js dashboard

evento de alerta → bandeja persistente → adaptador Telegram
```

Los archivos operativos continúan siendo una bitácora recuperable durante la transición. La aplicación consulta la base de datos; `scripts/sync_database.py` proyecta la bitácora hacia tablas normalizadas sin duplicados. El worker ejecuta esa sincronización después de cada ciclo cuando las dependencias del backend están instaladas.

## Backend

- `brain_projectbet.api`: API y contratos públicos.
- `brain_projectbet.database`: modelos SQLAlchemy, sesiones y sincronización.
- `brain_projectbet.providers`: límites externos y adaptadores.
- `brain_projectbet.normalization`: frontera contra formatos del proveedor.
- `brain_projectbet.domain`, `rules`, `strategies`: lógica independiente de HTTP y SQL.
- `brain_projectbet.notifications`: entrega desacoplada.
- `brain_projectbet.backtesting`: evaluación posterior, no bloquea el producto web.

## Persistencia

PostgreSQL es el destino productivo. SQLite utiliza el mismo modelo para desarrollo y pruebas sin exigir Docker. Alembic es la única vía de cambios de esquema versionados. `create_all` en el ciclo de vida de FastAPI facilita una base local vacía; los despliegues ejecutan primero `alembic upgrade head`.

## Límites actuales

- No hay autenticación ni aislamiento multiusuario todavía.
- El editor crea objetivos dinámicos y condiciones declarativas. El evaluador genérico soporta grupos `AND`, `OR`, `NOT` y comparadores seguros; el worker solo sabe construir automáticamente las métricas del adaptador `favorite_pressure` actual.
- Las credenciales Telegram permanecen en variables de entorno; no se muestran ni guardan desde la UI.
- El estado estadístico de la estrategia inicial sigue siendo `HEURÍSTICA`; la aplicación no lo presenta como probabilidad validada.
