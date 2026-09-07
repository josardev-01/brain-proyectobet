# Registro de decisiones

## DEC-006 — Objetivos dinámicos y primer evento objetivo

**Problema:** El primer caso de uso necesita un evento objetivo concreto para capturar datos y hacer backtesting, sin limitar el producto a ese único escenario.

**Opciones:**

- Codificar “favorito perdiendo” y “gol próximo” directamente en el pipeline.
- Usar un objetivo genérico de cualquier gol y especializarlo más adelante.
- Representar objetivos mediante definiciones dinámicas y versionadas.

**Decisión:** Adoptar definiciones dinámicas y versionadas con tipo de evento, sujeto, horizonte temporal, precondiciones y estado estadístico. La primera definición será `favorite_goal_within_10m` v1: gol del favorito pre-match dentro de 10 minutos cuando está perdiendo.

**Motivo:** Permite comenzar con una etiqueta inequívoca y añadir en el futuro goles, corners, tarjetas u otros eventos sin acoplar los objetivos a proveedores o reestructurar el pipeline.

**Impacto:** La adquisición y normalización de datos serán neutrales respecto al objetivo. Las reglas, etiquetas de backtesting y modelos referenciarán una versión del objetivo. La primera definición queda clasificada como `HEURÍSTICA` hasta disponer de evidencia histórica.

## DEC-007 — Candidatos de favoritos claros y heurística de presión v1

**Problema:** Definir cuándo un partido entra en observación y cuándo esa observación se convierte en alerta, incluyendo minutos avanzados y tiempo añadido.

**Opciones:**

- Limitar candidatos a una franja cerrada, por ejemplo minutos 45–80.
- Mantener candidatos desde el minuto 45 sin límite superior.
- Emitir alertas apenas el favorito pierda, sin exigir actividad ofensiva.

**Decisión:** Un partido será elegible cuando la cuota decimal del favorito sea como máximo 1.55 y su probabilidad 1X2 normalizada sea al menos 60%. El episodio candidato se activa si el favorito pierde desde el minuto 45 y permanece activo sin minuto máximo, incluido el tiempo añadido. La alerta v1 requiere que el favorito no tenga desventaja de tarjetas rojas y cumpla `SOT10 >= 2 OR (shots10 >= 4 AND corners10 >= 2)`.

**Motivo:** Los favoritos que siguen perdiendo en minutos avanzados continúan siendo relevantes. Separar elegibilidad, episodio y presión evita alertar solo por marcador y permite evaluar cada componente.

**Impacto:** Se deben iniciar snapshots desde el minuto 35 para precalentar la ventana de 10 minutos. La posesión se guarda como contexto. Toda la regla v1 se clasifica como `HEURÍSTICA` y será versionada al calibrarse.

## DEC-008 — Heurística de presión v2 y consenso de odds

**Problema:** La regla v1 podía activar una alerta con tiros y corners pero ningún tiro a puerta, dependía de un solo bookmaker y trataba incorrectamente algunos horizontes incompletos al final del partido.

**Opciones:**

- Mantener v1 hasta reunir histórico.
- Añadir pesos arbitrarios a un Goal Pressure Score.
- Mejorar invariantes observables sin afirmar calibración estadística.

**Decisión:** Usar la mediana de al menos tres mercados 1X2 completos para el filtro de favorito. La presión v2 exige `SOT10 >= 2 OR (SOT10 >= 1 AND shots10 >= 3 AND corners10 >= 1)`, además de que el favorito no sea superado por el rival en tiros ni tiros a puerta dentro de la ventana. Se conserva la exclusión de desventaja por tarjeta roja. Horizontes incompletos sin gol al finalizar el partido se marcan como censurados.

**Motivo:** Las odds de distintas casas no tienen idéntica calidad predictiva; el consenso reduce dependencia de un valor aislado. Los tiros a puerta representan amenaza más directa que volumen estéril. Marcador, tiempo restante, eventos recientes y tarjetas son variables dinámicas relevantes para predicción en juego.

**Impacto:** La regla pasa a versión 2 pero permanece `HEURÍSTICA`. El backtesting deberá comparar v1 y v2 por precision, recall y lift, agrupando observaciones por partido para evitar tratar minutos correlacionados como muestras independientes.

## DEC-009 — Descubrimiento y monitoreo automático con presupuesto de API

**Problema:** Detectar favoritos claros antes del partido y seguirlos en vivo sin agotar la cuota diaria del proveedor ni consultar estadísticas de encuentros irrelevantes.

