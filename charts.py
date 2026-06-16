# charts.py — gráficos Plotly · mobile-first (newsletter CEG)

import numpy as np
import plotly.graph_objects as go
from config import (
    AXIS_LABELS, EVENT_PALETTE, HEATMAP_COLORSCALE,
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_H1, COLOR_H2, COLOR_H3,
    COLOR_BG_BODY, COLOR_TEXT, FONT_BODY, FONT_UI, RISK_PALETTE,
)

_BG_PLOT = "#fafaf8"
_GRID    = "#e8e3dc"

# largura alvo mobile ~400px → todos os gráficos desenhados para essa proporção
_W = 420
_FONT_BASE = 11   # base para labels e ticks


def _hex_to_rgba(h: str, a: float) -> str:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


def _base_layout(height: int = 500) -> dict:
    return dict(
        height=height,
        paper_bgcolor=COLOR_BG_BODY,
        plot_bgcolor=_BG_PLOT,
        font=dict(family=FONT_UI, size=_FONT_BASE, color=COLOR_TEXT),
    )


# ── scatter ───────────────────────────────────────────────────────────────────

def make_scatter(df, x_col: str, y_col: str, size_col: str, color_by: str) -> go.Figure:
    """
    Mobile-first: proporção vertical (alto > largo).
    Tamanho da bola = |RISK_SCORE|.
    Legenda empilhada à direita para não competir com o gráfico.
    Texto das bolhas pequeno e posicionado por rotação.
    """
    fig = go.Figure()
    events = sorted(df["EVENT_LETTER"].unique())

    max_score = df["RISK_SCORE"].abs().max() or 1.0
    sizeref   = 2.0 * max_score / (42 ** 2)   # bolas menores → menos sobreposição

    _positions = [
        "top center", "bottom center",
        "top right",  "bottom right",
        "top left",   "bottom left",
    ]

    for i, evt in enumerate(events):
        sub      = df[df["EVENT_LETTER"] == evt].copy().reset_index(drop=True)
        evt_name = sub["SHORT_EVENT"].iloc[0]

        marker_sizes  = sub["RISK_SCORE"].abs().tolist()
        marker_colors = (
            sub["RISK_COLOR"].tolist() if color_by == "risk"
            else [EVENT_PALETTE[i % len(EVENT_PALETTE)]] * len(sub)
        )
        text_positions = [_positions[j % len(_positions)] for j in range(len(sub))]

        hover = (
            "<b>%{customdata[0]}</b><br>"
            "<i>%{customdata[1]}</i><br>"
            f"Risk score: <b>%{{customdata[2]:+.3f}}</b><br>"
            f"{AXIS_LABELS.get(x_col, x_col)}: %{{x:.2f}}<br>"
            f"{AXIS_LABELS.get(y_col, y_col)}: %{{y:.2f}}<br>"
            "<extra></extra>"
        )

        fig.add_trace(go.Scatter(
            x=sub[x_col],
            y=sub[y_col],
            mode="markers+text",
            name=f"{evt} — {evt_name}",
            marker=dict(
                size=marker_sizes,
                sizemode="area",
                sizeref=sizeref,
                sizemin=8,
                color=marker_colors,
                opacity=0.87,
                line=dict(width=1.2, color="white"),
            ),
            text=sub["DIM_LABEL"],
            textposition=text_positions,
            textfont=dict(size=_FONT_BASE, color=COLOR_H2, family=FONT_UI),
            customdata=sub[["SHORT_EVENT", "DIM_LABEL", "RISK_SCORE", "TRUSTABILITY"]].values,
            hovertemplate=hover,
        ))

    # linhas de quadrante
    fig.add_hline(y=0.5, line_dash="dot", line_color=_GRID, line_width=1)
    fig.add_vline(x=0.0, line_dash="dot", line_color=COLOR_H3, line_width=1, opacity=0.4)

    # rótulos de quadrante — só no mobile ficam muito pequenos, então minimalistas
    for ax, ay, xanc, yanc, txt in [
        (-1.15, 1.12, "left",  "top",    "Alta prob. · Neg."),
        ( 0.03, 1.12, "left",  "top",    "Alta prob. · Pos."),
        (-1.15, 0.00, "left",  "bottom", "Baixa prob. · Neg."),
        ( 0.03, 0.00, "left",  "bottom", "Baixa prob. · Pos."),
    ]:
        fig.add_annotation(
            x=ax, y=ay, text=txt, showarrow=False,
            font=dict(size=8, color="#c8c4bc", family=FONT_UI),
            xanchor=xanc, yanchor=yanc,
        )

    fig.update_layout(
        **_base_layout(600),          # altura > largura esperada → proporção vertical
        margin=dict(l=8, r=8, t=16, b=8),
        legend=dict(
            orientation="v",          # empilhada verticalmente
            yanchor="top",   y=1.0,
            xanchor="left",  x=0,
            font=dict(size=10, family=FONT_UI, color=COLOR_TEXT),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=_GRID, borderwidth=1,
            itemsizing="constant",
            itemwidth=30,
        ),
        xaxis=dict(
            title=dict(text=AXIS_LABELS.get(x_col, x_col),
                       font=dict(size=_FONT_BASE, color=COLOR_H3)),
            gridcolor=_GRID, zeroline=False, range=[-1.2, 1.2],
            tickfont=dict(size=10, color=COLOR_H3),
        ),
        yaxis=dict(
            title=dict(text=AXIS_LABELS.get(y_col, y_col),
                       font=dict(size=_FONT_BASE, color=COLOR_H3)),
            gridcolor=_GRID, zeroline=False, range=[-0.05, 1.25],
            tickfont=dict(size=10, color=COLOR_H3),
        ),
    )
    return fig


