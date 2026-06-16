# charts.py — gráficos Plotly com paleta CEG

import numpy as np
import plotly.graph_objects as go
from config import (
    AXIS_LABELS, EVENT_PALETTE, HEATMAP_COLORSCALE,
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_H1, COLOR_H2, COLOR_H3,
    COLOR_BG_BODY, COLOR_TEXT, FONT_BODY, FONT_UI, RISK_PALETTE,
)

_BG_PLOT = "#fafaf8"
_GRID    = "#e8e3dc"


def _hex_to_rgba(h: str, a: float) -> str:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


def _base_layout(height: int = 500) -> dict:
    return dict(
        height=height,
        paper_bgcolor=COLOR_BG_BODY,
        plot_bgcolor=_BG_PLOT,
        font=dict(family=FONT_UI, size=15, color=COLOR_TEXT),
    )


# ── scatter ───────────────────────────────────────────────────────────────────

def make_scatter(df, x_col: str, y_col: str, size_col: str, color_by: str) -> go.Figure:
    """
    Tamanho da bola = |RISK_SCORE| (sizeref normalizado).
    Cor = RISK_COLOR (por risco) ou EVENT_PALETTE (por evento).
    Texto: label da dimensão com posição adaptativa por quadrante.
    """
    fig = go.Figure()
    events = sorted(df["EVENT_LETTER"].unique())

    # sizeref: sizemode="area" — |score|=1.0 → ~55px diâmetro
    max_score = df["RISK_SCORE"].abs().max() or 1.0
    sizeref   = 2.0 * max_score / (55 ** 2)

    for i, evt in enumerate(events):
        sub      = df[df["EVENT_LETTER"] == evt].copy().reset_index(drop=True)
        evt_name = sub["SHORT_EVENT"].iloc[0]

        marker_sizes  = sub["RISK_SCORE"].abs().tolist()

        if color_by == "risk":
            marker_colors = sub["RISK_COLOR"].tolist()
        else:
            marker_colors = [EVENT_PALETTE[i % len(EVENT_PALETTE)]] * len(sub)

        # rotação de posições para reduzir sobreposição
        _positions = ["top center", "bottom center", "top right",
                      "bottom right", "top left", "bottom left"]
        text_positions = [
            _positions[j % len(_positions)]
            for j in range(len(sub))
        ]

        hover = (
            "<b>%{customdata[0]}</b><br>"
            "<i>%{customdata[1]}</i><br>"
            f"Risk score: <b>%{{customdata[2]:+.3f}}</b><br>"
            f"{AXIS_LABELS.get(x_col, x_col)}: %{{x:.2f}}<br>"
            f"{AXIS_LABELS.get(y_col, y_col)}: %{{y:.2f}}<br>"
            "Confiabilidade: %{customdata[3]:.2f}"
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
                sizemin=17,
                color=marker_colors,
                opacity=0.85,
                line=dict(width=1.5, color="white"),
            ),
            text=sub["DIM_LABEL"],
            textposition=text_positions,
            textfont=dict(size=17, color=COLOR_H2, family=FONT_UI),
            customdata=sub[["SHORT_EVENT", "DIM_LABEL", "RISK_SCORE", "TRUSTABILITY"]].values,
            hovertemplate=hover,
        ))

    # linhas de quadrante
    fig.add_hline(y=0.5, line_dash="dot", line_color=_GRID, line_width=1)
    fig.add_vline(x=0.0, line_dash="dot", line_color=COLOR_H3, line_width=1, opacity=0.5)

    # rótulos de quadrante — discretos, cantos
    for ax, ay, xanc, yanc, txt in [
        (-1.18, 1.08, "left",  "top",    "Alta prob. · Impacto negativo"),
        ( 0.02, 1.08, "left",  "top",    "Alta prob. · Impacto positivo"),
        (-1.18, 0.01, "left",  "bottom", "Baixa prob. · Impacto negativo"),
        ( 0.02, 0.01, "left",  "bottom", "Baixa prob. · Impacto positivo"),
    ]:
        fig.add_annotation(
            x=ax, y=ay, text=txt, showarrow=False,
            font=dict(size=14, color="#c0bdb5", family=FONT_UI),
            xanchor=xanc, yanchor=yanc,
        )

    fig.update_layout(
        **_base_layout(600),
        margin=dict(l=10, r=20, t=80, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left",   x=0,
            font=dict(size=17, family=FONT_UI, color=COLOR_TEXT),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=_GRID, borderwidth=1,
            itemsizing="constant",
            tracegroupgap=4,
        ),
        xaxis=dict(
            title=dict(text=AXIS_LABELS.get(x_col, x_col), font=dict(size=17, color=COLOR_H3)),
            gridcolor=_GRID, zeroline=False, range=[-1.25, 1.25],
            tickfont=dict(size=17, color=COLOR_H3),
        ),
        yaxis=dict(
            title=dict(text=AXIS_LABELS.get(y_col, y_col), font=dict(size=17, color=COLOR_H3)),
            gridcolor=_GRID, zeroline=False, range=[-0.05, 1.15],
            tickfont=dict(size=17, color=COLOR_H3),
        ),
    )
    return fig


