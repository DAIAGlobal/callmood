import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Force UTF-8 to avoid console encoding issues with emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
os.environ["PYTHONIOENCODING"] = "utf-8"

# Project paths
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from pipeline import PipelineOrchestrator  # noqa: E402

AUDIO_FILE = ROOT / "audio_in" / "Grabación de llamada 1929_251211_145452.m4a"
DESKTOP_REPORT = Path(r"C:\Users\nicol\OneDrive\Escritorio\da-012.txt")


def main():
    if not AUDIO_FILE.exists():
        raise FileNotFoundError(f"Audio no encontrado: {AUDIO_FILE}")

    pipeline = PipelineOrchestrator(str(ROOT / "config.yaml"))
    levels = ["basic", "standard", "advanced"]
    results = {}

    for level in levels:
        print(f"\n=== Procesando nivel {level.upper()} ===", flush=True)
        res = pipeline.process_audio_file(str(AUDIO_FILE), service_level=level)
        results[level] = {
            "status": res.get("status"),
            "errors": res.get("errors"),
            "processing_time_seconds": res.get("processing_time_seconds"),
            "risk": res.get("data", {}).get("risk", {}),
            "qa": res.get("data", {}).get("qa", {}).get("classification"),
            "sentiment": res.get("data", {}).get("sentiment", {}).get("overall"),
            "patterns": len(res.get("data", {}).get("patterns", [])),
            "anomalies": len(res.get("data", {}).get("anomalies", [])),
        }
        print(json.dumps(results[level], indent=2, ensure_ascii=False), flush=True)

    pipeline.close()

    write_report(results)


def write_report(results: dict) -> None:
    DESKTOP_REPORT.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("DAIA 2.0 - Ejecución niveles BASIC/STANDARD/ADVANCED")
    lines.append(f"Fecha: {ts}")
    lines.append(f"Audio: {AUDIO_FILE.name}")
    lines.append(f"Ubicación audio: {AUDIO_FILE}")
    lines.append("Reportes generados en: reports/ (JSON y TXT por nivel)")
    lines.append("")

    for level, res in results.items():
        lines.append(f"== {level.upper()} ==")
        lines.append(f"Estado: {res.get('status')}")
        lines.append(f"Errores: {res.get('errors')}")
        lines.append(f"Tiempo (s): {res.get('processing_time_seconds')}")
        risk = res.get("risk", {})
        lines.append(f"Riesgo: {risk.get('level')} (score {risk.get('score')})")
        lines.append(f"QA: {res.get('qa')}")
        lines.append(f"Sentimiento: {res.get('sentiment')}")
        lines.append(f"Patrones: {res.get('patterns')} | Anomalías: {res.get('anomalies')}")
        lines.append("")

    lines.append("Notas:")
    lines.append("- Keywords de riesgo leen la clave 'list' del YAML (fix aplicado).")
    lines.append("- Modelos locales (Whisper + HF sentimiento), sin llamadas a la nube.")

    DESKTOP_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReporte guardado en: {DESKTOP_REPORT}")


if __name__ == "__main__":
    main()
