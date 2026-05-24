"""3_estadisticos.py — Descriptivos, boxplot, histograma, media móvil, AUC."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import CSS, ORDEN, NIVELES, C, load, filtrar, metricas, auc_por_dia, sidebar

st.set_page_config(page_title="Estadísticos · Gas Monitor", page_icon="🔬", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
sidebar()

df_full = load()

st.markdown("""
<div style='padding:1.2rem 0 .6rem;'>
  <div class='lbl' style='margin:0 0 .2rem;'>Estadísticos</div>
  <h1 style='margin:0;font-size:1.85rem;'>Análisis Estadístico</h1>
</div>""", unsafe_allow_html=True)

c1, c2 = st.columns(2)
f0 = c1.date_input("Desde", value=df_full["fecha"].min(),
                   min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())
f1 = c2.date_input("Hasta", value=df_full["fecha"].max(),
                   min_value=df_full["fecha"].min(), max_value=df_full["fecha"].max())

df  = filtrar(df_full, f0, f1)
met = metricas(df)
if df.empty:
    st.warning("Sin datos."); st.stop()

tabs = st.tabs(["📊 Descriptivos", "📦 Boxplot", "📈 Histograma", "🔄 Media móvil", "📐 AUC por día"])

# ─── TAB 1: Descriptivos ──────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="lbl">● Estadísticos de gas_raw (ADC 0–4095)</div>', unsafe_allow_html=True)
    col_t, col_i = st.columns(2)

    with col_t:
        filas = [
            ("Total registros",  f"{met['total']:,}"),
            ("Mínimo",           f"{met['minimo']} ADC"),
            ("Máximo (pico)",    f"{met['pico']} ADC"),
            ("Media",            f"{met['promedio']} ADC"),
            ("Mediana",          f"{met['mediana']} ADC"),
            ("Desv. estándar",   f"{met['std']} ADC"),
            ("IQR",              f"{met['iqr']} ADC"),
            ("Asimetría",        f"{met['asimetria']}"),
            ("Curtosis",         f"{met['curtosis']}"),
            ("Días activos",     f"{met['dias_activos']} / {met['dias']}"),
            ("Horas nivel ALTO+",f"{met['tiempo_alto']} h"),
            ("Dosis AUC total",  f"{met['auc']:,} ADC·min"),
        ]
        for k, v in filas:
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;padding:.42rem 0;
                        border-bottom:1px solid #1e1e35;'>
              <span style='color:#64748b;font-size:.82rem;'>{k}</span>
              <span style='font-family:Space Mono,monospace;font-size:.83rem;
                           font-weight:600;color:#f8fafc;'>{v}</span>
            </div>""", unsafe_allow_html=True)

    with col_i:
        skim  = met["asimetria"]
        media = met["promedio"]
        medi  = met["mediana"]
        dist  = ("aprox. **simétrica** (media ≈ mediana)"
                 if abs(media-medi)/max(medi,1) < 0.1
                 else "**sesgo positivo** — picos altos elevan la media"
                 if media > medi else "**sesgo negativo**")
        kurt  = ("**Leptocúrtica** — colas pesadas, outliers extremos"
                 if met["curtosis"]>3
                 else "**Platicúrtica** — distribución plana, alta dispersión"
                 if met["curtosis"]<1 else "**Mesocúrtica** — distribución normal")
        st.markdown(f"""
        <div class='card' style='margin-top:0;'>
          <div style='font-family:Space Mono,monospace;font-size:.7rem;color:#22c55e;margin-bottom:.6rem;'>
            INTERPRETACIÓN AUTOMÁTICA
          </div>
          <p style='color:#94a3b8;font-size:.83rem;line-height:1.85;margin:0;'>
            Distribución {dist}.<br><br>
            {kurt}.<br><br>
            IQR = <strong style='color:#f8fafc;'>{met["iqr"]} ADC</strong> — delimita el 50 % central.
            Outliers por encima de <strong style='color:#ef4444;'>{int(medi+1.5*met["iqr"])} ADC</strong>.
          </p>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="lbl">● Porcentaje de tiempo por nivel</div>', unsafe_allow_html=True)
    ct = df["estado"].value_counts()
    total = len(df)
    for nombre in ORDEN:
        n = ct.get(nombre, 0)
        pct = n/total*100
        color = C[nombre]
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;padding:4px 0;'>
          <div style='width:78px;font-family:Space Mono,monospace;font-size:.7rem;
                      color:{color};text-align:right;'>{nombre}</div>
          <div style='flex:1;background:#1e1e35;border-radius:4px;height:16px;'>
            <div style='width:{pct}%;background:{color};height:100%;
                        border-radius:4px;opacity:.8;'></div>
          </div>
          <div style='width:90px;font-family:Space Mono,monospace;font-size:.7rem;color:#94a3b8;'>
            {pct:.1f}% · {n:,}
          </div>
        </div>""", unsafe_allow_html=True)

