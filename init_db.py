import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'asociacion.db'

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

# Crear tabla si no existe
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    address TEXT,
    payment_method TEXT,
    role TEXT DEFAULT 'Socio',
    is_active INTEGER DEFAULT 0
)
''')
print("✅ Tabla 'users' creada correctamente.")

# Insertar usuario administrador si no existe
admin_username = 'mrpopo2025'
admin_password = 'mrpopo2025@'
admin_hashed = generate_password_hash(admin_password)

c.execute('SELECT * FROM users WHERE username = ?', (admin_username,))
if c.fetchone() is None:
    c.execute('''
    INSERT INTO users (name, email, username, password, address, payment_method, role, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('Administrador', 'admin@aescodb.es', admin_username, admin_hashed, '', 'Ninguno', 'Admin', 1))
    conn.commit()
    print("✅ Usuario administrador creado correctamente.")
else:
    print("ℹ️ El usuario administrador ya existe.")

conn.close()

conn.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        tipo TEXT NOT NULL,
        fecha TEXT NOT NULL,
        hora TEXT,
        lugar TEXT,
        descripcion TEXT,
        asistentes TEXT
    )
''')

import sqlite3

# Ruta de la base de datos
DATABASE = 'database.db'

# Conexión
conn = sqlite3.connect(DATABASE)
c = conn.cursor()

# Crear tabla 'concursos'
c.execute('''
    CREATE TABLE IF NOT EXISTS concursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descripcion TEXT,
        bases TEXT,
        activo INTEGER DEFAULT 1,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        num_participantes INTEGER DEFAULT 0,
        resultado TEXT
    )
''')

conn.commit()
conn.close()

print("Tabla 'concursos' creada correctamente.")
