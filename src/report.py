
from pathlib import Path

import pandas as pd
import yaml
import warnings

from src.energy_balance import format_balance, run_balance
from src.Feedstockmodel import (
    COL_MIX,
    composition_table,
    energy_constants,
    farm_mix_row,
    fit_feedstock_yield,
    load_properties,
    parse_mixture,
    same_mixture,
    Scenario_data_issue,
    vs_from_wet,
)
from src.group_1_adapter import (
    COL_ELEC_MJ,
    COL_ID,
    COL_NAME,
    COL_SPEC,
    COL_SPEC_REPORTED,
    COL_STABILITY,
    COL_YIELD,
    align_to_group1,
    group1_basis,
    mj_per_kwh,
    chp_heat_available_kwh,
    get_scenario,
    load_scenarios,
    missing_ids,
    scenario_to_flows,
    select_ids,
)
from src.heat_recovery import heat_offset

REQUIRED_SECTIONS = (
    "farm", "pretreatment", "chp", "heat_recovery", "energy_value", "emissions",
)


def load_assumptions(path) -> dict:
    a = yaml.safe_load(Path(path).read_text())
    missing = [s for s in REQUIRED_SECTIONS if s not in a]
    if missing:
        raise ValueError(f"assumptions file is missing section(s): {missing}")
    return a


def placeholders(a: dict) -> list:
    """Sections still marked placeholder, so the report can flag them."""
    return [k for k, v in a.items() if isinstance(v, dict) and v.get("status") == "placeholder"]

def scenario_settings(a:dict) -> dict:
    s = a.get("scenarios") or {}
    return {
        "run": s.get("run"),
        "base_id": s.get("base_id", "S1"),
        "reference_id": s.get("reference_id", "S3"),
        "use_batch": s.get("use_batch_adjustment", True)
    }

def alignment_checks(a: dict, df: pd.DataFrame, info:dict, props:dict, yields:dict, constants:tuple) -> dict:
    b = info["basis"]
    ref_id = scenario_settings(a)["reference_id"]
    ref = get_scenario(df, ref_id)
    out = {
        "yield_basis": b["yield_basis"],
        "reference_id": ref_id,
        "ref_yield": float(ref[COL_SPEC]),
        "ref_reported": float(ref[COL_SPEC_REPORTED]),
        "reported_matches": info["reported_matches"],
        "group1_vs_fraction": b["ts_fraction"] * b["vs_of_ts"],
        "your_vs_fraction": props.get("food_waste"),
        "reconcile": None,
    } 
    farm_wet = a["farm"]["waste_wet_kg_per_day"]
    farm_vs = vs_from_wet(farm_wet, props)
    total = sum(farm_vs.values())
    out["farm_vs_shares"] = {k: v / total for k, v in farm_vs.items()}

    if b["yield_basis"] == "reported" or "food_waste" not in props:
        return out
    if not same_mixture(parse_mixture(ref[COL_MIX]), {"food_waste": 1.0}):
        return out
    if ref[COL_ID] in b["olr_overrides"]:
        return out

    row = farm_mix_row(df, {"food_waste": b["wet_kg_per_day"]}, props, ref_id, "Group 1 feed",  ref_id, True, yields, constants)

    ours = row[COL_ELEC_MJ] / mj_per_kwh
    theirs = float(ref[COL_ELEC_MJ]) / mj_per_kwh
    if b["yield_basis"] == "practical":
        theirs *= float(ref[COL_STABILITY])
    diff = ours / theirs - 1
    out["reconcile"] = {"ours_kwh_day": ours, "theirs_kwh_day": theirs, "diff": diff}
    if abs(diff) > 0.01:
        warnings.warn(
            f"Group 1's own feed gives {diff:.1%} electricity in your model. Your food-waste VS "
            f"fraction is {props['food_waste']:.3f}; Group 1 use {out['group1_vs_fraction']:.3f}.",
            UserWarning, stacklevel=2,
        )
    return out

