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
    # Composite Score dengan bobot
    final_score = (skor_medis * 0.6) + (skor_hukum * 0.4)
    
    # Inisialisasi probabilitas
    probabilities = {
        "Rehabilitasi Rawat Jalan": 0,
        "Rehabilitasi Rawat Inap": 0,
        "Proses Hukum": 0,
        "Proses Hukum + Rehabilitasi": 0
    }
    
    reasoning = []
    primary_recommendation = ""
    
    # ==========================================================================
    # RULE 1: REHABILITASI RAWAT JALAN
    # ==========================================================================
    if (20 <= skor_medis <= 50 and  # Kecanduan ringan-sedang
        skor_hukum <= 20 and         # Pengguna murni atau sharing minimal
        breakdown_medis['Fungsi Sosial']['skor'] <= 8):  # Masih produktif
        
        probabilities["Rehabilitasi Rawat Jalan"] = 85
        reasoning.append("✓ Tingkat kecanduan ringan-sedang (20-50 poin)")
        reasoning.append("✓ Tidak ada keterlibatan jaringan signifikan")
        reasoning.append("✓ Masih berfungsi sosial (produktif)")
        reasoning.append("✓ Sesuai kriteria rawat jalan")
        primary_recommendation = "Rehabilitasi Rawat Jalan"
    
    # ==========================================================================
    # RULE 2: REHABILITASI RAWAT INAP
    # ==========================================================================
    elif (skor_medis > 50 and       # Kecanduan berat
          skor_hukum <= 25 and      # Pengguna atau pengedar sangat kecil
          (breakdown_medis['Fungsi Sosial']['skor'] >= 8 or 
           breakdown_medis['Komorbid']['skor'] >= 8)):
        
        probabilities["Rehabilitasi Rawat Inap"] = 80
        reasoning.append("✓ Tingkat ketergantungan berat (>50 poin)")
        reasoning.append("✓ Butuh pengawasan intensif 24 jam")
        reasoning.append("✓ Gangguan fungsi sosial atau komorbid serius")
        reasoning.append("✓ Tidak ada bukti penjualan/peredaran besar")
        primary_recommendation = "Rehabilitasi Rawat Inap"
    
    # ==========================================================================
    # RULE 3: PROSES HUKUM
    # ==========================================================================
    elif (skor_hukum > 40 and       # Pengedar/bandar
          breakdown_hukum['Barang Bukti']['skor'] >= 18 and
          skor_medis < 40):         # Kecanduan tidak dominan
        
        probabilities["Proses Hukum"] = 75
        reasoning.append("✗ Indikasi kuat keterlibatan peredaran")
        reasoning.append("✗ Barang bukti signifikan")
        reasoning.append("✗ Tingkat kecanduan tidak dominan")
        reasoning.append("✗ Memenuhi kriteria tindak pidana peredaran")
        primary_recommendation = "Proses Hukum"
    
    # ==========================================================================
    # RULE 4: PROSES HUKUM + REHABILITASI (DUAL INTERVENTION)
    # ==========================================================================
    elif (skor_medis > 50 and       # Pecandu berat
          skor_hukum > 30):         # Terlibat peredaran
        
        probabilities["Proses Hukum + Rehabilitasi"] = 85
        reasoning.append("! Pecandu berat dengan ketergantungan severe")
        reasoning.append("! Sekaligus terlibat dalam peredaran narkotika")
        reasoning.append("! Memerlukan dual intervention:")
        reasoning.append("  → Rehabilitasi untuk mengatasi kecanduan")
        reasoning.append("  → Proses hukum untuk aspek peredaran")
        primary_recommendation = "Proses Hukum + Rehabilitasi"
    
    # ==========================================================================
    # EDGE CASES & REFINEMENT
    # ==========================================================================
    else:
        # Default berdasarkan dominasi skor
        if skor_medis > skor_hukum * 1.5:  # Medis sangat dominan
            if skor_medis > 60:
                probabilities["Rehabilitasi Rawat Inap"] = 70
                primary_recommendation = "Rehabilitasi Rawat Inap"
                reasoning.append("✓ Aspek medis sangat dominan (severe addiction)")
            else:
                probabilities["Rehabilitasi Rawat Jalan"] = 65
                primary_recommendation = "Rehabilitasi Rawat Jalan"
                reasoning.append("✓ Aspek medis dominan (moderate addiction)")
        
        elif skor_hukum > skor_medis * 1.5:  # Hukum sangat dominan
            probabilities["Proses Hukum"] = 70
            primary_recommendation = "Proses Hukum"
            reasoning.append("✗ Aspek hukum sangat dominan")
        
        else:  # Balanced - perlu evaluasi lebih lanjut
            probabilities["Proses Hukum + Rehabilitasi"] = 60
            primary_recommendation = "Proses Hukum + Rehabilitasi"
            reasoning.append("! Skor medis dan hukum relatif seimbang")
            reasoning.append("! Perlu evaluasi mendalam Tim Asesmen Terpadu")
    
    # Tambahkan reasoning tambahan berdasarkan SEMA 4/2010
    if breakdown_hukum['Barang Bukti']['skor'] == 0:
        reasoning.append("• Barang bukti di bawah gramatur SEMA 4/2010")
    
    if breakdown_hukum['Riwayat Pidana']['skor'] >= 10:
        reasoning.append("⚠ Catatan: Ada riwayat kasus sebelumnya")
    
    # Normalisasi probabilitas jika ada multiple recommendations
    total_prob = sum(probabilities.values())
    if total_prob > 100:
        probabilities = {k: (v/total_prob)*100 for k, v in probabilities.items()}
    
    # Tambahkan probabilitas kecil untuk opsi lain (realistis)
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
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20}},
        delta = {'reference': max_score/2},
        gauge = {
            'axis': {'range': [None, max_score], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_score/3], 'color': "lightgreen"},
                {'range': [max_score/3, 2*max_score/3], 'color': "yellow"},
                {'range': [2*max_score/3, max_score], 'color': "salmon"}
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
    
    # Bar untuk skor aktual
    fig.add_trace(go.Bar(
        y=categories,
        x=scores,
        name='Skor Aktual',
        orientation='h',
        marker=dict(color='#1f77b4'),
        text=scores,
        textposition='auto',
    ))
    
    # Bar untuk sisa dari max score
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
    
    colors = ['#28a745' if v == max(values) else '#17a2b8' for v in values]
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
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
    # Header
    st.markdown('<h1 class="main-header">⚖️ SISTEM PREDIKSI TAT BNN</h1>', 
                unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Tools Bantu Tim Asesmen Terpadu - Penanganan Penyalahguna Narkotika</p>', 
                unsafe_allow_html=True)
    
    # Warning Box
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ PERHATIAN PENTING:</strong><br>
        Sistem ini adalah <strong>ALAT BANTU</strong> untuk proses asesmen. 
        Keputusan final tetap berada di tangan <strong>Tim Asesmen Terpadu BNN</strong> 
        dan aparat penegak hukum yang berwenang.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Info Regulasi
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
    
    # Tab Layout
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Input Data", 
        "📊 Hasil Analisis", 
        "📈 Visualisasi Detail",
        "ℹ️ Panduan"
    ])
    
    # ==========================================================================
    # TAB 1: INPUT DATA
    # ==========================================================================
    with tab1:
        st.header("📋 Input Data Asesmen")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏥 ASESMEN MEDIS")
            
            # Informasi Identitas (Opsional - untuk dokumentasi)
            with st.expander("👤 Informasi Identitas (Opsional)", expanded=False):
                nama_inisial = st.text_input("Inisial Nama", placeholder="Contoh: AB")
                usia = st.number_input("Usia", min_value=0, max_value=100, value=25)
                jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            
            st.markdown("---")
            
            # 1. Hasil Tes Urine
            st.markdown("**1️⃣ Hasil Tes Urine/Laboratorium**")
            zat_positif = st.multiselect(
                "Zat yang terdeteksi POSITIF:",
                JENIS_NARKOTIKA,
                help="Pilih semua zat yang terdeteksi positif dalam tes urine/lab"
            )
            
            st.markdown("---")
            
            # 2. Tingkat Kecanduan (DSM-5)
            st.markdown("**2️⃣ Kriteria DSM-5 (Gangguan Penggunaan Zat)**")
            st.caption("Berikan tanda centang pada kriteria yang terpenuhi:")
            
            dsm5_checked = []
            for i, criteria in enumerate(DSM5_CRITERIA, 1):
                if st.checkbox(f"{i}. {criteria}", key=f"dsm5_{i}"):
                    dsm5_checked.append(criteria)
            
            dsm5_count = len(dsm5_checked)
            
            # Tampilkan interpretasi
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
            
            # 3. Durasi Penggunaan
            st.markdown("**3️⃣ Durasi Penggunaan Narkotika**")
            durasi_bulan = st.number_input(
                "Berapa lama sudah menggunakan? (dalam bulan)",
                min_value=0,
                max_value=240,
                value=6,
                help="Estimasi durasi penggunaan narkotika"
            )
            
            st.markdown("---")
            
            # 4. Fungsi Sosial
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
            
            # 5. Komorbid
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
            
            # 1. Peran dalam Kasus
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
            
            # 2. Barang Bukti
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
            
            # Tampilkan status gramatur
            if barang_bukti < gramatur_limit:
                st.success(f"✓ Di bawah gramatur SEMA (< {gramatur_limit}g)")
            elif barang_bukti <= gramatur_limit * 2:
                st.warning(f"⚠ Mendekati/sedikit di atas gramatur SEMA")
            else:
                st.error(f"✗ Jauh melebihi gramatur SEMA (> {gramatur_limit}g)")
            
            st.markdown("---")
            
            # 3. Status Penangkapan
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
            
            # 4. Riwayat Pidana
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
        
        # Tombol Analisis
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn2:
            analyze_button = st.button(
                "🔍 ANALISIS & PREDIKSI",
                use_container_width=True,
                type="primary"
            )
    
    # ==========================================================================
    # TAB 2: HASIL ANALISIS
    # ==========================================================================
    with tab2:
        if 'analyze_button' in locals() and analyze_button:
            with st.spinner('🔄 Melakukan analisis...'):
                # Hitung skor
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
                
                # Simpan ke session state untuk digunakan di tab lain
                st.session_state['results'] = {
                    'skor_medis': skor_medis,
                    'skor_hukum': skor_hukum,
                    'breakdown_medis': breakdown_medis,
                    'breakdown_hukum': breakdown_hukum,
                    'probabilities': probabilities,
                    'reasoning': reasoning,
                    'primary_rec': primary_rec,
                    'final_score': final_score,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            st.success("✅ Analisis selesai!")
            
        # Tampilkan hasil jika sudah ada di session state
        if 'results' in st.session_state:
            results = st.session_state['results']
            
            st.header("📊 HASIL ANALISIS TAT")
            st.caption(f"Waktu Analisis: {results['timestamp']}")
            
            # Tampilkan Skor Utama
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
            
            # Rekomendasi Utama
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
            
            # Reasoning
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
            
            # Distribusi Probabilitas
            st.markdown("### 📊 Distribusi Probabilitas Semua Rekomendasi")
            
            # Tampilkan sebagai tabel
            prob_df = pd.DataFrame({
                'Rekomendasi': list(results['probabilities'].keys()),
                'Probabilitas (%)': [f"{v:.1f}%" for v in results['probabilities'].values()],
                'Status': ['✅ PRIMARY' if k == results['primary_rec'] else '◻️ Alternative' 
                          for k in results['probabilities'].keys()]
            })
            st.dataframe(prob_df, use_container_width=True, hide_index=True)
            
            # Visualisasi
            fig_prob = create_probability_chart(results['probabilities'])
            st.plotly_chart(fig_prob, use_container_width=True)
            
            st.markdown("---")
            
            # Catatan Penting
            st.markdown("""
            <div class="info-box">
                <strong>📌 CATATAN PENTING:</strong><br>
                • Rekomendasi ini bersifat <strong>informatif dan membantu</strong> proses asesmen<br>
                • Keputusan final harus melalui <strong>Case Conference TAT</strong><br>
                • Pertimbangkan faktor kontekstual lain yang tidak tercakup dalam sistem<br>
                • Konsultasikan dengan tim dokter, psikolog, dan penegak hukum
            </div>
            """, unsafe_allow_html=True)
            
            # Export Data
            st.markdown("---")
            st.markdown("### 💾 Export Hasil Analisis")
            
            export_data = {
                "timestamp": results['timestamp'],
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
            
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"TAT_Analysis_{results['timestamp'].replace(':', '-')}.json",
                    mime="application/json"
                )
        
        else:
            st.info("👈 Silakan isi data di tab **Input Data** dan klik tombol **Analisis & Prediksi**")
    
    # ==========================================================================
    # TAB 3: VISUALISASI DETAIL
    # ==========================================================================
    with tab3:
        if 'results' in st.session_state:
            results = st.session_state['results']
            
            st.header("📈 VISUALISASI DETAIL")
            
            # Gauge Charts untuk Skor
            col1, col2 = st.columns(2)
            
            with col1:
                fig_medis = create_gauge_chart(
                    results['skor_medis'],
                    "Skor Asesmen Medis"
                )
                st.plotly_chart(fig_medis, use_container_width=True)
            
            with col2:
                fig_hukum = create_gauge_chart(
                    results['skor_hukum'],
                    "Skor Asesmen Hukum"
                )
                st.plotly_chart(fig_hukum, use_container_width=True)
            
            st.markdown("---")
            
            # Breakdown Charts
            fig_breakdown_medis = create_breakdown_chart(
                results['breakdown_medis'],
                "Breakdown Skor Asesmen Medis"
            )
            st.plotly_chart(fig_breakdown_medis, use_container_width=True)
            
            st.markdown("---")
            
            fig_breakdown_hukum = create_breakdown_chart(
                results['breakdown_hukum'],
                "Breakdown Skor Asesmen Hukum"
            )
            st.plotly_chart(fig_breakdown_hukum, use_container_width=True)
            
            st.markdown("---")
            
            # Tabel Detail Breakdown
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
            st.info("👈 Silakan lakukan analisis terlebih dahulu di tab **Hasil Analisis**")

    # ==========================================================================
    # TAB 4: PANDUAN
    # ==========================================================================
    with tab4:
        st.header("ℹ️ PANDUAN PENGGUNAAN SISTEM TAT PREDICTOR")

        with st.expander("🎯 **Tujuan Sistem**", expanded=True):
            st.markdown("""
            Sistem ini dirancang sebagai **alat bantu** untuk Tim Asesmen Terpadu (TAT) BNN dalam:
            - Melakukan asesmen awal terhadap kasus penyalahgunaan narkotika
            - Memprediksi rekomendasi berdasarkan kriteria hukum dan medis
            - Membantu pengambilan keputusan rehabilitasi atau proses hukum
            - Menyediakan dokumentasi digital untuk case conference TAT
            """)

        with st.expander("📋 **Prosedur Input Data**"):
            st.markdown("""
            **Langkah-langkah Input Data:**
            1. **Asesmen Medis** - Isi informasi dari hasil pemeriksaan medis dan psikologis
               - Hasil tes urine/laboratorium
               - Kriteria DSM-5 (11 kriteria kecanduan)
               - Durasi penggunaan
               - Fungsi sosial
               - Kondisi komorbid
            2. **Asesmen Hukum** - Isi informasi dari hasil penyelidikan
               - Peran dalam kasus (pengguna/pengedar)
               - Barang bukti dan jenis narkotika
               - Status penangkapan
               - Riwayat pidana
            3. Klik tombol **Analisis & Prediksi** untuk mendapatkan hasil
            """)

        with st.expander("⚖️ **Dasar Hukum & Kriteria**"):
            st.markdown("""
            **Regulasi yang Digunakan:**
            - **UU No. 35 Tahun 2009** tentang Narkotika
            - **SEMA No. 4 Tahun 2010** tentang Rehabilitasi
            - **Peraturan Bersama 7 Instansi** No. 01/PB/MA/III/2014
            - **Perka BNN No. 11 Tahun 2014** tentang Asesmen
            - **DSM-5** untuk diagnosis gangguan penggunaan zat

            **Kriteria SEMA 4/2010 untuk Rehabilitasi:**
            - Tertangkap tangan
            - Barang bukti pemakaian 1 hari
            - Uji laboratorium positif
            - Tidak terlibat peredaran gelap
            - Bukan residivis
            """)

        with st.expander("📊 **Interpretasi Skor**"):
            st.markdown("""
            **Skor Asesmen Medis (0-100):**
            - **0-20**: Kecanduan sangat ringan
            - **21-50**: Kecanduan ringan-sedang
            - **51-70**: Kecanduan sedang-berat
            - **71-100**: Kecanduan sangat berat

            **Skor Asesmen Hukum (0-100):**
            - **0-20**: Risiko hukum rendah (pengguna murni)
            - **21-40**: Risiko hukum sedang (pengedar kecil)
            - **41-60**: Risiko hukum tinggi (pengedar besar)
            - **61-100**: Risiko hukum sangat tinggi (bandar)

            **Composite Score** = (Skor Medis × 0.6) + (Skor Hukum × 0.4)
            """)

        with st.expander("🔍 **Jenis Rekomendasi**"):
            st.markdown("""
            **Rehabilitasi Rawat Jalan:**
            - Untuk kasus kecanduan ringan dengan risiko hukum rendah
            - Masih berfungsi sosial dan produktif
            - Tidak terlibat peredaran

            **Rehabilitasi Rawat Inap:**
            - Untuk kasus kecanduan berat
            - Gangguan fungsi sosial serius
            - Membutuhkan pengawasan intensif

            **Proses Hukum:**
            - Untuk kasus terlibat peredaran
            - Barang bukti melebihi gramatur SEMA
            - Kecanduan bukan faktor dominan

            **Proses Hukum + Rehabilitasi:**
            - Dual intervention untuk pecandu berat sekaligus pengedar
            - Memerlukan penanganan medis dan hukum
            """)

        with st.expander("⚠️ **Batasan Sistem**"):
            st.markdown("""
            **Penting Dipahami:**
            - Sistem ini **bukan pengganti** keputusan profesional TAT
            - Hasil hanya **alat bantu** untuk proses asesmen
            - Harus dikombinasikan dengan **evaluasi klinis mendalam**
            - Faktor kontekstual spesifik kasus harus dipertimbangkan
            - Keputusan final tetap di tangan **BNN dan aparat hukum berwenang**
            """)

        with st.expander("💾 **Export & Dokumentasi**"):
            st.markdown("""
            **Fitur Export:**
            - Hasil analisis dapat di-download dalam format JSON
            - Data mencakup skor, breakdown, dan reasoning
            - Cocok untuk dokumentasi case conference TAT
            - Dapat digunakan untuk audit dan evaluasi program
            """)

        st.markdown("---")
        st.markdown("""
        <div class="info-box">
            <strong>💡 TIPS PENGGUNAAN:</strong><br>
            Gunakan sistem ini sebagai <strong>starting point</strong> untuk diskusi TAT.<br>
            Gabungkan dengan <strong>penilaian klinis dan hukum profesional</strong>.<br>
            Catat semua asumsi dan batasan dalam proses dokumentasi kasus.
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
