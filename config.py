# config.py — paleta CEG, thresholds e labels globais

# ── Paleta CEG ────────────────────────────────────────────────────────────────
COLOR_PRIMARY   = "#26619C"
COLOR_SECONDARY = "#acac95"
COLOR_BG_EMAIL  = "#f2f2f2"
COLOR_BG_BODY   = "#ffffff"
COLOR_TEXT      = "#2e2e2e"
COLOR_H1        = "#26619C"
COLOR_H2        = "#1a1a1a"
COLOR_H3        = "#555555"
FONT_BODY       = "Georgia, 'Times New Roman', serif"
FONT_UI         = "Arial, Helvetica, sans-serif"

# ── Risk palette (vermelho → neutro → azul CEG) ───────────────────────────────
RISK_PALETTE = {
    "critical": "#c0392b",   # vermelho escuro
    "high":     "#e67e22",   # laranja
    "moderate": "#acac95",   # secundária CEG (neutro)
    "low":      "#5dade2",   # azul claro
    "positive": "#26619C",   # azul primário CEG
}

# Thresholds: score <= valor → label
RISK_THRESHOLDS = [
    (-0.4, "critical"),
    (-0.1, "high"),
    ( 0.1, "moderate"),
    ( 0.3, "low"),
]
RISK_DEFAULT_LABEL = "positive"

AXIS_LABELS = {
    "IMPACT":      "Impacto",
    "PROB_DV_IV":  "Probabilidade condicional",
    "TRUSTABILITY":"Confiabilidade",
    "RISK_SCORE":  "Risk Score",
}

# Paleta de eventos (tons do azul CEG + complementares)
EVENT_PALETTE = [
    "#26619C",  # primário CEG
    "#acac95",  # secundário CEG
    "#5dade2",  # azul claro
    "#1a5276",  # azul escuro
    "#7f8c8d",  # cinza
    "#2e86c1",  # azul médio
]

HEATMAP_COLORSCALE = [
    [0.00, "#c0392b"],   # critical
    [0.35, "#e67e22"],   # high
    [0.50, "#f5f5f0"],   # neutro (quase branco levemente quente)
    [0.65, "#5dade2"],   # low
    [1.00, "#26619C"],   # positive — azul CEG
]

GLOBAL_CSS = f"""
<style>
  html, body, [class*="css"] {{
    font-family: {FONT_UI};
    color: {COLOR_TEXT};
  }}
  .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}
  h1 {{
    font-size: 1.4rem !important; font-weight: 700 !important;
    color: {COLOR_H1} !important; font-family: {FONT_BODY} !important;
    letter-spacing: -0.01em;
  }}
  h2 {{
    font-size: 0.75rem !important; font-weight: 600 !important;
    color: {COLOR_H3} !important; font-family: {FONT_UI} !important;
    letter-spacing: 0.08em; text-transform: uppercase;
  }}
  .stMetric {{
    background: {COLOR_BG_BODY};
    border: 1px solid #e0dbd4;
    border-radius: 8px;
    padding: 0.75rem 1rem;
  }}
  .stMetric label {{
    font-size: 0.68rem !important; text-transform: uppercase;
    letter-spacing: 0.07em; color: {COLOR_H3} !important;
    font-family: {FONT_UI} !important;
  }}
  .stMetric [data-testid="metric-container"] > div:nth-child(2) {{
    font-family: {FONT_BODY} !important;
    font-size: 1.4rem;
    color: {COLOR_H1};
  }}
  div[data-testid="stSidebar"] {{
    background: {COLOR_H2} !important;
    border-right: 1px solid #333;
  }}
  div[data-testid="stSidebar"] * {{ color: #e8e4de !important; }}
  div[data-testid="stSidebar"] label {{
    color: {COLOR_SECONDARY} !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: .06em;
  }}
</style>
"""
