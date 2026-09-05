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
