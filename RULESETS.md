# Chat de Reglas y Speech Base

Este módulo permite ajustar palabras clave y un speech de referencia sin tocar código. El pipeline usa el ruleset activo desde `data/rulesets.json`.

## Estructura del ruleset
```json
[
  {
    "id": "default",
    "name": "Base compliance",
    "keywords": ["reclamo", "devolucion", "cancelacion"],
    "required_phrases": ["gracias por llamar", "puedo ayudarte"],
    "template_text": "...speech base...",
    "user_id": "default",
    "thresholds": {
      "keyword_weight": 2,
      "missing_required_weight": 3,
      "similarity_weight": 5,
      "critical": 10,
      "high": 7,
      "medium": 4
    },
    "created_by": "user",
    "created_at": "2026-01-21T00:00:00Z",
    "version": 1,
    "active": true
  }
]
```

## Cómo funciona
- El pipeline carga el ruleset activo al evaluar riesgo.
- Si se define `DAIA_RULES_USER` en el entorno, toma el ruleset activo de ese usuario; si no existe, usa el activo global.
- Calcula: coincidencias de `keywords`, frases obligatorias faltantes y similitud con `template_text` (Jaccard simple).
- Suma el score del ruleset al score de riesgo existente y toma la severidad más alta (BAJO < MEDIO < ALTO < CRÍTICO).
- Resultado disponible en `result['data']['risk']['rules_engine']`.

## Operaciones rápidas
- **Activar otro ruleset**: marcar `"active": true` en el deseado y `false` en el resto dentro de `data/rulesets.json`.
- **Agregar reglas**: añadir un objeto nuevo al arreglo con un `id` único.
- **Ajustar pesos/umbrales**: modificar `thresholds`; los pesos escalan el score, los umbrales definen MEDIO/ALTO/CRÍTICO.
- **Por usuario**: guarda `user_id` y activa uno por usuario; la GUI envía `DAIA_RULES_USER` al pipeline automáticamente.

## Notas
- Si el archivo no existe o está corrupto, se regenera un preset por defecto para no interrumpir el pipeline.
- No se entrenan modelos: todo es reglas y similitud ligera.
