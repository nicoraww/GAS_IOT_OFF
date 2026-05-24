"""1_dashboard.py — Gauges, KPIs, serie diaria, donut, AUC por día."""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import CSS, ORDEN, NIVELES, C, load, filtrar, metricas, auc_por_dia, make_gauge, sidebar

st.set_page_config(page_title="Dashboard · Gas Monitor", page_icon="📊", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
sidebar()

df_full = load()

st.markdown("""
<div style='padding:1.2rem 0 .6rem;'>
  <div class='lbl' style='margin:0 0 .2rem;'>Dashboard</div>
  <h1 style='margin:0;font-size:1.85rem;'>Resumen General</h1>
</div>""", unsafe_allow_html=True)

# ─── Filtro fechas ────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
f0 = c1.date_input("Desde", value=df_full["fecha"].min(),
                   min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())
f1 = c2.date_input("Hasta", value=df_full["fecha"].max(),
                   min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())

df  = filtrar(df_full, f0, f1)
met = metricas(df)
if df.empty:
    st.warning("Sin datos en el rango."); st.stop()

# ─── Color nivel promedio ─────────────────────────────────────────────────────
nv_prom = next((n for n, d in NIVELES.items() if d["min"] <= met["promedio"] <= d["max"]), "CRITICO")
cp = C[nv_prom]
pct_critico = round(df[df["estado"] == "CRITICO"].shape[0] / len(df) * 100, 1)
pct_activos = round(met["dias_activos"] / max(met["dias"], 1) * 100, 1)

# ─── Gauges ───────────────────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Indicadores del período seleccionado</div>', unsafe_allow_html=True)
g1, g2, g3, g4 = st.columns(4)
with g1:
    st.plotly_chart(make_gauge(met["promedio"], "PROMEDIO ADC", 4095, cp), use_container_width=True, key="g1")
with g2:
    st.plotly_chart(make_gauge(met["pico"], "PICO MÁXIMO ADC", 4095, "#ef4444"), use_container_width=True, key="g2")
with g3:
    st.plotly_chart(make_gauge(pct_activos, "DÍAS ACTIVOS %", 100, "#f97316", "%"), use_container_width=True, key="g3")
with g4:
    st.plotly_chart(make_gauge(pct_critico, "% TIEMPO CRÍTICO", 100, "#a855f7", "%"), use_container_width=True, key="g4")

# ─── KPIs ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Métricas clave</div>', unsafe_allow_html=True)
k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("Lecturas",       f"{met['total']:,}")
k2.metric("Días activos",   f"{met['dias_activos']} / {met['dias']}")
k3.metric("Dosis AUC",      f"{met['auc']:,} ADC·min")
k4.metric("Horas ALTO+",    f"{met['tiempo_alto']} h")
k5.metric("Pico",           f"{met['pico']} ADC")
k6.metric("Promedio",       f"{met['promedio']} ADC")

# ─── Serie diaria ─────────────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Evolución diaria — promedio, pico y mínimo</div>', unsafe_allow_html=True)
dd = df.groupby("fecha").agg(prom=("gas_raw","mean"), pico=("gas_raw","max"), mn=("gas_raw","min")).reset_index()

fig_d = go.Figure()
fig_d.add_trace(go.Scatter(x=dd["fecha"], y=dd["pico"],  name="Pico",
    line=dict(color="#ef444450",width=1), fill=None))
fig_d.add_trace(go.Scatter(x=dd["fecha"], y=dd["prom"],  name="Promedio",
    line=dict(color="#f97316",width=2.5),
    fill="tonexty", fillcolor="rgba(249,115,22,0.08)"))
fig_d.add_trace(go.Scatter(x=dd["fecha"], y=dd["mn"],    name="Mínimo",
    line=dict(color="#22c55e50",width=1),
    fill="tonexty", fillcolor="rgba(34,197,94,0.04)"))
fig_d.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
    font=dict(color="#64748b"), height=260, margin=dict(l=10,r=10,t=10,b=10),
    hovermode="x unified",
    legend=dict(bgcolor="#0f0f1e", bordercolor="#1e1e35"))
fig_d.update_yaxes(gridcolor="#1e1e35")
fig_d.update_xaxes(gridcolor="#1e1e35")
st.plotly_chart(fig_d, use_container_width=True)

# ─── Donut + AUC ─────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.markdown('<div class="lbl">● Distribución por nivel</div>', unsafe_allow_html=True)
    ct = df["estado"].value_counts()
    lbs = [n for n in ORDEN if n in ct.index]
    vls = [ct[n] for n in lbs]
    clrs= [C[n] for n in lbs]
    fig_p = go.Figure(go.Pie(
        labels=lbs, values=vls,
        marker=dict(colors=clrs, line=dict(color="#080810", width=2)),
        hole=0.58, textfont=dict(family="Space Mono", size=10)
    ))
    fig_p.add_annotation(text=f"<b>{sum(vls):,}</b>", x=0.5, y=0.5,
        font=dict(size=15, color="#f8fafc", family="Space Mono"), showarrow=False)
    fig_p.update_layout(paper_bgcolor="#080810", height=270,
        margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(bgcolor="#0f0f1e", bordercolor="#1e1e35",
                    font=dict(color="#94a3b8", size=10)))
    st.plotly_chart(fig_p, use_container_width=True)

with col_r:
    st.markdown('<div class="lbl">● Dosis acumulada (AUC) por día</div>', unsafe_allow_html=True)
    df_auc = auc_por_dia(df)
    bc = ["#ef4444" if v>500000 else "#f97316" if v>150000 else "#eab308" if v>30000 else "#22c55e"
          for v in df_auc["auc"]]
    fig_auc = go.Figure(go.Bar(x=df_auc["fecha"], y=df_auc["auc"],
        marker_color=bc, opacity=0.85))
    fig_auc.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
        font=dict(color="#64748b"), height=270, margin=dict(l=10,r=10,t=10,b=30),
        showlegend=False)
    fig_auc.update_yaxes(gridcolor="#1e1e35", title="ADC·min")
    fig_auc.update_xaxes(tickangle=45, tickfont=dict(size=8))
    st.plotly_chart(fig_auc, use_container_width=True)
