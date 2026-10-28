
import re
import warnings

import numpy as np
import pandas as pd

from src.group_1_adapter import(
    COL_BATCH_CHANGE,
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
        raise ValueError(f"cannot read a feedstock mixture from {text!r}")
    out: dict = {}
    for name, pct in parts:
        keys = _ALIASES.get(name.lower())
        if keys is None:
            raise ValueError(f"Unkown feedstock {name!r} in {text!r}")
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
        raise ValueError(f"scenario file is missing colomns: {missing}")

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

def fit_feedstock_yield(df: pd.DataFrame, reference_id: str = "S3", exclude_id=("S9",), fit_ids=None):

    rows = fit_rows(df, reference_id, exclude_id, fit_ids)

    fracs = [parse_mixture(m) for m in rows[COL_MIX]]
    names = [f for f in FEEDSTOCK if any(f in fr for fr in fracs)]
    a = np.array([[fr.get(n,0.0) for n in names] for fr in fracs])
    b = rows[COL_SPEC].to_numpy(dtype=float)

    sol, _, rank, _ = np.linalg.lstsq(a,b, rcond=None)
    if rank < len(names):
        raise ValueError("The scenarios do not pin down the yeild of every feedstock")
    worst = float(np.abs(a @ sol - b).max())
    return dict(zip(names, (float(x) for x in sol))), worst


def Scenario_data_issue(df:pd.DataFrame, tol:float = 0.01) -> pd.DataFrame:
    _need_columns(df, (COL_CH4_MJ, COL_ELEC_MJ, COL_YIELD))
    checks = {
        "methane energy content (MJ/Nm3)": df[COL_CH4_MJ] / df[COL_YIELD],
        "electrical efficiency": df[COL_ELEC_MJ] / df[COL_CH4_MJ],
    }
    rows = []
    for name, s in checks.items():
        expected = float(s.median())
        bad = (s / expected - 1).abs() > tol
        for sid, value in zip(df.loc[bad, COL_ID], s[bad]):
            rows.append({COL_ID: sid,"check": name, "value":float(value), "expected": expected})
    return pd.DataFrame(rows, columns=[COL_ID, "check", "value", "expected"])

def energy_constants(df: pd.DataFrame, tol:float = 0.01, warn:bool = True):
    issues =Scenario_data_issue(df, tol)
    bad_ids = sort_ids(set(issues[COL_ID]))
    if len(bad_ids) > len(df) / 2:
        raise ValueError(
            f"Energy columns disagree for {len(bad_ids)} of {len(df)} scenarios."
            "Group 1's model has changed, check before scaling up"
        )
    if bad_ids and warn:
        warnings.warn(
            f"Energy columns for {', '.join(bad_ids)} do not match their methane yield."
            "They are left out of the energy constants and their energy is worked out "
            "from the yield instead. Needs to be re-ran.",
            UserWarning, stacklevel=2,
        )
        good = df [~df[COL_ID].isin(bad_ids)]
    return(
        float((good[COL_CH4_MJ] / good[COL_YIELD]).median()),
        float((good[COL_ELEC_MJ] / good[COL_CH4_MJ]).median()),
    )
def pretreatment_multiplier(df: pd.DataFrame, scenario_id:str, reference_id: str = "S3"):

    _need_columns(df, (COL_MIX, COL_SPEC))
    for sid in (scenario_id, reference_id):
        if parse_mixture(get_scenario(df, sid)[COL_MIX]) != {"food_waste": 1.0}:
            raise ValueError(f"{sid} is not a 100% food-waste scenario")
    return float(get_scenario(df, scenario_id)[COL_SPEC] / get_scenario(df, reference_id)[COL_SPEC])

def scenario_multiplier(df: pd.DataFrame, scenario_id: str, yields:dict | None = None, reference_id:str = "S3", use_batch:bool = True):
    _need_columns(df,(COL_MIX, COL_SPEC))
    row = get_scenario(df, scenario_id)
    ref = get_scenario(df, reference_id)
    if scenario_id == reference_id:
        return 1.0, "reference"

    if(use_batch and COL_BATCH_CHANGE in df.columns
       and pd.notna(row[COL_BATCH_CHANGE]) and pd.notna(ref[COL_BATCH_CHANGE])):
        factor = (1 + float(row[COL_BATCH_CHANGE]) / 100) / (1 + float(ref[COL_BATCH_CHANGE]) / 100)
        return factor, "batch test (uncalibrated)"

    mix = parse_mixture(row[COL_MIX])
    if same_mixture(mix, parse_mixture(ref[COL_MIX])):
        return float(row[COL_SPEC]) / float(ref[COL_SPEC]), "specific yield vs reference"

    if yields is None:
        yields, _ = fit_feedstock_yield(df, reference_id)
    _check_supported(mix, yields)
    expected = sum(frac * yields[k] for k, frac in mix.items())
    return float(row[COL_SPEC]) / expected, "specific yields vs fitted mix" 
    

def load_properties(path) -> dict:
    props = pd.read_csv(path)
    has_split = {"ts_fraction", "vs_of_ts"} <= set(props.columns)
    if not has_split:
        _need_columns(props,("feedstock", "vs_fraction_of_wet"))
    out = {}
    for _, r in props.iterrows():
        name = str(r["feedstock"]).strip()
        if name not in FEEDSTOCK:
            raise ValueError(f"Unkown feedstock {name!r}; use one of {list(FEEDSTOCK)}")
        if has_split and pd.notna(r["ts_fraction"]) and pd.notna(r["vs_of_ts"]):
            frac = float(r["ts_fraction"]) * float(r["vs_of_ts"])
        else:
            frac = float(r["vs_fraction_of_wet"])
        if not 0 < frac <= 1:
            raise ValueError(f"vs_fraction_of_wet for {name} must be in (0,1]")
        out[name] = frac
    return out


def _check_supported(composition: dict, supported) -> None:
    unkown = [k for k in composition if k not in supported]
    if unkown:
        raise KeyError(
            f"no group1 yield for {unkown}. supported: {list(supported)}"
            "Map the waste to the closest supprt type, or ask group 1 to run (simulation building team)"
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

def farm_mix_row(df: pd.DataFrame, wet_kg_per_day:dict, vs_fraction_of_wet:dict, pretreatment_id: str = "S3", label:str = "Farm mix", reference_id: str = "S3", use_batch: bool = True, yields:dict | None = None, constants: tuple | None = None) -> pd.Series:
    if yields is None:
        yields, _ = fit_feedstock_yield(df, reference_id)
    mj_per_nm3, elec_eff = constants if constants is not None else energy_constants(df)
    vs = vs_from_wet(wet_kg_per_day, vs_fraction_of_wet)
    mult, basis = scenario_multiplier(df, pretreatment_id, yields, reference_id, use_batch)
    row = mix_row(vs, yields, mj_per_nm3, elec_eff, mult, label)
    row["scenario_id"] = pretreatment_id
    row["multiplier"] = mult
    row["basis"] = basis
    return row

def composition_table(df:pd.DataFrame, compositions: dict, vs_fraction_of_wet:dict, pretreatment_id:str = "S3", operating_days:float = 365, reference_id: str = "S3", use_batch: bool = True, yeilds: dict | None = None, constants: tuple | None = None) -> pd.DataFrame:
    if yeilds is None:
        yeilds, _ = fit_feedstock_yield(df, reference_id)
    if constants is None:
        constants = energy_constants(df)
    rows = []
    for name, wet in compositions.items():
        row = farm_mix_row(df, wet, vs_fraction_of_wet, pretreatment_id, name, reference_id, use_batch, yeilds, constants)
        rows.append(
            {
                "composition": name,
                "wet_kg_per_day":sum(wet.values()),
                "vs_kg_per_day":sum(vs_from_wet(wet, vs_fraction_of_wet).values()),
                "ch4_nm3_per_day":row[COL_YIELD],
                "electricity_kwh_per_year": row[COL_ELEC_MJ] / mj_per_kwh * operating_days,
            }
        )
    out = pd.DataFrame(rows)
    base = out["electricity_kwh_per_year"].iloc[0]
    out["vs_first"] = out["electricity_kwh_per_year"] / base -1
    return out
