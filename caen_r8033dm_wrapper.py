
from caen_r8033dm import CAENR8033DM
import sys
import time

class CAENR8033DM_WRAPPER:
    def __init__(self, json_data):
        self.prefix = "CAEN R8033DM"    #Prefix for log messages
        self.caen = CAENR8033DM(json_data)
        self.rounding_factor = 2
        self.ramp_wait = 1
        if (self.caen.caen.value == -1):
            sys.exit(f"{self.prefix} --> Device could not be intialized, returned {self.caen.caen.value}")

        #Doesn't seem to work
        # if (self.get_board_control() == self.caen.board_params['BdCtr']['Onstate']):
        #     sys.exit(f"{self.prefix} --> Board control is in Local mode, not Remote!")

        if (self.get_board_interlock() == self.caen.board_params['BdIlk']['Onstate']):
            sys.exit(f"{self.prefix} --> Board interlock has tripped!")

        if (self.get_board_status() != 0):
            sys.exit(f"{self.prefix} --> Board failed with error {hex(self.get_board_status())}")

        # print(self.get_channel_status(3))
        # print(self.get_channel_status([3,4,5,6, 7]))
        #
        # self.set_powerdown([4, 5], 1)
        # self.set_HV_value([4, 5], 69.42)
        # self.set_overcurrent(5, 34.35)
        # self.set_current_range(1, 0)
        # self.set_current_range(1, 1)
        # self.set_trip_time([4,5,6], [7.7,8.8,9])
        # self.set_rampdown(3, 57)
        # self.set_rampup([3,4,5], 45)
        # self.set_powerdown([3,4], [0,1])

        self.set_HV_value(2, 500)
        self.set_rampup(2, 50)
        self.set_rampdown(2, 50)
        self.turn_on(2)
        self.turn_off(2)
        #self.turn_on(2)


    def turn_on(self, ch):
        status = self.get_channel_status(ch)
        if (not isinstance(ch, list)):
            if (status > 0x7):
                self.channel_error(i, status[num])
            self.caen.set_ch_parameter(ch, "Pw", 1)
            self.get_check_channel_parameter(ch, "Pw", 1)
            time.sleep(self.ramp_wait)                                      #Need the device to update, sometimes it says it's completed before it starts
            if (self.get_channel_status(ch) != 1):
                self.wait_for_ramp(ch, True)
        else:
            for num,i in enumerate(ch):
                if (status[num] > 0x7):
                    self.channel_error(i, status[num])
                self.caen.set_ch_parameter(ch, "Pw", 1)
                self.get_check_channel_parameter(ch, "Pw", 1)
                time.sleep(self.ramp_wait)
                for i in ch:
                    if (self.get_channel_status(i) != 1):
                        self.wait_for_ramp(ch, True)

    def turn_off(self, ch):
        status = self.get_channel_status(ch)
        if (not isinstance(ch, list)):
            if (status > 0x7):
                self.channel_error(i, status[num])
            self.caen.set_ch_parameter(ch, "Pw", 0)
            self.get_check_channel_parameter(ch, "Pw", 0)
            time.sleep(self.ramp_wait)
            if (self.get_channel_status(ch) != 0):
                self.wait_for_ramp(ch, False)
        else:
            for num,i in enumerate(ch):
                if (status[num] > 0x7):
                    self.channel_error(i, status[num])
                self.caen.set_ch_parameter(ch, "Pw", 0)
                self.get_check_channel_parameter(ch, "Pw", 0)
                time.sleep(self.ramp_wait)
                for i in ch:
                    if (self.get_channel_status(i) != 0):
                        self.wait_for_ramp(ch, False)

    def wait_for_ramp(self, ch, going_up):
        done = False
        while(not done):
            #print(self.get_channel_status(ch))
            #print(self.caen.get_channel_parameter_value(ch, "Pw"))
            if (going_up):
                if (self.get_channel_status(ch) == 1):
                    break
                print(f"{self.prefix} --> Channel {ch} is ramping up to {self.get_HV_value(ch)}, currently at {self.get_voltage(ch)}")
            else:
                if (self.get_channel_status(ch) == 0):
                    break
                print(f"{self.prefix} --> Channel {ch} is ramping down to turn off, currently at {self.get_voltage(ch)}")
            time.sleep(self.ramp_wait)
            if (self.get_channel_status(ch) > 0x7):
                self.channel_error(i, self.get_channel_status(ch))


    def get_voltage(self, ch):
        return self.caen.get_channel_parameter_value(ch, "VMon")

    def set_HV_value(self, ch, voltage):
        self.caen.set_ch_parameter(ch, "VSet", voltage)
        return self.get_check_channel_parameter(ch, "VSet", voltage)

    def get_HV_value(self, ch):
        return self.caen.get_channel_parameter_value(ch, "VSet")

    def set_overcurrent(self, ch, current):
        self.caen.set_ch_parameter(ch, "ISet", current)
        return self.get_check_channel_parameter(ch, "ISet", current)

    def get_overcurrent(self, ch, current):
        return self.caen.get_channel_parameter_value(ch, "ISet")

    def get_current(self, ch):
        return self.caen.get_channel_parameter_value(ch, "IMon")

    def set_current_range(self, ch, value):
        self.caen.set_ch_parameter(ch, "IMRange", value)
        return self.get_check_channel_parameter(ch, "IMRange", value)

    def get_current_range(self, ch):
        return self.caen.get_channel_parameter_value(ch, "IMRange")

    def set_trip_time(self, ch, value):
        self.caen.set_ch_parameter(ch, "Trip", value)
        return self.get_check_channel_parameter(ch, "Trip", value)

    def get_trip_time(self, ch):
        return self.caen.get_channel_parameter_value(ch, "Trip")

    def set_rampdown(self, ch, value):
        self.caen.set_ch_parameter(ch, "RDwn", value)
        return self.get_check_channel_parameter(ch, "RDwn", value)

    def get_rampdown(self, ch):
        return self.caen.get_channel_parameter_value(ch, "RDwn")

    def set_rampup(self, ch, value):
        self.caen.set_ch_parameter(ch, "RUp", value)
        return self.get_check_channel_parameter(ch, "RUp", value)

    def get_rampup(self, ch):
        return self.caen.get_channel_parameter_value(ch, "RUp")

    def set_powerdown(self, ch, value):
        self.caen.set_ch_parameter(ch, "PDwn", value)
        return self.get_check_channel_parameter(ch, "PDwn", value)

    def get_powerdown(self, ch):
        return self.caen.get_channel_parameter_value(ch, "PDwn")

    def get_channel_status(self, ch):
        return self.caen.get_channel_parameter_value(ch, "Status")

    def get_check_channel_parameter(self, ch, param, value):
        resp = self.caen.get_channel_parameter_value(ch, param)
        if (isinstance(ch, list) and not isinstance(value, list)):
            for num in range(len(ch)):
                if (round(resp[num],self.rounding_factor) != value):
                    print(f"{self.prefix} --> {self.get_channel_status(ch[num])}")
                    sys.exit(f"{self.prefix} --> Wrote {value} to {param}, read back {resp} list")
        elif (isinstance(ch, list) and isinstance(value, list)):
            for num,i in enumerate(value):
                if (round(resp[num],self.rounding_factor) != i):
                    print(f"{self.prefix} --> {self.get_channel_status(ch[num])}")
                    sys.exit(f"{self.prefix} --> Wrote {value} to {param}, read back {resp} list")
        elif (round(resp,self.rounding_factor) != value):
            print(f"{self.prefix} --> {self.get_channel_status(ch)}")
            sys.exit(f"{self.prefix} --> Wrote {value} to {param}, read back {resp}")
        return resp

    def get_board_status(self):
        return self.caen.get_board_parameter_value("BdStatus")

    def get_board_interlock(self):
        if (self.caen.get_board_parameter_value("BdIlk")):
            return self.caen.board_params['BdIlk']['Onstate']
        else:
            return self.caen.board_params['BdIlk']['Offstate']

    #Always seems to return Local, even when it's Remote
    def get_board_control(self):
        ret = self.caen.get_board_parameter_value("BdCtr")
        #print(ret)
        if (ret):
            return self.caen.board_params['BdCtr']['Onstate']
        else:
            return self.caen.board_params['BdCtr']['Offstate']

    def channel_error(self, ch, val):
        if (val > 0x7):
            print(f"{self.prefix} --> Error code {hex(val)}")
            if (val & 0x8):
                sys.exit(f"{self.prefix} --> Channel {ch} is overcurrent")
            elif (val & 0x10):
                sys.exit(f"{self.prefix} --> Channel {ch} is overvoltage")
            elif (val & 0x20):
                sys.exit(f"{self.prefix} --> Channel {ch} is undervoltage")
            elif (val & 0x40):
                sys.exit(f"{self.prefix} --> Channel {ch} has tripped due to overcurrent")
            elif (val & 0x80):
                sys.exit(f"{self.prefix} --> Channel {ch} is overpowered")
            elif (val & 0x100):
                sys.exit(f"{self.prefix} --> Channel {ch} has a temperature warning")
            elif (val & 0x200):
                sys.exit(f"{self.prefix} --> Channel {ch} is over temperature")
            elif (val & 0x400):
                sys.exit(f"{self.prefix} --> Channel {ch}'s switch is in the kill state")
            elif (val & 0x800):
                sys.exit(f"{self.prefix} --> Channel {ch}'s interlock is tripped")
            elif (val & 0x1000):
                sys.exit(f"{self.prefix} --> Channel {ch}'s switch is in the off state")
            elif (val & 0x2000):
                sys.exit(f"{self.prefix} --> Channel {ch} has a general failure")
            elif (val & 0x4000):
                sys.exit(f"{self.prefix} --> Channel {ch}'s switch is on but in local mode")
            elif (val & 0x20):
                sys.exit(f"{self.prefix} --> Channel {ch}'s voltage exceeds the hardware max")
