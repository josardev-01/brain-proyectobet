---
name: projectbet-cybersecurity
description: "Audita y endurece la seguridad de ProjectBet: autenticacion, autorizacion, API FastAPI, frontend Next.js, PostgreSQL, Docker/Caddy, Telegram, secretos, dependencias y despliegue Oracle VPS. Usala para revisiones de vulnerabilidades, cambios de seguridad, preparacion para publicar, incidentes o decisiones que afecten datos y cuentas. No la uses para analisis futbolistico sin impacto de seguridad."
---

# Ciberseguridad de ProjectBet

Protege cuentas, datos, credenciales del proveedor, token de Telegram y la infraestructura sin bloquear el desarrollo local.

## Flujo de trabajo

1. Define el alcance, activos, actores, puntos de entrada y fronteras de confianza.
2. Reune evidencia en codigo, configuracion, dependencias, registros y comportamiento reproducible. No presentes una sospecha como vulnerabilidad confirmada.
3. Clasifica cada hallazgo por severidad, confianza, precondiciones, impacto y superficie afectada.
4. Corrige primero exposicion de secretos, omisiones de autorizacion, escalada de privilegios, inyecciones y configuraciones publicas inseguras.
5. Prefiere controles del servidor y denegacion por defecto. La interfaz nunca sustituye autorizacion en la API.
6. Añade pruebas negativas y positivas, ejecuta la suite pertinente y documenta el riesgo residual.
7. Antes de publicar, revisa completamente `references/security-baseline.md`.

## Invariantes

- Nunca muestres, registres, confirmes por valor ni incluyas en commits contraseñas, JWT, claves SSH, `API_FOOTBALL_KEY` o `TELEGRAM_BOT_TOKEN`.
- No ejecutes escaneos intrusivos, ataques de fuerza bruta ni pruebas sobre produccion sin autorizacion explicita y alcance definido.
- Un usuario `PENDING`, `REJECTED` o inactivo no obtiene sesion. Un usuario comun no administra cuentas ni estrategias globales.
- Aplica autenticacion, rol, propiedad y aislamiento multiusuario en cada operacion sensible.
- Las cookies de sesion deben ser `HttpOnly`, `Secure` en produccion, `SameSite` apropiado y de alcance minimo; considera CSRF para toda mutacion basada en cookie.
- Usa errores de autenticacion prudentes, comparaciones seguras, hash de contraseña resistente y limites contra abuso.
- Valida longitud, tipo, rango y estructura de entradas; limita cargas, paginacion y expresiones configurables.
- En produccion expone solo 80/443. PostgreSQL y la API interna permanecen en red privada; usa TLS, CORS por lista permitida y cabeceras defensivas.
- Fija y audita dependencias e imagenes. Ejecuta contenedores sin privilegios cuando sea viable.
- Mantiene copias de seguridad verificables y un procedimiento de restauracion; una copia nunca probada no cuenta como recuperacion.
- La seguridad temporal del modelo exige impedir fuga de datos futuros en snapshots y backtests.

## Formato de auditoria

Entrega primero los hallazgos, ordenados por severidad. Para cada uno incluye evidencia precisa, escenario explotable, correccion y prueba. Separa:

- confirmado ahora;
- mitigado por el entorno actual pero obligatorio antes de publicar;
- mejora de defensa en profundidad.

Si no hay hallazgos confirmados, dilo expresamente y enumera limites de la revision.
