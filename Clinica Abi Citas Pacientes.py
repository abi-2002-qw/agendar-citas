import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from datetime import datetime, timedelta
from plyer import notification
import time

# Conexión a MySQL (XAMPP)
def conectar_a_mysql():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Usuario por defecto de XAMPP
        password="",  # Contraseña por defecto de XAMPP (vacía)
        database="centro_medico"  # Nombre de la base de datos
    )

# Crear la base de datos y tablas si no existen
def crear_base_de_datos():
    conn = conectar_a_mysql()
    c = conn.cursor()

    # Tabla de usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE,
                    password VARCHAR(255),
                    tipo VARCHAR(50))''')

    # Tabla de médicos
    c.execute('''CREATE TABLE IF NOT EXISTS medicos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255))''')

    # Tabla de citas
    c.execute('''CREATE TABLE IF NOT EXISTS citas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    paciente_id INT,
                    medico_id INT,
                    fecha DATE,
                    hora TIME,
                    FOREIGN KEY(paciente_id) REFERENCES usuarios(id),
                    FOREIGN KEY(medico_id) REFERENCES medicos(id))''')

    # Insertar datos de prueba (si no existen)
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios (username, password, tipo) VALUES (%s, %s, %s)",
                  ("admin", "admin123", "admin"))
        c.execute("INSERT INTO usuarios (username, password, tipo) VALUES (%s, %s, %s)",
                  ("paciente1", "paciente123", "paciente"))
        c.execute("INSERT INTO medicos (nombre) VALUES (%s)", ("Dr. Pérez",))
        c.execute("INSERT INTO medicos (nombre) VALUES (%s)", ("Dra. López",))

    conn.commit()
    conn.close()

crear_base_de_datos()

# Función para iniciar sesión
def iniciar_sesion():
    username = entry_username.get()
    password = entry_password.get()

    conn = conectar_a_mysql()
    c = conn.cursor()
    c.execute('SELECT * FROM usuarios WHERE username=%s AND password=%s', (username, password))
    usuario = c.fetchone()
    conn.close()

    if usuario:
        messagebox.showinfo("Inicio de Sesión", f"Bienvenido {usuario[1]}")
        root.withdraw()  # Oculta la ventana de inicio de sesión
        if usuario[3] == 'paciente':
            abrir_ventana_paciente(usuario[0])
        elif usuario[3] == 'admin':
            abrir_ventana_admin()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")

# Interfaz del Paciente
def abrir_ventana_paciente(paciente_id):
    ventana_paciente = tk.Toplevel()
    ventana_paciente.title("Paciente")
    ventana_paciente.geometry("400x300")

    def cargar_citas():
        conn = conectar_a_mysql()
        c = conn.cursor()
        c.execute('SELECT citas.id, medicos.nombre, citas.fecha, citas.hora FROM citas '
                  'JOIN medicos ON citas.medico_id = medicos.id '
                  'WHERE citas.paciente_id=%s', (paciente_id,))
        citas = c.fetchall()
        conn.close()

        for row in tree.get_children():
            tree.delete(row)
        for cita in citas:
            tree.insert("", "end", values=cita)

    def agendar_cita():
        def guardar_cita():
            medico_id = combo_medicos.current() + 1  # Los IDs empiezan en 1
            fecha = entry_fecha.get()
            hora = entry_hora.get()
            if medico_id and fecha and hora:
                conn = conectar_a_mysql()
                c = conn.cursor()
                c.execute('INSERT INTO citas (paciente_id, medico_id, fecha, hora) VALUES (%s, %s, %s, %s)',
                          (paciente_id, medico_id, fecha, hora))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Cita agendada correctamente")
                ventana_agendar.destroy()
                cargar_citas()
            else:
                messagebox.showerror("Error", "Todos los campos son obligatorios")

        ventana_agendar = tk.Toplevel()
        ventana_agendar.title("Agendar Cita")

        tk.Label(ventana_agendar, text="Médico:").grid(row=0, column=0)
        combo_medicos = ttk.Combobox(ventana_agendar)
        combo_medicos.grid(row=0, column=1)
        conn = conectar_a_mysql()
        c = conn.cursor()


        
        c.execute('SELECT nombre FROM medicos')
        medicos = c.fetchall()
        conn.close()
        combo_medicos['values'] = [medico[0] for medico in medicos]

        tk.Label(ventana_agendar, text="Fecha (YYYY-MM-DD):").grid(row=1, column=0)
        entry_fecha = tk.Entry(ventana_agendar)
        entry_fecha.grid(row=1, column=1)

        tk.Label(ventana_agendar, text="Hora (HH:MM):").grid(row=2, column=0)
        entry_hora = tk.Entry(ventana_agendar)
        entry_hora.grid(row=2, column=1)

        tk.Button(ventana_agendar, text="Guardar", command=guardar_cita).grid(row=3, column=1)

    def cancelar_cita():
        seleccionado = tree.selection()
        if seleccionado:
            cita_id = tree.item(seleccionado)['values'][0]
            conn = conectar_a_mysql()
            c = conn.cursor()
            c.execute('DELETE FROM citas WHERE id=%s', (cita_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Cita cancelada correctamente")
            cargar_citas()

    tk.Button(ventana_paciente, text="Agendar Cita", command=agendar_cita).pack()
    tk.Button(ventana_paciente, text="Cancelar Cita", command=cancelar_cita).pack()

    tree = ttk.Treeview(ventana_paciente, columns=("ID", "Médico", "Fecha", "Hora"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Médico", text="Médico")
    tree.heading("Fecha", text="Fecha")
    tree.heading("Hora", text="Hora")
    tree.pack()

    cargar_citas()

# Interfaz del Administrador
def abrir_ventana_admin():
    ventana_admin = tk.Toplevel()
    ventana_admin.title("Administrador")
    ventana_admin.geometry("600x400")

    def cargar_citas():
        conn = conectar_a_mysql()
        c = conn.cursor()
        c.execute('SELECT citas.id, usuarios.username, medicos.nombre, citas.fecha, citas.hora FROM citas '
                  'JOIN usuarios ON citas.paciente_id = usuarios.id '
                  'JOIN medicos ON citas.medico_id = medicos.id')
        citas = c.fetchall()
        conn.close()

        for row in tree.get_children():
            tree.delete(row)
        for cita in citas:
            tree.insert("", "end", values=cita)

    def cancelar_cita():
        seleccionado = tree.selection()
        if seleccionado:
            cita_id = tree.item(seleccionado)['values'][0]
            conn = conectar_a_mysql()
            c = conn.cursor()
            c.execute('DELETE FROM citas WHERE id=%s', (cita_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Cita cancelada correctamente")
            cargar_citas()

    tree = ttk.Treeview(ventana_admin, columns=("ID", "Paciente", "Médico", "Fecha", "Hora"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Paciente", text="Paciente")
    tree.heading("Médico", text="Médico")
    tree.heading("Fecha", text="Fecha")
    tree.heading("Hora", text="Hora")
    tree.pack()

    tk.Button(ventana_admin, text="Cancelar Cita", command=cancelar_cita).pack()

    cargar_citas()

# Interfaz de Inicio de Sesión
root = tk.Tk()
root.title("Inicio de Sesión")
root.geometry("300x150")

tk.Label(root, text="Usuario:").pack()
entry_username = tk.Entry(root)
entry_username.pack()

tk.Label(root, text="Contraseña:").pack()
entry_password = tk.Entry(root, show="*")
entry_password.pack()

tk.Button(root, text="Iniciar Sesión", command=iniciar_sesion).pack()

root.mainloop()
