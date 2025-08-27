# app.py
# MVP Streamlit – Avance por capítulos de protocolos
# Requisitos: streamlit, pandas, numpy, plotly
# pip install streamlit pandas numpy plotly

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Avances de Protocolos", layout="wide")
# ---------- Encabezado principal ----------
st.markdown(
    """
    <div style="text-align:left; margin-top:-60px; margin-bottom:20px;">
        <h1 style="font-size:32px; margin-bottom:5px;">
            Sumideros Naturales de Carbono
        </h1>
        <h2 style="font-size:22px; font-weight:normal; margin-top:0; margin-bottom:3px;">
            Protocolos de Carbono para Ecosistemas de Investigación
        </h2>
        <h3 style="font-size:18px; font-weight:normal; color:gray; margin-top:0;">
            Convenio de investigación Ecopetrol – Fundación Natura – IDEAM.
        </h3>
    </div>
    <hr>
    """,
    unsafe_allow_html=True
)
# ---------- Sidebar: Carga de datos ----------
st.sidebar.title("⚙️ Configuración")
uploaded = st.sidebar.file_uploader("Cargar Excel (.xlsx)", type=["xlsx"])

# Umbral de "atrasado"
umbral = st.sidebar.slider("Umbral de atraso (%)", min_value=0, max_value=100, value=60, step=5)

# Mostrar/ocultar comentarios
mostrar_comentarios = st.sidebar.checkbox("Mostrar comentarios por capítulo", value=False)

# Dataset de ejemplo si no cargan archivo
def ejemplo_df():
    return pd.DataFrame({
        "Protocolo": ["Manglar","Manglar","Manglar","Páramo","Páramo","Seagrass","Seagrass"],
        "Capítulo": ["Introducción y alcance","Metodología de muestreo","Modelo de carbono","Introducción y alcance","Metodología de muestreo","Introducción y alcance","Inventario de datos"],
        "Avance (%)": [0,2,5,10,15,19,20],
        "Comentario": [
            "Revisión con el equipo IDEAM completada.",
            "Aprobado por comité técnico.",
            "Revisión con el equipo IDEAM en curso.",
            "Revisión interna en curso.",
            "Revisión con proveedor en curso.",
            "Listo para validación externa.",
            "Integración de bases de datos pendiente."
        ]
    })

if uploaded:
    try:
        df = pd.read_excel(uploaded, sheet_name="AvanceProtocolos")
    except Exception as e:
        st.error(f"Error leyendo el Excel: {e}")
        st.stop()
else:
    st.info("Cargar Excel de avance. Usando datos de ejemplo.")
    df = ejemplo_df()

# Validaciones mínimas
cols_req = {"Protocolo","Capítulo","Avance (%)","Comentario"}
faltan = cols_req - set(df.columns)
if faltan:
    st.error(f"El Excel debe contener las columnas: {', '.join(cols_req)}. Faltan: {', '.join(faltan)}")
    st.stop()

# Normalizar tipos
df["Avance (%)"] = pd.to_numeric(df["Avance (%)"], errors="coerce").fillna(0).clip(0,100)

# ---------- Filtros ----------
protocolos = sorted(df["Protocolo"].dropna().unique().tolist())
sel_protocolos = st.multiselect("Filtrar por protocolo(s)", options=protocolos, default=protocolos)

solo_atrasados = st.checkbox("Ver solo capítulos atrasados", value=False)

filtrado = df[df["Protocolo"].isin(sel_protocolos)].copy()
if solo_atrasados:
    filtrado = filtrado[filtrado["Avance (%)"] < umbral]

# ---------- Tabs de navegación ----------
tab_resumen, tab_detalle, tab_tiempo = st.tabs(["🏁 Resumen", "🔎 Detalle por protocolo", "⏱️ Línea de tiempo"]) 

