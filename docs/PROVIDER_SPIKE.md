# Spike de proveedores v0.1

## Objetivo

Comprobar con respuestas reales si API-Football o SportMonks entregan los datos necesarios, con suficiente frecuencia y calidad, para construir ventanas temporales y evaluar objetivos dinámicos.

El primer objetivo es:

```text
id: favorite_goal_within_10m
evento: goal
sujeto: prematch_favorite
horizonte: 10 minutos
precondición: prematch_favorite_is_losing = true
estado: HEURÍSTICA
```

El objetivo no está integrado en los clientes de proveedores. `TargetEvent` y `ObjectiveDefinition` permiten cambiar evento, sujeto, horizonte y precondiciones sin modificar la capa de adquisición.

La estrategia ejecutable completa está en `config/strategies/favorite_losing_pressure_v2.json`. Allí se definen también el filtro de cuota/probabilidad, minutos de calentamiento y activación, ventana y umbrales de presión. Todos los comandos aceptan `--strategy RUTA`.

Una estrategia ya usada para producir resultados es inmutable. Para experimentar, copiar el archivo, incrementar `version` y cambiar sus parámetros; no editar silenciosamente la versión anterior. Incorporar otro tipo de evento no modifica proveedor ni normalización, pero sí requiere un evaluador y etiquetador apropiados para ese evento.

## Datos mínimos que se deben verificar

1. Identificadores estables de partido, competición y equipos.
2. Estado, periodo, minuto y marcador.
3. Eventos de gol con tiempo y equipo.
4. Tiros, tiros a puerta, corners y posesión.
5. Ataques peligrosos y xG, cuando estén disponibles.
6. Odds 1X2 pre-partido y bookmaker asociado.
7. Valores nulos diferenciados de ceros reales.
8. Frecuencia de actualización, latencia y correcciones tardías.

## Preparación

```powershell
Copy-Item .env.example .env
```

Completar las claves en `.env`. El archivo está excluido de Git.

Para ejecutar desde el repositorio sin instalar el paquete:

```powershell
$env:PYTHONPATH = "src"
python scripts/provider_spike.py api-football live
python scripts/provider_spike.py api-football statistics --fixture-id ID
python scripts/provider_spike.py api-football odds --fixture-id ID
python scripts/provider_spike.py sportmonks live
python scripts/provider_spike.py sportmonks odds --fixture-id ID
```

Las respuestas se guardan en `data/raw/provider-spike/`, fuera del control de versiones. No deben contener nuestras claves, aunque sí pueden contener datos sujetos a las condiciones del proveedor; no publicarlas sin revisar la licencia aplicable.

## Recolección temporal controlada

Una vez identificado un fixture y un bookmaker con mercado 1X2:

```powershell
$env:PYTHONPATH = "src"
python scripts/collect_fixture.py --fixture-id ID --cycles 1
```

Por defecto se utiliza el consenso mediano de al menos tres bookmakers. Para forzar una casa específica, añade por ejemplo `--bookmaker Bet365`.

Para una serie real, aumenta `--cycles` y conserva el intervalo predeterminado de 60 segundos. Cada ciclo consume dos solicitudes después de la consulta inicial de odds. El proceso se detiene si termina el partido o si la cuota diaria restante alcanza `--minimum-remaining`.

API-Football informa dos límites distintos. `x-ratelimit-requests-remaining` corresponde al día y `X-RateLimit-Remaining` al minuto. Deben registrarse por separado: el primero protege el presupuesto total; el segundo controla la velocidad de llamadas.

Ejemplo de 16 capturas:

```powershell
python scripts/collect_fixture.py --fixture-id ID --bookmaker Bet365 --cycles 16 --interval-seconds 60 --minimum-remaining 10
```

Los snapshots se guardan como JSON Lines en `data/raw/snapshots/`. Las ventanas solo se consideran disponibles cuando existe un snapshot de referencia suficientemente antiguo; una corrección decreciente del proveedor produce `null`, no actividad negativa.

El etiquetador mantiene el resultado en `null` hasta observar por completo el horizonte futuro. Los minutos añadidos todavía requieren timestamps o secuencias de eventos más precisas para desambiguar triggers dentro del mismo minuto 45/90; no usar esos casos para validar el modelo hasta resolverlo.

## Registro de candidatos v1

El recolector registra una observación cuando el partido es elegible y alcanzó el minuto de precalentamiento 35. La observación indica por separado si el episodio está activo:

```text
eligible_prematch = favorite_odds <= 1.55 AND normalized_probability >= 0.60
episode_active = eligible_prematch AND minute >= 45 AND favorite_is_losing
```

El identificador incluye proveedor, fixture, objetivo, versión, minuto y tiempo añadido. Esto evita duplicar observaciones del mismo minuto y conserva trazabilidad para backtesting. La salida se guarda en `data/raw/candidates/`, excluida de Git.

