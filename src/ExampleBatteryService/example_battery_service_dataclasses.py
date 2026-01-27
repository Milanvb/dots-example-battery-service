from dataclasses import dataclass
from typing import List

@dataclass
class MaxChargeAndDischargeOutput:
    max_charge_active_power : float | None = None
    max_discharge_active_power : float | None = None


