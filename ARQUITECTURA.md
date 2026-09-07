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

## Seguridad inicial

El API registra usuarios con contraseñas Argon2 y emite sesiones JWT con vencimiento. El navegador recibe el token en una cookie `HttpOnly` y `SameSite=Lax`; clientes externos también pueden usar el bearer devuelto. Crear o activar estrategias requiere autenticación y las estrategias de usuario solo pueden ser modificadas por su propietario. En producción es obligatorio definir `JWT_SECRET`.

## Ejecución declarativa

El runtime transforma snapshots normalizados en un diccionario estable de métricas: marcador, minuto, estado del favorito, acumulados y deltas exactos de ventana. Después evalúa expresiones declarativas activas. El endpoint de evaluaciones de partido expone resultado, razones, campos ausentes y estado estadístico, sin usar información futura.

## Límites actuales

- Aún no hay recuperación de contraseña, verificación de correo ni roles administrativos.
- El editor crea objetivos dinámicos y condiciones declarativas. El evaluador genérico soporta grupos `AND`, `OR`, `NOT` y comparadores seguros; emitir y etiquetar alertas de un nuevo tipo de evento todavía requiere su contrato específico.
- Las credenciales Telegram permanecen en variables de entorno; no se muestran ni guardan desde la UI.
- El estado estadístico de la estrategia inicial sigue siendo `HEURÍSTICA`; la aplicación no lo presenta como probabilidad validada.
