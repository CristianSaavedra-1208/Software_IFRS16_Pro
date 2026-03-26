import sqlite3
import pandas as pd

conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
print("--- CAMPO_EXTRA ---")
df = pd.read_sql("SELECT * FROM config_params WHERE tipo='CAMPO_EXTRA'", conn)
print(df)

# Let's also verify how pandas parses an excel file with a comma in large numbers
# The user might have formatted the Excel cell as "23.040,94"
c = "23040,94"
c2 = "23,040.94"
try: print('float of c:', float(c))
except Exception as e: print('error:', e)
try: print('float of c2:', float(c2.replace(',', '')))
except Exception as e: print('error:', e)

conn.close()
