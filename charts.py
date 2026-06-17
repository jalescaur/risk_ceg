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

def _apply_overlap_jitter(df, x_col: str, y_col: str) -> "pd.DataFrame":
    """
    Detecta pontos com X/Y muito próximos (mesmo cluster visual) e aplica
    um pequeno deslocamento circular para separá-los, sem alterar os
    valores reais usados no hover/eixos.

    Tolerância: 1.5% do range de cada eixo — pontos dentro dessa
    distância em AMBOS os eixos são considerados sobrepostos.

    Retorna o df com duas colunas extras:
      _X_PLOT, _Y_PLOT   — coordenadas com jitter aplicado (para plotagem)
      _CLUSTER_SIZE      — quantos pontos compartilham o mesmo cluster
    """
    import pandas as pd

    df = df.copy()
    df["_X_PLOT"] = df[x_col].astype(float)
    df["_Y_PLOT"] = df[y_col].astype(float)
    df["_CLUSTER_SIZE"] = 1

    x_range = df[x_col].max() - df[x_col].min() or 1.0
    y_range = df[y_col].max() - df[y_col].min() or 1.0
    tol_x = x_range * 0.015
    tol_y = y_range * 0.015

    # agrupa por proximidade usando arredondamento na tolerância
    # (clustering simples: quantiza coordenadas na grade de tolerância)
    keys = list(zip(
        (df[x_col] / tol_x).round() if tol_x > 0 else df[x_col] * 0,
        (df[y_col] / tol_y).round() if tol_y > 0 else df[y_col] * 0,
    ))
    df["_CLUSTER_KEY"] = keys

    jitter_radius_x = x_range * 0.025
    jitter_radius_y = y_range * 0.025

    for key, group in df.groupby("_CLUSTER_KEY"):
        n = len(group)
        if n <= 1:
            continue
        idxs = group.index.tolist()
        for j, idx in enumerate(idxs):
            angle = 2 * np.pi * j / n
            df.loc[idx, "_X_PLOT"] = df.loc[idx, x_col] + jitter_radius_x * np.cos(angle)
            df.loc[idx, "_Y_PLOT"] = df.loc[idx, y_col] + jitter_radius_y * np.sin(angle)
            df.loc[idx, "_CLUSTER_SIZE"] = n

    df = df.drop(columns=["_CLUSTER_KEY"])
    return df


