"""
Script para generar PDF desde markdown usando ReportLab
"""
import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

def generate_pdf_from_markdown(md_path, pdf_path):
    """
    Convierte archivo markdown a PDF usando ReportLab
    
    Args:
        md_path: Ruta del archivo .md
        pdf_path: Ruta de salida del .pdf
    """
    
    # Leer markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Crear PDF
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#2980b9'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    # Construir documento
    story = []
    current_table = []
    in_table = False
    
    for line in lines:
        line = line.rstrip()
        
        # Saltar líneas vacías en contexto no-tabla
        if not line and not in_table:
            story.append(Spacer(1, 0.1*inch))
            continue
        
        # Headers
        if line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
            story.append(Spacer(1, 0.2*inch))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], heading2_style))
            story.append(Spacer(1, 0.15*inch))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], heading3_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Detectar inicio de tabla
        elif '|' in line and not in_table:
            in_table = True
            # Primera fila (headers)
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            current_table.append(cells)
        
        # Continuar tabla
        elif '|' in line and in_table:
            # Saltar línea separadora (---|---|)
            if '---' in line:
                continue
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            current_table.append(cells)
        
        # Fin de tabla (línea sin |)
        elif not '|' in line and in_table and current_table:
            # Crear tabla
            if current_table:
                # Ajustar anchos de columna
                num_cols = len(current_table[0])
                col_widths = [doc.width / num_cols] * num_cols
                
                t = Table(current_table, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                story.append(t)
                story.append(Spacer(1, 0.2*inch))
            
            current_table = []
            in_table = False
            
            # Procesar línea actual si no está vacía
            if line:
                story.append(Paragraph(line, normal_style))
        
        # Texto normal
        elif line.startswith('**') or line.startswith('- ') or line.startswith('* '):
            story.append(Paragraph(line, normal_style))
        elif line and not line.startswith('#') and not line.startswith('---'):
            story.append(Paragraph(line, normal_style))
    
    # Agregar última tabla si existe
    if in_table and current_table:
        num_cols = len(current_table[0])
        col_widths = [doc.width / num_cols] * num_cols
        t = Table(current_table, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(t)
    
    # Construir PDF
    doc.build(story)
    
    print(f"✅ PDF generado exitosamente: {pdf_path}")


if __name__ == "__main__":
    # Rutas
    project_root = Path(__file__).parent
    md_file = project_root / "DA-01_Especificaciones_y_Casos_de_Uso.md"
    
    # Intentar escritorio primero, luego fallback a carpeta del proyecto
    possible_desktops = [
        Path.home() / "Desktop",
        Path.home() / "Escritorio",
        Path.home() / "OneDrive" / "Desktop",
        Path.home() / "OneDrive" / "Escritorio",
    ]
    
    desktop = None
    for path in possible_desktops:
        if path.exists():
            desktop = path
            break
    
    # Si no se encuentra escritorio, usar carpeta del proyecto
    if desktop is None:
        desktop = project_root
        print("⚠️ No se encontró carpeta del escritorio, usando carpeta del proyecto")
    
    pdf_file = desktop / "da-01.pdf"
    
    print(f"📄 Generando PDF desde: {md_file}")
    print(f"📁 Destino: {pdf_file}")
    
    try:
        generate_pdf_from_markdown(md_file, pdf_file)
        print(f"\n✅ ÉXITO: PDF guardado como '{pdf_file}'")
        if desktop == project_root:
            print(f"📌 Ubicación: {pdf_file.absolute()}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
