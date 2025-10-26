# ==============================================================
#  SIMULACIÓN DEL ROBOT EN EL VIÑEDO (Pygame) + EXCEL PROFESIONAL
#  - Recorre una cuadrícula 4x5
#  - Colorea celdas en rojo si se exceden umbrales
#  - Envía lecturas a ThingSpeak
#  - Al finalizar: Reporte_Vinedo.xlsx (datos + gráfico + resumen)
# ==============================================================

import pygame
import time
import random
import requests
import pandas as pd
import os
from datetime import datetime

# ------------------ CONFIG THINGSPEAK -------------------------
API_KEY = "IMQYPGC76T39UY1A"   # <-- REEMPLAZA por tu Write API Key
URL = "https://api.thingspeak.com/update"

# ------------------ PARÁMETROS DEL TERRENO --------------------
FILAS, COLUMNAS = 4, 5     # cuadrícula 4x5
ROBOT_PX = (90, 90)        # tamaño del sprite del robot (ajusta a tu fondo)

# ------------------ UMBRALES (edítalos si gustas) -------------
UMBRAL_HUMEDAD_SUELO = 35      # %
UMBRAL_TEMP_SUELO = 33         # °C
UMBRAL_PH_SUELO = 7.5
UMBRAL_HUMEDAD_AIRE = 85       # %
UMBRAL_TEMP_AIRE = 35          # °C
UMBRAL_RADIACION = 45000       # lux

# ------------------ GENERACIÓN DE SENSORES --------------------
def generar_datos():
    return {
        "humedad_suelo":     round(random.uniform(10, 40), 2),
        "temperatura_suelo": round(random.uniform(15, 35), 2),
        "ph_suelo":          round(random.uniform(5.5, 8.0), 2),
        "humedad_aire":      round(random.uniform(40, 90), 2),
        "temperatura_aire":  round(random.uniform(15, 35), 2),
        "radiacion":         round(random.uniform(0, 50000), 2)
    }

def evaluar_alertas(d):
    tipos = []
    if d["humedad_suelo"]     > UMBRAL_HUMEDAD_SUELO: tipos.append("Humedad Suelo")
    if d["temperatura_suelo"] > UMBRAL_TEMP_SUELO:    tipos.append("Temp Suelo")
    if d["ph_suelo"]          > UMBRAL_PH_SUELO:      tipos.append("pH Suelo")
    if d["humedad_aire"]      > UMBRAL_HUMEDAD_AIRE:  tipos.append("Humedad Aire")
    if d["temperatura_aire"]  > UMBRAL_TEMP_AIRE:     tipos.append("Temp Aire")
    if d["radiacion"]         > UMBRAL_RADIACION:     tipos.append("Radiación")
    return tipos

def enviar_thingspeak(d):
    payload = {
        'api_key': API_KEY,
        'field1': d["humedad_suelo"],
        'field2': d["temperatura_suelo"],
        'field3': d["ph_suelo"],
        'field4': d["humedad_aire"],
        'field5': d["temperatura_aire"],
        'field6': d["radiacion"]
    }
    try:
        r = requests.get(URL, params=payload, timeout=6)
        ok = (r.status_code == 200 and r.text.strip() != "0")
        print("📡 Envío TS:", "OK" if ok else f"Error({r.status_code})", "| Entry:", r.text.strip())
    except Exception as e:
        print("⚠️ Error conexión TS:", e)

# ------------------ PYGAME: CARGA VISUAL ----------------------
pygame.init()
pygame.display.set_caption("Simulación robot viñedo (con Excel final)")

fondo = pygame.image.load("fondo_vinedo.png")
robot_img = pygame.image.load("robot.png")
ANCHO, ALTO = fondo.get_width(), fondo.get_height()
ventana = pygame.display.set_mode((ANCHO, ALTO))
robot_img = pygame.transform.scale(robot_img, ROBOT_PX)

CELDA_ANCHO = ANCHO // COLUMNAS
CELDA_ALTO  = ALTO // FILAS

# Matriz de color por alerta (None/ 'rojo')
colores_matriz = [[None for _ in range(COLUMNAS)] for _ in range(FILAS)]

