# ==============================================================
#  SIMULADOR ROBOT VIÑEDO (LOCAL, SIN THINGSPEAK)
#  - Recorre la matriz 4x5 con Pygame
#  - Genera datos de 6 sensores
#  - Escribe cada lectura en "datos.csv" en tiempo real
#  - (Opcional) Genera un Excel al finalizar con gráficos/alertas
# ==============================================================

import pygame
import time
import random
import csv
import os
from datetime import datetime
import pandas as pd

# ------------------ Parámetros ------------------
FILAS, COLUMNAS = 4, 5
ROBOT_PX = (90, 90)
CSV_PATH = "datos.csv"
GENERAR_EXCEL_AL_FINAL = True  # Cambia a False si no quieres Excel

# Umbrales
UMBRAL = {
    "humedad_suelo": 35,
    "temperatura_suelo": 33,
    "ph_suelo": 7.5,
    "humedad_aire": 85,
    "temperatura_aire": 35,
    "radiacion": 45000
}

# ------------------ Funciones -------------------
def generar_datos():
    return {
        "humedad_suelo": round(random.uniform(10, 40), 2),
        "temperatura_suelo": round(random.uniform(15, 35), 2),
        "ph_suelo": round(random.uniform(5.5, 8.0), 2),
        "humedad_aire": round(random.uniform(40, 90), 2),
        "temperatura_aire": round(random.uniform(15, 35), 2),
        "radiacion": round(random.uniform(0, 50000), 2)
    }

def evaluar_alerta(d):
    tipos = []
    if d["humedad_suelo"] > UMBRAL["humedad_suelo"]: tipos.append("Humedad Suelo")
    if d["temperatura_suelo"] > UMBRAL["temperatura_suelo"]: tipos.append("Temperatura Suelo")
    if d["ph_suelo"] > UMBRAL["ph_suelo"]: tipos.append("pH Suelo")
    if d["humedad_aire"] > UMBRAL["humedad_aire"]: tipos.append("Humedad Aire")
    if d["temperatura_aire"] > UMBRAL["temperatura_aire"]: tipos.append("Temperatura Aire")
    if d["radiacion"] > UMBRAL["radiacion"]: tipos.append("Radiación")
    return "FUERA DE LO NORMAL" if tipos else "NORMAL", ", ".join(tipos)

def asegurar_csv_con_header(path):
    existe = os.path.exists(path)
    if not existe or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "timestamp",
                "fila", "columna",
                "humedad_suelo", "temperatura_suelo", "ph_suelo",
                "humedad_aire", "temperatura_aire", "radiacion",
                "alerta", "tipo_alerta"
            ])

def anexar_csv(path, fila_dict):
    # Escribe una fila y hace flush para que Streamlit la vea de inmediato
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            fila_dict["timestamp"],
            fila_dict["fila"], fila_dict["columna"],
            fila_dict["humedad_suelo"], fila_dict["temperatura_suelo"], fila_dict["ph_suelo"],
            fila_dict["humedad_aire"], fila_dict["temperatura_aire"], fila_dict["radiacion"],
            fila_dict["alerta"], fila_dict["tipo_alerta"]
        ])
        f.flush()

# ------------------ Pygame ----------------------
pygame.init()
pygame.display.set_caption("Simulación robot viñedo (local, tiempo real)")

fondo = pygame.image.load("fondo_vinedo.png")
robot_img = pygame.image.load("robot.png")

ANCHO, ALTO = fondo.get_width(), fondo.get_height()
ventana = pygame.display.set_mode((ANCHO, ALTO))
robot_img = pygame.transform.scale(robot_img, ROBOT_PX)

CELDA_ANCHO = ANCHO // COLUMNAS
CELDA_ALTO = ALTO // FILAS
colores_matriz = [[None for _ in range(COLUMNAS)] for _ in range(FILAS)]

asegurar_csv_con_header(CSV_PATH)

recorrido = []
direccion = 1
corriendo = True