**Opciones:**

- Consultar todos los partidos y sus estadísticas durante toda la jornada.
- Descubrir candidatos pre-partido y consultar individualmente solo los elegibles que estén en vivo.
- Limitar el producto a una lista fija de equipos o ligas.

**Decisión:** Crear un registro diario de elegibles a partir del consenso 1X2 y usar una única consulta global de partidos en vivo por ciclo. Se guarda una línea base estadística al observar por primera vez cada elegible desde el minuto 35; después se consulta de nuevo solo mientras el favorito esté perdiendo desde el minuto 45. Se procesan como máximo tres partidos por ciclo y se conserva una reserva diaria predeterminada de 15 solicitudes. La alerta se deduplica por fixture, objetivo y versión de regla.

**Motivo:** El filtrado temprano concentra la cuota en partidos útiles, permite precalentar la ventana antes del minuto 45 y evita spam cuando una condición permanece activa. Mantener objetivos y reglas versionados conserva la posibilidad de incorporar otros eventos en el futuro.

**Impacto:** El descubrimiento predeterminado lee como máximo tres páginas y, por tanto, es una muestra parcial cuando el proveedor reporta más páginas. Esa limitación debe conservarse en los resultados y no se puede presentar como cobertura total. Una ventana se evalúa solo si su duración real coincide con los 10 minutos declarados; saltos de captura no se reinterpretan como ventanas válidas. La estrategia permanece `EXPERIMENTAL` hasta definir ligas prioritarias, medir cobertura y completar backtesting.

## DEC-010 — Repetición temporal sin fuga de información

**Problema:** Evaluar la heurística con datos guardados puede inflar artificialmente el resultado si una decisión usa snapshots o eventos que todavía no existían al momento de la alerta.

**Opciones:**

- Evaluar cada snapshot con la serie completa del partido.
- Reproducir la serie en orden y separar datos de decisión de eventos usados como etiqueta.
- Medir únicamente alertas emitidas en vivo, sin capacidad de repetir experimentos.

**Decisión:** El motor de replay entrega a la regla solo el prefijo de snapshots disponible hasta cada observación. Al primer trigger del partido congela la decisión y usa los eventos posteriores exclusivamente para etiquetar el objetivo. La primera alerta es la unidad de evaluación del episodio.

**Motivo:** Mantiene causalidad temporal, coincide con la deduplicación del monitor y permite comparar versiones de reglas sobre exactamente la misma evidencia.

**Impacto:** Los resultados del replay no validan la heurística por sí solos; requieren una muestra de partidos terminados y eventos completos. Los tiempos añadidos se comparan mediante los campos `elapsed` y `extra`, pero deberán migrar a timestamps del proveedor si se detectan ambigüedades de cambio de periodo.

## DEC-011 — Finalización post-partido y métricas disponibles

**Problema:** Los snapshots y alertas en vivo no bastan para medir una regla si después no se recupera el resultado final y los eventos exactos del partido.

**Decisión:** Un finalizador revisa fixtures elegibles con antigüedad mínima configurable, procesa únicamente estados con resultado (`FT`, `AET`, `PEN`), conserva la respuesta final y los eventos crudos, añade un snapshot terminal, ejecuta el replay y guarda un registro deduplicado por fixture, objetivo y versión de regla.

**Motivo:** Cierra el ciclo observación → resultado → evidencia sin mezclar formatos del proveedor con la regla ni volver a contar un partido al repetir el proceso.

**Impacto:** El resumen inicial informa cobertura, candidatos, alertas resueltas y precisión. `recall`, `F1` y `lift` permanecen sin valor hasta construir una población completa de oportunidades etiquetadas; no se derivarán artificialmente solo de las alertas emitidas. Los resultados continúan clasificados como `EXPERIMENTAL`.

## DEC-012 — Bandeja de alertas y entrega desacoplada

**Problema:** Enviar a Telegram directamente desde el motor puede perder una alerta si la red falla después de evaluarla o duplicarla durante un reintento.

**Decisión:** El monitor persiste primero un `AlertEvent` explicable. Un proceso independiente lee alertas pendientes, usa un adaptador Telegram y registra un recibo deduplicado por alerta, canal y destino. Solo después de una respuesta satisfactoria se considera entregada.

**Motivo:** Separa decisión estadística de efectos externos, permite reintentos seguros y deja preparado el sistema para otros canales.

**Impacto:** La recolección y el backtesting funcionan sin credenciales de Telegram. Activar entregas reales requiere `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`; los secretos permanecen exclusivamente en `.env`.

