import pandas as pd
from datetime import date
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import obtener_motor_financiero
from core import simular_libro_mayor

contratos = cargar_contratos()
rems_grupos = cargar_remediciones_todas_agrupadas()

target_ids = ['CNT-HOL-0008', 'CNT-HOL-0019', 'CNT-HOL-0195', 'CNT-PAC-0087', 'CNT-PAC-0116', 'CNT-PAC-0120', 'CNT-HOL-008', 'CNT-HOL-019']
targets = [c for c in contratos if c['Codigo_Interno'] in target_ids]

print(f"Found {len(targets)} contracts to validate.")

for c in targets:
    print(f"\n{'='*50}")
    print(f"Validating {c['Codigo_Interno']} - {c['Empresa']}")
    
    rems = rems_grupos.get(c['Codigo_Interno'], [])
    tab, vp, rou = obtener_motor_financiero(c, rems=rems)
    
    # 1. Initial VPN
    print(f"Initial VPN (VP): {vp:,.2f}")
    print(f"Initial ROU: {rou:,.2f}")
    print(f"Moneda: {c['Moneda']}")
    
    tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
    if tc_ini_hist <= 0: tc_ini_hist = 1.0
    
    # Evaluate at 31.12.2024 (Start of 2025) and 31.12.2025 (End of 2025)
    f_start = pd.to_datetime('2024-12-31')
    f_end = pd.to_datetime('2025-12-31')
    
    rb_2024, aa_2024, p_2024 = simular_libro_mayor(c, tab, f_start, rems, tc_ini_hist, vp, rou)
    rb_2025, aa_2025, p_2025 = simular_libro_mayor(c, tab, f_end, rems, tc_ini_hist, vp, rou)
    
    print(f"\n--- Balances at 31.12.2024 ---")
    print(f"ROU Bruto: {rb_2024:,.2f}")
    print(f"Amort Acum: {aa_2024:,.2f}")
    print(f"ROU Neto: {rb_2024 - aa_2024:,.2f}")
    print(f"Pasivo: {p_2024:,.2f}")
    
    print(f"\n--- Balances at 31.12.2025 ---")
    print(f"ROU Bruto: {rb_2025:,.2f}")
    print(f"Amort Acum: {aa_2025:,.2f}")
    print(f"ROU Neto: {rb_2025 - aa_2025:,.2f}")
    print(f"Pasivo: {p_2025:,.2f}")
    
    print(f"\n--- 2025 Movements ---")
    print(f"ROU Reajustes/Additions (ROU Bruto Mov): {rb_2025 - rb_2024:,.2f}")
    print(f"Depreciation for 2025 (Amort Acum Mov): {aa_2025 - aa_2024:,.2f}")
    
    # Let's also check the monthly logic from tab for 2025
    tab_2025 = tab[(tab['Fecha'] > f_start) & (tab['Fecha'] <= f_end)]
    if not tab_2025.empty:
        total_dep = tab_2025['Dep_Orig'].sum()
        total_pago = tab_2025['Pago_Orig'].sum()
        print(f"Total Depreciacion Orig en Tabla (2025): {total_dep:,.2f}")
        # Let's pick a random month in 2025 to see how it calculates
        sample = tab_2025.iloc[0]
        print(f"Ejemplo Cuota {sample['Mes']}: Dep Orig={sample['Dep_Orig']:,.2f}")
