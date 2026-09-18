import sqlite3
import os
from datetime import datetime
import pandas as pd

DB_NAME = "colegio.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_bd():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aulas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_ratificacion TEXT NOT NULL,
        codigo_estudiante TEXT UNIQUE NOT NULL,
        apellidos_nombres TEXT NOT NULL,
        apoderado_nombres TEXT NOT NULL,
        apoderado_dni TEXT NOT NULL,
        parentesco TEXT NOT NULL,
        direccion TEXT NOT NULL,
        telefonos TEXT NOT NULL,
        observaciones TEXT,
        grado_seccion TEXT NOT NULL,
        periodo INTEGER DEFAULT 2026,
        doc_dni_estudiante INTEGER DEFAULT 0,
        doc_dni_ppff INTEGER DEFAULT 0,
        doc_hoja_impresa INTEGER DEFAULT 0,
        doc_gestion_riesgos INTEGER DEFAULT 0,
        doc_compromiso INTEGER DEFAULT 0,
        doc_exoneracion_religion INTEGER DEFAULT 0,
        doc_autorizacion_salida INTEGER DEFAULT 0,
        doc_carta_poder INTEGER DEFAULT 0
    )
    """)

    columnas_docs = [
        ("doc_dni_estudiante", "INTEGER DEFAULT 0"),
        ("doc_dni_ppff", "INTEGER DEFAULT 0"),
        ("doc_hoja_impresa", "INTEGER DEFAULT 0"),
        ("doc_gestion_riesgos", "INTEGER DEFAULT 0"),
        ("doc_compromiso", "INTEGER DEFAULT 0"),
        ("doc_exoneracion_religion", "INTEGER DEFAULT 0"),
        ("doc_autorizacion_salida", "INTEGER DEFAULT 0"),
        ("doc_carta_poder", "INTEGER DEFAULT 0")
    ]
    
    cursor.execute("PRAGMA table_info(alumnos)")
    columnas_existentes = [col["name"] for col in cursor.fetchall()]
    
    for col_nombre, col_tipo in columnas_docs:
        if col_nombre not in columnas_existentes:
            cursor.execute(f"ALTER TABLE alumnos ADD COLUMN {col_nombre} {col_tipo}")

    conn.commit()
    conn.close()

def registrar_aula_si_no_existe(aula_nombre):
    if not aula_nombre or not str(aula_nombre).strip() or str(aula_nombre).strip().upper() == "NAN":
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO aulas (nombre) VALUES (?)", (str(aula_nombre).strip().upper(),))
    conn.commit()
    conn.close()

def listar_aulas_guardadas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM aulas WHERE nombre != 'NAN' ORDER BY nombre ASC")
    filas = [r["nombre"] for r in cursor.fetchall()]
    conn.close()
    return filas

def guardar_alumno(datos):
    registrar_aula_si_no_existe(datos['grado_seccion'])
    conn = get_connection()
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
    INSERT INTO alumnos (
        fecha_ratificacion, codigo_estudiante, apellidos_nombres,
        apoderado_nombres, apoderado_dni, parentesco, direccion,
        telefonos, observaciones, grado_seccion, periodo,
        doc_dni_estudiante, doc_dni_ppff, doc_hoja_impresa,
        doc_gestion_riesgos, doc_compromiso, doc_exoneracion_religion,
        doc_autorizacion_salida, doc_carta_poder
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(codigo_estudiante) DO UPDATE SET
        fecha_ratificacion = excluded.fecha_ratificacion,
        apellidos_nombres = excluded.apellidos_nombres,
        apoderado_nombres = excluded.apoderado_nombres,
        apoderado_dni = excluded.apoderado_dni,
        parentesco = excluded.parentesco,
        direccion = excluded.direccion,
        telefonos = excluded.telefonos,
        observaciones = excluded.observaciones,
        grado_seccion = excluded.grado_seccion,
        doc_dni_estudiante = excluded.doc_dni_estudiante,
        doc_dni_ppff = excluded.doc_dni_ppff,
        doc_hoja_impresa = excluded.doc_hoja_impresa,
        doc_gestion_riesgos = excluded.doc_gestion_riesgos,
        doc_compromiso = excluded.doc_compromiso,
        doc_exoneracion_religion = excluded.doc_exoneracion_religion,
        doc_autorizacion_salida = excluded.doc_autorizacion_salida,
        doc_carta_poder = excluded.doc_carta_poder
    """, (
        fecha_actual,
        datos['codigo_estudiante'],
        datos['apellidos_nombres'],
        datos['apoderado_nombres'],
        datos['apoderado_dni'],
        datos['parentesco'],
        datos['direccion'],
        datos['telefonos'],
        datos['observaciones'],
        datos['grado_seccion'].strip().upper(),
        datos.get('periodo', 2026),
        datos.get('doc_dni_estudiante', 0),
        datos.get('doc_dni_ppff', 0),
        datos.get('doc_hoja_impresa', 0),
        datos.get('doc_gestion_riesgos', 0),
        datos.get('doc_compromiso', 0),
        datos.get('doc_exoneracion_religion', 0),
        datos.get('doc_autorizacion_salida', 0),
        datos.get('doc_carta_poder', 0)
    ))
    conn.commit()
    conn.close()

