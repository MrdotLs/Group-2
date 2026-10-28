import pandas as pd
import re

mj_per_kwh = 3.6

COL_ID = "Scenario ID"
COL_NAME = "Scenario"
COL_CH4_MJ  = "Energy CH4 (MJ)"
COL_ELEC_MJ = "Electricity potential (MJ)"
COL_YIELD = "Treated Yield (Nm3/d)"
COL_SPEC = "Specific Yield (L/kgVS)"
COL_Improvement = "Improvement (%)"

COL_BATCH_CHANGE = "Adjusted batch yield change vs S3 (%)"
COL_STABILITY = "Stability Score"

COL_VS_FED = "VS fed (kg/d)"
COL_SPEC_REPORTED = "Specific Yield reported (L/kgVS)"

MAX_YIELD_L_PER_KGVS = 1014.0

YIELD_BASES = ("formula", "practical", "reported")

GROUP1_BASIS = {
    "yield_basis": "formula",
    "wet_kg_per_day": 10.0,
    "ts_fraction": 0.25,
    "vs_of_ts": 0.90,
    "reactor_m3": 1.0,
    "olr_overrides": {"S9":4.5},
}

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

def _id_number(scenario_id) -> int:
    m = re.search(r"(\d+)", str(scenario_id))
    return int(m.group(1)) if m else 10**9

def sort_ids(ids) -> list:
    return sorted(ids, key=lambda s:(_id_number(s), str(s)))

def missing_ids(df: pd.DataFrame) -> list:
    nums = {_id_number(s) for s in df[COL_ID]}
    return [f"s{n}" for n in range(1, max(nums) + 1) if n not in nums]

def select_ids(df: pd.DataFrame, spec) -> list:
    available = sort_ids(df[COL_ID])
    if spec is None or str(spec).strip().lower() == "all":
        return available
    items = spec if isinstance(spec, (list, tuple)) else str(spec).split(",")
    out = []
    for item in (str(i).strip() for i in items):
        if not item:
            continue
        if "-" in item:
            lo, hi = (_id_number(x) for x in item.split("-", 1))
            out += [s for s in available if lo <= _id_number(s) <= hi]
        else:
            get_scenario(df, item)
            out.append(item)
    return list(dict.fromkeys(out))

def implied_feed_kgvs_per_day(rows: pd.Series) -> float:
    if COL_VS_FED in rows.index and pd.notna(rows[COL_VS_FED]):
        return float(rows[COL_VS_FED])
    return float(rows[COL_YIELD] * 1000.0 / float(rows[COL_SPEC]))

def group1_basis(settings:dict | None = None) -> dict:
    b = {**GROUP1_BASIS, **(settings or {})}
    b["yield_basis"] = str(b["yield_basis"]).lower()
    if b["yield_basis"] not in YIELD_BASES:
        raise ValueError(f"group1_basis_yield_basis must be one of {list(YIELD_BASES)}")
    for k in ("wet_kg_per_day", "ts_fraction", "vs_of_ts", "reactor_m3"):
        b[k] = float(b[k])
        if b[k] <= 0:
            raise ValueError(f"group1_basis.{k} must be positive")
    if b["ts_fraction"] > 1 or b["vs_of_ts"] > 1:
        raise ValueError("group1_basis fraction must be at most 1")
    b["olr_overrides"] = dict(b.get("olr_overrides") or {})
    return b

def vs_fed_kg_per_day(df: pd.DataFrame, basis:dict) -> pd.Series:
    if COL_VS_FED in df.columns:
        return df[COL_VS_FED].astype(float)
    default = basis["wet_kg_per_day"] * basis["ts_fraction"] * basis["vs_of_ts"]
    over = basis["olr_overrides"]
    return pd.Series(
        [float(over[sid]) * basis["reactor_m3"] if sid in over else default for sid in df[COL_ID]],
        index = df.index,
    )

def align_to_group1(df: pd.DataFrame, setting: dict | None = None):
    b = group1_basis(setting)
    out = df.copy()
    out[COL_SPEC_REPORTED] = df[COL_SPEC]
    info = {"basis": b, "vs_fed": None, "reported_matches": None}

    if b["yield_basis"] == "reported":
        y = out[COL_SPEC].astype(float)
    else:
        vs = vs_fed_kg_per_day(out, b)
        y = out[COL_YIELD] * 1000.0 / vs
        if b["yield_basis"] == "practical":
            if COL_STABILITY not in out.columns:
                raise ValueError("yield_basis 'practical' needs group 1's  'stability score' column")
            y = y * out[COL_STABILITY]
        out[COL_VS_FED] = vs
        info["vs_fed"] = vs

        per_vs = out[COL_YIELD] * 1000.0 / vs
        info["reported_matches"] = bool(((out[COL_SPEC_REPORTED] / per_vs - 1).abs() < 0.01).all())

    too_high = y > MAX_YIELD_L_PER_KGVS
    if too_high.any():
        bad = ", ".join(f"{sid} ({v:,.0f})" for sid, v in zip(out.loc[too_high, COL_ID], y[too_high]))
        raise ValueError(
            f"Methane per kg VS is above the {MAX_YIELD_L_PER_KGVS:,.0f} L/kgVS maximum for {bad}."
            "The file is probably scaled up: set group1_basis.wet_kg_per_day to wet feed"
            "Group 1 used for it (e.g 400)."
        )
    out[COL_SPEC] = y
    return out, info


def scale_factor_for_feed(df: pd.DataFrame,  reference_id: str, farm_kgvs_per_day:float) -> float:
    if farm_kgvs_per_day <= 0:
        raise ValueError("farm_kgvs_per_day must be positive")
    return farm_kgvs_per_day / implied_feed_kgvs_per_day(get_scenario, reference_id)

def _to_kwh_per_year(mj_per_day: float, scale_factor: float, opreating_days: float) -> float:
    return mj_per_day / mj_per_kwh * opreating_days * scale_factor

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
        ("Plant own use (electricity)", "parasitic", gross * own_use_frac),
      
    ]
    return pd.DataFrame(rows, columns=["stream", "direction", "kwh_per_year"])

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