# ------------------ SIMULACIÓN -------------------------------
recorrido = []
direccion = 1
corriendo = True

print("🚜 Iniciando simulación...\n")

while corriendo:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            corriendo = False

    for fila in range(FILAS):
        rango = range(COLUMNAS) if direccion == 1 else reversed(range(COLUMNAS))
        for col in rango:
            # Fondo base
            ventana.blit(fondo, (0, 0))

            # Pintar celdas con alerta (rojo translúcido)
            for f in range(FILAS):
                for c in range(COLUMNAS):
                    if colores_matriz[f][c] == "rojo":
                        rect = pygame.Surface((CELDA_ANCHO, CELDA_ALTO), pygame.SRCALPHA)
                        rect.fill((255, 0, 0, 110))  # RGBA
                        ventana.blit(rect, (c * CELDA_ANCHO, f * CELDA_ALTO))

            # Posicionar robot (centrado en la celda actual)
            rx = col * CELDA_ANCHO + (CELDA_ANCHO - ROBOT_PX[0]) // 2
            ry = fila * CELDA_ALTO  + (CELDA_ALTO  - ROBOT_PX[1]) // 2
            ventana.blit(robot_img, (rx, ry))
            pygame.display.update()

            # Lectura + envío
            datos = generar_datos()
            tipos_alerta = evaluar_alertas(datos)
            print(f"📍 Fila {fila+1}, Columna {col+1} → {datos} | Alertas: {', '.join(tipos_alerta) if tipos_alerta else 'Ninguna'}")
            enviar_thingspeak(datos)

            # Marcar celda si hay alerta
            if tipos_alerta:
                colores_matriz[fila][col] = "rojo"

            # Registrar para el reporte
            recorrido.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fila": fila+1,
                "columna": col+1,
                "humedad_suelo": datos["humedad_suelo"],
                "temperatura_suelo": datos["temperatura_suelo"],
                "ph_suelo": datos["ph_suelo"],
                "humedad_aire": datos["humedad_aire"],
                "temperatura_aire": datos["temperatura_aire"],
                "radiacion": datos["radiacion"],
                "alerta": True if tipos_alerta else False,
                "tipo_alerta": ", ".join(tipos_alerta)
            })

            time.sleep(1.1)  # velocidad de muestreo

        direccion *= -1
    corriendo = False

pygame.quit()
print("\n✅ Recorrido completo. Generando Excel...")

# ------------------ EXCEL PROFESIONAL ------------------------
df = pd.DataFrame(recorrido)

# Totales de alertas por tipo (para Resumen)
tipos = ["Humedad Suelo", "Temp Suelo", "pH Suelo", "Humedad Aire", "Temp Aire", "Radiación"]
conteos = {t: sum(df["tipo_alerta"].str.contains(t, na=False)) for t in tipos}
df_resumen = pd.DataFrame({"Sensor": tipos, "Alertas": [conteos[t] for t in tipos]})
def recomendacion(n):
    if n >= 3: return "🟥 Revisar con prioridad (posible condición fuera de control)."
    if n >= 1: return "🟧 Atención moderada; verificar condiciones."
    return "🟩 Dentro de valores normales."
df_resumen["Recomendación"] = df_resumen["Alertas"].apply(recomendacion)

