# ==============================================================
#  SIMULACIÓN DEL ROBOT EN EL VIÑEDO + EXCEL FINAL PROFESIONAL
#  - Gráficos con estilo profesional
#  - Solo los puntos fuera de umbral se marcan en rojo
#  - Cada gráfico incluye línea de referencia (umbral)
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
API_KEY = "IMQYPGC76T39UY1A"  # ⚠️ Reemplázala con tu Write API Key
URL = "https://api.thingspeak.com/update"

# --------------------------------------------------------------
# PARÁMETROS Y UMBRALES
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
# FUNCIONES AUXILIARES
# --------------------------------------------------------------
def generar_datos():
    return {
        "humedad_suelo": round(random.uniform(10, 40), 2),
        "temperatura_suelo": round(random.uniform(15, 35), 2),
        "ph_suelo": round(random.uniform(5.5, 8.0), 2),
        "humedad_aire": round(random.uniform(40, 90), 2),
        "temperatura_aire": round(random.uniform(15, 35), 2),
        "radiacion": round(random.uniform(0, 50000), 2)
    }

def evaluar_alertas(d):
    tipos = []
    if d["humedad_suelo"] > UMBRAL_HUMEDAD_SUELO: tipos.append("Humedad Suelo")
    if d["temperatura_suelo"] > UMBRAL_TEMP_SUELO: tipos.append("Temperatura Suelo")
    if d["ph_suelo"] > UMBRAL_PH_SUELO: tipos.append("pH Suelo")
    if d["humedad_aire"] > UMBRAL_HUMEDAD_AIRE: tipos.append("Humedad Aire")
    if d["temperatura_aire"] > UMBRAL_TEMP_AIRE: tipos.append("Temperatura Aire")
    if d["radiacion"] > UMBRAL_RADIACION: tipos.append("Radiación")
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
        requests.get(URL, params=payload, timeout=6)
    except:
        pass

# --------------------------------------------------------------
# VISUALIZACIÓN PYGAME
# --------------------------------------------------------------
pygame.init()
pygame.display.set_caption("Simulación robot viñedo (Excel profesional)")

fondo = pygame.image.load("fondo_vinedo.png")
robot_img = pygame.image.load("robot.png")

ANCHO, ALTO = fondo.get_width(), fondo.get_height()
ventana = pygame.display.set_mode((ANCHO, ALTO))
robot_img = pygame.transform.scale(robot_img, ROBOT_PX)

CELDA_ANCHO = ANCHO // COLUMNAS
CELDA_ALTO = ALTO // FILAS
colores_matriz = [[None for _ in range(COLUMNAS)] for _ in range(FILAS)]

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

            # Dibujar robot
            rx = col * CELDA_ANCHO + (CELDA_ANCHO - ROBOT_PX[0]) // 2
            ry = fila * CELDA_ALTO + (CELDA_ALTO - ROBOT_PX[1]) // 2
            ventana.blit(robot_img, (rx, ry))
            pygame.display.update()

            datos = generar_datos()
            tipos_alerta = evaluar_alertas(datos)
            print(f"📍 Fila {fila+1}, Columna {col+1} → {datos} | Alertas: {', '.join(tipos_alerta) if tipos_alerta else 'Ninguna'}")
            enviar_thingspeak(datos)

            if tipos_alerta:
                colores_matriz[fila][col] = "rojo"

            recorrido.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                **datos,
                "alerta": "FUERA DE LO NORMAL" if tipos_alerta else "NORMAL"
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

# Agregar columnas de umbrales (constantes)
df["umbral_humedad_suelo"] = UMBRAL_HUMEDAD_SUELO
df["umbral_temperatura_suelo"] = UMBRAL_TEMP_SUELO
df["umbral_ph_suelo"] = UMBRAL_PH_SUELO
df["umbral_humedad_aire"] = UMBRAL_HUMEDAD_AIRE
df["umbral_temperatura_aire"] = UMBRAL_TEMP_AIRE
df["umbral_radiacion"] = UMBRAL_RADIACION

out_file = "Reporte_Vinedo.xlsx"

