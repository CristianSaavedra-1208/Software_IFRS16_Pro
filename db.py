import sqlite3
import pandas as pd

DB_NAME = "ifrs16_platinum.db"

def conectar():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS monedas 
                      (fecha TEXT, moneda TEXT, valor REAL, PRIMARY KEY(fecha, moneda))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS contratos (
                        Codigo_Interno TEXT PRIMARY KEY, Empresa TEXT, Clase_Activo TEXT, 
                        ID TEXT, Proveedor TEXT, Cod1 TEXT, Cod2 TEXT, Nombre TEXT, 
                        Moneda TEXT, Canon REAL, Tasa REAL, Tasa_Mensual REAL,
                        Valor_Moneda_Inicio REAL, Plazo INTEGER, Inicio TEXT, Fin TEXT, 
                        Estado TEXT DEFAULT 'Activo', Fecha_Baja TEXT, 
                        Ajuste_ROU REAL DEFAULT 0.0, Tipo_Pago TEXT DEFAULT 'Vencido',
                        Fecha_Remedicion TEXT)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS remediciones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        Codigo_Interno TEXT, Fecha_Remedicion TEXT,
                        Canon REAL, Tasa REAL, Tasa_Mensual REAL,
                        Fin TEXT, Plazo INTEGER, Ajuste_ROU REAL,
                        FOREIGN KEY(Codigo_Interno) REFERENCES contratos(Codigo_Interno))''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS config_params (
                        tipo TEXT, valor TEXT, PRIMARY KEY(tipo, valor))''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        usuario TEXT PRIMARY KEY, password_hash TEXT, rol TEXT DEFAULT 'Lector')''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS credenciales_erp (
                        erp_nombre TEXT PRIMARY KEY, esta_activo BOOLEAN, secretos_json TEXT)''')
    
    # Migraciones para agregar componentes del ROU y Remedición
    nuevas_columnas = {
        'Ajuste_ROU': 'REAL DEFAULT 0.0',
        'Costos_Directos': 'REAL DEFAULT 0.0',
        'Pagos_Anticipados': 'REAL DEFAULT 0.0',
        'Costos_Desmantelamiento': 'REAL DEFAULT 0.0',
        'Incentivos': 'REAL DEFAULT 0.0',
        'Fecha_Remedicion': 'TEXT',
        'Frecuencia_Pago': "TEXT DEFAULT 'Mensual'"
    }
    for col, tipo in nuevas_columnas.items():
        try:
            cursor.execute(f"ALTER TABLE contratos ADD COLUMN {col} {tipo}")
        except sqlite3.OperationalError:
            pass # La columna ya existe
            
    nuevas_columnas_rem = {
        'Baja_Pasivo': 'REAL DEFAULT 0.0',
        'Baja_ROU': 'REAL DEFAULT 0.0',
        'P_L_Efecto': 'REAL DEFAULT 0.0'
    }
    for col, tipo in nuevas_columnas_rem.items():
        try:
            cursor.execute(f"ALTER TABLE remediciones ADD COLUMN {col} {tipo}")
        except sqlite3.OperationalError:
            pass
            
    # Migración de Seguridad RBAC
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT DEFAULT 'Administrador'")
    except sqlite3.OperationalError:
        pass

    # Insertar admin por defecto si no hay usuarios
    cursor.execute("SELECT count(*) as c FROM usuarios")
    if cursor.fetchone()['c'] == 0:
        h = hashlib.sha256("1234".encode()).hexdigest()
        cursor.execute("INSERT INTO usuarios (usuario, password_hash, rol) VALUES ('admin', ?, 'Administrador')", (h,))
        
    # Inyectar Monedas Base si la tabla config_params las carece
    try:
        cursor.execute("SELECT count(*) as c FROM config_params WHERE tipo='MONEDA'")
        if cursor.fetchone()['c'] == 0:
            cursor.executemany("INSERT OR IGNORE INTO config_params VALUES (?,?)", [
                ('MONEDA', 'UF'), ('MONEDA', 'CLP'), ('MONEDA', 'USD'), ('MONEDA', 'EUR')
            ])
            
        cursor.execute("SELECT count(*) as c FROM config_params WHERE tipo='FRECUENCIA_PAGO'")
        if cursor.fetchone()['c'] == 0:
            cursor.executemany("INSERT OR IGNORE INTO config_params VALUES (?,?)", [
                ('FRECUENCIA_PAGO', 'Mensual|1'), ('FRECUENCIA_PAGO', 'Bimestral|2'), 
                ('FRECUENCIA_PAGO', 'Trimestral|3'), ('FRECUENCIA_PAGO', 'Semestral|6'), 
                ('FRECUENCIA_PAGO', 'Anual|12')
            ])
    except Exception:
        pass

    # Parámetros por defecto
    cursor.execute("SELECT count(*) as c FROM config_params")
    if cursor.fetchone()['c'] == 0:
        defaults = [('EMPRESA', 'Holdco'), ('EMPRESA', 'Pacifico'),
                    ('CLASE_ACTIVO', 'Oficinas'), ('CLASE_ACTIVO', 'Vehículos'),
                    ('CLASE_ACTIVO', 'Maquinaria'), ('CLASE_ACTIVO', 'Bodegas'),
                    ('CLASE_ACTIVO', 'Inmuebles'),
                    ('CUENTA_ROU_NUM', '1401'), ('CUENTA_ROU_NOM', 'Activo Derecho de Uso ROU'),
                    ('CUENTA_PASIVO_NUM', '2101'), ('CUENTA_PASIVO_NOM', 'Pasivo por Arrendamiento IFRS 16'),
                    ('CUENTA_BCO_AJUSTE_NUM', '1101'), ('CUENTA_BCO_AJUSTE_NOM', 'Banco / Provisiones Ajuste Inicial'),
                    ('CUENTA_GASTO_AMORT_NUM', '4101'), ('CUENTA_GASTO_AMORT_NOM', 'Gasto Amortización ROU'),
                    ('CUENTA_AMORT_ACUM_NUM', '1402'), ('CUENTA_AMORT_ACUM_NOM', 'Amortización Acumulada ROU'),
                    ('CUENTA_GASTO_INT_NUM', '4201'), ('CUENTA_GASTO_INT_NOM', 'Gasto Financiero Interés'),
                    ('CUENTA_BANCO_PAGO_NUM', '1102'), ('CUENTA_BANCO_PAGO_NOM', 'Banco / Efectivo'),
                    ('CUENTA_PERDIDA_TC_NUM', '4301'), ('CUENTA_PERDIDA_TC_NOM', 'Pérdida por Dif. Cambio'),
                    ('CUENTA_GANANCIA_TC_NUM', '4302'), ('CUENTA_GANANCIA_TC_NOM', 'Ganancia por Dif. Cambio')]
        cursor.executemany("INSERT INTO config_params VALUES (?,?)", defaults)
        
    conn.commit()
    conn.close()

import os
import hashlib

def verificar_credenciales(u, p):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, rol FROM usuarios WHERE usuario=?", (u,))
    row = cursor.fetchone()
    conn.close()
    if row:
        if hashlib.sha256(p.encode()).hexdigest() == row['password_hash']:
            # Retorna el rol o Administrador por defecto si viene nulo
            return row['rol'] if 'rol' in row.keys() and row['rol'] else 'Administrador'
    return False

def agregar_usuario(u, p, rol='Lector'):
    conn = conectar()
    h = hashlib.sha256(p.encode()).hexdigest()
    conn.execute("INSERT OR REPLACE INTO usuarios (usuario, password_hash, rol) VALUES (?,?,?)", (u, h, rol))
    conn.commit()
    conn.close()

def obtener_usuarios():
    conn = conectar()
    df = pd.read_sql("SELECT usuario, rol FROM usuarios", conn)
    conn.close()
    return df.to_dict('records')

def obtener_parametros(tipo):
    conn = conectar()
    df = pd.read_sql(f"SELECT valor FROM config_params WHERE tipo='{tipo}'", conn)
    conn.close()
    return [v for v in df['valor'].tolist() if v and str(v).strip()]

import json

def guardar_credencial_erp(erp_nombre, esta_activo, secretos_dict):
    conn = conectar()
    c = conn.cursor()
    if esta_activo:
        c.execute("UPDATE credenciales_erp SET esta_activo=0")
    
    secretos_json = json.dumps(secretos_dict)
    c.execute("INSERT OR REPLACE INTO credenciales_erp (erp_nombre, esta_activo, secretos_json) VALUES (?, ?, ?)",
              (erp_nombre, 1 if esta_activo else 0, secretos_json))
    conn.commit()
    conn.close()

def leer_credencial_erp(erp_nombre):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM credenciales_erp WHERE erp_nombre=?", (erp_nombre,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'activo': bool(row['esta_activo']), 'secretos': json.loads(row['secretos_json'])}
    return {'activo': False, 'secretos': {}}

def obtener_erp_activo():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT erp_nombre FROM credenciales_erp WHERE esta_activo=1")
    row = c.fetchone()
    conn.close()
    return row['erp_nombre'] if row else None

def agregar_parametro(tipo, valor):
    conn = conectar()
    conn.execute("INSERT OR IGNORE INTO config_params VALUES (?,?)", (tipo, valor))
    conn.commit()
    conn.close()

def eliminar_parametro(tipo, valor):
    conn = conectar()
    
    # Validaciones críticas de integridad
    if tipo == 'MONEDA':
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM contratos WHERE Moneda=?", (valor,))
        if c.fetchone()['cnt'] > 0:
            conn.close()
            return False # Prohibido: Moneda en uso (histórico o vigente)
            
    if tipo == 'CAMPO_EXTRA':
        c = conn.cursor()
        try:
            c.execute(f"SELECT COUNT(*) as cnt FROM contratos WHERE \"{valor}\" IS NOT NULL AND TRIM(\"{valor}\") != ''")
            if c.fetchone()['cnt'] > 0:
                conn.close()
                return False # Prohibido: Contiene datos
        except sqlite3.OperationalError:
            pass
            
    conn.execute("DELETE FROM config_params WHERE tipo=? AND valor=?", (tipo, valor))
    conn.commit()
    conn.close()
    return True

def invocar_columna_extra(nombre):
    conn = conectar()
    try:
         conn.execute(f'ALTER TABLE contratos ADD COLUMN "{nombre}" TEXT')
    except sqlite3.OperationalError:
         pass # La columna ya existe
         
    conn.execute("INSERT OR IGNORE INTO config_params VALUES (?,?)", ('CAMPO_EXTRA', nombre))
    conn.commit()
    conn.close()

def cargar_monedas():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM monedas ORDER BY fecha DESC", conn)
    conn.close()
    return df

def insertar_moneda(f, m, v):
    conn = conectar()
    conn.execute("INSERT OR REPLACE INTO monedas VALUES (?,?,?)", (f, m, v))
    conn.commit()
    conn.close()

def cargar_masivo_monedas(df):
    conn = conectar()
    cursor = conn.cursor()
    df.columns = [c.lower().strip() for c in df.columns]
    for _, fila in df.iterrows():
        fecha_str = pd.to_datetime(fila['fecha']).strftime('%Y-%m-%d')
        cursor.execute('''INSERT OR REPLACE INTO monedas (fecha, moneda, valor) 
                          VALUES (?, ?, ?)''', (fecha_str, str(fila['moneda']), float(fila['valor'])))
    conn.commit()
    conn.close()

def cargar_contratos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contratos")
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        # Ocultar columnas legadas que el usuario no utiliza
        d.pop('Cod1', None)
        d.pop('Cod2', None)
        rows.append(d)
    conn.close()
    return rows

def insertar_contrato(c):
    conn = conectar()
    
    # Asegurar llaves numéricas por defecto
    for campo in ['Costos_Directos', 'Pagos_Anticipados', 'Costos_Desmantelamiento', 'Incentivos', 'Ajuste_ROU']:
        if campo not in c: c[campo] = 0.0
        
    # Obtener campos extra configurables para asegurar que existan en el dict
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM config_params WHERE tipo='CAMPO_EXTRA'")
    campos_extra = [dict(row)['valor'] for row in cursor.fetchall()]
    for ex in campos_extra:
        if ex not in c:
            c[ex] = None
            
    columnas = list(c.keys())
    # Escapar nombres de columnas con comillas dobles para SQLite
    cols_sql = ", ".join([f'"{col}"' for col in columnas])
    vals_sql = ", ".join(["?"] * len(columnas))
    
    query = f"INSERT INTO contratos ({cols_sql}) VALUES ({vals_sql})"
    valores = tuple(c[col] for col in columnas)
    conn.execute(query, valores)
    
    conn.commit()
    conn.close()

def dar_baja_contrato(cod, fecha):
    conn = conectar()
    conn.execute("UPDATE contratos SET Estado='Baja', Fecha_Baja=? WHERE Codigo_Interno=?", (fecha, cod))
    conn.commit()
    conn.close()

def marcar_contrato_remedido(cod, fecha):
    conn = conectar()
    conn.execute("UPDATE contratos SET Estado='Remedido', Fecha_Baja=? WHERE Codigo_Interno=?", (fecha, cod))
    conn.commit()
    conn.close()

def actualizar_contrato_remedicion(cod, can, tas, t_m, fin, p, f_rem):
    conn = conectar()
    conn.execute("UPDATE contratos SET Canon=?, Tasa=?, Tasa_Mensual=?, Fin=?, Plazo=?, Fecha_Remedicion=? WHERE Codigo_Interno=?", 
                 (can, tas, t_m, fin, p, f_rem, cod))
    conn.commit()
    conn.close()

def insertar_remedicion(cod, f_rem, can, tas, t_m, fin, p, aj_rou, b_pas=0.0, b_rou=0.0, pl_efec=0.0):
    conn = conectar()
    conn.execute("INSERT INTO remediciones (Codigo_Interno, Fecha_Remedicion, Canon, Tasa, Tasa_Mensual, Fin, Plazo, Ajuste_ROU, Baja_Pasivo, Baja_ROU, P_L_Efecto) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                 (cod, f_rem, can, tas, t_m, fin, p, aj_rou, b_pas, b_rou, pl_efec))
    conn.commit()
    conn.close()

def cargar_remediciones(cod=None):
    conn = conectar()
    if cod:
        df = pd.read_sql(f"SELECT * FROM remediciones WHERE Codigo_Interno='{cod}' ORDER BY Fecha_Remedicion ASC", conn)
    else:
        df = pd.read_sql("SELECT * FROM remediciones ORDER BY Codigo_Interno, Fecha_Remedicion ASC", conn)
    conn.close()
    return [dict(r) for _, r in df.iterrows()]

def cargar_remediciones_todas_agrupadas():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM remediciones ORDER BY Codigo_Interno, Fecha_Remedicion ASC", conn)
    conn.close()
    grouped = {}
    for _, r in df.iterrows():
        d = dict(r)
        cod = d['Codigo_Interno']
        if cod not in grouped: grouped[cod] = []
        grouped[cod].append(d)
    return grouped

def limpiar_monedas():
    conn = conectar()
    conn.execute("DELETE FROM monedas")
    conn.commit()
    conn.close()

def limpiar_contratos():
    conn = conectar()
    conn.execute("DELETE FROM contratos")
    conn.execute("DELETE FROM remediciones")
    conn.commit()
    conn.close()

inicializar_db()