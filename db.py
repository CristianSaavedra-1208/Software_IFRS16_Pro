import sqlite3
import pandas as pd
import streamlit as st

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
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS bitacora_auditoria (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha_hora TEXT,
                        usuario TEXT,
                        accion TEXT,
                        entidad_id TEXT,
                        detalles TEXT)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS periodos_contables (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        empresa TEXT DEFAULT 'Todas',
                        anio INTEGER,
                        mes INTEGER,
                        fecha_cierre TEXT,
                        estado TEXT DEFAULT 'Cerrado',
                        cerrado_por TEXT,
                        fecha_accion TEXT,
                        motivo TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS saldos_cierre_periodo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        periodo_cierre TEXT,
                        codigo_interno TEXT,
                        empresa TEXT,
                        pasivo_clp REAL,
                        rou_bruto_clp REAL,
                        amort_acum_clp REAL,
                        saldo_pasivo_moneda REAL,
                        moneda TEXT,
                        tc_cierre REAL)''')
                        
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_saldos_cierre_lookup 
                      ON saldos_cierre_periodo (codigo_interno, periodo_cierre DESC)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_periodos_contables_lookup 
                      ON periodos_contables (estado, fecha_cierre DESC)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS storage_reportes_periodo (
                        periodo_cierre TEXT,
                        anio INTEGER,
                        mes INTEGER,
                        empresa TEXT,
                        modulo TEXT,
                        payload_json TEXT,
                        fecha_guardado TEXT,
                        PRIMARY KEY (periodo_cierre, empresa, modulo))''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_storage_reportes_lookup 
                      ON storage_reportes_periodo (anio, mes, empresa, modulo)''')
    
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
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN clave_visible TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    # Sincronizar claves visibles conocidas si están vacías
    cursor.execute(
        "UPDATE usuarios SET clave_visible='Mundo16' WHERE (clave_visible IS NULL OR clave_visible='') AND password_hash='d0a77ca08a2b817665d66f07a5bf28a339e99a0ed8c2a4d309b57acfa8d7b59c'"
    )
    cursor.execute(
        "UPDATE usuarios SET clave_visible='1234' WHERE (clave_visible IS NULL OR clave_visible='') AND password_hash='03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4'"
    )

    # Insertar admin por defecto si no hay usuarios
    cursor.execute("SELECT count(*) as c FROM usuarios")
    if cursor.fetchone()['c'] == 0:
        h = hashlib.sha256("1234".encode()).hexdigest()
        cursor.execute("INSERT INTO usuarios (usuario, password_hash, rol, clave_visible) VALUES ('admin', ?, 'Administrador', '1234')", (h,))
        
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
                    ('CUENTA_BCO_AJUSTE_NUM', '1101'), ('CUENTA_BCO_AJUSTE_NOM', 'Ajustes'),
                    ('CUENTA_GASTO_AMORT_NUM', '4101'), ('CUENTA_GASTO_AMORT_NOM', 'Gasto Amortización ROU'),
                    ('CUENTA_AMORT_ACUM_NUM', '1402'), ('CUENTA_AMORT_ACUM_NOM', 'Amortización Acumulada ROU'),
                    ('CUENTA_GASTO_INT_NUM', '4201'), ('CUENTA_GASTO_INT_NOM', 'Gasto Financiero Interés'),
                    ('CUENTA_BANCO_PAGO_NUM', '1102'), ('CUENTA_BANCO_PAGO_NOM', 'Banco / Efectivo'),
                    ('CUENTA_PERDIDA_TC_NUM', '4301'), ('CUENTA_PERDIDA_TC_NOM', 'Pérdida por Dif. Cambio'),
                    ('CUENTA_GANANCIA_TC_NUM', '4302'), ('CUENTA_GANANCIA_TC_NOM', 'Ganancia por Dif. Cambio')]
        cursor.executemany("INSERT INTO config_params VALUES (?,?)", defaults)
        
    # --- Índices para mejorar rendimiento ---
    # Contratos
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contratos_moneda ON contratos(Moneda)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contratos_estado ON contratos(Estado)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contratos_empresa ON contratos(Empresa)")
    # Remediciones
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_remediciones_codigo ON remediciones(Codigo_Interno)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_remediciones_fecha ON remediciones(Fecha_Remedicion)")
    # Monedas
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_monedas_fecha ON monedas(fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_monedas_moneda ON monedas(moneda)")

    conn.commit()
    conn.close()

import os
import hashlib

def verificar_credenciales(u, p):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, rol, clave_visible FROM usuarios WHERE usuario=?", (u,))
    row = cursor.fetchone()
    if row:
        if hashlib.sha256(p.encode()).hexdigest() == row['password_hash']:
            if not row['clave_visible']:
                cursor.execute("UPDATE usuarios SET clave_visible=? WHERE usuario=?", (p, u))
                conn.commit()
            conn.close()
            # Retorna el rol o Administrador por defecto si viene nulo
            return row['rol'] if 'rol' in row.keys() and row['rol'] else 'Administrador'
    conn.close()
    return False

def agregar_usuario(u, p, rol='Lector'):
    conn = conectar()
    h = hashlib.sha256(p.encode()).hexdigest()
    conn.execute("INSERT OR REPLACE INTO usuarios (usuario, password_hash, rol, clave_visible) VALUES (?,?,?,?)", (u, h, rol, p))
    conn.commit()
    conn.close()

def obtener_usuarios(incluir_claves=False):
    conn = conectar()
    if incluir_claves:
        df = pd.read_sql("SELECT usuario, rol, clave_visible FROM usuarios", conn)
    else:
        df = pd.read_sql("SELECT usuario, rol FROM usuarios", conn)
    conn.close()
    return df.to_dict('records')

@st.cache_data
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
    st.cache_data.clear()  # Invalida caché de obtener_parametros

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
    st.cache_data.clear()  # Invalida caché de obtener_parametros
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
    st.cache_data.clear()  # Invalida caché de obtener_parametros

def cargar_monedas():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM monedas ORDER BY fecha DESC", conn)
    conn.close()
    return df

def obtener_tc_spot(moneda, fecha_str):
    """Lookup optimizado de tipo de cambio via SQL directo.
    Retorna el valor mas reciente de 'moneda' en o antes de 'fecha_str' (formato YYYY-MM-DD).
    Logica identica a: df[(df['moneda']==moneda) & (df['fecha']<=fecha_str)].iloc[0]['valor']
    pero sin cargar toda la tabla en memoria.
    """
    if moneda == "CLP":
        return 1.0
    conn = conectar()
    c = conn.cursor()
    c.execute(
        "SELECT valor FROM monedas WHERE moneda = ? AND fecha <= ? ORDER BY fecha DESC LIMIT 1",
        (moneda, fecha_str)
    )
    row = c.fetchone()
    conn.close()
    return float(row['valor']) if row else 0.0

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

def insertar_contrato(c, usuario_act="Sistema/Usuario"):
    conn = conectar()
    try:
        # Asegurar llaves numéricas por defecto
        for campo in ['Costos_Directos', 'Pagos_Anticipados', 'Costos_Desmantelamiento', 'Incentivos', 'Ajuste_ROU']:
            if campo not in c: c[campo] = 0.0
            
        # Obtener columnas reales existentes en la tabla contratos
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(contratos)")
        cols_existentes = {row['name'] for row in cursor.fetchall()}
        
        # Filtrar solo columnas que realmente existen en la tabla contratos
        c_filtrado = {k: v for k, v in c.items() if k in cols_existentes}
        
        columnas = list(c_filtrado.keys())
        # Escapar nombres de columnas con comillas dobles para SQLite
        cols_sql = ", ".join([f'"{col}"' for col in columnas])
        vals_sql = ", ".join(["?"] * len(columnas))
        
        query = f"INSERT INTO contratos ({cols_sql}) VALUES ({vals_sql})"
        valores = tuple(c_filtrado[col] for col in columnas)
        conn.execute(query, valores)
        
        conn.commit()
        
        # Audit Log
        registrar_log(usuario_act, "CREAR_CONTRATO", c['Codigo_Interno'], f"Inicio: {c.get('Inicio')}, Clase: {c.get('Clase_Activo')}, Frecuencia: {c.get('Frecuencia_Pago', 'Mensual')}")
    finally:
        conn.close()

def dar_baja_contrato(cod, fecha, usuario_act="Sistema/Usuario"):
    conn = conectar()
    conn.execute("UPDATE contratos SET Estado='Baja', Fecha_Baja=? WHERE Codigo_Interno=?", (fecha, cod))
    conn.commit()
    conn.close()
    registrar_log(usuario_act, "BAJA_CONTRATO", cod, f"Dado de baja el {fecha}")

def marcar_contrato_remedido(cod, fecha, usuario_act="Sistema/Usuario"):
    conn = conectar()
    conn.execute("UPDATE contratos SET Estado='Remedido', Fecha_Baja=? WHERE Codigo_Interno=?", (fecha, cod))
    conn.commit()
    conn.close()
    registrar_log(usuario_act, "MARCAR_REMEDIDO", cod, f"Marcado Histórico por nueva Remedición el {fecha}")

def actualizar_contrato_remedicion(cod, can, tas, t_m, fin, p, f_rem):
    conn = conectar()
    conn.execute("UPDATE contratos SET Canon=?, Tasa=?, Tasa_Mensual=?, Fin=?, Plazo=?, Fecha_Remedicion=? WHERE Codigo_Interno=?", 
                 (can, tas, t_m, fin, p, f_rem, cod))
    conn.commit()
    conn.close()

def insertar_remedicion(cod, f_rem, can, tas, t_m, fin, p, aj_rou, b_pas=0.0, b_rou=0.0, pl_efec=0.0, usuario_act="Sistema/Usuario"):
    conn = conectar()
    conn.execute("INSERT INTO remediciones (Codigo_Interno, Fecha_Remedicion, Canon, Tasa, Tasa_Mensual, Fin, Plazo, Ajuste_ROU, Baja_Pasivo, Baja_ROU, P_L_Efecto) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                 (cod, f_rem, can, tas, t_m, fin, p, aj_rou, b_pas, b_rou, pl_efec))
    conn.commit()
    conn.close()
    registrar_log(usuario_act, "CREAR_REMEDICION", cod, f"Nueva Remedición desde {f_rem}. P/L Efectivo: {pl_efec}")

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

def is_audit_enabled():
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("SELECT valor FROM config_params WHERE tipo='AUDIT_LOG_ENABLED'")
        row = c.fetchone()
        conn.close()
        return bool(row) and row['valor'] == '1'
    except:
        conn.close()
        return False

def registrar_log(usuario, accion, entidad_id, detalles=""):
    if not is_audit_enabled():
        return
    import datetime
    import os
    import pandas as pd
    
    conn = conectar()
    fh = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO bitacora_auditoria (fecha_hora, usuario, accion, entidad_id, detalles) VALUES (?, ?, ?, ?, ?)",
                 (fh, usuario, accion, str(entidad_id), str(detalles)))
                 
    # Rotación Automática
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM bitacora_auditoria")
    if c.fetchone()['cnt'] >= 5000:
        try:
            df = pd.read_sql("SELECT * FROM bitacora_auditoria ORDER BY id ASC", conn)
            dir_logs = os.path.join("data", "logs_historicos")
            if not os.path.exists(dir_logs):
                os.makedirs(dir_logs)
                
            fh_clean = fh.replace(":", "").replace(" ", "_").replace("-", "")
            file_name = f"Historial_Logs_{fh_clean}.xlsx"
            file_path = os.path.join(dir_logs, file_name)
            
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as wr:
                df.to_excel(wr, index=False)
                
            conn.execute("DELETE FROM bitacora_auditoria")
            fh_post = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO bitacora_auditoria (fecha_hora, usuario, accion, entidad_id, detalles) VALUES (?, ?, ?, ?, ?)",
                         (fh_post, "Sistema", "ROTACION_LOGS", "Base de Datos", f"Rotación automática exitosa. Logs guardados en {file_name}"))
        except Exception:
            pass
            
    conn.commit()
    conn.close()

