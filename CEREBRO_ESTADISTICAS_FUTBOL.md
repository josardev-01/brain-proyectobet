# CEREBRO DEL PROYECTO — Estadísticas de Fútbol

**Versión:** 0.2  
**Estado:** Base operativa inicial  
**Stack base:** Python + FastAPI + PostgreSQL + frontend Node.js  
**Canal inicial de alertas:** Telegram

---

## 1. Misión del proyecto

Construir una solución capaz de recibir estadísticas de partidos de fútbol en vivo, analizarlas en tiempo real, evaluar reglas configurables por el usuario y disparar alertas cuando se cumplan determinadas condiciones.

El sistema debe permitir que **cada usuario defina el objetivo de sus alertas**. El motor no estará limitado de forma rígida a apuestas, scouting, análisis de rendimiento o seguimiento de partidos. La plataforma será neutral y permitirá construir estrategias personalizadas a partir de estadísticas y parámetros.

Flujo conceptual:

**Datos en vivo → Normalización → Variables derivadas → Reglas → Evaluación estadística → Alerta → Telegram**

A futuro:

**Datos históricos → Backtesting → Probabilidades → Optimización de reglas → Modelos predictivos**

---

## 2. Rol de ChatGPT en este proyecto

ChatGPT debe actuar simultáneamente como:

- Analista experto en estadísticas deportivas y fútbol.
- Arquitecto de software.
- Desarrollador backend con foco en Python y FastAPI.
- Especialista en PostgreSQL y modelado de datos.
- Diseñador de motores de reglas.
- Ingeniero de datos.
- Asesor en modelos probabilísticos y Machine Learning.
- Revisor crítico de decisiones técnicas y estadísticas.

Su función no es confirmar automáticamente las decisiones del usuario.

Cuando exista una alternativa superior debe indicarla con claridad, explicando:

- beneficios,
- inconvenientes,
- impacto técnico,
- impacto estadístico,
- coste,
- dificultad de implementación,
- consecuencias futuras.

---

## 3. Regla fundamental de trabajo

No asumir decisiones importantes cuando existan varias alternativas razonables que puedan afectar significativamente:

- arquitectura,
- precisión de las estadísticas,
- comportamiento de las alertas,
- costes,
- proveedores,
- modelo de datos,
- escalabilidad,
- experiencia de usuario,
- mantenimiento futuro.

En esos casos se debe consultar al usuario antes de fijar la decisión.

No es necesario consultar decisiones triviales, internas, reversibles o que no afecten el rumbo del proyecto.

---

## 4. Filosofía de desarrollo

Desarrollar el proyecto incrementalmente.

Prioridad:

**MVP funcional → observación → medición → validación → backtesting → optimización → automatización → modelos avanzados**

Evitar sobreingeniería en etapas tempranas.

Cada componente nuevo debe justificar al menos una de estas mejoras:

- mayor precisión,
- menor latencia,
- mejor calidad de alertas,
- mayor flexibilidad,
- menor coste,
- mejor escalabilidad,
- mejor mantenibilidad,
- mejor experiencia de usuario.

---

## 5. Decisiones tomadas hasta el momento

### DEC-001 — Objetivo de las alertas

El sistema será neutral.

Cada usuario decidirá el objetivo de sus estrategias y alertas.

No acoplar el motor de reglas exclusivamente a apuestas deportivas.

### DEC-002 — Backend

Tecnología base:

- Python
- FastAPI

Motivos principales:

- excelente ecosistema estadístico,
- facilidad de integración con APIs,
- procesamiento de datos,
- backtesting,
- Machine Learning futuro,
- buena capacidad para servicios asíncronos.

### DEC-003 — Base de datos

Usar PostgreSQL como almacenamiento principal.

Debe almacenar al menos:

- usuarios,
- partidos,
- snapshots estadísticos,
- eventos,
- reglas,
- estrategias,
- triggers,
- alertas,
- resultados de backtesting.

Redis podrá incorporarse cuando exista una necesidad real de:

- cache,
- estados temporales,
- rate limiting,
- colas rápidas,
- deduplicación,
- coordinación entre workers.

No incorporarlo obligatoriamente desde el primer día.

### DEC-004 — Frontend

Usar ecosistema Node.js.

Recomendación provisional:

**Next.js + TypeScript**

Motivos:

- madurez,
- buena experiencia de desarrollo,
- amplio ecosistema,
- fácil construcción de dashboards,
- buena integración con APIs REST,
- posibilidad de evolucionar hacia aplicación completa.

Esta decisión puede revisarse antes de iniciar el frontend.

### DEC-005 — Canal inicial

Telegram será el primer canal de notificación.

La lógica de Telegram debe mantenerse desacoplada del motor de reglas para permitir posteriormente otros canales.

---

## 6. Proveedor de estadísticas

El proveedor NO debe quedar acoplado directamente al motor de negocio.

Crear una interfaz o adaptador conceptual:

```text
FootballDataProvider
    get_live_matches()
    get_match_statistics(match_id)
    get_match_events(match_id)
    get_pre_match_data(match_id)
```

Cada fuente externa implementará ese contrato.

Ejemplos futuros:

```text
ApiFootballProvider
SportMonksProvider
OddspediaProvider
OtherProvider
```

### Estrategia inicial

Priorizar una API formal antes que scraping siempre que la cobertura y estadísticas sean suficientes.

El scraping debe considerarse un adaptador secundario y no el fundamento irreversible del producto debido a posibles:

- cambios de HTML,
- sistemas anti-bot,
- restricciones de uso,
- cambios en endpoints internos,
- inestabilidad,
- mantenimiento constante.

### Evaluación actual

Para MVP se deben evaluar primero:

1. API-Football.
2. SportMonks.
3. Otras APIs gratuitas o de bajo coste.
4. Scraping o endpoints internos de páginas públicas solo si aportan estadísticas necesarias que las opciones anteriores no ofrecen de manera viable.

SportMonks dispone actualmente de un plan gratuito permanente para pruebas, aunque limitado a determinadas competiciones, por lo que puede servir para validar arquitectura y estructura de datos antes de contratar cobertura superior.

Antes de elegir proveedor definitivo se debe realizar una prueba comparativa basada en:

- cobertura de ligas,
- frecuencia de actualización,
- latencia,
- estadísticas disponibles,
- disponibilidad de odds pre-match/live,
- calidad de identificadores,
- límites de requests,
- estabilidad,
- coste.

---

## 7. Capa de normalización

Nunca permitir que el formato específico de un proveedor llegue directamente al motor de reglas.

Crear un modelo interno normalizado.

Ejemplo conceptual:

```text
MatchState

match_id
provider_match_id
competition_id
home_team_id
away_team_id
minute
period
status
score_home
score_away
shots_home
shots_away
shots_on_target_home
shots_on_target_away
shots_off_target_home
shots_off_target_away
blocked_shots_home
blocked_shots_away
dangerous_attacks_home
dangerous_attacks_away
attacks_home
attacks_away
corners_home
corners_away
possession_home
possession_away
xg_home
xg_away
yellow_cards_home
yellow_cards_away
red_cards_home
red_cards_away
timestamp
```

Los campos no disponibles en determinado proveedor deben admitir valores nulos.

---

## 8. Regla imprescindible: almacenar historia temporal

No almacenar únicamente el estado actual del partido.

Mantener snapshots periódicos o eventos suficientes para reconstruir la evolución.

Ejemplo:

```text
12:00 shots_home = 2
13:00 shots_home = 2
14:00 shots_home = 3
15:00 shots_home = 4
```

Esto permite calcular:

- tiros últimos 3 minutos,
- tiros últimos 5 minutos,
- tiros últimos 10 minutos,
- tiros últimos 15 minutos,
- ataques recientes,
- aceleración ofensiva,
- momentum,
- presión sostenida,
- cambios después de un gol,
- cambios después de una tarjeta roja.

