import sqlite3

# Ruta a tu base de datos
DATABASE = 'asociacion.db'

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Crear tabla de sorteos
cursor.execute('''
CREATE TABLE IF NOT EXISTS raffles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    premio TEXT,
    fecha TEXT,
    activo INTEGER DEFAULT 1,
    ganador_id INTEGER
)
''')

# Crear tabla de participaciones
cursor.execute('''
CREATE TABLE IF NOT EXISTS participaciones_sorteos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    socio_id INTEGER NOT NULL,
    sorteo_id INTEGER NOT NULL,
    UNIQUE(socio_id, sorteo_id)
)
''')

conn.commit()
conn.close()
print("Tablas 'raffles' y 'participaciones_sorteos' creadas correctamente.")
