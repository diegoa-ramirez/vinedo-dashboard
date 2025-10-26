# ==============================================================
#  SIMULACIÓN DEL ROBOT EN EL VIÑEDO + REPORTE EXCEL PROFESIONAL
#  (Incluye gráficos individuales, leyenda, celdas ajustadas)
# ==============================================================

import pygame
import time
import random
import requests
import pandas as pd
import os
from datetime import datetime

# --------------------------------------------------------------
# CONFIGURACIÓN DE THINGSPEAK
# --------------------------------------------------------------
API_KEY = "TU_API_KEY_AQUI"  # ⚠️ Reemplaza con tu Write API Key
URL = "https://api.thingspeak.com/update"

# --------------------------------------------------------------
# PARÁMETROS GENERALES DEL TERRENO Y UMBRALES
# --------------------------------------------------------------
FILAS, COLUMNAS = 4, 5
ROBOT_PX = (90, 90)

UMBRAL_HUMEDAD_SUELO = 35
UMBRAL_TEMP_SUELO = 33
UMBRAL_PH_SUELO = 7.5
UMBRAL_HUMEDAD_AIRE = 85
UMBRAL_TEMP_AIRE = 35
UMBRAL_RADIACION = 45000

# --------------------------------------------------------------
# FUNCIONES DE SIMULACIÓN Y ALERTA
# --------------------------------------------------------------
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
    if d["temperatura_suelo"] > UMBRAL_TEMP_SUELO:    tipos.append("Temperatura Suelo")
    if d["ph_suelo"]          > UMBRAL_PH_SUELO:      tipos.append("pH Suelo")
    if d["humedad_aire"]      > UMBRAL_HUMEDAD_AIRE:  tipos.append("Humedad Aire")
    if d["temperatura_aire"]  > UMBRAL_TEMP_AIRE:     tipos.append("Temperatura Aire")
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

# --------------------------------------------------------------
# VISUALIZACIÓN CON PYGAME
# --------------------------------------------------------------
pygame.init()
pygame.display.set_caption("Simulación robot viñedo (con Excel final)")

fondo = pygame.image.load("fondo_vinedo.png")
robot_img = pygame.image.load("robot.png")

ANCHO, ALTO = fondo.get_width(), fondo.get_height()
ventana = pygame.display.set_mode((ANCHO, ALTO))
robot_img = pygame.transform.scale(robot_img, ROBOT_PX)

CELDA_ANCHO = ANCHO // COLUMNAS
CELDA_ALTO = ALTO // FILAS

colores_matriz = [[None for _ in range(COLUMNAS)] for _ in range(FILAS)]

# --------------------------------------------------------------
# SIMULACIÓN
# --------------------------------------------------------------
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
            ventana.blit(fondo, (0, 0))

            # Dibujar alertas
            for f in range(FILAS):
                for c in range(COLUMNAS):
                    if colores_matriz[f][c] == "rojo":
                        rect = pygame.Surface((CELDA_ANCHO, CELDA_ALTO), pygame.SRCALPHA)
                        rect.fill((255, 0, 0, 110))
                        ventana.blit(rect, (c * CELDA_ANCHO, f * CELDA_ALTO))

            # Posición robot
            rx = col * CELDA_ANCHO + (CELDA_ANCHO - ROBOT_PX[0]) // 2
            ry = fila * CELDA_ALTO + (CELDA_ALTO - ROBOT_PX[1]) // 2
            ventana.blit(robot_img, (rx, ry))
            pygame.display.update()

            # Sensores
            datos = generar_datos()
            tipos_alerta = evaluar_alertas(datos)
            print(f"📍 Fila {fila+1}, Columna {col+1} → {datos} | Alertas: {', '.join(tipos_alerta) if tipos_alerta else 'Ninguna'}")
            enviar_thingspeak(datos)

            if tipos_alerta:
                colores_matriz[fila][col] = "rojo"

            recorrido.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fila": fila+1,
                "columna": col+1,
                **datos,
                "alerta": "FUERA DE LO NORMAL" if tipos_alerta else "NORMAL",
                "tipo_alerta": ", ".join(tipos_alerta)
            })
            time.sleep(1.2)
        direccion *= -1
    corriendo = False

pygame.quit()
print("\n✅ Recorrido completo. Generando Excel...")

# --------------------------------------------------------------
# CREACIÓN DEL EXCEL PROFESIONAL
# --------------------------------------------------------------
df = pd.DataFrame(recorrido)

