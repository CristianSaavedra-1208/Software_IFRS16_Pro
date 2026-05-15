from db import cargar_contratos, cargar_remediciones_todas_agrupadas
lista_c_todas = [c for c in cargar_contratos() if c['Empresa'] == 'Pacifico']
rems_grupos = cargar_remediciones_todas_agrupadas()

for c in lista_c_todas:
    for r in rems_grupos.get(c['Codigo_Interno'], []):
        bp = float(r.get('Baja_Pasivo') or 0.0)
        br = float(r.get('Baja_ROU') or 0.0)
        if bp > 0 or br > 0:
            print(f"Contract {c['Codigo_Interno']} has Reduccion: Baja_Pasivo={bp}, Baja_ROU={br}")
