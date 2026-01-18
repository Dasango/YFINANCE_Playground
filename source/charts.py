import plotly.graph_objects as go
from .config import TRANSLATIONS
from .data_loader import df_chart

def create_styled_perf_chart(lang):
    title = TRANSLATIONS[lang]["chart_performance"]
    fig = go.Figure()
    
    if not df_chart.empty:
        fig.add_trace(go.Scatter(
            x=df_chart["Datetime"],
            y=df_chart["Close"],
            mode='lines',
            line=dict(color='#059669', width=2),
            fill='tozeroy',
            fillcolor='rgba(5, 150, 105, 0.05)'
        ))
        
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#0C1327',
        plot_bgcolor='#0C1327',
        showlegend=False,
        margin=dict(l=40, r=20, t=20, b=40),
        height=380,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#64748B', size=10)),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.05)',
            gridwidth=1,
            griddash='dot',
            zeroline=False,
            tickprefix="$",
            tickfont=dict(color='#64748B', size=10),
        ),
        font=dict(family="Inter", color="white")
    )
    return fig

def create_styled_loss_chart(lang):
    iters = list(range(30))
    vals = [max(0.0001, 2.5 * (0.82**i)) for i in iters]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=iters, y=vals, mode='lines', line=dict(color='#059669', width=2)))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#0C1327',
        plot_bgcolor='#0C1327',
        showlegend=False,
        margin=dict(l=40, r=20, t=10, b=40),
        height=200,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#64748B', size=10)),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.05)',
            gridwidth=1,
            griddash='dot',
            zeroline=False,
            tickfont=dict(color='#64748B', size=10)
        ),
        font=dict(family="Inter", color="white")
    )
    return fig
