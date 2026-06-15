# app.py — entry point
# Executar com: streamlit run app.py

import streamlit as st
from config import GLOBAL_CSS
from sidebar import render_sidebar
from charts import make_scatter, make_heatmap, make_bar, make_radar

# ── configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Risk Score Visualizer",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── sidebar + dados ───────────────────────────────────────────────────────────
df, controls = render_sidebar()

# ── guard: sem dados ──────────────────────────────────────────────────────────
if df is None or df.empty:
    st.info("Carregue um arquivo ou use o exemplo embutido para começar.")
    st.stop()

# ── header ────────────────────────────────────────────────────────────────────
st.markdown("## Risk Score Visualizer")
st.caption("Análise de eventos geopolíticos e dimensões de risco")
st.markdown("")

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Eventos",     df["EVENT_LETTER"].nunique())
k2.metric("Dimensões",   len(df))
k3.metric("Score médio", f"{df['RISK_SCORE'].mean():+.3f}")
k4.metric("Score mín",   f"{df['RISK_SCORE'].min():+.3f}")
k5.metric("Score máx",   f"{df['RISK_SCORE'].max():+.3f}")

st.markdown("---")

# ── abas de visualização ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🔵 Scatter", "🔥 Heatmap", "📊 Ranking", "🕸 Radar"])

with tab1:
    st.markdown("**Impacto × Probabilidade**")
    st.plotly_chart(
        make_scatter(df, controls["x_axis"], controls["y_axis"],
                     controls["size_col"], controls["color_by"]),
        use_container_width=True,
        config={"displayModeBar": True},
    )
    st.caption("Quadrantes de impacto: esquerda = negativo | direita = positivo | cima = alta probabilidade")

with tab2:
    st.markdown("**Heatmap**")
    st.plotly_chart(
        make_heatmap(df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with tab3:
    st.markdown("**Risk score médio por evento**")
    st.plotly_chart(
        make_bar(df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with tab4:
    st.markdown("**Radar por evento**")
    radar_event = st.selectbox(
        "Selecione o evento",
        sorted(df["EVENT_LETTER"].unique()),
        key="radar_sel",
    )
    fig_radar = make_radar(df, radar_event)
    if fig_radar:
        evt_name = df[df["EVENT_LETTER"] == radar_event]["EVENT_KEYWORD"].iloc[0]
        st.caption(f"**{radar_event}** — {evt_name}")
        st.plotly_chart(fig_radar, use_container_width=True,
                        config={"displayModeBar": False})
    else:
        st.info("Sem dados para este evento.")

# ── tabela detalhada ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("🗂 Tabela detalhada", expanded=False):
    display_cols = [
        "ID_DIMENSION", "EVENT_KEYWORD", "DIM_LABEL",
        "PROB_VD_IV", "IMPACT", "TRUSTABILITY", "RISK_SCORE", "RISK_LABEL",
    ]
    available = [c for c in display_cols if c in df.columns]
    st.dataframe(
        df[available]
          .rename(columns={"DIM_LABEL": "DIMENSION", "RISK_LABEL": "CLASSIFICAÇÃO"})
          .sort_values("RISK_SCORE"),
        use_container_width=True,
        hide_index=True,
    )