La historia temporal será una de las piezas centrales del producto.

---

## 9. Variables estadísticas

Separar en tres niveles.

### Nivel 1 — Estadísticas directas

- goles,
- tiros,
- tiros a puerta,
- corners,
- posesión,
- ataques,
- ataques peligrosos,
- tarjetas,
- faltas,
- minuto,
- xG cuando esté disponible.

### Nivel 2 — Variables derivadas

Ejemplos:

```text
shots_rate
shots_on_target_rate
shot_accuracy
dangerous_attacks_rate
corner_rate
attack_intensity
offensive_dominance
score_difference
pressure_index
momentum
```

### Nivel 3 — Variables predictivas

Posteriormente:

```text
prob_goal_next_5m
prob_goal_next_10m
prob_home_goal_next_10m
prob_away_goal_next_10m
expected_pressure
expected_threat
historical_rule_lift
```

---

## 10. Ventanas temporales

Evitar depender exclusivamente de datos acumulados.

Ventanas iniciales sugeridas:

- 3 minutos,
- 5 minutos,
- 10 minutos,
- 15 minutos.

Ejemplo:

```text
shots_last_5
shots_last_10
shots_on_target_last_10
dangerous_attacks_last_10
corners_last_10
xg_delta_last_10
```

Las ventanas temporales permitirán distinguir un partido históricamente activo de uno que está activo en este preciso momento.

---

## 11. Primer caso de uso

Primera estrategia experimental:

# Favorito perdiendo + probabilidad elevada de gol en próximos 10 minutos

Objetivo:

Detectar cuando el equipo identificado como favorito antes del partido se encuentra perdiendo y presenta señales suficientes de presión ofensiva como para considerar elevada la probabilidad de que se produzca un gol durante los próximos 10 minutos.

El gol puede analizarse inicialmente como:

- cualquier gol en el partido durante los próximos 10 minutos,

y posteriormente separar:

- gol del favorito,
- gol del rival.

Esta definición debe validarse antes del primer backtesting definitivo.

---

## 12. Cómo identificar al favorito

No definir favorito solamente por reputación del equipo.

Fuente recomendada inicialmente:

**probabilidad implícita derivada de odds pre-match del mercado 1X2.**

Ejemplo decimal:

```text
P_raw = 1 / odd
```

Eliminar posteriormente el margen de la casa normalizando las probabilidades:

```text
P_home = (1 / odd_home) / SUM(1 / odd_i)
P_draw = (1 / odd_draw) / SUM(1 / odd_i)
P_away = (1 / odd_away) / SUM(1 / odd_i)
```

El favorito será inicialmente el equipo con mayor probabilidad implícita normalizada entre home y away.

Guardar también la intensidad del favoritismo.

Ejemplo:

```text
favorite_probability = 0.62
```

No tratar igual un favorito de 41% que uno de 75%.

---

## 13. Primera hipótesis estadística para gol próximo

No utilizar una única estadística como condición definitiva.

Crear inicialmente un **Goal Pressure Score** interpretable.

Versión conceptual:

```text
GPS =
    w1 * normalized_shots_last_10
  + w2 * normalized_sot_last_10
  + w3 * normalized_dangerous_attacks_last_10
  + w4 * normalized_corners_last_10
  + w5 * normalized_xg_last_10
  + w6 * offensive_dominance
  + w7 * momentum
```

Los pesos **NO deben fijarse arbitrariamente como definitivos**.

Durante el MVP pueden utilizarse pesos heurísticos solamente para generar datos y probar el pipeline.

Posteriormente deben calibrarse con histórico.

Variables con prioridad inicial:

1. tiros a puerta recientes,
2. xG reciente si existe,
3. tiros recientes,
4. ataques peligrosos recientes,
5. corners recientes,
6. dominio ofensivo,
7. aceleración respecto a la ventana anterior.

---

## 14. Primera regla experimental

Ejemplo únicamente como punto de partida:

