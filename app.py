# app.py — entry point · mobile-first / retrato
import streamlit as st
from config import GLOBAL_CSS
from sidebar import render_sidebar
from charts import make_scatter, make_heatmap, make_bar, make_radar

st.set_page_config(
    page_title="Risk Score Visualizer",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",   # sidebar fechada por padrão no mobile
)

# CSS adicional: coluna central com largura máxima de 480px (retrato)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
  /* container central estreito — simula tela de celular */
  .main .block-container {
    max-width: 480px !important;
    margin: 0 auto !important;
    padding-left: 12px !important;
    padding-right: 12px !important;
  }
  /* tabs mais compactas */
  .stTabs [data-baseweb="tab"] { font-size: 12px !important; padding: 6px 10px !important; }
  /* métricas em grid 2×3 no mobile */
  div[data-testid="column"] { min-width: 0 !important; }
</style>
""", unsafe_allow_html=True)

_CHART_CFG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "zoom2d","pan2d","select2d","lasso2d",
        "zoomIn2d","zoomOut2d","autoScale2d","resetScale2d",
        "hoverClosestCartesian","hoverCompareCartesian","toggleSpikelines",
    ],
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "displaylogo": False,
    "responsive": True,   # redimensiona com o container
}

# ── sidebar + dados ────────────────────────────────────────────────────────────
df, controls = render_sidebar()

if df is None or df.empty:
    st.info("Carregue um arquivo ou use o exemplo embutido para começar.")
    st.stop()

# ── header ─────────────────────────────────────────────────────────────────────
st.markdown("## Risk Score Visualizer")
st.caption("Análise de eventos geopolíticos e dimensões de risco")

# ── KPIs — 2 colunas para caber em retrato ────────────────────────────────────
r1c1, r1c2 = st.columns(2)
r2c1, r2c2 = st.columns(2)
r3c1, _    = st.columns(2)

r1c1.metric("Eventos",     df["EVENT_LETTER"].nunique())
r1c2.metric("Dimensões",   len(df))
r2c1.metric("Score médio", f"{df['RISK_SCORE'].mean():+.3f}")
r2c2.metric("Score mín",   f"{df['RISK_SCORE'].min():+.3f}")
r3c1.metric("Score máx",   f"{df['RISK_SCORE'].max():+.3f}")

st.markdown("---")

# ── abas ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🔵 Scatter", "🔥 Heatmap", "📊 Ranking", "🕸 Radar"])

with tab1:
    st.caption("Impacto × Probabilidade — tamanho = |risk score|")
    st.plotly_chart(
        make_scatter(df, controls["x_axis"], controls["y_axis"],
                     controls["size_col"], controls["color_by"]),
        use_container_width=True,
        config=_CHART_CFG,
    )

with tab2:
    st.caption("Eventos × Dimensões — cor = risk score")
    st.plotly_chart(
        make_heatmap(df),
        use_container_width=True,
        config=_CHART_CFG,
    )

with tab3:
    st.caption("Risk score médio por evento")
    st.plotly_chart(
        make_bar(df),
        use_container_width=True,
        config=_CHART_CFG,
    )

with tab4:
    radar_event = st.selectbox(
        "Evento", sorted(df["EVENT_LETTER"].unique()), key="radar_sel",
    )
    fig_radar = make_radar(df, radar_event)
    if fig_radar:
        evt_name = df[df["EVENT_LETTER"] == radar_event]["EVENT_KEYWORD"].iloc[0]
        st.caption(f"**{radar_event}** — {evt_name}")
        st.plotly_chart(fig_radar, use_container_width=True, config=_CHART_CFG)
    else:
        st.info("Sem dados para este evento.")

# ── tabela ──────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("🗂 Tabela detalhada"):
    display_cols = ["EVENT_KEYWORD","DIM_LABEL","PROB_VD_IV","IMPACT","RISK_SCORE","RISK_LABEL"]
    available = [c for c in display_cols if c in df.columns]
    st.dataframe(
        df[available]
          .rename(columns={"DIM_LABEL":"DIMENSÃO","RISK_LABEL":"CLASSE"})
          .sort_values("RISK_SCORE"),
        use_container_width=True,
        hide_index=True,
        column_config={
            "RISK_SCORE": st.column_config.NumberColumn(format="%+.3f"),
            "PROB_VD_IV": st.column_config.NumberColumn(format="%.2f"),
            "IMPACT":     st.column_config.NumberColumn(format="%.2f"),
        },
    )