import pandas as pd
import matplotlib.pyplot as plt

# 1. Cargar el archivo CSV
# 'skiprows=3' salta las primeras filas (Price, Ticker, Datetime...) que no son datos directos.
# 'names' asigna los nombres correctos a las columnas.
archivo = 'assets/datos_google_5m_2026-01-16_2153.csv'
df = pd.read_csv(archivo, skiprows=3, names=['Datetime', 'Close', 'High', 'Low', 'Open', 'Volume'])

# 2. Convertir la columna de fecha al formato correcto
# Esto asegura que el eje X entienda que son fechas y horas.
df['Datetime'] = pd.to_datetime(df['Datetime'])

# 3. Filtrar los datos: Tomar una fila cada 30 filas
# La sintaxis [::30] significa "toma todo, desde el principio hasta el final, saltando de 30 en 30".
df_filtrado = df.iloc[::30]

# 4. Generar el gráfico de líneas
plt.figure(figsize=(12, 6)) # Tamaño de la figura (ancho, alto)

# Graficamos 'Datetime' en el eje X y 'Close' (Precio de cierre) en el eje Y
plt.plot(df_filtrado['Datetime'], df_filtrado['Close'], label='Precio de Cierre (GOOGL)', color='blue')

# Añadir títulos y etiquetas
plt.title('Precio de GOOGL (Muestreo cada 30 registros)')
plt.xlabel('Fecha')
plt.ylabel('Precio de Cierre')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5) # Cuadrícula ligera
plt.xticks(rotation=45) # Rotar fechas para que se lean mejor

# Ajustar diseño para que no se corten las etiquetas
plt.tight_layout()

# Mostrar (o guardar) el gráfico
plt.savefig('grafico_googl.png')
plt.show()