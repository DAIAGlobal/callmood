# DA-2.0 — Especificaciones Funcionales y Casos de Uso

## Resumen
Documento que define las Especificaciones Funcionales y los Casos de Uso para el proyecto DAIA (auditoría de llamadas). Contiene alcance, actores, requisitos funcionales y escenarios de uso prioritarios.

## Alcance
- Auditoría automática de llamadas telefónicas para generar métricas, hallazgos y reportes.
- Integración con almacenamiento, generación de reportes y exportación.
- Interfaces para batch y UI para revisión humana.

## Actores
- Analista: Revisa auditorías, valida hallazgos y exporta reportes.
- Administrador: Configura reglas, gestiona usuarios y sincroniza almacenamiento.
- Sistema de Transcripción: Servicio externo que provee texto transcrito.
- Motor de Reglas: Componente que evalúa transcripciones y genera hallazgos.

## Requisitos Funcionales (RF)
1. RF-01: Ingesta de audio
   - El sistema debe aceptar archivos de audio (wav, mp3) en modo batch y por carpeta de sincronización.
2. RF-02: Transcripción
   - El sistema debe enviar audios al motor de transcripción y almacenar el texto resultante con metadatos (duración, timestamps, hablantes).
3. RF-03: Evaluación mediante reglas
   - El sistema debe ejecutar un motor de reglas sobre la transcripción para detectar incumplimientos, palabras clave y métricas.
4. RF-04: Generación de reportes
   - El sistema debe generar reportes por llamada en formatos JSON y TXT, y exportar reportes consolidados en PDF.
5. RF-05: Interfaz de revisión
   - El Analista debe poder abrir la auditoría en la UI, ver hallazgos, añadir notas y marcar el estado de la llamada.
6. RF-06: Configuración de reglas
   - El Administrador debe poder crear, editar y activar/desactivar reglas desde archivos de configuración (e.g., rulesets.json).
7. RF-07: Almacenamiento y sincronización
   - El sistema debe sincronizar archivos a un almacenamiento remoto (p.ej. Google Drive) y mantener rastreo de versiones.
8. RF-08: KPIs y métricas
   - El sistema debe calcular métricas agregadas (scoring, riesgo, sentimiento) y exponerlas para reporting.
9. RF-09: Seguridad y auditoría
   - Registrar accesos, cambios de configuración y eventos críticos en logs con timestamps.
10. RF-10: Internacionalización
   - Soportar contenido en español e inglés para reportes y UI.

## Requisitos No Funcionales (RNF)
- RNF-01: Rendimiento: procesar al menos 50 llamadas simultáneas en batch.
- RNF-02: Disponibilidad: tolerancia a fallos en componentes externos; reintentos y colas.
- RNF-03: Escalabilidad: arquitectura modular para escalar procesamiento y reglas.
- RNF-04: Mantenibilidad: reglas y transformaciones definidas en archivos legibles y versionados.

## Casos de Uso

### Caso de Uso 1 — Auditoría Batch
- Actor primario: Administrador
- Precondición: Carpeta `audio_in/` poblada con archivos.
- Flujo principal:
  1. Administrador inicia proceso batch.
  2. Sistema toma archivos y los envía al módulo de transcripción.
  3. Transcripción devuelve texto y metadatos.
  4. Motor de Reglas ejecuta reglas y genera hallazgos.
  5. Sistema guarda resultados en `reports/` y genera reportes consolidados.
  6. Sistema notifica fin de proceso y ubicación de reportes.
- Postcondición: Reportes generados y almacenados; logs actualizados.
- Excepciones:
  - Falla de transcripción: marcar archivo como error y continuar con los demás.

### Caso de Uso 2 — Revisión por Analista
- Actor primario: Analista
- Precondición: Auditoría generada y disponible en UI.
- Flujo principal:
  1. Analista abre UI y selecciona una llamada.
  2. Visualiza transcripción, marcadores de hallazgos y métricas.
  3. Añade notas y corrige o valida hallazgos.
  4. Marca la llamada como `Validada` o `Requiere revisión`.
  5. Exporta reporte individual en PDF si es necesario.
- Postcondición: Estado actualizado y anotaciones guardadas.

### Caso de Uso 3 — Gestión de Reglas
- Actor primario: Administrador
- Precondición: Acceso administrativo.
- Flujo principal:
  1. Administrador sube o edita un `ruleset` (JSON).
  2. Sistema valida la sintaxis del ruleset y realiza pruebas con muestras.
  3. Si es válido, se publica y se registra la versión.
