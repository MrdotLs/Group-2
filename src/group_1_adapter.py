import pandas as pd

mj_per_kwh = 3.6

COL_ID = "Scenario ID"
COL_NAME = "Scenario"
COL_CH4_MJ = "Energy CH4 (MJ)"
COL_ELEC_MJ = "Electricity potential"
COL_YIELD = "Treated Yield (Nm3/d)"
COL_SPEC = "Specific Yield (L/kgVs)"
COL_Improvement = "Improvement (%)"

required_col = (COL_ID, COL_NAME, COL_CH4_MJ, COL_ELEC_MJ, COL_YIELD, COL_SPEC)

def load_scenarios(path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in required_col if c not in df.columns]
    if missing:
        raise ValueError(f"scenario file is missing columns: {missing}")
    if df[COL_ID].duplicated().any():
        raise ValueError("Scenario must be unique")
    return df


def get_scenario(df: pd.DataFrame, scenario_id:str) -> pd.Series:
    rows = df.loc[df[COL_ID]==scenario_id]
    if rows.empty:
        raise KeyError(f"unkown scenario {scenario_id!r}; available:{list(df[COL_ID])}")
    return rows.iloc[0]

def implied_feed_kgvs_per_day(rows: pd.Series) -> float:
    pass
