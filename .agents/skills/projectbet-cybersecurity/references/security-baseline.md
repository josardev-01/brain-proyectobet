# Linea base de seguridad antes de publicar

## Activos y fronteras

- Cuentas, roles, estados de aprobacion, sesiones y destinos de notificacion.
- Claves de API-Football, Telegram, JWT, PostgreSQL y SSH de Oracle.
- API FastAPI, navegador/Next.js, Caddy, contenedores, base de datos y proveedor externo.
- Datos historicos, reglas, alertas y resultados de backtesting.

## Controles exigidos

### Identidad y autorizacion

- Probar registro pendiente, inicio de sesion, cierre, expiracion, rechazo, desactivacion y aprobacion.
- Probar acceso anonimo, usuario, propietario y administrador sobre cada ruta.
- Impedir que usuarios modifiquen estrategias del sistema o recursos ajenos.
- Evitar enumeracion y fuerza bruta con respuestas prudentes, coste uniforme y limites distribuidos.
- Definir revocacion de sesiones y rotacion de JWT.

### API y navegador

- Restringir CORS a origenes exactos y aplicar proteccion CSRF a mutaciones autenticadas por cookie.
- Deshabilitar documentacion y esquema publico en produccion salvo necesidad explicita.
- Validar entradas, limites de pagina, tamaño de peticion y complejidad de reglas.
- Añadir CSP compatible, `frame-ancestors`, `nosniff`, Referrer-Policy y Permissions-Policy en el proxy.
- No exponer trazas, configuracion, identificadores internos innecesarios ni tokens en JSON al navegador.

### Datos y notificaciones

- Aislar datos por propietario; una alerta privada solo llega a destinos autorizados del propietario.
- Cifrar trafico, limitar privilegios de PostgreSQL y no publicar su puerto.
- Definir retencion, respaldo cifrado, restauracion probada y borrado seguro.
- Tratar payloads de API-Football y Telegram como datos no confiables.

### Infraestructura y suministro

- Publicar solo 80/443; restringir SSH por clave y, cuando sea posible, por origen.
- Ejecutar procesos como usuarios no root, con filesystem y capacidades minimas.
- Fijar versiones/digests, generar SBOM y auditar dependencias de Python, Node e imagenes.
- Separar secretos de imagenes, repositorio, logs y backups; documentar rotacion inmediata.
- Aplicar actualizaciones del sistema, firewall, limites, observabilidad y alertas de seguridad.

## Evidencia minima de salida

- Suite automatizada y pruebas de autorizacion negativas pasando.
- Escaneos de secretos y dependencias sin criticos no aceptados.
- Configuracion de produccion validada sin valores por defecto inseguros.
- Reinicio y restauracion comprobados.
- Registro de riesgos residuales, responsable y condicion previa a publicacion.
