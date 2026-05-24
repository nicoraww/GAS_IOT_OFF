"""2_serie.py — Serie temporal con resolución configurable y heatmap hora/día."""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import CSS, ORDEN, NIVELES, C, load, filtrar, sidebar

st.set_page_config(page_title="Serie Temporal · Gas Monitor", page_icon="📈", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
sidebar()

df_full = load()

st.markdown("""
<div style='padding:1.2rem 0 .6rem;'>
  <div class='lbl' style='margin:0 0 .2rem;'>Serie Temporal</div>
  <h1 style='margin:0;font-size:1.85rem;'>Evolución en el Tiempo</h1>
</div>""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
f0  = c1.date_input("Desde", value=df_full["fecha"].min(),
                    min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())
f1  = c2.date_input("Hasta", value=df_full["fecha"].max(),
                    min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())
res = c3.selectbox("Resolución", ["15s (raw)","1 min","5 min","1 hora","1 día"], index=2)

df = filtrar(df_full, f0, f1)
if df.empty:
    st.warning("Sin datos."); st.stop()

freq_map = {"15s (raw)": None, "1 min":"1min", "5 min":"5min", "1 hora":"1h", "1 día":"1D"}
freq = freq_map[res]

if freq:
    dp = df.set_index("timestamp")["gas_raw"].resample(freq).mean().dropna().reset_index()
    dp.columns = ["timestamp","gas_raw"]
    dp["estado"]    = dp["gas_raw"].apply(lambda x: next((n for n,d in NIVELES.items() if d["min"]<=x<=d["max"]),"CRITICO"))
    dp["nivel_num"] = dp["estado"].map({n:d["idx"] for n,d in NIVELES.items()}).fillna(5)
    dp["color"]     = dp["estado"].map(C)
else:
    dp = df.copy()

st.markdown(f'<div class="lbl">● {len(dp):,} puntos · resolución: {res}</div>', unsafe_allow_html=True)

# ─── Serie principal ──────────────────────────────────────────────────────────
fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    row_heights=[0.75, 0.25], vertical_spacing=0.04)

fig.add_trace(go.Scatter(x=dp["timestamp"], y=dp["gas_raw"], name="gas_raw",
    line=dict(color="#f97316", width=1.2),
    fill="tozeroy", fillcolor="rgba(249,115,22,0.07)"), row=1, col=1)

if len(dp) > 20:
    mm = dp["gas_raw"].rolling(20, center=True).mean()
    fig.add_trace(go.Scatter(x=dp["timestamp"], y=mm, name="MM 20pts",
        line=dict(color="#f8fafc", width=2, dash="dot")), row=1, col=1)

for nombre, data in NIVELES.items():
    if nombre != "SEGURO":
        fig.add_hline(y=data["min"], line_dash="dot", line_color=data["color"],
                      line_width=0.7, opacity=0.5, row=1, col=1)

media = dp["gas_raw"].mean()
fig.add_hline(y=media, line_dash="dash", line_color="#64748b", line_width=1, opacity=0.6,
              annotation_text=f"Media {media:.0f}", row=1, col=1)

colors_bar = [C.get(n, "#a855f7") for n in dp["estado"]]
fig.add_trace(go.Bar(x=dp["timestamp"], y=dp["nivel_num"],
    marker_color=colors_bar, opacity=0.8, name="Nivel"), row=2, col=1)

fig.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
    font=dict(color="#64748b"), height=440,
    margin=dict(l=10,r=10,t=15,b=10), hovermode="x unified", showlegend=True,
    legend=dict(bgcolor="#0f0f1e", bordercolor="#1e1e35"))
fig.update_yaxes(gridcolor="#1e1e35", zerolinecolor="#1e1e35")
fig.update_xaxes(gridcolor="#1e1e35")
fig.update_yaxes(row=2, col=1, range=[0,5],
                 tickvals=[0,1,2,3,4,5],
                 ticktext=["SEG","TRA","LEV","MOD","ALT","CRI"])
st.plotly_chart(fig, use_container_width=True)

# ─── Heatmap hora × día ───────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Mapa de calor — Promedio ADC por hora y día de semana</div>', unsafe_allow_html=True)

orden_dias = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
etiq_dias  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

pivot = df.pivot_table(index="dia_semana", columns="hora", values="gas_raw", aggfunc="mean")
pivot = pivot.reindex([d for d in orden_dias if d in pivot.index])
etiq_y = [etiq_dias[orden_dias.index(d)] for d in pivot.index]

fig_h = go.Figure(go.Heatmap(
    z=pivot.values,
    x=[f"{h:02d}h" for h in pivot.columns],
    y=etiq_y,
    colorscale=[[0,"#22c55e"],[0.2,"#3b82f6"],[0.4,"#eab308"],
                [0.6,"#f97316"],[0.8,"#ef4444"],[1,"#a855f7"]],
    hoverongaps=False,
    colorbar=dict(title="ADC", tickfont=dict(color="#64748b"))
))
fig_h.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
    font=dict(color="#64748b"), height=250, margin=dict(l=10,r=10,t=10,b=10))
st.plotly_chart(fig_h, use_container_width=True)

st.markdown("""
<div style='font-size:.78rem;color:#475569;line-height:1.6;'>
💡 <strong style='color:#94a3b8;'>Lectura:</strong>
Colores cálidos (rojo/morado) = mayor concentración.
Identifica en qué horas y días se hicieron las sesiones de exposición.
</div>""", unsafe_allow_html=True)