def make_scatter(df, x_col: str, y_col: str, size_col: str, color_by: str,
                  font_size: int = 17, show_labels: bool = True,
                  position_mode: str = "rotate", fixed_position: str = "top center",
                  individual_positions: dict | None = None) -> go.Figure:
    """
    Tamanho da bola = |RISK_SCORE| (sizeref normalizado).
    Cor = RISK_COLOR (por risco) ou EVENT_PALETTE (por evento).
    Texto: label da dimensão com posição adaptativa por quadrante.

    font_size:            tamanho da fonte dos rótulos das bolhas (px).
    show_labels:           se False, oculta o texto fixo nas bolhas — mantém
                           apenas o hover.
    position_mode:         "rotate" alterna entre 6 posições por índice para
                           reduzir sobreposição entre rótulos vizinhos;
                           "fixed" usa a mesma posição (fixed_position) para
                           todos os rótulos; "individual" usa o dict
                           individual_positions para definir a posição de
                           cada bolha separadamente (chave: ID_DIMENSION).
    fixed_position:        uma das 9 posições do Plotly, usada apenas
                           quando position_mode="fixed".
    individual_positions:  dict {ID_DIMENSION: posição}, usado apenas
                           quando position_mode="individual". Dimensões
                           ausentes do dict caem em fixed_position.
    """
    fig = go.Figure()
    df = _apply_overlap_jitter(df, x_col, y_col)
    events = sorted(df["EVENT_LETTER"].unique())

    # sizeref: sizemode="area" — |score|=1.0 → ~55px diâmetro
    max_score = df["RISK_SCORE"].abs().max() or 1.0
    sizeref   = 2.0 * max_score / (55 ** 2)

    for i, evt in enumerate(events):
        sub = df[df["EVENT_LETTER"] == evt].copy().reset_index(drop=True)
        if sub.empty:
            continue
        # garante que as colunas de eixo existem no subset
        for _col in (x_col, y_col, size_col):
            if _col not in sub.columns:
                continue
        evt_name = sub["SHORT_EVENT"].iloc[0]

        marker_sizes  = sub["RISK_SCORE"].abs().tolist()

        if color_by == "risk":
            marker_colors = sub["RISK_COLOR"].tolist()
        else:
            marker_colors = [EVENT_PALETTE[i % len(EVENT_PALETTE)]] * len(sub)

        # posição do texto: rodízio, fixa, ou individual por bolha
        if position_mode == "individual":
            _ip = individual_positions or {}
            text_positions = [
                _ip.get(dim_id, fixed_position)
                for dim_id in sub["ID_DIMENSION"]
            ]
        elif position_mode == "fixed":
            text_positions = [fixed_position] * len(sub)
        else:
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
            f"{AXIS_LABELS.get(x_col, x_col)}: %{{customdata[5]:.2f}}<br>"
            f"{AXIS_LABELS.get(y_col, y_col)}: %{{customdata[6]:.2f}}<br>"
            "Confiabilidade: %{customdata[3]:.2f}"
            "%{customdata[7]}"
            "<extra></extra>"
        )

        # texto auxiliar de cluster, já formatado (evita template aninhado em customdata)
        cluster_suffix = [
            f"<br><i>📍 {n} bolhas sobrepostas aqui</i>" if n > 1 else ""
            for n in sub["_CLUSTER_SIZE"]
        ]

        custom = np.column_stack([
            sub["SHORT_EVENT"].values,
            sub["DIM_LABEL"].values,
            sub["RISK_SCORE"].values,
            sub["TRUSTABILITY"].values,
            sub["_CLUSTER_SIZE"].values,
            sub[x_col].values,
            sub[y_col].values,
            cluster_suffix,
        ])

        fig.add_trace(go.Scatter(
            x=sub["_X_PLOT"],
            y=sub["_Y_PLOT"],
            mode="markers+text" if show_labels else "markers",
            name=f"{evt} — {evt_name}",
            marker=dict(
                size=marker_sizes,
                sizemode="area",
                sizeref=sizeref,
                sizemin=17,
                color=marker_colors,
                opacity=0.85,
                line=dict(
                    width=[2.5 if n > 1 else 1.5 for n in sub["_CLUSTER_SIZE"]],
                    color=["#c0392b" if n > 1 else "white" for n in sub["_CLUSTER_SIZE"]],
                ),
            ),
            text=sub["DIM_LABEL"] if show_labels else None,
            textposition=text_positions if show_labels else None,
            textfont=dict(size=font_size, color=COLOR_H2, family=FONT_UI),
            customdata=custom,
            hovertemplate=hover,
        ))

        # badge "+N" para clusters com sobreposição (1 por cluster, não por ponto)
        seen_clusters = set()
        for _, row in sub.iterrows():
            n = row["_CLUSTER_SIZE"]
            if n <= 1:
                continue
            cluster_key = (round(row["_X_PLOT"], 6), round(row["_Y_PLOT"], 6), n)
            # usa o centro real (não-jittered) do cluster como referência
            center_key = (row[x_col], row[y_col])
            if center_key in seen_clusters:
                continue
            seen_clusters.add(center_key)
            fig.add_annotation(
                x=row[x_col], y=row[y_col],
                text=f"+{n}",
                showarrow=False,
                font=dict(size=11, color="white", family=FONT_UI),
                bgcolor="#c0392b",
                borderpad=3,
                xanchor="center", yanchor="middle",
                xshift=14, yshift=14,
            )

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