```text
favorite_is_losing = TRUE
AND minute BETWEEN 45 AND 80
AND favorite_shots_last_10 >= X
AND favorite_sot_last_10 >= Y
AND favorite_dangerous_attacks_last_10 >= Z
AND favorite_offensive_dominance >= D
AND goal_pressure_score >= G
```

Los valores X, Y, Z, D y G deben obtenerse mediante experimentación y backtesting.

No considerarlos reglas válidas por intuición.

---

## 15. Modelo probabilístico objetivo

Cuando exista histórico suficiente, reemplazar progresivamente umbrales heurísticos por:

```text
P(goal in next 10 minutes | current match state)
```

Y más específicamente:

```text
P(favorite scores in next 10 minutes | favorite losing, state)
```

Primer modelo recomendado cuando exista dataset:

**Regresión logística.**

Motivos:

- simple,
- interpretable,
- rápida,
- fácil de calibrar,
- permite analizar importancia de variables.

Posteriormente comparar contra:

- Gradient Boosting,
- XGBoost,
- LightGBM.

No utilizar redes neuronales hasta demostrar que modelos más simples son insuficientes.

---

## 16. Motor de reglas

Separar:

### Condición

```text
shots_on_target_last_10 >= 3
```

### Regla

Conjunto lógico de condiciones.

### Estrategia

Conjunto de reglas orientado a detectar un escenario deportivo.

Ejemplo:

```text
strategy:
    favorite_comeback_pressure
```

Debe soportar inicialmente:

- AND,
- OR,
- NOT,
- >,
- >=,
- <,
- <=,
- =,
- !=,
- BETWEEN.

A futuro permitir grupos anidados:

```text
(A AND B AND C) OR (D AND E)
```

---

## 17. Modelo conceptual de condición

Ejemplo JSON:

```json
{
  "metric": "favorite_shots_on_target_last_10",
  "operator": ">=",
  "value": 3
}
```

Ejemplo de estrategia:

```json
{
  "name": "Favorite losing high pressure",
  "conditions": [
    {
      "metric": "favorite_is_losing",
      "operator": "=",
      "value": true
    },
    {
      "metric": "favorite_shots_on_target_last_10",
      "operator": ">=",
      "value": 3
    }
  ]
}
```

---

## 18. Motor de alertas

Una condición verdadera no debe generar mensajes repetidos en cada actualización.

Implementar:

### Trigger once

Solo una alerta por partido/regla.

### Cooldown

Ejemplo:

```text
cooldown = 10 minutos
```

### Re-arm

Una regla podrá dispararse nuevamente únicamente después de dejar de cumplirse y volver a cumplirse.

### Deduplicación

Definir una identidad aproximada:

```text
user_id + match_id + rule_id + trigger_window
```

---

## 19. Telegram

Arquitectura:

```text
Rule Engine
    ↓
Alert Event
    ↓
Notification Service
    ↓
Telegram Adapter
```

No llamar directamente a Telegram desde la lógica estadística.

Esto permitirá incorporar posteriormente:

- Discord,
- WhatsApp,
- email,
- push notifications,
- webhooks.

---

## 20. Formato recomendado de alerta

Ejemplo:

```text
⚽ FAVORITO BAJO PRESIÓN

Manchester X vs Team Y
Minuto: 68'
Marcador: 0-1

Favorito: Manchester X
Prob. pre-match: 67%

Últimos 10 minutos:
Tiros: 6
A puerta: 3
Ataques peligrosos: 15
Corners: 3
xG: 0.58

Goal Pressure Score: 82/100
Prob. gol próximos 10': 36%

Regla: Favorite Losing — High Pressure
```

Las alertas deben ser explicables.

---

## 21. Backtesting

Toda estrategia relevante debe ser evaluable sobre histórico.

Evento objetivo inicial:

```text
goal_within_next_10_minutes
```

Posteriormente:

```text
favorite_goal_within_next_10_minutes
```

Guardar como mínimo:

- estrategia,
- versión,
- partido,
- liga,
- minuto del trigger,
- marcador,
- estadísticas al trigger,
- favorito,
- probabilidad pre-match,
- resultado objetivo,
- tiempo hasta el siguiente gol.

---

## 22. Métricas de calidad

Registrar:

```text
TP
FP
FN
TN
```

Calcular:

```text
Precision = TP / (TP + FP)

Recall = TP / (TP + FN)

F1 = 2 * Precision * Recall / (Precision + Recall)
```

Para un sistema de alertas priorizar inicialmente una buena **Precision** para reducir señales irrelevantes.

---

## 23. Lift

Métrica fundamental:

```text
Lift = P(Event | Rule) / P(Event)
```

Ejemplo:

```text
P(gol próximos 10') = 0.12
P(gol próximos 10' | regla) = 0.30

Lift = 2.5
```

Una regla con Lift cercano a 1 aporta poca información adicional.

---

## 24. Otras métricas futuras importantes

Para probabilidades considerar además:

- Brier Score,
- Log Loss,
- ROC-AUC,
- Precision-Recall AUC,
- Calibration Curve.

La calibración será especialmente importante.

Una probabilidad indicada como 70% debería aproximarse a una frecuencia real cercana al 70% en una muestra suficientemente grande.

---

## 25. Segmentación

Nunca asumir que una estrategia funciona igual en todas las competiciones.

Evaluar posteriormente por:

- liga,
- país,
- equipo,
- local/visitante,
- minuto,
- marcador,
- nivel del favorito,
- diferencia de goles,
- tarjeta roja,
- temporada.

---

## 26. Arquitectura inicial sugerida

```text
                        ┌────────────────────┐
                        │   DATA PROVIDERS   │
                        │ API / Scraping     │
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │ PROVIDER ADAPTERS  │
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │ NORMALIZATION      │
                        └─────────┬──────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    ▼                            ▼
            ┌───────────────┐            ┌──────────────┐
            │ PostgreSQL    │            │ Live State   │
            │ History       │            │ Processing   │
            └───────────────┘            └───────┬──────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │ Feature Engine  │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │ Rule Engine     │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │ Alert Service   │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │ Telegram        │
                                        └─────────────────┘
```

---

## 27. Backend — módulos sugeridos

Estructura conceptual:

```text
app/
├── api/
├── core/
├── models/
├── schemas/
├── providers/
├── normalization/
├── statistics/
├── rules/
├── alerts/
├── notifications/
├── backtesting/
├── repositories/
├── services/
└── workers/
```

Evitar crear todos los módulos con complejidad completa desde el primer commit.

La estructura debe crecer con necesidades reales.

---

## 28. Frontend inicial

Recomendación provisional:

```text
Next.js
TypeScript
React
```

Primeras pantallas previstas:

1. Dashboard de partidos en vivo.
2. Detalle de partido.
3. Creador de reglas.
4. Estrategias.
5. Alertas disparadas.
6. Configuración Telegram.
7. Resultados/backtesting.

El creador de reglas debe intentar evitar que el usuario tenga que escribir código.

Ejemplo UI:

```text
[Favorite Shots On Target Last 10m]
[>=]
[3]

AND

[Favorite Dangerous Attacks Last 10m]
[>=]
[12]
```

---

## 29. Principio de explicabilidad

Nunca generar únicamente:

```text
ALERTA ACTIVADA
```

Indicar siempre qué variables provocaron el trigger.

Esto será importante para:

- confianza del usuario,
- debugging,
- ajuste de reglas,
- backtesting,
- comparación de estrategias.

---

## 30. Versionado de estrategias

No sobrescribir silenciosamente reglas que ya tienen histórico.

Ejemplo:

```text
favorite_pressure_v1
favorite_pressure_v2
favorite_pressure_v3
```

Cada versión debe mantener sus resultados históricos.

---

## 31. Decision Log

Registrar decisiones importantes.

Formato:

```text
DEC-XXX

Problema:
...

Opciones:
A
B
C

Decisión:
...

Motivo:
...

Impacto:
...
```