print("🚜 Iniciando simulación local… (mirar dashboard Streamlit)")
while corriendo:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            corriendo = False

    for fila in range(FILAS):
        rango = range(COLUMNAS) if direccion == 1 else reversed(range(COLUMNAS))
        for col in rango:
            # Dibujo fondo y celdas con alerta previa
            ventana.blit(fondo, (0, 0))
            for f in range(FILAS):
                for c in range(COLUMNAS):
                    if colores_matriz[f][c] == "rojo":
                        s = pygame.Surface((CELDA_ANCHO, CELDA_ALTO), pygame.SRCALPHA)
                        s.fill((255, 0, 0, 110))
                        ventana.blit(s, (c * CELDA_ANCHO, f * CELDA_ALTO))

            # Posicionar robot
            rx = col * CELDA_ANCHO + (CELDA_ANCHO - ROBOT_PX[0]) // 2
            ry = fila * CELDA_ALTO + (CELDA_ALTO - ROBOT_PX[1]) // 2
            ventana.blit(robot_img, (rx, ry))
            pygame.display.update()

            # Sensores y alerta
            datos = generar_datos()
            estado, tipos = evaluar_alerta(datos)
            if estado == "FUERA DE LO NORMAL":
                colores_matriz[fila][col] = "rojo"

            fila_csv = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fila": fila + 1,
                "columna": col + 1,
                **datos,
                "alerta": estado,
                "tipo_alerta": tipos
            }
            recorrido.append(fila_csv)

            # Escribir en CSV y avisar por consola
            anexar_csv(CSV_PATH, fila_csv)
            print(f"📍 ({fila+1},{col+1}) → {datos} | {estado} {f'[{tipos}]' if tipos else ''}")

            # Ritmo de la simulación (ajusta si quieres más rápido/lento)
            time.sleep(1.0)
        direccion *= -1
    corriendo = False

pygame.quit()
print("\n✅ Simulación finalizada.")

# ------------------ Excel opcional ----------------
if GENERAR_EXCEL_AL_FINAL:
    print("📄 Generando Excel…")
    df = pd.DataFrame(recorrido)
    out_file = "Reporte_Vinedo.xlsx"
    with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
        wb = writer.book
        fmt_hdr = wb.add_format({"bold": True, "bg_color": "#1F4E78", "font_color": "white", "border":1, "align":"center"})
        fmt_cell = wb.add_format({"border":1})
        fmt_red = wb.add_format({"bg_color": "#FFC7CE", "font_color":"#9C0006"})
        fmt_green = wb.add_format({"bg_color": "#C6EFCE", "font_color":"#006100"})
        fmt_title = wb.add_format({"bold": True, "font_size": 14})

        # Hoja Datos
        df.to_excel(writer, sheet_name="Datos", index=False)
        ws = writer.sheets["Datos"]
        ws.write_row(0, 0, df.columns.tolist(), fmt_hdr)
        ws.set_column("A:A", 19)
        ws.set_column("B:C", 9)
        ws.set_column("D:I", 18)
        ws.set_column("J:J", 22)
        ws.set_column("K:K", 40)
        ws.conditional_format("J2:J{}".format(len(df)+1), {"type":"text","criteria":"containing","value":"NORMAL","format":fmt_green})
        ws.conditional_format("J2:J{}".format(len(df)+1), {"type":"text","criteria":"containing","value":"FUERA","format":fmt_red})

        # Gráficos individuales (verde normal + puntos rojos + línea de umbral)
        sensores = [
            ("humedad_suelo",      "Humedad Suelo (%)",      UMBRAL["humedad_suelo"]),
            ("temperatura_suelo",  "Temperatura Suelo (°C)", UMBRAL["temperatura_suelo"]),
            ("ph_suelo",           "pH Suelo",               UMBRAL["ph_suelo"]),
            ("humedad_aire",       "Humedad Aire (%)",       UMBRAL["humedad_aire"]),
            ("temperatura_aire",   "Temperatura Aire (°C)",  UMBRAL["temperatura_aire"]),
            ("radiacion",          "Radiación (lux)",        UMBRAL["radiacion"]),
        ]

        ws.write(1, 12, "Gráficos individuales con umbral", fmt_title)
        row_graph = 3
        for col_name, label, umbral in sensores:
            cidx = df.columns.get_loc(col_name)
            chart = wb.add_chart({"type": "scatter", "subtype":"straight_with_markers"})
            # Línea tendencia (verde)
            chart.add_series({
                "name": f"{label} (Normal)",
                "categories": ["Datos", 1, 0, len(df), 0],
                "values": ["Datos", 1, cidx, len(df), cidx],
                "marker": {"type":"circle","size":5,"border":{"color":"green"},"fill":{"color":"green"}},
                "line": {"color": "#70AD47"}
            })
            # Línea umbral
            umbral_col = f"umbral_{col_name}"
            df[umbral_col] = umbral
            uidx = df.columns.get_loc(umbral_col)
            chart.add_series({
                "name": "Umbral",
                "categories": ["Datos", 1, 0, len(df), 0],
                "values": ["Datos", 1, uidx, len(df), uidx],
                "line": {"color": "red", "dash_type":"dash"}
            })
            chart.set_title({"name": label})
            chart.set_style(10)
            chart.set_size({"width": 600, "height": 300})
            chart.set_legend({"position":"bottom"})
            chart.set_y_axis({"major_gridlines":{"visible": False}})
            ws.insert_chart(f"M{row_graph}", chart)
            row_graph += 17

    try:
        if os.name == "nt":
            os.startfile(out_file)
    except:
        pass
    print(f"✅ Excel generado: {out_file}")

print("🏁 Listo. Puedes cerrar esta ventana.")