def _to_portrait_png(fig: go.Figure, width: int = 480, height: int = 720,
                     df=None) -> bytes:
    """
    Gera PNG em proporção retrato via kaleido.
    Range Y ajustado aos dados reais (+padding), margem direita generosa
    para labels não cortarem, legenda abaixo.
    """
    import plotly.io as pio
    import numpy as np

    portrait = go.Figure(fig)

    # ── range Y adaptado aos dados reais ──────────────────────────────────────
    # Coleta todos os valores Y de todos os traces
    all_y = []
    for trace in portrait.data:
        if hasattr(trace, "y") and trace.y is not None:
            all_y.extend([v for v in trace.y if v is not None])
    if all_y:
        y_min = max(0.0, min(all_y) - 0.12)
        y_max = min(1.0, max(all_y)) + 0.18   # padding topo para labels
    else:
        y_min, y_max = -0.05, 1.25

    portrait.update_layout(
        width=width,
        height=height,
        margin=dict(l=52, r=100, t=20, b=100),  # r=100 labels direita, b=100 legenda
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.10,
            xanchor="left", x=0,
            font=dict(size=9),
            itemsizing="constant",
            tracegroupgap=0,
        ),
        font=dict(size=9),
        xaxis=dict(
            tickfont=dict(size=9),
            title=dict(font=dict(size=10)),
            range=[-1.70, 1.70],    # margem generosa para labels
        ),
        yaxis=dict(
            tickfont=dict(size=9),
            title=dict(font=dict(size=10)),
            range=[y_min, y_max],   # comprime ao range real dos dados
        ),
    )

    # ── substituir text dos traces por annotations com repulsão ─────────────
    import math

    # 1. Coleta todos os pontos (x, y, label) de todos os traces
    points = []  # (x, y, label, trace_idx, point_idx)
    for ti, trace in enumerate(portrait.data):
        if not (hasattr(trace, "x") and trace.x is not None and len(trace.x)):
            continue
        labels = list(trace.text) if trace.text is not None else []
        for pi, (xi, yi) in enumerate(zip(trace.x, trace.y)):
            label = labels[pi] if pi < len(labels) else ""
            points.append({"x": xi, "y": yi, "label": label, "ti": ti, "pi": pi})

    # 2. Para cada ponto, calcula offset do label com repulsão simples
    # Offset inicial: acima do ponto
    # ── Passo 1: offset inicial — todos os labels acima do ponto ────────────
    offsets = [[0.0, 0.10] for _ in points]

    # ── Passo 2: decolisão global — empurra labels que se sobrepõem ──────────
    # Estima largura de cada label em unidades de dados (aprox. 0.10 por char)
    CHAR_W = 0.055
    LBL_H  = 0.06

    def lbl_w(label): return max(0.12, len(label) * CHAR_W)

    for _iter in range(80):
        for i in range(len(points)):
            if not points[i]["label"]: continue
            lx_i = points[i]["x"] + offsets[i][0]
            ly_i = points[i]["y"] + offsets[i][1]
            w_i  = lbl_w(points[i]["label"])
            fx, fy = 0.0, 0.0
            for j in range(len(points)):
                if i == j or not points[j]["label"]: continue
                lx_j = points[j]["x"] + offsets[j][0]
                ly_j = points[j]["y"] + offsets[j][1]
                w_j  = lbl_w(points[j]["label"])
                dx = lx_i - lx_j
                dy = ly_i - ly_j
                gap_x = (w_i + w_j) / 2 + 0.04
                gap_y = LBL_H + 0.03
                ox = max(0, gap_x - abs(dx))
                oy = max(0, gap_y - abs(dy))
                if ox > 0 and oy > 0:
                    push_x = ox * 0.4 * (1 if dx >= 0 else -1)
                    push_y = oy * 0.5 * (1 if dy >= 0 else -1)
                    fx += push_x
                    fy += push_y
            offsets[i][0] += fx * 0.5
            offsets[i][1] += fy * 0.5

    # ── Passo 3: clamp — mantém labels dentro do range visível ───────────────
    X_MIN, X_MAX = -1.55, 1.55
    Y_MIN_LBL = y_min + 0.02
    Y_MAX_LBL = y_max - 0.02
    for i in range(len(points)):
        lx = points[i]["x"] + offsets[i][0]
        ly = points[i]["y"] + offsets[i][1]
        w  = lbl_w(points[i]["label"])
        # clamp X considerando âncora
        if lx - w/2 < X_MIN:
            offsets[i][0] += (X_MIN - (lx - w/2))
        if lx + w/2 > X_MAX:
            offsets[i][0] -= ((lx + w/2) - X_MAX)
        # clamp Y
        if ly < Y_MIN_LBL:
            offsets[i][1] += Y_MIN_LBL - ly
        if ly > Y_MAX_LBL:
            offsets[i][1] -= ly - Y_MAX_LBL

    # 3. Remove text dos traces e desliga mode text
    for trace in portrait.data:
        if hasattr(trace, "mode") and trace.mode and "text" in trace.mode:
            trace.update(mode="markers", text=None)
        trace.update(cliponaxis=False)

    # 4. Adiciona annotations posicionadas com offset calculado
    existing_anns = list(portrait.layout.annotations or [])
    # remove anotações de quadrante no portrait (poluem em tela pequena)
    new_anns = []

    for i, pt in enumerate(points):
        if not pt["label"]:
            continue
        lx = pt["x"] + offsets[i][0]
        ly = pt["y"] + offsets[i][1]
        # linha conectora da annotation ao ponto real
        # xanchor dinâmico: ponto à esquerda → ancor à esquerda do label
        x_range_left  = -1.70
        x_range_right =  1.70
        x_rel = (lx - x_range_left) / (x_range_right - x_range_left)
        # xanchor controla de onde o texto cresce:
        # ponto à esquerda do range → texto cresce para direita ("left")
        # ponto à direita do range  → texto cresce para esquerda ("right")
        # centro → centrado
        if x_rel < 0.30:
            xanchor = "left"    # texto à esquerda: cresce para direita
        elif x_rel > 0.70:
            xanchor = "right"   # texto à direita: cresce para esquerda
        else:
            xanchor = "center"

        yanchor = "bottom" if offsets[i][1] >= 0 else "top"

        # ax/ay em pixels relativos ao ponto (mais confiável que axref="x")
        # Converte offset de dados para pixels aproximados
        # Plot area: ~380px wide para range 3.4 units → ~112px/unit
        # Plot area: ~600px tall para range ~0.8 units → ~750px/unit
        DATA_TO_PX_X = 380 / 3.4
        DATA_TO_PX_Y = 560 / (y_max - y_min)
        ax_px = offsets[i][0] * DATA_TO_PX_X
        ay_px = -offsets[i][1] * DATA_TO_PX_Y  # Y invertido em pixels

        new_anns.append(dict(
            x=pt["x"], y=pt["y"],
            ax=ax_px, ay=ay_px,
            axref="pixel", ayref="pixel",
            xref="x", yref="y",
            text=f"<b>{pt['label']}</b>",
            showarrow=True,
            arrowhead=0,
            arrowwidth=0.8,
            arrowcolor="#cccccc",
            font=dict(size=9, color=COLOR_H2, family=FONT_UI),
            bgcolor="rgba(255,255,255,0.75)",
            borderpad=2,
            xanchor=xanchor,
            yanchor=yanchor,
        ))

    portrait.update_layout(annotations=new_anns)

    return pio.to_image(portrait, format="png", scale=2)