def obtener_logs():
    conn = conectar()
    try:
        df = pd.read_sql("SELECT * FROM bitacora_auditoria ORDER BY id DESC LIMIT 1000", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# --- GESTIÓN DE PERIODOS CONTABLES Y CANDADOS DE SEGURIDAD ---

def obtener_periodos_contables(empresa=None):
    conn = conectar()
    try:
        if empresa and empresa != "Todas":
            df = pd.read_sql("SELECT * FROM periodos_contables WHERE empresa='Todas' OR empresa=? ORDER BY fecha_cierre DESC, id DESC", conn, params=(empresa,))
        else:
            df = pd.read_sql("SELECT * FROM periodos_contables ORDER BY fecha_cierre DESC, id DESC", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def obtener_ultimo_periodo_cerrado(empresa="Todas"):
    conn = conectar()
    cursor = conn.cursor()
    try:
        if empresa and empresa != "Todas":
            cursor.execute("SELECT fecha_cierre FROM periodos_contables WHERE estado='Cerrado' AND (empresa='Todas' OR empresa=?) ORDER BY fecha_cierre DESC LIMIT 1", (empresa,))
        else:
            cursor.execute("SELECT fecha_cierre FROM periodos_contables WHERE estado='Cerrado' ORDER BY fecha_cierre DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row['fecha_cierre'] if row else None
    except Exception:
        conn.close()
        return None

def es_periodo_cerrado(fecha_evaluar, empresa="Todas"):
    if not fecha_evaluar:
        return False
    try:
        f_s = pd.to_datetime(fecha_evaluar).strftime('%Y-%m-%d')
        f_limite = obtener_ultimo_periodo_cerrado(empresa)
        if f_limite and f_s <= f_limite:
            return True
        return False
    except Exception:
        return False

def obtener_info_cierre_mes(anio, mes, empresa="Todas"):
    from datetime import date
    from dateutil.relativedelta import relativedelta
    conn = conectar()
    cursor = conn.cursor()
    try:
        anio = int(anio)
        mes = int(mes)
        f_cierre_str = (pd.to_datetime(date(anio, mes, 1)) + relativedelta(day=31)).strftime('%Y-%m-%d')
        if empresa and empresa != "Todas":
            cursor.execute(
                "SELECT * FROM periodos_contables WHERE estado='Cerrado' AND anio=? AND mes=? AND (empresa='Todas' OR empresa=?) ORDER BY id DESC LIMIT 1",
                (anio, mes, empresa)
            )
        else:
            cursor.execute(
                "SELECT * FROM periodos_contables WHERE estado='Cerrado' AND anio=? AND mes=? ORDER BY id DESC LIMIT 1",
                (anio, mes)
            )
        row = cursor.fetchone()
        if row:
            res = dict(row)
            conn.close()
            return res
        # Fallback: si existe un período posterior cerrado que cubre esta fecha
        if empresa and empresa != "Todas":
            cursor.execute(
                "SELECT * FROM periodos_contables WHERE estado='Cerrado' AND fecha_cierre>=? AND (empresa='Todas' OR empresa=?) ORDER BY fecha_cierre DESC LIMIT 1",
                (f_cierre_str, empresa)
            )
        else:
            cursor.execute(
                "SELECT * FROM periodos_contables WHERE estado='Cerrado' AND fecha_cierre>=? ORDER BY fecha_cierre DESC LIMIT 1",
                (f_cierre_str,)
            )
        row2 = cursor.fetchone()
        conn.close()
        return dict(row2) if row2 else None
    except Exception:
        conn.close()
        return None

def es_mes_cerrado(anio, mes, empresa="Todas"):
    return obtener_info_cierre_mes(anio, mes, empresa) is not None

def guardar_reporte_storage(anio, mes, empresa, modulo, payload_obj):
    import zlib
    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta
    anio = int(anio)
    mes = int(mes)
    f_cierre_str = (pd.to_datetime(date(anio, mes, 1)) + relativedelta(day=31)).strftime('%Y-%m-%d')
    fh_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload_str = json.dumps(payload_obj, default=str, ensure_ascii=False)
    payload_compressed = sqlite3.Binary(zlib.compress(payload_str.encode('utf-8'), level=9))
    conn = conectar()
    conn.execute(
        """INSERT OR REPLACE INTO storage_reportes_periodo
           (periodo_cierre, anio, mes, empresa, modulo, payload_json, fecha_guardado)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (f_cierre_str, anio, mes, empresa, modulo, payload_compressed, fh_now)
    )
    conn.commit()
    conn.close()

def _decodificar_payload_storage(raw_val):
    import zlib
    if raw_val is None:
        return None
    if isinstance(raw_val, (bytes, bytearray, memoryview)):
        return json.loads(zlib.decompress(bytes(raw_val)).decode('utf-8'))
    return json.loads(raw_val)

def obtener_reporte_storage(anio, mes, empresa, modulo):
    from datetime import date
    from dateutil.relativedelta import relativedelta
    anio = int(anio)
    mes = int(mes)
    f_cierre_str = (pd.to_datetime(date(anio, mes, 1)) + relativedelta(day=31)).strftime('%Y-%m-%d')
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT payload_json, fecha_guardado FROM storage_reportes_periodo WHERE periodo_cierre=? AND empresa=? AND modulo=?",
            (f_cierre_str, empresa, modulo)
        )
        row = cursor.fetchone()
        if row and row['payload_json'] is not None:
            conn.close()
            return _decodificar_payload_storage(row['payload_json'])
        # Fallback instantáneo: si se consulta una empresa específica y está guardado el consolidado 'Todas'
        if empresa and empresa != "Todas" and modulo != "ASIENTOS":
            cursor.execute(
                "SELECT payload_json FROM storage_reportes_periodo WHERE periodo_cierre=? AND empresa='Todas' AND modulo=?",
                (f_cierre_str, modulo)
            )
            row_all = cursor.fetchone()
            conn.close()
            if row_all and row_all['payload_json'] is not None:
                data_all = _decodificar_payload_storage(row_all['payload_json'])
                if modulo == "NOTAS_MOVIMIENTO" and isinstance(data_all, dict):
                    return {
                        "roll_pasivo": [r for r in data_all.get("roll_pasivo", []) if r.get("Empresa") == empresa],
                        "roll_activo": [r for r in data_all.get("roll_activo", []) if r.get("Empresa") == empresa]
                    }
                elif isinstance(data_all, list):
                    return [r for r in data_all if r.get("Empresa") == empresa]
            return None
        conn.close()
        return None
    except Exception:
        conn.close()
        return None

def generar_snapshots_cierre(anio, mes, empresa="Todas"):
    from datetime import date
    from dateutil.relativedelta import relativedelta
    import core
    
    f_cierre_dt = pd.to_datetime(date(int(anio), int(mes), 1)) + relativedelta(day=31)
    f_cierre_str = f_cierre_dt.strftime('%Y-%m-%d')
    
    contratos = cargar_contratos()
    if empresa and empresa != "Todas":
        contratos = [c for c in contratos if c.get('Empresa') == empresa]
        
    rems_grupos = cargar_remediciones_todas_agrupadas()
    
    snapshots = []
    for c in contratos:
        cid = c['Codigo_Interno']
        f_ini = pd.to_datetime(c['Inicio'])
        if f_ini > f_cierre_dt:
            continue
            
        rems_all = rems_grupos.get(cid, [])
        rems = [r for r in rems_all if pd.to_datetime(r['Fecha_Remedicion']) <= f_cierre_dt]
        try:
            tab, vp, rou = core.motor_financiero_v21(c, rems)
        except Exception:
            tab, vp, rou = core.motor_financiero_v21(c)
            
        tc_ini = float(c.get('Valor_Moneda_Inicio') or 1.0)
        if tc_ini <= 0: tc_ini = 1.0
        
        # Calcular saldo exacto al corte
        rb, aa, pasivo = core.simular_libro_mayor(c, tab, f_cierre_dt, rems, tc_ini, vp, rou, usar_snapshot=True)
        
        past_tab = tab[tab['Fecha'] <= f_cierre_dt] if (tab is not None and not tab.empty and 'Fecha' in tab.columns) else pd.DataFrame()
        s_fin_orig = past_tab.iloc[-1]['S_Fin_Orig'] if not past_tab.empty else 0.0
        
        moneda = c.get('Moneda', 'CLP')
        tc_cierre = core.obtener_tc_cache(moneda, f_cierre_dt)
        
        snapshots.append((
            f_cierre_str, cid, c.get('Empresa', 'Todas'),
            float(pasivo), float(rb), float(aa),
            float(s_fin_orig), moneda, float(tc_cierre)
        ))
        
    conn = conectar()
    cursor = conn.cursor()
    if empresa and empresa != "Todas":
        cursor.execute("DELETE FROM saldos_cierre_periodo WHERE periodo_cierre=? AND empresa=?", (f_cierre_str, empresa))
    else:
        cursor.execute("DELETE FROM saldos_cierre_periodo WHERE periodo_cierre=?", (f_cierre_str,))
        
    cursor.executemany(
        """INSERT INTO saldos_cierre_periodo 
           (periodo_cierre, codigo_interno, empresa, pasivo_clp, rou_bruto_clp, amort_acum_clp, saldo_pasivo_moneda, moneda, tc_cierre)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        snapshots
    )
    conn.commit()
    conn.close()

def cerrar_periodo_contable(anio, mes, empresa="Todas", usuario="admin", motivo=""):
    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta
    
    try:
        anio = int(anio)
        mes = int(mes)
        f_fin_mes = pd.to_datetime(date(anio, mes, 1)) + relativedelta(day=31)
        f_cierre_str = f_fin_mes.strftime('%Y-%m-%d')
        fh_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = conectar()
        cursor = conn.cursor()
        
        # Verificar si ya existe registro cerrado para este mes/empresa
        cursor.execute("SELECT id FROM periodos_contables WHERE anio=? AND mes=? AND empresa=? AND estado='Cerrado'", (anio, mes, empresa))
        if cursor.fetchone():
            conn.close()
            return False, f"El período {mes:02d}/{anio} para la empresa '{empresa}' ya se encuentra cerrado."
            
        # Limpiar registros previos 'Abierto' del mismo mes/empresa para evitar duplicados en el historial activo
        cursor.execute("DELETE FROM periodos_contables WHERE anio=? AND mes=? AND empresa=? AND estado='Abierto'", (anio, mes, empresa))
        
        cursor.execute(
            "INSERT INTO periodos_contables (empresa, anio, mes, fecha_cierre, estado, cerrado_por, fecha_accion, motivo) VALUES (?, ?, ?, ?, 'Cerrado', ?, ?, ?)",
            (empresa, anio, mes, f_cierre_str, usuario, fh_now, motivo)
        )
        conn.commit()
        conn.close()
        
        # Generar snapshot automático de saldos de cierre para aceleración máxima
        try:
            generar_snapshots_cierre(anio, mes, empresa)
        except Exception:
            pass
            
        # Invalidate LRU caches
        try:
            import core
            if hasattr(core, 'limpiar_caches_financieros'):
                core.limpiar_caches_financieros()
        except Exception:
            pass
        
        registrar_log(usuario, "CIERRE_PERIODO", f"{anio}-{mes:02d}", f"Cierre contable empresa: {empresa}. Snapshot generado. Motivo: {motivo}")
        return True, f"Período {mes:02d}/{anio} ({f_cierre_str}) cerrado y saldos congelados en Storage exitosamente."
    except Exception as e:
        return False, f"Error al cerrar período: {str(e)}"

def reabrir_periodo_contable(anio, mes, empresa="Todas", usuario="admin", motivo=""):
    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta
    try:
        anio = int(anio)
        mes = int(mes)
        f_fin_mes = pd.to_datetime(date(anio, mes, 1)) + relativedelta(day=31)
        f_cierre_str = f_fin_mes.strftime('%Y-%m-%d')
        fh_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = conectar()
        cursor = conn.cursor()
        
        # Buscar el período solicitado y cualquier período posterior cerrado (reapertura en cascada)
        if empresa and empresa != "Todas":
            cursor.execute(
                "SELECT id, anio, mes, fecha_cierre FROM periodos_contables WHERE fecha_cierre>=? AND (empresa=? OR empresa='Todas') AND estado='Cerrado' ORDER BY fecha_cierre ASC",
                (f_cierre_str, empresa)
            )
        else:
            cursor.execute(
                "SELECT id, anio, mes, fecha_cierre FROM periodos_contables WHERE fecha_cierre>=? AND estado='Cerrado' ORDER BY fecha_cierre ASC",
                (f_cierre_str,)
            )
        rows = cursor.fetchall()
        if not rows:
            conn.close()
            return False, f"No se encontró un período cerrado en o desde {mes:02d}/{anio} ({empresa})."
            
        periodos_reabiertos = [f"{r['mes']:02d}/{r['anio']}" for r in rows]
        
        if empresa and empresa != "Todas":
            cursor.execute(
                "UPDATE periodos_contables SET estado='Abierto', fecha_accion=?, cerrado_por=?, motivo=? WHERE fecha_cierre>=? AND (empresa=? OR empresa='Todas') AND estado='Cerrado'",
                (fh_now, usuario, f"Reapertura (desde {mes:02d}/{anio}): {motivo}", f_cierre_str, empresa)
            )
            cursor.execute("DELETE FROM saldos_cierre_periodo WHERE periodo_cierre>=? AND (empresa='Todas' OR empresa=?)", (f_cierre_str, empresa))
            cursor.execute("DELETE FROM storage_reportes_periodo WHERE periodo_cierre>=? AND (empresa='Todas' OR empresa=?)", (f_cierre_str, empresa))
        else:
            cursor.execute(
                "UPDATE periodos_contables SET estado='Abierto', fecha_accion=?, cerrado_por=?, motivo=? WHERE fecha_cierre>=? AND estado='Cerrado'",
                (fh_now, usuario, f"Reapertura (desde {mes:02d}/{anio}): {motivo}", f_cierre_str)
            )
            cursor.execute("DELETE FROM saldos_cierre_periodo WHERE periodo_cierre>=?", (f_cierre_str,))
            cursor.execute("DELETE FROM storage_reportes_periodo WHERE periodo_cierre>=?", (f_cierre_str,))
            
        conn.commit()
        conn.close()
        
        try:
            import core
            if hasattr(core, 'limpiar_caches_financieros'):
                core.limpiar_caches_financieros()
        except Exception:
            pass
        
        resumen_per = ", ".join(periodos_reabiertos)
        registrar_log(usuario, "REAPERTURA_PERIODO", f"{anio}-{mes:02d}", f"Reapertura en cascada ({resumen_per}) empresa: {empresa}. Motivo: {motivo}")
        return True, f"Período(s) {resumen_per} reabierto(s) exitosamente y Storage liberado desde {f_cierre_str}."
    except Exception as e:
        return False, f"Error al reabrir período: {str(e)}"

inicializar_db()