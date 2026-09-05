# Análisis de la heurística de presión v2

## Estado

`HEURÍSTICA`. Las mejoras de estructura no equivalen a validación predictiva.

## Cambios respecto de v1

1. La selección pre-partido utiliza la mediana de al menos tres bookmakers en vez de depender de una sola casa.
2. La rama combinada exige al menos un tiro a puerta; tiros y corners sin amenaza directa ya no bastan.
3. El favorito debe igualar o superar al rival en tiros y tiros a puerta durante la ventana.
4. Los horizontes tardíos incompletos se consideran censurados si no ocurre el gol antes del final.
5. Se conserva `minute >= 45` sin límite superior y se registra el tiempo añadido.

## Regla

```text
eligible = median_favorite_odds <= 1.55
           AND normalized_probability >= 0.60

candidate = eligible
            AND minute >= 45
            AND favorite_is_losing

pressure = favorite_without_red_card_disadvantage
           AND (
               favorite_sot_10 >= 2
               OR (
                   favorite_sot_10 >= 1
                   AND favorite_shots_10 >= 3
                   AND favorite_corners_10 >= 1
               )
           )
           AND favorite_shots_10 >= opponent_shots_10
           AND favorite_sot_10 >= opponent_sot_10
```

## Fundamento y límites

- Las odds de múltiples bookmakers han mostrado diferencias en precisión; usar consenso disminuye dependencia de una casa aislada.
- En modelos en vivo, tiempo restante, marcador, eventos recientes y tarjetas son variables contextuales centrales.
- Las tarjetas rojas modifican materialmente la intensidad de gol y no deben mezclarse como si el estado numérico fuera igual.
- La posesión continúa como variable descriptiva, no como requisito, porque no distingue por sí sola control productivo de posesión estéril.
- Corners y tiros siguen siendo proxies. Sin localización de tiro o xG no podemos medir bien la calidad de las oportunidades.

Fuentes de referencia:

- Štrumbelj y Šikonja, *Online bookmakers’ odds as forecasts: The case of European soccer leagues*, International Journal of Forecasting, DOI 10.1016/j.ijforecast.2009.10.005.
- Yao et al., *Goal or Miss? A Bernoulli Distribution for In-Game Outcome Prediction in Soccer*, Entropy 2022, DOI 10.3390/e24070971.
- *Influence of Red and Yellow cards on team performance in elite soccer*, Annals of Operations Research, DOI 10.1007/s10479-022-04733-0.

## Validación requerida

Comparar v1 y v2 sobre los mismos partidos. Reportar precision, recall, F1, lift y tasa base; separar por liga, minuto, diferencia de goles, localía, fuerza del favorito y tarjetas. Las particiones de entrenamiento/prueba deben hacerse por partido y cronológicamente, nunca mezclando minutos del mismo encuentro entre conjuntos.
