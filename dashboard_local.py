# ==============================================================
#  DASHBOARD LOCAL EN TIEMPO REAL (Streamlit)
#  - Lee "datos.csv" que escribe el simulador
#  - 6 gráficos con umbral, puntos rojos (exceso) y alertas
#  - Tabla de histórico y leyenda de umbrales
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os

# --- LIMPIEZA AUTOMÁTICA AL INICIAR ---
if os.path.exists("datos.csv"):
    os.remove("datos.csv")

st.set_page_config(page_title="Dashboard Viñedo (Local)", layout="wide")

CSV_PATH = "datos.csv"

# Umbrales (deben coincidir con el simulador)
UMBRAL = {
    "humedad_suelo": 35,
    "temperatura_suelo": 33,
    "ph_suelo": 7.5,
    "humedad_aire": 85,
    "temperatura_aire": 35,
    "radiacion": 45000
}

SENSORES = [
    ("humedad_suelo",     "Humedad Suelo (%)"),
    ("temperatura_suelo", "Temperatura Suelo (°C)"),
    ("ph_suelo",          "pH Suelo"),
    ("humedad_aire",      "Humedad Aire (%)"),
    ("temperatura_aire",  "Temperatura Aire (°C)"),
    ("radiacion",         "Radiación (lux)"),
]

st.title("🌱 Dashboard en tiempo real (Local, sin ThingSpeak)")
st.caption("Lee datos de 'datos.csv' escritos por el simulador (Pygame).")

# Panel de control
colA, colB = st.columns(2)
refresh_secs = colA.slider("Intervalo de actualización (s)", 1, 10, 2, help="Cada cuántos segundos recargar los datos.")
mostrar_tabla = colB.checkbox("Mostrar tabla histórica", True)

placeholder_alertas = st.empty()
placeholder_graficos = st.container()
placeholder_tabla = st.container()

def cargar_datos():
    if not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
        return pd.DataFrame()
    try:
        df = pd.read_csv(CSV_PATH)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        # Convertir a numérico
        for s, _ in SENSORES:
            if s in df.columns:
                df[s] = pd.to_numeric(df[s], errors="coerce")
        return df
    except Exception as e:
        # Si justo están escribiendo, reintenta en breve
        time.sleep(0.2)
        try:
            df = pd.read_csv(CSV_PATH)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            for s, _ in SENSORES:
                if s in df.columns:
                    df[s] = pd.to_numeric(df[s], errors="coerce")
            return df
        except:
            return pd.DataFrame()

def graficar_sensor(df, short, label):
    fig = px.line(df, x="timestamp", y=short, title=label,
                  line_shape="spline", color_discrete_sequence=["#2E8B57"])
    if short in UMBRAL:
        umbral = UMBRAL[short]
        fig.add_hline(y=umbral, line_dash="dash", line_color="red", annotation_text=f"Umbral {umbral}")
        mask = df[short] > umbral
        if mask.any():
            fig.add_scatter(
                x=df.loc[mask, "timestamp"],
                y=df.loc[mask, short],
                mode="markers",
                marker=dict(color="red", size=8),
                name="Fuera de lo normal"
            )
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Tiempo",
        yaxis_title=label,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#f3f3f3")
    return fig

# Bucle de refresco (no bloqueante para el usuario)
while True:
    df = cargar_datos()

    if df.empty:
        st.info("Aún no hay datos. Ejecuta el simulador para iniciar el flujo en tiempo real…")
    else:
        # Alertas en vivo
        ultimo = df.iloc[-1]
        with placeholder_alertas:
            st.subheader("🚨 Alertas en vivo")
            cols = st.columns(3)
            for i, (short, label) in enumerate(SENSORES):
                if short not in df.columns: 
                    continue
                val = ultimo[short]
                if pd.isna(val):
                    texto = f"⛔ {label}: sin dato"
                elif val > UMBRAL[short]:
                    texto = f"🔴 {label}: {val} > {UMBRAL[short]} (FUERA DE LO NORMAL)"
                else:
                    texto = f"🟢 {label}: {val} ≤ {UMBRAL[short]} (NORMAL)"
                cols[i % 3].markdown(f"**{texto}**")

        # Gráficos
        with placeholder_graficos:
            st.subheader("📈 Gráficos por sensor")
            grid = st.columns(3)
            for i, (short, label) in enumerate(SENSORES):
                if short in df.columns:
                    grid[i % 3].plotly_chart(graficar_sensor(df, short, label), use_container_width=True)

        # Tabla
        if mostrar_tabla:
            with placeholder_tabla:
                st.subheader("🧾 Histórico reciente")
                st.dataframe(df.tail(50), use_container_width=True)

        # Leyenda
        st.subheader("📘 Leyenda de umbrales")
        leyenda = pd.DataFrame({
            "Sensor": [lbl for _, lbl in SENSORES],
            "Umbral Máximo Permitido": [UMBRAL[s] for s, _ in SENSORES]
        })
        st.table(leyenda)

    st.caption(f"🔁 Auto-actualizando cada {refresh_secs} s…")
    time.sleep(refresh_secs)
    st.rerun()
