# Resultados del spike de proveedores

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
