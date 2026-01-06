"""
=================================================================================
SISTEM PREDIKSI TAT (TIM ASESMEN TERPADU) BNN
=================================================================================
Tools bantu untuk proses asesmen narkotika berdasarkan:
- UU No. 35 Tahun 2009 tentang Narkotika
- SEMA No. 4 Tahun 2010
- Peraturan Bersama 7 Instansi No. 01/PB/MA/III/2014
- Perka BNN No. 11 Tahun 2014
- Instrumen Asesmen: ASAM, ASSIST, DSM-5, ICD-10

CATATAN PENTING:
Sistem ini adalah ALAT BANTU untuk Tim Asesmen Terpadu.
Keputusan final tetap ada di tangan BNN dan aparat penegak hukum.
=================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# =============================================================================
# KONFIGURASI HALAMAN
# =============================================================================
st.set_page_config(
    page_title="TAT Predictor - BNN",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# KONSTANTA DAN KONFIGURASI
# =============================================================================

# Gramatur berdasarkan SEMA 4/2010
GRAMATUR_LIMITS = {
    "Ganja/Cannabis": 5.0,
    "Metamfetamin/Sabu": 1.0,
    "Heroin": 1.8,
    "Kokain": 1.8,
    "Ekstasi/MDMA": 2.4,
    "Morfin": 1.8,
    "Kodein": 72.0,
    "Lainnya": 1.0
}

# Jenis-jenis narkotika untuk tes urine
JENIS_NARKOTIKA = [
    "Metamfetamin (MET/Sabu)",
    "Morfin (MOP/Heroin)",
    "Kokain (COC)",
    "Amfetamin (AMP)",
    "Benzodiazepin (BZO)",
    "THC (Ganja)",
    "MDMA (Ekstasi)",
    "Lainnya"
]

# Kriteria DSM-5 (11 kriteria gangguan penggunaan zat)
DSM5_CRITERIA = [
    "Menggunakan dalam jumlah/waktu lebih lama dari yang direncanakan",
    "Keinginan kuat/gagal mengurangi penggunaan",
    "Banyak waktu untuk mendapatkan/menggunakan/pulih dari efek",
    "Craving (keinginan kuat menggunakan)",
    "Gagal memenuhi kewajiban (kerja/sekolah/rumah)",
    "Terus menggunakan meski ada masalah sosial/interpersonal",
    "Mengurangi/meninggalkan aktivitas penting karena penggunaan",
    "Menggunakan dalam situasi berbahaya",
    "Terus menggunakan meski tahu ada masalah fisik/psikologis",
    "Toleransi (butuh dosis lebih tinggi)",
    "Withdrawal/Sakau (gejala putus zat)"
]

# =============================================================================
# FUNGSI GENERATE PDF
# =============================================================================

def _safe_add_style(styles, style_obj):
    """
    Mencegah KeyError pada ReportLab ketika nama style sudah ada di stylesheet.
    - Jika sudah ada, return style yang existing.
    - Jika belum ada, add dan return.
    """
    name = getattr(style_obj, "name", None)
    if not name:
        return style_obj
    if name in styles.byName:
        return styles.byName[name]
    styles.add(style_obj)
    return styles.byName[name]


def generate_pdf_report(export_data):
    """Generate PDF report from analysis data (fix: avoid duplicate style names)"""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=72
    )

    elements = []
    styles = getSampleStyleSheet()

    # Pakai NAMA CUSTOM supaya tidak bentrok dengan bawaan ('Title', 'Heading1', dst)
    style_center = _safe_add_style(
        styles,
        ParagraphStyle(name="TAT_Center", parent=styles["Normal"], alignment=TA_CENTER)
    )
    style_left = _safe_add_style(
        styles,
        ParagraphStyle(name="TAT_Left", parent=styles["Normal"], alignment=TA_LEFT)
    )
    style_title = _safe_add_style(
        styles,
        ParagraphStyle(
            name="TAT_Title",
            parent=styles["Title"],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20
        )
    )
    style_h1 = _safe_add_style(
        styles,
        ParagraphStyle(
            name="TAT_H1",
            parent=styles["Heading1"],
            fontSize=14,
            alignment=TA_LEFT,
            spaceAfter=12
        )
    )
    style_h2 = _safe_add_style(
        styles,
        ParagraphStyle(
            name="TAT_H2",
            parent=styles["Heading2"],
            fontSize=12,
            alignment=TA_LEFT,
            spaceAfter=8
        )
    )

    # Title
    elements.append(Paragraph("LAPORAN ANALISIS TAT - BNN", style_title))
    elements.append(Paragraph(f"Waktu Analisis: {export_data.get('timestamp', '-')}", style_center))
    elements.append(Spacer(1, 20))

    # Summary Section
    elements.append(Paragraph("RINGKASAN HASIL", style_h1))

    summary_data = [
        ["Parameter", "Nilai"],
        ["Skor Asesmen Medis", f"{export_data.get('skor_medis', 0)}/100"],
        ["Skor Asesmen Hukum", f"{export_data.get('skor_hukum', 0)}/100"],
        ["Composite Score", f"{float(export_data.get('final_score', 0.0)):.1f}/100"],
        ["Rekomendasi Utama", export_data.get("rekomendasi_utama", "-")],
        ["Tingkat Keyakinan", f"{float(export_data.get('confidence', 0.0)):.1f}%"],
    ]

    summary_table = Table(summary_data, colWidths=[2.5 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Breakdown Medis
    elements.append(Paragraph("BREAKDOWN ASESMEN MEDIS", style_h1))
    medis_data = [["Kategori", "Skor", "Detail"]]
    for kategori, data in (export_data.get("breakdown_medis", {}) or {}).items():
        medis_data.append([
            str(kategori),
            f"{data.get('skor', 0)}/{data.get('max', 0)}",
            str(data.get('detail', ''))
        ])

    medis_table = Table(medis_data, colWidths=[1.5 * inch, 1 * inch, 3 * inch])
    medis_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(medis_table)
    elements.append(Spacer(1, 20))

    # Breakdown Hukum
    elements.append(Paragraph("BREAKDOWN ASESMEN HUKUM", style_h1))
    hukum_data = [["Kategori", "Skor", "Detail"]]
    for kategori, data in (export_data.get("breakdown_hukum", {}) or {}).items():
        hukum_data.append([
            str(kategori),
            f"{data.get('skor', 0)}/{data.get('max', 0)}",
            str(data.get('detail', ''))
        ])

    hukum_table = Table(hukum_data, colWidths=[1.5 * inch, 1 * inch, 3 * inch])
    hukum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(hukum_table)
    elements.append(Spacer(1, 20))

    # Probabilities
    elements.append(Paragraph("DISTRIBUSI PROBABILITAS", style_h1))
    prob_data = [["Rekomendasi", "Probabilitas (%)", "Status"]]
    rekom_utama = export_data.get("rekomendasi_utama", "")
    for rec, prob in (export_data.get("probabilities", {}) or {}).items():
        status = "PRIMARY" if rec == rekom_utama else "ALTERNATIVE"
        prob_data.append([str(rec), f"{float(prob):.1f}%", status])

    prob_table = Table(prob_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])
    prob_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(prob_table)
    elements.append(Spacer(1, 20))

    # Reasoning
    elements.append(Paragraph("ALASAN DAN PERTIMBANGAN", style_h1))
    for reason in (export_data.get("reasoning", []) or []):
        elements.append(Paragraph(f"• {reason}", style_left))

    elements.append(Spacer(1, 20))

    # Footer
    elements.append(Paragraph("CATATAN PENTING:", style_h2))
    elements.append(Paragraph("Sistem ini adalah ALAT BANTU untuk proses asesmen.", style_left))
    elements.append(Paragraph("Keputusan final tetap berada di tangan Tim Asesmen Terpadu BNN.", style_left))
    elements.append(Paragraph(
        f"Dokumen ini dihasilkan oleh Sistem Prediksi TAT BNN pada {export_data.get('timestamp', '-')}",
        style_center
    ))

    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_txt_report(export_data):
    """Generate TXT report from analysis data"""
    txt_content = []
    txt_content.append("=" * 60)
    txt_content.append("LAPORAN ANALISIS TAT - BADAN NARKOTIKA NASIONAL")
    txt_content.append("=" * 60)
    txt_content.append(f"Waktu Analisis: {export_data['timestamp']}")
    txt_content.append("")

    # Summary
    txt_content.append("RINGKASAN HASIL")
    txt_content.append("-" * 40)
    txt_content.append(f"Skor Asesmen Medis: {export_data['skor_medis']}/100")
    txt_content.append(f"Skor Asesmen Hukum: {export_data['skor_hukum']}/100")
    txt_content.append(f"Composite Score: {export_data['final_score']:.1f}/100")
    txt_content.append(f"Rekomendasi Utama: {export_data['rekomendasi_utama']}")
    txt_content.append(f"Tingkat Keyakinan: {export_data['confidence']:.1f}%")
    txt_content.append("")

    # Breakdown Medis
    txt_content.append("BREAKDOWN ASESMEN MEDIS")
    txt_content.append("-" * 40)
    for kategori, data in export_data['breakdown_medis'].items():
        txt_content.append(f"{kategori}: {data['skor']}/{data['max']} - {data['detail']}")
    txt_content.append("")

    # Breakdown Hukum
    txt_content.append("BREAKDOWN ASESMEN HUKUM")
    txt_content.append("-" * 40)
    for kategori, data in export_data['breakdown_hukum'].items():
        txt_content.append(f"{kategori}: {data['skor']}/{data['max']} - {data['detail']}")
    txt_content.append("")

    # Probabilities
    txt_content.append("DISTRIBUSI PROBABILITAS")
    txt_content.append("-" * 40)
    for rec, prob in export_data['probabilities'].items():
        status = " (PRIMARY)" if rec == export_data['rekomendasi_utama'] else ""
        txt_content.append(f"{rec}: {prob:.1f}%{status}")
    txt_content.append("")

    # Reasoning
    txt_content.append("ALASAN DAN PERTIMBANGAN")
    txt_content.append("-" * 40)
    for reason in export_data['reasoning']:
        txt_content.append(f"• {reason}")
    txt_content.append("")

    # Footer
    txt_content.append("=" * 60)
    txt_content.append("CATATAN PENTING:")
    txt_content.append("- Sistem ini adalah ALAT BANTU untuk proses asesmen.")
    txt_content.append("- Keputusan final tetap berada di tangan Tim Asesmen Terpadu BNN.")
    txt_content.append("=" * 60)

    return "\n".join(txt_content)

# =============================================================================
# FUNGSI PERHITUNGAN SKOR
# =============================================================================

def calculate_medical_score(zat_positif, dsm5_count, durasi_bulan,
                           fungsi_sosial, ada_komorbid, tingkat_komorbid):
    """
    Menghitung Skor Asesmen Medis (0-100 poin)

    Komponen:
    1. Hasil Tes Urine (0-25 poin)
    2. Tingkat Kecanduan DSM-5 (0-30 poin)
    3. Durasi Penggunaan (0-15 poin)
    4. Dampak Fungsi Sosial (0-15 poin)
    5. Kondisi Komorbid (0-15 poin)
    """
    score = 0
    breakdown = {}

    # 1. Hasil Tes Urine (0-25 poin)
    num_zat = len(zat_positif)
    if num_zat == 0:
        urine_score = 0
    elif num_zat == 1:
        urine_score = 10
    elif num_zat <= 3:
        urine_score = 15
    else:  # Polisubstansi (≥4 zat)
        urine_score = 25

    breakdown['Tes Urine'] = {
        'skor': urine_score,
        'max': 25,
        'detail': f"{num_zat} zat terdeteksi positif"
    }
    score += urine_score

    # 2. Tingkat Kecanduan berdasarkan DSM-5 (0-30 poin)
    if dsm5_count <= 1:
        addiction_score = 0
        severity = "Tidak ada gangguan"
    elif dsm5_count <= 3:
        addiction_score = 10
        severity = "Ringan (Mild)"
    elif dsm5_count <= 5:
        addiction_score = 20
        severity = "Sedang (Moderate)"
    else:  # ≥6 kriteria
        addiction_score = 30
        severity = "Berat (Severe)"

    breakdown['Tingkat Kecanduan'] = {
        'skor': addiction_score,
        'max': 30,
        'detail': f"{dsm5_count}/11 kriteria DSM-5 - {severity}"
    }
    score += addiction_score

    # 3. Durasi Penggunaan (0-15 poin)
    if durasi_bulan < 6:
        duration_score = 5
        duration_label = "< 6 bulan"
    elif durasi_bulan <= 12:
        duration_score = 10
        duration_label = "6-12 bulan"
    else:
        duration_score = 15
        duration_label = "> 12 bulan"

    breakdown['Durasi Penggunaan'] = {
        'skor': duration_score,
        'max': 15,
        'detail': f"{durasi_bulan} bulan ({duration_label})"
    }
    score += duration_score

    # 4. Dampak Fungsi Sosial (0-15 poin)
    if fungsi_sosial == "Masih produktif (sekolah/kerja)":
        social_score = 0
    elif fungsi_sosial == "Mulai terganggu":
        social_score = 8
    else:  # "Tidak berfungsi sama sekali"
        social_score = 15

    breakdown['Fungsi Sosial'] = {
        'skor': social_score,
        'max': 15,
        'detail': fungsi_sosial
    }
    score += social_score

    # 5. Kondisi Komorbid (0-15 poin)
    if not ada_komorbid:
        comorbid_score = 0
        comorbid_detail = "Tidak ada"
    elif tingkat_komorbid == "Ringan":
        comorbid_score = 8
        comorbid_detail = "Gangguan psikologis ringan"
    else:  # "Berat"
        comorbid_score = 15
        comorbid_detail = "Gangguan psikiatrik/medis serius"

    breakdown['Komorbid'] = {
        'skor': comorbid_score,
        'max': 15,
        'detail': comorbid_detail
    }
    score += comorbid_score

    return score, breakdown


def calculate_legal_score(peran, barang_bukti, jenis_narkotika,
                          status_tangkap, riwayat_pidana):
    """
    Menghitung Skor Asesmen Hukum (0-100 poin)

    Komponen:
    1. Keterlibatan Jaringan Peredaran (0-40 poin)
    2. Barang Bukti vs Gramatur SEMA (0-25 poin)
    3. Status Penangkapan (0-15 poin)
    4. Riwayat Pidana (0-20 poin)
    """
    score = 0
    breakdown = {}

    # 1. Keterlibatan Jaringan Peredaran (0-40 poin)
    role_mapping = {
        "Pengguna murni (untuk diri sendiri)": 0,
        "Berbagi dengan teman (sharing)": 15,
        "Kurir/pengedar kecil": 25,
        "Pengedar besar/bandar": 40
    }
    network_score = role_mapping[peran]
    breakdown['Keterlibatan Jaringan'] = {
        'skor': network_score,
        'max': 40,
        'detail': peran
    }
    score += network_score

    # 2. Barang Bukti vs Gramatur SEMA (0-25 poin)
    gramatur_limit = GRAMATUR_LIMITS.get(jenis_narkotika, 1.0)

    if barang_bukti < gramatur_limit:
        evidence_score = 0
        evidence_label = f"Di bawah gramatur SEMA (< {gramatur_limit}g)"
    elif barang_bukti <= gramatur_limit * 5:
        evidence_score = 10
        evidence_label = f"1-5x gramatur SEMA ({gramatur_limit}-{gramatur_limit*5}g)"
    elif barang_bukti <= gramatur_limit * 20:
        evidence_score = 18
        evidence_label = f"5-20x gramatur SEMA"
    else:
        evidence_score = 25
        evidence_label = f"Lebih dari 20x gramatur SEMA (> {gramatur_limit*20}g)"

    breakdown['Barang Bukti'] = {
        'skor': evidence_score,
        'max': 25,
        'detail': f"{barang_bukti}g - {evidence_label}"
    }
    score += evidence_score

    # 3. Status Penangkapan (0-15 poin)
    arrest_mapping = {
        "Sukarela datang untuk asesmen": 0,
        "Operasi targeted (penggerebekan terencana)": 8,
        "Tertangkap tangan saat transaksi": 15
    }
    arrest_score = arrest_mapping[status_tangkap]
    breakdown['Status Penangkapan'] = {
        'skor': arrest_score,
        'max': 15,
        'detail': status_tangkap
    }
    score += arrest_score

    # 4. Riwayat Pidana (0-20 poin)
    history_mapping = {
        "First offender (pertama kali)": 0,
        "Pernah rehab sebelumnya (relapse)": 10,
        "Residivis kasus narkotika": 20
    }
    history_score = history_mapping[riwayat_pidana]
    breakdown['Riwayat Pidana'] = {
        'skor': history_score,
        'max': 20,
        'detail': riwayat_pidana
    }
    score += history_score

    return score, breakdown


def apply_decision_rules(skor_medis, skor_hukum, breakdown_medis, breakdown_hukum):
    """
    Menerapkan Decision Rules untuk menghasilkan probabilitas rekomendasi

    Berdasarkan:
    - SEMA 4/2010
    - Kriteria TAT BNN
    - Best practices rehabilitasi
    """
    final_score = (skor_medis * 0.6) + (skor_hukum * 0.4)

    probabilities = {
        "Rehabilitasi Rawat Jalan": 0,
        "Rehabilitasi Rawat Inap": 0,
        "Proses Hukum": 0,
        "Proses Hukum + Rehabilitasi": 0
    }

    reasoning = []
    primary_recommendation = ""

    # RULE 1: REHABILITASI RAWAT JALAN
    if (20 <= skor_medis <= 50 and
        skor_hukum <= 20 and
        breakdown_medis['Fungsi Sosial']['skor'] <= 8):

        probabilities["Rehabilitasi Rawat Jalan"] = 85
        reasoning.append("✓ Tingkat kecanduan ringan-sedang (20-50 poin)")
        reasoning.append("✓ Tidak ada keterlibatan jaringan signifikan")
        reasoning.append("✓ Masih berfungsi sosial (produktif)")
        reasoning.append("✓ Sesuai kriteria rawat jalan")
        primary_recommendation = "Rehabilitasi Rawat Jalan"

    # RULE 2: REHABILITASI RAWAT INAP
    elif (skor_medis > 50 and
          skor_hukum <= 25 and
          (breakdown_medis['Fungsi Sosial']['skor'] >= 8 or
           breakdown_medis['Komorbid']['skor'] >= 8)):

        probabilities["Rehabilitasi Rawat Inap"] = 80
        reasoning.append("✓ Tingkat ketergantungan berat (>50 poin)")
        reasoning.append("✓ Butuh pengawasan intensif 24 jam")
        reasoning.append("✓ Gangguan fungsi sosial atau komorbid serius")
        reasoning.append("✓ Tidak ada bukti penjualan/peredaran besar")
        primary_recommendation = "Rehabilitasi Rawat Inap"

    # RULE 3: PROSES HUKUM
    elif (skor_hukum > 40 and
          breakdown_hukum['Barang Bukti']['skor'] >= 18 and
          skor_medis < 40):

        probabilities["Proses Hukum"] = 75
        reasoning.append("✗ Indikasi kuat keterlibatan peredaran")
        reasoning.append("✗ Barang bukti signifikan")
        reasoning.append("✗ Tingkat kecanduan tidak dominan")
        reasoning.append("✗ Memenuhi kriteria tindak pidana peredaran")
        primary_recommendation = "Proses Hukum"

    # RULE 4: PROSES HUKUM + REHABILITASI
    elif (skor_medis > 50 and
          skor_hukum > 30):

        probabilities["Proses Hukum + Rehabilitasi"] = 85
        reasoning.append("! Pecandu berat dengan ketergantungan severe")
        reasoning.append("! Sekaligus terlibat dalam peredaran narkotika")
        reasoning.append("! Memerlukan dual intervention:")
        reasoning.append("  → Rehabilitasi untuk mengatasi kecanduan")
        reasoning.append("  → Proses hukum untuk aspek peredaran")
        primary_recommendation = "Proses Hukum + Rehabilitasi"

    # EDGE CASES
    else:
        if skor_medis > skor_hukum * 1.5:
            if skor_medis > 60:
                probabilities["Rehabilitasi Rawat Inap"] = 70
                primary_recommendation = "Rehabilitasi Rawat Inap"
                reasoning.append("✓ Aspek medis sangat dominan (severe addiction)")
            else:
                probabilities["Rehabilitasi Rawat Jalan"] = 65
                primary_recommendation = "Rehabilitasi Rawat Jalan"
                reasoning.append("✓ Aspek medis dominan (moderate addiction)")

        elif skor_hukum > skor_medis * 1.5:
            probabilities["Proses Hukum"] = 70
            primary_recommendation = "Proses Hukum"
            reasoning.append("✗ Aspek hukum sangat dominan")

        else:
            probabilities["Proses Hukum + Rehabilitasi"] = 60
            primary_recommendation = "Proses Hukum + Rehabilitasi"
            reasoning.append("! Skor medis dan hukum relatif seimbang")
            reasoning.append("! Perlu evaluasi mendalam Tim Asesmen Terpadu")

    if breakdown_hukum['Barang Bukti']['skor'] == 0:
        reasoning.append("• Barang bukti di bawah gramatur SEMA 4/2010")

    if breakdown_hukum['Riwayat Pidana']['skor'] >= 10:
        reasoning.append("⚠ Catatan: Ada riwayat kasus sebelumnya")

    total_prob = sum(probabilities.values())
    if total_prob > 100:
        probabilities = {k: (v / total_prob) * 100 for k, v in probabilities.items()}

    remaining = 100 - probabilities[primary_recommendation]
    other_options = [k for k in probabilities.keys() if k != primary_recommendation]
    for opt in other_options:
        probabilities[opt] = remaining / len(other_options)

    return probabilities, reasoning, primary_recommendation, final_score

# =============================================================================
# FUNGSI VISUALISASI
# =============================================================================

def create_gauge_chart(score, title, max_score=100):
    """Membuat gauge chart untuk visualisasi skor"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        delta={'reference': max_score / 2},
        gauge={
            'axis': {'range': [None, max_score], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_score / 3], 'color': "lightgreen"},
                {'range': [max_score / 3, 2 * max_score / 3], 'color': "yellow"},
                {'range': [2 * max_score / 3, max_score], 'color': "salmon"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_score * 0.8
            }
        }
    ))
    fig.update_layout(height=300)
    return fig


