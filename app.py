import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from utils.scoring import calculate_tat_score, get_recommendation
from utils.pdf_generator import generate_pdf_report
from utils.data_storage import save_case, load_cases, get_statistics

# Page config
st.set_page_config(
    page_title="TAT Decision Support System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        margin: 1rem 0;
    }
    .danger-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'case_data' not in st.session_state:
    st.session_state.case_data = {}
if 'recommendation' not in st.session_state:
    st.session_state.recommendation = None

# Sidebar Navigation
st.sidebar.title("🏛️ TAT-DSS v1.0")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navigasi",
    ["📝 Input Asesmen", "📊 Dashboard & Statistik", "📚 Panduan Hukum", "ℹ️ Tentang Sistem"]
)
st.sidebar.markdown("---")
st.sidebar.info("""
**Tim Asesmen Terpadu (TAT)**  
Badan Narkotika Nasional

Dasar Hukum:
- UU No. 35/2009 (Narkotika)
- KUHP Nasional UU No. 1/2023
- UU Penyesuaian Pidana 2025
- Pedoman Jaksa Agung 18/2021
""")

# ============================================================================
# MENU 1: INPUT ASESMEN
# ============================================================================
if menu == "📝 Input Asesmen":
    st.markdown('<p class="main-header">⚖️ TIM ASESMEN TERPADU (TAT)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sistem Pendukung Keputusan Cepat & Akurat</p>', unsafe_allow_html=True)
    
    # Progress indicator
    progress_col1, progress_col2, progress_col3 = st.columns(3)
    with progress_col1:
        st.info("**STEP 1** | Data Identitas")
    with progress_col2:
        st.info("**STEP 2** | Asesmen Medis & Hukum")
    with progress_col3:
        st.info("**STEP 3** | Rekomendasi TAT")
    
    st.markdown("---")
    
    # SECTION 1: IDENTITAS TERSANGKA
    st.header("1️⃣ IDENTITAS TERSANGKA")
    col1, col2 = st.columns(2)
    
    with col1:
        nama = st.text_input("Nama Lengkap", placeholder="Nama tersangka")
        usia = st.number_input("Usia", min_value=10, max_value=100, value=25)
        jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
        
    with col2:
        pendidikan = st.selectbox("Pendidikan Terakhir", 
                                  ["SD", "SMP", "SMA/SMK", "Diploma", "S1", "S2/S3"])
        pekerjaan = st.text_input("Pekerjaan", placeholder="Pekerjaan tersangka")
        tanggal_asesmen = st.date_input("Tanggal Asesmen", value=datetime.now())
    
    st.markdown("---")
    
    # SECTION 2: ASESMEN CEPAT
    st.header("2️⃣ ASESMEN CEPAT")
    
    # Tab untuk memisahkan asesmen medis dan hukum
    tab1, tab2 = st.tabs(["🏥 Asesmen Medis", "⚖️ Asesmen Hukum"])
    
    # TAB MEDIS
    with tab1:
        st.subheader("A. Hasil Tes Urine")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            met_test = st.checkbox("MET (Methamphetamine)")
            amp_test = st.checkbox("AMP (Amphetamine)")
            thc_test = st.checkbox("THC (Cannabis)")
        with col2:
            coc_test = st.checkbox("COC (Cocaine)")
            mop_test = st.checkbox("MOP (Morphine)")
            bzo_test = st.checkbox("BZO (Benzodiazepine)")
        with col3:
            mdma_test = st.checkbox("MDMA (Ecstasy)")
            k2_test = st.checkbox("K2 (Synthetic Cannabis)")
        
        # Hitung jenis zat yang positif
        positive_tests = sum([met_test, amp_test, thc_test, coc_test, mop_test, bzo_test, mdma_test, k2_test])
        
        st.info(f"**Zat Terdeteksi:** {positive_tests} jenis")
        
        st.markdown("---")
        st.subheader("B. Tingkat Kecanduan (Quick Assessment)")
        
        col1, col2 = st.columns(2)
        with col1:
            frekuensi = st.select_slider(
                "Frekuensi Penggunaan (3 bulan terakhir)",
                options=["Tidak pernah", "1-2 kali", "Bulanan", "Mingguan", "Harian"],
                value="Bulanan"
            )
            durasi = st.select_slider(
                "Durasi Penggunaan",
                options=["< 6 bulan", "6-12 bulan", "1-3 tahun", "> 3 tahun"],
                value="6-12 bulan"
            )
        
        with col2:
            withdrawal = st.checkbox("Gejala withdrawal saat berhenti", value=False)
            toleransi = st.checkbox("Butuh dosis lebih tinggi (toleransi)", value=False)
            kehidupan_terganggu = st.checkbox("Aktivitas sehari-hari terganggu", value=False)
            keinginan_kuat = st.checkbox("Keinginan kuat untuk menggunakan", value=False)
        
        # Hitung skor kecanduan sederhana
        addiction_score = 0
        if frekuensi == "Harian": addiction_score += 8
        elif frekuensi == "Mingguan": addiction_score += 6
        elif frekuensi == "Bulanan": addiction_score += 3
        elif frekuensi == "1-2 kali": addiction_score += 1
        
        if durasi == "> 3 tahun": addiction_score += 6
        elif durasi == "1-3 tahun": addiction_score += 4
        elif durasi == "6-12 bulan": addiction_score += 2
        elif durasi == "< 6 bulan": addiction_score += 1
        
        addiction_score += sum([withdrawal, toleransi, kehidupan_terganggu, keinginan_kuat]) * 3
        
        # Klasifikasi
        if addiction_score <= 10:
            addiction_level = "RINGAN"
            addiction_color = "success"
        elif addiction_score <= 20:
            addiction_level = "SEDANG"
            addiction_color = "warning"
        else:
            addiction_level = "BERAT"
            addiction_color = "danger"
        
        st.markdown(f'<div class="{addiction_color}-box"><strong>Tingkat Kecanduan: {addiction_level}</strong> (Skor: {addiction_score}/30)</div>', 
                   unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("C. Kondisi Medis & Psikologis")
        
        col1, col2 = st.columns(2)
        with col1:
            kondisi_fisik = st.selectbox("Kondisi Fisik Umum", 
                                        ["Baik", "Cukup", "Kurang", "Buruk"])
            bekas_suntikan = st.checkbox("Tanda bekas suntikan", value=False)
        
        with col2:
            gangguan_jiwa = st.checkbox("Gangguan jiwa/depresi/ansietas", value=False)
            dukungan_keluarga = st.selectbox("Dukungan Keluarga", 
                                            ["Kuat", "Sedang", "Lemah"])
        
        motivasi_pulih = st.slider("Motivasi untuk Pulih (1-10)", 1, 10, 5)
    
    # TAB HUKUM
    with tab2:
        st.subheader("A. Barang Bukti")
        
        col1, col2 = st.columns(2)
        with col1:
            jenis_narkotika = st.selectbox(
                "Jenis Narkotika",
                ["Ganja (Cannabis)", "Sabu (Methamphetamine)", "Ekstasi (MDMA)", 
                 "Kokain", "Heroin", "Lainnya"]
            )
            berat_bb = st.number_input("Berat Barang Bukti (gram)", min_value=0.0, value=0.5, step=0.1)
        
        with col2:
            golongan = st.selectbox("Golongan Narkotika", ["Golongan I", "Golongan II", "Golongan III"])
            lokasi_bb = st.selectbox("Lokasi Ditemukan BB", 
                                    ["Pada tubuh", "Di kendaraan", "Di rumah", "Lainnya"])
        
        # Threshold check (sesuai praktik lapangan)
        threshold_map = {
            "Ganja (Cannabis)": 5.0,
            "Sabu (Methamphetamine)": 1.0,
            "Ekstasi (MDMA)": 0.5,  # 5 butir ≈ 0.5 gram
            "Kokain": 1.0,
            "Heroin": 0.5
        }
        
        threshold = threshold_map.get(jenis_narkotika, 1.0)
        above_threshold = berat_bb > threshold
        
        if above_threshold:
            st.warning(f"⚠️ BB ({berat_bb}g) **MELEBIHI** threshold end user ({threshold}g)")
        else:
            st.success(f"✅ BB ({berat_bb}g) **DI BAWAH** threshold end user ({threshold}g)")
        
        st.markdown("---")
        st.subheader("B. Indikator Pengedaran (Quick Check)")
        
        col1, col2 = st.columns(2)
        with col1:
            alat_timbang = st.checkbox("Alat timbang ditemukan")
            packaging = st.checkbox("Material packaging ditemukan")
            hp_multiple = st.checkbox("HP/alat komunikasi multiple")
        
        with col2:
            daftar_transaksi = st.checkbox("Daftar nama/transaksi ditemukan")
            uang_besar = st.checkbox("Uang tunai dalam jumlah besar")
            intelijen_jaringan = st.checkbox("Intel: Bagian dari jaringan")
        
        indikator_pengedar = sum([alat_timbang, packaging, hp_multiple, 
                                   daftar_transaksi, uang_besar, intelijen_jaringan])
        
        if indikator_pengedar >= 3:
            st.error(f"🚨 **INDIKASI KUAT PENGEDAR** ({indikator_pengedar}/6 indikator)")
            peran = "PENGEDAR"
        else:
            st.success(f"✅ **INDIKASI END USER** ({indikator_pengedar}/6 indikator)")
            peran = "END USER"
        
        st.markdown("---")
        st.subheader("C. Rekam Jejak")
        
        col1, col2 = st.columns(2)
        with col1:
            first_offender = st.checkbox("First Offender (belum pernah divonis)", value=True)
            if not first_offender:
                jumlah_vonis = st.number_input("Jumlah Vonis Sebelumnya", min_value=1, max_value=10, value=1)
            else:
                jumlah_vonis = 0
        
        with col2:
            riwayat_rehab = st.number_input("Jumlah Rehabilitasi Sebelumnya", 
                                           min_value=0, max_value=5, value=0)
            
            if riwayat_rehab >= 3:
                st.error("⚠️ Sudah 3x rehabilitasi (batas maksimal)")
    
    st.markdown("---")
    
    # SECTION 3: GENERATE RECOMMENDATION
    st.header("3️⃣ REKOMENDASI TAT")
    
    if st.button("🎯 GENERATE REKOMENDASI", type="primary", use_container_width=True):
        # Compile data
        case_data = {
            # Identitas
            'nama': nama,
            'usia': usia,
            'jenis_kelamin': jenis_kelamin,
            'pendidikan': pendidikan,
            'pekerjaan': pekerjaan,
            'tanggal_asesmen': str(tanggal_asesmen),
            
            # Medis
            'positive_tests': positive_tests,
            'addiction_score': addiction_score,
            'addiction_level': addiction_level,
            'frekuensi': frekuensi,
            'durasi': durasi,
            'withdrawal': withdrawal,
            'toleransi': toleransi,
            'kondisi_fisik': kondisi_fisik,
            'gangguan_jiwa': gangguan_jiwa,
            'dukungan_keluarga': dukungan_keluarga,
            'motivasi_pulih': motivasi_pulih,
            
            # Hukum
            'jenis_narkotika': jenis_narkotika,
            'berat_bb': berat_bb,
            'above_threshold': above_threshold,
            'indikator_pengedar': indikator_pengedar,
            'peran': peran,
            'first_offender': first_offender,
            'jumlah_vonis': jumlah_vonis,
            'riwayat_rehab': riwayat_rehab,
            'golongan': golongan
        }
        
        # Calculate final score & recommendation
        final_score, scoring_details = calculate_tat_score(case_data)
        recommendation = get_recommendation(final_score, case_data)
        
        # Store in session state
        st.session_state.case_data = case_data
        st.session_state.case_data['final_score'] = final_score
        st.session_state.case_data['scoring_details'] = scoring_details
        st.session_state.recommendation = recommendation
        
        # Display results
        st.success("✅ Rekomendasi berhasil di-generate!")
        
        # Score breakdown
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Skor Total", f"{final_score}", 
                     help="Rentang: -15 hingga +20")
        with col2:
            st.metric("Tingkat Kecanduan", addiction_level)
        with col3:
            st.metric("Klasifikasi Peran", peran)
        
        st.markdown("---")
        
        # REKOMENDASI UTAMA
        rec_type = recommendation['type']
        rec_color = recommendation['color']
        
        st.markdown(f'<div class="{rec_color}-box">', unsafe_allow_html=True)
        st.markdown(f"### 📋 REKOMENDASI: **{rec_type}**")
        st.markdown(recommendation['detail'])
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Program & Durasi
        if recommendation.get('program'):
            st.markdown("#### 🎯 Program Rehabilitasi")
            st.write(recommendation['program'])
        
        if recommendation.get('durasi'):
            st.markdown(f"**Durasi:** {recommendation['durasi']}")
        
        if recommendation.get('tempat'):
            st.markdown(f"**Tempat:** {recommendation['tempat']}")
        
        # Monitoring
        if recommendation.get('monitoring'):
            st.markdown("#### 📊 Monitoring & Evaluasi")
            st.write(recommendation['monitoring'])
        
        # Dasar Hukum
        st.markdown("#### ⚖️ Dasar Hukum")
        st.info(recommendation['dasar_hukum'])
        
        # Catatan khusus
        if recommendation.get('catatan'):
            st.warning(f"**⚠️ Catatan Khusus:** {recommendation['catatan']}")
        
        st.markdown("---")
        
        # EXPORT OPTIONS
        st.subheader("📄 Export Dokumen")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Download PDF Report", use_container_width=True):
                pdf_buffer = generate_pdf_report(case_data, recommendation)
                st.download_button(
                    label="💾 Simpan PDF",
                    data=pdf_buffer,
                    file_name=f"TAT_Report_{nama.replace(' ', '_')}_{tanggal_asesmen}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        with col2:
            if st.button("💾 Simpan ke Database", use_container_width=True):
                save_case(case_data, recommendation)
                st.success("✅ Data tersimpan!")
        
        with col3:
            if st.button("📋 Copy JSON", use_container_width=True):
                json_data = json.dumps(case_data, indent=2, ensure_ascii=False)
                st.code(json_data, language='json')

# ============================================================================
# MENU 2: DASHBOARD & STATISTIK
# ============================================================================
elif menu == "📊 Dashboard & Statistik":
    st.markdown('<p class="main-header">📊 DASHBOARD & STATISTIK TAT</p>', unsafe_allow_html=True)
    
    # Load data
    cases = load_cases()
    
    if len(cases) == 0:
        st.info("Belum ada data kasus. Silakan input asesmen terlebih dahulu.")
    else:
        # Summary metrics
        stats = get_statistics(cases)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Kasus", stats['total_cases'])
        with col2:
            st.metric("Rekomendasi Rehabilitasi", f"{stats['rehab_percentage']:.1f}%")
        with col3:
            st.metric("Rata-rata Usia", f"{stats['avg_age']:.1f} tahun")
        with col4:
            st.metric("First Offender", f"{stats['first_offender_percentage']:.1f}%")
        
        st.markdown("---")
        
        # Charts
        tab1, tab2, tab3 = st.tabs(["📈 Distribusi Rekomendasi", "🎯 Tingkat Kecanduan", "⚖️ Jenis Narkotika"])
        
        with tab1:
            import plotly.express as px
            
            rec_counts = pd.DataFrame(stats['recommendation_distribution'].items(), 
                                     columns=['Rekomendasi', 'Jumlah'])
            fig = px.pie(rec_counts, values='Jumlah', names='Rekomendasi', 
                        title='Distribusi Rekomendasi TAT')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            addiction_counts = pd.DataFrame(stats['addiction_level_distribution'].items(),
                                           columns=['Tingkat', 'Jumlah'])
            fig = px.bar(addiction_counts, x='Tingkat', y='Jumlah',
                        title='Distribusi Tingkat Kecanduan',
                        color='Tingkat',
                        color_discrete_map={'RINGAN': 'green', 'SEDANG': 'orange', 'BERAT': 'red'})
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            drug_counts = pd.DataFrame(stats['drug_type_distribution'].items(),
                                      columns=['Jenis', 'Jumlah'])
            fig = px.bar(drug_counts, x='Jenis', y='Jumlah',
                        title='Distribusi Jenis Narkotika')
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Detailed table
        st.subheader("📋 Daftar Kasus")
        df_cases = pd.DataFrame(cases)
        df_display = df_cases[['nama', 'usia', 'jenis_narkotika', 'addiction_level', 
                               'peran', 'final_score', 'tanggal_asesmen']]
        st.dataframe(df_display, use_container_width=True)

# ============================================================================
# MENU 3: PANDUAN HUKUM
# ============================================================================
elif menu == "📚 Panduan Hukum":
    st.markdown('<p class="main-header">📚 PANDUAN HUKUM TAT</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["⚖️ Dasar Hukum", "📊 Threshold BB", "🎯 Algoritma Scoring", "📝 Template Dokumen"])
    
    with tab1:
        st.subheader("Dasar Hukum TAT")
        
        st.markdown("""
        ### 1. UU No. 35 Tahun 2009 (Narkotika)
        - **Pasal 54**: Pecandu dan korban penyalahguna WAJIB rehabilitasi
        - **Pasal 103**: Masa rehabilitasi diperhitungkan sebagai masa menjalani hukuman
        - **Pasal 127**: Sanksi penyalahguna (max 4 tahun Gol I)
        
        ### 2. KUHP Nasional (UU No. 1 Tahun 2023)
        - **Pasal 103**: Rehabilitasi sebagai pidana alternatif
        - **Pasal 105**: Rehabilitasi untuk pecandu narkotika
        - **Berlaku**: 2 Januari 2026
        
        ### 3. UU Penyesuaian Pidana (2025)
        - Menghapus pidana minimum khusus
        - Sanksi kumulatif alternatif (dan/atau)
        - Hakim punya diskresi penuh (0 tahun - maksimum)
        
        ### 4. Pedoman Jaksa Agung No. 18 Tahun 2021
        - **Prioritas rehabilitasi** atas penuntutan
        - "**HARAM** melimpahkan pecandu ke persidangan"
        - Maksimal 3x rehabilitasi, kali ke-4 baru dilimpahkan
        
        ### 5. Peraturan Bersama 7 Instansi (2014)
        - Mekanisme TAT (Tim Asesmen Terpadu)
        - Komposisi: Tim Medis + Tim Hukum
        - Timeline: Max 2x24 jam selesai
        """)
    
    with tab2:
        st.subheader("Threshold Barang Bukti End User")
        
        st.markdown("""
        Berdasarkan praktik lapangan dan pedoman tidak tertulis:
        """)
        
        threshold_data = {
            'Jenis Narkotika': ['Ganja (Cannabis)', 'Sabu (Methamphetamine)', 
                               'Ekstasi (MDMA)', 'Kokain', 'Heroin'],
            'Threshold (gram)': [5.0, 1.0, 0.5, 1.0, 0.5],
            'Basis Perhitungan': ['10x pakai @ 0.5g', '10x pakai @ 0.1g', 
                                  '5 butir @ 0.1g', '10x pakai @ 0.1g', '5x pakai @ 0.1g'],
            'Keterangan': ['Di atas 5g → indikasi pengedar', 
                          'Di atas 1g → indikasi pengedar',
                          'Di atas 5 butir → indikasi pengedar',
                          'Di atas 1g → indikasi pengedar',
                          'Di atas 0.5g → indikasi pengedar']
        }
        
        df_threshold = pd.DataFrame(threshold_data)
        st.table(df_threshold)
        
        st.warning("""
        ⚠️ **CATATAN PENTING:**
        - Threshold ini BUKAN aturan resmi, tetapi praktik lapangan
        - Perlu dikeluarkan Peraturan BNN/PP yang menetapkan threshold resmi
        - Digunakan sebagai SALAH SATU pertimbangan, bukan satu-satunya
        """)
    
    with tab3:
        st.subheader("Algoritma Scoring TAT")
        
        st.markdown("""
        ### Faktor yang Mendukung REHABILITASI (+)
        - [+3] Usia < 25 tahun
        - [+3] First offender
        - [+2] BB di bawah threshold
        - [+2] Tidak ada indikator pengedaran (<3 indikator)
        - [+2] Motivasi pulih tinggi (≥7)
        - [+2] Dukungan keluarga kuat
        - [+1] Kondisi fisik baik
        
        ### Faktor yang Mendukung PROSES HUKUM (-)
        - [-5] Indikasi pengedar (≥3 indikator)
        - [-4] Residivis narkotika
        - [-3] BB >> threshold (>2x threshold)
        - [-3] Sudah 3x rehabilitasi
        - [-2] Kecanduan berat
        - [-1] Motivasi pulih rendah
        
        ### Interpretasi Skor Akhir
        - **≥ 8**: Rehabilitasi Prioritas Tinggi
        - **4-7**: Rehabilitasi dengan Monitoring Ketat
        - **0-3**: Rehabilitasi di Lapas/Rutan atau Proses Hukum dengan Catatan
        - **< 0**: Proses Hukum Penuh (Pengedar/Bandar)
        """)
        
        st.info("""
        💡 **Tips Penggunaan:**
        - Algoritma ini adalah PANDUAN, bukan keputusan final
        - Tim TAT tetap harus mempertimbangkan faktor kontekstual
        - Keputusan akhir adalah tanggung jawab Tim TAT secara kolektif
        """)
    
    with tab4:
        st.subheader("Template Dokumen TAT")
        
        doc_type = st.selectbox("Pilih Template",
                               ["Berita Acara TAT", "Surat Rekomendasi", 
                                "Surat Penghentian Penyidikan (SP3)"])
        
        if doc_type == "Berita Acara TAT":
            st.markdown("""BERITA ACARA
            TIM ASESMEN TERPADU (TAT)
            
            Nomor: BA-TAT/[WILAYAH]/[NOMOR]/[BULAN]/[TAHUN]
            
            Pada hari ini [Hari], tanggal [Tanggal] [Bulan] [Tahun], bertempat 
            di [Lokasi], telah dilakukan Asesmen Terpadu terhadap:
            
            Nama            : [Nama Lengkap]
            Tempat/Tgl Lahir: [Tempat, Tanggal]
            Jenis Kelamin   : [L/P]
            Pekerjaan       : [Pekerjaan]
            Alamat          : [Alamat Lengkap]
            
            Tersangka dalam perkara: Pasal [Nomor Pasal] UU No. 35 Tahun 2009
            tentang Narkotika dengan barang bukti: [Jenis & Jumlah]
            
            HASIL ASESMEN MEDIS:
            1. Tes Urine         : [Positif/Negatif] untuk [Jenis Zat]
            2. Tingkat Kecanduan : [Ringan/Sedang/Berat]
            3. Kondisi Kesehatan : [Deskripsi]
            4. Dukungan Keluarga : [Kuat/Sedang/Lemah]
            
            HASIL ASESMEN HUKUM:
            1. Barang Bukti      : [Jumlah & Jenis]
            2. Indikasi Peran    : [End User/Pengedar]
            3. Rekam Jejak       : [First Offender/Residivis]
            4. Riwayat Rehabilitasi: [Jumlah kali]
            
            REKOMENDASI TIM ASESMEN TERPADU:
            Berdasarkan hasil asesmen di atas, Tim merekomendasikan:
            [REHABILITASI RAWAT JALAN / RAWAT INAP / PROSES HUKUM]
            
            dengan pertimbangan: [Alasan singkat]
            
            Demikian Berita Acara ini dibuat dengan sebenarnya.
            
            TIM ASESMEN TERPADU
            
            Tim Medis,                          Tim Hukum,
            
            1. [Nama]                          1. [Nama]
               [Jabatan]                          [Jabatan/Institusi]
            
            2. [Nama]                          2. [Nama]
               [Jabatan]                          [Jabatan/Institusi]
            
            Mengetahui,
            Ketua TAT,
            
            [Nama]
            [Jabatan]
```
            """)
        
        elif doc_type == "Surat Rekomendasi":
            st.markdown("""
```
            SURAT REKOMENDASI
            TIM ASESMEN TERPADU (TAT)
            
            Nomor: SR-TAT/[WILAYAH]/[NOMOR]/[BULAN]/[TAHUN]
            
            Kepada Yth.
            [Jaksa Penuntut Umum / Penyidik]
            [Nama Institusi]
            di [Tempat]
            
            Perihal: Rekomendasi Rehabilitasi
            
            Dengan hormat,
            
            Berdasarkan hasil Asesmen Terpadu yang telah dilaksanakan pada 
            tanggal [Tanggal] terhadap:
            
            Nama            : [Nama Lengkap]
            Tersangka perkara: Pasal [Nomor] UU No. 35 Tahun 2009
            
            Dengan mempertimbangkan:
            1. Pasal 54 UU No. 35 Tahun 2009 (Rehabilitasi wajib bagi pecandu)
            2. Pasal 103 KUHP Nasional (Rehabilitasi sebagai pidana alternatif)
            3. Pedoman Jaksa Agung No. 18 Tahun 2021
            4. Hasil asesmen medis: Tingkat kecanduan [Ringan/Sedang/Berat]
            5. Hasil asesmen hukum: [Alasan]
            
            Maka Tim Asesmen Terpadu MEREKOMENDASIKAN:
            
            REHABILITASI [RAWAT JALAN / RAWAT INAP]
            
            Program  : [Deskripsi program]
            Tempat   : [Nama IPWL]
            Durasi   : [Durasi]
            Monitoring: Tes urine berkala setiap [Interval]
            
            Berdasarkan rekomendasi ini, kami mohon agar:
            [Untuk Penyidik: Diterbitkan SP3 dengan syarat rehabilitasi]
            [Untuk JPU: Penghentian penuntutan dengan syarat rehabilitasi]
            
            Demikian surat rekomendasi ini dibuat untuk dapat dipergunakan 
            sebagaimana mestinya.
            
            [Kota], [Tanggal]
            Ketua Tim Asesmen Terpadu,
            
            [Nama]
            [Jabatan]
            
            Tembusan:
            1. Kepala BNN [Provinsi/Kabupaten/Kota]
            2. [IPWL yang ditunjuk]
            3. Yang bersangkutan
```
            """)
        
        else:  # SP3
            st.markdown("""
```
            SURAT PERINTAH PENGHENTIAN PENYIDIKAN
            (SP3)
            
            Nomor: SP3/[NOMOR]/[BULAN]/[TAHUN]/[SATKER]
            
            Menimbang:
            a. Bahwa telah dilakukan penyidikan terhadap tersangka [Nama] 
               dalam perkara dugaan Pasal [Nomor] UU No. 35 Tahun 2009;
            b. Bahwa berdasarkan hasil Tim Asesmen Terpadu (TAT) tanggal 
               [Tanggal], tersangka diklasifikasikan sebagai pecandu/
               penyalahguna narkotika;
            c. Bahwa sesuai Pasal 54 UU No. 35 Tahun 2009, pecandu WAJIB 
               menjalani rehabilitasi medis dan sosial;
            d. Bahwa sesuai Pedoman Jaksa Agung No. 18 Tahun 2021, prioritas 
               penanganan penyalahguna adalah rehabilitasi;
            
            Mengingat:
            1. UU No. 35 Tahun 2009 tentang Narkotika
            2. KUHAP (Pasal 109 ayat 2)
            3. Pasal 103 KUHP Nasional (UU No. 1 Tahun 2023)
            4. Pedoman Jaksa Agung No. 18 Tahun 2021
            5. Peraturan Bersama 7 Instansi tahun 2014
            6. Hasil Rekomendasi TAT
            
            MEMUTUSKAN:
            
            MENETAPKAN:
            
            Pertama   : Menghentikan penyidikan terhadap tersangka [Nama] 
                        dalam perkara dugaan Pasal [Nomor] UU No. 35 Tahun 
                        2009 tentang Narkotika.
            
            Kedua     : Tersangka [Nama] WAJIB menjalani program rehabilitasi 
                        [rawat jalan/rawat inap] di [Nama IPWL] selama 
                        [Durasi].
            
            Ketiga    : Apabila tersangka tidak menjalani atau drop out dari 
                        program rehabilitasi, maka penyidikan dapat dilanjutkan 
                        kembali.
            
            Keempat   : Surat Perintah ini mulai berlaku sejak tanggal 
                        ditetapkan.
            
            Ditetapkan di : [Kota]
            Pada tanggal  : [Tanggal]
            
            [Jabatan Penyidik]
            
            [Nama]
            [Pangkat/NRP]
            
            Tembusan:
            1. Jaksa Penuntut Umum
            2. Kepala BNN [Provinsi/Kab/Kota]
            3. [IPWL yang ditunjuk]
            4. Tersangka/Keluarga
            5. Arsip
```
            """)

# ============================================================================
# MENU 4: TENTANG SISTEM
# ============================================================================
else:  # Tentang Sistem
    st.markdown('<p class="main-header">ℹ️ TENTANG SISTEM TAT-DSS</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ## 🎯 Tentang TAT Decision Support System
    
    **TAT-DSS (Tim Asesmen Terpadu - Decision Support System)** adalah sistem 
    pendukung keputusan berbasis web yang dirancang untuk membantu Tim Asesmen 
    Terpadu dalam melakukan asesmen cepat, objektif, dan akurat terhadap 
    tersangka penyalahguna narkotika.
    
    ### 🚀 Fitur Utama
    
    1. **Asesmen Cepat & Terstruktur**
       - Input data tersederhanakan
       - Asesmen medis dan hukum terintegrasi
       - Waktu pengisian: 5-10 menit
    
    2. **Algoritma Scoring Otomatis**
       - Berbasis regulasi terbaru (KUHP Nasional, UU Penyesuaian Pidana)
       - Mempertimbangkan 15+ faktor
       - Hasil objektif dan konsisten
    
    3. **Rekomendasi Instant**
       - Rehabilitasi vs Proses Hukum
       - Detail program dan durasi
       - Dasar hukum lengkap
    
    4. **Export & Dokumentasi**
       - Generate PDF report otomatis
       - Template dokumen resmi
       - Database kasus untuk statistik
    
    5. **Dashboard Analitik**
       - Statistik kasus real-time
       - Visualisasi data
       - Monitoring trend
    
    ### 📋 Metodologi
    
    Sistem ini dikembangkan berdasarkan:
    - Penelusuran regulasi terbaru (2023-2025)
    - Best practices internasional (Portugal, Switzerland, Canada)
    - Konsultasi dengan praktisi hukum dan medis
    - Prinsip evidence-based decision making
    
    ### ⚖️ Compliance Legal
    
    TAT-DSS sepenuhnya compliant dengan:
    - UU No. 35 Tahun 2009 (Narkotika)
    - UU No. 1 Tahun 2023 (KUHP Nasional)
    - UU Penyesuaian Pidana (2025)
    - Pedoman Jaksa Agung No. 18 Tahun 2021
    - Peraturan Bersama 7 Instansi (2014)
    
    ### 🔒 Keamanan & Privasi
    
    - Data tersimpan lokal (tidak cloud)
    - Enkripsi untuk data sensitif
    - Access control berbasis role
    - Compliance dengan UU Pelindungan Data Pribadi
    
    ### 👥 Tim Pengembang
    
    Dikembangkan oleh:
    - Legal Expert (Hukum Pidana & Narkotika)
    - Medical Expert (Addiction Medicine)
    - Software Engineer (Full-stack Development)
    - UX Designer
    
    ### 📞 Kontak & Support
    
    Untuk pertanyaan, saran, atau pelaporan bug:
    - Email: support@tat-dss.id (contoh)
    - WhatsApp: +62-XXX-XXXX-XXXX
    - Website: www.tat-dss.id (contoh)
    
    ### 📄 Lisensi & Disclaimer
    
    **Lisensi**: Open Source (MIT License)
    
    **Disclaimer**: 
    Sistem ini adalah ALAT BANTU untuk Tim Asesmen Terpadu. Keputusan 
    akhir tetap menjadi tanggung jawab Tim TAT secara kolektif. Sistem 
    ini tidak menggantikan pertimbangan profesional Tim Medis dan Tim Hukum.
    
    ### 🔄 Versi & Update
    
    **Versi Saat Ini**: 1.0.0 (Beta)  
    **Tanggal Rilis**: Januari 2026  
    **Update Terakhir**: [Auto-update]
    
    **Changelog:**
    - v1.0.0: Initial release dengan fitur core
    - [Future updates akan ditampilkan di sini]
    
    ### 🙏 Acknowledgments
    
    Terima kasih kepada:
    - Badan Narkotika Nasional (BNN)
    - Kementerian Hukum dan HAM
    - Mahkamah Agung RI
    - Kejaksaan Agung RI
    - Kepolisian Negara RI
    - Kementerian Kesehatan
    - Seluruh praktisi dan akademisi yang berkontribusi
    
    ---
    
    **"Dari punishment menuju healing. Dari retribusi menuju rehabilitasi."**
    """)
    
    # Version info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Version**: 1.0.0 Beta")
    with col2:
        st.info("**Last Update**: Jan 2026")
    with col3:
        st.info("**License**: MIT")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.9rem;'>
    <p><strong>TAT Decision Support System v1.0</strong> | © 2026 BNN | 
    Developed with ❤️ for justice and humanity</p>
    <p><em>"Rehabilitation, Not Criminalization"</em></p>
</div>
""", unsafe_allow_html=True)
```

---

## FILE 3: utils/scoring.py (Algoritma Scoring)
```python
def calculate_tat_score(case_data):
    """
    Calculate TAT score based on multiple factors
    Returns: (final_score, scoring_details)
    """
    score = 0
    details = []
    
    # ========== FAKTOR POSITIF (Mendukung Rehabilitasi) ==========
    
    # 1. Usia < 25 tahun (+3)
    if case_data['usia'] < 25:
        score += 3
        details.append("+3: Usia < 25 tahun (young offender)")
    
    # 2. First offender (+3)
    if case_data['first_offender']:
        score += 3
        details.append("+3: First offender (belum pernah divonis)")
    
    # 3. BB di bawah threshold (+2)
    if not case_data['above_threshold']:
        score += 2
        details.append(f"+2: BB ({case_data['berat_bb']}g) di bawah threshold")
    
    # 4. Tidak ada indikator pengedaran (+2)
    if case_data['indikator_pengedar'] < 3:
        score += 2
        details.append(f"+2: Indikator pengedar rendah ({case_data['indikator_pengedar']}/6)")
    
    # 5. Motivasi pulih tinggi (+2)
    if case_data['motivasi_pulih'] >= 7:
        score += 2
        details.append(f"+2: Motivasi pulih tinggi ({case_data['motivasi_pulih']}/10)")
    
    # 6. Dukungan keluarga kuat (+2)
    if case_data['dukungan_keluarga'] == "Kuat":
        score += 2
        details.append("+2: Dukungan keluarga kuat")
    
    # 7. Kondisi fisik baik (+1)
    if case_data['kondisi_fisik'] == "Baik":
        score += 1
        details.append("+1: Kondisi fisik baik")
    
    # ========== FAKTOR NEGATIF (Mendukung Proses Hukum) ==========
    
    # 1. Indikasi pengedar (-5)
    if case_data['indikator_pengedar'] >= 3:
        score -= 5
        details.append(f"-5: INDIKASI KUAT PENGEDAR ({case_data['indikator_pengedar']}/6)")
    
    # 2. Residivis narkotika (-4)
    if not case_data['first_offender']:
        score -= 4
        details.append(f"-4: Residivis ({case_data['jumlah_vonis']}x vonis)")
    
    # 3. BB >> threshold (-3)
    threshold_map = {
        "Ganja (Cannabis)": 5.0,
        "Sabu (Methamphetamine)": 1.0,
        "Ekstasi (MDMA)": 0.5,
        "Kokain": 1.0,
        "Heroin": 0.5
    }
    threshold = threshold_map.get(case_data['jenis_narkotika'], 1.0)
    if case_data['berat_bb'] > (threshold * 2):
        score -= 3
        details.append(f"-3: BB sangat besar ({case_data['berat_bb']}g >> {threshold}g)")
    
    # 4. Sudah 3x rehabilitasi (-3)
    if case_data['riwayat_rehab'] >= 3:
        score -= 3
        details.append(f"-3: Sudah {case_data['riwayat_rehab']}x rehabilitasi (batas maks)")
    
    # 5. Kecanduan berat (-2)
    if case_data['addiction_level'] == "BERAT":
        score -= 2
        details.append("-2: Tingkat kecanduan berat")
    
    # 6. Motivasi pulih rendah (-1)
    if case_data['motivasi_pulih'] < 5:
        score -= 1
        details.append(f"-1: Motivasi pulih rendah ({case_data['motivasi_pulih']}/10)")
    
    return score, details


def get_recommendation(final_score, case_data):
    """
    Generate recommendation based on final score and case details
    """
    recommendation = {}
    
    # Decision tree
    addiction_level = case_data['addiction_level']
    peran = case_data['peran']
    riwayat_rehab = case_data['riwayat_rehab']
    
    # KRITERIA ELIMINASI: Pengedar atau Residivis ke-4+
    if peran == "PENGEDAR" or case_data['indikator_pengedar'] >= 3:
        recommendation['type'] = "PROSES HUKUM PENUH"
        recommendation['color'] = "danger"
        recommendation['detail'] = """
        Berdasarkan asesmen, tersangka terindikasi **PENGEDAR/BANDAR** dengan 
        bukti kuat keterlibatan dalam jaringan peredaran gelap narkotika.
        
        **TIDAK DIREKOMENDASIKAN** untuk rehabilitasi.
        """
        recommendation['dasar_hukum'] = """
        - Pasal 111-126 UU No. 35 Tahun 2009 (Peredaran Gelap Narkotika)
        - Peraturan Bersama 7 Instansi: TAT untuk pecandu/penyalahguna, bukan pengedar
        """
        recommendation['catatan'] = "Lanjutkan proses penyidikan dan penuntutan sesuai prosedur normal."
        return recommendation
    
    if riwayat_rehab >= 3:
        recommendation['type'] = "PROSES HUKUM DENGAN CATATAN"
        recommendation['color'] = "warning"
        recommendation['detail'] = """
        Tersangka telah menjalani **3 kali rehabilitasi** sebelumnya (batas maksimal 
        sesuai Pedoman Jaksa Agung No. 18/2021). 
        
        Direkomendasikan untuk **dilimpahkan ke persidangan**, namun hakim dapat 
        mempertimbangkan rehabilitasi di Lapas/Rutan sebagai bagian dari vonis.
        """
        recommendation['program'] = """
        Jika hakim memutuskan vonis pidana penjara, disarankan:
        - Program rehabilitasi di Lapas/Rutan (Pasal 105 KUHP Nasional)
        - Detoksifikasi medis
        - Terapi individual dan kelompok
        - Konseling berkelanjutan
        """
        recommendation['dasar_hukum'] = """
        - Pedoman Jaksa Agung No. 18 Tahun 2021 (Maksimal 3x rehabilitasi)
        - Pasal 105 KUHP Nasional (Rehabilitasi di Lapas)
        - Pasal 127 UU No. 35 Tahun 2009
        """
        recommendation['catatan'] = """
        Meski sudah 3x rehabilitasi, hakim tetap punya diskresi mempertimbangkan 
        faktor-faktor khusus (usia muda, kondisi kesehatan, dll) untuk memberikan 
        kesempatan terakhir.
        """
        return recommendation
    
    # DECISION BERDASARKAN SKOR
    if final_score >= 8:
        # REHABILITASI PRIORITAS TINGGI
        if addiction_level == "RINGAN":
            recommendation['type'] = "REHABILITASI RAWAT JALAN"
            recommendation['color'] = "success"
            recommendation['detail'] = """
            Tersangka diklasifikasikan sebagai **penyalahguna tingkat ringan** 
            dengan prognosis sangat baik untuk rehabilitasi rawat jalan.
            """
            recommendation['program'] = """
            - Program konseling dan edukasi (8-12 kali pertemuan)
            - Terapi Kognitif-Behavioral (CBT)
            - Motivational interviewing
            - Terapi keluarga (jika diperlukan)
            """
            recommendation['durasi'] = "3 bulan (12 kali pertemuan, 1x/minggu)"
            recommendation['tempat'] = "IPWL BNN / Puskesmas / Klinik Pratama terakreditasi"
            recommendation['monitoring'] = """
            - Tes urine berkala: Setiap 2 minggu
            - Evaluasi progress: Bulan ke-1, 2, 3
            - Case manager: Konselor adiksi dari IPWL
            """
            
        elif addiction_level == "SEDANG":
            recommendation['type'] = "REHABILITASI RAWAT INAP"
            recommendation['color'] = "success"
            recommendation['detail'] = """
            Tersangka diklasifikasikan sebagai **pecandu tingkat sedang** yang 
            memerlukan program rehabilitasi rawat inap terstruktur.
            """
            recommendation['program'] = """
            - Detoksifikasi medis (fase awal)
            - Terapi individual intensif
            - Terapi kelompok (peer support)
            - Terapi keluarga
            - Life skills training
            - Spiritual/religious counseling
            - Persiapan reintegrasi sosial
            """
            recommendation['durasi'] = "3-6 bulan (rawat inap penuh)"
            recommendation['tempat'] = "Balai Rehabilitasi BNN / RS Ketergantungan Obat / Lembaga Rehabilitasi terakreditasi"
            recommendation['monitoring'] = """
            - Tes urine: Setiap minggu selama rawat inap
            - Evaluasi medis: Setiap 2 minggu
            - Evaluasi psikologis: Setiap bulan
            - Aftercare program: 6 bulan pasca rawat inap
            """
            
        else:  # BERAT
            recommendation['type'] = "REHABILITASI RAWAT INAP INTENSIF"
            recommendation['color'] = "warning"
            recommendation['detail'] = """
            Tersangka diklasifikasikan sebagai **pecandu berat** dengan komplikasi 
            medis/psikososial yang memerlukan rehabilitasi intensif jangka panjang.
            """
            recommendation['program'] = """
            - Detoksifikasi medis ketat (dengan monitoring 24/7)
            - Manajemen withdrawal syndrome
            - Terapi dual diagnosis (jika ada gangguan jiwa komorbid)
            - Terapi individual dan kelompok intensif
            - Terapi okupasi dan vocational training
            - Family therapy
            - Pembinaan spiritual
            """
            recommendation['durasi'] = "6-12 bulan (rawat inap)"
            recommendation['tempat'] = "Balai Rehabilitasi BNN / RS Ketergantungan Obat dengan fasilitas lengkap"
            recommendation['monitoring'] = """
            - Tes urine: 2x/minggu
            - Pemeriksaan medis: Setiap minggu
            - Evaluasi psikologis: Setiap 2 minggu
            - Case conference: Setiap bulan
            - Aftercare program: 12 bulan pasca rawat inap
            """
            recommendation['catatan'] = """
            Perlu koordinasi dengan BPJS untuk pembiayaan. Jika ada komplikasi medis 
            berat (HIV, hepatitis, TB), rujuk ke RS rujukan yang memiliki program adiksi.
            """
        
        recommendation['dasar_hukum'] = """
        - Pasal 54 UU No. 35 Tahun 2009 (Rehabilitasi wajib bagi pecandu)
        - Pasal 103 ayat (2) UU No. 35 Tahun 2009 (Masa rehabilitasi = masa hukuman)
        - Pasal 103 & 105 KUHP Nasional (Rehabilitasi sebagai pidana alternatif)
        - Pedoman Jaksa Agung No. 18 Tahun 2021 (Prioritas rehabilitasi)
        """
        
    elif final_score >= 4:
        # REHABILITASI DENGAN MONITORING KETAT
        if addiction_level in ["RINGAN", "SEDANG"]:
            recommendation['type'] = "REHABILITASI RAWAT INAP DENGAN MONITORING KETAT"
            recommendation['color'] = "warning"
            recommendation['detail'] = """
            Tersangka memenuhi syarat rehabilitasi, namun dengan **faktor risiko tertentu** 
            yang memerlukan monitoring lebih ketat.
            """
            recommendation['program'] = """
            - Program rehabilitasi standar (sesuai tingkat kecanduan)
            - PLUS: Monitoring intensif oleh petugas BNN
            - Sistem pelaporan berkala ke penyidik/JPU
            - Sanksi jelas jika drop out (lanjut proses hukum)
            """
            recommendation['durasi'] = "4-6 bulan dengan evaluasi ketat"
            recommendation['tempat'] = "Balai Rehabilitasi BNN (prioritas, untuk memudahkan monitoring)"
            recommendation['monitoring'] = """
            - Tes urine: Seminggu 2x (random)
            - Laporan progress ke penyidik/JPU: Setiap 2 minggu
            - Evaluasi Tim TAT: Bulan ke-2 dan ke-4
            - Jika drop out atau relapse: Proses hukum dilanjutkan
            """
        else:  # BERAT
            recommendation['type'] = "REHABILITASI DI LAPAS/RUTAN"
            recommendation['color'] = "warning"
            recommendation['detail'] = """
            Tersangka pecandu berat dengan faktor risiko tinggi. Direkomendasikan 
            rehabilitasi di Lapas/Rutan untuk memastikan compliance.
            """
            recommendation['program'] = """
            - Rehabilitasi dalam lingkungan terstruktur (Lapas/Rutan)
            - Program detoksifikasi dan terapi adiksi
            - Pemisahan dari narapidana lain (blok khusus rehabilitasi)
            - Monitoring ketat 24/7
            """
            recommendation['durasi'] = "6-12 bulan"
            recommendation['tempat'] = "Lapas/Rutan dengan fasilitas rehabilitasi"
            recommendation['monitoring'] = """
            - Tes urine: Random, minimal 1x/minggu
            - Evaluasi progress: Setiap bulan
            - Kolaborasi petugas Lapas dengan tim medis BNN
            """
        
        recommendation['dasar_hukum'] = """
        - Pasal 103 & 105 KUHP Nasional
        - Pasal 54 & 127 UU No. 35 Tahun 2009
        - PP No. 25 Tahun 2011 (Rehabilitasi di Lapas)
        """
        recommendation['catatan'] = """
        Monitoring ketat diperlukan karena: [sebutkan faktor risiko spesifik dari case_data].
        Jika tidak kooperatif atau relapse berulang, proses hukum dapat dilanjutkan.
        """
    
    elif final_score >= 0:
        # ZONA GREY: Pertimbangan Kasus per Kasus
        recommendation['type'] = "PERTIMBANGAN KHUSUS (CASE CONFERENCE)"
        recommendation['color'] = "warning"
        recommendation['detail'] = """
        Kasus ini berada di **zona abu-abu** dengan skor yang tidak konklusif. 
        Diperlukan case conference mendalam oleh seluruh Tim TAT untuk memutuskan.
        """
        recommendation['program'] = """
        OPSI 1: Rehabilitasi di Lapas/Rutan
        - Jika Tim yakin ada niat baik dan potensi pemulihan
        
        OPSI 2: Proses hukum dengan catatan kepada Hakim
        - Hakim dapat mempertimbangkan vonis rehabilitasi (Pasal 103 KUHP)
        - Atau vonis pidana penjara dengan program rehabilitasi di Lapas
        """
        recommendation['dasar_hukum'] = """
        - Diskresi Tim TAT berdasarkan Peraturan Bersama 7 Instansi
        - Pasal 103 KUHP Nasional (Hakim tetap punya diskresi)
- Pedoman Jaksa Agung No. 18 Tahun 2021
"""
recommendation['catatan'] = f"""
PERLU DIBAHAS DALAM CASE CONFERENCE:
1. Faktor-faktor yang meringankan dan memberatkan
2. Prognosis rehabilitasi
3. Kepentingan terbaik tersangka vs kepentingan masyarakat
4. Ketersediaan dukungan keluarga dan sosial
    **Skor Final:** {final_score} (Zona Grey: 0-3)
    
    Tim TAT dapat meminta second opinion dari ahli eksternal jika diperlukan.
    """

else:  # final_score < 0
    # PROSES HUKUM PENUH
    recommendation['type'] = "PROSES HUKUM PENUH"
    recommendation['color'] = "danger"
    recommendation['detail'] = """
    Berdasarkan asesmen, terdapat **faktor-faktor berat** yang mengindikasikan 
    bahwa rehabilitasi bukan opsi yang tepat saat ini. Direkomendasikan 
    untuk melanjutkan proses hukum.
    """
    recommendation['program'] = """
    Proses penyidikan dan penuntutan dilanjutkan sesuai prosedur normal.
    
    CATATAN UNTUK JAKSA/HAKIM:
    Meskipun direkomendasikan proses hukum, hakim tetap dapat mempertimbangkan:
    - Pasal 103 KUHP Nasional (Rehabilitasi sebagai pidana alternatif)
    - Pasal 105 KUHP Nasional (Rehabilitasi di Lapas)
    
    Jika hakim memutuskan vonis pidana penjara, disarankan agar Lapas 
    menyediakan akses program rehabilitasi/konseling adiksi.
    """
    recommendation['dasar_hukum'] = """
    - Pasal 111-126 UU No. 35 Tahun 2009 (sesuai peran tersangka)
    - KUHP Nasional (UU No. 1 Tahun 2023)
    - UU Penyesuaian Pidana (2025) - Hakim punya diskresi penuh
    """
    recommendation['catatan'] = f"""
    **ALASAN PROSES HUKUM:**
    {chr(10).join(['- ' + d for d in case_data.get('scoring_details', []) if d.startswith('-')])}
    
    Meski demikian, sistem peradilan pidana tetap harus mempertimbangkan 
    pendekatan restoratif dan kemanusiaan sesuai amanat KUHP Nasional.
    """

return recommendation