def _evaluate(a: dict, row: pd.Series):
    farm, chp, hr = a["farm"], a["chp"], a["heat_recovery"]
    val, em = a["energy_value"], a["emissions"]
    
    days = float(farm["operating_days_per_year"])
    wet = farm["waste_wet_kg_per_day"]

    heat_available = chp_heat_available_kwh(
        row, operating_days=days, thermal_eff=chp["thermal_efficiency"]
    )
    heat = heat_offset(
        heat_available, hr["usable_fraction"], hr["boiler_efficiency"], val["heat_fuel_price"]
    )
    flows = scenario_to_flows(row, operating_days=days, own_use_frac=chp["own_use_fraction"])
    bal = run_balance(flows, recovered_kwh=heat["useful_heat_kwh"])

    net_kwh = bal["net_electric_kwh"]
    self_kwh = net_kwh * val["self_use_fraction"]
    elec_saving = (
        self_kwh * val["electricity_avoided"] + (net_kwh - self_kwh) * val["electricity_export"]
    )
    co2 = (
        net_kwh * em["grid_kg_co2_per_kwh"] + heat["displaced_fuel_kwh"] * em["heat_fuel_kg_co2_per_kwh"]
    ) / 1000.0

    summary = {
        "Waste processed (wet t/yr)": sum(wet.values()) * days / 1000.0,
        "Methane (Nm3/yr)": row[COL_YIELD] * days,
        "Gross electricity (kWh/yr)": bal["gross_useful_kwh"],
        "Net electricity (kWh/yr)": net_kwh,
        "Useful recovered heat (kWh/yr)": heat["useful_heat_kwh"],
        "Overall efficiency (%)": bal["net_efficiency"] * 100,
        "Electricity saving ($/yr)": elec_saving,
        "Heat saving ($/yr)": heat["annual_saving"],
        "CO2 avoided (t/yr)": co2,
    }
    return bal, heat, summary

def scenario_table(a:dict, df:pd.DataFrame, props:dict, ids=None, yields: dict | None = None, constants: tuple | None = None) -> pd.DataFrame:
    s = scenario_settings(a)
    ref_id = s["reference_id"]
    ids = select_ids(df, ids)
    if yields is None:
        yields, _ = fit_feedstock_yield(df, ref_id)
    if constants is None:
        constants = energy_constants(df)
    flagged = set(Scenario_data_issue(df)[COL_ID])
    ref_mix = parse_mixture(get_scenario(df, ref_id)[COL_MIX])
    wet = a["farm"]["waste_wet_kg_per_day"]

    rows = []
    for sid in ids:
        g1 = get_scenario(df, sid)
        row = farm_mix_row(df, wet, props, sid, "Farm mix", ref_id, s["use_batch"], yields, constants)
        _, _, summary = _evaluate(a, row)
        summary.pop("Waste processed (wet t/yr)")

        notes = []
        if sid in flagged:
            notes.append("Group 1 energy columns don't match its yield; energy taken from yield")
        if row["basis"].startswith("batch"):
            notes.append("effect from uncalibrated batch test")
        if not same_mixture(parse_mixture(g1[COL_MIX]), ref_mix):
            notes.append("different feedstock; only its process effect is applied to the farm mix")

        rows.append({
            COL_ID: sid,
            COL_NAME: g1[COL_NAME],
            "Group 1 mixture": g1[COL_MIX],
            "Yield multiplier": row["multiplier"],
            "Basis": row["basis"],
            **summary, 
            "Total Savings ($/yr)": summary["Electricity saving ($/yr)"] + summary["Heat saving ($/yr)"],
            "Notes": "; ".join(notes),
        })

    out = pd.DataFrame(rows)
    base = s["base_id"]
    if base in set(out[COL_ID]):
        b = out.loc[out[COL_ID] == base, "Net electricity (kWh/yr)"].iloc[0]
        out.insert(
            out.columns.get_loc("Total Savings ($/yr)") + 1,
            f"Net electricity vs {base} (%)",
            (out["Net electricity (kWh/yr)"] / b -1) * 100,
        )
    return out

def _load(scenario_path, a:dict | None = None):
    df = scenario_path.copy() if isinstance(scenario_path, pd.DataFrame) else load_scenarios(scenario_path)
    return align_to_group1(df, (a or {}).get("group1_basis"))

def run_all_scenario(assumptions, scenario_path, properties_path, ids=None) -> pd.DataFrame:
    a = assumptions if isinstance(assumptions, dict) else load_assumptions(assumptions)
    (df, _), props = _load(scenario_path, a), load_properties(properties_path)
    yields, _ = fit_feedstock_yield(df, scenario_settings(a)["reference_id"])
    return scenario_table(a, df, props, ids, yields, energy_constants(df))


