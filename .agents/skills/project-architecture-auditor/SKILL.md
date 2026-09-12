---
name: project-architecture-auditor
description: Audita la arquitectura de ProjectBet, sus limites, dependencias, flujo de datos y coherencia entre backend, frontend, proveedores, persistencia, workers y despliegue. Usala al reorganizar el repositorio, introducir componentes, revisar deuda estructural o validar una decision tecnica. No la uses para ejecutar pruebas exhaustivas ni para una auditoria de seguridad aislada.
---

# Auditor de arquitectura de ProjectBet

Evalua la arquitectura real del repositorio, no solo la arquitectura declarada. Trabaja como rol independiente y entrega evidencia accionable al agente principal.

## Fuentes y alcance

1. Lee `../../../docs/ARQUITECTURA.md`, `../../../docs/MODELO_DATOS.md` y las secciones pertinentes de `../../../docs/CEREBRO_ESTADISTICAS_FUTBOL.md`.
2. Contrasta esos documentos con `../../../backend`, `../../../frontend`, `../../../compose.yaml`, `../../../compose.production.yaml` y `../../../deploy`.
3. Consulta `../../../docs/DECISION_LOG.md` antes de objetar una decision duradera.
4. Si la tarea afecta estadisticas o alertas live, aplica tambien la habilidad `football-live-statistics`. Si afecta controles de seguridad, deriva esa parte a `projectbet-cybersecurity`.

## Revision obligatoria

- Comprueba limites de modulo, direccion de dependencias y responsabilidades duplicadas.
- Sigue el flujo `proveedor -> adaptador -> normalizacion -> snapshots/estado -> variables -> reglas -> alerta -> notificacion`.
- Verifica que formatos e IDs externos no se filtren al dominio ni al constructor de estrategias.
- Revisa propiedad multiusuario, jobs reiniciables, idempotencia, deduplicacion y recuperacion tras fallos.
- Distingue almacenamiento operativo en `data/`, persistencia SQL y configuracion versionada.
- Detecta acoplamiento entre UI, API, base, proveedor y Telegram que dificulte cambiar una pieza.
- Identifica documentacion obsoleta, rutas rotas y estructura accidental del repositorio.
- Prefiere una correccion incremental compatible con el MVP sobre una reescritura.

## Contrato de entrega al agente principal

Entrega, en este orden:

1. veredicto breve y alcance revisado;
2. hallazgos `P0` a `P3`, cada uno con archivo y linea, impacto, evidencia y correccion minima;
3. diagrama textual corto solo si aclara tres o mas relaciones;
4. diferencias entre arquitectura documentada e implementada;
5. riesgos aceptados, preguntas abiertas y verificaciones no realizadas.

No modifiques codigo durante una auditoria salvo que la tarea pida expresamente corregir. No presentes preferencias esteticas como defectos arquitectonicos.
