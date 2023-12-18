
from caen_r8033dm import CAENR8033DM
import sys

class CAENR8033DM_WRAPPER:
    def __init__(self, json_data):
        self.prefix = "CAEN R8033DM"    #Prefix for log messages
        self.caen = CAENR8033DM(json_data)
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


    def turn_on(self, ch):
        print("here")

    def turn_off(self, ch):
        print("here")

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
            if (not all(i == value for i in resp)):
                sys.exit(f"{self.prefix} --> Wrote {value} to {param}, read back {resp} list")
        elif (isinstance(ch, list) and isinstance(value, list)):
            for num,i in enumerate(value):
                if (round(resp[num],2) != i):
                    sys.exit(f"{self.prefix} --> Wrote {value} to {param}, read back {resp} list")
        elif (round(resp,2) != value):
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
