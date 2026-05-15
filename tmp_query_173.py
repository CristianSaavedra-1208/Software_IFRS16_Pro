from db import cargar_contratos, cargar_remediciones_todas_agrupadas
lista_c_todas = [c for c in cargar_contratos() if c['Empresa'] == 'Pacifico']
rems_grupos = cargar_remediciones_todas_agrupadas()

found = []
for c in lista_c_todas:
    for key, val in c.items():
        if isinstance(val, (int, float)):
            if abs(val - 173984) < 1000 or abs(val) == 173984:
                found.append(f"{c['Codigo_Interno']}: {key} = {val}")
    for r in rems_grupos.get(c['Codigo_Interno'], []):
        for key, val in r.items():
            if isinstance(val, (int, float)):
                if abs(val - 173984) < 1000 or abs(val) == 173984:
                    found.append(f"{c['Codigo_Interno']} Rem: {key} = {val}")
print('Found:', found)
