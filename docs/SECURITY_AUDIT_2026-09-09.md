# Auditoria de seguridad — 2026-09-09

Estado: entorno local, no publicado. Alcance revisado: API FastAPI, autenticacion y RBAC, modelos PostgreSQL, frontend Next.js, Docker Compose, Caddy, secretos, notificaciones y dependencias Python/Node.

## Corregido en esta revision

1. **Autorizacion de estrategias globales.** Un usuario aprobado comun podia cambiar la activacion de una estrategia con `owner_id = NULL`. Ahora solo un administrador puede modificar estrategias del sistema y hay pruebas positivas/negativas.
2. **Persistencia y exposicion local.** API, web, PostgreSQL y notificador forman un conjunto reiniciable; PostgreSQL, API y web se enlazan solamente a `127.0.0.1` durante el desarrollo.
3. **Configuracion de produccion.** Se rechazan secretos JWT predeterminados, cortos o de ejemplo, origenes CORS no HTTPS y duraciones de sesion fuera de rango.
4. **Superficie de API.** Swagger, ReDoc y OpenAPI quedan deshabilitados en produccion; Caddy deja de publicar esas rutas.
5. **Contenedores.** API, notificador y frontend se ejecutan con usuarios sin privilegios.
6. **Navegador.** Caddy añade proteccion contra framing, restricciones de permisos, `nosniff`, HSTS y una politica base compatible con Next.js.
7. **Autenticacion.** La comprobacion de un correo inexistente ejecuta Argon2 con un hash ficticio para reducir enumeracion por tiempo. Los campos de login tienen limites de tamaño y la cookie usa ruta explicita.
8. **Cadena de suministro.** `pnpm audit` y `pip-audit` no detectan vulnerabilidades conocidas en las dependencias instaladas. La version vulnerable de `pip` local fue actualizada y la imagen exige `pip >= 26.2`.
9. **Secretos.** Se inspeccionaron el arbol actual y 40 objetos de historial. Solo aparecieron nombres/valores de ejemplo en archivos `.example`; no se detectaron claves privadas ni tokens con los patrones revisados.

## Pendiente antes de publicar

### Prioridad alta

- **Definir el limite publico del producto.** Actualmente dashboard, partidos, snapshots, evaluaciones, listado/configuracion de estrategias, alertas y evaluacion de reglas son de lectura publica. Es aceptable solo para una demostracion deliberadamente publica. Para una beta cerrada deben requerir cuenta aprobada y filtrar recursos por propietario.
- **Limitar abuso de autenticacion.** Falta rate limiting distribuido para registro e inicio de sesion. Aplicarlo en API/proxy con ventanas por IP e identidad, respuestas `429` y observabilidad, sin confiar ciegamente en `X-Forwarded-For`.
- **Aislar alertas futuras por usuario.** Hoy cada alerta del sistema se envia a todos los endpoints habilitados. Antes de ejecutar estrategias privadas, cada alerta debe tener propietario/audiencia y solo entregarse a destinos autorizados.
- **Sesion revocable.** Un JWT robado sigue valido hasta expirar (12 horas por defecto). Antes de publicar, reducir la duracion y añadir rotacion/revocacion o sesiones opacas persistidas.
- **Backups y restauracion.** Automatizar copia cifrada de PostgreSQL y probar la restauracion en otra instancia.

### Prioridad media

- Añadir proteccion CSRF explicita si se mantienen mutaciones autenticadas por cookie o si frontend/API dejan de ser estrictamente mismo sitio. Ahora la mitigacion depende de `SameSite=Lax`, JSON y CORS exacto.
- No devolver el JWT en el cuerpo al navegador cuando la aplicacion use exclusivamente cookie `HttpOnly`; conservar un flujo separado si se necesitan clientes API.
- Registrar de forma inmutable inicios de sesion relevantes, aprobaciones, rechazos y cambios de estrategia, sin datos secretos.
- Fijar dependencias Python con lock/hashes y, para maxima reproducibilidad, digests de imagenes base.
- Aplicar limites de tamaño de peticion en Caddy/API y revisar limites de expresiones al ampliar el DSL.

## Evidencia ejecutada

- Reinicio real de los cuatro servicios Docker con PostgreSQL persistente.
- Flujo real: login administrador, registro pendiente, login rechazado con `403`, aprobacion administrativa, login de usuario aprobado y limpieza de cuentas temporales.
- 99 pruebas unitarias/integracion aprobadas.
- Build de imagenes y comprobacion de usuarios: `projectbet` para API/notificador y `node` para frontend.
- `pnpm audit --audit-level high`: sin vulnerabilidades conocidas.
- `pip-audit`: sin vulnerabilidades conocidas en paquetes auditables; el paquete local no esta publicado en PyPI y se valida mediante sus pruebas.

Esta auditoria reduce riesgos conocidos, pero no equivale a una prueba de penetracion sobre una instancia publica. Debe repetirse tras definir la politica de acceso y antes de abrir la VPS a Internet.
