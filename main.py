
import tkinter as tk
from tkinter import messagebox
import psycopg2
from pyproj import Transformer
from tkintermapview import TkinterMapView
import requests
import folium
import webbrowser

# Configuración de la base de datos
DB_CONFIG = {
    "dbname": "nyc",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}

DATA_URL = ""

# Función para cargar los datos en la base de datos
def cargar_datos():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS pueblosHuelva;")
        cursor.execute("""
            CREATE TABLE pueblosHuelva (
                id SERIAL PRIMARY KEY,
                municipio TEXT,
                coordenadas GEOMETRY(Point, 25830),
                altura NUMERIC
            );
        """)

        response = requests.get(DATA_URL)
        response.raise_for_status()
        lineas = response.text.strip().split("\n")[1:]

        for linea in lineas:
            municipio, x, y, altura = linea.split("\t")
            cursor.execute("""
    INSERT INTO pueblosHuelva (municipio, coordenadas, altura)
    VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 25830), %s);
""", (municipio, float(x), float(y), float(altura)))

        conn.commit()
        messagebox.showinfo("Éxito", "Datos cargados correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")
    finally:
        cursor.close()
        conn.close()

# Función para mostrar los datos en un mapa
def mostrar_datos(altura_minima):
    try:
        altura_minima = float(altura_minima)
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Filtrar municipios según la altura mínima
        cursor.execute("""
            SELECT municipio, ST_X(ST_Transform(coordenadas, 4326)) AS lon, 
                   ST_Y(ST_Transform(coordenadas, 4326)) AS lat, altura
            FROM pueblosHuelva
            WHERE altura > %s;
        """, (altura_minima,))

        municipios = cursor.fetchall()
        if not municipios:
            messagebox.showinfo("Sin datos", "No hay municipios que cumplan con el criterio de altura mínima.")
            return

        
        latitudes, longitudes = zip(*[(lat, lon) for _, lon, lat, _ in municipios])
        lat_centro, lon_centro = sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)

        mapa = folium.Map(location=[lat_centro, lon_centro], zoom_start=0)

        contador =0 
        
        # Agregar marcadores al mapa
        for (municipio, lon, lat, altura) in municipios:
            contador = contador +1
            folium.Marker(
                location=[lat, lon],
                popup=f"{municipio}<br>Altura: {altura} m",
                tooltip=municipio
            ).add_to(mapa)
        # Guardar y abrir el mapa
        mapa.save("mapa_huelva.html")
        webbrowser.open("mapa_huelva.html")
        messagebox.showinfo("Éxito", f"Mapa generado y abierto en el navegador con {contador} pueblo/s")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo mostrar el mapa: {e}")
    finally:
        cursor.close()
        conn.close()

# Crear la interfaz gráfica
def crear_interfaz():
    ventana = tk.Tk()
    ventana.title("Israel Aznar Villegas")
    ventana.geometry("400x250")
    ventana.resizable(False, False)
    # Elementos de la interfaz
    tk.Label(ventana, text="Mapa de Municipios de Huelva", font=("Arial", 12)).pack(pady=10)
    
    # Botones
    tk.Button(ventana, text="Cargar datos", command=cargar_datos, width=20).pack(pady=10)
    tk.Button(
        ventana, 
        text="Mostrar datos", 
        command=lambda: mostrar_datos(entrada_altura.get()), 
        width=20
    ).pack(pady=10)

    tk.Label(ventana, text="Altura mínima (metros):").pack(pady=10)
    entrada_altura = tk.Entry(ventana)
    entrada_altura.pack(pady=5)
    ventana.mainloop()

# Ejecutar la interfaz
if __name__ == "__main__":
    crear_interfaz()


