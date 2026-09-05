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
