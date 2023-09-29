import pyvisa
import sys
import json
from keysight_daq970a import Keysight970A
from rigol_dp832a import RigolDP832A

class LDOmeasure:
    def __init__(self, config_file, name):
        self.prefix = "DUNE HV Crate Tester"
        print(f"{self.prefix} --> Welcome to the DUNE FD2 LDO Measurement Script")
        with open(config_file, "r") as jsonfile:
            self.json_data = json.load(jsonfile)
        self.rm = pyvisa.ResourceManager('@py')

        k = Keysight970A(self.rm, self.json_data)
        k.initialize()

        r = RigolDP832A(self.rm, self.json_data)
        r.initialize()
        #resp.measure_temp()
        #self.name = name
        #self.begin_measurement()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(f"Error: You need to supply a config file for this test as the argument! You had {len(sys.argv)-1} arguments!")
    name = input("Input the name of this test\n")
    x = LDOmeasure(sys.argv[1], name)
