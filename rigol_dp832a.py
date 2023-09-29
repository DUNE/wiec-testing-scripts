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

    def initialize(self):
        self.rigol.write(f"SOURce1:VOLTage:LEVel:IMMediate:AMPLitude 4.20")
