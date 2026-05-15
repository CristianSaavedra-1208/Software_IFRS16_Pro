import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
from datetime import date
from unittest.mock import patch, MagicMock
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import motor_financiero_v21, modulo_asientos
from core import simular_libro_mayor

st.session_state.auth = True

def run_asientos_mes(m_idx, a=2026):
    with patch('streamlit.selectbox') as mock_sb, \
         patch('streamlit.number_input') as mock_ni, \
         patch('streamlit.button') as mock_btn, \
         patch('streamlit.dataframe'), \
         patch('streamlit.download_button'), \
         patch('streamlit.header'), \
         patch('streamlit.tabs') as mock_tabs, \
         patch('streamlit.expander'), \
         patch('streamlit.info'), \
         patch('streamlit.columns') as mock_cols:
         
        c1, c2, c3 = MagicMock(), MagicMock(), MagicMock()
        mock_cols.return_value = [c1, c2, c3]
        
        mock_sb.side_effect = lambda *args, **kwargs: 'Pacifico' if args[0] == 'Empresa' else ['Enero', 'Febrero', 'Marzo'][m_idx-1]
        c1.selectbox.return_value = 'Pacifico'
        c2.selectbox.return_value = ['Enero', 'Febrero', 'Marzo'][m_idx-1]
        c3.number_input.return_value = a
        mock_btn.return_value = True
        
        t1, t2 = MagicMock(), MagicMock()
        mock_tabs.return_value = [t1, t2]
        t1.__enter__.return_value = t1
        t1.__exit__.return_value = False
        t2.__enter__.return_value = t2
        t2.__exit__.return_value = False
        
        modulo_asientos()
        
    return st.session_state.get('asientos_data', [])

asientos_per_contract = {}

for m in [1, 2, 3]:
    detalles = run_asientos_mes(m)
    for d in detalles:
        c_code = d.get('Cod1')
        if not c_code: continue
        
        if c_code not in asientos_per_contract:
            asientos_per_contract[c_code] = {'rou': 0.0, 'aa': 0.0}
            
        cta_num = str(d.get('N° Cuenta')).strip()
        debe = float(d.get('Debe', 0))
        haber = float(d.get('Haber', 0))
        
        if cta_num in ['1401', '1208104', '1208114']:
            asientos_per_contract[c_code]['rou'] += (debe - haber)
        elif cta_num in ['1402', '1208105', '1208115']:
            asientos_per_contract[c_code]['aa'] += (haber - debe)

lista_c_todas = [c for c in cargar_contratos() if c['Empresa'] == 'Pacifico']
rems_grupos = cargar_remediciones_todas_agrupadas()

f_ant = pd.to_datetime(date(2025, 12, 31))
f_act = pd.to_datetime(date(2026, 3, 31))

print("Contratos con diferencia ROU o AA > 100")
total_diff_rou = 0
total_diff_aa = 0

for c in lista_c_todas:
    c_code = c['Codigo_Interno']
    tab, vp, rou = motor_financiero_v21(c, rems=rems_grupos.get(c_code, []))
    tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
    if tc_ini_hist <= 0: tc_ini_hist = 1.0
    
    rb_1, aa_1, p_1 = simular_libro_mayor(c, tab, f_ant, rems_grupos.get(c_code, []), tc_ini_hist, vp, rou)
    rb_2, aa_2, p_2 = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c_code, []), tc_ini_hist, vp, rou)
    
    mov_recon_rou = rb_2 - rb_1
    mov_recon_aa = aa_2 - aa_1
    
    asiento_rou = asientos_per_contract.get(c_code, {}).get('rou', 0.0)
    asiento_aa = asientos_per_contract.get(c_code, {}).get('aa', 0.0)
    
    diff_rou = mov_recon_rou - asiento_rou
    diff_aa = mov_recon_aa - asiento_aa
    
    total_diff_rou += diff_rou
    total_diff_aa += diff_aa
    
    if abs(diff_rou) > 100 or abs(diff_aa) > 100:
        print(f"[{c_code}] Diff ROU: {diff_rou:,.0f} | Diff AA: {diff_aa:,.0f} | Recon ROU: {mov_recon_rou:,.0f} | Asiento ROU: {asiento_rou:,.0f} | Recon AA: {mov_recon_aa:,.0f} | Asiento AA: {asiento_aa:,.0f} | Estado: {c['Estado']}")

print(f"TOTAL DIFF ROU: {total_diff_rou:,.0f}")
print(f"TOTAL DIFF AA: {total_diff_aa:,.0f}")