def export_scatter_portrait(df, x_col: str, y_col: str,
                            size_col: str, color_by: str,
                            swap_axes: bool = False) -> bytes:
    """
    swap_axes=True: inverte X↔Y — útil quando os dados estão concentrados
    numa faixa vertical e o celular precisa de orientação diferente.
    """
    _x = y_col if swap_axes else x_col
    _y = x_col if swap_axes else y_col
    fig = make_scatter(df, _x, _y, size_col, color_by)
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


# ── exportação portrait via matplotlib (controle total de labels) ─────────────

def export_scatter_portrait_mpl(df, x_col: str, y_col: str,
                                size_col: str, color_by: str,
                                font_size: int = 8, show_labels: bool = True,
                                position_mode: str = "rotate") -> bytes:
    """
    Versão matplotlib do scatter portrait.
    Usa adjustText para posicionar labels sem sobreposição.

    font_size:     tamanho da fonte dos rótulos (pt). Equivalente ao slider
                   do scatter interativo, mas em escala matplotlib (pt vs px).
    show_labels:   se False, omite os rótulos e a chamada ao adjustText —
                   útil para exportar uma versão limpa e anotar manualmente
                   depois (PowerPoint, Canva etc.).
    position_mode: "rotate" deixa o adjustText mover os labels livremente
                   para evitar colisão (pode afastar mais da bolha em
                   zonas densas); "fixed" reduz a força de repulsão para
                   manter os labels o mais rente possível à bolha,
                   aceitando alguma sobreposição residual em troca de
                   proximidade.
    Retorna PNG bytes.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from adjustText import adjust_text
    import io as _io

    # Paletas
    RISK_COLORS_MPL = {
        "critical": "#c0392b",
        "high":     "#e67e22",
        "moderate": "#acac95",
        "low":      "#5dade2",
        "positive": "#26619C",
    }
    EVENT_COLORS_MPL = ["#26619C", "#acac95", "#5dade2", "#1a5276", "#7f8c8d", "#2e86c1"]
    BG_PLOT  = "#fafaf8"
    GRID_CLR = "#e8e3dc"
    TEXT_CLR = "#1a1a1a"
    FONT_FAM = "DejaVu Sans"

    fig, ax = plt.subplots(figsize=(4.2, 7.0), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(BG_PLOT)

    # Grid
    ax.grid(True, color=GRID_CLR, linewidth=0.5, zorder=0)
    ax.spines[["top","right","left","bottom"]].set_visible(False)
    ax.tick_params(colors="#888", labelsize=8)

    # Linhas de quadrante
    ax.axhline(0.5, color=GRID_CLR, lw=1, ls="--", zorder=1)
    ax.axvline(0.0, color="#999",   lw=0.8, ls="--", zorder=1)

    events = sorted(df["EVENT_LETTER"].unique())
    texts  = []
    legend_handles = []
    seen_clusters_mpl = set()
    df = _apply_overlap_jitter(df, x_col, y_col)

    # Escala de tamanho: |RISK_SCORE| → área do marcador
    max_score = df["RISK_SCORE"].abs().max() or 1.0

    for i, evt in enumerate(events):
        sub = df[df["EVENT_LETTER"] == evt].copy()
        evt_name = sub["SHORT_EVENT"].iloc[0]

        if color_by == "risk":
            colors = [RISK_COLORS_MPL[sub["RISK_LABEL"].iloc[j]]
                      for j in range(len(sub))]
        else:
            colors = [EVENT_COLORS_MPL[i % len(EVENT_COLORS_MPL)]] * len(sub)

        sizes = ((sub["RISK_SCORE"].abs() / max_score) * 1200 + 60).tolist()
        edge_colors = ["#c0392b" if n > 1 else "white" for n in sub["_CLUSTER_SIZE"]]
        edge_widths = [2.2 if n > 1 else 1.2 for n in sub["_CLUSTER_SIZE"]]

        sc = ax.scatter(
            sub["_X_PLOT"], sub["_Y_PLOT"],
            s=sizes, c=colors, alpha=0.88,
            edgecolors=edge_colors, linewidths=edge_widths, zorder=3,
        )

        # Labels
        if show_labels:
            for _, row in sub.iterrows():
                t = ax.text(
                    row["_X_PLOT"], row["_Y_PLOT"], row["DIM_LABEL"],
                    fontsize=font_size, color=TEXT_CLR, fontfamily=FONT_FAM,
                    fontweight="bold", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7, lw=0),
                )
                texts.append(t)

        # Badge "+N" para clusters sobrepostos (1 por cluster)
        for _, row in sub.iterrows():
            n = row["_CLUSTER_SIZE"]
            if n <= 1:
                continue
            center_key = (row[x_col], row[y_col])
            if center_key in seen_clusters_mpl:
                continue
            seen_clusters_mpl.add(center_key)
            ax.annotate(
                f"+{n}",
                xy=(row[x_col], row[y_col]),
                xytext=(8, 8), textcoords="offset points",
                fontsize=7, color="white", fontweight="bold",
                ha="center", va="center", zorder=6,
                bbox=dict(boxstyle="circle,pad=0.25", fc="#c0392b", ec="none"),
            )

        # Legenda
        legend_handles.append(
            mpatches.Patch(color=EVENT_COLORS_MPL[i % len(EVENT_COLORS_MPL)],
                           label=f"{evt} — {evt_name}")
        )

    # adjustText: repele automaticamente; força menor em modo "fixed"/
    # "individual" para manter os labels o mais rente possível à bolha.
    # Nota: "individual" (posição por bolha) só existe no scatter
    # interativo — o adjustText não aceita posição fixa por ponto, então
    # aqui ele cai no mesmo comportamento de "fixed" (força reduzida).
    if texts:
        if position_mode in ("fixed", "individual"):
            adjust_text(
                texts, ax=ax,
                arrowprops=dict(arrowstyle="-", color="#bbb", lw=0.7, shrinkA=4),
                expand_points=(1.1, 1.15),
                expand_text=(1.05, 1.1),
                force_points=(0.2, 0.3),
                force_text=(0.2, 0.3),
                lim=300,
            )
        else:
            adjust_text(
                texts, ax=ax,
                arrowprops=dict(arrowstyle="-", color="#bbb", lw=0.7, shrinkA=4),
                expand_points=(2.0, 2.5),
                expand_text=(1.6, 1.8),
                force_points=(1.0, 1.5),
                force_text=(1.2, 1.5),
                lim=500,
            )

    # Eixos
    ax.set_xlabel(AXIS_LABELS.get(x_col, x_col), fontsize=9, color="#555")
    ax.set_ylabel(AXIS_LABELS.get(y_col, y_col), fontsize=9, color="#555")
    ax.set_xlim(-1.4, 1.4)

    all_y = df[y_col].values
    y_pad = (all_y.max() - all_y.min()) * 0.35 + 0.12
    ax.set_ylim(max(0, all_y.min() - y_pad), min(1.05, all_y.max()) + y_pad)

    # Legenda abaixo
    ax.legend(
        handles=legend_handles,
        loc="upper center", bbox_to_anchor=(0.5, -0.08),
        fontsize=7.5, framealpha=0.9, ncol=1,
        handlelength=1.2, handleheight=1.0,
    )

    plt.tight_layout(rect=[0, 0.10, 1, 1])

    buf = _io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()