# =============================
# 🏁 TAB: RESUMEN EJECUTIVO
# =============================
with tab_resumen:
    st.markdown("### 📌 Resumen ejecutivo")

    col1, col2, col3 = st.columns(3)
    avance_total = filtrado["Avance (%)"].mean() if len(filtrado) else np.nan
    total_capitulos = len(filtrado)
    cap_atrasados = (filtrado["Avance (%)"] < umbral).sum()

    with col1:
        st.metric("📊 Avance promedio global", f"{(avance_total if pd.notna(avance_total) else 0):.1f}%")
    with col2:
        st.metric("📚 Capítulos considerados", f"{total_capitulos}")
    with col3:
        st.metric("⛔ Capítulos bajo umbral", f"{cap_atrasados}")

    st.markdown("---")

    # Tarjetas por protocolo (promedios)
    st.subheader("🧭 Avance promedio por protocolo")
    grp = filtrado.groupby("Protocolo", as_index=False)["Avance (%)"].mean().sort_values("Avance (%)", ascending=False)

    if grp.empty:
        st.warning("No hay datos para mostrar con los filtros actuales.")
    else:
        ccols = st.columns(min(4, max(1, len(grp))))
        for i, (_, row) in enumerate(grp.iterrows()):
            with ccols[i % len(ccols)]:
                st.metric(f"**{row['Protocolo']}**", f"{row['Avance (%)']:.1f}%")

    st.markdown("---")

    # Capítulos críticos (los de menor avance)
    st.subheader("Capítulos de menor avance")
    top_n = st.slider("Mostrar N capítulos con menor avance", min_value=3, max_value=20, value=7, step=1)
    if not filtrado.empty:
        worst = filtrado.sort_values("Avance (%)").head(top_n)
        st.dataframe(
            worst[["Protocolo", "Capítulo", "Avance (%)", "Comentario"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Ajusta los filtros para ver capítulos críticos.")

# =============================
# 🔎 TAB: DETALLE POR PROTOCOLO
# =============================
with tab_detalle:
    st.markdown("### 📑 Detalle por protocolo")
    if filtrado.empty:
        st.info("Ajusta los filtros para ver el detalle por capítulos.")
    else:
        protos_det = sorted(filtrado["Protocolo"].dropna().unique().tolist())
        sel_prot = st.selectbox("Selecciona un protocolo", options=protos_det, index=0)

        dfp = filtrado[filtrado["Protocolo"] == sel_prot].copy()
        dfp = dfp.sort_values("Avance (%)", ascending=False)

        # Opción de visualización
        modo = st.radio("Modo de visualización", ["Gráfica", "Tabla compacta"], horizontal=True)

        if modo == "Gráfica":
            fig = px.bar(
                dfp,
                x="Avance (%)",
                y="Capítulo",
                color="Avance (%)",
                color_continuous_scale="Turbo",
                orientation="h",
                text="Avance (%)",
                height=min(800, 120 + len(dfp) * 28)
            )
            fig.update_traces(texttemplate="%{x:.0f}%", textposition="outside", cliponaxis=False)
            fig.update_layout(
                coloraxis_showscale=False,
                margin=dict(l=120, r=40, t=20, b=40),
                bargap=0.15
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Tabla compacta con barra de progreso integrada
            st.dataframe(
                dfp[["Capítulo", "Avance (%)", "Comentario"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Avance (%)": st.column_config.ProgressColumn(
                        "Avance (%)",
                        min_value=0,
                        max_value=100,
                        format="%d%%"
                    )
                }
            )

        if mostrar_comentarios and modo == "Gráfica":
            with st.expander("📝 Ver comentarios por capítulo"):
                st.dataframe(
                    dfp[["Capítulo", "Avance (%)", "Comentario"]],
                    use_container_width=True,
                    hide_index=True
                )

# =============================
# ⏱️ TAB: LÍNEA DE TIEMPO (opcional)
# =============================
with tab_tiempo:
    st.markdown("### ⏱️ Evolución en el tiempo")
    st.caption("Esta vista se activa si el Excel incluye una columna **Fecha** (por fila). Para ver tendencia, registra múltiples cortes temporales por capítulo o protocolo.")

    if "Fecha" not in df.columns:
        st.info("Agrega una columna **Fecha** (formato fecha) a tu Excel para habilitar la línea de tiempo. Repite filas de capítulos con diferentes fechas para ver la evolución del avance.")
    else:
        # Preparar datos de tiempo (asegurar tipo datetime y quitar tz)
        dt = df.copy()
        dt["Fecha"] = pd.to_datetime(dt["Fecha"], errors="coerce").dt.tz_localize(None)
        dt = dt.dropna(subset=["Fecha"]).sort_values("Fecha")

        if dt.empty:
            st.info("No hay fechas válidas. Verifica el formato de la columna **Fecha**.")
        else:
            # Convertir a date para el slider (evita KeyError con Timestamp)
            min_d = dt["Fecha"].min().date()
            max_d = dt["Fecha"].max().date()

            # Si solo hay un día, usar date_input en vez de slider de rango
            if min_d == max_d:
                sel_d = st.date_input("Fecha", value=min_d)
                dts = dt[dt["Fecha"].dt.date == sel_d].copy()
            else:
                rango = st.slider(
                    "Rango de fechas",
                    min_value=min_d,
                    max_value=max_d,
                    value=(min_d, max_d),
                )
                # Filtrar usando objetos date
                dts = dt[
                    (dt["Fecha"].dt.date >= rango[0]) &
                    (dt["Fecha"].dt.date <= rango[1])
                ].copy()

            # Filtro de protocolos
            protocolos_time = sorted(dts["Protocolo"].dropna().unique().tolist())
            if not protocolos_time:
                st.warning("Sin datos para los filtros seleccionados.")
                st.stop()

            sel_protos_time = st.multiselect("Filtrar protocolos", options=protocolos_time, default=protocolos_time)
            dts = dts[dts["Protocolo"].isin(sel_protos_time)].copy()

            vista = st.radio("Vista", ["Promedio por protocolo", "Capítulos"], horizontal=True)

            if vista == "Promedio por protocolo":
                agg = dts.groupby(["Fecha", "Protocolo"], as_index=False)["Avance (%)"].mean()
                if agg.empty:
                    st.warning("Sin datos para la combinación seleccionada.")
                else:
                    figt = px.line(
                        agg,
                        x="Fecha",
                        y="Avance (%)",
                        color="Protocolo",
                        markers=True,
                        hover_data={"Protocolo": True, "Avance (%)": ":.1f", "Fecha": "|%Y-%m-%d"},
                    )
                    figt.update_layout(yaxis_range=[0, 100], margin=dict(l=40, r=20, t=20, b=40))
                    st.plotly_chart(figt, use_container_width=True)
            else:
                # Capítulos por protocolo (para no saturar, elegir uno)
                prot_choice = st.selectbox("Selecciona un protocolo", options=protocolos_time)
                dts_p = dts[dts["Protocolo"] == prot_choice].copy()
                agg = dts_p.groupby(["Fecha", "Capítulo"], as_index=False)["Avance (%)"].mean()
                if agg.empty:
                    st.warning("Sin datos de capítulos para el protocolo seleccionado en el rango de fechas.")
                else:
                    figt = px.line(
                        agg,
                        x="Fecha",
                        y="Avance (%)",
                        color="Capítulo",
                        markers=True,
                        hover_data={"Capítulo": True, "Avance (%)": ":.1f", "Fecha": "|%Y-%m-%d"},
                    )
                    figt.update_layout(yaxis_range=[0, 100], margin=dict(l=40, r=20, t=20, b=40), legend_title_text="Capítulo")
                    st.plotly_chart(figt, use_container_width=True)

# ---------- Pie de página ----------
import datetime
fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")

st.markdown(
    f"""
    <hr>
    <div style="text-align:left; color:gray; font-size:14px; margin-top:30px;">
        📅 Fecha de generación del reporte: {fecha_hoy}<br>
        Este panel es un <b>producto en pruebas</b>, desarrollado para uso interno. Estudio SNC. GLT, ICPET - Ecopetrol.
    </div>
    """,
    unsafe_allow_html=True
)
