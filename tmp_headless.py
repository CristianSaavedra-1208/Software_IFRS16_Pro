import streamlit as st
from app import modulo_asientos
from unittest.mock import patch, MagicMock
import pandas as pd
from io import BytesIO

st.session_state.auth = True

captured_df = None

def mock_download_button(*args, **kwargs):
    global captured_df
    data = kwargs.get('data')
    if data:
        # data is Excel file bytes
        captured_df = pd.read_excel(BytesIO(data), sheet_name='Asientos')

with patch('streamlit.selectbox') as mock_sb, \
     patch('streamlit.number_input') as mock_ni, \
     patch('streamlit.button') as mock_btn, \
     patch('streamlit.dataframe'), \
     patch('streamlit.download_button', side_effect=mock_download_button), \
     patch('streamlit.header'), \
     patch('streamlit.columns') as mock_cols:
     
    # Mock columns
    c1, c2, c3 = MagicMock(), MagicMock(), MagicMock()
    mock_cols.return_value = [c1, c2, c3]
    
    # Mock return values for the column widgets
    c1.selectbox.return_value = 'Pacifico'
    c2.selectbox.return_value = 'Enero'
    c3.number_input.return_value = 2026
    
    # Actually, we can just patch streamlit.selectbox directly if they don't use the column objects
    mock_sb.side_effect = lambda *args, **kwargs: 'Todas' if args[0] == 'Empresa' else 'Enero'
    
    mock_btn.return_value = True
    
    modulo_asientos()

if captured_df is not None:
    # Let's sum up ROU and AmortAcum
    # The columns in Asientos excel are: Empresa, Cod1, Transacción, N° Cuenta, Cuenta, Tipo, Debe, Haber
    df = captured_df
    
    rou_net = 0
    aa_net = 0
    pasivo_net = 0
    for idx, r in df.iterrows():
        cta_num = str(r['N° Cuenta']).strip()
        debe = float(r['Debe']) if pd.notnull(r['Debe']) else 0
        haber = float(r['Haber']) if pd.notnull(r['Haber']) else 0
        
        # ROU is 1208104, 1208114...
        # Wait, get_cta returns standard numbers
        if cta_num in ['1401', '1208104', '1208114']:
            rou_net += (debe - haber)
        elif cta_num in ['1402', '1208105', '1208115']:
            aa_net += (haber - debe)
        elif cta_num in ['2101', '2201514', '2201515']:
            pasivo_net += (haber - debe)
            
    print(f"Total Asientos Activo Neto: {rou_net - aa_net}")
    print(f"ROU: {rou_net}, AA: {aa_net}")
    print(f"Pasivo: {pasivo_net}")
    
    # Let's check CNT-PAC-0789
    c789 = df[df['Cod1'] == 'CNT-PAC-0789']
    print("\nAsientos para CNT-PAC-0789:")
    print(c789)
