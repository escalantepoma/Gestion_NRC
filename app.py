import streamlit as st
import pandas as pd
import io
from datetime import datetime

from database import (
    inicializar_bd,
    guardar_alumno,
    listar_alumnos,
    obtener_alumno_por_codigo,
    listar_aulas_guardadas,
    procesar_excel_masivo,
    eliminar_alumno,
    vaciar_alumnos
)
from pdf_generator import generar_ficha_pdf

st.set_page_config(page_title="Sistema de Ratificación Escolar", page_icon="🏫", layout="wide")

try:
    inicializar_bd()
except Exception as e:
    st.error(f"Error en BD: {e}")

st.title("🏫 Control de Ratificación de Matrícula")
st.caption("Gestión ágil de ratificación anual, nuevos ingresos y fichas de matrícula")

tab1, tab2, tab3 = st.tabs([
    "📝 Ratificación / Nuevo Registro", 
    "📋 Planillón y Búsqueda",
    "📤 Carga y Plantilla Excel"
])

# -------------------------------------------------------------
# TAB 1: RATIFICACIÓN RÁPIDA / REGISTRO NUEVO
# -------------------------------------------------------------
with tab1:
    st.subheader("Ficha del Estudiante y Apoderado")
    ahora = datetime.now()
    st.info(f"📅 **Fecha de ratificación asignada al guardar:** {ahora.day:02d} / {ahora.month:02d} / {ahora.year} (Automática)")

    # 1. BUSCADOR DINÁMICO
    st.markdown("##### 🔍 Buscar alumno para Ratificación Anual (Opcional)")
    col_s1, col_s2, col_s3 = st.columns([2.5, 2, 1])
    
    with col_s1:
        txt_buscar = st.text_input("Ingrese DNI o Apellidos:", placeholder="Ej: 82383709 o ALCANTARA...")
    
    candidatos = []
    if txt_buscar.strip():
        candidatos = listar_alumnos(busqueda=txt_buscar.strip())

    alumno_precargado = None
    with col_s2:
        if candidatos:
            opciones_candidatos = ["-- Seleccione alumno --"] + [f"{c['codigo_estudiante']} - {c['apellidos_nombres']}" for c in candidatos]
            seleccion_candidato = st.selectbox("Coincidencias:", opciones_candidatos)
            if seleccion_candidato != "-- Seleccione alumno --":
                dni_elegido = seleccion_candidato.split(" - ")[0]
                alumno_precargado = obtener_alumno_por_codigo(dni_elegido)
        else:
            if txt_buscar.strip():
                st.caption("Sin coincidencias (se creará como nuevo).")
            else:
                st.caption("Escriba para buscar estudiante.")

    with col_s3:
        st.write("")
        if st.button("🧹 Limpiar formulario", use_container_width=True):
            alumno_precargado = None
            st.rerun()

    # Precarga de datos
    v_cod = alumno_precargado['codigo_estudiante'] if alumno_precargado else ""
    v_nom = alumno_precargado['apellidos_nombres'] if alumno_precargado else ""
    v_apo_nom = alumno_precargado['apoderado_nombres'] if alumno_precargado else ""
    v_apo_dni = alumno_precargado['apoderado_dni'] if alumno_precargado else ""
    v_parentesco = alumno_precargado['parentesco'] if alumno_precargado else "Madre"
    v_dir = alumno_precargado['direccion'] if alumno_precargado else ""
    v_tel = alumno_precargado['telefonos'] if alumno_precargado else ""
    v_obs = alumno_precargado['observaciones'] if alumno_precargado else ""
    v_aula_previa = alumno_precargado['grado_seccion'] if alumno_precargado else ""

    if alumno_precargado:
        st.success(f"📌 Alumno cargado: **{v_nom}** | Salón anterior registrado: **{v_aula_previa}**")

    # 2. DEFINICIÓN DEL AULA Y AÑO (FUERA DEL FORMULARIO PARA REACCIÓN INMEDIATA)
    st.markdown("---")
    st.markdown("##### 🏫 Asignación de Período y Salón para la Matrícula")
    
    col_per, col_tipo_aula = st.columns([1, 2])
    with col_per:
        periodo_actual = st.number_input("Año Lectivo / Período:", min_value=2024, max_value=2035, value=2026, step=1)
    
    aulas_existentes = listar_aulas_guardadas()
    
    with col_tipo_aula:
        modo_aula = st.radio(
            "Seleccione cómo asignar el salón:",
            ["Elegir de la lista existente", "➕ Escribir un nuevo salón (cambio de año/sección)"],
            horizontal=True
        )

    aula_seleccionada_final = ""
    col_sel_a1, col_sel_a2 = st.columns(2)
    
    if modo_aula == "Elegir de la lista existente":
        with col_sel_a1:
            if aulas_existentes:
                idx_default = aulas_existentes.index(v_aula_previa) if v_aula_previa in aulas_existentes else 0
                aula_seleccionada_final = st.selectbox("Seleccione el aula existente:", aulas_existentes, index=idx_default)
            else:
                st.warning("Aún no hay aulas registradas. Marque la opción '➕ Escribir un nuevo salón'.")
    else:
        with col_sel_a1:
            aula_seleccionada_final = st.text_input(
                "Escriba el nuevo salón/grado/sección (*):",
                placeholder="Ej: 4 AÑOS - ROJA, 1° B PRIMARIA, 5° A SECUNDARIA"
            )

    # 3. FORMULARIO DE DATOS GENERALES Y CONFIRMACIÓN
    with st.form("form_ratificacion", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Datos del Estudiante")
            cod_est = st.text_input("DNI o Código de Estudiante (*)", value=v_cod, max_chars=15)
            nom_est = st.text_input("Apellidos y Nombres del Estudiante (*)", value=v_nom)
            direccion = st.text_input("Dirección Domiciliaria (*)", value=v_dir)
            telefonos = st.text_input("Teléfono(s) de contacto (*)", value=v_tel)
            
        with c2:
            st.markdown("##### Datos del Apoderado")
            nom_apo = st.text_input("Apellidos y Nombres del Padre y/o Apoderado (*)", value=v_apo_nom)
            dni_apo = st.text_input("DNI / Doc. Identidad del Apoderado (*)", value=v_apo_dni, max_chars=15)
            
            parentescos_lista = ["Madre", "Padre", "Tutor Legal", "Abuelo/a", "Tío/a", "Hermano/a", "Otro"]
            idx_par = parentescos_lista.index(v_parentesco) if v_parentesco in parentescos_lista else 0
            parentesco = st.selectbox("Parentesco (*)", parentescos_lista, index=idx_par)
            
            obs = st.text_area("Observaciones (opcional)", value=v_obs, height=110)

        st.markdown("---")
        st.markdown(f"##### 📑 Documentos recepcionados para el año escolar {periodo_actual}")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            chk_dni_est = st.checkbox("DNI Estudiante", value=bool(alumno_precargado['doc_dni_estudiante']) if alumno_precargado else False)
            chk_dni_ppff = st.checkbox("DNI PPFF / Apoderado", value=bool(alumno_precargado['doc_dni_ppff']) if alumno_precargado else False)
            chk_hoja_imp = st.checkbox("Hoja Impresa de Matrícula", value=bool(alumno_precargado['doc_hoja_impresa']) if alumno_precargado else False)
            chk_riesgos = st.checkbox("Ficha Gestión de Riesgos", value=bool(alumno_precargado['doc_gestion_riesgos']) if alumno_precargado else False)
        with d_col2:
            chk_compromiso = st.checkbox("Carta de Compromiso", value=bool(alumno_precargado['doc_compromiso']) if alumno_precargado else False)
            chk_religion = st.checkbox("Exoneración de Religión", value=bool(alumno_precargado['doc_exoneracion_religion']) if alumno_precargado else False)
            chk_salida = st.checkbox("Autorización de Salida de la I.E.", value=bool(alumno_precargado['doc_autorizacion_salida']) if alumno_precargado else False)
            chk_carta_poder = st.checkbox("Carta Poder", value=bool(alumno_precargado['doc_carta_poder']) if alumno_precargado else False)

        st.write("")
        texto_boton = f"💾 Ratificar Matrícula para el Período {periodo_actual}" if alumno_precargado else f"💾 Guardar Estudiante Nuevo ({periodo_actual})"
        guardar = st.form_submit_button(texto_boton, use_container_width=True)
        
        if guardar:
            aula_final = aula_seleccionada_final.strip()
            
            if not cod_est or not nom_est or not nom_apo or not dni_apo or not direccion or not telefonos or not aula_final:
                st.error("⚠️ Complete todos los campos obligatorios (*), asegurando que el salón no quede vacío.")
            else:
                datos = {
                    "codigo_estudiante": cod_est.strip(),
                    "apellidos_nombres": nom_est.strip().upper(),
                    "apoderado_nombres": nom_apo.strip().upper(),
                    "apoderado_dni": dni_apo.strip(),
                    "parentesco": parentesco,
                    "direccion": direccion.strip(),
                    "telefonos": telefonos.strip(),
                    "observaciones": obs.strip(),
                    "grado_seccion": aula_final.upper(),
                    "periodo": int(periodo_actual),
                    "doc_dni_estudiante": 1 if chk_dni_est else 0,
                    "doc_dni_ppff": 1 if chk_dni_ppff else 0,
                    "doc_hoja_impresa": 1 if chk_hoja_imp else 0,
                    "doc_gestion_riesgos": 1 if chk_riesgos else 0,
                    "doc_compromiso": 1 if chk_compromiso else 0,
                    "doc_exoneracion_religion": 1 if chk_religion else 0,
                    "doc_autorizacion_salida": 1 if chk_salida else 0,
                    "doc_carta_poder": 1 if chk_carta_poder else 0
                }
                guardar_alumno(datos)
                st.success(f"✅ ¡Éxito! Estudiante {nom_est.strip().upper()} ratificado en '{aula_final.upper()}' para el año {periodo_actual}.")
                st.rerun()

# -------------------------------------------------------------
# TAB 2: PLANILLÓN Y GESTIÓN
# -------------------------------------------------------------
with tab2:
    st.subheader("Planillón General de Estudiantes")
    col_f1, col_f2 = st.columns([3, 2])
    with col_f1:
        criterio = st.text_input("🔍 Buscar por DNI o Apellidos:", placeholder="Escriba para filtrar...", key="busq_planillon")
    with col_f2:
        aulas_para_filtro = ["Todos"] + listar_aulas_guardadas()
        filtro_aula = st.selectbox("Filtrar por Aula:", aulas_para_filtro, key="filtro_planillon")
        
    registros = listar_alumnos(criterio, filtro_aula)
    
    if registros:
        datos_tabla = []
        for r in registros:
            total_docs = sum([
                r['doc_dni_estudiante'] or 0,
                r['doc_dni_ppff'] or 0,
                r['doc_hoja_impresa'] or 0,
                r['doc_gestion_riesgos'] or 0,
                r['doc_compromiso'] or 0,
                r['doc_exoneracion_religion'] or 0,
                r['doc_autorizacion_salida'] or 0,
                r['doc_carta_poder'] or 0
            ])
            datos_tabla.append({
                "Fecha": str(r['fecha_ratificacion'])[:10],
                "DNI / Cód.": r['codigo_estudiante'],
                "Estudiante": r['apellidos_nombres'],
                "Grado / Sección": r['grado_seccion'],
                "Apoderado": r['apoderado_nombres'],
                "Teléfonos": r['telefonos'],
                "Docs": f"{total_docs}/8"
            })
        
        df = pd.DataFrame(datos_tabla)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Tabla en CSV", data=csv, file_name="planillon_alumnos.csv", mime="text/csv")
        
        st.markdown("---")
        st.subheader("⚙️ Acciones por Estudiante")
        
        codigos = [str(r['codigo_estudiante']) for r in registros]
        seleccion = st.selectbox(
            "Seleccione estudiante para imprimir o eliminar:",
            codigos,
            format_func=lambda c: f"{c} - {next((r['apellidos_nombres'] for r in registros if str(r['codigo_estudiante']) == c), '')}"
        )
        
        if seleccion:
            alumno_sel = obtener_alumno_por_codigo(seleccion)
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                try:
                    pdf_bytes = generar_ficha_pdf(alumno_sel)
                    st.download_button(
                        label=f"📄 Descargar PDF de {alumno_sel['apellidos_nombres']}",
                        data=pdf_bytes,
                        file_name=f"Ficha_{alumno_sel['codigo_estudiante']}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as err_pdf:
                    st.warning(f"No se pudo previsualizar PDF: {err_pdf}")
            
            with col_btn2:
                if st.button(f"🗑️ Eliminar estudiante ({alumno_sel['codigo_estudiante']})", use_container_width=True):
                    eliminar_alumno(alumno_sel['codigo_estudiante'])
                    st.warning(f"Estudiante eliminado.")
                    st.rerun()

        st.markdown("---")
        with st.expander("⚠️ Mantenimiento y Borrado Masivo"):
            confirmar_vaciado = st.checkbox("Confirmo que deseo vaciar todos los registros del sistema")
            if st.button("🚨 Borrar todo el planillón", disabled=not confirmar_vaciado, use_container_width=True):
                vaciar_alumnos()
                st.success("Se vació la lista correctamente.")
                st.rerun()
    else:
        st.info("No hay alumnos registrados con esos criterios.")

# -------------------------------------------------------------
# TAB 3: PLANTILLA Y CARGA EXCEL
# -------------------------------------------------------------
with tab3:
    st.subheader("Importación y Exportación Masiva")
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.markdown("##### 1. Descargar Formato Oficial")
        st.write("Completa esta plantilla y súbela a la derecha:")
        
        cols_formato = [
            "DNI / Código Estudiante", "Apellidos y Nombres Estudiante", "Grado y Sección",
            "Apellidos y Nombres Apoderado", "DNI Apoderado", "Parentesco",
            "Dirección Domiciliaria", "Teléfonos", "Observaciones",
            "Doc: DNI Estudiante", "Doc: DNI PPFF", "Doc: Hoja Impresa",
            "Doc: Ficha Gestión Riesgos", "Doc: Carta Compromiso",
            "Doc: Exoneración Religión", "Doc: Autorización Salida", "Doc: Carta Poder"
        ]
        datos_demo = [
            [
                "72345678", "QUISPE MAMANI, JUAN CARLOS", "1° A PRIMARIA",
                "QUISPE FLORES, CARLOS", "09876543", "Padre",
                "Av. Principal 123", "991234567", "Sin observaciones",
                "SI", "SI", "SI", "SI", "SI", "NO", "SI", "NO"
            ]
        ]
        df_demo = pd.DataFrame(datos_demo, columns=cols_formato)
        buffer_xls = io.BytesIO()
        with pd.ExcelWriter(buffer_xls, engine='openpyxl') as writer:
            df_demo.to_excel(writer, index=False, sheet_name="Matricula")
            
        st.download_button(
            "📥 Descargar Plantilla Excel (.xlsx)",
            data=buffer_xls.getvalue(),
            file_name="Plantilla_Alumnos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_der:
        st.markdown("##### 2. Subir Archivo Diligenciado")
        subido = st.file_uploader("Selecciona el archivo Excel (.xlsx):", type=["xlsx", "xls"])
        if subido and st.button("🚀 Procesar e Importar", use_container_width=True):
            with st.spinner("Importando..."):
                try:
                    cant = procesar_excel_masivo(subido)
                    st.success(f"¡Listo! Se procesaron {cant} estudiantes.")
                    st.rerun()
                except Exception as err:
                    st.error(f"Error en la carga: {err}")