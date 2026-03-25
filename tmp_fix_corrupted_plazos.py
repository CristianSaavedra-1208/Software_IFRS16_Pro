import sqlite3
import pandas as pd

conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
cursor = conn.cursor()

# Encontrar los contratos afectados
cursor.execute("SELECT Codigo_Interno, SUM(Plazo) as total_n_p FROM remediciones GROUP BY Codigo_Interno")
rems = cursor.fetchall()

updated = 0
for r in rems:
    cod = r[0]
    total_np = r[1]
    cursor.execute("SELECT Plazo FROM contratos WHERE Codigo_Interno=?", (cod,))
    c = cursor.fetchone()
    if c:
        current_plazo = c[0]
        # Restamos los meses de extension que app.py sumo por error
        orig_plazo = current_plazo - total_np
        
        # Validacion logica: el plazo original jamas puede ser negativo ni cero
        if orig_plazo > 0:
            cursor.execute("UPDATE contratos SET Plazo=? WHERE Codigo_Interno=?", (orig_plazo, cod))
            updated += 1
            print(f"[{cod}] Restaurado Plazo original de {current_plazo} a {orig_plazo}")

conn.commit()
conn.close()
print(f"Ejecucion terminada. Se sanitaron temporal {updated} contratos.")
