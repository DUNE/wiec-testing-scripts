import pyvisa
import sys
import json
import os
import time
from keysight_daq970a import Keysight970A
from rigol_dp832a import RigolDP832A
from caen_r8033dm_wrapper import CAENR8033DM_WRAPPER

class LDOmeasure:
    def __init__(self, config_file, name):
        self.prefix = "DUNE HV Crate Tester"
        print(f"{self.prefix} --> Welcome to the DUNE HV crate production testing script")
        with open(config_file, "r") as jsonfile:
            self.json_data = json.load(jsonfile)
        self.rm = pyvisa.ResourceManager('@py')

        #Initialize all instruments first so that you don't waste time with input if something is not connected
        self.c = CAENR8033DM_WRAPPER(self.json_data)
        self.k = Keysight970A(self.rm, self.json_data)

        #Since there are 2 Rigols, set them up here so they know what channels they have
        self.r0 = RigolDP832A(self.rm, self.json_data, 0)
        self.r0.setup_fan()
        self.r0.setup_heater_supply()
        self.r0.setup_heater_switch()

        self.r1 = RigolDP832A(self.rm, self.json_data, 1)
        self.r1.setup_hvpullup()
        self.r1.setup_fanread()
        self.sequence()

    def sequence(self):
        #Fan test
        self.k.initialize_fan()
        self.r0.power("ON", "fan")
        self.r1.power("ON", "fanread")
        print(f"{self.prefix} --> Fans turned on, waiting {float(self.json_data['fan_wait'])} seconds for the fans to reach steady state...")
        time.sleep(float(self.json_data['fan_wait']))
        fan_voltage = self.r0.get_voltage("fan")
        fan_current = self.r0.get_current("fan")
        fanread_voltage = self.r1.get_voltage("fanread")
        fanread_current = self.r1.get_current("fanread")
        fan_read_signal = self.k.measure_fan()
        self.r0.power("OFF", "fan")
        self.r0.power("OFF", "fanread")
        print(f"{self.prefix} --> Fans turned off")
        print(f"{self.prefix} --> Fan power supply was {fan_voltage}V and {fan_current}A")
        print(f"{self.prefix} --> Read signal for each fan was {fan_read_signal}")
        print(f"{self.prefix} --> Fan read pullup supply was {fanread_voltage}V and {fanread_current}A")

        #Heater test
        #First measure resistance of heating element with no power connected
        self.k.initialize_resistance()
        heater_resistance = self.k.measure_resistance()
        print(f"{self.prefix} --> Heating element resistances are {fan_read_signal}")

        #Then prepare RTD and switch relay to connect power
        self.k.initialize_rtd()
        temp1 = self.k.measure_rtd()
        self.r0.power("ON", "heat_supply")
        self.r0.power("ON", "heat_switch")
        print(f"{self.prefix} --> Heat turned on, waiting {float(self.json_data['heat_wait'])} seconds for the sensors to heat up...")
        time.sleep(float(self.json_data['heat_wait']))
        supply_voltage = self.r0.get_voltage("heat_supply")
        supply_current = self.r0.get_current("heat_supply")
        switch_voltage = self.r0.get_voltage("heat_switch")
        switch_current = self.r0.get_current("heat_switch")
        temp2 = self.k.measure_rtd()

        self.r0.power("OFF", "heat_supply")
        self.r0.power("OFF", "heat_switch")
        print(f"{self.prefix} --> Heat turned off")
        print(f"{self.prefix} --> Heat power supply was {supply_voltage}V and {supply_current}A")
        print(f"{self.prefix} --> Heat power switch was {switch_voltage}V and {switch_current}A")
        print(f"{self.prefix} --> Original temperatures were {temp1}")
        print(f"{self.prefix} --> Temperatures after {float(self.json_data['heat_wait'])} seconds were {temp2}")

        #HV Leakage Test
        #Turn on HV
        hv_results = {}
        self.r1.power("ON", "hvpullup")
        for i in range(8):
            #Do the positive voltage with open termination
            self.k.set_relay(0 << i, 0)
            self.c.turn_on(i)
            print(f"{self.prefix} --> HV reached max value, waiting {float(self.json_data['hv_stability_wait'])} seconds to stabilize...")
            hv_results[i] = {"P,NT,V" : self.c.get_voltage(i)}
            hv_results[i]["P,NT,C"] = self.c.get_current(i)

            #Turn on 10k termination
            self.k.set_relay(0 << i, 1 << i)
            print(f"{self.prefix} --> HV termination switched, waiting {float(self.json_data['hv_termination_wait'])} seconds...")
            time.sleep(float(self.json_data['hv_termination_wait']))

            hv_results[i]["P,10k,V"] = self.c.get_voltage(i)
            hv_results[i]["P,10k,C"] = self.c.get_current(i)
            self.c.turn_off(i)
            print(f"{self.prefix} --> HV turned off, waiting {float(self.json_data['hv_stability_wait'])} seconds to stabilize...")

            #Turn on negative voltage
            self.k.set_relay(1 << i, 0)
            self.c.turn_on(i+8)
            print(f"{self.prefix} --> HV reached max value, waiting {float(self.json_data['hv_stability_wait'])} seconds to stabilize...")
            hv_results[i]["N,NT,V"] = self.c.get_voltage(i)
            hv_results[i]["N,NT,C"] = self.c.get_current(i)

            #Turn on 10k termination
            self.k.set_relay(1 << i, 1 << i)
            print(f"{self.prefix} --> HV termination switched, waiting {float(self.json_data['hv_termination_wait'])} seconds...")
            time.sleep(float(self.json_data['hv_termination_wait']))

            hv_results[i]["N,10k,V"] = self.c.get_voltage(i)
            hv_results[i]["N,10k,C"] = self.c.get_current(i)
            self.c.turn_off(i+8)
            print(f"{self.prefix} --> HV turned off, waiting {float(self.json_data['hv_stability_wait'])} seconds to stabilize...")

            print(f"{self.prefix} --> Channel {i} HV results are {hv_results[i]}")

        self.r1.power("OFF", "hvpullup")
        print(f"{self.prefix} --> Test complete")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(f"Error: You need to supply a config file for this test as the argument! You had {len(sys.argv)-1} arguments!")
    #name = input("Input the name of this test\n")
    x = LDOmeasure(sys.argv[1], "test")
