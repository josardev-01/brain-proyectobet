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
