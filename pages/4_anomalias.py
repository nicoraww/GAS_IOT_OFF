"""4_anomalias.py — Z-score, tasa de cambio, tabla de anomalías."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import CSS, NIVELES, C, load, filtrar, sidebar

st.set_page_config(page_title="Anomalías · Gas Monitor", page_icon="⚠️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
sidebar()

df_full = load()

st.markdown("""
<div style='padding:1.2rem 0 .6rem;'>
  <div class='lbl' style='margin:0 0 .2rem;'>Anomalías</div>
  <h1 style='margin:0;font-size:1.85rem;'>Detección de Anomalías</h1>
</div>""", unsafe_allow_html=True)

c1,c2,c3 = st.columns(3)
f0       = c1.date_input("Desde", value=df_full["fecha"].min(),
                          min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())
f1       = c2.date_input("Hasta", value=df_full["fecha"].max(),
                          min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())
umbral_z = c3.slider("Umbral Z-score", 1.5, 4.0, 2.5, 0.1)

df = filtrar(df_full, f0, f1)
if df.empty:
    st.warning("Sin datos."); st.stop()

serie = df["gas_raw"].dropna()
z     = (serie - serie.mean()) / serie.std()
mask  = z.abs() > umbral_z
df_anom = df.loc[mask].copy()
df_anom["z_score"] = z[mask].values

# ─── KPIs ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Detección por Z-score</div>', unsafe_allow_html=True)
k1,k2,k3,k4 = st.columns(4)
k1.metric("Anomalías detectadas", f"{len(df_anom):,}")
k2.metric("% del total",          f"{len(df_anom)/len(df)*100:.2f}%")
k3.metric("Z-score máximo",       f"{z.abs().max():.2f}")
k4.metric("Umbral aplicado",      f"±{umbral_z}")

# ─── Gráfica Z-score ──────────────────────────────────────────────────────────
dp = df.set_index("timestamp")["gas_raw"].resample("5min").mean().dropna().reset_index()
dp.columns = ["timestamp","gas_raw"]
z_r  = (dp["gas_raw"] - dp["gas_raw"].mean()) / dp["gas_raw"].std()
mask_r = z_r.abs() > umbral_z

fig_z = go.Figure()
fig_z.add_trace(go.Scatter(x=dp["timestamp"], y=dp["gas_raw"],
    name="gas_raw", line=dict(color="#f97316",width=1.2), opacity=0.8))
fig_z.add_trace(go.Scatter(
    x=dp.loc[mask_r,"timestamp"], y=dp.loc[mask_r,"gas_raw"],
    mode="markers", name=f"Anomalías (z>{umbral_z})",
    marker=dict(color="#facc15",size=8,symbol="circle-open",line=dict(width=2,color="#facc15"))))

ub = serie.mean() + umbral_z*serie.std()
lb = max(0, serie.mean() - umbral_z*serie.std())
fig_z.add_hrect(y0=lb, y1=ub, fillcolor="rgba(249,115,22,0.05)", line_width=0)
fig_z.add_hline(y=ub, line_dash="dot", line_color="#ef4444", line_width=1,
               annotation_text=f"Límite sup: {ub:.0f}")
fig_z.add_hline(y=lb, line_dash="dot", line_color="#22c55e", line_width=1,
               annotation_text=f"Límite inf: {lb:.0f}")
fig_z.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
    font=dict(color="#64748b"), height=330, margin=dict(l=10,r=10,t=20,b=10),
    hovermode="x unified", legend=dict(bgcolor="#0f0f1e",bordercolor="#1e1e35"))
fig_z.update_yaxes(gridcolor="#1e1e35")
fig_z.update_xaxes(gridcolor="#1e1e35")
st.plotly_chart(fig_z, use_container_width=True)

# ─── Tasa de cambio ───────────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Tasa de cambio — Δ ADC por minuto</div>', unsafe_allow_html=True)

df_tc = df.set_index("timestamp")["gas_raw"].resample("1min").mean().dropna().reset_index()
df_tc.columns = ["timestamp","gas_raw"]
df_tc["delta"] = df_tc["gas_raw"].diff()
top_sub = df_tc.nlargest(10,"delta")[["timestamp","gas_raw","delta"]]
top_cai = df_tc.nsmallest(10,"delta")[["timestamp","gas_raw","delta"]]

fig_tc = go.Figure()
fig_tc.add_trace(go.Scatter(x=df_tc["timestamp"], y=df_tc["delta"],
    name="Δ/min", line=dict(color="#3b82f6",width=1),
    fill="tozeroy", fillcolor="rgba(59,130,246,0.06)"))
fig_tc.add_hline(y=0, line_color="#334155", line_width=1)
fig_tc.add_trace(go.Scatter(x=top_sub["timestamp"], y=top_sub["delta"],
    mode="markers", marker=dict(color="#ef4444",size=9,symbol="triangle-up"),
    name="Top subidas"))
fig_tc.add_trace(go.Scatter(x=top_cai["timestamp"], y=top_cai["delta"],
    mode="markers", marker=dict(color="#22c55e",size=9,symbol="triangle-down"),
    name="Top caídas"))
fig_tc.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
    font=dict(color="#64748b"), height=260, margin=dict(l=10,r=10,t=20,b=10),
    legend=dict(bgcolor="#0f0f1e",bordercolor="#1e1e35"))
fig_tc.update_yaxes(gridcolor="#1e1e35", title="Δ ADC/min")
st.plotly_chart(fig_tc, use_container_width=True)

col_s, col_c = st.columns(2)
with col_s:
    st.markdown("**🔴 Top 10 subidas** — posibles inicios de sesión")
    st.dataframe(top_sub.rename(columns={"timestamp":"Fecha/Hora","gas_raw":"ADC","delta":"Δ ADC/min"}),
                 use_container_width=True, hide_index=True)
with col_c:
    st.markdown("**🟢 Top 10 caídas** — posibles fines de sesión")
    st.dataframe(top_cai.rename(columns={"timestamp":"Fecha/Hora","gas_raw":"ADC","delta":"Δ ADC/min"}),
                 use_container_width=True, hide_index=True)

# ─── Tabla anomalías ──────────────────────────────────────────────────────────
if len(df_anom) > 0:
    st.markdown('<div class="lbl">● Tabla de anomalías (primeras 50)</div>', unsafe_allow_html=True)
    t = df_anom[["timestamp","gas_raw","estado","z_score"]].head(50).copy()
    t["z_score"]   = t["z_score"].round(2)
    t["timestamp"] = t["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(t.rename(columns={"timestamp":"Fecha/Hora","gas_raw":"ADC",
                                    "estado":"Nivel","z_score":"Z-score"}),
                 use_container_width=True, hide_index=True)
