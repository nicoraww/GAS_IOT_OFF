# 🧪 Gas Cámara Monitor

Análisis histórico de exposición a gas en cámara de resistencia de materiales.
**100 % offline — alimentado por CSV, sin dependencias externas.**

`ESP32 + MQ2 (Wokwi)` → `InfluxDB` → `CSV` → **`Streamlit`**

---

## 📁 Archivos del repo

```
/
├── app.py                       # Inicio — resumen y contexto
├── utils.py                     # Carga CSV, helpers, CSS
├── gas_camara_datos.csv         # Dataset: 178,560 registros · 30 días
├── requirements.txt
├── .streamlit/config.toml
└── pages/
    ├── 1_dashboard.py           # Gauges, KPIs, serie diaria, AUC
    ├── 2_serie.py               # Serie temporal + heatmap
    ├── 3_estadisticos.py        # Descriptivos, boxplot, histograma, MM, AUC
    ├── 4_anomalias.py           # Z-score, tasa de cambio
    └── 5_datos.py               # Explorador + descarga CSV
```

## 🚀 Despliegue en Streamlit Cloud

1. Sube este repositorio a GitHub (con el CSV incluido)
2. [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Selecciona el repo → main file: **`app.py`** → **Deploy**

## 💻 Local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📊 Dataset

| Campo | Descripción |
|---|---|
| `timestamp` | Fecha y hora de la lectura |
| `gas_raw` | Valor ADC del sensor MQ2 (0–4095) |
| `estado` | Nivel: SEGURO · TRAZA · LEVE · MODERADO · ALTO · CRITICO |

- **Período:** 14 abril – 14 mayo 2026
- **Registros:** 178,560 (cada 15 segundos)
- **Sensor:** ESP32 + MQ2 simulado en Wokwi

---
EAFIT · Ingeniería IoT · 2026
