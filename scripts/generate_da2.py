from pathlib import Path
import sys

# Asegurar que el proyecto root esté en sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from generate_pdf import generate_pdf_from_markdown

md_path = project_root / "da-2.0.md"

# Destino solicitado por el usuario
pdf_path = Path(r"C:\Users\nicol\OneDrive\Escritorio\DAIA\daia-landing\da-2.0.pdf")
pdf_path.parent.mkdir(parents=True, exist_ok=True)

print(f"Generando PDF desde: {md_path}")
print(f"Destino: {pdf_path}")

try:
    generate_pdf_from_markdown(md_path, pdf_path)
    print("PDF generado correctamente.")
except Exception as e:
    print(f"Error al generar PDF: {e}")
    raise
