# Farm waste-to-energy - Group 2 energy and TEA

## Summary (S3)

| metric                         |    value |
|:-------------------------------|---------:|
| Waste processed (wet t/yr)     |   180    |
| Methane (Nm3/yr)               | 17425.8  |
| Gross electricity (kWh/yr)     | 60667.2  |
| Net electricity (kWh/yr)       | 54600.5  |
| Useful recovered heat (kWh/yr) | 54600.9  |
| Overall efficiency (%)         |    63    |
| Electricity saving ($/yr)      | 16161.8  |
| Heat saving ($/yr)             |  3854.19 |
| CO2 avoided (t/yr)             |    60.96 |

## Energy balance

```
Energy in                      173,336kWh/yr
Gross useful output             60,667kWh/yr
of which own use                 6,067kWh/yr
Net electricity                 54,601kWh/yr
Recovered heat used             54,601kWh/yr
Loses                           58,068kWh/yr
Total out                      173,336kWh/yr
Closure error                    0.0%
Efficiency (gross)              66.5%
Efficiency (net)                63.0%
```

## Effect of waste composition

| composition        |   wet_kg_per_day |   vs_kg_per_day |   ch4_nm3_per_day |   electricity_kwh_per_year |   vs_first |
|:-------------------|-----------------:|----------------:|------------------:|---------------------------:|-----------:|
| Farm mix           |              500 |          112.5  |             48.41 |                    60667.2 |       0    |
| All food waste     |              500 |          112.5  |             48.41 |                    60667.2 |       0    |
| Carbohydrate-heavy |              500 |          146.25 |             52.06 |                    65248.8 |       0.08 |
| With oil           |              500 |          148.75 |             81.69 |                   102386   |       0.69 |
| All oil            |              500 |          475    |            381.27 |                   477851   |       6.88 |

## Alignment with Group 1

- Yield basis: methane per kg VS fed (Treated Yield / VS fed), as in formulas 22-23
- S3: 430.2 L CH4/kg VS used; Group 1's Specific Yield column says 285.1
- Group 1's Specific Yield column is not methane per kg VS fed (it is treated yield x stability / 2.5), so it is not used
- Food-waste VS share of wet weight: yours 0.225, Group 1 0.225
- Farm mix by VS (Group 1's SCG percentages are by VS): food_waste 100.0%
- Check: Group 1's own feed in your model gives 3.37 kWh/day of electricity vs their 3.37 (+0.0%, matches)

## All scenarios

The farm's own waste run under each Group 1 scenario. Full columns are in all_scenarios.csv.

| Scenario ID   | Scenario                                 |   Yield multiplier |   Net electricity (kWh/yr) |   CO2 avoided (t/yr) |   Total Savings ($/yr) |   Net electricity vs S3 (%) | Notes   |
|:--------------|:-----------------------------------------|-------------------:|---------------------------:|---------------------:|-----------------------:|----------------------------:|:--------|
| S3            | Moderate fungal pretreatment (Reference) |                  1 |                    54600.5 |                60.96 |                20015.9 |                           0 |         |

## Data checks (for Group 1)

Not in the scenario file: s18, s19, s20.

These rows have energy columns that do not match their methane yield. The pipeline uses the yield and ignores those columns.

| Scenario ID   | check                           |   value |   expected |
|:--------------|:--------------------------------|--------:|-----------:|
| S16           | Methane energy content (MJ/Nm3) |  32.217 |     35.808 |

## Status

These assumptions are still placeholders, so the numbers above are illustrative: chp, heat_recovery, emissions.

| section | source / who to ask |
| --- | --- |
| chp | need an engine sheet |
| heat_recovery | need digester heating demand and on-form heat use |
| emissions | find publisher and cite it |
