# sidebar.py — sidebar com upload, filtros e controles de visualização

import streamlit as st
import pandas as pd
from data import load_file, preprocess
from sample_data import load_sample


def render_sidebar() -> tuple[pd.DataFrame | None, dict]:
    """
    Renderiza a sidebar completa e retorna:
      - df: DataFrame pré-processado e filtrado (ou None se sem dados)
      - controls: dict com as opções de visualização selecionadas pelo usuário
    """
    with st.sidebar:
        st.markdown("### ⬡ Risk Visualizer")
        st.markdown("---")

        # ── fonte de dados ────────────────────────────────────────────────────
        st.markdown("**Dados**")
        data_source = st.radio(
            "Fonte", ["Exemplo embutido", "Upload CSV / Excel"],
            label_visibility="collapsed",
        )

        df_raw = None
        if data_source == "Upload CSV / Excel":
            uploaded = st.file_uploader("Arquivo", type=["csv", "xlsx", "xls"])
            if uploaded:
                try:
                    df_raw = load_file(uploaded)
                    st.success(f"{len(df_raw)} linhas carregadas")
                except Exception as e:
                    st.error(f"Erro ao carregar arquivo: {e}")
        else:
            df_raw = load_sample()
            st.caption("Usando dados de exemplo (3 eventos, 9 dimensões)")

        # ── filtros ───────────────────────────────────────────────────────────
        df = None
        if df_raw is not None:
            df = preprocess(df_raw)

            st.markdown("---")
            st.markdown("**Filtros**")

            all_events = sorted(df["EVENT_LETTER"].unique())
            sel_events = st.multiselect("Eventos", all_events, default=all_events)
            df = df[df["EVENT_LETTER"].isin(sel_events)]

            risk_range = st.slider(
                "Faixa de risk score", -1.0, 1.0, (-1.0, 1.0), step=0.05,
            )
            df = df[
                (df["RISK_SCORE"] >= risk_range[0]) &
                (df["RISK_SCORE"] <= risk_range[1])
            ]

        # ── controles de scatter ──────────────────────────────────────────────
        st.markdown("---")
        st.markdown("**Scatter – eixos**")

        x_axis = st.selectbox(
            "Eixo X", ["IMPACT", "PROB_VD_IV", "TRUSTABILITY"], index=0,
        )
        y_axis = st.selectbox(
            "Eixo Y", ["PROB_VD_IV", "IMPACT", "TRUSTABILITY"], index=0,
        )
        size_col = st.selectbox(
            "Tamanho do ponto", ["TRUSTABILITY", "PROB_VD_IV", "IMPACT"], index=0,
        )
        color_by = st.radio("Cor por", ["risk", "evento"], horizontal=True)

    controls = {
        "x_axis":   x_axis,
        "y_axis":   y_axis,
        "size_col": size_col,
        "color_by": color_by,
    }
    return df, controls
