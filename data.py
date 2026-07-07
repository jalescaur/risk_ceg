# data.py — parsing, pré-processamento e lógica de negócio

import re
import pandas as pd
from config import RISK_PALETTE, RISK_THRESHOLDS, RISK_DEFAULT_LABEL


REQUIRED_COLUMNS = [
    "ID_DIMENSION", "EVENT_KEYWORD", "DIMENSION_KEYWORD",
    "IMPACT", "PROB_VD_IV", "TRUSTABILITY",
]


def missing_columns(df: pd.DataFrame) -> list[str]:
    """Retorna as colunas obrigatórias ausentes no DataFrame."""
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]


# ── helpers de classificação ──────────────────────────────────────────────────

def risk_label(score: float) -> str:
    """Classifica um risk score em categoria textual."""
    for threshold, label in RISK_THRESHOLDS:
        if score <= threshold:
            return label
    return RISK_DEFAULT_LABEL


def risk_color(score: float) -> str:
    """Retorna a cor hex correspondente ao risk score."""
    return RISK_PALETTE[risk_label(score)]


# ── parsing de IDs ────────────────────────────────────────────────────────────

def parse_event_id(id_str: str) -> tuple[str, str, str]:
    """
    Extrai componentes do ID_DIMENSION.

    Aceita dois formatos:
      EVT_YYYY_M_D_LETRA_NUM  (6 partes, ex.: EVT_2026_6_16_A_1)
      EVT_YYYY_M_D_NUM        (5 partes, sem letra — ex.: EVT_2026_6_16_1)

    No formato sem letra, EVENT_LETTER é derivado da combinação YYYY_M_D
    (todas as dimensões com a mesma data caem no mesmo "evento"), e o NUM
    final é usado como dim_num.

    Retorna: (date_str, event_letter, dim_num)
    """
    parts = id_str.split("_")

    if len(parts) >= 6 and re.fullmatch(r"[A-Za-z]+", parts[4]):
        # formato completo: EVT_YYYY_M_D_LETRA_NUM
        date_str     = f"{parts[1]}-{parts[2].zfill(2)}-{parts[3].zfill(2)}"
        event_letter = parts[4]
        dim_num      = parts[5]
        return date_str, event_letter, dim_num

    if len(parts) == 5:
        # formato sem letra: EVT_YYYY_M_D_NUM
        date_str     = f"{parts[1]}-{parts[2].zfill(2)}-{parts[3].zfill(2)}"
        event_letter = f"{parts[1]}_{parts[2]}_{parts[3]}"  # agrupa por data
        dim_num      = parts[4]
        return date_str, event_letter, dim_num

    return "unknown", id_str, "1"


# ── pré-processamento principal ───────────────────────────────────────────────

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe o DataFrame bruto e devolve um enriquecido com colunas derivadas.

    Colunas adicionadas:
      DATE, EVENT_LETTER, DIM_NUM  — desmembradas de ID_DIMENSION
      RISK_SCORE                   — recalculado se necessário
      RISK_LABEL, RISK_COLOR       — classificação e cor
      DIM_LABEL                    — rótulo legível da dimensão
      SHORT_EVENT                  — versão truncada de EVENT_KEYWORD
      EVENT_AGG_SCORE              — média do risk score por evento
    """
    df = df.copy()

    # parse ID
    parsed = df["ID_DIMENSION"].apply(lambda x: pd.Series(parse_event_id(x),
                                      index=["DATE","EVENT_LETTER","DIM_NUM"]))
    df = pd.concat([df, parsed], axis=1)

    # tipos numéricos
    for col in ["RISK_SCORE","IMPACT","PROB_VD_IV","TRUSTABILITY","PROB_DV","PROB_VIT"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # recalcula RISK_SCORE se a coluna estiver toda nula ou ausente
    if "RISK_SCORE" not in df.columns or df["RISK_SCORE"].isna().all():
        df["RISK_SCORE"] = df["PROB_VD_IV"] * df["IMPACT"] * df["TRUSTABILITY"]

    # classificação
    df["RISK_LABEL"] = df["RISK_SCORE"].apply(risk_label)
    df["RISK_COLOR"] = df["RISK_SCORE"].apply(risk_color)

    # rótulo da dimensão: usa DIMENSION_KEYWORD se preenchido, senão "Dim N"
    df["DIM_LABEL"] = df.apply(
        lambda r: r["DIMENSION_KEYWORD"]
                  if pd.notna(r["DIMENSION_KEYWORD"]) and str(r["DIMENSION_KEYWORD"]).strip()
                  else f"Dim {r['DIM_NUM']}",
        axis=1,
    )

    # evento truncado para legenda
    df["SHORT_EVENT"] = df["EVENT_KEYWORD"].apply(
        lambda x: (str(x)[:40] + "…") if len(str(x)) > 40 else str(x)
    )

    # score agregado por evento (média)
    df["EVENT_AGG_SCORE"] = df.groupby("EVENT_LETTER")["RISK_SCORE"].transform("mean")

    return df


# ── loader de arquivo ─────────────────────────────────────────────────────────

def load_file(uploaded_file) -> pd.DataFrame:
    """Carrega CSV ou Excel a partir de um st.file_uploader object."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError(f"Formato não suportado: {name}")