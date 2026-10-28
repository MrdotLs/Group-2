
import re

import numpy as np
import pandas as pd

from src.group_1_adapter import(
    COL_CH4_MJ,
    COL_ELEC_MJ,
    COL_ID,
    COL_NAME,
    COL_SPEC,
    COL_YIELD,
    mj_per_kwh,
    get_scenario,
    sort_ids,
)

COL_MIX = "Feedstock Mixture"
COL_FPSI = "FPSI"

FEEDSTOCK = ("food_waste", "scg", "rice", "meat", "oil", "peel")
_ALIASES = {"fw": "food_waste", "scg":"scg", "rice":"rice", "meat":"meat", "oil":"oil", "peel":"peel"}

def parse_mixture(text:str) -> dict:
    parts = re.findall(r"([A-Za-z]+)\s*:\s*([0-9.]+)\s*%", str(text))
    if not parts:
        raise ValueError(f"Cannot read a feedstock mixture from {text!r}")
    out: dict = {}
    for name, pct in parts:
        keys = _ALIASES.get(name.lower())
        if keys is None:
            raise ValueError(f"Unknown feedstock {name!r} in {text!r}")
        out[keys] = out.get(keys, 0.0) + float(pct) / 100.0
    if abs(sum(out.values()) - 1.0) > 0.01:
        raise ValueError(f"Mixure {text!r} does not add up to 100%")
    return out

def same_mixture(a:dict, b:dict, tol:float = 1e-6) -> bool:
    keys = set(a) | set(b)
    return all(abs(a.get(k, 0.0) - b.get(k, 0.0)) <= tol for k in keys)


def _need_columns(df: pd.DataFrame, cols) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Scenario file is missing columns: {missing}")

def fit_rows(df: pd.DataFrame, reference_id: str = "s3", exclude_id=("S9",), fit_ids=None) -> pd.DataFrame:
    _need_columns(df, (COL_MIX, COL_FPSI, COL_SPEC,COL_ID))
    if fit_ids is not None:
        for sid in fit_ids:
            get_scenario(df, sid)
        return df[[COL_ID].isin(fit_ids)]
    ref = get_scenario(df, reference_id)
    ref_mix = parse_mixture(ref[COL_MIX])
    same_pretreatment = (df[COL_FPSI] - ref[COL_FPSI]).abs() < 1e-6
    is_ref = df[COL_ID] == reference_id
    other_mix = df[COL_MIX].map(lambda m : not same_mixture(parse_mixture(m), ref_mix))
    return df[same_pretreatment & ~df[COL_ID].isin(exclude_id) & (is_ref | other_mix)]

def fit_feedstock_yield(df: pd.DataFrame, reference_id: str = "S3", exclude_id=("S9",)):
    _need_columns(df, (COL_MIX, COL_FPSI, COL_SPEC, COL_ID))
    ref = get_scenario(df, reference_id)
    same_pretreatment = (df[COL_FPSI] - ref[COL_FPSI]).abs() < 1e-6
    rows = df[same_pretreatment  & ~df[COL_ID].isin(exclude_id)]

    fracs = [parse_mixture(m) for m in rows[COL_MIX]]
    names = [f for f in FEEDSTOCK if any(f in fr for fr in fracs)]
    a = np.array([[fr.get(n,0.0) for n in names] for fr in fracs])
    b = rows[COL_SPEC].to_numpy(dtype=float)

    sol, _, rank, _ = np.linalg.lstsq(a,b, rcond=None)
    if rank < len(names):
        raise ValueError("The scenarios do not pin down the yield of every feedstock")
    worst = float(np.abs(a @ sol - b).max())
    return dict(zip(names, (float(x) for x in sol))), worst


def Scenario_data_issue(df:pd.DataFrame, tol:float = 0.01) -> pd.DataFrame:
    _need_columns(df, COL_CH4_MJ, COL_ELEC_MJ, COL_YIELD)
    checks = {
        "Methane energy content (MJ/Nm3)": df[COL_CH4_MJ] / df[COL_YIELD],
        "Electrical efficiency": df[COL_ELEC_MJ] / df[COL_CH4_MJ],
    }
    rows = []
    for name, s in checks.items():
        expected = float(s.median())
        bad = (s / expected - 1).abs() > tol
        for sid, value in zip(df.loc[bad, COL_ID], s[bad]):
            rows.append({COL_ID: sid,"check": name, "value":float(value), "expected": expected})
    return pd.DataFrame(rows, columns=[COL_ID, "check", "value", "expected"])