out_file = "Reporte_Vinedo.xlsx"
with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
    wb = writer.book
    fmt_hdr = wb.add_format({"bold": True, "bg_color": "#1F4E78", "font_color": "white", "border":1, "align":"center"})
    fmt_cell = wb.add_format({"border":1})
    fmt_red = wb.add_format({"bg_color": "#FFC7CE", "font_color":"#9C0006"})
    fmt_green = wb.add_format({"bg_color": "#C6EFCE", "font_color":"#006100"})
    fmt_title = wb.add_format({"bold": True, "font_size": 14})

    # --- HOJA 1: Datos ---
    df.to_excel(writer, sheet_name="Datos", index=False)
    ws = writer.sheets["Datos"]

    # Encabezado bonito
    ws.write_row(0, 0, df.columns.tolist(), fmt_hdr)
    ws.set_column("A:A", 19)
    ws.set_column("B:C", 9)
    ws.set_column("D:I", 20)
    ws.set_column("J:J", 22)
    ws.set_column("K:K", 40)

    # Bordes
    ws.conditional_format(0, 0, len(df), len(df.columns)-1, {"type": "no_blanks", "format": fmt_cell})

    # Colorear alertas
    ws.conditional_format("J2:J{}".format(len(df)+1),
        {"type": "cell", "criteria": "==", "value": '"FUERA DE LO NORMAL"', "format": fmt_red})
    ws.conditional_format("J2:J{}".format(len(df)+1),
        {"type": "cell", "criteria": "==", "value": '"NORMAL"', "format": fmt_green})

    # Crear gráficos individuales
    sensores = {
        "Humedad Suelo (%)": "D",
        "Temperatura Suelo (°C)": "E",
        "pH Suelo": "F",
        "Humedad Aire (%)": "G",
        "Temperatura Aire (°C)": "H",
        "Radiación (lux)": "I",
    }
    ws.write(1, 12, "Gráficos individuales de sensores", fmt_title)
    row_graph = 3
    for name, col in sensores.items():
        chart = wb.add_chart({"type": "line"})
        chart.add_series({
            "name": name,
            "categories": ["Datos", 1, 0, len(df), 0],
            "values": ["Datos", 1, ord(col)-65, len(df), ord(col)-65],
        })
        chart.set_title({"name": name})
        chart.set_legend({"none": True})
        chart.set_y_axis({"major_gridlines": {"visible": False}})
        ws.insert_chart(f"M{row_graph}", chart, {"x_scale": 1.1, "y_scale": 1.1})
        row_graph += 17  # espacio entre gráficos

    # Leyenda de rangos normales
    ws.write(row_graph + 2, 12, "Leyenda de valores normales", fmt_title)
    leyenda = [
        ["Humedad Suelo", "10 - 35 %"],
        ["Temperatura Suelo", "15 - 33 °C"],
        ["pH Suelo", "5.5 - 7.5"],
        ["Humedad Aire", "40 - 85 %"],
        ["Temperatura Aire", "15 - 35 °C"],
        ["Radiación", "0 - 45,000 lux"]
    ]
    ws.write_row(row_graph + 4, 12, ["Sensor", "Rango normal"], fmt_hdr)
    for i, (sensor, rango) in enumerate(leyenda):
        ws.write_row(row_graph + 5 + i, 12, [sensor, rango], fmt_cell)

    # --- HOJA 2: Resumen ---
    tipos = ["Humedad Suelo", "Temperatura Suelo", "pH Suelo",
             "Humedad Aire", "Temperatura Aire", "Radiación"]
    conteos = {t: sum(df["tipo_alerta"].str.contains(t, na=False)) for t in tipos}
    df_resumen = pd.DataFrame({"Sensor": tipos, "Alertas": [conteos[t] for t in tipos]})
    df_resumen["Estado general"] = df_resumen["Alertas"].apply(
        lambda n: "FUERA DE LO NORMAL" if n >= 1 else "NORMAL"
    )
    df_resumen.to_excel(writer, sheet_name="Resumen", index=False)
    ws2 = writer.sheets["Resumen"]

    ws2.write_row(0, 0, df_resumen.columns.tolist(), fmt_hdr)
    ws2.set_column("A:A", 22)
    ws2.set_column("B:B", 12)
    ws2.set_column("C:C", 25)

    ws2.conditional_format("C2:C{}".format(len(df_resumen)+1),
        {"type": "cell", "criteria": "==", "value": '"FUERA DE LO NORMAL"', "format": fmt_red})
    ws2.conditional_format("C2:C{}".format(len(df_resumen)+1),
        {"type": "cell", "criteria": "==", "value": '"NORMAL"', "format": fmt_green})

    # Gráfico de barras de alertas
    bar = wb.add_chart({"type": "column"})
    bar.add_series({
        "name": "Alertas",
        "categories": ["Resumen", 1, 0, len(df_resumen), 0],
        "values": ["Resumen", 1, 1, len(df_resumen), 1],
        "data_labels": {"value": True}
    })
    bar.set_title({"name": "Alertas por sensor"})
    bar.set_y_axis({"major_gridlines": {"visible": False}})
    ws2.insert_chart("E2", bar, {"x_scale": 1.2, "y_scale": 1.1})

# Abrir el archivo Excel automáticamente
try:
    if os.name == "nt":
        os.startfile(out_file)
except Exception:
    pass

print(f"📁 Reporte generado: {out_file}")
print("✅ Listo para presentación.")