# ── heatmap ───────────────────────────────────────────────────────────────────

def make_heatmap(df) -> go.Figure:
    """Mobile: eventos nas linhas, dimensões nas colunas com tickangle acentuado."""
    pivot = df.pivot_table(
        index="SHORT_EVENT", columns="DIM_LABEL",
        values="RISK_SCORE", aggfunc="mean",
    )

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=HEATMAP_COLORSCALE,
        zmid=0, zmin=-1, zmax=1,
        text=[[f"{v:+.2f}" if not np.isnan(v) else "–" for v in row]
              for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=10, family=FONT_BODY, color=COLOR_H2),
        hovertemplate="<b>%{y}</b><br>%{x}<br>Risk score: <b>%{z:+.3f}</b><extra></extra>",
        colorbar=dict(
            title=dict(text="Score", font=dict(size=9, color=COLOR_H3)),
            tickvals=[-1, -0.5, 0, 0.5, 1],
            tickfont=dict(size=8, color=COLOR_H3),
            len=0.7, thickness=12,
        ),
    ))

    n_rows = len(pivot)
    n_cols = len(pivot.columns)
    fig.update_layout(
        **_base_layout(max(280, n_rows * 70 + n_cols * 18 + 60)),
        margin=dict(l=4, r=4, t=8, b=8),
        xaxis=dict(
            side="top", tickangle=-45,
            tickfont=dict(size=9, color=COLOR_H3, family=FONT_UI),
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=10, color=COLOR_H3, family=FONT_UI),
        ),
    )
    return fig


# ── ranking (bar horizontal) ──────────────────────────────────────────────────

def make_bar(df) -> go.Figure:
    """Mobile: barras horizontais, labels curtos, altura proporcional ao nº de eventos."""
    from data import risk_color

    agg = (
        df.groupby(["EVENT_LETTER", "SHORT_EVENT"])["RISK_SCORE"]
          .mean()
          .reset_index()
          .sort_values("RISK_SCORE")
    )
    colors = [risk_color(s) for s in agg["RISK_SCORE"]]

    fig = go.Figure(go.Bar(
        x=agg["RISK_SCORE"],
        y=agg["SHORT_EVENT"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0), opacity=0.88),
        text=[f"{v:+.2f}" for v in agg["RISK_SCORE"]],
        textposition="outside",
        textfont=dict(size=11, family=FONT_BODY, color=COLOR_H2),
        hovertemplate="<b>%{y}</b><br>Score médio: <b>%{x:+.3f}</b><extra></extra>",
    ))

    fig.add_vline(x=0, line_color=COLOR_H2, line_width=1.5)

    fig.update_layout(
        **_base_layout(max(220, len(agg) * 56 + 60)),
        margin=dict(l=4, r=60, t=8, b=8),
        xaxis=dict(
            title=dict(text="Risk score médio", font=dict(size=_FONT_BASE, color=COLOR_H3)),
            gridcolor=_GRID, zeroline=False, range=[-1.2, 1.2],
            tickfont=dict(size=10, color=COLOR_H3),
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=10, color=COLOR_H2, family=FONT_UI),
            automargin=True,
        ),
    )
    return fig


# ── radar ─────────────────────────────────────────────────────────────────────

def make_radar(df, event_letter: str) -> go.Figure | None:
    """Mobile: margens menores, labels do eixo angular mais compactos."""
    sub = df[df["EVENT_LETTER"] == event_letter].copy()
    if sub.empty:
        return None

    categories = sub["DIM_LABEL"].tolist() + [sub["DIM_LABEL"].iloc[0]]
    scores     = sub["RISK_SCORE"].tolist() + [sub["RISK_SCORE"].iloc[0]]

    from data import risk_color
    line_color = risk_color(sub["RISK_SCORE"].mean())
    fill_color = _hex_to_rgba(line_color, 0.15)

    fig = go.Figure(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill="toself",
        fillcolor=fill_color,
        line=dict(color=line_color, width=2),
        marker=dict(size=6, color=line_color),
        hovertemplate="<b>%{theta}</b><br>Risk score: <b>%{r:+.3f}</b><extra></extra>",
    ))

    fig.update_layout(
        height=360,
        margin=dict(l=40, r=40, t=32, b=32),
        paper_bgcolor=COLOR_BG_BODY,
        polar=dict(
            bgcolor=_BG_PLOT,
            radialaxis=dict(
                visible=True, range=[-1, 1],
                tickfont=dict(size=8, color=COLOR_H3),
                gridcolor=_GRID,
                tickvals=[-1, -0.5, 0, 0.5, 1],
            ),
            angularaxis=dict(
                tickfont=dict(size=9, color=COLOR_H2, family=FONT_UI),
                gridcolor=_GRID,
            ),
        ),
        font=dict(family=FONT_UI, size=10, color=COLOR_TEXT),
    )
    return fig