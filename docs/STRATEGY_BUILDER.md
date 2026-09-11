# Constructor de estrategias

## Referencia funcional

Se analizó `https://thebookiehunter.com/filters` como referencia de producto,
sin reutilizar código ni diseño. La página separa resultados, goles, corners,
tarjetas, rachas, ligas incluidas/excluidas y campos que aparecerán en Telegram.
También permite guardar filtros con nombre y exige sesión para crear filtros.

La principal mejora que adopta ProjectBet es separar conceptos que allí aparecen
en una misma pantalla:

1. **Objetivo:** qué evento se desea observar y en qué horizonte.
2. **Alcance:** en qué ligas o países se aplicará.
3. **Condiciones:** datos pre-partido y en vivo unidos mediante AND u OR.
4. **Alerta:** qué evidencia debe incluir la notificación.
5. **Versión y estado estadístico:** cada cambio crea una versión nueva y nace
   como `HEURÍSTICA`.

## Contrato implementado

El backend publica un catálogo cerrado de métricas y operadores. El navegador
no puede introducir código ejecutable. La expresión se valida en servidor y los
datos ausentes fallan de forma cerrada y explicable.

Métricas iniciales:

- minuto, marcador y estado del local o visitante;
- cuota y probabilidad pre-partido por local, empate y visitante;
- tiros, tiros a puerta y tiros fuera;
- ataques y ataques peligrosos;
- corners, posesión y tarjetas;
- ventanas recientes de 5, 10 o 15 minutos.

Las métricas se identifican de forma neutral por equipo local o visitante. Cuando una
estadística admite historia, el periodo se elige separadamente como total del partido o
últimos N minutos; “ventana reciente” no forma parte del nombre de la estadística.

Cada estrategia pertenece al usuario que la crea. Si está activa, se evalúa después de
cada sincronización live y su alerta solo se entrega a los destinos Telegram de ese
propietario.

El contenido opcional del mensaje se controla con `alert_fields`. Telegram muestra
únicamente los bloques seleccionados; dentro de ellos omite las estadísticas que el
proveedor no haya entregado, en lugar de completar el mensaje con `N/D`. La cabecera
con estrategia, partido y minuto se conserva siempre para identificar la señal. Las
condiciones evaluadas son un campo seleccionable independiente.

El alcance admite ligas incluidas, ligas excluidas y países. Las condiciones
admiten `AND`, `OR`, `>`, `>=`, `=`, `!=`, `<`, `<=` y `BETWEEN`.

El constructor visual admite grupos anidados `AND`, `OR` y `NOT`. Desde una
tarjeta existente, **Usar como base** carga su alcance, condiciones, objetivo y
contenido de alerta, propone el siguiente número de versión y conserva intacta
la versión anterior.

## Evolución recomendada

El siguiente incremento del constructor debe permitir probar una estrategia sobre
un partido elegido y mostrar una estimación de cobertura antes de activarla. Los objetivos corner y
tarjeta se pueden definir desde ahora, pero requieren etiquetadores específicos
antes de presentar backtesting o probabilidades como disponibles.
