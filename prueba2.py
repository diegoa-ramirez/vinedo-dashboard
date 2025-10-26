# ==============================================================
#  SIMULACIÓN DEL ROBOT EN EL VIÑEDO (COLOR POR CÓDIGO)
#  - Cada celda se colorea en rojo si se supera un umbral
# ==============================================================

import pygame
import time
import random
import requests
import pandas as pd

# --------------------------------------------------------------
# CONFIGURACIÓN DE THINGSPEAK
# --------------------------------------------------------------
API_KEY = "TU_API_KEY_AQUI"  # ⚠️ Reemplaza por tu Write API Key
URL = "https://api.thingspeak.com/update"

# --------------------------------------------------------------
# FUNCIONES DE SENSORES
# --------------------------------------------------------------
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
# CONFIGURACIÓN VISUAL (Pygame)
# --------------------------------------------------------------
pygame.init()
pygame.display.set_caption("Simulación del robot en el viñedo (alertas por color)")

# Cargar imágenes
fondo = pygame.image.load("fondo_vinedo.png")
robot_img = pygame.image.load("robot.png")

# Tamaño de ventana según el fondo
ANCHO, ALTO = fondo.get_width(), fondo.get_height()
ventana = pygame.display.set_mode((ANCHO, ALTO))

# Escalar robot
robot_img = pygame.transform.scale(robot_img, (90, 90))

# Parámetros del viñedo
FILAS, COLUMNAS = 4, 5
CELDA_ANCHO = ANCHO // COLUMNAS
CELDA_ALTO = ALTO // FILAS

# Umbrales de alerta
UMBRAL_HUMEDAD_SUELO = 35
UMBRAL_TEMP_SUELO = 33
UMBRAL_PH_SUELO = 7.5

# Matriz de colores (para almacenar si hay alerta)
colores_matriz = [[None for _ in range(COLUMNAS)] for _ in range(FILAS)]

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
            # Dibujar fondo
            ventana.blit(fondo, (0, 0))

            # Dibujar celdas con color según alertas previas
            for f in range(FILAS):
                for c in range(COLUMNAS):
                    if colores_matriz[f][c] == "rojo":
                        rect = pygame.Surface((CELDA_ANCHO, CELDA_ALTO), pygame.SRCALPHA)
                        rect.fill((255, 0, 0, 120))  # rojo semitransparente
                        ventana.blit(rect, (c * CELDA_ANCHO, f * CELDA_ALTO))

            # Dibujar robot
            robot_x = col * CELDA_ANCHO + (CELDA_ANCHO - 90) // 2
            robot_y = fila * CELDA_ALTO + (CELDA_ALTO - 90) // 2
            ventana.blit(robot_img, (robot_x, robot_y))
            pygame.display.update()

            # Simular lectura y envío
            datos = generar_datos()
            print(f"📍 Fila {fila+1}, Columna {col+1} → {datos}")
            enviar_datos(datos)

            # Verificar umbrales y colorear si se excede alguno
            if (datos["humedad_suelo"] > UMBRAL_HUMEDAD_SUELO or
                datos["temperatura_suelo"] > UMBRAL_TEMP_SUELO or
                datos["ph_suelo"] > UMBRAL_PH_SUELO):
                colores_matriz[fila][col] = "rojo"

            recorrido.append({
                "fila": fila+1,
                "columna": col+1,
                **datos
            })

            time.sleep(1.2)  # tiempo entre lecturas

        direccion *= -1  # invertir dirección en cada fila
    corriendo = False

# Guardar resultados en CSV
df = pd.DataFrame(recorrido)
df.to_csv("Recorrido_Vinedo_Color.csv", index=False)
print("\n✅ Recorrido completo guardado en 'Recorrido_Vinedo_Color.csv'.")
pygame.quit()