def run_pipeline(assumptions, scenario_path, properties_path, scenario_id: str | None = None) -> dict:

    a = assumptions if isinstance(assumptions, dict) else load_assumptions(assumptions)
    df, align_info = _load(scenario_path, a)
    props = load_properties(properties_path)
    s = scenario_settings(a)
    sid = scenario_id or a["pretreatment"]["scenario_id"]
    days = float(a["farm"]["operating_days_per_year"])
    wet = a["farm"]["waste_wet_kg_per_day"]

    yields, _ = fit_feedstock_yield(df, s["reference_id"])
    constants = energy_constants(df)

    row = farm_mix_row(df, wet, props, sid, "Farm mix", s["reference_id"], s["use_batch"], yields, constants)
    bal, heat, summary = _evaluate(a, row)

    comparison = composition_table(
        df,
        {"Farm mix": wet, **a.get("compositions",{})},
        props,
        sid,
        days,
        s["reference_id"],
        s["use_batch"],
        yields,
        constants
    )

    results = {
        "assumptions": a,
        "scenario_id":sid,
        "scenario_row":row,
        "balance":bal,
        "heat":heat,
        "comparison":comparison,
        "placeholders": placeholders(a),
        "yields": yields,
        "data_issues": Scenario_data_issue(df),
        "missing_ids": missing_ids(df),
        "summary": summary,
        "alignment": alignment_checks(a, df, align_info, props, yields, constants),
    }
    if s["run"]:
        results["all_scenarios"] = scenario_table(a, df, props, s["run"], yields, constants)
    return results

def summary_frame(results: dict) -> pd.DataFrame:
    rows = [
        {"metric": k, "value": ("not yet available" if v is None else round(float(v), 2))}
        for k, v in results["summary"].items()
    ]
    return pd.DataFrame(rows)


