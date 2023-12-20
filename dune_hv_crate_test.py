import pyvisa
import sys
import json
import os
import time
import openpyxl
from datetime import datetime
from keysight_daq970a import Keysight970A
from rigol_dp832a import RigolDP832A
from caen_r8033dm_wrapper import CAENR8033DM_WRAPPER

class LDOmeasure:
    def __init__(self, config_file, name = None):
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

        if (name):
            self.test_name = name
        else:
            self.test_name = input("Input the test name:\n")


        self.rounding_factor = int(self.json_data["rounding_factor"])
        self.datastore = {}
        self.datastore['input_params'] = self.json_data
        self.datastore['test_name'] = self.test_name
        self.start_time = datetime.now()
        self.datastore['start_time'] = self.start_time
        self.initialize_spreadsheet()
        self.sequence()

    def initialize_spreadsheet(self):
        if (self.json_data["relative"] == "True"):
            output_path = os.path.abspath(self.json_data["output_directory"])
        else:
            output_path = os.path.normpath(self.json_data["output_directory"])

        self.path_to_spreadsheet = os.path.join(output_path, f"{self.json_data['output_file']}")
        self.datastore['spreadsheet_path'] = self.path_to_spreadsheet

        json_date = datetime.today().strftime('%Y%m%d%H%M%S')
        os.makedirs(os.path.join(output_path, json_date))
        self.json_output_file = os.path.join(output_path, json_date, f"{json_date}_{self.test_name}.json")
        self.datastore['json_path'] = self.json_output_file

        if (os.path.isfile(self.path_to_spreadsheet)):
            self.wb = openpyxl.load_workbook(filename = self.path_to_spreadsheet)
            self.ws = self.wb.active
            self.row = self.ws.max_row + 1
        else:
            self.wb = openpyxl.Workbook()
            self.ws = self.wb.active
            self.ws.title = self.json_data["sheet_name"]

            top_style = openpyxl.styles.NamedStyle(name="top")
            top_style.font = openpyxl.styles.Font(bold=True, name='Calibri')
            bd = openpyxl.styles.Side(style='thin')
            top_style.border = openpyxl.styles.Border(left=bd, top=bd, right=bd, bottom=bd)
            self.wb.add_named_style(top_style)

            #Yes I'm using magic numbers, but I need to build the spreadsheet in a specific way, hopefully it's only done once
            self.ws.cell(row=2, column=1, value="Test Name").style = top_style
            self.ws.cell(row=2, column=2, value="Date").style = top_style
            self.ws.cell(row=2, column=3, value="Time").style = top_style
            self.ws.cell(row = 1, column = 4, value="Fan Test - V/I for power supplying all 4 fans, RD signal outputs").style = top_style
            self.ws.merge_cells(start_row=1, start_column=4, end_row=1, end_column=9)
            self.ws.cell(row=2, column=4, value="Supply Voltage").style = top_style
            self.ws.cell(row=2, column=5, value="Supply Current").style = top_style
            self.ws.cell(row=2, column=6, value="Fan 1 RD").style = top_style
            self.ws.cell(row=2, column=7, value="Fan 2 RD").style = top_style
            self.ws.cell(row=2, column=8, value="Fan 3 RD").style = top_style
            self.ws.cell(row=2, column=9, value="Fan 4 RD").style = top_style

            self.ws.cell(row=1, column=10, value="Heater Test").style = top_style
            self.ws.merge_cells(start_row=1, start_column=10, end_row=1, end_column=17)
            self.ws.cell(row=2, column=10, value="TC1_Resistance").style = top_style
            self.ws.cell(row=2, column=11, value="TC1_Temp_Rise").style = top_style
            self.ws.cell(row=2, column=12, value="TC2_Resistance").style = top_style
            self.ws.cell(row=2, column=13, value="TC2_Temp_Rise").style = top_style
            self.ws.cell(row=2, column=14, value="TC3_Resistance").style = top_style
            self.ws.cell(row=2, column=15, value="TC3_Temp_Rise").style = top_style
            self.ws.cell(row=2, column=16, value="TC4_Resistance").style = top_style
            self.ws.cell(row=2, column=17, value="TC4_Temp_Rise").style = top_style

            self.ws.cell(row=1, column=18, value="HV Test - Resistance for each configuration").style = top_style
            self.ws.merge_cells(start_row=1, start_column=12, end_row=1, end_column=21+(7*4))
            for i in range(8):
                self.ws.cell(row=2, column=18+(i*4), value=f"Ch{i}+ Open").style = top_style
                self.ws.cell(row=2, column=19+(i*4), value=f"Ch{i}+ 10k").style = top_style
                self.ws.cell(row=2, column=20+(i*4), value=f"Ch{i}- Open").style = top_style
                self.ws.cell(row=2, column=21+(i*4), value=f"Ch{i}- 10k").style = top_style

            column_letters = tuple(openpyxl.utils.get_column_letter(col_number + 1) for col_number in range(self.ws.max_column))
            for column_letter in column_letters:
                self.ws.column_dimensions[column_letter].bestFit = True
            self.ws.freeze_panes = self.ws.cell(row=3, column=2)
            self.wb.save(self.path_to_spreadsheet)
            self.row = 3

        self.ws.cell(row=self.row, column=1, value=self.test_name)
        self.ws.cell(row=self.row, column=2, value=datetime.today().strftime('%m/%d/%Y'))
        self.ws.cell(row=self.row, column=3, value=datetime.today().strftime('%I:%M:%S %p'))
        self.wb.save(self.path_to_spreadsheet)

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
        self.r1.power("OFF", "fanread")
        print(f"{self.prefix} --> Fans turned off")
        print(f"{self.prefix} --> Fan power supply was {fan_voltage}V and {fan_current}A")
        print(f"{self.prefix} --> Read signal for each fan was {fan_read_signal}")
        print(f"{self.prefix} --> Fan read pullup supply was {fanread_voltage}V and {fanread_current}A")

        self.ws.cell(row=self.row, column=4, value=fan_voltage)
        self.ws.cell(row=self.row, column=5, value=fan_current)
        self.ws.cell(row=self.row, column=6, value=round(fan_read_signal[1], self.rounding_factor))
        self.ws.cell(row=self.row, column=7, value=round(fan_read_signal[2], self.rounding_factor))
        self.ws.cell(row=self.row, column=8, value=round(fan_read_signal[3], self.rounding_factor))
        self.ws.cell(row=self.row, column=9, value=round(fan_read_signal[4], self.rounding_factor))

        self.datastore['fan_voltage'] = fan_voltage
        self.datastore['fan_current'] = fan_current
        self.datastore['fanread_voltage'] = fanread_voltage
        self.datastore['fanread_current'] = fanread_current
        self.datastore['fan_read_signal'] = fan_read_signal

        #Heater test
        #First measure resistance of heating element with no power connected
        self.k.initialize_resistance()
        heater_resistance = self.k.measure_resistance()
        print(f"{self.prefix} --> Heating element resistances are {fan_read_signal}")

        self.ws.cell(row=self.row, column=10, value=round(heater_resistance[1], self.rounding_factor))
        self.ws.cell(row=self.row, column=11, value=round(heater_resistance[2], self.rounding_factor))
        self.ws.cell(row=self.row, column=12, value=round(heater_resistance[3], self.rounding_factor))
        self.ws.cell(row=self.row, column=13, value=round(heater_resistance[4], self.rounding_factor))

        self.datastore['heater_resistance'] = heater_resistance

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
        temp_rise = []
        temp_rise.append(temp2[1] - temp1[1])
        temp_rise.append(temp2[2] - temp1[2])
        temp_rise.append(temp2[3] - temp1[3])
        temp_rise.append(temp2[4] - temp1[4])

        self.r0.power("OFF", "heat_supply")
        self.r0.power("OFF", "heat_switch")
        print(f"{self.prefix} --> Heat turned off")
        print(f"{self.prefix} --> Heat power supply was {supply_voltage}V and {supply_current}A")
        print(f"{self.prefix} --> Heat power switch was {switch_voltage}V and {switch_current}A")
        print(f"{self.prefix} --> Original temperatures were {temp1}")
        print(f"{self.prefix} --> Temperatures after {float(self.json_data['heat_wait'])} seconds were {temp2}, a rise of {temp_rise}")

        self.ws.cell(row=self.row, column=14, value=round(temp_rise[0], self.rounding_factor))
        self.ws.cell(row=self.row, column=15, value=round(temp_rise[1], self.rounding_factor))
        self.ws.cell(row=self.row, column=16, value=round(temp_rise[2], self.rounding_factor))
        self.ws.cell(row=self.row, column=17, value=round(temp_rise[3], self.rounding_factor))

        self.datastore['heater_supply_voltage'] = supply_voltage
        self.datastore['heater_supply_current'] = supply_current
        self.datastore['heater_switch_voltage'] = switch_voltage
        self.datastore['heater_switch_current'] = switch_current

        self.datastore['temp1'] = temp1
        self.datastore['temp2'] = temp2
        self.datastore['temp_rise'] = temp_rise

        #HV Leakage Test
        #Turn on HV
        hv_results = {}
        self.r1.power("ON", "hvpullup")
        for i in range(8):
            #Do the positive voltage with open termination
            self.k.set_relay(0 << i, 0)
            self.c.turn_on(i)
            print(f"{self.prefix} --> HV reached max value, waiting {float(self.json_data['hv_stability_wait'])} seconds to stabilize...")
            time.sleep(float(self.json_data['hv_stability_wait']))
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
            time.sleep(float(self.json_data['hv_stability_wait']))

            #Turn on negative voltage
            self.k.set_relay(1 << i, 0)
            self.c.turn_on(i+8)
            print(f"{self.prefix} --> HV reached max value, waiting {float(self.json_data['hv_stability_wait'])} seconds to stabilize...")
            time.sleep(float(self.json_data['hv_stability_wait']))
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
            time.sleep(float(self.json_data['hv_stability_wait']))

            print(f"{self.prefix} --> Channel {i} HV results are {hv_results[i]}")
            try:
                hv_results[i]["P,NT,R"] = float(hv_results[i]["P,NT,V"])/float(hv_results[i]["P,NT,C"])
            except ZeroDivisionError:
                hv_results[i]["P,NT,R"] = 0
            try:
                hv_results[i]["P,10k,R"] = float(hv_results[i]["P,10k,V"])/float(hv_results[i]["P,10k,C"])
            except ZeroDivisionError:
                hv_results[i]["P,10k,R"] = 0
            try:
                hv_results[i]["N,NT,R"] = float(hv_results[i]["N,NT,V"])/float(hv_results[i]["N,NT,C"])
            except ZeroDivisionError:
                hv_results[i]["N,NT,R"] = 0
            try:
                hv_results[i]["N,10k,R"] = float(hv_results[i]["N,NT,V"])/float(hv_results[i]["N,10k,C"])
            except ZeroDivisionError:
                hv_results[i]["N,10k,R"] = 0
            self.ws.cell(row=self.row, column=12+(i*4), value=round(float(hv_results[i]["P,NT,R"]), self.rounding_factor))
            self.ws.cell(row=self.row, column=13+(i*4), value=round(float(hv_results[i]["P,10k,R"]), self.rounding_factor))
            self.ws.cell(row=self.row, column=14+(i*4), value=round(float(hv_results[i]["N,NT,R"]), self.rounding_factor))
            self.ws.cell(row=self.row, column=15+(i*4), value=round(float(hv_results[i]["N,10k,R"]), self.rounding_factor))

            self.datastore[f'hv_ch{i}'] = {'pos_open_V' : hv_results[i]["P,NT,V"]}
            self.datastore[f'hv_ch{i}']['pos_open_V'] = hv_results[i]["P,NT,V"]
            self.datastore[f'hv_ch{i}']['pos_open_I'] = hv_results[i]["P,NT,C"]
            self.datastore[f'hv_ch{i}']['pos_open_R'] = hv_results[i]["P,NT,R"]
            self.datastore[f'hv_ch{i}']['pos_term_V'] = hv_results[i]["P,10k,V"]
            self.datastore[f'hv_ch{i}']['pos_term_I'] = hv_results[i]["P,10k,C"]
            self.datastore[f'hv_ch{i}']['pos_term_R'] = hv_results[i]["P,10k,R"]
            self.datastore[f'hv_ch{i}']['neg_open_V'] = hv_results[i]["N,NT,V"]
            self.datastore[f'hv_ch{i}']['neg_open_I'] = hv_results[i]["N,NT,C"]
            self.datastore[f'hv_ch{i}']['neg_open_R'] = hv_results[i]["N,NT,R"]
            self.datastore[f'hv_ch{i}']['neg_term_V'] = hv_results[i]["N,10k,V"]
            self.datastore[f'hv_ch{i}']['neg_term_I'] = hv_results[i]["N,10k,C"]
            self.datastore[f'hv_ch{i}']['neg_term_R'] = hv_results[i]["N,10k,R"]

        self.wb.save(self.path_to_spreadsheet)
        self.r1.power("OFF", "hvpullup")

        end_time = datetime.now()
        test_time = end_time - self.start_time
        self.datastore['end_time'] = end_time
        self.datastore['test_time'] = test_time

        with open(self.json_output_file, 'w', encoding='utf-8') as f:
            json.dump(self.datastore, f, ensure_ascii=False, indent=4, default=str)

        print(f"{self.prefix} --> Test complete")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(f"Error: You need to supply a config file for this test as the argument! You had {len(sys.argv)-1} arguments!")
    if (len(sys.argv) == 2):
        LDOmeasure(sys.argv[1])
    elif (len(sys.argv) == 3):
        LDOmeasure(sys.argv[1], sys.argv[2])
    else:
        sys.exit(f"Error: You need to supply a config file and optional test name for this program, 2 arguments max. You supplied {sys.argv}, which is {len(sys.argv)-1} arguments")