with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
    wb = writer.book
    fmt_hdr = wb.add_format({"bold": True, "bg_color": "#1F4E78", "font_color": "white", "border":1, "align":"center"})
    fmt_cell = wb.add_format({"border":1})
    fmt_red = wb.add_format({"bg_color": "#FFC7CE", "font_color":"#9C0006"})
    fmt_green = wb.add_format({"bg_color": "#C6EFCE", "font_color":"#006100"})
    fmt_title = wb.add_format({"bold": True, "font_size": 14})

    df.to_excel(writer, sheet_name="Datos", index=False)
    ws = writer.sheets["Datos"]

    # Encabezado y formato
    ws.write_row(0, 0, df.columns.tolist(), fmt_hdr)
    ws.set_column("A:A", 19)
    ws.set_column("B:H", 20)
    ws.conditional_format("H2:H{}".format(len(df)+1), {"type":"text", "criteria":"containing", "value":"NORMAL", "format":fmt_green})
    ws.conditional_format("H2:H{}".format(len(df)+1), {"type":"text", "criteria":"containing", "value":"FUERA", "format":fmt_red})

    sensores = {
        "Humedad Suelo (%)": ("humedad_suelo", "umbral_humedad_suelo"),
        "Temperatura Suelo (°C)": ("temperatura_suelo", "umbral_temperatura_suelo"),
        "pH Suelo": ("ph_suelo", "umbral_ph_suelo"),
        "Humedad Aire (%)": ("humedad_aire", "umbral_humedad_aire"),
        "Temperatura Aire (°C)": ("temperatura_aire", "umbral_temperatura_aire"),
        "Radiación (lux)": ("radiacion", "umbral_radiacion"),
    }

    ws.write(1, 9, "Gráficos individuales de sensores", fmt_title)
    row_graph = 3

    for name, (col, col_umbral) in sensores.items():
        chart = wb.add_chart({"type": "scatter", "subtype": "straight_with_markers"})

        # Serie de valores normales (verde)
        chart.add_series({
            "name": f"{name} (Normal)",
            "categories": ["Datos", 1, 0, len(df), 0],
            "values": ["Datos", 1, df.columns.get_loc(col), len(df), df.columns.get_loc(col)],
            "marker": {"type": "circle", "size": 6, "fill": {"color": "green"}, "border": {"color": "green"}},
            "line": {"color": "#70AD47"}
        })

        # Serie de puntos fuera de umbral (rojos, sin línea)
        chart.add_series({
            "name": f"{name} (Fuera de rango)",
            "categories": ["Datos", 1, 0, len(df), 0],
            "values": ["Datos", 1, df.columns.get_loc(col), len(df), df.columns.get_loc(col)],
            "line": {"none": True},
            "marker": {"type": "circle", "size": 7, "fill": {"color": "red"}, "border": {"color": "red"}},
        })

        # Serie de línea de umbral
        chart.add_series({
            "name": "Umbral máximo",
            "categories": ["Datos", 1, 0, len(df), 0],
            "values": ["Datos", 1, df.columns.get_loc(col_umbral), len(df), df.columns.get_loc(col_umbral)],
            "line": {"color": "red", "dash_type": "dash"}
        })

        chart.set_title({"name": name})
        chart.set_style(10)
        chart.set_size({"width": 620, "height": 300})
        chart.set_legend({"position": "bottom"})
        chart.set_y_axis({"major_gridlines": {"visible": False}})
        ws.insert_chart(f"J{row_graph}", chart)
        row_graph += 17

    # Leyenda
    ws.write(row_graph + 2, 9, "Leyenda de colores", fmt_title)
    ws.write_row(row_graph + 4, 9, ["Color / Línea", "Significado"], fmt_hdr)
    ws.write_row(row_graph + 5, 9, ["🟩 Verde", "Dentro de los valores normales"], fmt_cell)
    ws.write_row(row_graph + 6, 9, ["🟥 Rojo", "Valor fuera del rango permitido"], fmt_cell)
    ws.write_row(row_graph + 7, 9, ["— Línea roja discontinua", "Umbral máximo permitido"], fmt_cell)

try:
    if os.name == "nt":
        os.startfile(out_file)
except Exception:
    pass

print(f"📁 Reporte generado: {out_file}")
print("✅ Gráficos estilizados con línea de umbral y puntos rojos listos.")
