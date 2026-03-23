"""
Helpers to persist pipeline results into human-readable artifacts (JSON/TXT).

These helpers operate on the raw dict emitted by the pipeline layer so that
reporting stays decoupled from domain entities and can evolve independently.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _build_base_filename(result: Dict[str, Any]) -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_base = Path(result.get('audio_file', 'unknown')).stem or 'report'
    return f"{timestamp}_{filename_base}"


def save_json_report(result: Dict[str, Any], output_dir: str = "artifacts/reports") -> Optional[str]:
    """Persist a compact JSON summary of the pipeline result."""
    try:
        if not isinstance(result, dict):
            logger.error("❌ Resultado inválido para JSON")
            return None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"{_build_base_filename(result)}.json"
        filepath = output_path / filename

        data = result.get('data', {})
        transcript_text = data.get('transcription', {}).get('text', '')

        report_data = {
            'timestamp': datetime.now().isoformat(),
            'filename': result.get('audio_file', 'unknown'),
            'duration': result.get('duration', 0),
            'service_level': result.get('service_level', 'standard'),
            'status': result.get('status', 'unknown'),
            'transcript': transcript_text[:500] + '...' if len(transcript_text) > 500 else transcript_text,
            'qa': data.get('qa', {}),
            'sentiment': data.get('sentiment', {}),
            'risk': data.get('risk', {}),
            'kpis': data.get('kpis', {}),
            'patterns': data.get('patterns', []),
            'anomalies': data.get('anomalies', []),
        }

        with filepath.open('w', encoding='utf-8') as handle:
            json.dump(report_data, handle, ensure_ascii=False, indent=2, default=str)

        logger.info("✓ JSON guardado: %s", filepath)
        return str(filepath)

    except IOError as exc:
        logger.error("❌ Error de I/O al guardar JSON: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("❌ Error guardando JSON: %s", exc)
        return None


def save_text_report(result: Dict[str, Any], output_dir: str = "artifacts/reports") -> Optional[str]:
    """Persist an opinionated TXT report ready for quick QA review."""
    try:
        if not isinstance(result, dict):
            logger.error("❌ Resultado inválido para texto")
            return None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"{_build_base_filename(result)}.txt"
        filepath = output_path / filename

        data = result.get('data', {})
        transcript_data = data.get('transcription', {})
        qa_data = data.get('qa', {})
        sentiment_data = data.get('sentiment', {})
        risk_data = data.get('risk', {})
        kpis_data = data.get('kpis', {})
        patterns_data = data.get('patterns', [])
        anomalies_data = data.get('anomalies', [])

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        with filepath.open('w', encoding='utf-8') as handle:
            handle.write("=" * 80 + "\n")
            handle.write("CallMood - REPORTE DE ANÁLISIS DE LLAMADA\n")
            handle.write("=" * 80 + "\n\n")

            # Información general
            handle.write("-" * 80 + "\n")
            handle.write("📋 INFORMACIÓN GENERAL\n")
            handle.write("-" * 80 + "\n")
            handle.write(f"Archivo: {result.get('audio_file', 'N/A')}\n")
            duration = result.get('duration', 0)
            handle.write(f"Duración: {duration} segundos ({int(duration)//60}min {int(duration)%60}s)\n")
            handle.write(f"Nivel de análisis: {result.get('service_level', 'N/A').upper()}\n")
            handle.write(f"Procesado: {timestamp}\n")
            handle.write(f"Estado: {result.get('status', 'N/A').upper()}\n\n")

            # Resumen ejecutivo
            handle.write("-" * 80 + "\n")
            handle.write("🎯 RESUMEN EJECUTIVO\n")
            handle.write("-" * 80 + "\n")

            qa_score = qa_data.get('compliance_percentage', 0)
            qa_class = qa_data.get('classification', 'N/A')
            risk_level = risk_data.get('level', 'N/A')

            overall_sent = sentiment_data.get('overall', {})
            if isinstance(overall_sent, dict):
                sentiment_label = overall_sent.get('label', 'N/A')
                sentiment_conf = overall_sent.get('confidence', 0)
            else:
                sentiment_label = str(overall_sent)
                sentiment_conf = sentiment_data.get('confidence', 0)

            handle.write(f"\n📊 Calidad General: {qa_class}\n")
            handle.write(f"   • Cumplimiento QA: {qa_score:.1f}%\n")
            eval_status = '✅ APROBADO' if qa_score >= 70 else '❌ NO CUMPLE' if qa_score < 50 else '⚠️ MEJORABLE'
            handle.write(f"   • Evaluación: {eval_status}\n\n")

            handle.write(f"😊 Análisis Emocional: {str(sentiment_label).upper().replace('_', ' ')}\n")
            handle.write(f"   • Confianza: {sentiment_conf:.1%}\n")
            sent_status = '✅ Positivo' if 'positive' in str(sentiment_label).lower() else '❌ Negativo' if 'negative' in str(sentiment_label).lower() else '⚪ Neutral'
            handle.write(f"   • Valoración: {sent_status}\n\n")

            handle.write(f"⚠️ Nivel de Riesgo: {risk_level}\n")
            critical_keywords = risk_data.get('critical_found', [])
            if critical_keywords:
                handle.write(f"   • Palabras críticas: {', '.join(critical_keywords)}\n")
            risk_status = (
                '🔴 CRÍTICO - Requiere atención' if risk_level == 'CRÍTICO'
                else '🟡 MEDIO - Supervisar' if risk_level == 'MEDIO'
                else '🟢 BAJO - Normal'
            )
            handle.write(f"   • Estado: {risk_status}\n\n")

            # Análisis emocional detallado
            if sentiment_data.get('segments'):
                handle.write("-" * 80 + "\n")
                handle.write("💭 ANÁLISIS EMOCIONAL POR SEGMENTO\n")
                handle.write("-" * 80 + "\n\n")

                segments = sentiment_data.get('segments', [])
                for i, segment in enumerate(segments[:5], 1):
                    seg_label = segment.get('label', 'unknown')
                    seg_conf = segment.get('confidence', 0)
                    seg_text = segment.get('text', '')[:100]

                    emoji = "😊" if 'positive' in str(seg_label).lower() else "😞" if 'negative' in str(seg_label).lower() else "😐"
                    handle.write(f"{emoji} Segmento {i}: {str(seg_label).upper().replace('_', ' ')} ({seg_conf:.1%})\n")
                    handle.write(f'   "{seg_text}..."\n\n')

            # Transcripción
            handle.write("-" * 80 + "\n")
            handle.write("📝 TRANSCRIPCIÓN\n")
            handle.write("-" * 80 + "\n")
            transcript_text = transcript_data.get('text', 'No disponible')
            handle.write(transcript_text[:1000] + ("..." if len(transcript_text) > 1000 else "") + "\n\n")

            # QA
            handle.write("-" * 80 + "\n")
            handle.write("✅ EVALUACIÓN DE CALIDAD (QA)\n")
            handle.write("-" * 80 + "\n")
            handle.write(f"Puntuación: {qa_score:.1f}%\n")
            handle.write(f"Clasificación: {qa_class}\n")
            handle.write(f"Nivel evaluado: {qa_data.get('level', 'N/A')}\n\n")

            if qa_data.get('details'):
                handle.write("Detalles por categoría:\n")
                for detail in qa_data.get('details', []):
                    check_type = detail.get('check_type', 'N/A')
                    passed = detail.get('passed', False)
                    status_icon = "✅" if passed else "❌"
                    handle.write(f"  {status_icon} {check_type}\n")
            handle.write("\n")

            # KPIs
            if kpis_data:
                handle.write("-" * 80 + "\n")
                handle.write("📊 MÉTRICAS OPERACIONALES (KPIs)\n")
                handle.write("-" * 80 + "\n\n")

                metrics = kpis_data.get('metrics', {})
                for metric_name, metric_info in metrics.items():
                    value = metric_info.get('value', 'N/A')
                    classification = metric_info.get('classification', '')
                    unit = metric_info.get('unit', '')

                    handle.write(f"• {metric_name.replace('_', ' ').title()}: {value}{unit}")
                    if classification:
                        handle.write(f" ({classification})")
                    handle.write("\n")
                handle.write("\n")

            # Patrones
            if patterns_data:
                handle.write("-" * 80 + "\n")
                handle.write("🔍 PATRONES DE CONVERSACIÓN DETECTADOS\n")
                handle.write("-" * 80 + "\n")
                for pattern in patterns_data:
                    handle.write(f"  • {pattern.get('name', pattern.get('type', 'N/A'))}: {pattern.get('description', '') or pattern.get('severity', '')}\n")
                handle.write("\n")

            # Anomalías
            if anomalies_data:
                handle.write("-" * 80 + "\n")
                handle.write("⚠️ ANOMALÍAS DETECTADAS\n")
                handle.write("-" * 80 + "\n")
                for anomaly in anomalies_data:
                    handle.write(f"  ⚠️ {anomaly.get('type', 'N/A')}: {anomaly.get('description', anomaly.get('severity', ''))}\n")
                handle.write("\n")

            # Recomendaciones
            handle.write("-" * 80 + "\n")
            handle.write("💡 RECOMENDACIONES\n")
            handle.write("-" * 80 + "\n")

            if qa_score < 50:
                handle.write("  🔴 CRÍTICO: Llamada no cumple estándares mínimos de calidad\n")
                handle.write("     - Revisar protocolo de atención\n")
                handle.write("     - Capacitación urgente requerida\n")
            elif qa_score < 70:
                handle.write("  🟡 ATENCIÓN: Llamada requiere mejoras\n")
                handle.write("     - Reforzar cumplimiento de procedimientos\n")
                handle.write("     - Supervisión cercana recomendada\n")
            else:
                handle.write("  🟢 SATISFACTORIO: Llamada cumple estándares\n")
                handle.write("     - Mantener nivel de servicio\n")

            if 'negative' in str(sentiment_label).lower():
                handle.write("  😞 Sentimiento negativo detectado\n")
                handle.write("     - Evaluar satisfacción del cliente\n")
                handle.write("     - Considerar follow-up\n")

            if risk_level in ['CRÍTICO', 'ALTO', 'HIGH', 'CRITICAL']:
                handle.write(f"  ⚠️ Riesgo {risk_level} identificado\n")
                handle.write("     - Revisión inmediata requerida\n")
                handle.write("     - Escalación a supervisor\n")

            handle.write("\n")
            handle.write("=" * 80 + "\n")
            handle.write("Fin del Reporte\n")
            handle.write("=" * 80 + "\n")

        logger.info("✓ Reporte TXT guardado: %s", filepath)
        return str(filepath)

    except IOError as exc:
        logger.error("❌ Error de I/O guardando reporte: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("❌ Error guardando reporte: %s", exc)
        return None