# ─── TAB 2: Boxplot ───────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="lbl">● Boxplot general y por nivel</div>', unsafe_allow_html=True)
    cb1, cb2 = st.columns(2)
    s = df["gas_raw"].dropna()
    q1, med, q3 = s.quantile(.25), s.median(), s.quantile(.75)
    iqr = q3-q1
    out_n = int(((s<q1-1.5*iqr)|(s>q3+1.5*iqr)).sum())

    with cb1:
        fig_bx = go.Figure(go.Box(y=s, name="gas_raw", marker_color="#f97316",
            line_color="#f97316", boxmean=True, fillcolor="rgba(249,115,22,.18)"))
        fig_bx.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
            font=dict(color="#64748b"), height=320, margin=dict(l=10,r=10,t=20,b=10))
        fig_bx.update_yaxes(gridcolor="#1e1e35")
        st.plotly_chart(fig_bx, use_container_width=True)
        st.caption(f"Q1: {q1:.0f} · Mediana: {med:.0f} · Q3: {q3:.0f} · Outliers: {out_n}")

    with cb2:
        nv_pres = [n for n in ORDEN if n in df["estado"].values]
        fig_bxn = go.Figure()
        for n in nv_pres:
            datos_n = df[df["estado"]==n]["gas_raw"]
            fig_bxn.add_trace(go.Box(y=datos_n, name=n, marker_color=C[n],
                line_color=C[n], fillcolor=f"{C[n]}30", boxmean=True))
        fig_bxn.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
            font=dict(color="#64748b"), height=320, margin=dict(l=10,r=10,t=20,b=10),
            showlegend=False)
        fig_bxn.update_yaxes(gridcolor="#1e1e35")
        st.plotly_chart(fig_bxn, use_container_width=True)

# ─── TAB 3: Histograma ────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="lbl">● Histograma y distribución</div>', unsafe_allow_html=True)
    nbins = st.slider("Bins", 10, 100, 40)
    datos = df["gas_raw"].dropna()
    media = datos.mean(); std = datos.std(); medi = datos.median()

    fig_hh = go.Figure(go.Histogram(x=datos, nbinsx=nbins,
        marker_color="#f97316", opacity=0.6, name="Frecuencia"))
    for n, data in NIVELES.items():
        xmn = max(data["min"], int(datos.min()))
        xmx = min(data["max"], int(datos.max()))
        if xmn < xmx:
            fig_hh.add_vrect(x0=xmn, x1=xmx, fillcolor=data["color"], opacity=0.07, line_width=0)
    for val, color, lbl in [
        (media,         "#f8fafc", f"Media: {media:.0f}"),
        (medi,          "#22c55e", f"Mediana: {medi:.0f}"),
        (media+std,     "#64748b", f"+1σ: {media+std:.0f}"),
        (max(0,media-std),"#64748b",f"-1σ: {max(0,media-std):.0f}"),
    ]:
        fig_hh.add_vline(x=val, line_dash="dot", line_color=color, line_width=1.5,
                        annotation_text=lbl, annotation_font=dict(color=color, size=9))
    fig_hh.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
        font=dict(color="#64748b"), height=340, margin=dict(l=10,r=10,t=20,b=10))
    fig_hh.update_yaxes(gridcolor="#1e1e35", title="Frecuencia")
    fig_hh.update_xaxes(gridcolor="#1e1e35", title="gas_raw (ADC)")
    st.plotly_chart(fig_hh, use_container_width=True)

