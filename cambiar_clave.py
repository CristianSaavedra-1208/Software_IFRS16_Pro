from db import agregar_usuario

# 1. Pon aquí tu nombre de usuario (ej: admin)
usuario = "admin"

# 2. Pon aquí la nueva clave que quieres usar
nueva_clave = "TU_NUEVA_CLAVE_AQUI" 

# Ejecutamos el cambio en la base de datos conservando tu rol de Administrador
agregar_usuario(usuario, nueva_clave, rol="Administrador")

print(f"\n✅ ¡Éxito! La clave del usuario '{usuario}' ha sido actualizada en la base de datos local (ifrs16_platinum.db).")
print("👉 Ahora recuerda hacer Commit/Push en tu GitHub para que la nube reciba este cambio.")
