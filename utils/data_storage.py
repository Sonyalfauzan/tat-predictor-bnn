import json
import os
from datetime import datetime
import pandas as pd

# Data file path
DATA_FILE = "tat_cases.json"

def save_case(case_data, recommendation):
    """
    Save case to JSON file (simple persistence)
    """
    # Load existing cases
    cases = load_cases()
    
    # Add timestamp and recommendation
    case_data['timestamp'] = datetime.now().isoformat()
    case_data['recommendation_type'] = recommendation.get('type', '')
    
    # Append new case
    cases.append(case_data)
    
    # Save to file
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    
    return True

def load_cases():
    """
    Load all cases from JSON file
    """
    if not os.path.exists(DATA_FILE):
        return []
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        return cases
    except:
        return []

def get_statistics(cases):
    """
    Calculate statistics from cases
    """
    if len(cases) == 0:
        return {
            'total_cases': 0,
            'rehab_percentage': 0,
            'avg_age': 0,
            'first_offender_percentage': 0,
            'recommendation_distribution': {},
            'addiction_level_distribution': {},
            'drug_type_distribution': {}
        }
    
    df = pd.DataFrame(cases)
    
    # Total cases
    total_cases = len(df)
    
    # Rehab percentage (recommendation contains "REHABILITASI")
    rehab_cases = df[df['recommendation_type'].str.contains('REHABILITASI', na=False)]
    rehab_percentage = (len(rehab_cases) / total_cases) * 100
    
    # Average age
    avg_age = df['usia'].mean()
    
    # First offender percentage
    first_offender_count = df['first_offender'].sum()
    first_offender_percentage = (first_offender_count / total_cases) * 100
    
    # Recommendation distribution
    recommendation_distribution = df['recommendation_type'].value_counts().to_dict()
    
    # Addiction level distribution
    addiction_level_distribution = df['addiction_level'].value_counts().to_dict()
    
    # Drug type distribution
    drug_type_distribution = df['jenis_narkotika'].value_counts().to_dict()
    
    return {
        'total_cases': total_cases,
        'rehab_percentage': rehab_percentage,
        'avg_age': avg_age,
        'first_offender_percentage': first_offender_percentage,
        'recommendation_distribution': recommendation_distribution,
        'addiction_level_distribution': addiction_level_distribution,
        'drug_type_distribution': drug_type_distribution
    }

def export_to_excel(cases, filename="tat_export.xlsx"):
    """
    Export cases to Excel file
    """
    if len(cases) == 0:
        return None
    
    df = pd.DataFrame(cases)
    
    # Select relevant columns
    columns = ['nama', 'usia', 'jenis_kelamin', 'tanggal_asesmen',
               'jenis_narkotika', 'berat_bb', 'addiction_level',
               'peran', 'first_offender', 'final_score', 'recommendation_type']
    
    df_export = df[columns]
    
    # Rename columns for better readability
    df_export.columns = ['Nama', 'Usia', 'Jenis Kelamin', 'Tanggal Asesmen',
                         'Jenis Narkotika', 'BB (gram)', 'Tingkat Kecanduan',
                         'Peran', 'First Offender', 'Skor Final', 'Rekomendasi']
    
    # Save to Excel
    df_export.to_excel(filename, index=False)
    
    return filename
