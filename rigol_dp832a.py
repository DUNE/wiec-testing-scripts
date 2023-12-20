# -*- coding: utf-8 -*-
"""
Created on Wed Sept 25 10:51:58 2023

@author: Eraguzin
"""

class RigolDP832A:
    def __init__(self, rm, json_data, index):
        self.prefix = "Rigol DP832A"
        self.json_data = json_data
        self.rigol = rm.open_resource(self.json_data[f'rigol832a{index}'])
        print(f"{self.prefix} --> Connected to {self.rigol.query('*IDN?')}")
        self.rigol.write("*RST")
        self.channels = []
        self.index = index
        self.channel_num = 3

    def setup_fan(self):
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_fan_ch']) - (self.channel_num * self.index)}:VOLTage:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_fan_voltage']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_fan_ch']) - (self.channel_num * self.index)}:CURRent:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_fan_current']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_fan_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:LEVel {self.json_data['rigol832a_fan_overcurrent']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_fan_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:STATe {self.json_data['rigol832a_fan_overcurrent_en']}")
        self.channels.append("fan")

    def setup_heater_supply(self):
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_heater_supply_ch']) - (self.channel_num * self.index)}:VOLTage:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_heater_supply_voltage']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_heater_supply_ch']) - (self.channel_num * self.index)}:CURRent:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_heater_supply_current']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_heater_supply_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:LEVel {self.json_data['rigol832a_heater_supply_overcurrent']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_heater_supply_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:STATe {self.json_data['rigol832a_heater_supply_overcurrent_en']}")
        self.channels.append("heat_supply")

    def setup_heater_switch(self):
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_heater_switch_ch']) - (self.channel_num * self.index)}:VOLTage:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_heater_switch_voltage']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_heater_switch_ch']) - (self.channel_num * self.index)}:CURRent:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_heater_switch_current']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_heater_switch_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:LEVel {self.json_data['rigol832a_heater_switch_overcurrent']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_heater_switch_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:STATe {self.json_data['rigol832a_heater_switch_overcurrent_en']}")
        self.channels.append("heat_switch")

    def setup_hvpullup(self):
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_hvpullup_ch']) - (self.channel_num * self.index)}:VOLTage:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_hvpullup_voltage']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_hvpullup_ch']) - (self.channel_num * self.index)}:CURRent:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_hvpullup_current']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_hvpullup_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:LEVel {self.json_data['rigol832a_hvpullup_overcurrent']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_hvpullup_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:STATe {self.json_data['rigol832a_hvpullup_overcurrent_en']}")
        self.channels.append("hvpullup")

    def setup_fanread(self):
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_fanread_ch']) - (self.channel_num * self.index)}:VOLTage:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_fanread_voltage']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_fanread_ch']) - (self.channel_num * self.index)}:CURRent:LEVel:IMMediate:AMPLitude {self.json_data['rigol832a_fanread_current']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_fanread_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:LEVel {self.json_data['rigol832a_fanread_overcurrent']}")
        self.rigol.write(f"SOURce{int(self.json_data['rigol832a_fanread_ch']) - (self.channel_num * self.index)}:CURRent:PROTection:STATe {self.json_data['rigol832a_fanread_overcurrent_en']}")
        self.channels.append("fanread")

    #Because I want to decouple the name of the channel with the actual number, this will need to be called almost every time
    def get_ch_with_name(self, ch):
        if (ch == "fan" and "fan" in self.channels):
            return int(self.json_data['rigol832a_fan_ch']) - (self.channel_num * self.index)
        elif (ch == "heat_supply" and "heat_supply" in self.channels):
            return int(self.json_data['rigol832a_heater_supply_ch']) - (self.channel_num * self.index)
        elif (ch == "heat_switch" and "heat_switch" in self.channels):
            return int(self.json_data['rigol832a_heater_switch_ch']) - (self.channel_num * self.index)
        elif (ch == "hvpullup" and "hvpullup" in self.channels):
            return int(self.json_data['rigol832a_hvpullup_ch']) - (self.channel_num * self.index)
        elif (ch == "fanread" and "fanread" in self.channels):
            return int(self.json_data['rigol832a_fanread_ch']) - (self.channel_num * self.index)
        else:
            print(f"{self.prefix} --> WARNING: Did not understand channel type {ch}")
            print(f"{self.prefix} --> WARNING: Channels initialized for Rigol {self.index} are {self.channels}")
            return 0

    def power(self, onoff, ch):
        if (onoff == "ON" or onoff == "OFF"):
            chan = self.get_ch_with_name(ch)
            if (chan != 0):
                self.rigol.write(f"OUTPut:STATe CH{chan},{onoff}")
                print(f"{self.prefix} --> Turned {onoff} Power Supply {self.index+1}, {ch}- Channel {chan}")
        else:
            print(f"{self.prefix} --> WARNING: Did not understand on/off choise {onoff}")

    def get_current(self, ch):
        chan = self.get_ch_with_name(ch)
        if (chan != 0):
            curr = self.rigol.query(f"MEASure:CURRent:DC? CH{chan}")
            return float(curr)

    def get_voltage(self, ch):
        chan = self.get_ch_with_name(ch)
        if (chan != 0):
            volt = self.rigol.query(f"MEASure:VOLTage:DC? CH{chan}")
            return float(volt)

    def check_overcurr_protection(self, ch):
        chan = self.get_ch_with_name(ch)
        if (chan != 0):
            status = self.rigol.query(f"SOURce{chan}:CURRent:PROTection:TRIPped?")
            return status
