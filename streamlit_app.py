# ==============================================================
#  DASHBOARD EN TIEMPO REAL - VIÑEDO (Streamlit Cloud)
#  - Lee de ThingSpeak (canal + read key)
#  - 6 gráficos con umbral y puntos rojos al exceder
#  - Panel de alertas, tabla histórica y leyenda
# ==============================================================

import os
import time
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# ---------- Configuración de página ----------
st.set_page_config(page_title="Viñedo - Dashboard IoT", layout="wide")

# ---------- Secrets ----------
CHANNEL_ID = st.secrets.get("THINGSPEAK_CHANNEL_ID", "")
READ_KEY   = st.secrets.get("THINGSPEAK_READ_API_KEY", "")

UMBRAL_HUMEDAD_SUELO = float(st.secrets.get("UMBRAL_HUMEDAD_SUELO", 35))
UMBRAL_TEMP_SUELO    = float(st.secrets.get("UMBRAL_TEMP_SUELO", 33))
UMBRAL_PH_SUELO      = float(st.secrets.get("UMBRAL_PH_SUELO", 7.5))
UMBRAL_HUMEDAD_AIRE  = float(st.secrets.get("UMBRAL_HUMEDAD_AIRE", 85))
UMBRAL_TEMP_AIRE     = float(st.secrets.get("UMBRAL_TEMP_AIRE", 35))
UMBRAL_RADIACION     = float(st.secrets.get("UMBRAL_RADIACION", 45000))

REFRESH_SECS         = int(st.secrets.get("REFRESH_SECS", 10))

# ---------- Parámetros del canal ----------
SENSORES = {
    "field1": ("humedad_suelo",       "Humedad Suelo (%)",        UMBRAL_HUMEDAD_SUELO),
    "field2": ("temperatura_suelo",   "Temperatura Suelo (°C)",   UMBRAL_TEMP_SUELO),
    "field3": ("ph_suelo",            "pH Suelo",                 UMBRAL_PH_SUELO),
    "field4": ("humedad_aire",        "Humedad Aire (%)",         UMBRAL_HUMEDAD_AIRE),
    "field5": ("temperatura_aire",    "Temperatura Aire (°C)",    UMBRAL_TEMP_AIRE),
    "field6": ("radiacion",           "Radiación (lux)",          UMBRAL_RADIACION),
}

# ---------- UI: Header ----------
st.title("🌱 Dashboard en tiempo real - Viñedo")
st.caption("Visualización profesional de 6 sensores con umbrales y alertas.")

# ---------- Función: Descargar datos ThingSpeak ----------
@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def cargar_thingspeak(channel_id: str, read_key: str, results: int = 8000) -> pd.DataFrame:
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"
    params = {"results": results}
    if read_key:
        params["api_key"] = read_key
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    feeds = data.get("feeds", [])
    if not feeds:
        return pd.DataFrame()
    df = pd.DataFrame(feeds)
    rename_map = {}
    for k, (short, _, _) in SENSORES.items():
        if k in df.columns:
            rename_map[k] = short
    df = df.rename(columns=rename_map)
    if "created_at" in df.columns:
        df["timestamp"] = pd.to_datetime(df["created_at"])
    else:
        df["timestamp"] = pd.to_datetime(df.index)
    for short, _, _ in SENSORES.values():
        if short in df.columns:
            df[short] = pd.to_numeric(df[short], errors="coerce")
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df[["timestamp"] + [v[0] for v in SENSORES.values() if v[0] in df.columns]]

# ---------- Cargar datos ----------
if not CHANNEL_ID:
    st.error("Falta configurar `THINGSPEAK_CHANNEL_ID` en Secrets de Streamlit.")
    st.stop()

try:
    df = cargar_thingspeak(CHANNEL_ID, READ_KEY)
except Exception as e:
    st.error(f"Error al leer ThingSpeak: {e}")
    st.stop()

if df.empty:
    st.info("Aún no hay datos. Esperando lecturas del simulador…")
    st.stop()

# ---------- Panel de alertas ----------
st.subheader("🚨 Alertas en vivo")
alert_cols = st.columns(3)
ultimo = df.iloc[-1]

for i, (short, label, umbral) in enumerate(SENSORES.values()):
    if short not in df.columns:
        continue
    valor = ultimo[short]
    if pd.isna(valor):
        texto = f"⛔ {label}: sin dato"
        color = "gray"
    elif valor > umbral:
        texto = f"🔴 {label}: {valor} > {umbral} (FUERA DE LO NORMAL)"
        color = "red"
    else:
        texto = f"🟢 {label}: {valor} ≤ {umbral} (NORMAL)"
        color = "green"
    alert_cols[i % 3].markdown(f"**{texto}**")

# ---------- Gráficos ----------
st.subheader("📈 Gráficos de sensores")
grid = st.columns(3)

def grafico_sensor(df_sensor, short, label, umbral):
    fig = px.line(df_sensor, x="timestamp", y=short, title=label,
                  line_shape="spline", color_discrete_sequence=["#2E8B57"])
    fig.add_hline(y=umbral, line_dash="dash", line_color="red",
                  annotation_text=f"Umbral {umbral}")
    mask = df_sensor[short] > umbral
    if mask.any():
        fig.add_scatter(x=df_sensor.loc[mask, "timestamp"],
                        y=df_sensor.loc[mask, short],
                        mode="markers",
                        marker=dict(color="red", size=8),
                        name="Fuera de lo normal")
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Tiempo",
        yaxis_title=label,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    return fig

i = 0
for short, label, umbral in SENSORES.values():
    if short not in df.columns:
        continue
    grid[i % 3].plotly_chart(grafico_sensor(df, short, label, umbral), use_container_width=True)
    i += 1

# ---------- Tabla histórica ----------
st.subheader("🧾 Histórico reciente")
st.dataframe(df.tail(50), use_container_width=True)

# ---------- Leyenda ----------
st.subheader("📘 Leyenda de umbrales")
leyenda = pd.DataFrame({
    "Sensor": [v[1] for v in SENSORES.values()],
    "Umbral Máximo Permitido": [v[2] for v in SENSORES.values()]
})
st.table(leyenda)

st.caption(f"🔁 Actualizando cada {REFRESH_SECS} segundos")
time.sleep(REFRESH_SECS)
st.experimental_rerun()
