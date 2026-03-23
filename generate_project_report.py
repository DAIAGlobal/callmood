import os
from pathlib import Path

root = Path('c:/dev/daia_call_audit')
file_list_path = root / 'file_list.txt'
output_md = root / 'daia_call_audit_full_report.md'
output_pdf = Path(r'C:/Users/nicol/OneDrive/Escritorio/daia_call_audit_full_report.pdf')

files = [Path(f).relative_to(root) for f in file_list_path.read_text(encoding='utf-8').splitlines() if f.strip()]

# helper

def describe_file(rel_path):
    p = rel_path.as_posix()
    name = rel_path.name
    if p == '.env':
        return 'Configuración de entorno local (variables secretas y de entorno).'
    if p == '.env.example':
        return 'Ejemplo de configuración de entorno para copia y personalización.'
    if p == '.gitignore':
        return 'Ignora archivos generados y sensibles en Git.'
    if name == 'README.md':
        return 'Documentación principal del proyecto.'
    if name.lower().endswith('.md') and rel_path.parts[0] == 'docs':
        return 'Documentación de características y uso del sistema.'
    if rel_path.parts[0] == 'src':
        if 'backend' in rel_path.parts:
            return 'API backend FastAPI y lógica de datos.'
        if 'engine' in rel_path.parts:
            return 'Motor de análisis DAIA (pipeline, reglas, modelos, reportes).'
        if 'gui' in rel_path.parts:
            return 'Interfaz de usuario GUI con PySide6.'
    if rel_path.parts[0] == 'scripts':
        return 'Scripts de ayuda para ejecución y pruebas manuales.'
    if rel_path.parts[0] == 'workers':
        return 'Worker de procesamiento asíncrono (RQ).'
    if rel_path.parts[0] == 'tests':
        return 'Pruebas automatizadas (pytest).'
    if name.endswith('.yml') or name.endswith('.yaml'):
        return 'Archivo de configuración YAML.'
    if name.endswith('.py'):
        return 'Archivo Python con lógica de aplicación.'
    return 'Archivo de proyecto (detalles en función de su ubicación).'

header = '# Reporte de archivos del proyecto DAIA_CALL_AUDIT\n\n'
header += 'Este documento enumera los archivos del proyecto y ofrece una descripción breve de su propósito.\n\n'
header += f'Total de archivos: {len(files)}\n\n'
header += '## Resumen de arquitectura\n'
header += '- API: src/backend/app\n'
header += '- Motor análisis: src/engine/daia\n'
header += '- GUI: src/gui\n'
header += '- Workers: workers\n'
header += '- Scripts: scripts\n'
header += '- Documentación: docs, README.md\n\n'

with output_md.open('w', encoding='utf-8') as f:
    f.write(header)
    f.write('## Lista de archivos clave (no exhaustiva para mantener tamaño manejable)\n\n')
    # list key files and top directories
    interesting = [
        '.env.example', 'README.md', 'docker-compose.yml', 'Dockerfile', 'config.yaml',
    ]
    for pattern in interesting:
        path = root / pattern
        if path.exists():
            rel = path.relative_to(root)
            f.write(f'- `{rel}`: {describe_file(rel)}\n')
    f.write('\n## Detalle por directorio\n\n')

    # sections by high-level dirs
    top_dirs = ['src/backend/app', 'src/engine/daia', 'src/gui', 'scripts', 'workers', 'tests', 'docs']
    for d in top_dirs:
        f.write(f'### {d}\n')
        items = [fp for fp in files if fp.as_posix().startswith(d)]
        f.write(f'- Archivos en carpeta: {len(items)}\n')
        if len(items) <= 40:
            for item in items:
                f.write(f'  - `{item}`: {describe_file(item)}\n')
        else:
            for item in sorted(items)[:20]:
                f.write(f'  - `{item}`: {describe_file(item)}\n')
            f.write(f'  - ... (+{len(items)-20} archivos adicionales)\n')
        f.write('\n')

    f.write('## Indice completo de archivos\n\n')
    for rel in files:
        f.write(f'- `{rel}`: {describe_file(rel)}\n')

# Generar PDF simple (ReportLab)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

text = output_md.read_text(encoding='utf-8').splitlines()

c = canvas.Canvas(str(output_pdf), pagesize=letter)
width, height = letter
x = 0.5*inch
y = height - 0.5*inch
max_height = 0.4*inch

for line in text:
    if y < 0.5*inch:
        c.showPage()
        y = height - 0.5*inch
    if len(line) > 200:
        # wrap
        while line:
            chunk = line[:100]
            c.drawString(x, y, chunk)
            line = line[100:]
            y -= 12
            if y < 0.5*inch:
                c.showPage()
                y = height - 0.5*inch
        continue
    c.drawString(x, y, line)
    y -= 12

c.save()

print('Generated', output_md, 'and', output_pdf)
