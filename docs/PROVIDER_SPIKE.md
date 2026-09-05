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
