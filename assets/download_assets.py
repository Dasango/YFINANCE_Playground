import yfinance as yf
import pandas as pd


def descargar_datos_google_intradia():
    ticker = "GOOGL"
    
    # CONFIGURACIÓN INTRADÍA
    # 'interval="1m"' pide datos de cada minuto.
    # 'period="7d"' es el LÍMITE MÁXIMO de Yahoo Finance para datos de 1 minuto.
    intervalo = "5m"
    periodo = "60d"
    
    # Generamos un nombre de archivo con una fecha fija
    fecha_hoy = "2026-01-16"
    nombre_archivo = f"datos_google_{intervalo}_{fecha_hoy}.csv"

    print(f"--- Iniciando descarga intradía para {ticker} ---")
    print(f"Intervalo: {intervalo}")
    print(f"Periodo: Últimos {periodo} (Límite máximo de la API para 1 minuto)")

    try:
        # Descargar datos
        # Nota: No se usan start/end para intradía de 1m, es mejor usar 'period'
        df = yf.download(ticker, period=periodo, interval=intervalo, auto_adjust=True)

        if df.empty:
            print("Error: No se encontraron datos. Es posible que el mercado esté cerrado o el límite excedido.")
            return

        # Mostrar resumen
        print("\nResumen de datos descargados:")
        print(df.head(3))
        print("...")
        print(df.tail(3))
        print(f"\nTotal de registros (minutos): {len(df)}")

        # Guardar a CSV
        df.to_csv(nombre_archivo)
        print(f"\n[Éxito] Archivo guardado como: {nombre_archivo}")

    except Exception as e:
        print(f"\n[Error] Ocurrió un problema: {e}")

if __name__ == "__main__":
    descargar_datos_google_intradia()