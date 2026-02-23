#!/usr/bin/env python
"""
Generador de PDF para SA-01 — Resolución Técnica
Convierte Markdown extenso a PDF profesional con ReportLab
"""

import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    PageTemplate, Frame, KeepTogether
)
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def generate_sa01_pdf(md_path, pdf_path):
    """
    Genera PDF profesional de SA-01 desde Markdown
    """
    
    # Leer markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Crear PDF
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Estilos personalizados
    styles = getSampleStyleSheet()
    
    # Titulo principal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    h1_style = ParagraphStyle(
        'H1Custom',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    h2_style = ParagraphStyle(
        'H2Custom',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#374151'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    h3_style = ParagraphStyle(
        'H3Custom',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        leftIndent=20,
        fontName='Courier'
    )
    
    # Construir documento
    story = []
    
    # Portada
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        "SA-01 — Resolución Técnica de Reestructuración",
        title_style
    ))
    story.append(Paragraph(
        "Evolución hacia Plataforma Multi-Tenant",
        subtitle_style
    ))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d de %B, %Y')}", normal_style))
    story.append(Paragraph("<b>Versión:</b> 1.0", normal_style))
    story.append(Paragraph("<b>Estado:</b> Ready for Implementation", normal_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Dividir contenido en secciones
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Saltar vacías
        if not line:
            story.append(Spacer(1, 0.08*inch))
            i += 1
            continue
        
        # Títulos
        if line.startswith('# ') and 'SA-01' not in line:
            if story and not isinstance(story[-1], PageBreak):
                story.append(PageBreak())
            story.append(Paragraph(line[2:], h1_style))
            i += 1
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], h2_style))
            i += 1
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], h3_style))
            i += 1
        elif line.startswith('#### '):
            story.append(Paragraph(line[5:], h3_style))
            i += 1
        
        # Tablas (simple detection)
        elif '|' in line and i+1 < len(lines) and '|' in lines[i+1]:
            # Procesar tabla
            table_rows = []
            while i < len(lines) and '|' in lines[i]:
                if '---' in lines[i]:
                    i += 1
                    continue
                cells = [cell.strip() for cell in lines[i].split('|')[1:-1]]
                table_rows.append(cells)
                i += 1
            
            if table_rows:
                # Ajustar anchos
                num_cols = len(table_rows[0])
                col_widths = [doc.width / num_cols] * num_cols
                
                t = Table(table_rows, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3f4f6')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.1*inch))
            continue
        
        # Bloques de código
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # Skip closing ```
            
            code_block = '\n'.join(code_lines)
            story.append(Paragraph("<b>Código:</b>", h3_style))
            for code_line in code_lines[:20]:  # Limitar líneas
                story.append(Paragraph(code_line.replace('<', '&lt;').replace('>', '&gt;'), code_style))
            if len(code_lines) > 20:
                story.append(Paragraph("[...código truncado...]", code_style))
            story.append(Spacer(1, 0.1*inch))
            continue
        
        # Listas (simple bullet points)
        elif line.startswith('- ') or line.startswith('* '):
            bullet_text = line[2:].strip()
            bullet_para = Paragraph(f"• {bullet_text}", normal_style)
            story.append(bullet_para)
            i += 1
        
        # Texto normal
        elif line.strip():
            story.append(Paragraph(line, normal_style))
            i += 1
        else:
            i += 1
    
    # Construir PDF
    doc.build(story)
    print(f"✅ PDF generado: {pdf_path}")


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    md_file = project_root / "SA-01_TECHNICAL_RESOLUTION.md"
    
    # Detectar escritorio
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
    
    if desktop is None:
        desktop = project_root
        print("⚠️ Escritorio no encontrado, usando carpeta del proyecto")
    
    # Path personalizado si es necesario
    desktop_daia = desktop / "DAIA" / "daia-landing"
    desktop_daia.mkdir(parents=True, exist_ok=True)
    
    pdf_file = desktop_daia / "SA-01_Resolucion_Tecnica.pdf"
    
    print(f"📄 Generando PDF desde: {md_file}")
    print(f"📁 Destino: {pdf_file}")
    
    try:
        generate_sa01_pdf(md_file, pdf_file)
        print(f"\n✅ ÉXITO: PDF guardado como '{pdf_file}'")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
