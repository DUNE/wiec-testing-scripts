import pyvisa
import sys
import json
import os
from keysight_daq970a import Keysight970A
from rigol_dp832a import RigolDP832A
from caen_r8033dm import CAENR8033DM

class LDOmeasure:
    def __init__(self, config_file, name):
        self.prefix = "DUNE HV Crate Tester"
        print(f"{self.prefix} --> Welcome to the DUNE HV crate production testing script")
        with open(config_file, "r") as jsonfile:
            self.json_data = json.load(jsonfile)
        self.rm = pyvisa.ResourceManager('@py')

        c = CAENR8033DM(self.json_data)
        sys.exit()

        k = Keysight970A(self.rm, self.json_data)
        k.set_relay(24, 69)
        k.initialize_resistance()
        print(k.measure_resistance())
        k.initialize_fan()
        print(k.measure_fan())
        k.initialize_fan()
        print(k.initialize_rtd())
        k.heaters_on()

        r = RigolDP832A(self.rm, self.json_data)
        r.initialize()


        r.get_current("fan")
        print(r.get_voltage("fan"))
        print(r.check_overcurr_protection("fan"))

        self.name = name
        self.begin_measurement()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(f"Error: You need to supply a config file for this test as the argument! You had {len(sys.argv)-1} arguments!")
    #name = input("Input the name of this test\n")
    x = LDOmeasure(sys.argv[1], "test")
