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

        _AXIS_OPTS = ["IMPACT", "PROB_VD_IV", "TRUSTABILITY"]
        # filtra apenas colunas presentes no df atual
        _avail = [c for c in _AXIS_OPTS if df is not None and c in df.columns] or _AXIS_OPTS

        x_axis = st.selectbox("Eixo X", _avail, index=0)
        _y_opts = _avail  # permite mesmo eixo (Plotly suporta)
        y_axis = st.selectbox(
            "Eixo Y", _y_opts,
            index=min(1, len(_y_opts) - 1),  # default: segunda opção se existir
        )
        size_col = st.selectbox("Tamanho do ponto", _avail, index=0)
        color_by = st.radio("Cor por", ["risk", "evento"], horizontal=True)

        # ── controles de rótulo (bolhas) ─────────────────────────────────────
        st.markdown("---")
        st.markdown("**Scatter – rótulos**")

        n_dims = len(df) if df is not None else 0
        show_labels = st.toggle(
            "Mostrar rótulos nas bolhas", value=(n_dims <= 12),
            help="Desative quando houver muitas dimensões próximas e os "
                 "rótulos colidirem. O hover continua disponível mesmo "
                 "desativado; a versão exportada (PNG) pode ser editada "
                 "por fora (PowerPoint, Canva etc.) se precisar de rótulos.",
        )
        font_size = st.slider(
            "Tamanho da fonte", min_value=9, max_value=22, value=17, step=1,
            disabled=not show_labels,
        )

    controls = {
        "x_axis":      x_axis,
        "y_axis":      y_axis,
        "size_col":    size_col,
        "color_by":    color_by,
        "font_size":   font_size,
        "show_labels": show_labels,
    }
    return df, controls