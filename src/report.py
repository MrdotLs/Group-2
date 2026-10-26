"""Report: run the four energy modules from assumptions.yaml and write the output.

run_pipeline()  does the calculation and returns a dict of results
write_report()  turns that dict into summary.csv, two charts and report.md

The cost side is optional. Until Group 3 delivers a total, the report covers the
energy results and says plainly which cost numbers are missing.
"""

from pathlib import Path

import pandas as pd
import yaml

from src.energy_balance import format_balance, run_balance
from src.Feedstockmodel import (
    composition_table,
    farm_mix_row,
    fit_feedstock_yield,
    load_properties,
)
from src.group_1_adapter import (
    COL_ELEC_MJ,
    mj_per_kwh,
    chp_heat_available_kwh,
    load_scenarios,
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


def run_pipeline(assumptions, scenario_path, properties_path) -> dict:
    """Composition -> methane -> electricity and heat -> energy balance -> savings."""
    a = assumptions if isinstance(assumptions, dict) else load_assumptions(assumptions)
    df = load_scenarios(scenario_path)
    props = load_properties(properties_path)

    farm, chp, hr = a["farm"], a["chp"], a["heat_recovery"]
    val, days = a["energy_value"], float(farm["operating_days_per_year"])
    wet = farm["waste_wet_kg_per_day"]

    row = farm_mix_row(df, wet, props, a["pretreatment"]["scenario_id"], label="Farm mix")

    heat_available = chp_heat_available_kwh(
        row, operating_days=days, thermal_eff=chp["thermal_efficiency"]
    )
    heat = heat_offset(
        heat_available, hr["usable_fraction"], hr["boiler_efficiency"], val["heat_fuel_price"]
    )

    from src.group_1_adapter import scenario_to_flows  # local import keeps the top tidy

    flows = scenario_to_flows(row, operating_days=days, own_use_frac=chp["own_use_fraction"])
    bal = run_balance(flows, recovered_kwh=heat["useful_heat_kwh"])

    # Savings: electricity used on site avoids the retail tariff, the rest is exported.
    net_kwh = bal["net_electric_kwh"]
    self_kwh = net_kwh * val["self_use_fraction"]
    elec_saving = (
        self_kwh * val["electricity_avoided"]
        + (net_kwh - self_kwh) * val["electricity_export"]
    )
    annual_saving = elec_saving + heat["annual_saving"]

    em = a["emissions"]
    co2 = (
        net_kwh * em["grid_kg_co2_per_kwh"]
        + heat["displaced_fuel_kwh"] * em["heat_fuel_kg_co2_per_kwh"]
    ) / 1000.0

    comparison = composition_table(
        df,
        {"Farm mix": wet, **a.get("compositions", {})},
        props,
        a["pretreatment"]["scenario_id"],
        days,
    )

    return {
        "assumptions": a,
        "scenario_row": row,
        "balance": bal,
        "heat": heat,
        "comparison": comparison,
        "placeholders": placeholders(a),
        "yields": fit_feedstock_yield(df)[0],
        "summary": {
            "Waste processed (wet t/yr)": sum(wet.values()) * days / 1000.0,
            "Methane (Nm3/yr)": row["Treated Yield (Nm3/d)"] * days,
            "Gross electricity (kWh/yr)": bal["gross_useful_kwh"],
            "Net electricity (kWh/yr)": net_kwh,
            "Useful recovered heat (kWh/yr)": heat["useful_heat_kwh"],
            "Overall efficiency (%)": bal["net_efficiency"] * 100,
            "Electricity saving ($/yr)": elec_saving,
            "Heat saving ($/yr)": heat["annual_saving"],
            "CO2 avoided (t/yr)": co2,
        },
    }


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

    if charts:
        for p in _save_charts(results, out):
            written[p.stem] = p

    a = results["assumptions"]
    missing = [k for k, v in results["summary"].items() if v is None]
    lines = [
        f"# {a.get('project', {}).get('name', 'Waste to energy')} - Group 2 energy and TEA",
        "",
        "## Summary",
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
        "## Status",
        "",
    ]
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