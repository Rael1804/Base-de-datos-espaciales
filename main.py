
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

DATA_URL = "http://www.uhu.es/jluis.dominguez/AGI/pueblosHuelva.txt"

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
'''
# Función para mostrar los datos en un mapa interactivo
def mostrar_datos(altura_minima, frame_mapa):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Filtrar municipios según la altura mínima
        if altura_minima:
            cursor.execute("""
                SELECT municipio, coord_x, coord_y, altura 
                FROM pueblosHuelva 
                WHERE altura > %s;
            """, (float(altura_minima),))
        else:
            cursor.execute("SELECT municipio, coord_x, coord_y, altura FROM pueblosHuelva;")

        municipios = cursor.fetchall()
        if not municipios:
            messagebox.showinfo("Sin datos", "No hay municipios que cumplan con el criterio de altura mínima.")
            return

        # Convertir coordenadas de UTM a lat/lon
        transformer = Transformer.from_crs("epsg:25830", "epsg:4326")  # UTM a lat/lon
        coordenadas_latlon = [transformer.transform(x, y) for _, x, y, _ in municipios]

        # Configurar el mapa en tkintermapview
        for widget in frame_mapa.winfo_children():
            widget.destroy()

        mapa = TkinterMapView(frame_mapa, width=800, height=600, corner_radius=0)
        mapa.pack(fill=tk.BOTH, expand=True)

        # Centrar el mapa en las coordenadas de los municipios
        latitudes, longitudes = zip(*coordenadas_latlon)
        lat_centro, lon_centro = sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)
        mapa.set_position(lat_centro, lon_centro)
        mapa.set_zoom(10)

        # Agregar marcadores en el mapa
        for (municipio, _, _, altura), (lat, lon) in zip(municipios, coordenadas_latlon):
            mapa.set_marker(lat, lon, text=f"{municipio}\nAltura: {altura} m")

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo mostrar el mapa: {e}")
    finally:
        cursor.close()
        conn.close()

# Crear la interfaz gráfica
def crear_interfaz():
    ventana = tk.Tk()
    ventana.title("Mapa de Municipios de Huelva")
    ventana.geometry("900x700")
    ventana.resizable(True, True)

    # Frame para los controles superiores
    frame_superior = tk.Frame(ventana)
    frame_superior.pack(side=tk.TOP, fill=tk.X, pady=10)

    tk.Label(frame_superior, text="Altura mínima (metros):", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
    entrada_altura = tk.Entry(frame_superior, font=("Arial", 12))
    entrada_altura.pack(side=tk.LEFT, padx=10)

    tk.Button(frame_superior, text="Cargar datos", command=cargar_datos, width=20).pack(side=tk.LEFT, padx=10)

    frame_mapa = tk.Frame(ventana)
    frame_mapa.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    tk.Button(frame_superior, text="Mostrar datos", command=lambda: mostrar_datos(entrada_altura.get(), frame_mapa), width=20).pack(side=tk.LEFT, padx=10)
    ventana.mainloop()

# Ejecutar la interfaz
if __name__ == "__main__":
    crear_interfaz()
'''


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