out_file = "Reporte_Vinedo.xlsx"
with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
    # --- Hoja 1: Datos (tabla + formato + gráfico combinado) ---
    df.to_excel(writer, sheet_name="Datos", index=False)
    wb  = writer.book
    ws  = writer.sheets["Datos"]

    # Formatos
    fmt_hdr = wb.add_format({"bold": True, "bg_color": "#1F4E78", "font_color": "white", "border":1, "align":"center"})
    fmt_cell = wb.add_format({"border":1})
    fmt_bool = wb.add_format({"border":1, "align":"center"})
    fmt_ok   = wb.add_format({"bg_color": "#C6EFCE", "font_color":"#006100"})
    fmt_bad  = wb.add_format({"bg_color": "#FFC7CE", "font_color":"#9C0006"})
    fmt_title= wb.add_format({"bold": True, "font_size": 14})

    # Encabezados bonitos
    ws.write_row(0, 0, df.columns.tolist(), fmt_hdr)
    ws.set_column("A:A", 19)  # timestamp
    ws.set_column("B:C", 9)   # fila, columna
    ws.set_column("D:I", 20)  # sensores
    ws.set_column("J:J", 8)   # alerta
    ws.set_column("K:K", 28)  # tipo alerta

    # Bordes a toda la tabla
    ws.conditional_format(0, 0, len(df), len(df.columns)-1,
                          {"type": "no_blanks", "format": fmt_cell})

    # Semáforo en columna 'alerta'
    ws.conditional_format("J2:J{}".format(len(df)+1),
                          {"type":"cell", "criteria":"==", "value":True, "format":fmt_bad})
    ws.conditional_format("J2:J{}".format(len(df)+1),
                          {"type":"cell", "criteria":"==", "value":False, "format":fmt_ok})

    # Gráfico combinado (todas las series)
    chart = wb.add_chart({"type":"line"})
    last_row = len(df)+1
    series_cols = {
        "Humedad Suelo (%)": "D",
        "Temperatura Suelo (°C)": "E",
        "pH Suelo": "F",
        "Humedad Aire (%)": "G",
        "Temperatura Aire (°C)": "H",
        "Radiación (lux)": "I",
    }
    # para que los nombres de columnas se vean amigables:
    ws.write(0, 3, "Humedad Suelo (%)", fmt_hdr)
    ws.write(0, 4, "Temperatura Suelo (°C)", fmt_hdr)
    ws.write(0, 5, "pH Suelo", fmt_hdr)
    ws.write(0, 6, "Humedad Aire (%)", fmt_hdr)
    ws.write(0, 7, "Temperatura Aire (°C)", fmt_hdr)
    ws.write(0, 8, "Radiación (lux)", fmt_hdr)

    for name, col in series_cols.items():
        chart.add_series({
            "name":       ["Datos", 0, ord(col)-65],
            "categories": ["Datos", 1, 0, last_row-1, 0],   # timestamp
            "values":     ["Datos", 1, ord(col)-65, last_row-1, ord(col)-65],
        })
    chart.set_title({"name":"Evolución de sensores"})
    chart.set_x_axis({"name":"Tiempo"})
    chart.set_y_axis({"name":"Valor medido"})
    chart.set_legend({"position":"bottom"})
    ws.write(1, 12, "Gráfico de sensores", fmt_title)
    ws.insert_chart("M3", chart, {"x_scale":1.1, "y_scale":1.1})

    # --- Hoja 2: Resumen (conteos + recomendaciones + gráfico barras) ---
    df_resumen.to_excel(writer, sheet_name="Resumen", index=False)
    ws2 = writer.sheets["Resumen"]
    ws2.set_column("A:A", 22)
    ws2.set_column("B:B", 12)
    ws2.set_column("C:C", 60)
    ws2.write(0, 0, "Sensor", fmt_hdr)
    ws2.write(0, 1, "Alertas", fmt_hdr)
    ws2.write(0, 2, "Recomendación", fmt_hdr)

    # Barras de datos para 'Alertas'
    ws2.conditional_format("B2:B{}".format(len(df_resumen)+1),
                           {"type":"3_color_scale",
                            "min_color":"#C6EFCE", "mid_color":"#FFEB84", "max_color":"#F4B084"})

    # Gráfico de barras (alertas por sensor)
    bar = wb.add_chart({"type":"column"})
    bar.add_series({
        "name": "Alertas",
        "categories": ["Resumen", 1, 0, len(df_resumen), 0],
        "values":     ["Resumen", 1, 1, len(df_resumen), 1],
        "data_labels":{"value":True}
    })
    bar.set_title({"name":"Alertas por sensor"})
    bar.set_y_axis({"major_gridlines": {"visible": False}})
    bar.set_legend({"none": True})
    ws2.insert_chart("E2", bar, {"x_scale":1.1, "y_scale":1.1})

# Intentar abrir el archivo automáticamente (Windows)
try:
    if os.name == "nt":
        os.startfile(out_file)
except Exception:
    pass

print(f"📁 Reporte generado: {out_file}")
print("✅ Listo para presentar.")
