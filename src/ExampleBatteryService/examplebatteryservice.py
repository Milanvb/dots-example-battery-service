from datetime import datetime
from esdl import esdl
import helics as h
from dots_infrastructure.DataClasses import EsdlId, TimeStepInformation
from dots_infrastructure.CalculationServiceHelperFunctions import get_single_param_with_name
from dots_infrastructure.Logger import LOGGER
from esdl import EnergySystem

from ExampleBatteryService.example_battery_service_base import ExampleBatteryServiceBase
from ExampleBatteryService.example_battery_service_dataclasses import FullSelfConsumptionOutput

class ExampleBatteryService(ExampleBatteryServiceBase):

    def init_calculation_service(self, energy_system: esdl.EnergySystem):
        self.max_capacity : dict[EsdlId, float] = {}
        self.initial_capacity : dict[EsdlId, float] = {}
        self.current_charge : dict[EsdlId, float] = {}
        for esdl_object in energy_system.eAllContents():
            if isinstance(esdl_object, esdl.Battery):
                self.max_capacity[esdl_object.id] = 3000
                self.current_charge[esdl_object.id] = self.initial_capacity

    def charge_battery(self, to_charge, esdl_id):
        current_charge = self.current_charge[esdl_id]
        max_capacity = self.max_capacity[esdl_id]
        amount_charged = to_charge
        if current_charge + to_charge > max_capacity:
            self.current_charge[esdl_id] = self.max_capacity[esdl_id]
            amount_charged = abs(max_capacity - current_charge)
        else:
            self.current_charge[esdl_id] += to_charge
        return amount_charged
    
    def discharge_battery(self, to_discharge, esdl_id):
        current_charge = self.current_charge[esdl_id]
        amount_discharged = to_discharge
        if current_charge - to_discharge > 0:
            self.current_charge[esdl_id] -= to_discharge
        else:
            amount_discharged = current_charge
            self.current_charge[esdl_id] = 0
        return amount_discharged

    def full_self_consumption(self, param_dict : dict, simulation_time : datetime, time_step_number : TimeStepInformation, esdl_id : EsdlId, energy_system : EnergySystem):
        pv_active_power_w = get_single_param_with_name(param_dict, "pv_active_power")
        demand_active_power_w = get_single_param_with_name(param_dict, "demand_active_power")
        to_charge_w = pv_active_power_w - demand_active_power_w
        amount_charged = 0
        amount_discharged = 0
        if to_charge_w < 0:
            amount_discharged = self.discharge_battery(abs(to_charge_w), esdl_id)
        else:
            amount_charged = self.charge_battery(to_charge_w, esdl_id)

        consumption_w = 0
        if amount_charged > 0 and self.current_charge[esdl_id] == self.max_capacity[esdl_id]:
            consumption_w = pv_active_power_w - demand_active_power_w - amount_charged
        if amount_discharged > 0 and self.current_charge[esdl_id] == 0:
            consumption_w = pv_active_power_w - demand_active_power_w + amount_discharged

        return FullSelfConsumptionOutput(consumption_w)

if __name__ == "__main__":

    helics_simulation_executor = ExampleBatteryService()
    helics_simulation_executor.start_simulation()
    helics_simulation_executor.stop_simulation()
