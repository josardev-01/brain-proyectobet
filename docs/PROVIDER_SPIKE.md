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
python scripts/collect_fixture.py --fixture-id ID --bookmaker Bet365 --cycles 1
```

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

La alerta no equivale al candidato. Se evalúa únicamente con una ventana completa de 10 minutos y la regla `favorite_losing_pressure` v1, clasificada como `HEURÍSTICA`.

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