def create_breakdown_chart(breakdown, title):
    """Membuat horizontal bar chart untuk breakdown skor"""
    categories = list(breakdown.keys())
    scores = [breakdown[cat]['skor'] for cat in categories]
    max_scores = [breakdown[cat]['max'] for cat in categories]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=categories,
        x=scores,
        name='Skor Aktual',
        orientation='h',
        marker=dict(color='#1f77b4'),
        text=scores,
        textposition='auto',
    ))

    fig.add_trace(go.Bar(
        y=categories,
        x=[max_scores[i] - scores[i] for i in range(len(scores))],
        name='Sisa Skor',
        orientation='h',
        marker=dict(color='#d3d3d3'),
        showlegend=False
    ))

    fig.update_layout(
        title=title,
        barmode='stack',
        height=400,
        xaxis_title="Poin",
        yaxis_title="Kategori",
        showlegend=True
    )

    return fig


def create_probability_chart(probabilities):
    """Membuat bar chart untuk probabilitas rekomendasi"""
    categories = list(probabilities.keys())
    values = list(probabilities.values())

    colors_list = ['#28a745' if v == max(values) else '#17a2b8' for v in values]

    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors_list,
            text=[f"{v:.1f}%" for v in values],
            textposition='auto',
        )
    ])

    fig.update_layout(
        title="Distribusi Probabilitas Rekomendasi",
        xaxis_title="Jenis Rekomendasi",
        yaxis_title="Probabilitas (%)",
        yaxis=dict(range=[0, 100]),
        height=400
    )

    return fig