Esto evita volver a discutir decisiones sin conocer el contexto histórico.

---

## 32. Economía de tokens y forma de interacción

ChatGPT debe adaptar el nivel de profundidad a la tarea.

### Bajo esfuerzo

Para:

- errores simples,
- sintaxis,
- pequeños cambios,
- preguntas puntuales.

### Esfuerzo medio

Para:

- endpoints,
- funciones,
- queries SQL,
- estructuras de datos,
- reglas.

### Alto esfuerzo

Para:

- arquitectura,
- proveedor de datos,
- diseño estadístico,
- fórmulas predictivas,
- backtesting,
- optimización,
- decisiones difíciles de revertir.

Evitar repetir todo el contexto del proyecto en cada respuesta.

Trabajar mediante cambios incrementales.

Cuando el contexto crezca demasiado, recomendar al usuario consolidar información relevante en los archivos maestros del proyecto.

---

## 33. Archivos maestros sugeridos

Mantener progresivamente:

```text
/CEREBRO.md
/ARQUITECTURA.md
/MODELO_DATOS.md
/MOTOR_REGLAS.md
/FORMULAS.md
/DECISION_LOG.md
/BACKTESTING.md
```

`CEREBRO.md` contiene principios relativamente estables.

Los detalles técnicos que cambian con frecuencia deben trasladarse a los documentos especializados para evitar inflar innecesariamente el contexto principal.

---

## 34. Reglas para futuras recomendaciones estadísticas

Toda fórmula propuesta debe clasificarse como una de estas categorías:

```text
HEURÍSTICA
EXPERIMENTAL
VALIDADA
```

### HEURÍSTICA

Basada en razonamiento deportivo, todavía sin backtesting.

### EXPERIMENTAL

Probada sobre datos pero todavía sin evidencia suficiente.

### VALIDADA

Ha cumplido métricas previamente definidas en una muestra suficientemente representativa.

Nunca presentar una heurística como una fórmula estadísticamente demostrada.

---

## 35. Objetivo de evolución

### Fase 1

Obtener partidos en vivo.

### Fase 2

Persistir snapshots.

### Fase 3

Calcular estadísticas por ventanas temporales.

### Fase 4

Crear motor de reglas configurable.

### Fase 5

Enviar alertas por Telegram.

### Fase 6

Registrar resultados de las alertas.

### Fase 7

Construir backtesting.

### Fase 8

Calibrar Goal Pressure Score.

### Fase 9

Estimar probabilidades reales de gol próximos 10 minutos.

### Fase 10

Comparar estrategias y modelos automáticamente.

---

## 36. Principio rector del producto

La meta no es generar muchas alertas.

La meta es transformar:

**datos → contexto → señal → probabilidad → regla → alerta explicable → resultado → aprendizaje**

Cada alerta debe poder medirse y cada regla debe poder mejorarse.

---

## 37. Próxima decisión recomendada

Antes de comenzar el backend productivo, realizar un pequeño **spike técnico de proveedores de datos**.

Comparar al menos API-Football y SportMonks utilizando partidos reales.

Medir:

- estadísticas disponibles,
- actualización durante partidos,
- latencia,
- facilidad de integración,
- odds disponibles,
- identificadores,
- límites del plan gratuito,
- capacidad de reconstruir ventanas temporales.

No construir todavía scraping como dependencia principal hasta demostrar que una API formal no satisface las necesidades del MVP.

---

# Estado actual

**CEREBRO v0.2**

Primer escenario definido:

> Detectar una probabilidad elevada de gol durante los próximos 10 minutos cuando el favorito pre-match se encuentra perdiendo.

Stack provisional:

```text
Backend: Python + FastAPI
Database: PostgreSQL
Frontend: Next.js + TypeScript
Notifications: Telegram
Data Provider: pendiente de spike comparativo
```

Este archivo deberá evolucionar junto con el proyecto sin convertir decisiones experimentales en reglas permanentes antes de validarlas.

