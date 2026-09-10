# Resultados del spike de proveedores

## GOAL API y APIFootball.com — observación 2026-09-09

**Estado:** EXPERIMENTAL. Las consultas reales confirman acceso y estructura,
pero no estabilidad longitudinal ni cobertura garantizada del plan gratuito.

GOAL API devolvió 20 partidos en vivo y declaró una cuota diaria de 1.000
solicitudes. El endpoint de estadísticas de un partido live incluyó corners,
ataques, ataques peligrosos, tiros a puerta, tiros fuera y posesión. Su listado
live no incluyó un minuto corriente fiable: `matchStatus` expuso `LIVE` o
`HALF_TIME`; los minutos aparecieron solamente en eventos. Por ello no debe ser
el reloj exclusivo de la heurística hasta resolver esa ausencia.

APIFootball.com devolvió 23 encuentros live de 13 ligas y estadísticas en 20.
`match_status` incluyó minutos numéricos, `Half Time`, `Finished` y `90+`. Las
estadísticas observadas incluyeron corners, ataques, ataques peligrosos, tiros a
puerta, tiros fuera y posesión. La cobertura observada supera las dos ligas que
la página comercial asigna al plan gratuito; puede corresponder a una
habilitación inicial y no se considerará permanente sin medirla varios días.
La consulta de cuotas del día respondió `No odd found (please check your plan)`,
por lo que esta habilitación no se usará como fuente de cuotas pre-partido. La
selección inicial de favoritos seguirá usando API-Football mientras se evalúan
alternativas.

Las claves permanecen en `.env`. APIFootball.com autoriza por IP; desarrollo
local y VPS necesitan registrar sus IP públicas de salida por separado.

## API-Football — observación 2026-09-05

**Estado:** EXPERIMENTAL. Una sola observación valida el pipeline, no la calidad general del proveedor.

### Consulta de partidos en vivo

- Partidos devueltos: 105.
- Latencia observada: 528.65 ms.
- La respuesta incluyó identificador, competición, país, equipos, estado, minuto y marcador.

### Partido de muestra

```text
Fixture: 1556663
Partido: ST Mirren vs Celtic
Instante observado: minuto 42
Marcador: 1-0
```

Odds 1X2 pre-partido de Bet365:

```text
Local: 7.00
Empate: 4.75
Visitante: 1.42
```

Probabilidades implícitas normalizadas:

```text
ST Mirren: 13.51%
Empate: 19.91%
Celtic: 66.59%
```

Celtic queda identificado como favorito pre-match y la precondición `prematch_favorite_is_losing = true` se cumplía.

Estadísticas acumuladas observadas:

| Métrica | ST Mirren | Celtic |
|---|---:|---:|
| Tiros | 7 | 8 |
| Tiros a puerta | 1 | 3 |
| Corners | 3 | 6 |
| Posesión | 32% | 68% |

Latencias adicionales:

- Estadísticas del fixture: 346.95 ms.
- Odds pre-partido: 596.70 ms.

### Hallazgos

- El caso inicial puede identificarse sin reglas basadas en reputación: odds normalizadas + marcador actual.
- La muestra aporta tiros, tiros a puerta, corners, posesión, pases, faltas, offsides y tarjetas.
- No se observaron `dangerous_attacks` ni xG en esta respuesta.
- Las estadísticas son acumuladas. Las ventanas de 3, 5, 10 y 15 minutos deberán derivarse comparando snapshots capturados en distintos instantes.
- Se necesitan observaciones de múltiples competiciones y momentos para determinar cobertura real, frecuencia de actualización y consistencia.

### Siguiente captura requerida

Ejecutar el mismo ciclo sobre varios partidos y conservar al menos un snapshot por minuto. Para etiquetar `favorite_goal_within_10m`, registrar los eventos disponibles exactamente 10 minutos después de cada instante candidato, evitando usar información futura en las variables.

## Validación del recolector controlado

Se ejecutó un ciclo adicional sobre el fixture 1556663:

```text
Minuto: 45
Estado: HT
Marcador: 1-0
Favorito: away (Celtic)
Probabilidad normalizada: 66.59%
Precondición favorito perdiendo: true
Ventanas disponibles: ninguna; todavía falta historia suficiente
Solicitudes restantes informadas por el límite del minuto: 7
```

El recolector se detuvo porque interpretó incorrectamente el encabezado del límite por minuto como cuota diaria. El dashboard mostraba solo 6% de uso y la documentación oficial distingue ambos encabezados. La lógica fue corregida para proteger la cuota diaria sin detener una captura válida por el contador del minuto.

