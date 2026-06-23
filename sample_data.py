# sample_data.py — dados de exemplo para desenvolvimento e testes

import pandas as pd

COLUMNS = [
    "ID_DIMENSION", "EVENT_KEYWORD", "DIMENSION_KEYWORD",
    "PROB_DV", "IV_USED", "PROB_VIT", "PROB_DV_IV",
    "IMPACT", "TRUSTABILITY", "RISK_SCORE",
]

ROWS = [
    ["EVT_2026_6_11_A_1","USTR Section 301 / 25% tariff on Brazil","Trade policy",   0.7,"IV_1,IV_2",1,  0.7, -0.65,0.9,-0.41],
    ["EVT_2026_6_11_A_2","USTR Section 301 / 25% tariff on Brazil","Market access",  0.5,"IV_3",     0.5,0.5, -0.85,0.8,-0.34],
    ["EVT_2026_6_11_A_3","USTR Section 301 / 25% tariff on Brazil","Retaliation risk",0.7,"IV_4",    0.7,0.7,  0.65,0.9, 0.41],
    ["EVT_2026_6_11_B_1","OPEC+ June-7 hike under Hormuz closure", "Energy prices",  0.5,"IV_1,IV_2",0.6,0.5, -0.75,0.7,-0.26],
    ["EVT_2026_6_11_B_2","OPEC+ June-7 hike under Hormuz closure", "Supply chain",   0.5,"IV_1,IV_3",0.5,0.5, -1.0, 0.8,-0.40],
    ["EVT_2026_6_11_B_3","OPEC+ June-7 hike under Hormuz closure", "Geopolitical",   1.0,"IV_1",     1,  1,    0.85,0.8, 0.68],
    ["EVT_2026_6_11_C_1","EU Official-Journal Brazilian meat ban",  "Export loss",    0.7,"IV_1,IV_2",1,  0.7, -0.3, 0.7,-0.15],
    ["EVT_2026_6_11_C_2","EU Official-Journal Brazilian meat ban",  "Regulatory",     1.0,"IV_3",     1,  1,   -0.55,0.9,-0.50],
    ["EVT_2026_6_11_C_3","EU Official-Journal Brazilian meat ban",  "Compliance",     0.7,"IV_4",     1,  0.7, -0.15,0.8,-0.08],
]


def load_sample() -> pd.DataFrame:
    return pd.DataFrame(ROWS, columns=COLUMNS)
