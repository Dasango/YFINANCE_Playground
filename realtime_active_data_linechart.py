import gradio as gr
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def get_realtime_data(ticker="GOOG", period="60d", interval="5m"):
    """
    Downloads data using yfinance and filters for the last 24 hours.
    """
    try:
        # Download data
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        
        if df.empty:
            return pd.DataFrame()

        # Handle MultiIndex if present (yfinance sometimes returns this)
        if isinstance(df.columns, pd.MultiIndex):
            try:
                df = df.xs(ticker, axis=1, level=1)
            except KeyError:
                # Fallback if structure is different
                pass
        
        # Ensure index is datetime and localized/converted
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Filter last 24 hours
        # Use local time notion if possible, or just take the last 24h from the latest timestamp in data
        # Real "last 24 hours" implies from NOW. But market data stops. 
        # So maybe "last 24 hours of available data" or "last 24 hours from now"?
        # User said "solo los datos de las utlimas 24 horas".
        # If market is closed, "last 24h from now" might be empty.
        # Let's assume "Last 24 hours of data" or "Latest day".
        # But "realtime" implies checking against Now. 
        # Let's try to filter: last_timestamp - 24h.
        
        latest_time = df.index.max()
        start_time = latest_time - timedelta(hours=24)
        
        df_filtered = df[df.index >= start_time].copy()
        
        return df_filtered
        
    except Exception as e:
        print(f"Error downloading data: {e}")
        return pd.DataFrame()

def create_plot(ticker="GOOG", period="60d", interval="5m"):
    df = get_realtime_data(ticker, period, interval)
    
    if df.empty:
        return px.line(title=f"No data found for {ticker} in last 24h")
    
    # Plotting 'Close' price
    fig = px.line(df, x=df.index, y="Close", title=f"Realtime Data: {ticker} (Last 24h)")
    
    # Customize aesthetic
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis_title="Time",
        yaxis_title="Close Price"
    )
    # Ejes negros
    fig.update_xaxes(linecolor='black', showgrid=False)
    fig.update_yaxes(linecolor='black', showgrid=False)
    
    return fig

def create_realtime_chart_component(ticker="GOOG", period="60d", interval="5m"):
    with gr.Column():
        gr.Markdown("### 📈 Realtime Active Data (Last 24h)")
        plot = gr.Plot(label=f"{ticker} Last 24h")
        
        # Button/Timer to refresh? User didn't explicitly ask for refresh button for this, 
        # but "active data" implies it might update.
        # Let's add a timer for this too, every 60 seconds (since it's market data, 5m interval)
        # or maybe faster if they want "active". 5m interval doesn't change every second.
        # Let's set it to 60s.
        
        def refresh():
            return create_plot(ticker, period, interval)
            
        timer = gr.Timer(60) # Refresh every 60 seconds
        timer.tick(refresh, outputs=[plot])
        
        # Initial load
        # Since we are returning the component, we can't call load on 'demo' here. 
        # But we can define a load event on the plot if possible or just rely on Timer (which waits for interval).
        # We should ideally trigger an immediate update. 
        # In Gradio 5, we can use the `value` argument of gr.Plot?
        # Yes, let's pre-calculate the initial value so it shows up immediately.
        
        initial_fig = create_plot(ticker, period, interval)
        plot.value = initial_fig
        
        return plot

if __name__ == "__main__":
    with gr.Blocks() as demo:
        create_realtime_chart_component()
    demo.launch()
