
import pandas as pd 
import warnings 

out_kind = ("useful_out", "recovered_out", "loss")
valid_direction = ("in",) + out_kind + ("parasitic",)
required_columns = {"stream", "direction", "kwh_per_year"}


def validate_flows(df: pd.DataFrame) -> pd.DataFrame:
    missing_requirement = required_columns - set(df.columns)
    if missing_requirement:
        raise ValueError(f"Missing Column(s): {sorted(missing_requirement)}")

    df = df.copy()
    df["direction"] = df["direction"].astype("str").str.strip().str.lower()
    df["kwh_per_year"] = pd.to_numeric(df["kwh_per_year"], errors="raise")

    bad = sorted(set(df["direction"]) - set(valid_direction))
    if bad:
        raise ValueError(f"Unkown Directions(s) {bad}; ise on of {list(valid_direction)}")

    if(df["kwh_per_year"] < 0).any():
        raise ValueError(f"kwh_per_year must be higher then negative value")

    if df.loc[df["direction"] == "in", "kwh_per_year"].sum() <= 0:
        raise ValueError("No energy input found")
    return df

def load_flow(path) -> pd.DataFrame:
    return validate_flows(pd.read_csv(path))

def run_balance(flows, tol:float = 0.05, recovered_kwh: float | None = None) -> dict:
    df = validate_flows(flows)  if isinstance(flows, pd.DataFrame) else load_flow(flows)

    def total(kind: str) -> float:
        return float(df.loc[df["direction"] == kind, "kwh_per_year"].sum())

    e_in = total("in")
    gross = total("useful_out")
    recovered = total("recovered_out")
    loss = total("loss")
    parasatic = total("parasitic")

    if parasatic > gross:
        raise ValueError("Plant own use (parasitic) exceed gross useful output")

    if recovered_kwh is not None:
        if recovered_kwh < 0:
            raise ValueError("kwh cannot be negative")
        moved = recovered_kwh - recovered
        if loss - moved < 0:
            raise ValueError("recovered heat exceed the lost it meant to come out if it")
        recovered, loss = recovered_kwh, loss - moved

    e_out = gross + recovered + loss
    closure = abs(e_in - e_out) /  e_in
    closed = closure <= tol
    if not closed:
        warnings.warn(f"Energy balance does not close: error{closure:.1%} exceed {tol:.0%}", UserWarning, stacklevel=2)

    net_electric = gross - parasatic
    return{
        "e_in":e_in,
        "e_out": e_out,
        "closure": closure,
        "closed": closed,
        "gross_useful_kwh": gross,
        "parasitic_kwh": parasatic,
        "net_electric_kwh": net_electric,
        "recovered_heat_kwh": recovered,
        "loss_kwh": loss,
        "efficiency": (gross + recovered) / e_in,
        "net_efficiency": (net_electric + recovered) / e_in,
        "breakdown":{
            "Net electricity": net_electric,
            "Plant own use": parasatic,
            "Recovered heat": recovered,
            "Losses": loss,
        },
    }
   
def format_balance(r: dict) -> str:
    rows = [
        ("Energy in", r["e_in"]),
        ("Gross useful output", r["gross_useful_kwh"]),
        ("of which own use", r["parasitic_kwh"]),
        ("Net electricity", r["net_electric_kwh"]),
        ("Recovered heat used", r["recovered_heat_kwh"]),
        ("Loses", r["loss_kwh"]),
        ("Total out", r["e_out"]),
    ]
    lines = [f"{name:<24}{value:>14,.0f}kWh/yr" for name, value in rows]
    lines.append(f"{'Closure error':<24}{r['closure']:>13.1%}")
    lines.append(f"{'Efficiency (gross)':<24}{r['efficiency']:>13.1%}")
    lines.append(f"{'Efficiency (net)':<24}{r['net_efficiency']:>13.1%}")
    return "\n".join(lines)