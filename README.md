# Group 2 - Energy Recovery6 and Conceptual TEA
**Grabbing Scenario Scaling them up for actual use**

Core group 2 of Waste-to-Engery project. This code takes a farm food-waste composition, worksout how much energy it produces, checks the energy balance closes, and report what farmer saves each year

**Group 2:** The Minh Tran (103488609, team lead), Serei Putthi Ros(105215456)

##What this awnser

The supervisor question is wether this is worthit for the farmer: What does it cost, how much energy does it produce, and how much does that save over a year. This code covers the energy and savings side.

Group 1's simulation give yield at laboratory scale(3.4 volatile soilids per day ) This code would scale to account fro farm and account for the fact farmer waste will not have same composition as the lab's

##Quick Start
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Output lands in `outputs/`: `report.md`, `summary.csv,` `comparison.csv` and two charts.

## Project Structure

```
Group 2/
├── main.py                     command-line runner
├── data/
│   ├── assumptions.yaml        every input and assumption
│   ├── scenario_summary.csv    from Group 1
│   └── feedstock_properties.csv  moisture / volatile solids fractions
├── src/
│   ├── Feedstockmodel.py       waste composition -> methane
│   ├── group_1_adapter.py      Group 1's format -> annual kWh
│   ├── heat_recovery.py        usable heat and displaced fuel
│   ├── energy_balance.py       first-law check, net output
│   └── report.py               savings, CO2, writes the output
├── tests/                      pytest suite
└── outputs/                    generated, not committed
```


## How the calculation works
Each stage, with the numbers from a 400kg/day run (320kg food waste, 80kg spent coffee grounds):

| Stage | Module | Result |
| --- | --- | --- |
| Wet waste to volatile solids | `Feedstockmodel.vs_from_wet` | 98.4 kg VS/day |
| Volatile solids to methane | `Feedstockmodel.methane_nm3` | 27.18 Nm³/day |
| Methane to energy | `Feedstockmodel.mix_row` | 973 MJ/day |
| Per day to per year | `group_1_adapter._to_kwh_per_year` | 98,672 kWh/yr in |
| Heat recovery | `heat_recovery.heat_offset` | 31,082 kWh/yr usable |
| Energy balance | `energy_balance.run_balance` | 31,081 kWh/yr net electricity, 63% efficiency |
| Savings | `report.run_pipeline` | about $10,100/yr |

Only part of wet waste can produce gas, so first stage matter more that it looks:
400kg of waste and only 98 kg of usable material

Heat recovery is what lifts efficiency from 31.5% to 63% the engine turn 35% of the methane energy to electricity; recovering the waste heat roughly double the useful output

### Feedstock yeilds

`fit_feetstock_yeild` does not use Group 1's scenario one at a time. It fits a specific yeild for each feedstock across all their same-pretreatment scenarios, than builds any compisition from those six numbers

| Feedstock | L CH₄ / kg VS |
| --- | --- |
| Oil | 532 |
| Food waste | 285 |
| Meat | 261 |
| Spent coffee grounds | 254 |
| Rice | 232 |
| Banana peel | 200 |

Group 1's food-waste/coffee blends combine exactly in proportion, which is what makes this valid. Coffee ground were never run alone, so 254 is extraploated from the blends.

##Configuration
eveything is in `data/assumptions.yaml` Seven Section are required: `farm`, `pretreatment`, `chp`, `heat_recovery`, `energy_value`, `emission`, `costs`.

Supported waste types: `food_waste`, `scg`, `rice`, `meat`, `oil`, `peel`. Anything else raises an error - to map the closest type or ask group 1 

## Known limitation
**Yields assume the farm's loading rate matches the lab's.** Group 1's scenario S9 produces twice the metane of S6 for the same mix but 20% less per kg of volatile solids. Scaling the feed up without sizing the digester with it will overstate the energy.

**untested blends.** Only food waste with coffee grounds was shown to combine proportionally. Rice-Heavy and oil blends assume the same behavior.