## Primera ventana temporal y etiqueta real

Después de separar correctamente los límites, la API informó:

```text
Cuota diaria: 100
Restante antes de la serie: 93
Límite por minuto: 10
Restante en ese minuto: 9
```

Se capturaron snapshots en los minutos 45, 49, 50, 51, 52, 53, 54 y 55. La serie se detuvo voluntariamente al completar la primera ventana de 10 minutos, conservando cuota.

Ventana 45–55:

| Delta acumulado | ST Mirren | Celtic |
|---|---:|---:|
| Tiros | 0 | 3 |
| Tiros a puerta | 0 | 1 |
| Corners | 0 | 2 |

Los eventos del fixture confirmaron un gol de Liam Scales para Celtic al minuto 51. Para el trigger observado en el minuto 42:

```text
Objetivo: favorite_goal_within_10m v1
Sujeto: Celtic (team_id 247)
Horizonte observable: minuto 42 < evento <= minuto 52
Gol del sujeto: minuto 51
Etiqueta: true
```

Este caso demuestra que el pipeline puede enlazar odds, marcador, snapshots, equipo favorito y evento futuro. Sigue siendo una observación `EXPERIMENTAL`; no valida todavía una fórmula predictiva ni los umbrales de presión.

### Consenso de odds aplicado posteriormente

La respuesta guardada contenía seis bookmakers con mercado 1X2 completo. La mediana fue:

```text
Local: 6.795
Empate: 4.85
Visitante: 1.41
Probabilidad normalizada de Celtic: 66.75%
```

El consenso confirma la clasificación de favorito y reduce dependencia de Bet365. La ventana 45–55 describe lo ocurrido durante esos diez minutos, pero no debe reutilizarse como variable de un trigger al minuto 45; hacerlo introduciría fuga temporal.

## Auditoría automática de calidad — 2026-09-05

Se auditaron los archivos locales disponibles sin realizar nuevas consultas:

```text
Fixtures: 2
Snapshots: 10
Fixtures con estado terminal: 2
Fixtures con alguna ventana exacta de 10 minutos: 1
```

Disponibilidad ponderada por snapshot:

| Grupo de métricas | Disponibilidad observada |
|---|---:|
| Tiros | 90% |
| Tiros a puerta | 90% |
| Corners | 90% |
| Posesión | 90% |
| Tarjetas rojas normalizadas | 10% |
| Ataques peligrosos | 0% |
| xG | 0% |

El 90% no implica cobertura general del proveedor: un fixture aporta nueve capturas completas y el otro únicamente un snapshot terminal sin estadísticas. La serie útil posee una ventana 45–55 exacta, pero también un salto de 35 minutos hasta el estado final. Por ahora, tiros, tiros a puerta, corners y posesión son utilizables para el spike; ataques peligrosos y xG deben considerarse no disponibles en esta muestra.

## Segunda jornada de elegibles — 2026-09-06

Se revisaron tres páginas de 64 reportadas y se identificaron cinco favoritos mediante consenso. Los cinco fixtures se cerraron con resultado y eventos finales. La auditoría de secuencia de goles reconcilió correctamente los cinco marcadores.

Exposición al escenario objetivo:

| Partido | Favorito | Primera vez perdiendo desde 45' |
|---|---|---:|
| FC Dallas vs Sporting Kansas City | FC Dallas | No ocurrió |
| Vancouver Whitecaps vs St. Louis City | Vancouver Whitecaps | 45' |
| Orgryte IS vs Hammarby FF | Hammarby FF | No ocurrió |
| Remo vs Flamengo | Flamengo | No ocurrió |
| Corinthians vs Chapecoense | Corinthians | 77' |

Hubo dos escenarios reales, pero no existían snapshots en vivo de esos fixtures. Por tanto, no se puede evaluar retrospectivamente la presión sin introducir datos que no fueron capturados en el instante correspondiente. La ronda demuestra que el filtro encuentra casos útiles y que la siguiente prioridad es mantener activo el monitor durante las ventanas programadas.

Durante el cierre se observó HTTP 429 al superar el límite de 10 solicitudes por minuto, aun con cuota diaria suficiente. El finalizador se endureció para detenerse antes de cruzar cualquiera de los dos límites y reanudó los dos fixtures pendientes sin duplicar los siete ya completados. Al finalizar quedaron 80 solicitudes diarias y 6 del minuto.
