# app.py — entry point
import streamlit as st
from config import GLOBAL_CSS
from sidebar import render_sidebar
from charts import (
    make_scatter, make_heatmap, make_bar, make_radar,
    export_scatter_portrait_mpl,
    export_heatmap_portrait,
    export_bar_portrait, export_radar_portrait,
)

st.set_page_config(
    page_title="Risk Score Visualizer",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

_CHART_CFG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "zoom2d","pan2d","select2d","lasso2d",
        "zoomIn2d","zoomOut2d","autoScale2d","resetScale2d",
        "hoverClosestCartesian","hoverCompareCartesian","toggleSpikelines",
    ],
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "displaylogo": False,
}

# ── sidebar + dados ────────────────────────────────────────────────────────────
df, controls = render_sidebar()

if df is None or df.empty:
    st.info("Carregue um arquivo ou use o exemplo embutido para começar.")
    st.stop()

# ── header ─────────────────────────────────────────────────────────────────────
st.markdown("## Risk Score Visualizer")
st.caption("Análise de eventos geopolíticos e dimensões de risco")
st.markdown("")

# ── KPIs ───────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Eventos",     df["EVENT_LETTER"].nunique())
k2.metric("Dimensões",   len(df))
k3.metric("Score médio", f"{df['RISK_SCORE'].mean():+.3f}")
k4.metric("Score mín",   f"{df['RISK_SCORE'].min():+.3f}")
k5.metric("Score máx",   f"{df['RISK_SCORE'].max():+.3f}")

st.markdown("---")

# ── helper: botão de download portrait ────────────────────────────────────────
def _dl_button(png_bytes: bytes, filename: str):
    st.download_button(
        label="📱 Baixar versão mobile (retrato)",
        data=png_bytes,
        file_name=filename,
        mime="image/png",
        use_container_width=False,
    )

# ── abas ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🔵 Scatter", "🔥 Heatmap", "📊 Ranking", "🕸 Radar"])

with tab1:
    st.markdown("**Impacto × Probabilidade**")
    fig1 = make_scatter(df, controls["x_axis"], controls["y_axis"],
                        controls["size_col"], controls["color_by"],
                        font_size=controls["font_size"],
                        show_labels=controls["show_labels"],
                        position_mode=controls["position_mode"],
                        fixed_position=controls["fixed_position"],
                        individual_positions=controls["individual_positions"])
    st.plotly_chart(fig1, use_container_width=True, config=_CHART_CFG)
    st.caption("Quadrantes: esquerda = impacto negativo | direita = positivo | cima = alta probabilidade")

    with st.expander("📱 Exportar para mobile / newsletter"):
        st.caption("PNG 420×700px · otimizado para celular e email")
        if st.button("Gerar PNG retrato", key="gen_scatter"):
            with st.spinner("Gerando…"):
                png = export_scatter_portrait_mpl(
                    df, controls["x_axis"], controls["y_axis"],
                    controls["size_col"], controls["color_by"],
                    font_size=max(6, controls["font_size"] - 7),  # px → pt aprox.
                    show_labels=controls["show_labels"],
                    position_mode=controls["position_mode"],
                )
            _dl_button(png, "scatter_mobile.png")

with tab2:
    st.markdown("**Heatmap**")
    fig2 = make_heatmap(df)
    st.plotly_chart(fig2, use_container_width=True, config=_CHART_CFG)

    with st.expander("📱 Exportar para mobile / newsletter"):
        if st.button("Gerar PNG retrato", key="gen_heatmap"):
            with st.spinner("Gerando…"):
                png = export_heatmap_portrait(df)
            _dl_button(png, "heatmap_mobile.png")

with tab3:
    st.markdown("**Risk score médio por evento**")
    fig3 = make_bar(df)
    st.plotly_chart(fig3, use_container_width=True, config=_CHART_CFG)

    with st.expander("📱 Exportar para mobile / newsletter"):
        if st.button("Gerar PNG retrato", key="gen_bar"):
            with st.spinner("Gerando…"):
                png = export_bar_portrait(df)
            _dl_button(png, "ranking_mobile.png")

with tab4:
    st.markdown("**Radar por evento**")
    radar_event = st.selectbox(
        "Selecione o evento",
        sorted(df["EVENT_LETTER"].unique()),
        key="radar_sel",
    )
    fig4 = make_radar(df, radar_event)
    if fig4:
        evt_name = df[df["EVENT_LETTER"] == radar_event]["EVENT_KEYWORD"].iloc[0]
        st.caption(f"**{radar_event}** — {evt_name}")
        st.plotly_chart(fig4, use_container_width=True, config=_CHART_CFG)

        with st.expander("📱 Exportar para mobile / newsletter"):
            if st.button("Gerar PNG retrato", key="gen_radar"):
                with st.spinner("Gerando…"):
                    png = export_radar_portrait(df, radar_event)
                if png:
                    _dl_button(png, f"radar_{radar_event}_mobile.png")
    else:
        st.info("Sem dados para este evento.")

# ── tabela ──────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("🗂 Tabela detalhada", expanded=False):
    display_cols = [
        "ID_DIMENSION", "EVENT_KEYWORD", "DIM_LABEL",
        "PROB_DV_IV", "IMPACT", "TRUSTABILITY", "RISK_SCORE", "RISK_LABEL",
    ]
    available = [c for c in display_cols if c in df.columns]
    st.dataframe(
        df[available]
          .rename(columns={"DIM_LABEL": "DIMENSION", "RISK_LABEL": "CLASSIFICAÇÃO"})
          .sort_values("RISK_SCORE"),
        use_container_width=True,
        hide_index=True,
    )