def listar_alumnos(busqueda="", filtro_aula="Todos"):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM alumnos WHERE 1=1"
    params = []
    
    if busqueda:
        query += " AND (codigo_estudiante LIKE ? OR apellidos_nombres LIKE ?)"
        params.extend([f"%{busqueda}%", f"%{busqueda}%"])
        
    if filtro_aula != "Todos":
        query += " AND grado_seccion = ?"
        params.append(filtro_aula)
        
    query += " ORDER BY apellidos_nombres ASC"
    cursor.execute(query, params)
    filas = cursor.fetchall()
    conn.close()
    return filas

def obtener_alumno_por_codigo(codigo):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alumnos WHERE codigo_estudiante = ?", (str(codigo),))
    alumno = cursor.fetchone()
    conn.close()
    return alumno

def eliminar_alumno(codigo_estudiante):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alumnos WHERE codigo_estudiante = ?", (str(codigo_estudiante),))
    conn.commit()
    conn.close()

def vaciar_alumnos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alumnos")
    cursor.execute("DELETE FROM aulas")
    conn.commit()
    conn.close()

def procesar_excel_masivo(archivo_excel):
    df = pd.read_excel(archivo_excel)
    
    def a_booleano(val):
        if pd.isna(val):
            return 0
        val_str = str(val).strip().upper()
        return 1 if val_str in ["SI", "SÍ", "1", "TRUE", "X"] else 0

    total_procesados = 0
    for _, row in df.iterrows():
        cod_est = str(row.get("DNI / Código Estudiante", "")).strip().replace(".0", "")
        nom_est = str(row.get("Apellidos y Nombres Estudiante", "")).strip()
        
        if not cod_est or cod_est.lower() == "nan":
            continue

        grado_sec = str(row.get("Grado y Sección", "")).strip().upper()
        nom_apo = str(row.get("Apellidos y Nombres Apoderado", "")).strip().upper()
        dni_apo = str(row.get("DNI Apoderado", "")).strip().replace(".0", "")
        parentesco = str(row.get("Parentesco", "Madre")).strip()
        direccion = str(row.get("Dirección Domiciliaria", "")).strip()
        telefonos = str(row.get("Teléfonos", "")).strip().replace(".0", "")
        observaciones = str(row.get("Observaciones", "")).strip()
        if observaciones.lower() == "nan":
            observaciones = ""

        datos = {
            "codigo_estudiante": cod_est,
            "apellidos_nombres": nom_est.upper(),
            "apoderado_nombres": nom_apo,
            "apoderado_dni": dni_apo,
            "parentesco": parentesco,
            "direccion": direccion,
            "telefonos": telefonos,
            "observaciones": observaciones,
            "grado_seccion": grado_sec,
            "periodo": 2026,
            "doc_dni_estudiante": a_booleano(row.get("Doc: DNI Estudiante")),
            "doc_dni_ppff": a_booleano(row.get("Doc: DNI PPFF")),
            "doc_hoja_impresa": a_booleano(row.get("Doc: Hoja Impresa")),
            "doc_gestion_riesgos": a_booleano(row.get("Doc: Ficha Gestión Riesgos")),
            "doc_compromiso": a_booleano(row.get("Doc: Carta Compromiso")),
            "doc_exoneracion_religion": a_booleano(row.get("Doc: Exoneración Religión")),
            "doc_autorizacion_salida": a_booleano(row.get("Doc: Autorización Salida")),
            "doc_carta_poder": a_booleano(row.get("Doc: Carta Poder"))
        }
        guardar_alumno(datos)
        total_procesados += 1

    return total_procesados