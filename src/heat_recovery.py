

HOURS_PER_YEAR = 8760 #Can be change

def recovered_from_stream(
        m_dot_kg_s: float,
        cp_kj_per_kg_k: float,
        t_hot_in_c:float,
        t_hot_target_c: float,
        t_sink_c: float,
        hours_per_year: float,
        dt_min_k: float = 10.0,
        effectiveness: float = 0.8,
)-> float:
    if m_dot_kg_s <= 0 or cp_kj_per_kg_k <= 0:
        raise ValueError("Mass flow and cp must be positive")
    if not 0 < hours_per_year <= HOURS_PER_YEAR:
        raise ValueError(f"hours_per_year must be in (0, {HOURS_PER_YEAR})")
    if t_hot_target_c >= t_hot_in_c:
        raise ValueError ("Target temperature mut be below the inlet temperature")
    if dt_min_k < 0:
        raise ValueError ("dt_min_k must not be negative")
    if not 0 < effectiveness <= 1:
        raise ValueError("effectiveness must be between 0,1")

    floor_c = t_sink_c + dt_min_k
    t_out_c = max(t_hot_target_c, floor_c)
    if t_hot_in_c <= t_out_c:
        return 0.0

    q_kw = m_dot_kg_s * cp_kj_per_kg_k * (t_hot_in_c - t_out_c)
    return q_kw * hours_per_year * effectiveness

def heat_offset(
    recovered_kwh: float,
    usable_fraction: float,
    boiler_eff: float,
    fuel_price: float | None = None,
    
)-> dict:

    if recovered_kwh < 0:
        raise ValueError("recovered_kwh  cant be negative")
    if not 0 < usable_fraction <= 1:
        raise ValueError("usable_fraction must be (0,1)")
    if not 0 < boiler_eff <= 1:
        raise ValueError("Boiler_eff must be in (0,1)")
   
    useful = recovered_kwh * usable_fraction
    displaced = useful / boiler_eff

    out = {
        "recovered_kwh": recovered_kwh,
        "useful_heat_kwh": useful,
        "displaced_fuel_kwh": displaced,
    }
    if fuel_price is not None:
        out["annual_saving"] = displaced * fuel_price
        out["heat_price_per_kwh"] = fuel_price/boiler_eff
    return out