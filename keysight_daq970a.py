# -*- coding: utf-8 -*-
"""
Created on Wed Sept 25 10:51:58 2023

@author: Eraguzin
"""

class Keysight970A:
    def __init__(self, rm, json_data):
        self.json_data = json_data
        self.keysight = rm.open_resource(self.json_data['keysight970a'])
        print(f"keysight DAQ 970A --> Connected to {self.keysight.query('*IDN?')}")
        self.keysight.write("*RST")

    def initialize(self):
        #Build the string of the list of RTD channels
        rtd_ch_list = ""
        rtd_slot = self.json_data['keysight970a_901A_slot']
        for i in range(1,5,1):
            ch_num = int(self.json_data[f'keysight970a_rtd_ch{i}'])
            ch_string = f"{rtd_slot}{ch_num:02d}"
            if (i == 1):
                rtd_ch_list += (f"@{ch_string}")
            else:
                rtd_ch_list += (f",{ch_string}")

        #Keysight DAQ970A requires you to do a Configure first and then change the parameters with Sense
        #Configure sets the resistance of the RTD, and default resolution
        self.keysight.write(f"CONFigure:TEMPerature:FRTD {self.json_data['keysight970a_rtd_RES']},DEF,({rtd_ch_list})")

        #Sets the sample rate a little slower for accuracy, whether in low power mode or not, and units to use
        self.keysight.write(f"SENSe1:TEMPerature:NPLCycles {self.json_data['keysight970a_rtd_NPLcycles']},({rtd_ch_list})")
        self.keysight.write(f"SENSe1:TEMPerature:TRANsducer:FRTD:POWer:LIMit:STATe {self.json_data['keysight970a_rtd_LowPower']},({rtd_ch_list})")
        self.keysight.write(f"UNIT:TEMPerature {self.json_data['keysight970a_rtd_units']},({rtd_ch_list})")
        self.keysight.write("FORMat:READing:CHANnel ON")
        #self.keysight.write("FORMat:READing:UNIT ON")
        #print(self.keysight.query("ROUTe:SCAN?"))
        #self.keysight.write("ROUTe:SCAN (@)")
        #self.keysight.write("ROUTe:CLOSe (@105,107)")

    def measure_temp(self):
        #Response is something like
        #['+9.90000000E+2', '101', '+9.90000000E+2', '102', '+9.90000000E+1', '103', '+9.90000000E+0', '104\n']
        #Get rid of /n at the end of the string
        resp = self.keysight.query("READ?", delay = 1).strip()
        #Split commas into lists
        sep = resp.split(",")
        #Make a dictionary with the channel as the key and the float reading as value
        results = {}
        for i in range(0,7,2):
            results[sep[i+1]] = float(sep[i])

        return results