# ── heatmap ───────────────────────────────────────────────────────────────────

def make_heatmap(df) -> go.Figure:
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
        textfont=dict(size=11, family=FONT_BODY, color=COLOR_H2),
        hovertemplate="<b>%{y}</b><br>%{x}<br>Risk score: <b>%{z:+.3f}</b><extra></extra>",
        colorbar=dict(
            title=dict(text="Risk score", font=dict(size=10, color=COLOR_H3)),
            tickvals=[-1, -0.5, 0, 0.5, 1],
            tickfont=dict(size=9, color=COLOR_H3),
            len=0.8,
        ),
    ))

    fig.update_layout(
        **_base_layout(max(300, len(pivot) * 80 + 80)),
        margin=dict(l=0, r=20, t=16, b=16),
        xaxis=dict(
            side="top", tickangle=-30,
            tickfont=dict(size=10, color=COLOR_H3, family=FONT_UI),
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=10, color=COLOR_H3, family=FONT_UI),
        ),
    )
    return fig


# ── ranking (bar horizontal) ──────────────────────────────────────────────────

def make_bar(df) -> go.Figure:
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
        **_base_layout(max(260, len(agg) * 64 + 80)),
        margin=dict(l=0, r=80, t=16, b=16),
        xaxis=dict(
            title=dict(text="Risk score médio", font=dict(size=11, color=COLOR_H3)),
            gridcolor=_GRID, zeroline=False, range=[-1.2, 1.2],
            tickfont=dict(size=10, color=COLOR_H3),
        ),
        yaxis=dict(title="", tickfont=dict(size=11, color=COLOR_H2, family=FONT_UI)),
    )
    return fig


# ── radar ─────────────────────────────────────────────────────────────────────

def make_radar(df, event_letter: str) -> go.Figure | None:
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
        marker=dict(size=7, color=line_color),
        hovertemplate="<b>%{theta}</b><br>Risk score: <b>%{r:+.3f}</b><extra></extra>",
    ))

    fig.update_layout(
        height=400,
        margin=dict(l=60, r=60, t=40, b=40),
        paper_bgcolor=COLOR_BG_BODY,
        polar=dict(
            bgcolor=_BG_PLOT,
            radialaxis=dict(
                visible=True, range=[-1, 1],
                tickfont=dict(size=9, color=COLOR_H3),
                gridcolor=_GRID,
                tickvals=[-1, -0.5, 0, 0.5, 1],
            ),
            angularaxis=dict(
                tickfont=dict(size=10, color=COLOR_H2, family=FONT_UI),
                gridcolor=_GRID,
            ),
        ),
        font=dict(family=FONT_UI, size=11, color=COLOR_TEXT),
    )
    return fig

# ── exportação vertical (mobile/newsletter) ───────────────────────────────────

def _to_portrait_png(fig: go.Figure, width: int = 480, height: int = 720) -> bytes:
    """
    Gera PNG em proporção retrato via kaleido.
    Ajustes: margens generosas, fonte pequena, legenda abaixo do gráfico.
    """
    import plotly.io as pio
    portrait = go.Figure(fig)
    portrait.update_layout(
        width=width,
        height=height,
        # margens: topo para legenda, direita para labels que ultrapassam
        margin=dict(l=48, r=72, t=16, b=72),
        legend=dict(
            orientation="h",          # horizontal embaixo — não sobrepõe o gráfico
            yanchor="top", y=-0.08,
            xanchor="left", x=0,
            font=dict(size=9),
            itemsizing="constant",
            tracegroupgap=0,
        ),
        font=dict(size=9),
        xaxis=dict(
            tickfont=dict(size=9),
            title=dict(font=dict(size=10)),
            range=[-1.3, 1.5],        # range X mais largo → labels direita não cortam
        ),
        yaxis=dict(
            tickfont=dict(size=9),
            title=dict(font=dict(size=10)),
            range=[-0.05, 1.28],      # espaço extra no topo para labels
        ),
    )
    # reduzir fonte dos traces de texto
    for trace in portrait.data:
        if hasattr(trace, "textfont") and trace.textfont:
            trace.update(textfont=dict(size=9))
    # reduzir fonte das anotações de quadrante
    for ann in portrait.layout.annotations:
        ann.update(font=dict(size=7))
    return pio.to_image(portrait, format="png", scale=2)


def export_scatter_portrait(df, x_col: str, y_col: str,
                            size_col: str, color_by: str) -> bytes:
    fig = make_scatter(df, x_col, y_col, size_col, color_by)
    return _to_portrait_png(fig, width=420, height=700)

def export_heatmap_portrait(df) -> bytes:
    fig = make_heatmap(df)
    n   = len(df["SHORT_EVENT"].unique())
    return _to_portrait_png(fig, width=420, height=max(400, n * 90 + 120))

def export_bar_portrait(df) -> bytes:
    fig = make_bar(df)
    n   = df["EVENT_LETTER"].nunique()
    return _to_portrait_png(fig, width=420, height=max(320, n * 72 + 100))

def export_radar_portrait(df, event_letter: str) -> bytes | None:
    fig = make_radar(df, event_letter)
    if fig is None:
        return None
    return _to_portrait_png(fig, width=420, height=440)