# =============================================================================
# APLIKASI UTAMA
# =============================================================================

def main():
    st.markdown('<h1 class="main-header">⚖️ SISTEM PREDIKSI TAT BNN</h1>',
                unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Tools Bantu Tim Asesmen Terpadu - Penanganan Penyalahguna Narkotika</p>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ PERHATIAN PENTING:</strong><br>
        Sistem ini adalah <strong>ALAT BANTU</strong> untuk proses asesmen.
        Keputusan final tetap berada di tangan <strong>Tim Asesmen Terpadu BNN</strong>
        dan aparat penegak hukum yang berwenang.
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("📋 Dasar Hukum")
        st.markdown("""
        **Regulasi yang Digunakan:**
        - UU No. 35 Tahun 2009 tentang Narkotika
        - SEMA No. 4 Tahun 2010
        - Peraturan Bersama 7 Instansi (2014)
        - Perka BNN No. 11 Tahun 2014

        **Instrumen Asesmen:**
        - ASAM (6 Dimensi)
        - DSM-5 (11 Kriteria)
        - ASSIST
        - DAST-10
        """)
        st.markdown("---")
        st.info("**Versi:** 1.0.0\n\n**Update:** Desember 2025")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Input Data",
        "📊 Hasil Analisis",
        "📈 Visualisasi Detail",
        "ℹ️ Panduan"
    ])

    # ======================================================================
    # TAB 1: INPUT DATA
    # ======================================================================
    with tab1:
        st.header("📋 Input Data Asesmen")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏥 ASESMEN MEDIS")

            with st.expander("👤 Informasi Identitas (Opsional)", expanded=False):
                nama_inisial = st.text_input("Inisial Nama", placeholder="Contoh: AB")
                usia = st.number_input("Usia", min_value=0, max_value=100, value=25)
                jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])

            st.markdown("---")

            st.markdown("**1️⃣ Hasil Tes Urine/Laboratorium**")
            zat_positif = st.multiselect(
                "Zat yang terdeteksi POSITIF:",
                JENIS_NARKOTIKA,
                help="Pilih semua zat yang terdeteksi positif dalam tes urine/lab"
            )

            st.markdown("---")

            st.markdown("**2️⃣ Kriteria DSM-5 (Gangguan Penggunaan Zat)**")
            st.caption("Berikan tanda centang pada kriteria yang terpenuhi:")

            dsm5_checked = []
            for i, criteria in enumerate(DSM5_CRITERIA, 1):
                if st.checkbox(f"{i}. {criteria}", key=f"dsm5_{i}"):
                    dsm5_checked.append(criteria)

            dsm5_count = len(dsm5_checked)

            if dsm5_count == 0:
                st.info("Tidak ada kriteria terpenuhi")
            elif dsm5_count <= 1:
                st.info(f"**{dsm5_count}/11** - Belum memenuhi kriteria gangguan")
            elif dsm5_count <= 3:
                st.warning(f"**{dsm5_count}/11** - Gangguan Penggunaan **RINGAN**")
            elif dsm5_count <= 5:
                st.warning(f"**{dsm5_count}/11** - Gangguan Penggunaan **SEDANG**")
            else:
                st.error(f"**{dsm5_count}/11** - Gangguan Penggunaan **BERAT**")

            st.markdown("---")

            st.markdown("**3️⃣ Durasi Penggunaan Narkotika**")
            durasi_bulan = st.number_input(
                "Berapa lama sudah menggunakan? (dalam bulan)",
                min_value=0,
                max_value=240,
                value=6,
                help="Estimasi durasi penggunaan narkotika"
            )

            st.markdown("---")

            st.markdown("**4️⃣ Status Fungsi Sosial/Okupasional**")
            fungsi_sosial = st.radio(
                "Bagaimana fungsi sosial klien saat ini?",
                [
                    "Masih produktif (sekolah/kerja)",
                    "Mulai terganggu",
                    "Tidak berfungsi sama sekali"
                ],
                help="Penilaian terhadap kemampuan menjalankan fungsi sehari-hari"
            )

            st.markdown("---")

            st.markdown("**5️⃣ Kondisi Komorbid (Gangguan Penyerta)**")
            ada_komorbid = st.checkbox(
                "Ada gangguan psikiatrik/medis komorbid?",
                help="Gangguan kesehatan mental atau fisik yang menyertai"
            )

            tingkat_komorbid = None
            if ada_komorbid:
                tingkat_komorbid = st.radio(
                    "Tingkat keparahan komorbid:",
                    ["Ringan", "Berat"],
                    help="Ringan: gangguan anxietas, depresi ringan, dll.\nBerat: gangguan psikotik, bipolar, penyakit fisik serius"
                )

        with col2:
            st.subheader("⚖️ ASESMEN HUKUM")

            st.markdown("**1️⃣ Peran Tersangka/Terdakwa**")
            peran = st.selectbox(
                "Indikasi peran dalam kasus:",
                [
                    "Pengguna murni (untuk diri sendiri)",
                    "Berbagi dengan teman (sharing)",
                    "Kurir/pengedar kecil",
                    "Pengedar besar/bandar"
                ],
                help="Berdasarkan hasil investigasi dan keterangan"
            )

            st.markdown("---")

            st.markdown("**2️⃣ Barang Bukti Narkotika**")
            jenis_narkotika = st.selectbox(
                "Jenis narkotika yang disita:",
                list(GRAMATUR_LIMITS.keys()),
                help="Pilih jenis narkotika sesuai barang bukti"
            )

            gramatur_limit = GRAMATUR_LIMITS[jenis_narkotika]

            barang_bukti = st.number_input(
                f"Jumlah barang bukti (gram):",
                min_value=0.0,
                max_value=1000.0,
                value=0.5,
                step=0.1,
                help=f"Gramatur SEMA 4/2010 untuk {jenis_narkotika}: ≤ {gramatur_limit}g"
            )

            if barang_bukti < gramatur_limit:
                st.success(f"✓ Di bawah gramatur SEMA (< {gramatur_limit}g)")
            elif barang_bukti <= gramatur_limit * 2:
                st.warning(f"⚠ Mendekati/sedikit di atas gramatur SEMA")
            else:
                st.error(f"✗ Jauh melebihi gramatur SEMA (> {gramatur_limit}g)")

            st.markdown("---")

            st.markdown("**3️⃣ Status Penangkapan**")
            status_tangkap = st.selectbox(
                "Bagaimana klien ditangkap/datang?",
                [
                    "Sukarela datang untuk asesmen",
                    "Operasi targeted (penggerebekan terencana)",
                    "Tertangkap tangan saat transaksi"
                ],
                help="Modus penangkapan/kedatangan klien"
            )

            st.markdown("---")

            st.markdown("**4️⃣ Riwayat Pidana/Rehabilitasi**")
            riwayat_pidana = st.radio(
                "Status riwayat kasus sebelumnya:",
                [
                    "First offender (pertama kali)",
                    "Pernah rehab sebelumnya (relapse)",
                    "Residivis kasus narkotika"
                ],
                help="Riwayat keterlibatan kasus narkotika sebelumnya"
            )

        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn2:
            analyze_button = st.button(
                "🔍 ANALISIS & PREDIKSI",
                use_container_width=True,
                type="primary"
            )

    # ======================================================================
    # TAB 2: HASIL ANALISIS
    # ======================================================================
    with tab2:
        if 'analyze_button' in locals() and analyze_button:
            with st.spinner('🔄 Melakukan analisis...'):
                skor_medis, breakdown_medis = calculate_medical_score(
                    zat_positif, dsm5_count, durasi_bulan,
                    fungsi_sosial, ada_komorbid, tingkat_komorbid
                )

                skor_hukum, breakdown_hukum = calculate_legal_score(
                    peran, barang_bukti, jenis_narkotika,
                    status_tangkap, riwayat_pidana
                )

                probabilities, reasoning, primary_rec, final_score = apply_decision_rules(
                    skor_medis, skor_hukum, breakdown_medis, breakdown_hukum
                )

                st.session_state['results'] = {
                    'skor_medis': skor_medis,
                    'skor_hukum': skor_hukum,
                    'breakdown_medis': breakdown_medis,
                    'breakdown_hukum': breakdown_hukum,
                    'probabilities': probabilities,
                    'reasoning': reasoning,
                    'primary_rec': primary_rec,
                    'final_score': final_score,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'input_data': {
                        'nama_inisial': nama_inisial,
                        'usia': usia,
                        'jenis_kelamin': jenis_kelamin,
                        'zat_positif': zat_positif,
                        'dsm5_count': dsm5_count,
                        'durasi_bulan': durasi_bulan,
                        'fungsi_sosial': fungsi_sosial,
                        'ada_komorbid': ada_komorbid,
                        'tingkat_komorbid': tingkat_komorbid,
                        'peran': peran,
                        'jenis_narkotika': jenis_narkotika,
                        'barang_bukti': barang_bukti,
                        'status_tangkap': status_tangkap,
                        'riwayat_pidana': riwayat_pidana
                    }
                }

            st.success("✅ Analisis selesai!")

        if 'results' in st.session_state:
            results = st.session_state['results']

            st.header("📊 HASIL ANALISIS TAT")
            st.caption(f"Waktu Analisis: {results['timestamp']}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(
                    "Skor Asesmen Medis",
                    f"{results['skor_medis']}/100",
                    delta="60% bobot" if results['skor_medis'] > 50 else None
                )
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(
                    "Skor Asesmen Hukum",
                    f"{results['skor_hukum']}/100",
                    delta="40% bobot" if results['skor_hukum'] > 50 else None
                )
                st.markdown('</div>', unsafe_allow_html=True)

            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric(
                    "Composite Score",
                    f"{results['final_score']:.1f}/100",
                    delta="Weighted"
                )
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")

            st.markdown("### 🎯 REKOMENDASI UTAMA")
            confidence = results['probabilities'][results['primary_rec']]

            if "Rehabilitasi" in results['primary_rec'] and "Hukum" not in results['primary_rec']:
                box_class = "success-box"
                icon = "✅"
            elif "Proses Hukum" == results['primary_rec']:
                box_class = "warning-box"
                icon = "⚠️"
            else:
                box_class = "info-box"
                icon = "ℹ️"

            st.markdown(f"""
            <div class="{box_class}">
                <h2 style="margin: 0;">{icon} {results['primary_rec']}</h2>
                <p style="font-size: 1.2rem; margin: 0.5rem 0;">
                    <strong>Tingkat Keyakinan: {confidence:.1f}%</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            st.markdown("### 📝 ALASAN & PERTIMBANGAN")
            for reason in results['reasoning']:
                if reason.startswith("✓"):
                    st.success(reason)
                elif reason.startswith("✗"):
                    st.error(reason)
                elif reason.startswith("!"):
                    st.warning(reason)
                elif reason.startswith("•") or reason.startswith("⚠"):
                    st.info(reason)
                else:
                    st.write(reason)

            st.markdown("---")

            st.markdown("### 📊 Distribusi Probabilitas Semua Rekomendasi")
            prob_df = pd.DataFrame({
                'Rekomendasi': list(results['probabilities'].keys()),
                'Probabilitas (%)': [f"{v:.1f}%" for v in results['probabilities'].values()],
                'Status': ['✅ PRIMARY' if k == results['primary_rec'] else '◻️ Alternative'
                           for k in results['probabilities'].keys()]
            })
            st.dataframe(prob_df, use_container_width=True, hide_index=True)

            fig_prob = create_probability_chart(results['probabilities'])
            st.plotly_chart(fig_prob, use_container_width=True)

            st.markdown("---")

            st.markdown("""
            <div class="info-box">
                <strong>📌 CATATAN PENTING:</strong><br>
                • Rekomendasi ini bersifat <strong>informatif dan membantu</strong> proses asesmen<br>
                • Keputusan final harus melalui <strong>Case Conference TAT</strong><br>
                • Pertimbangkan faktor kontekstual lain yang tidak tercakup dalam sistem<br>
                • Konsultasikan dengan tim dokter, psikolog, dan penegak hukum
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 💾 Export Hasil Analisis")

            export_data = {
                "timestamp": results['timestamp'],
                "input_data": results['input_data'],
                "skor_medis": results['skor_medis'],
                "skor_hukum": results['skor_hukum'],
                "final_score": results['final_score'],
                "rekomendasi_utama": results['primary_rec'],
                "confidence": results['probabilities'][results['primary_rec']],
                "breakdown_medis": results['breakdown_medis'],
                "breakdown_hukum": results['breakdown_hukum'],
                "probabilities": results['probabilities'],
                "reasoning": results['reasoning']
            }

            col_exp1, col_exp2 = st.columns(2)

            with col_exp1:
                txt_report = generate_txt_report(export_data)
                st.download_button(
                    label="📄 Download TXT Report",
                    data=txt_report,
                    file_name=f"TAT_Analysis_{results['timestamp'].replace(':', '-').replace(' ', '_')}.txt",
                    mime="text/plain"
                )

            with col_exp2:
                pdf_bytes = generate_pdf_report(export_data)
                st.download_button(
                    label="📘 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"TAT_Analysis_{results['timestamp'].replace(':', '-').replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("👈 Silakan isi data di tab **Input Data** dan klik tombol **Analisis & Prediksi**")

    # ======================================================================
    # TAB 3: VISUALISASI DETAIL
    # ======================================================================
    with tab3:
        if 'results' in st.session_state:
            results = st.session_state['results']

            st.header("📈 VISUALISASI DETAIL")

            col1, col2 = st.columns(2)

            with col1:
                fig_medis = create_gauge_chart(results['skor_medis'], "Skor Asesmen Medis")
                st.plotly_chart(fig_medis, use_container_width=True)

            with col2:
                fig_hukum = create_gauge_chart(results['skor_hukum'], "Skor Asesmen Hukum")
                st.plotly_chart(fig_hukum, use_container_width=True)

            st.markdown("---")

            fig_breakdown_medis = create_breakdown_chart(results['breakdown_medis'], "Breakdown Skor Asesmen Medis")
            st.plotly_chart(fig_breakdown_medis, use_container_width=True)

            st.markdown("---")

            fig_breakdown_hukum = create_breakdown_chart(results['breakdown_hukum'], "Breakdown Skor Asesmen Hukum")
            st.plotly_chart(fig_breakdown_hukum, use_container_width=True)

            st.markdown("---")

            st.markdown("### 📋 Detail Breakdown Skor")
            col_table1, col_table2 = st.columns(2)

            with col_table1:
                st.markdown("**Asesmen Medis:**")
                medis_detail = []
                for kategori, data in results['breakdown_medis'].items():
                    medis_detail.append({
                        'Kategori': kategori,
                        'Skor': f"{data['skor']}/{data['max']}",
                        'Detail': data['detail']
                    })
                st.dataframe(pd.DataFrame(medis_detail), use_container_width=True, hide_index=True)

            with col_table2:
                st.markdown("**Asesmen Hukum:**")
                hukum_detail = []
                for kategori, data in results['breakdown_hukum'].items():
                    hukum_detail.append({
                        'Kategori': kategori,
                        'Skor': f"{data['skor']}/{data['max']}",
                        'Detail': data['detail']
                    })
                st.dataframe(pd.DataFrame(hukum_detail), use_container_width=True, hide_index=True)
        else:
            st.info("👈 Silakan isi data di tab **Input Data** dan klik tombol **Analisis & Prediksi**")

    # ======================================================================
    # TAB 4: PANDUAN
    # ======================================================================
    with tab4:
        st.header("ℹ️ PANDUAN PENGGUNAAN SISTEM")

        st.markdown("""
        ### 📖 Tentang Sistem TAT Predictor

        Sistem ini dirancang sebagai **alat bantu** untuk Tim Asesmen Terpadu (TAT) dalam
        melakukan asesmen terhadap tersangka/terdakwa penyalahguna narkotika. Sistem menggunakan
        pendekatan **rule-based scoring** yang transparan dan dapat dipertanggungjawabkan.
        """)

        st.markdown("---")

        with st.expander("⚖️ DASAR HUKUM & REGULASI", expanded=True):
            st.markdown("""
            #### Landasan Hukum:

            1. **UU No. 35 Tahun 2009** tentang Narkotika
               - Pasal 54: Kewajiban rehab untuk pecandu
               - Pasal 103: Hakim dapat menetapkan rehabilitasi
               - Pasal 127: Penyalahguna dapat direhabilitasi

            2. **SEMA No. 4 Tahun 2010**
               - Kriteria penempatan ke lembaga rehabilitasi
               - Gramatur maksimal per jenis narkotika

            3. **Peraturan Bersama 7 Instansi (2014)**
               - Tata cara penanganan pecandu narkotika
               - Prosedur asesmen terpadu

            4. **Perka BNN No. 11 Tahun 2014**
               - Tata cara penanganan tersangka pecandu
               - Mekanisme TAT

            #### Instrumen Asesmen Internasional:

            - **ASAM** (American Society of Addiction Medicine) - 6 Dimensi
            - **DSM-5** - 11 Kriteria Gangguan Penggunaan Zat
            - **ASSIST** (Alcohol, Smoking and Substance Involvement Screening Test)
            - **DAST-10** (Drug Abuse Screening Test)
            - **ASI** (Addiction Severity Index)
            """)

        with st.expander("📏 KRITERIA SEMA 4/2010 (Gramatur Narkotika)", expanded=False):
            st.markdown("""
            #### Gramatur Maksimal untuk Rehabilitasi:

            Berdasarkan SEMA No. 4 Tahun 2010, berikut adalah batas maksimal barang bukti
            yang dapat dipertimbangkan untuk rehabilitasi:
            """)

            gramatur_df = pd.DataFrame({
                'Jenis Narkotika': list(GRAMATUR_LIMITS.keys()),
                'Batas Maksimal': [f"≤ {v}g" for v in GRAMATUR_LIMITS.values()],
                'Catatan': [
                    'Untuk ganja kering/daun',
                    'Kristal metamfetamin',
                    'Heroin/putaw dalam bentuk murni',
                    'Kokain murni',
                    'Tablet ekstasi @ 0,3g = 8 butir',
                    'Morfin dalam bentuk murni',
                    'Kodein dalam bentuk tablet',
                    'Disesuaikan dengan jenis'
                ]
            })

            st.dataframe(gramatur_df, use_container_width=True, hide_index=True)

            st.warning("""
            ⚠️ **PENTING:** Gramatur di atas adalah **pedoman umum**. Hakim tetap memiliki
            kewenangan untuk mempertimbangkan faktor-faktor lain dalam memutuskan rehabilitasi.
            """)

        with st.expander("🧠 KRITERIA DSM-5 (Gangguan Penggunaan Zat)", expanded=False):
            st.markdown("""
            #### 11 Kriteria Diagnostik DSM-5:

            Sistem DSM-5 menggunakan 11 kriteria untuk mendiagnosis gangguan penggunaan zat.
            Tingkat keparahan ditentukan berdasarkan jumlah kriteria yang terpenuhi:
            """)

            for i, criteria in enumerate(DSM5_CRITERIA, 1):
                st.markdown(f"{i}. {criteria}")

            st.markdown("""
            #### Interpretasi Tingkat Keparahan:

            - **0-1 kriteria**: Tidak ada gangguan
            - **2-3 kriteria**: Gangguan Penggunaan **RINGAN** (Mild)
            - **4-5 kriteria**: Gangguan Penggunaan **SEDANG** (Moderate)
            - **6+ kriteria**: Gangguan Penggunaan **BERAT** (Severe)
            """)

        with st.expander("🏥 ASAM 6 DIMENSI", expanded=False):
            st.markdown("""
            #### American Society of Addiction Medicine (ASAM) Criteria:

            ASAM menggunakan 6 dimensi untuk menilai tingkat keparahan dan menentukan
            level perawatan yang tepat:

            1. **Dimensi 1**: Intoxication Akut dan/atau Potensi Withdrawal
            2. **Dimensi 2**: Kondisi dan Komplikasi Biomedis
            3. **Dimensi 3**: Kondisi Emosional, Behavioral, Kognitif
            4. **Dimensi 4**: Kesiapan untuk Berubah
            5. **Dimensi 5**: Potensi Relapse
            6. **Dimensi 6**: Lingkungan Pemulihan/Hidup
            """)

        st.markdown("---")

        with st.expander("📝 CARA PENGGUNAAN SISTEM", expanded=True):
            st.markdown("""
            ### Langkah-langkah Penggunaan:

            1. Input data di tab **Input Data**
            2. Klik **Analisis & Prediksi**
            3. Review hasil di tab **Hasil Analisis**
            4. Eksplor detail di tab **Visualisasi Detail**
            5. Gunakan sebagai bahan **Case Conference TAT**
            """)

        with st.expander("⚠️ KETERBATASAN & DISCLAIMER", expanded=False):
            st.markdown("""
            - Output sistem bersifat rekomendatif (tidak mengikat).
            - Keputusan final ada pada Tim TAT dan otoritas berwenang.
            - Akurasi sangat tergantung kualitas input.
            """)

        st.markdown("""
        ---
        <div class="info-box">
        <strong>💡 TIPS:</strong><br>
        Gunakan sistem ini sebagai bagian dari proses asesmen komprehensif.
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# JALANKAN APLIKASI
# =============================================================================
if __name__ == "__main__":
    main()
