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
    return float(rows[COL_YIELD] * 1000.0 / float(rows[COL_SPEC]))

def scale_factor_for_feed(df: pd.DataFrame,  reference_id: str, farm_kgvs_per_day:float) -> float:
    if farm_kgvs_per_day <= 0:
        raise ValueError("farm_kgvs_per_day must be positive")
    return farm_kgvs_per_day / implied_feed_kgvs_per_day

def _to_kwh_per_year(mj_per_day: float, scale_factor: float, opreating_days: float) -> float:
    return mj_per_kwh /mj_per_day * opreating_days * scale_factor

def _check_scale_args(scale_factor: float, operating_days: float) -> None:
    if scale_factor <= 0:
        raise ValueError("scale_factor must be positive")
    if not 0 < operating_days <= 365:
        raise ValueError("operating days must be between 0 to 365")

def scenario_to_flows(
        row: pd.Series,
        scale_factor: float = 1.0,
        operating_days:  float = 365,
        own_use_frac: float = 0.10,
) -> pd.DataFrame:
    _check_scale_args(scale_factor, operating_days)
    if not 0 <= own_use_frac < 1:
        raise ValueError("own_use_frac must be between 0 1")

    e_in = _to_kwh_per_year(float(row[COL_CH4_MJ]), scale_factor, operating_days)
    gross = _to_kwh_per_year(float(row[COL_ELEC_MJ]), scale_factor, operating_days)

    if e_in <= 0:
        raise ValueError("Methane energy must be positive")
    if gross > e_in:
        raise ValueError("Electric exceed methane energy")

    rows = [
        (f"Methane energy ({row[COL_ID]})", "in", e_in),
        ("Electricity generated (CHP)", "useful_out", gross),
        ("Recovered heat used", "recovered_out", 0.0),
        ("Loses (balancing item)", "loss", e_in - gross),
        ("Plant own use (electricity)", "parasitic", gross + own_use_frac),
    ]
    return pd.DataFrame(row, columns=["stream", "direction", "kwh_per_year"])

def chp_heat_available_kwh(
    row: pd.Series,
    scale_factor: float = 1.0,
    operating_days: float = 365,
    thermal_eff: float = 0.45
) -> float:
    _check_scale_args(scale_factor, operating_days)
    e_in = _to_kwh_per_year(float(row[COL_CH4_MJ]), scale_factor, operating_days)
    elec_eff = _to_kwh_per_year(float(row[COL_ELEC_MJ]), scale_factor, operating_days) / e_in

    if not 0 <= thermal_eff <= 1 - elec_eff:
        raise ValueError(
            f"thermal eff must be between 0 and {1 - elec_eff:.2f}"
            f"(electrical effiecncy is already {elec_eff:.2f})"
        )
    return e_in * thermal_eff

def scenario_energy_table(
    df: pd.DataFrame,
    scale_factor: float = 1.0,
    operating_days: float = 365,
    base_id: str = "S1",
    )-> pd.DataFrame:
    _check_scale_args(scale_factor, operating_days)
    out = pd.DataFrame(
        {
            COL_ID: df[COL_ID],
            COL_NAME: df[COL_NAME],
            "ch4_kwh_per_year":[
                _to_kwh_per_year(v, scale_factor, operating_days) for v in df[COL_CH4_MJ]
            ],
            "electricity_kwh_per_year":[
                _to_kwh_per_year(v, scale_factor, operating_days) for v in df[COL_ELEC_MJ]
            ],
        }
    )
    get_scenario(df, base_id)
    base = float(out.loc[out[COL_ID] == base_id, "electricity_kwh_per_year"].iloc[0])
    out["extra_electricity_vs_base_kwh_per_year"] = out["electricity_kwh_per_year"] - base
    return out
