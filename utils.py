"""
utils.py — Carga del CSV, constantes y helpers compartidos por todas las páginas.
"""
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

# ─── Ruta del CSV ─────────────────────────────────────────────────────────────
CSV_PATH = Path(__file__).parent / "gas_camara_datos.csv"

# ─── Paleta de niveles ────────────────────────────────────────────────────────
NIVELES = {
    "SEGURO":   {"color": "#22c55e", "min": 0,    "max": 400,  "idx": 0},
    "TRAZA":    {"color": "#3b82f6", "min": 401,  "max": 800,  "idx": 1},
    "LEVE":     {"color": "#eab308", "min": 801,  "max": 1200, "idx": 2},
    "MODERADO": {"color": "#f97316", "min": 1201, "max": 1800, "idx": 3},
    "ALTO":     {"color": "#ef4444", "min": 1801, "max": 2800, "idx": 4},
    "CRITICO":  {"color": "#a855f7", "min": 2801, "max": 4095, "idx": 5},
}
ORDEN = ["SEGURO", "TRAZA", "LEVE", "MODERADO", "ALTO", "CRITICO"]
C = {n: d["color"] for n, d in NIVELES.items()}   # shorthand color map

# ─── CSS ──────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;500;600&display=swap');
html,body,[class*="css"],.stApp{font-family:'Sora',sans-serif;background:#080810;color:#e2e8f0;}
[data-testid="stSidebar"]{background:#0d0d1a!important;border-right:1px solid #1e1e35;}
div[data-testid="metric-container"]{background:#0f0f1e;border:1px solid #1e1e35;border-radius:12px;padding:.9rem 1.1rem;}
h1,h2,h3{font-family:'Space Mono',monospace!important;}
.stTabs [data-baseweb="tab-list"]{background:#0f0f1e;border-radius:10px;padding:3px;border:1px solid #1e1e35;}
.stTabs [data-baseweb="tab"]{font-family:'Space Mono',monospace;font-size:.72rem;color:#64748b;border-radius:8px;}
.stTabs [aria-selected="true"]{background:#1e1e35!important;color:#f8fafc!important;}
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
.card{background:#0f0f1e;border:1px solid #1e1e35;border-radius:14px;padding:1.25rem;}
.lbl{font-family:'Space Mono',monospace;font-size:.68rem;color:#475569;
     letter-spacing:.14em;text-transform:uppercase;margin:.9rem 0 .5rem;}
</style>
"""

# ─── Carga cacheada ───────────────────────────────────────────────────────────
@st.cache_data
def load():
    df = pd.read_csv(CSV_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["nivel_num"] = df["estado"].map({n: d["idx"] for n, d in NIVELES.items()}).fillna(0).astype(int)
    df["color"]     = df["estado"].map(C).fillna("#a855f7")
    df["fecha"]     = df["timestamp"].dt.date
    df["hora"]      = df["timestamp"].dt.hour
    df["dia_semana"]= df["timestamp"].dt.day_name()
    return df

def filtrar(df, f0, f1):
    return df[(df["fecha"] >= f0) & (df["fecha"] <= f1)].copy()

# ─── Métricas ─────────────────────────────────────────────────────────────────
def metricas(df):
    if df.empty:
        return {}
    s = df["gas_raw"]
    q1, q3 = s.quantile(.25), s.quantile(.75)
    iqr = q3 - q1
    dias_activos = int(df[df["gas_raw"] > 1200].groupby("fecha").ngroups)
    tiempo_alto = 0
    if len(df) > 1:
        d2 = df.sort_values("timestamp").copy()
        d2["dt"] = d2["timestamp"].diff().dt.total_seconds().fillna(0)
        tiempo_alto = round(d2[d2["gas_raw"] > 1800]["dt"].sum() / 3600, 1)
    auc = 0
    if len(df) > 1:
        t = df["timestamp"].astype(np.int64) / 1e9
        auc = round(abs(float(np.trapezoid(s.values, t.values))) / 60, 0)
    return dict(
        total=len(df), dias=df["fecha"].nunique(),
        dias_activos=dias_activos, pico=int(s.max()),
        minimo=int(s.min()), promedio=round(float(s.mean()), 1),
        mediana=round(float(s.median()), 1), std=round(float(s.std()), 1),
        iqr=round(float(iqr), 1), asimetria=round(float(s.skew()), 3),
        curtosis=round(float(s.kurt()), 3),
        tiempo_alto=tiempo_alto, auc=int(auc),
    )

def auc_por_dia(df):
    rows = []
    for fecha, g in df.groupby("fecha"):
        s = g["gas_raw"]
        if len(s) > 1:
            t = g["timestamp"].astype(np.int64) / 1e9
            val = round(abs(float(np.trapezoid(s.values, t.values))) / 60, 0)
        else:
            val = 0
        prom = float(s.mean())
        nv = next((n for n, d in NIVELES.items() if d["min"] <= prom <= d["max"]), "CRITICO")
        rows.append({"fecha": str(fecha), "auc": val, "promedio": round(prom, 1), "nivel": nv})
    return pd.DataFrame(rows)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='padding:1.2rem 0 .8rem;'>
          <div style='font-family:Space Mono,monospace;font-size:1rem;font-weight:700;color:#f8fafc;'>🧪 GAS MONITOR</div>
          <div style='font-size:.68rem;color:#475569;font-family:Space Mono,monospace;margin-top:3px;'>
            CSV · ESP32+MQ2 · EAFIT 2026
          </div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div class="lbl">Navegación</div>', unsafe_allow_html=True)
        st.page_link("app.py",                  label="🏠  Inicio")
        st.page_link("pages/1_dashboard.py",    label="📊  Dashboard")
        st.page_link("pages/2_serie.py",        label="📈  Serie temporal")
        st.page_link("pages/3_estadisticos.py", label="🔬  Estadísticos")
        st.page_link("pages/4_anomalias.py",    label="⚠️  Anomalías")
        st.page_link("pages/5_datos.py",        label="🗄️  Datos")
        st.markdown("---")
        st.markdown("""
        <div style='font-size:.68rem;color:#334155;font-family:Space Mono,monospace;line-height:1.9;'>
          📁 gas_camara_datos.csv<br>
          📅 14 abr – 14 may 2026<br>
          📊 178,560 registros<br>
          ⏱️ Lectura cada 15 s
        </div>""", unsafe_allow_html=True)

# ─── Gauge Plotly ─────────────────────────────────────────────────────────────
def make_gauge(value, title, max_val, color, suffix="", height=200):
    import plotly.graph_objects as go
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 11, "color": "#64748b", "family": "Space Mono"}},
        number={"suffix": suffix, "font": {"size": 26, "color": "#f8fafc", "family": "Space Mono"}},
        gauge={
            "axis": {"range": [0, max_val], "tickcolor": "#1e1e35",
                     "tickfont": {"color": "#334155", "size": 9}},
            "bar":  {"color": color, "thickness": 0.28},
            "bgcolor": "#0f0f1e", "bordercolor": "#1e1e35", "borderwidth": 1,
            "threshold": {"line": {"color": color, "width": 3},
                          "thickness": 0.8, "value": value},
        }
    ))
    fig.update_layout(paper_bgcolor="#080810", height=height,
                      margin=dict(l=20, r=20, t=38, b=5))
    return fig
