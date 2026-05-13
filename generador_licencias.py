from licencia_utils import generate_license
from datetime import datetime

def main():
    print("===========================================")
    print("  🔑 GENERADOR DE LICENCIAS IFRS 16 PRO 🔑")
    print("===========================================")
    print("ADVERTENCIA: Este archivo es privado. NO lo incluya en el Docker del cliente.\n")
    
    cliente = input("1. Ingrese el nombre del Cliente / Empresa: ")
    
    while True:
        fecha_str = input("2. Ingrese la fecha de expiración (YYYY-MM-DD), ej. 2027-12-31: ")
        try:
            # Validar que el formato de fecha sea correcto
            datetime.strptime(fecha_str, '%Y-%m-%d')
            break
        except ValueError:
            print("Formato incorrecto. Por favor use el formato YYYY-MM-DD.")
            
    codigo_licencia = generate_license(cliente, fecha_str)
    
    print("\n-------------------------------------------")
    print("✅ LICENCIA GENERADA EXITOSAMENTE")
    print("-------------------------------------------")
    print(f"Cliente:    {cliente}")
    print(f"Expira el:  {fecha_str}")
    print("\nCÓDIGO DE LICENCIA PARA EL CLIENTE:")
    print(codigo_licencia)
    print("\n(Copia y envía este código al cliente para que active el software).")
    print("===========================================\n")
    
    input("Presione Enter para salir...")

if __name__ == "__main__":
    main()
