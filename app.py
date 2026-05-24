"""app.py — Página de inicio: contexto, resumen del dataset y escala de niveles."""
import streamlit as st
from utils import CSS, ORDEN, NIVELES, C, load, metricas, sidebar

st.set_page_config(page_title="Gas Monitor · Inicio", page_icon="🧪", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
sidebar()

df = load()
met = metricas(df)

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding:2.2rem 0 1.2rem;'>
  <div style='font-family:Space Mono,monospace;font-size:.7rem;color:#22c55e;
              letter-spacing:.2em;text-transform:uppercase;margin-bottom:.5rem;'>
    EAFIT · Ingeniería IoT · 2026
  </div>
  <h1 style='font-size:2.5rem;font-weight:700;line-height:1.1;margin:0;
             background:linear-gradient(135deg,#f8fafc 0%,#94a3b8 100%);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
    Sistema de Monitoreo<br>de Cámara de Gas
  </h1>
  <p style='color:#64748b;font-size:.92rem;margin-top:.8rem;max-width:580px;line-height:1.75;'>
    Análisis histórico de exposición a gas en cámara de pruebas de resistencia de materiales.
    Sensor <strong style='color:#94a3b8;'>ESP32 + MQ2</strong> (Wokwi) · 30 días · 178 K registros.
  </p>
</div>
""", unsafe_allow_html=True)

# ─── KPIs globales ────────────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Resumen del dataset completo</div>', unsafe_allow_html=True)
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Total registros",  f"{met['total']:,}")
c2.metric("Días de datos",    f"{met['dias']}")
c3.metric("Pico máximo",      f"{met['pico']} ADC")
c4.metric("Promedio global",  f"{met['promedio']} ADC")
c5.metric("Período inicio",   str(df['fecha'].min()))
c6.metric("Período fin",      str(df['fecha'].max()))

# ─── Distribución global ──────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Distribución por nivel — dataset completo</div>', unsafe_allow_html=True)
conteo = df["estado"].value_counts()
total  = len(df)
cols   = st.columns(6)
for col, nombre in zip(cols, ORDEN):
    n   = conteo.get(nombre, 0)
    pct = n / total * 100
    color = C[nombre]
    col.markdown(f"""
    <div style='background:#0f0f1e;border:1px solid #1e1e35;border-top:3px solid {color};
                border-radius:12px;padding:.9rem;text-align:center;'>
      <div style='font-family:Space Mono,monospace;font-size:.72rem;font-weight:700;
                  color:{color};margin-bottom:.25rem;'>{nombre}</div>
      <div style='font-size:1.5rem;font-weight:700;color:#f8fafc;
                  font-family:Space Mono,monospace;'>{pct:.1f}%</div>
      <div style='font-size:.65rem;color:#475569;margin-top:.2rem;'>{n:,} lecturas</div>
    </div>""", unsafe_allow_html=True)

# ─── Descripción + stack ──────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Proyecto</div>', unsafe_allow_html=True)
ca, cb = st.columns([3, 2])
with ca:
    st.markdown("""
    <div class='card'>
      <div style='font-family:Space Mono,monospace;font-size:.7rem;color:#22c55e;margin-bottom:.6rem;'>
        CÁMARA DE RESISTENCIA A GAS
      </div>
      <p style='color:#94a3b8;font-size:.86rem;line-height:1.8;margin:0;'>
        Una <strong style='color:#f8fafc;'>cámara de pruebas</strong> expone placas metálicas y
        materiales compuestos a gases controlados (GLP, metano, humo) para medir su degradación
        bajo exposición prolongada.<br><br>
        El sensor mide la concentración cada 15 s y la clasifica en 6 niveles.
        La métrica principal es la <strong style='color:#f97316;'>dosis acumulada (AUC)</strong>
        — cuánto gas total han recibido las placas, expresado en ADC·min.
      </p>
    </div>""", unsafe_allow_html=True)
with cb:
    st.markdown("""
    <div class='card'>
      <div style='font-family:Space Mono,monospace;font-size:.7rem;color:#22c55e;margin-bottom:.6rem;'>
        STACK TECNOLÓGICO
      </div>
      <div style='font-size:.82rem;color:#94a3b8;line-height:2.2;'>
        🔌 <strong style='color:#f8fafc;'>Wokwi</strong> — ESP32 + MQ2 simulado<br>
        📡 <strong style='color:#f8fafc;'>InfluxDB</strong> — Time-series cloud<br>
        📊 <strong style='color:#f8fafc;'>Grafana</strong> — Gauges tiempo real<br>
        🐍 <strong style='color:#f8fafc;'>Streamlit</strong> — Análisis histórico CSV<br>
        📓 <strong style='color:#f8fafc;'>Google Colab</strong> — Análisis estadístico
      </div>
    </div>""", unsafe_allow_html=True)

# ─── Escala niveles ───────────────────────────────────────────────────────────
st.markdown('<div class="lbl">● Escala de niveles MQ2 (ADC 0–4095)</div>', unsafe_allow_html=True)
info = [
    ("SEGURO",  "#22c55e","0–400",     "Sin gas"),
    ("TRAZA",   "#3b82f6","401–800",   "Mínimo"),
    ("LEVE",    "#eab308","801–1200",  "Bajo"),
    ("MODERADO","#f97316","1201–1800", "Activo"),
    ("ALTO",    "#ef4444","1801–2800", "Alerta"),
    ("CRITICO", "#a855f7","2801–4095", "Saturación"),
]
cols2 = st.columns(6)
for col, (nombre, color, rango, desc) in zip(cols2, info):
    col.markdown(f"""
    <div style='background:#0f0f1e;border:1px solid #1e1e35;border-left:3px solid {color};
                border-radius:10px;padding:.75rem .9rem;'>
      <div style='font-family:Space Mono,monospace;font-size:.7rem;font-weight:700;color:{color};'>{nombre}</div>
      <div style='font-size:.65rem;color:#64748b;font-family:Space Mono,monospace;margin-top:2px;'>{rango} ADC</div>
      <div style='font-size:.65rem;color:#475569;margin-top:2px;'>{desc}</div>
    </div>""", unsafe_allow_html=True)