def energy_constants(df: pd.DataFrame):
    _need_columns(df,(COL_CH4_MJ, COL_ELEC_MJ, COL_YIELD))
    series = {
        "Methane energy content": df[COL_CH4_MJ] / df[COL_YIELD],
        "Electrical efficiency": df[COL_ELEC_MJ] / df[COL_CH4_MJ],
    }
    for name, s in series.items():
        if s.max() / s.min() - 1 > 0.01:
            raise ValueError(
                f"{name} differs by more then 1% between scenerio"
                "Group 1's model has changed, check before scaling up"
            )
    return float(series["methane energy content"].median()), float(series["electrical efficiency"].median())

def pretreatment_multiplier(df: pd.DataFrame, scenario_id:str, reference_id: str = "S3"):

    _need_columns(df, (COL_MIX, COL_SPEC))
    for sid in (scenario_id, reference_id):
        if parse_mixture(get_scenario(df, sid)[COL_MIX]) != {"food_waste": 1.0}:
            raise ValueError(f"{sid} is not a 100% food-waste scenario")
    return float(get_scenario(df, scenario_id)[COL_SPEC] / get_scenario(df, reference_id)[COL_SPEC])

def load_properties(path) -> dict:
    props = pd.read_csv(path)
    _need_columns(props, ("feedstock", "vs_fraction_of_wet"))
    out = {}
    for name, frac in zip(props["feedstock"], props["vs_fraction_of_wet"]):
        if name not in FEEDSTOCK:
            raise ValueError(f"Unknown feedstock {name!r}; use one of {list(FEEDSTOCK)}")
        if not 0 < frac <= 1:
            raise ValueError(f"vs_fraction_of_wet for {name} must be in (0,1]")
        out[name] = float(frac)
    return out

def _check_supported(composition: dict, supported) -> None:
    Unknown = [k for k in composition if k not in supported]
    if Unknown:
        raise KeyError(
            f"no group1 yield for {Unknown}. supported: {list(supported)}"
            "Map the waste to the closest support type, or ask group 1 to run (simulation building team)"
        )
    if any(v < 0 for v in composition.values()):
        raise ValueError("Masses must not be negative")

def vs_from_wet(wet_kg: dict, vs_fraction_of_wet: dict) -> dict:
    _check_supported(wet_kg, vs_fraction_of_wet)
    return {k: v * vs_fraction_of_wet[k] for k, v in wet_kg.items()}

def methane_nm3(vs_kg:dict, yields:dict) -> float:
    _check_supported(vs_kg, yields)     
    return sum(vs_kg[k] * yields[k] for k in vs_kg) / 1000.0


def mix_row(vs_kg:dict, yields:dict, mj_per_nm3: float, elec_eff:float, multiplier:float = 1.0, label: str = "Farm mix") -> pd.Series:
    total_vs = sum(vs_kg.values())
    if total_vs <= 0:
        raise ValueError("The mix contain no volitile solids")
    ch4 = methane_nm3(vs_kg, yields) * multiplier
    mj = ch4 * mj_per_nm3
    return pd.Series (
        {
            COL_ID: "MIX",
            COL_NAME: label,
            COL_YIELD: ch4,
            COL_CH4_MJ: mj,
            COL_ELEC_MJ: mj * elec_eff,
            COL_SPEC: ch4 * 1000.0/ total_vs,
        }
    )

def farm_mix_row(df: pd.DataFrame, wet_kg_per_day:dict, vs_fraction_of_wet:dict, pretreatment_id: str = "S3", label:str = "Farm mix") -> pd.Series:
    yields, _ = fit_feedstock_yield(df)
    mj_per_nm3, elec_eff = energy_constants(df) 
    vs = vs_from_wet(wet_kg_per_day, vs_fraction_of_wet)
    mult = pretreatment_multiplier(df, pretreatment_id)
    return mix_row(vs, yields, mj_per_nm3, elec_eff, mult, label)

def composition_table(df:pd.DataFrame, compositions: dict, vs_fraction_of_wet:dict, pretreatment_id:str = "S3", operating_days:float = 365) -> pd.DataFrame:
    rows = []
    for name, wet in compositions.items():
        row = farm_mix_row(df, wet, vs_fraction_of_wet, pretreatment_id, label=name)
        rows.append(
            {
                "composition":name,
                
                "wet_kg_per_day":sum(wet.values()),
                "vs_kg_per_day":sum(vs_from_wet(wet, vs_fraction_of_wet).values()),
                "ch4_nm3_per_day":row[COL_YIELD],
                "electricity_kwh_per_year": row[COL_ELEC_MJ] / mj_per_kwh * operating_days,
            }
        )
    out = pd.DataFrame(rows)
    base = out["electricity_kwh_per_year"].iloc[0]
    out["vs_first"] = out["electricity_kwh_per_year"] / base - 1
    return out
