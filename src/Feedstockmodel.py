
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
    get_scenario
)

COL_MIX = "Feedstock Mixture"
COL_FPSI = "FPSI"

FEEDSTOCK = ("food_waste", "scg", "rice", "meat", "oil", "peel")
_ALIASES = {"fw": "food_waste", "scg":"scg", "rice":"rice", "meat":"meat", "oil":"oil", "peel":"peel"}

def parse_mixture(text:str) -> dict:
    parts = re.findall(r"")