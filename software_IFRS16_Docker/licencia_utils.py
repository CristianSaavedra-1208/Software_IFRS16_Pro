import hmac
import hashlib
import base64
import json
from datetime import datetime

# ¡Esta clave NUNCA debe salir del código fuente ofuscado ni ser compartida!
SECRET_KEY = b"IFRS16_PLATINUM_PRO_2026_MASTER_SECRET_X9!"

def generate_license(client_name: str, expiration_date_str: str) -> str:
    """Genera una licencia encriptada (Solo para uso del administrador)."""
    payload = {
        "client": client_name,
        "exp": expiration_date_str
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).digest()
    
    # Encode them separately and join with a dot
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('=')
    signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"IFRS16-{payload_b64}.{signature_b64}"

def verify_license(license_key: str):
    """Verifica si la licencia es válida y no ha expirado."""
    try:
        if not license_key or not license_key.startswith("IFRS16-"):
            return False, "Formato de licencia inválido."
            
        token = license_key[7:]
        
        if '.' not in token:
            return False, "Formato de token inválido."
            
        payload_b64, signature_b64 = token.split('.', 1)
        
        # Add padding back
        pad_len1 = 4 - (len(payload_b64) % 4)
        if pad_len1 != 4: payload_b64 += "=" * pad_len1
        
        pad_len2 = 4 - (len(signature_b64) % 4)
        if pad_len2 != 4: signature_b64 += "=" * pad_len2
            
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        signature = base64.urlsafe_b64decode(signature_b64)
        
        expected_signature = hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_signature, signature):
            return False, "Licencia alterada o firma inválida."
            
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        exp_date = datetime.strptime(payload['exp'], '%Y-%m-%d')
        # Comparar fechas (solo la parte de la fecha, ignorar horas)
        if datetime.now().date() > exp_date.date():
            return False, f"La licencia expiró el {payload['exp']}. Contacte a soporte."
            
        return True, payload
    except Exception as e:
        return False, "Error al decodificar la licencia."
