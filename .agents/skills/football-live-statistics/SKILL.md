---
name: football-live-statistics
description: Diseña, implementa y evalúa el sistema de estadísticas y alertas de fútbol en vivo de este proyecto. Úsala para proveedores de datos, normalización, snapshots, métricas temporales, reglas configurables, alertas por Telegram, backtesting, modelos probabilísticos, arquitectura o decisiones técnicas del producto. No la uses para consultas generales de fútbol ajenas al proyecto.
---

# Estadísticas de fútbol en vivo

Usa `../../../CEREBRO_ESTADISTICAS_FUTBOL.md` como fuente de verdad del producto. Léelo completo antes de una decisión arquitectónica, estadística o de alcance; para tareas pequeñas, localiza y lee las secciones pertinentes. Si el archivo y el código difieren, informa la discrepancia y no presentes la intención documental como comportamiento ya implementado.

## Forma de trabajo

- Actúa como analista deportivo, arquitecto de software e ingeniero de datos según lo requiera la tarea.
- Conserva el stack acordado: Python/FastAPI, PostgreSQL, frontend Node.js (provisionalmente Next.js con TypeScript) y Telegram como primer canal. Propón cambiarlo solo con una ventaja concreta y consulta antes de una decisión costosa o difícil de revertir.
- Avanza incrementalmente: MVP, medición, validación, backtesting y después optimización. Evita crear módulos o infraestructura sin una necesidad actual.
- Ante decisiones importantes con varias opciones razonables, presenta recomendación, alternativa y efectos técnicos, estadísticos, económicos y futuros; pide decisión al usuario antes de fijarlas. Resuelve autónomamente detalles triviales, internos o reversibles.
- Mantén breves las respuestas rutinarias. Profundiza en arquitectura, proveedores, fórmulas, backtesting y decisiones difíciles de revertir.

## Invariantes del producto

- Mantén el flujo `proveedor -> adaptador -> normalización -> historial/estado -> variables -> reglas -> evento de alerta -> notificación`.
- No expongas formatos del proveedor al motor de reglas. Usa un modelo interno normalizado y admite valores nulos para estadísticas ausentes.
- Conserva snapshots o eventos suficientes para reconstruir ventanas temporales; no guardes solo el estado más reciente.
- Separa condición, regla y estrategia. Versiona las estrategias con histórico; no sobrescribas silenciosamente una versión evaluada.
- Haz que las alertas sean explicables y evita duplicados mediante `trigger once`, `cooldown`, `re-arm` e identidad de deduplicación.
- Mantén Telegram detrás de una interfaz de notificación.
- Trata el scraping como adaptador secundario sujeto a términos de uso, estabilidad y mantenimiento. Prefiere una API formal cuando cobertura, latencia, estadísticas y coste sean adecuados.

## Rigor estadístico

- Etiqueta cada fórmula o umbral como `HEURÍSTICA`, `EXPERIMENTAL` o `VALIDADA`. Nunca presentes intuición deportiva como evidencia empírica.
- Define primero el evento objetivo y el horizonte temporal. Para el primer caso de uso, confirma si se predice cualquier gol o específicamente un gol del favorito en los próximos 10 minutos.
- Identifica al favorito mediante probabilidades implícitas 1X2 pre-partido normalizadas para retirar el margen; conserva también la intensidad del favoritismo.
- Usa ventanas recientes y contexto del marcador. El primer Goal Pressure Score es interpretable y heurístico; sus pesos y umbrales deben calibrarse con históricos.
- Evalúa reglas con precision, recall, F1 y lift. Para probabilidades añade calibración, Brier score, log loss y las métricas discriminativas pertinentes.
- Segmenta resultados por liga, temporada, localía, minuto, marcador, fuerza del favorito y eventos relevantes. Evita generalizar rendimiento global a todas las competiciones.
- Previene fuga temporal: toda variable del backtest debe estar disponible en el instante real del trigger.
- Cuando haya datos suficientes, comienza con regresión logística y compara modelos más complejos solo si aportan una mejora validada.

## Al implementar o revisar

1. Comprueba las decisiones vigentes en el cerebro y los archivos maestros existentes.
2. Delimita el resultado observable y los supuestos deportivos.
3. Implementa el cambio mínimo que respete los invariantes.
4. Verifica casos límite como datos faltantes, división por cero, minutos añadidos, correcciones del proveedor, partidos suspendidos y alertas repetidas cuando sean pertinentes.
5. Registra una decisión importante en el formato `DEC-XXX` cuando establezca una dirección duradera.
6. Indica qué está implementado, qué sigue siendo provisional y qué requiere datos reales o backtesting.

No conviertas automáticamente toda sugerencia del documento en trabajo autorizado. El alcance lo determina la petición actual del usuario.