## DEC-013 — Estrategias configurables y versionadas

**Problema:** Aunque objetivo y políticas estaban representados por clases, los scripts seleccionaban constantes fijas. Cambiar umbrales exigía editar código y podía desalinear descubrimiento, monitoreo y backtesting.

**Decisión:** Cada ejecución carga una estrategia JSON que reúne identidad, versión, estado estadístico, objetivo, política de candidatos, tipo de regla y parámetros. Todos los comandos del ciclo aceptan `--strategy` y usan por defecto `config/strategies/favorite_losing_pressure_v2.json`.

**Motivo:** Garantiza que filtro pre-partido, ventana, trigger y replay usen la misma definición, y permite comparar nuevas versiones sin tocar adquisición ni normalización.

**Impacto:** Una versión evaluada no debe editarse ni sobrescribirse; cualquier cambio de umbral requiere copiar la definición, incrementar la versión y conservar la anterior. El adaptador `favorite_pressure` actual admite específicamente el objetivo de gol del favorito pre-partido. Nuevos eventos como corners o tarjetas reutilizarán la infraestructura, pero deberán incorporar un evaluador y etiquetador compatibles.

## DEC-014 — Auditoría de calidad antes de interpretar resultados

**Problema:** Una regla puede no alertar por comportamiento deportivo o porque faltan estadísticas, snapshots o ventanas temporales completas.

**Decisión:** Auditar automáticamente cada serie por cobertura temporal, estado terminal, duplicados de reloj, separación máxima, existencia de una ventana exacta de 10 minutos y disponibilidad de campos normalizados.

**Motivo:** Separa ausencia de señal de ausencia de datos y evita atribuir al modelo limitaciones originadas en adquisición.

**Impacto:** Todo análisis de rendimiento deberá acompañarse de cobertura. La primera auditoría confirma datos útiles de tiros, tiros a puerta, corners y posesión, pero no cobertura de ataques peligrosos ni xG en la muestra actual.

## DEC-015 — Protección conjunta de cuota diaria y por minuto

**Problema:** Una ejecución por lotes puede conservar la cuota diaria y aun así recibir HTTP 429 al superar las 10 solicitudes permitidas dentro del minuto.

**Decisión:** Antes de iniciar otro fixture o descargar sus eventos, el finalizador comprueba cuántas solicitudes necesita contra ambos contadores. Si no existe capacidad, termina de forma reanudable. Los errores HTTP del proveedor se convierten en errores sanitizados sin exponer credenciales ni producir escrituras duplicadas.

**Motivo:** El límite diario controla coste y el límite por minuto controla ráfagas; ambos son independientes y deben respetarse.

**Impacto:** Los cierres parciales se pueden ejecutar otra vez: los registros completos se omiten y el fixture interrumpido continúa cuando vuelve a existir capacidad.

## DEC-016 — Exposición al escenario separada de disponibilidad estadística

**Problema:** Sin snapshots en vivo no se puede saber desde los resultados de replay si el favorito nunca perdió o si existió un candidato que no fue observado.

**Decisión:** Reconstruir con los eventos de gol si el favorito estuvo perdiendo desde el minuto 45 y validar la secuencia contra el marcador final. Si los goles no reconcilian el resultado, la exposición queda desconocida en vez de inferirse.

**Motivo:** Permite medir oportunidades perdidas por operación sin usar esa reconstrucción futura como variable de una alerta en vivo.

**Impacto:** En los primeros nueve elegibles hubo dos exposiciones reales no monitoreadas. La prioridad pasa a ser un worker persistente de jornada; no se modificarán umbrales con esta muestra incompleta.

## DEC-017 — Ejecutor reiniciable por ventanas de jornada

**Problema:** Las ejecuciones manuales omitieron dos escenarios reales porque no había un proceso activo durante los partidos.

**Decisión:** Construir el plan desde el registro pre-partido. Cada fixture se observa desde el minuto 35 hasta 150 minutos después del saque inicial y se finaliza a partir de las tres horas. Las ventanas solapadas se fusionan para compartir la consulta global de partidos en vivo. El ejecutor admite un ciclo único para integrarse con un programador y conserva la deduplicación existente, por lo que reiniciarlo no duplica candidatos, alertas ni resultados.

**Motivo:** La cobertura operativa es ahora el cuello de botella; cambiar la heurística con partidos no observados confundiría ausencia de datos con ausencia de señal.

