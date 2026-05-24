"""5_datos.py — Explorador de datos crudos con filtros y descarga CSV."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import CSS, ORDEN, load, filtrar, sidebar

st.set_page_config(page_title="Datos · Gas Monitor", page_icon="🗄️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
sidebar()

df_full = load()

st.markdown("""
<div style='padding:1.2rem 0 .6rem;'>
  <div class='lbl' style='margin:0 0 .2rem;'>Explorador</div>
  <h1 style='margin:0;font-size:1.85rem;'>Datos Crudos</h1>
</div>""", unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
f0       = c1.date_input("Desde", value=df_full["fecha"].min(),
                          min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())
f1       = c2.date_input("Hasta", value=df_full["fecha"].max(),
                          min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())
nv_sel   = c3.multiselect("Niveles", ORDEN, default=ORDEN)
max_rows = c4.selectbox("Filas", [100,500,1000,5000,"Todas"], index=1)

df = filtrar(df_full, f0, f1)
if nv_sel:
    df = df[df["estado"].isin(nv_sel)]
if df.empty:
    st.info("Sin datos con los filtros seleccionados."); st.stop()

k1,k2,k3,k4 = st.columns(4)
k1.metric("Registros filtrados", f"{len(df):,}")
k2.metric("Días",                f"{df['fecha'].nunique()}")
k3.metric("ADC promedio",        f"{df['gas_raw'].mean():.0f}")
k4.metric("ADC máximo",          f"{df['gas_raw'].max()}")

st.markdown("---")

df_show = df if max_rows == "Todas" else df.tail(int(max_rows))
df_disp = df_show[["timestamp","gas_raw","estado","nivel_num"]].copy()
df_disp["timestamp"] = df_disp["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
df_disp = df_disp.rename(columns={
    "timestamp":"Fecha/Hora","gas_raw":"ADC","estado":"Nivel","nivel_num":"Índice"})

st.dataframe(df_disp, use_container_width=True, hide_index=True, height=460,
    column_config={
        "ADC":    st.column_config.NumberColumn(format="%d"),
        "Índice": st.column_config.NumberColumn(format="%d"),
    })

col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    csv_out = df[["timestamp","gas_raw","estado"]].copy()
    csv_out["timestamp"] = csv_out["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.download_button("⬇️ Descargar CSV filtrado",
        csv_out.to_csv(index=False),
        file_name=f"gas_{f0}_{f1}.csv", mime="text/csv")

with col_dl2:
    resumen = df.groupby("estado")["gas_raw"].agg(
        count="count", mean="mean", min="min", max="max").round(1).reset_index()
    st.download_button("⬇️ Descargar resumen por nivel",
        resumen.to_csv(index=False),
        file_name="resumen_niveles.csv", mime="text/csv")

st.markdown("---")
st.markdown("""
<div style='background:#0f0f1e;border:1px solid #1e1e35;border-radius:12px;
            padding:.9rem 1rem;font-family:Space Mono,monospace;font-size:.72rem;
            color:#475569;line-height:2;'>
  <span style='color:#22c55e;'>FUENTE:</span> gas_camara_datos.csv &nbsp;|&nbsp;
  14 abr – 14 may 2026 &nbsp;|&nbsp; 178,560 registros &nbsp;|&nbsp;
  Cada 15 s &nbsp;|&nbsp; ESP32 + MQ2 (Wokwi)
</div>""", unsafe_allow_html=True)