# ─── TAB 4: Media móvil ───────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="lbl">● Tendencia — Media móvil configurable</div>', unsafe_allow_html=True)
    ventana = st.slider("Ventana (puntos a 5 min)", 5, 200, 60)

    df_mm = df.set_index("timestamp")["gas_raw"].resample("5min").mean().dropna().reset_index()
    df_mm.columns = ["timestamp","gas_raw"]
    df_mm["mm"] = df_mm["gas_raw"].rolling(ventana, center=True).mean()

    fig_mm = go.Figure()
    fig_mm.add_trace(go.Scatter(x=df_mm["timestamp"], y=df_mm["gas_raw"],
        name="Raw (5 min)", line=dict(color="#f97316",width=0.8), opacity=0.3))
    fig_mm.add_trace(go.Scatter(x=df_mm["timestamp"], y=df_mm["mm"],
        name=f"MM {ventana} pts", line=dict(color="#f8fafc",width=2.5)))
    fig_mm.add_hline(y=df_mm["gas_raw"].mean(), line_dash="dash", line_color="#64748b",
                     line_width=1, annotation_text=f"Media {df_mm['gas_raw'].mean():.0f}")
    fig_mm.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
        font=dict(color="#64748b"), height=330, margin=dict(l=10,r=10,t=20,b=10),
        legend=dict(bgcolor="#0f0f1e",bordercolor="#1e1e35"))
    fig_mm.update_yaxes(gridcolor="#1e1e35")
    fig_mm.update_xaxes(gridcolor="#1e1e35")
    st.plotly_chart(fig_mm, use_container_width=True)

# ─── TAB 5: AUC ───────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="lbl">● Dosis acumulada (AUC) por día</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#0f0f1e;border:1px solid #1e1e35;border-left:3px solid #f97316;
                border-radius:10px;padding:.85rem 1rem;margin-bottom:.75rem;
                font-size:.82rem;color:#94a3b8;'>
      <strong style='color:#f8fafc;'>AUC</strong> = integral de concentración × tiempo.
      Cuánto gas han recibido las placas acumulado. Unidad: <strong style='color:#f97316;'>ADC·minuto</strong>
    </div>""", unsafe_allow_html=True)

    df_auc = auc_por_dia(df)
    a1,a2,a3 = st.columns(3)
    a1.metric("AUC total",       f"{df_auc['auc'].sum():,.0f} ADC·min")
    a2.metric("AUC promedio/día",f"{df_auc['auc'].mean():,.0f} ADC·min")
    a3.metric("Día mayor dosis", str(df_auc.loc[df_auc['auc'].idxmax(),'fecha']))

    bc = [C.get(n,"#a855f7") for n in df_auc["nivel"]]
    fig_auc = go.Figure(go.Bar(x=df_auc["fecha"], y=df_auc["auc"],
        marker_color=bc, opacity=0.85,
        hovertemplate="<b>%{x}</b><br>AUC: %{y:,.0f} ADC·min<extra></extra>"))
    fig_auc.add_hline(y=df_auc["auc"].mean(), line_dash="dot",
                      line_color="#64748b", line_width=1.5,
                      annotation_text="Promedio")
    fig_auc.update_layout(paper_bgcolor="#080810", plot_bgcolor="#0f0f1e",
        font=dict(color="#64748b"), height=310, margin=dict(l=10,r=10,t=20,b=40))
    fig_auc.update_yaxes(gridcolor="#1e1e35", title="ADC·min")
    fig_auc.update_xaxes(tickangle=45, tickfont=dict(size=8))
    st.plotly_chart(fig_auc, use_container_width=True)

    # Clasificación
    def clasificar(auc):
        if auc < 50000:    return "Sin actividad",     "#334155"
        if auc < 300000:   return "Exposición baja",   "#22c55e"
        if auc < 1000000:  return "Exposición media",  "#f97316"
        return "Exposición alta", "#ef4444"

    df_auc["clase"] = df_auc["auc"].apply(lambda x: clasificar(x)[0])
    df_auc["clase_color"] = df_auc["auc"].apply(lambda x: clasificar(x)[1])
    conteo_clase = df_auc["clase"].value_counts()
    clase_colors = {"Sin actividad":"#334155","Exposición baja":"#22c55e",
                    "Exposición media":"#f97316","Exposición alta":"#ef4444"}

    fig_cp = go.Figure(go.Pie(
        labels=list(conteo_clase.index), values=list(conteo_clase.values),
        marker=dict(colors=[clase_colors.get(k,"#64748b") for k in conteo_clase.index],
                    line=dict(color="#080810",width=2)),
        hole=0.55, textfont=dict(family="Space Mono",size=10)
    ))
    fig_cp.update_layout(paper_bgcolor="#080810", height=240,
        margin=dict(l=0,r=0,t=20,b=0),
        legend=dict(bgcolor="#0f0f1e",font=dict(color="#94a3b8",size=10)))
    st.plotly_chart(fig_cp, use_container_width=True)