def _save_charts(results: dict, out_dir: Path) -> list:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    paths = []
    bal = results["balance"]

    fig, ax = plt.subplots(figsize=(7, 4))
    bottom = 0.0
    for label, value in bal["breakdown"].items():
        ax.bar("Energy out", value / 1000, bottom=bottom / 1000, label=label)
        bottom += value
    ax.bar("Energy in", bal["e_in"] / 1000, label="Methane in", color="0.6")
    ax.set_ylabel("MWh per year")
    ax.set_title(f"Energy balance (closure error {bal['closure']:.1%})")
    ax.legend(fontsize=8)
    fig.tight_layout()
    p = out_dir / "energy_balance.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)

    comp = results["comparison"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(comp["composition"], comp["electricity_kwh_per_year"] / 1000)
    ax.set_xlabel("Electricity, MWh per year")
    ax.set_title("Effect of waste composition")
    fig.tight_layout()
    p = out_dir / "composition.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)

    if "all_scenarios" in results:
        t = results["all_scenarios"].iloc[::-1]
        colours = ["tab:orange" if b.startswith("batch") else "tab:blue" for b in t["Basis"]]
        fig, ax = plt.subplots(figsize=(8, 0.32 * len(t) + 1.5))
        ax.barh(t[COL_ID] + "  " + t[COL_NAME], t["Net electricity (kWh/yr)"] / 1000, color=colours)
        ax.set_xlabel("Net electricity, MWh per year (orange = uncalibrated batch test)")
        ax.set_title("Farm mix under each Group 1 scenario")
        ax.tick_params(axis="y", labelsize=8)
        fig.tight_layout()
        p = out_dir / "all_scenarios.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        paths.append(p)
    return paths
        


def write_report(results: dict, out_dir="outputs", charts: bool = True) -> dict:
    """Write summary.csv, comparison.csv, report.md and (optionally) two charts."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = {}

    summary = summary_frame(results)
    summary.to_csv(out / "summary.csv", index=False)
    written["summary"] = out / "summary.csv"
    results["comparison"].to_csv(out / "comparison.csv", index=False)
    written["comparison"] = out / "comparison.csv"
    if "all_scenarios" in results:
        results["all_scenarios"].to_csv(out / "all_scenarios.csv", index = False)
        written["all_scenarios"] = out / "all_scenarios.csv"

    a = results["assumptions"]
    missing = [k for k, v in results["summary"].items() if v is None]
    if charts:
        for p in _save_charts(results, out):
            written[p.stem if p.stem not in written else f"{p.stem}_chart"] = p

    a = results["assumptions"]
    missing = [k for k, v in results["summary"].items() if v is None]
    lines = [
        f"# {a.get('project', {}).get('name', 'Waste to energy')} - Group 2 energy and TEA",
        "",
        f"## Summary ({results['scenario_id']})",
        "",
        summary.to_markdown(index=False),
        "",
        "## Energy balance",
        "",
        "```",
        format_balance(results["balance"]),
        "```",
        "",
        "## Effect of waste composition",
        "",
        results["comparison"].round(2).to_markdown(index=False),
        "",
    ]

    al = results.get("alignment")
    if al:
        basis_text = {
            "formula": "methane per kg VS fed (Treated Yield / VS fed), as in formulas 22-23",
            "practical": "methane per kg VS fed x Group 1's stability score",
            "reported": "Group 1's Specific Yield column as reported",
        }[al["yield_basis"]]
        lines += [
            "## Alignment with Group 1",
            "",
            f"- Yield basis: {basis_text}",
            f"- {al['reference_id']}: {al['ref_yield']:.1f} L CH4/kg VS used; "
            f"Group 1's Specific Yield column says {al['ref_reported']:.1f}",
        ]
        if al["reported_matches"] is False:
            lines.append("- Group 1's Specific Yield column is not methane per kg VS fed "
                         "(it is treated yield x stability / 2.5), so it is not used")
        if al["your_vs_fraction"] is not None:
            lines.append(f"- Food-waste VS share of wet weight: yours {al['your_vs_fraction']:.3f}, "
                         f"Group 1 {al['group1_vs_fraction']:.3f}")
        shares = ", ".join(f"{k} {v:.1%}" for k, v in al["farm_vs_shares"].items())
        lines.append(f"- Farm mix by VS (Group 1's SCG percentages are by VS): {shares}")
        rc = al["reconcile"]
        if rc:
            verdict = "matches" if abs(rc["diff"]) <= 0.01 else "does not match"
            lines.append(
                f"- Check: Group 1's own feed in your model gives {rc['ours_kwh_day']:.2f} kWh/day "
                f"of electricity vs their {rc['theirs_kwh_day']:.2f} ({rc['diff']:+.1%}, {verdict})"
            )
        lines.append("")
 
    if "all_scenarios" in results:
        t = results["all_scenarios"]
        keep = [c for c in t.columns if c in (
            COL_ID, COL_NAME, "Yield multiplier", "Net electricity (kWh/yr)",
            "Total Savings ($/yr)", "CO2 avoided (t/yr)", "Notes",
        ) or c.startswith("Net electricity vs")]
        lines += [
            "## All scenarios",
            "",
            "The farm's own waste run under each Group 1 scenario. Full columns are in all_scenarios.csv.",
            "",
            t[keep].round(3).to_markdown(index=False),
            "",
        ]
 
    issues = results.get("data_issues")
    gaps = results.get("missing_ids") or []
    if gaps or (issues is not None and len(issues)):
        lines += ["## Data checks (for Group 1)", ""]
        if gaps:
            lines.append(f"Not in the scenario file: {', '.join(gaps)}.")
            lines.append("")
        if issues is not None and len(issues):
            lines.append("These rows have energy columns that do not match their methane yield. "
                         "The pipeline uses the yield and ignores those columns.")
            lines.append("")
            lines.append(issues.round(3).to_markdown(index=False))
            lines.append("")
 
    lines += ["## Status", ""]
    if missing:
        lines.append(f"Not yet available (waiting on Group 3): {', '.join(missing)}.")
    if results["placeholders"]:
        lines.append(
            "These assumptions are still placeholders, so the numbers above are "
            f"illustrative: {', '.join(results['placeholders'])}."
        )
        lines.append("")
        lines.append("| section | source / who to ask |")
        lines.append("| --- | --- |")
        for k in results["placeholders"]:
            lines.append(f"| {k} | {a[k].get('source', '')} |")
    if not missing and not results["placeholders"]:
        lines.append("All inputs are confirmed.")
 
    (out / "report.md").write_text("\n".join(lines) + "\n")
    written["report"] = out / "report.md"
    return written
