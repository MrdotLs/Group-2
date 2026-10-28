# Farm waste-to-energy - Group 2 energy and TEA

## Summary (S3)

| metric                         |    value |
|:-------------------------------|---------:|
| Waste processed (wet t/yr)     |   146    |
| Methane (Nm3/yr)               | 15232.3  |
| Gross electricity (kWh/yr)     | 53030.8  |
| Net electricity (kWh/yr)       | 47727.7  |
| Useful recovered heat (kWh/yr) | 47728.1  |
| Overall efficiency (%)         |    63    |
| Electricity saving ($/yr)      | 12122.8  |
| Heat saving ($/yr)             |  3369.04 |
| CO2 avoided (t/yr)             |    44.64 |

## Energy balance

```
Energy in                      151,518kWh/yr
Gross useful output             53,031kWh/yr
of which own use                 5,303kWh/yr
Net electricity                 47,728kWh/yr
Recovered heat used             47,728kWh/yr
Loses                           50,759kWh/yr
Total out                      151,518kWh/yr
Closure error                    0.0%
Efficiency (gross)              66.5%
Efficiency (net)                63.0%
```

## Effect of waste composition

| composition        |   wet_kg_per_day |   vs_kg_per_day |   ch4_nm3_per_day |   electricity_kwh_per_year |   vs_first |
|:-------------------|-----------------:|----------------:|------------------:|---------------------------:|-----------:|
| Farm mix           |              400 |           100   |             41.73 |                    53030.8 |       0    |
| All food waste     |              400 |            90   |             38.72 |                    49207.9 |      -0.07 |
| Carbohydrate-heavy |              400 |           116   |             42.5  |                    54009.7 |       0.02 |
| With oil           |              400 |           109.5 |             53.54 |                    68038.5 |       0.28 |
| All oil            |              400 |           380   |            305.01 |                   387590   |       6.31 |

## Alignment with Group 1

- Yield basis: methane per kg VS fed (Treated Yield / VS fed), as in formulas 22-23
- S3: 430.2 L CH4/kg VS used; Group 1's Specific Yield column says 285.1
- Group 1's Specific Yield column is not methane per kg VS fed (it is treated yield x stability / 2.5), so it is not used
- Food-waste VS share of wet weight: yours 0.225, Group 1 0.225
- Farm mix by VS (Group 1's SCG percentages are by VS): food_waste 72.0%, scg 28.0%
- Check: Group 1's own feed in your model gives 3.37 kWh/day of electricity vs their 3.37 (+0.0%, matches)

## All scenarios

The farm's own waste run under each Group 1 scenario. Full columns are in all_scenarios.csv.

| Scenario ID   | Scenario                                     |   Yield multiplier |   Net electricity (kWh/yr) |   CO2 avoided (t/yr) |   Total Savings ($/yr) |   Net electricity vs S3 (%) | Notes                                                                   |
|:--------------|:---------------------------------------------|-------------------:|---------------------------:|---------------------:|-----------------------:|----------------------------:|:------------------------------------------------------------------------|
| S1            | Control food waste                           |              0.895 |                    42698.6 |               39.936 |                13859.5 |                     -10.537 |                                                                         |
| S2            | Low fungal pretreatment                      |              0.939 |                    44818.7 |               41.919 |                14547.6 |                      -6.095 |                                                                         |
| S3            | Moderate fungal pretreatment (Reference)     |              1     |                    47727.7 |               44.64  |                15491.9 |                       0     |                                                                         |
| S4            | High fungal pretreatment                     |              1.049 |                    50045.1 |               46.807 |                16244.1 |                       4.855 |                                                                         |
| S5            | Extended fungal pretreatment                 |              1.086 |                    51820.1 |               48.467 |                16820.2 |                       8.574 |                                                                         |
| S6            | Moderate pretreatment + 10% SCG              |              1     |                    47742.7 |               44.654 |                15496.7 |                       0.031 | different feedstock; only its process effect is applied to the farm mix |
| S7            | Moderate pretreatment + 20% SCG              |              1     |                    47712.6 |               44.625 |                15487   |                      -0.032 | different feedstock; only its process effect is applied to the farm mix |
| S8            | Moderate pretreatment + 30% SCG              |              1     |                    47732.8 |               44.644 |                15493.5 |                       0.011 | different feedstock; only its process effect is applied to the farm mix |
| S9            | Moderate pretreatment + 10% SCG + high OLR   |              1     |                    47742.7 |               44.654 |                15496.7 |                       0.031 | different feedstock; only its process effect is applied to the farm mix |
| S10           | Carbohydrate-rich (Cooked Rice)              |              1     |                    47727.7 |               44.64  |                15491.9 |                       0     | different feedstock; only its process effect is applied to the farm mix |
| S11           | Protein-rich (Meat Waste)                    |              1     |                    47727.7 |               44.64  |                15491.9 |                      -0     | different feedstock; only its process effect is applied to the farm mix |
| S12           | Lipid-rich (Plant Oil)                       |              1     |                    47727.7 |               44.64  |                15491.9 |                      -0     | different feedstock; only its process effect is applied to the farm mix |
| S13           | Fibre-rich (Banana Peel)                     |              1     |                    47727.7 |               44.64  |                15491.9 |                       0     | different feedstock; only its process effect is applied to the farm mix |
| S14           | Acidogenic Bacterial Activity (+20%)         |              1.001 |                    47777   |               44.686 |                15507.9 |                       0.103 |                                                                         |
| S15           | Acetogenic Bacterial Activity (+20%)         |              1.001 |                    47777   |               44.686 |                15507.9 |                       0.103 |                                                                         |
| S16           | Acetoclastic Methanogenic Archaea (+20%)     |              1.112 |                    53052.7 |               49.62  |                17220.3 |                      11.157 | Group 1 energy columns don't match its yield; energy taken from yield   |
| S17           | Hydrogenotrophic Methanogenic Archaea (+20%) |              1     |                    47727.7 |               44.64  |                15491.9 |                       0     |                                                                         |
| S21           | Low biochar addition                         |              1.001 |                    47790.8 |               44.699 |                15512.3 |                       0.132 | effect from uncalibrated batch test                                     |
| S22           | Moderate biochar addition                    |              1.001 |                    47789   |               44.697 |                15511.8 |                       0.128 | effect from uncalibrated batch test                                     |
| S23           | High biochar addition                        |              1.001 |                    47770.8 |               44.68  |                15505.9 |                       0.09  | effect from uncalibrated batch test                                     |
| S24           | Reduced inoculum: S:I = 2                    |              0.975 |                    46511.3 |               43.502 |                15097   |                      -2.549 | effect from uncalibrated batch test                                     |

## Data checks (for Group 1)

Not in the scenario file: s18, s19, s20.

These rows have energy columns that do not match their methane yield. The pipeline uses the yield and ignores those columns.

| Scenario ID   | check                           |   value |   expected |
|:--------------|:--------------------------------|--------:|-----------:|
| S16           | methane energy content (MJ/Nm3) |  32.217 |     35.808 |

## Status

These assumptions are still placeholders, so the numbers above are illustrative: chp, heat_recovery, emissions.

| section | source / who to ask |
| --- | --- |
| chp | need an engine sheet |
| heat_recovery | need digester heating demand and on-form heat use |
| emissions | find publisher and cite it |