- Postcondición: Nuevo ruleset activo; auditoría de cambios registrada.

### Caso de Uso 4 — Exportar Reporte Consolidado
- Actor primario: Administrador / Analista
- Precondición: Existen resultados de auditoría para el periodo solicitado.
- Flujo principal:
  1. Usuario solicita reporte consolidado desde UI o script.
  2. Sistema agrega métricas, tablas y hallazgos relevantes.
  3. Se genera un PDF con la estructura definida y se almacena en destino.
- Postcondición: PDF disponible en la ruta solicitada.

## Estructura del PDF de entrega
- Portada: título, versión, fecha, responsable.
- Índice y Resumen Ejecutivo.
- Especificaciones Funcionales detalladas.
- Casos de Uso con flujos y excepciones.
- Anexos: ejemplos de reportes, formato de ruleset.

## Versionado
- Versión: DA-2.0
- Fecha: 
## Pruebas Funcionales

Este apartado define casos de prueba funcionales para validar los requisitos principales del sistema. Cada caso incluye: objetivo, datos de entrada, pasos y criterios de aceptación.

### Prueba 1 — Ingesta y Procesamiento Batch
- Objetivo: Verificar que el sistema procesa un conjunto de audios en `audio_in/` y genera reportes.
- Datos de entrada: 5 archivos de audio (wav) de 30-60s en `audio_in/test_batch/`.
- Pasos:
   1. Ejecutar proceso batch (`process_batch.py` o script equivalente).
   2. Verificar que cada archivo sea transcrito y que exista un JSON en `reports/`.
   3. Verificar que el proceso registre errores para archivos inválidos y continúe.
- Criterios de aceptación:
   - Todos los archivos válidos generan un `.json` y `.txt` en `reports/`.
   - El archivo de salida contiene campos: `transcription`, `duration`, `speakers`, `findings`.

### Prueba 2 — Transcripción y Metadatos
- Objetivo: Comprobar que el motor de transcripción devuelve texto con timestamps y etiquetas de hablante.
- Datos de entrada: 1 archivo con diálogo de dos hablantes.
- Pasos:
   1. Enviar archivo al módulo de transcripción.
   2. Revisar el JSON resultante.
- Criterios de aceptación:
   - Presencia de timestamps por segmento.
   - Identificación de al menos 2 hablantes o marcas de segmento.

### Prueba 3 — Evaluación por Reglas
- Objetivo: Validar que las reglas detectan palabras clave y generan hallazgos.
- Datos de entrada: Transcripción que contiene las palabras activas de un `ruleset` de prueba.
- Pasos:
   1. Activar un `ruleset` de prueba (por ejemplo, reglas simples en `rulesets.json`).
   2. Ejecutar evaluación sobre la transcripción de prueba.
   3. Revisar salida `findings` en el JSON.
- Criterios de aceptación:
   - Se generan hallazgos que corresponden a las reglas (tipo, severidad, snippet de texto).

### Prueba 4 — Revisión y Anotaciones en UI
- Objetivo: Verificar que el Analista puede abrir una auditoría, añadir notas y cambiar estados.
- Datos de entrada: Auditoría generada con hallazgos.
- Pasos:
   1. Abrir la auditoría en la UI (`gui/main_window.py`).
   2. Añadir nota en un hallazgo y marcar la llamada como `Validada`.
   3. Guardar y volver a abrir la auditoría.
- Criterios de aceptación:
   - Las anotaciones persisten en el JSON de la auditoría.
   - El estado de la llamada cambia y se registra en logs.

### Prueba 5 — Exportar Reporte Individual y Consolidado
- Objetivo: Comprobar la generación de PDFs individuales y consolidados.
- Datos de entrada: Conjunto de auditorías para un periodo (p.ej., 10 llamadas).
- Pasos:
   1. Ejecutar comando de exportación o usar la UI para solicitar PDF consolidado.
   2. Verificar la creación del PDF y su estructura (portada, índice, tablas).
- Criterios de aceptación:
   - El PDF se genera en la ruta solicitada y contiene índices y hallazgos.

### Notas para pruebas
- Registrar en cada ejecución: versión del código, `ruleset` usado, y ruta de los artefactos generados.
- Para pruebas automatizadas, crear un pequeño conjunto de fixtures en `tests/fixtures/` y scripts que simulen la cola de procesamiento.
