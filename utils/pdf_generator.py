from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime

def generate_pdf_report(case_data, recommendation):
    """
    Generate PDF report for TAT assessment
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    # ============ HEADER ============
    elements.append(Paragraph("REKOMENDASI TIM ASESMEN TERPADU (TAT)", title_style))
    elements.append(Paragraph("BADAN NARKOTIKA NASIONAL", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Garis pemisah
    elements.append(Table([['', '']], colWidths=[18*cm], 
                         style=TableStyle([('LINEBELOW', (0,0), (-1,-1), 1, colors.black)])))
    elements.append(Spacer(1, 0.5*cm))
    
    # ============ IDENTITAS TERSANGKA ============
    elements.append(Paragraph("I. DATA TERSANGKA", heading_style))
    
    identitas_data = [
        ['Nama', ': ' + case_data.get('nama', '-')],
        ['Usia', ': ' + str(case_data.get('usia', '-')) + ' tahun'],
        ['Jenis Kelamin', ': ' + case_data.get('jenis_kelamin', '-')],
        ['Pendidikan', ': ' + case_data.get('pendidikan', '-')],
        ['Pekerjaan', ': ' + case_data.get('pekerjaan', '-')],
        ['Tanggal Asesmen', ': ' + case_data.get('tanggal_asesmen', '-')],
    ]
    
    identitas_table = Table(identitas_data, colWidths=[5*cm, 12*cm])
    identitas_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(identitas_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # ============ HASIL ASESMEN MEDIS ============
    elements.append(Paragraph("II. HASIL ASESMEN MEDIS", heading_style))
    
    # Tes Urine
    elements.append(Paragraph("<b>A. Hasil Tes Urine</b>", normal_style))
    elements.append(Paragraph(f"Jumlah zat terdeteksi: {case_data.get('positive_tests', 0)} jenis", normal_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Tingkat Kecanduan
    elements.append(Paragraph("<b>B. Tingkat Kecanduan</b>", normal_style))
    kecanduan_data = [
        ['Tingkat Kecanduan', ': ' + case_data.get('addiction_level', '-')],
        ['Skor Kecanduan', ': ' + str(case_data.get('addiction_score', '-')) + '/30'],
        ['Frekuensi Penggunaan', ': ' + case_data.get('frekuensi', '-')],
        ['Durasi Penggunaan', ': ' + case_data.get('durasi', '-')],
    ]
    
    kecanduan_table = Table(kecanduan_data, colWidths=[5*cm, 12*cm])
    kecanduan_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(kecanduan_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Kondisi Medis & Psikologis
    elements.append(Paragraph("<b>C. Kondisi Medis & Psikologis</b>", normal_style))
    kondisi_data = [
        ['Kondisi Fisik', ': ' + case_data.get('kondisi_fisik', '-')],
        ['Dukungan Keluarga', ': ' + case_data.get('dukungan_keluarga', '-')],
        ['Motivasi Pulih', ': ' + str(case_data.get('motivasi_pulih', '-')) + '/10'],
    ]
    
    kondisi_table = Table(kondisi_data, colWidths=[5*cm, 12*cm])
    kondisi_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(kondisi_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # ============ HASIL ASESMEN HUKUM ============
    elements.append(Paragraph("III. HASIL ASESMEN HUKUM", heading_style))
    
    # Barang Bukti
    elements.append(Paragraph("<b>A. Barang Bukti</b>", normal_style))
    bb_data = [
        ['Jenis Narkotika', ': ' + case_data.get('jenis_narkotika', '-')],
        ['Golongan', ': ' + case_data.get('golongan', '-')],
        ['Berat Barang Bukti', ': ' + str(case_data.get('berat_bb', '-')) + ' gram'],
        ['Status', ': ' + ('DI ATAS threshold' if case_data.get('above_threshold') else 'DI BAWAH threshold')],
    ]
    
    bb_table = Table(bb_data, colWidths=[5*cm, 12*cm])
    bb_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(bb_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Indikator Pengedaran
    elements.append(Paragraph("<b>B. Analisis Peran</b>", normal_style))
    peran_data = [
        ['Indikator Pengedaran', ': ' + str(case_data.get('indikator_pengedar', 0)) + '/6 indikator'],
        ['Klasifikasi Peran', ': ' + case_data.get('peran', '-')],
    ]
    
    peran_table = Table(peran_data, colWidths=[5*cm, 12*cm])
    peran_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(peran_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Rekam Jejak
    elements.append(Paragraph("<b>C. Rekam Jejak</b>", normal_style))
    rekam_data = [
        ['Status', ': ' + ('First Offender' if case_data.get('first_offender') else 'Residivis')],
        ['Riwayat Rehabilitasi', ': ' + str(case_data.get('riwayat_rehab', 0)) + ' kali'],
    ]
    
    rekam_table = Table(rekam_data, colWidths=[5*cm, 12*cm])
    rekam_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(rekam_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # ============ SCORING BREAKDOWN ============
    elements.append(Paragraph("IV. ANALISIS SCORING", heading_style))
    
    elements.append(Paragraph(f"<b>Skor Total: {case_data.get('final_score', 0)}</b>", normal_style))
    elements.append(Spacer(1, 0.2*cm))
    
    if 'scoring_details' in case_data:
        elements.append(Paragraph("<b>Rincian Scoring:</b>", normal_style))
        for detail in case_data['scoring_details']:
            elements.append(Paragraph(f"• {detail}", normal_style))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # ============ REKOMENDASI TAT ============
    elements.append(PageBreak())
    elements.append(Paragraph("V. REKOMENDASI TIM ASESMEN TERPADU", heading_style))
    
    # Box rekomendasi utama
    rec_type = recommendation.get('type', '-')
    rec_detail = recommendation.get('detail', '-')
    
    rec_box_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e8f4f8')),
        ('BORDER', (0,0), (-1,-1), 2, colors.HexColor('#1f77b4')),
        ('PADDING', (0,0), (-1,-1), 10),
    ])
    
    rec_content = f"<b><font size=12>{rec_type}</font></b><br/><br/>{rec_detail}"
    rec_table = Table([[Paragraph(rec_content, normal_style)]], colWidths=[17*cm])
    rec_table.setStyle(rec_box_style)
    elements.append(rec_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Program Rehabilitasi
    if recommendation.get('program'):
        elements.append(Paragraph("<b>A. Program Rehabilitasi</b>", normal_style))
        elements.append(Paragraph(recommendation['program'], normal_style))
        elements.append(Spacer(1, 0.3*cm))
    
    # Durasi & Tempat
    if recommendation.get('durasi'):
        elements.append(Paragraph(f"<b>Durasi:</b> {recommendation['durasi']}", normal_style))
    
    if recommendation.get('tempat'):
        elements.append(Paragraph(f"<b>Tempat:</b> {recommendation['tempat']}", normal_style))
    
    elements.append(Spacer(1, 0.3*cm))
    
    # Monitoring
    if recommendation.get('monitoring'):
        elements.append(Paragraph("<b>B. Monitoring & Evaluasi</b>", normal_style))
        elements.append(Paragraph(recommendation['monitoring'], normal_style))
        elements.append(Spacer(1, 0.3*cm))
    
    # Dasar Hukum
    elements.append(Paragraph("<b>C. Dasar Hukum</b>", normal_style))
    elements.append(Paragraph(recommendation.get('dasar_hukum', '-'), normal_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Catatan Khusus
    if recommendation.get('catatan'):
        elements.append(Paragraph("<b>D. Catatan Khusus</b>", normal_style))
        catatan_box = Table([[Paragraph(recommendation['catatan'], normal_style)]], colWidths=[17*cm])
        catatan_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff3cd')),
            ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#ffc107')),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(catatan_box)
    
    elements.append(Spacer(1, 1*cm))
    
    # ============ TANDA TANGAN ============
    elements.append(Paragraph("Demikian rekomendasi ini dibuat untuk dapat dipergunakan sebagaimana mestinya.", 
                             normal_style))
    elements.append(Spacer(1, 0.5*cm))
    
    today = datetime.now().strftime("%d %B %Y")
    elements.append(Paragraph(f"[Kota], {today}", normal_style))
    elements.append(Spacer(1, 1*cm))
    
    # Tabel tanda tangan
    ttd_data = [
        ['TIM MEDIS', 'TIM HUKUM'],
        ['', ''],
        ['', ''],
        ['', ''],
        ['_________________', '_________________'],
        ['[Nama]', '[Nama]'],
        ['[Jabatan]', '[Jabatan/Institusi]'],
    ]
    
    ttd_table = Table(ttd_data, colWidths=[8.5*cm, 8.5*cm])
    ttd_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(ttd_table)
    
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("Mengetahui,", ParagraphStyle('Center', alignment=TA_CENTER)))
    elements.append(Paragraph("Ketua Tim Asesmen Terpadu,", ParagraphStyle('Center', alignment=TA_CENTER)))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("_________________", ParagraphStyle('Center', alignment=TA_CENTER)))
    elements.append(Paragraph("[Nama]", ParagraphStyle('Center', alignment=TA_CENTER)))
    elements.append(Paragraph("[Jabatan]", ParagraphStyle('Center', alignment=TA_CENTER)))
    
    # Footer
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("─" * 80, ParagraphStyle('Center', alignment=TA_CENTER, fontSize=8)))
    elements.append(Paragraph("Dokumen ini dihasilkan oleh TAT Decision Support System v1.0", 
                             ParagraphStyle('Center', alignment=TA_CENTER, fontSize=8, textColor=colors.grey)))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
