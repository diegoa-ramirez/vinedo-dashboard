# ==============================================================
#  SIMULACIÓN DEL ROBOT EN EL VIÑEDO CON ALERTAS VISUALES
#  - Cada celda del viñedo se vuelve roja si el sensor supera un umbral
# ==============================================================

import pygame
import time
import random
import requests
import pandas as pd

# --------------------------------------------------------------
# CONFIGURACIÓN DE THINGSPEAK
# --------------------------------------------------------------
API_KEY = "IMQYPGC76T39UY1A"   # ⚠️ Reemplaza con tu clave real
URL = "https://api.thingspeak.com/update"

def generar_datos():
    """Genera datos simulados de sensores."""
    return {
        "humedad_suelo": round(random.uniform(10, 40), 2),
        "temperatura_suelo": round(random.uniform(15, 35), 2),
        "ph_suelo": round(random.uniform(5.5, 8.0), 2),
        "humedad_aire": round(random.uniform(40, 90), 2),
        "temperatura_aire": round(random.uniform(15, 35), 2),
        "radiacion": round(random.uniform(0, 50000), 2)
    }

def enviar_datos(datos):
    """Envía los datos a ThingSpeak."""
    payload = {
        'api_key': API_KEY,
        'field1': datos["humedad_suelo"],
        'field2': datos["temperatura_suelo"],
        'field3': datos["ph_suelo"],
        'field4': datos["humedad_aire"],
        'field5': datos["temperatura_aire"],
        'field6': datos["radiacion"]
    }
    try:
        r = requests.get(URL, params=payload, timeout=5)
        if r.status_code == 200:
            print("📡 Datos enviados correctamente.")
        else:
            print(f"⚠️ Error al enviar datos ({r.status_code})")
    except:
        print("⚠️ Fallo en la conexión.")

# --------------------------------------------------------------
# CONFIGURACIÓN VISUAL
# --------------------------------------------------------------
pygame.init()
pygame.display.set_caption("Simulación del robot en el viñedo (con alertas)")

# Cargar imágenes
fondo = pygame.image.load("fondo_vinedo.png")
robot_img = pygame.image.load("robot.png")
vid_roja = pygame.image.load("vid_roja.png")  # imagen de una sola vid roja

# Ajustar tamaños
ANCHO, ALTO = fondo.get_width(), fondo.get_height()
ventana = pygame.display.set_mode((ANCHO, ALTO))
robot_img = pygame.transform.scale(robot_img, (90, 90))
vid_roja = pygame.transform.scale(vid_roja, (ANCHO // 5, ALTO // 4))  # 4x5 cuadrantes

# Parámetros del viñedo
FILAS, COLUMNAS = 4, 5
CELDA_ANCHO = ANCHO // COLUMNAS
CELDA_ALTO = ALTO // FILAS

# Umbrales de ejemplo
UMBRAL_HUMEDAD_SUELO = 35
UMBRAL_TEMP_SUELO = 33
UMBRAL_PH_SUELO = 7.5

# Matriz de estado de celdas (False = normal, True = alerta)
alertas_matriz = [[False for _ in range(COLUMNAS)] for _ in range(FILAS)]

# --------------------------------------------------------------
# SIMULACIÓN PRINCIPAL
# --------------------------------------------------------------
recorrido = []
direccion = 1
corriendo = True

print("🚜 Iniciando simulación del robot...\n")

while corriendo:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            corriendo = False

    for fila in range(FILAS):
        rango = range(COLUMNAS) if direccion == 1 else reversed(range(COLUMNAS))
        for col in rango:
            ventana.blit(fondo, (0, 0))

            # Dibujar vides en alerta (superponer rojo donde haya alertas)
            for f in range(FILAS):
                for c in range(COLUMNAS):
                    if alertas_matriz[f][c]:
                        ventana.blit(vid_roja, (c * CELDA_ANCHO, f * CELDA_ALTO))

            # Posición del robot
            robot_x = col * CELDA_ANCHO + (CELDA_ANCHO - 90) // 2
            robot_y = fila * CELDA_ALTO + (CELDA_ALTO - 90) // 2
            ventana.blit(robot_img, (robot_x, robot_y))
            pygame.display.update()

            # Simular lectura y envío
            datos = generar_datos()
            print(f"📍 Fila {fila+1}, Columna {col+1} → {datos}")
            enviar_datos(datos)

            # Verificar umbrales → activar alerta visual
            if (datos["humedad_suelo"] > UMBRAL_HUMEDAD_SUELO or
                datos["temperatura_suelo"] > UMBRAL_TEMP_SUELO or
                datos["ph_suelo"] > UMBRAL_PH_SUELO):
                alertas_matriz[fila][col] = True

            recorrido.append({
                "fila": fila+1,
                "columna": col+1,
                **datos
            })

            time.sleep(1.2)

        direccion *= -1

    corriendo = False

# Guardar CSV con los datos
df = pd.DataFrame(recorrido)
df.to_csv("Recorrido_Vinedo_Alertas.csv", index=False)
print("\n✅ Recorrido completo guardado en 'Recorrido_Vinedo_Alertas.csv'.")
pygame.quit()
