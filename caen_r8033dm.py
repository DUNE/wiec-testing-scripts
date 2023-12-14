# -*- coding: utf-8 -*-
"""
Created on Wed Sept 25 10:51:58 2023

@author: Eraguzin
https://www.caen.it/?downloadfile=5208
https://www.caen.it/products/caen-hv-wrapper-library/

CAENHV_GetSysPropList returns 0 system properties and a null pointer
"""
import sys
import os
import pprint
from enum import IntEnum
from ctypes import c_int, c_float, c_void_p, c_char_p, c_char, c_ushort, pointer, cdll, cast, POINTER, byref, sizeof, c_ulong, c_uint32, c_long, c_short

class CAENR8033DM:
    def __init__(self, json_data):
        self.prefix = "CAEN R8033DM"
        self.model_id = 13              #13 is the value for teh 803X series
        self.comm_protocol = 0          #0 is the value for TCP/IP
        self.slot = 0                   #R8033DM only has one logical slot
        self.board_param_size = 10      #Empirically found that parameter names have max size of 10 characters, needed for pointer casting
        self.board_params = {}
        self.ch_params = {}
        self.json_data = json_data

        try:
            dllpath = os.path.join(os.getcwd(), self.json_data['caenR8033DM_driver'])
            self.libcaenhvwrapper = cdll.LoadLibrary(dllpath)  # Load CAEN's c-api shared library
        except Exception as e:
            print(e)
            sys.exit(f"{self.prefix} --> Could not load CAEN's C library at {dllpath}")

        print(f"{self.prefix} --> CAEN's C library opened at {dllpath}")

        #Integer handler for the connection
        self.caen = c_int()
        return_code = self.libcaenhvwrapper.CAENHV_InitSystem(c_int(self.model_id),
                                                              c_int(self.comm_protocol),
                                                              self.json_data['caenR8033DM'].encode('utf-8'),    #IP address for TCP/IP
                                                              "".encode('utf-8'),                               #Username, unused
                                                              "".encode('utf-8'),                               #Password, unused
                                                              pointer(self.caen))                               #Pointer to returned handle

        self.check_return(return_code, "Initialization Failed")

        self.get_crate_info()
        #self.get_sys_info()
        self.get_board_info()
        self.get_channel_info()

    def get_crate_info(self):
        c_num_of_slots = c_ushort()
        c_num_of_channels = POINTER(c_ushort)()
        c_description_list = c_char_p()
        c_model_list = c_char_p()
        c_serial_num_list = POINTER(c_ushort)()
        c_firmware_release_min_list = c_char_p()
        c_firmware_releae_max_list = c_char_p()
        return_code = self.libcaenhvwrapper.CAENHV_GetCrateMap(self.caen,
                                                            byref(c_num_of_slots),
                                                            byref(c_num_of_channels),
                                                            byref(c_model_list),
                                                            byref(c_description_list),
                                                            byref(c_serial_num_list),
                                                            byref(c_firmware_release_min_list),
                                                            byref(c_firmware_releae_max_list))
        self.check_return(return_code, "Failed to get crate map")
        print(f"{self.prefix} --> Connected to Caen {c_model_list.value.decode('utf-8')}, serial number {c_serial_num_list.contents.value} with {c_num_of_slots.value} slots and {c_num_of_channels.contents.value} channels detected")
        self.channel_list = c_num_of_channels.contents

    def get_channel_info(self):
        c_par_num = c_ushort()
        c_par_list = c_char_p()
        return_code = self.libcaenhvwrapper.CAENHV_GetChParamInfo(self.caen,
                                                            c_ushort(self.slot),
                                                            c_ushort(0),            #Default to channel 0 since they're all the same
                                                            byref(c_par_list),
                                                            byref(c_par_num))

        self.check_return(return_code, f"Failed to get channel info")

        #See comments in board info function for what happens here
        par_array = cast(c_par_list, (POINTER(c_char * self.board_param_size)))
        i = 0
        ch_params = []
        while (True):
            result = par_array[i].value.decode('utf-8')
            if (result.isalnum()):
                ch_params.append(result)
                i += 1
            else:
                break
        for ch in range(16):
            for i in ch_params:
                self.get_channel_property_info(ch, i)
                self.get_channel_parameter_value(ch, i)
        print("Channel properties are:")
        pprint.pprint(self.ch_params, width = 1)

    def get_channel_property_info(self, ch, param):
        c_prop_val = c_ulong()
        return_code = self.libcaenhvwrapper.CAENHV_GetChParamProp(self.caen,
                                                            c_ushort(self.slot),
                                                            c_ushort(ch),
                                                            param.encode('utf-8'),
                                                            "Type".encode('utf-8'),
                                                            byref(c_prop_val))

        self.check_return(return_code, f"Failed to get channel parameter {param} type")
        if (ch not in self.ch_params):
            self.ch_params[ch] = {param: {"Type" : self.PropertyType(c_prop_val.value).name}}
        else:
            self.ch_params[ch].update({param: {"Type" : self.PropertyType(c_prop_val.value).name}})
        #self.ch_params[ch][param] = {"Type" : self.PropertyType(c_prop_val.value).name}
        #self.ch_params[ch] = temp

        return_code = self.libcaenhvwrapper.CAENHV_GetChParamProp(self.caen,
                                                            c_ushort(self.slot),
                                                            c_ushort(ch),
                                                            param.encode('utf-8'),
                                                            "Mode".encode('utf-8'),
                                                            byref(c_prop_val))

        self.check_return(return_code, f"Failed to get channel parameter {param} mode")
        self.ch_params[ch][param]["Mode"] = self.PropertyMode(c_prop_val.value).name

        if (self.ch_params[ch][param]['Type'] == self.PropertyType.PARAM_TYPE_FLOAT.name):
            c_prop_val = c_float()
            return_code = self.libcaenhvwrapper.CAENHV_GetChParamProp(self.caen,
                                                                c_ushort(self.slot),
                                                                c_ushort(ch),
                                                                param.encode('utf-8'),
                                                                "Minval".encode('utf-8'),
                                                                byref(c_prop_val))
            self.check_return(return_code, f"Failed to get channel parameter {param} Minval")
            self.ch_params[ch][param]["Minval"] = c_prop_val.value

            return_code = self.libcaenhvwrapper.CAENHV_GetChParamProp(self.caen,
                                                                c_ushort(self.slot),
                                                                c_ushort(ch),
                                                                param.encode('utf-8'),
                                                                "Maxval".encode('utf-8'),
                                                                byref(c_prop_val))
            self.check_return(return_code, f"Failed to get channel parameter {param} Maxval")
            self.ch_params[ch][param]["Maxval"] = c_prop_val.value

            c_prop_val = c_ushort()
            return_code = self.libcaenhvwrapper.CAENHV_GetChParamProp(self.caen,
                                                                c_ushort(self.slot),
                                                                c_ushort(ch),
                                                                param.encode('utf-8'),
                                                                "Unit".encode('utf-8'),
                                                                byref(c_prop_val))
            self.check_return(return_code, f"Failed to get channel parameter {param} Unit")
            self.ch_params[ch][param]["Unit"] = c_prop_val.value

            c_prop_val = c_short()
            return_code = self.libcaenhvwrapper.CAENHV_GetChParamProp(self.caen,
                                                                c_ushort(self.slot),
                                                                c_ushort(ch),
                                                                param.encode('utf-8'),
                                                                "Exp".encode('utf-8'),
                                                                byref(c_prop_val))
            self.check_return(return_code, f"Failed to get channel parameter {param} Exp")
            self.ch_params[ch][param]["Exp"] = c_prop_val.value

    def get_channel_parameter_value(self, ch, param):
        if param not in self.ch_params[ch]:
            sys.exit(f"Tried to access parameter{param} which wasn't in the channel parameter list. Channel {ch} parameter list is {self.ch_params[ch]}")
        if (('Type' not in self.ch_params[ch][param]) or ('Mode' not in self.ch_params[ch][param])):
            sys.exit(f"Tried to access parameter{param} which didn't have Type and Mode set up in the channel parameter list. Channel {ch} parameter list is {self.ch_params[ch]}")
        if (self.ch_params[ch][param]['Mode'] == self.PropertyMode.PARAM_MODE_WRONLY):
            sys.exit(f"Trying to read a parameter that is read only. Channel {ch} parameter list is {self.ch_params[ch]}")

        if (self.ch_params[ch][param]['Type'] == self.PropertyType.PARAM_TYPE_FLOAT.name):
            c_param_val = c_float()
        else:
            c_param_val = c_long()



        return_code = self.libcaenhvwrapper.CAENHV_GetChParam(self.caen,
                                                            c_ushort(self.slot),
                                                            param.encode('utf-8'),
                                                            c_ushort(1),                #Number of channels you want to read
                                                            byref(c_ushort(ch)),        #Which channels you want to read
                                                            byref(c_param_val))

        if (self.check_return(return_code, f"Retrieving value for channel {ch}, parameter {param} failed") == 0):
            self.ch_params[ch][param]["Value"] = c_param_val.value
        else:
            self.ch_params[ch][param]["Value"] = "Error"

    def get_sys_info(self):
        print("system info")
        c_prop_num = c_ushort()
        c_prop_list = c_char_p()
        return_code = self.libcaenhvwrapper.CAENHV_GetSysPropList(self.caen,
                                                            byref(c_prop_num),
                                                            byref(c_prop_list))

        self.check_return(return_code, f"Failed to get system info")
        print(c_prop_num.value)
        par_array = cast(c_prop_list, (POINTER(c_char * 300)))
        for i in range(300):
            print(par_array.contents[i])

    def get_board_info(self):
        c_slot_num = c_ushort(self.slot)
        c_bd_param_list = c_char_p()
        #Function takes in a **char type as the parameter list. It will write back an array of char arrays
        return_code = self.libcaenhvwrapper.CAENHV_GetBdParamInfo(self.caen,
                                                            c_slot_num,
                                                            byref(c_bd_param_list))

        self.check_return(return_code, "Failed to get board parameters")

        #Cast as a pointer to 10 char arrays. The type is
        #<class 'caen_r8033dm.LP_c_char_Array_10'>
        #You need to just "know" that each parameter fills 10 chars, either with terminating null characters or gibberish
        #I confirmed by reading out the full memory block, and also through the example C script

        par_array = cast(c_bd_param_list, (POINTER(c_char * self.board_param_size)))

        #If you run par_array.contents, the type is <class 'caen_r8033dm.c_char_Array_10'> and the size is 10
        #But printing it just gives <caen_r8033dm.c_char_Array_10 object at 0x7ff81f8cfe30>
        #And you need to do par_array.contents[0], par_array.contents[1], par_array.contents[2], etc... to get the
        #parameter letter by letter - b'B', b'd', b'I', b'l', b'k', etc...
        #And par_array.contents.value will only give you the first value, as if there was only one char array the pointer pointed to
        #By indexing it as par_array[0] and par_array[1], then par_array[0].contents doesn't exist
        #But type(par_array[0]) is <class 'caen_r8033dm.c_char_Array_10'> and type(par_array[0].value) is <class 'bytes'>
        #So par_array[0].value is b'BdIlk', par_array[1] is b'BdIlkm', par_array[2] is b'BdCtr', etc...
        #These can be decoded through utf-8 or left as is to be passed back to other functions

        i = 0
        board_params = []

        #It's hard to know how many parameters there will be. Even in Caen's example code, they just loop until the pointer to char array is not valid
        #In this Ctypes way, we can go until the resulting 10 char array is either empty '' which happens. Or it's not alphanumeric characters
        #So it's gibberish like \a0\n4 and stuff like that
        while (True):
            result = par_array[i].value.decode('utf-8')
            if (result.isalnum()):
                board_params.append(result)
                i += 1
            else:
                break

        for i in board_params:
            self.get_board_property_info(i)
            self.get_board_parameter_value(i)

        print("Board level properties are:")
        pprint.pprint(self.board_params, width = 1)

    def get_board_property_info(self, param):
        c_prop_val = c_ulong()
        return_code = self.libcaenhvwrapper.CAENHV_GetBdParamProp(self.caen,
                                                            c_ushort(self.slot),
                                                            param.encode('utf-8'),
                                                            "Type".encode('utf-8'),
                                                            byref(c_prop_val))

        self.check_return(return_code, f"Failed to get board parameter {param} type")
        self.board_params[param] = {"Type" : self.PropertyType(c_prop_val.value).name}

        return_code = self.libcaenhvwrapper.CAENHV_GetBdParamProp(self.caen,
                                                            c_ushort(self.slot),
                                                            param.encode('utf-8'),
                                                            "Mode".encode('utf-8'),
                                                            byref(c_prop_val))

        self.check_return(return_code, f"Failed to get board parameter {param} mode")
        self.board_params[param]["Mode"] = self.PropertyMode(c_prop_val.value).name

        if (self.board_params[param]['Type'] == self.PropertyType.PARAM_TYPE_FLOAT.name):
            c_prop_val = c_float()
            return_code = self.libcaenhvwrapper.CAENHV_GetBdParamProp(self.caen,
                                                                c_ushort(self.slot),
                                                                param.encode('utf-8'),
                                                                "Minval".encode('utf-8'),
                                                                byref(c_prop_val))
            self.check_return(return_code, f"Failed to get board parameter {param} Minval")
            self.board_params[param]["Minval"] = c_prop_val.value

            return_code = self.libcaenhvwrapper.CAENHV_GetBdParamProp(self.caen,
                                                                c_ushort(self.slot),
                                                                param.encode('utf-8'),
                                                                "Maxval".encode('utf-8'),
                                                                byref(c_prop_val))
            self.check_return(return_code, f"Failed to get board parameter {param} Maxval")
            self.board_params[param]["Maxval"] = c_prop_val.value

            c_prop_val = c_ushort()
            return_code = self.libcaenhvwrapper.CAENHV_GetBdParamProp(self.caen,
                                                                c_ushort(self.slot),
                                                                param.encode('utf-8'),
                                                                "Unit".encode('utf-8'),
                                                                byref(c_prop_val))
            self.check_return(return_code, f"Failed to get board parameter {param} Unit")
            self.board_params[param]["Unit"] = c_prop_val.value

            c_prop_val = c_short()
            return_code = self.libcaenhvwrapper.CAENHV_GetBdParamProp(self.caen,
                                                                c_ushort(self.slot),
                                                                param.encode('utf-8'),
                                                                "Exp".encode('utf-8'),
                                                                byref(c_prop_val))
            self.check_return(return_code, f"Failed to get board parameter {param} Exp")
            self.board_params[param]["Exp"] = c_prop_val.value

        # elif (self.board_params[param]['Type'] == self.PropertyType.PARAM_TYPE_ONOFF.name):
        #     print("onoff")
        #     c_prop_val = c_char_p()
        #     return_code = self.libcaenhvwrapper.CAENHV_GetBdParamProp(self.caen,
        #                                                         c_ushort(self.slot),
        #                                                         param.encode('utf-8'),
        #                                                         "Onstate".encode('utf-8'),
        #                                                         byref(c_prop_val))
        #     self.check_return(return_code, f"Failed to get board parameter {param} Onstate")
        #     self.board_params[param]["Onstate"] = c_prop_val.value
        #     print("onoff")
        #     return_code = self.libcaenhvwrapper.CAENHV_GetBdParamProp(self.caen,
        #                                                         c_ushort(self.slot),
        #                                                         param.encode('utf-8'),
        #                                                         "Offstate".encode('utf-8'),
        #                                                         byref(c_prop_val))
        #     self.check_return(return_code, f"Failed to get board parameter {param} Offstate")
        #     self.board_params[param]["Offstate"] = c_prop_val.value

    def get_board_parameter_value(self, param):
        if param not in self.board_params:
            sys.exit(f"Tried to access parameter{param} which wasn't in the board parameter list. Board parameter list is {self.board_params}")
        if (('Type' not in self.board_params[param]) or ('Mode' not in self.board_params[param])):
            sys.exit(f"Tried to access parameter{param} which didn't have Type and Mode set up in the board parameter list. Board parameter list is {self.board_params}")
        if (self.board_params[param]['Mode'] == self.PropertyMode.PARAM_MODE_WRONLY):
            sys.exit(f"Trying to read a parameter that is read only. Board parameter list is {self.board_params}")

        if (self.board_params[param]['Type'] == self.PropertyType.PARAM_TYPE_FLOAT.name):
            c_param_val = c_float()
        else:
            c_param_val = c_long()

        return_code = self.libcaenhvwrapper.CAENHV_GetBdParam(self.caen,
                                                            c_ushort(self.slot),
                                                            byref(c_ushort(self.slot)),
                                                            param.encode('utf-8'),
                                                            byref(c_param_val))

        self.check_return(return_code, f"Retrieving value for parameter {param} failed")
        self.board_params[param]["Value"] = c_param_val.value

    def check_return(self, ret, message = None):
        if (ret != 0):
            if (message):
                print(f"{self.prefix} --> {message}")
                print(f"{self.prefix} --> Attempt to communicate with CAEN R8033DM resulted in error code {hex(ret)}")
            return -1
        else:
            return 0

    class PropertyType(IntEnum):
        PARAM_TYPE_FLOAT = 0
        PARAM_TYPE_ONOFF = 1
        PARAM_TYPE_CHSTATUS = 2
        PARAM_TYPE_BDSTATUS = 3

    class PropertyMode(IntEnum):
        PARAM_MODE_RDONLY = 0
        PARAM_MODE_WRONLY = 1
        PARAM_MODE_RDWR = 2
