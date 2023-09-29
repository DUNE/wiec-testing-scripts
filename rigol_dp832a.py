# -*- coding: utf-8 -*-
"""
Created on Wed Sept 25 10:51:58 2023

@author: Eraguzin
"""

class RigolDP832A:
    def __init__(self, rm, json_data):
        self.prefix = "Rigol DP832A"
        self.json_data = json_data
        self.rigol = rm.open_resource(self.json_data['rigol832a'])
        print(f"{self.prefix} --> Connected to {self.rigol.query('*IDN?')}")
        self.rigol.write("*RST")

    #Because I want to decouple the name of the channel with the actual number, this will need to be called almost every time
    def get_ch_with_name(self, ch):
        if (ch == "fan"):
            chan = self.json_data['rigol832a_fan_ch']

        else:
            print(f"{self.prefix} --> WARNING: Did not understand channel type {ch}")
            return 0

    def initialize(self):
        #Setup the fan channel
        self.rigol.write(f"SOURce{self.json_data['rigol832a_fan_ch']}:VOLTage:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_fan_voltage']}")
        self.rigol.write(f"SOURce{self.json_data['rigol832a_fan_ch']}:CURRent:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_fan_current']}")
        self.rigol.write(f"SOURce{self.json_data['rigol832a_fan_ch']}:CURRent:PROTection:LEVel {self.json_data['rigol832a_fan_overcurrent']}")
        self.rigol.write(f"SOURce{self.json_data['rigol832a_fan_ch']}:CURRent:PROTection:STATe {self.json_data['rigol832a_fan_overcurrent_en']}")

    def power(self, onoff, ch):
        if (onoff == "ON" or onoff == "OFF"):
            chan = self.get_ch_with_name(ch)
            if (chan != 0):
                self.rigol.write(f"OUTPut:STATe CH{chan},{onoff}")
                print(f"{self.prefix} --> Turned {onoff} {ch}- Channel {chan}")
        else:
            print(f"{self.prefix} --> WARNING: Did not understand on/off choise {onoff}")

    def get_current(self, ch):
        chan = self.get_ch_with_name(ch)
        if (chan != 0):
            curr = self.rigol.query(f"SOURce{chan}:CURRent:LEVel:IMMediate:AMPLitude?")
            return float(curr)

    def get_voltage(self, ch):
        chan = self.get_ch_with_name(ch)
        if (chan != 0):
            volt = self.rigol.query(f"SOURce{chan}:VOLTage:LEVel:IMMediate:AMPLitude?")
            return float(volt)

    def check_overcurr_protection(self, ch):
        chan = self.get_ch_with_name(ch)
        if (chan != 0):
            status = self.rigol.query(f"SOURce{chan}:CURRent:PROTection:TRIPped?")
            return status