La alerta no equivale al candidato. Se evalúa únicamente con una ventana completa de 10 minutos y la regla `favorite_losing_pressure` v2, clasificada como `HEURÍSTICA`.

## Descubrimiento y monitoreo automáticos

El registro diario se puede generar sin conocer de antemano los identificadores de los partidos:

```powershell
$env:PYTHONPATH = "src"
python scripts/discover_candidates.py --date 2026-09-05 --max-pages 3 --daily-reserve 15
```

La salida indica `pages_read` y `total_pages_reported`. Si son distintos, el registro tiene cobertura parcial y no representa toda la jornada. El límite de páginas protege la cuota del plan gratuito mientras se definen competiciones prioritarias.

El monitor consulta primero la lista global de partidos en vivo. Toma una línea base estadística de cada elegible desde el minuto 35 y luego vuelve a solicitar estadísticas solo mientras el favorito esté perdiendo desde el minuto 45:

```powershell
python scripts/monitor_candidates.py --cycles 1 --maximum-matches 3 --daily-reserve 15
```

Cada ciclo consume una consulta global, una consulta inicial por partido al crear su línea base y después una consulta por favorito que esté perdiendo. El proceso conserva una reserva diaria y no emite más de una alerta por combinación de partido, objetivo y versión de regla. Conviene usar intervalos que permitan obtener diferencias reales de 10 minutos; si falta una captura, el motor rechaza la ventana desalineada en lugar de tratarla como válida.

Para probar otra versión sin cambiar el código:

```powershell
python scripts/monitor_candidates.py --strategy config/strategies/MI_ESTRATEGIA.json --cycles 1
```

Archivos locales generados, todos excluidos de Git:

- `data/raw/eligible/AAAA-MM-DD.json`: registro pre-partido.
- `data/raw/snapshots/api-football-ID.jsonl`: serie temporal normalizada.
- `data/raw/candidates/api-football-ID.jsonl`: observaciones del episodio.
- `data/raw/alerts.jsonl`: alertas deduplicadas.

## Replay y etiquetado

Cuando el partido haya terminado, guardar sus eventos exactos y reproducir la decisión:

```powershell
$env:PYTHONPATH = "src"
python scripts/provider_spike.py api-football events --fixture-id ID
python scripts/replay_fixture.py --fixture-id ID --registry data/raw/eligible/AAAA-MM-DD.json --events RUTA_AL_JSON_DE_EVENTOS
```

El replay recorre los snapshots cronológicamente. Para cada decisión, la regla solo recibe el prefijo de la serie conocido hasta ese instante; los eventos futuros se usan después y únicamente como etiqueta. Se informa la primera alerta del episodio, coherente con la política antispam del monitor.

Un resultado `outcome: null` es desconocido o censurado, no un fallo de la regla. No debe convertirse en `false` al calcular métricas.

El cierre de todos los partidos elegibles que ya deberían haber terminado se automatiza así:

```powershell
python scripts/finalize_matches.py --registry data/raw/eligible/AAAA-MM-DD.json --daily-reserve 15
python scripts/summarize_backtests.py
```

El finalizador consulta primero el estado del fixture. Solo para `FT`, `AET` o `PEN` descarga los eventos, añade el estado terminal a la serie, ejecuta el replay y escribe un resultado deduplicado en `data/raw/backtesting/results.jsonl`. Por defecto espera 105 minutos desde el inicio previsto y procesa como máximo tres fixtures por ejecución.

El resumen calcula precisión únicamente sobre alertas con resultado observable. Mientras no exista una población completa de oportunidades etiquetadas, `recall`, `F1` y `lift` se mantienen en `null` deliberadamente.

## Entrega por Telegram

Las alertas se guardan primero como una bandeja local. Para revisar mensajes pendientes sin enviarlos:

```powershell
python scripts/send_pending_alerts.py --dry-run
```

La entrega real requiere completar `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` en `.env` y ejecutar:

```powershell
python scripts/send_pending_alerts.py
```

Cada envío confirmado crea un recibo en `data/raw/notifications/receipts.jsonl`. Un fallo conserva la alerta como pendiente para reintentarla; una ejecución repetida no vuelve a enviar entregas ya confirmadas al mismo destino.

## Matriz de evaluación

Registrar por proveedor y partido:

| Criterio | Resultado |
|---|---|
| Competición y cobertura | Pendiente |
| Estadísticas disponibles | Pendiente |
| Odds 1X2 pre-partido | Pendiente |
| Intervalo real de actualización | Pendiente |
| Latencia p50/p95 observada | Pendiente |
| Correcciones o valores inconsistentes | Pendiente |
| Requests consumidas por partido/hora | Pendiente |
| Coste estimado para el MVP | Pendiente |

No elegir proveedor hasta observar varios partidos y documentar campos ausentes por competición.

Los resultados de cada ronda se consolidan en [`PROVIDER_SPIKE_RESULTS.md`](PROVIDER_SPIKE_RESULTS.md). Las respuestas crudas permanecen fuera de Git.
