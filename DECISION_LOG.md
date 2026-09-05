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

**Decisión:** Crear un registro diario de elegibles a partir del consenso 1X2 y usar una única consulta global de partidos en vivo por ciclo. Solo desde el minuto 35 se consultarán estadísticas de encuentros presentes en ese registro, con un máximo configurable de dos partidos por ciclo y una reserva diaria predeterminada de 15 solicitudes. La alerta se deduplica por fixture, objetivo y versión de regla.

**Motivo:** El filtrado temprano concentra la cuota en partidos útiles, permite precalentar la ventana antes del minuto 45 y evita spam cuando una condición permanece activa. Mantener objetivos y reglas versionados conserva la posibilidad de incorporar otros eventos en el futuro.

**Impacto:** El descubrimiento predeterminado lee como máximo tres páginas y, por tanto, es una muestra parcial cuando el proveedor reporta más páginas. Esa limitación debe conservarse en los resultados y no se puede presentar como cobertura total. La estrategia permanece `EXPERIMENTAL` hasta definir ligas prioritarias, medir cobertura y completar backtesting.
