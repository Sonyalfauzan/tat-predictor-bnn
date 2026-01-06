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
