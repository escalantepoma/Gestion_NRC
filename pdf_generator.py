import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generar_ficha_pdf(alumno):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=30,
        bottomMargin=30
    )
    
    elementos = []
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle('TituloDoc', parent=styles['Heading1'], alignment=1, fontSize=13, leading=16, spaceAfter=4)
    subtitulo_style = ParagraphStyle('SubtituloDoc', parent=styles['Normal'], alignment=1, fontSize=10, leading=13, textColor=colors.HexColor("#333333"))
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=8.5, fontName="Helvetica-Bold")
    val_style = ParagraphStyle('Val', parent=styles['Normal'], fontSize=8.5, fontName="Helvetica")
    seccion_style = ParagraphStyle('Sec', parent=styles['Normal'], fontSize=9, fontName="Helvetica-Bold", textColor=colors.HexColor("#1A365D"))
    
    # Encabezado
    elementos.append(Paragraph("FICHA DE RATIFICACIÓN DE MATRÍCULA - AÑO ESCOLAR 2026", titulo_style))
    elementos.append(Paragraph("I.E. 7050 NICANOR RIVERA CÁCERES", subtitulo_style))
    elementos.append(Spacer(1, 10))
    
    try:
        f_dt = datetime.strptime(alumno['fecha_ratificacion'], "%Y-%m-%d %H:%M:%S")
    except:
        f_dt = datetime.now()
        
    fecha_texto = f"<b>Fecha de Registro:</b> {f_dt.day:02d} / {f_dt.month:02d} / {f_dt.year} (Hora: {f_dt.strftime('%H:%M')})"
    elementos.append(Paragraph(fecha_texto, val_style))
    elementos.append(Spacer(1, 6))
    
    # Datos Generales
    data_tabla = [
        [Paragraph("Grado y Sección:", label_style), Paragraph(str(alumno['grado_seccion']), val_style)],
        [Paragraph("DNI / Cód. Estudiante:", label_style), Paragraph(str(alumno['codigo_estudiante']), val_style)],
        [Paragraph("Estudiante:", label_style), Paragraph(str(alumno['apellidos_nombres']), val_style)],
        [Paragraph("Padre / Apoderado:", label_style), Paragraph(str(alumno['apoderado_nombres']), val_style)],
        [Paragraph("DNI del Apoderado:", label_style), Paragraph(str(alumno['apoderado_dni']), val_style)],
        [Paragraph("Parentesco:", label_style), Paragraph(str(alumno['parentesco']), val_style)],
        [Paragraph("Dirección Domiciliaria:", label_style), Paragraph(str(alumno['direccion']), val_style)],
        [Paragraph("Teléfono(s):", label_style), Paragraph(str(alumno['telefonos']), val_style)],
        [Paragraph("Observaciones:", label_style), Paragraph(str(alumno['observaciones'] or 'Ninguna'), val_style)],
    ]
    
    t = Table(data_tabla, colWidths=[140, 385])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 10))
    
    # Cuadro de Documentos Recepcionados
    elementos.append(Paragraph("DOCUMENTOS RECEPCIONADOS AL MOMENTO DE LA MATRÍCULA", seccion_style))
    elementos.append(Spacer(1, 4))
    
    def check_box(val):
        return "[ X ]" if val == 1 else "[   ]"
    
    docs_data = [
        [
            Paragraph(f"<b>{check_box(alumno['doc_dni_estudiante'])}</b> DNI del Estudiante", val_style),
            Paragraph(f"<b>{check_box(alumno['doc_compromiso'])}</b> Carta de Compromiso", val_style)
        ],
        [
            Paragraph(f"<b>{check_box(alumno['doc_dni_ppff'])}</b> DNI de PPFF / Apoderado", val_style),
            Paragraph(f"<b>{check_box(alumno['doc_exoneracion_religion'])}</b> Exoneración de Religión", val_style)
        ],
        [
            Paragraph(f"<b>{check_box(alumno['doc_hoja_impresa'])}</b> Hoja Impresa de Matrícula", val_style),
            Paragraph(f"<b>{check_box(alumno['doc_autorizacion_salida'])}</b> Autorización de Salida de la I.E.", val_style)
        ],
        [
            Paragraph(f"<b>{check_box(alumno['doc_gestion_riesgos'])}</b> Ficha de Gestión de Riesgos", val_style),
            Paragraph(f"<b>{check_box(alumno['doc_carta_poder'])}</b> Carta Poder (si aplica)", val_style)
        ]
    ]
    
    t_docs = Table(docs_data, colWidths=[262, 263])
    t_docs.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t_docs)
    elementos.append(Spacer(1, 35))
    
    # Firmas
    firmas_data = [
        [
            Paragraph("___________________________________<br/><b>Firma del Padre / Apoderado</b><br/>DNI: " + str(alumno['apoderado_dni']), subtitulo_style),
            Paragraph("___________________________________<br/><b>Recepción / Secretaría</b><br/>I.E. 7050 Nicanor Rivera Cáceres", subtitulo_style)
        ]
    ]
    t_firmas = Table(firmas_data, colWidths=[262, 263])
    t_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    elementos.append(t_firmas)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()