**Impacto:** El intervalo predeterminado es de diez minutos, compatible con la ventana exacta evaluada y con el presupuesto disponible para la jornada. Una ventana exacta de 10 minutos requiere observaciones compatibles y no se inventa si hay interrupciones. El proceso debe seguir respetando la reserva diaria y los límites por minuto del proveedor. Si hay más candidatos que capacidad por ciclo, se priorizan episodios activos sobre líneas base pendientes.

## DEC-018 — Desarrollo de producto desacoplado de la validación estadística

**Problema:** Esperar una muestra suficiente antes de construir API, persistencia y experiencia de usuario alarga el calendario sin mejorar la captura de evidencia.

**Decisión:** Avanzar en paralelo con un MVP integrado. PostgreSQL es el almacén productivo; SQLite comparte los modelos para desarrollo local. SQLAlchemy define el mapeo, Alembic versiona el esquema, FastAPI expone contratos REST y Next.js consume esos contratos. La bitácora JSON/JSONL se conserva temporalmente como evidencia recuperable y se sincroniza de forma idempotente.

**Motivo:** El contrato de partidos, snapshots, estrategias versionadas y alertas es estable aunque cambien posteriormente los umbrales. Esto permite desarrollar producto sin presentar la heurística como validada.

**Impacto:** Backend y frontend deben mostrar el estado estadístico explícito. La primera versión web permite observar partidos, snapshots, estrategias y alertas, además de registrar nuevos objetivos como definiciones inactivas. Ejecutar tipos de regla adicionales, autenticación y multiusuario quedan como siguientes incrementos; no se simula soporte que el worker todavía no tenga.

## DEC-019 — Expresiones declarativas seguras para reglas dinámicas

**Problema:** Incorporar objetivos futuros mediante código específico haría que cada nuevo caso exigiera modificar y desplegar el backend.

**Decisión:** Representar condiciones como datos y evaluarlas sin `eval` ni código suministrado por usuarios. El contrato soporta comparadores `>`, `>=`, `<`, `<=`, `=`, `!=`, `BETWEEN` y grupos anidados `AND`, `OR`, `NOT`, con límites de profundidad y cantidad de nodos. Una métrica ausente falla de forma cerrada y queda explicada.

**Motivo:** Permite construir reglas desde la interfaz manteniendo validación, explicabilidad y seguridad. Separa el lenguaje de condiciones de la construcción de métricas deportivas.

**Impacto:** El API puede validar y probar expresiones con cualquier diccionario de métricas. Cada nuevo evento aún necesita un extractor/etiquetador y métricas disponibles en tiempo real; el lenguaje genérico no convierte automáticamente una definición en una estrategia validada.

## DEC-020 — Sesiones de usuario y propiedad de estrategias

**Problema:** Permitir escrituras anónimas impide atribuir configuraciones y deja expuesta la activación de reglas.

**Decisión:** Registrar contraseñas exclusivamente como hashes Argon2 y usar JWT con vencimiento. La aplicación web mantiene la sesión en cookie `HttpOnly`, `SameSite=Lax`; el token bearer se conserva como contrato para otros clientes. Las escrituras de estrategias requieren identidad y respetan el propietario. Producción no arranca con el secreto JWT local predeterminado.

**Motivo:** Es un límite de seguridad suficiente para el siguiente incremento multiusuario sin acoplar el dominio deportivo al mecanismo de autenticación.

**Impacto:** Quedan pendientes verificación de correo, recuperación de contraseña, rotación/refresh de sesiones, protección CSRF adicional si la aplicación se distribuye entre sitios distintos y roles administrativos.

## DEC-021 — Destinos Telegram por usuario y recibos en base de datos

**Problema:** Un único `TELEGRAM_CHAT_ID` global no permite que distintos usuarios administren destinos y el recibo basado en archivos no expresa entregas por destinatario.

**Decisión:** Mantener un token de bot global exclusivamente en variables de entorno y guardar únicamente identificadores de chat asociados al usuario. Cada par alerta/destino tiene un recibo único con estado, intentos, error sanitizado y fecha de entrega. Un usuario solo administra sus propios destinos.

**Motivo:** Conserva el adaptador desacoplado, evita almacenar secretos del bot en la base y permite reintentos sin duplicar mensajes.

**Impacto:** Las alertas de la estrategia global se pueden distribuir a todos los destinos activos. Cuando el worker ejecute estrategias privadas, deberá conservar el propietario en el evento para limitar sus destinatarios. Activar entregas reales requiere el token del bot y al menos un chat configurado.
