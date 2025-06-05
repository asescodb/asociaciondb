from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import random
import os
import csv
from flask import send_file
from io import BytesIO
from fpdf import FPDF
import qrcode
import json

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'
DATABASE = 'asociacion.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template('index.html', time=current_time)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            if user['is_active']:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                flash('Has iniciado sesión correctamente.', 'success')
                return redirect(url_for('members_area'))
            else:
                flash('Tu cuenta aún no ha sido activada por un administrador.', 'error')
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        payment_method = request.form['payment_method']
        captcha = request.form['captcha']
        correct_answer = request.form['correct_answer']
        terms = request.form.get('terms')

        if not terms:
            flash('Debes aceptar los estatutos y condiciones.', 'error')
            return redirect(url_for('register'))
        if captcha.strip() != correct_answer:
            flash('Rompecabezas incorrecto.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (name, email, username, password, address, payment_method, role, is_active)
                VALUES (?, ?, ?, ?, '', ?, 'Socio', 0)
            ''', (name, email, username, hashed_password, payment_method))
            conn.commit()
            flash('Registro enviado. Espera aprobación de un administrador.', 'success')
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash('Nombre de usuario ya en uso.', 'error')
        finally:
            conn.close()

    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    correct_answer = str(num1 + num2)
    return render_template('register.html', num1=num1, num2=num2, correct_answer=correct_answer)

@app.route('/zona-socios')
def members_area():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder a esta página.', 'error')
        return redirect(url_for('login'))
    return render_template('members_area.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        user_answer = request.form.get('captcha_answer')
        correct_answer = request.form.get('correct_answer')
        if user_answer == correct_answer:
            flash('Mensaje enviado correctamente. ¡Gracias por contactar!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Respuesta incorrecta. Intenta de nuevo.', 'error')
            return redirect(url_for('contact'))
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    correct_answer = str(num1 + num2)
    return render_template('contact.html', num1=num1, num2=num2, correct_answer=correct_answer)

@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'Admin':
        flash('Acceso denegado. No tienes permisos de administrador.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    events = conn.execute('SELECT * FROM events').fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', users=users, events=events)

@app.route('/change-role/<int:user_id>', methods=['POST'])
def change_role(user_id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    new_role = request.form['new_role']
    conn = get_db_connection()
    conn.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()
    flash('Rol actualizado correctamente.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/toggle-activation/<int:user_id>', methods=['POST'])
def toggle_activation(user_id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute('SELECT is_active FROM users WHERE id = ?', (user_id,)).fetchone()
    new_status = 0 if user['is_active'] else 1
    conn.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
    conn.commit()
    conn.close()
    flash('Estado de activación cambiado correctamente.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/export-users')
def export_users():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    output = []
    header = users[0].keys() if users else []
    output.append(header)
    for user in users:
        output.append([user[key] for key in header])
    si = []
    for row in output:
        si.append(','.join(map(str, row)))
    response = make_response('\n'.join(si))
    response.headers["Content-Disposition"] = "attachment; filename=usuarios.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/member_card')
def member_card():
    if 'user_id' not in session:
        flash("Debes iniciar sesión para ver tu carné.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    # Datos
    nombre = user["name"]
    numero = str(user["id"]).zfill(4)
    fecha_alta = user["created_at"] if "created_at" in user.keys() else "Fecha no disponible"

    # Generar código QR
    qr_dato = f"{numero}-{nombre}-{fecha_alta}"
    qr_img = qrcode.make(qr_dato)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer)
    qr_buffer.seek(0)
    qr_path = f"temp_qr_{numero}.png"
    with open(qr_path, "wb") as f:
        f.write(qr_buffer.read())

    # Generar PDF
    pdf = FPDF(orientation='P', unit='mm', format=(110, 70))
    pdf.add_page()
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.rect(10, 10, 90, 60)

    pdf.set_font("Arial", "B", 12)
    pdf.set_xy(15, 15)
    pdf.cell(80, 10, f"Carné de Socio nº {numero}", ln=1)

    pdf.set_font("Arial", "", 10)
    pdf.set_x(15)
    pdf.cell(80, 8, f"Nombre: {nombre}", ln=1)
    pdf.set_x(15)
    pdf.cell(80, 8, f"Fecha de alta: {fecha_alta}", ln=1)

    pdf.image(qr_path, x=15, y=42, w=30)

    os.remove(qr_path)  # Elimina el archivo temporal

    # Devuelve el PDF como archivo
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, download_name=f"carnet_{numero}.pdf", as_attachment=False)

@app.route('/calendar')
def calendar():
    if 'username' not in session:
        flash('Debes iniciar sesión para acceder a esta página.', 'error')
        return redirect(url_for('login'))
    return render_template('calendar.html')

@app.route('/events')
def events():
    try:
        with open('static/data/eventos.json', 'r', encoding='utf-8') as f:
            eventos = json.load(f)
    except FileNotFoundError:
        eventos = []
    
    return render_template('events.html', eventos=eventos)

@app.route('/admin/delete-event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'role' not in session or session['role'] != 'Admin':
        flash('Acceso denegado.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()

    flash('Evento eliminado correctamente.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/contests')
def contests():
    if 'user_id' not in session:
        flash("Debes iniciar sesión para acceder a esta sección.", "error")
        return redirect(url_for('login'))

    conn = get_db_connection()
    concursos_activos = conn.execute("SELECT * FROM concursos WHERE activo = 1").fetchall()
    concursos_finalizados = conn.execute("SELECT * FROM concursos WHERE activo = 0").fetchall()
    conn.close()

    return render_template('concursos.html', activos=concursos_activos, finalizados=concursos_finalizados)

# Crear tabla de eventos si no existe
def crear_tabla_events():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            tipo TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            lugar TEXT NOT NULL,
            asistentes INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/raffles')
def raffles():
    if 'user_id' not in session:
        flash("Debes iniciar sesión para acceder a esta sección.", "error")
        return redirect(url_for('login'))

    conn = get_db_connection()
    hoy = datetime.today().date()

    activos = conn.execute("""
        SELECT * FROM raffles
        WHERE activo = 1 AND DATE(fecha) >= DATE(?)
    """, (hoy.isoformat(),)).fetchall()

    finalizados = conn.execute("""
        SELECT * FROM raffles
        WHERE activo = 0 AND DATE(fecha) >= DATE(?) - 7
    """, (hoy.isoformat(),)).fetchall()

    conn.close()

    return render_template('raffles.html', activos=activos, finalizados=finalizados)


if __name__ == '__main__':
    crear_tabla_events()  # Esto crea la tabla en SQLite al arrancar la app
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)



