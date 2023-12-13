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
from ctypes import c_int, c_float, c_void_p, c_char_p, c_char, c_ushort, pointer, cdll, cast, POINTER, byref, sizeof

class CAENR8033DM:
    def __init__(self, json_data):
        self.prefix = "CAEN R8033DM"
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
        return_code = self.libcaenhvwrapper.CAENHV_InitSystem(c_int(13),                                        #13 is the value for
                                                              c_int(0),                                         #0 is the value for TCP/IP
                                                              self.json_data['caenR8033DM'].encode('utf-8'),    #IP address for TCP/IP
                                                              "".encode('utf-8'),                               #Username, unused
                                                              "".encode('utf-8'),                               #Password, unused
                                                              pointer(self.caen))                               #Pointer to returned handle

        self.check_return(return_code, "Initialized successfully")

        #self.get_info()
        self.get_board_info()

    def get_info(self):
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
        print(type(c_model_list))
        print(c_model_list)
        print(type(c_model_list.value))
        print(c_model_list.value)
        print(f"{self.prefix} --> Connected to Caen {c_model_list.value.decode('utf-8')}, serial number {c_serial_num_list.contents.value} with {c_num_of_slots.value} slots and {c_num_of_channels.contents.value} channels detected")
        self.check_return(return_code)

        c_num_sys_props = c_ushort()
        c_param_list = c_char_p()
        #self.libcaenhvwrapper.CAENHV_GetBdParamInfo.argtypes = [c_int, POINTER(c_ushort), POINTER(c_char_p)]
        return_code = self.libcaenhvwrapper.CAENHV_GetBdParam(self.caen,
                                                            c_ushort(0),
                                                            byref(c_ushort(0)),
                                                            "BdIlk".encode('utf-8'),
                                                            byref(c_param_list))

        self.check_return(return_code, "failed")
        print(c_param_list)
        print(c_param_list.value)

    def get_board_info(self):

        c_num_sys_props = c_ushort(0)
        c_bd_param_list = c_char_p()
        print(type(c_bd_param_list))
        #self.libcaenhvwrapper.CAENHV_GetBdParamInfo.argtypes = [c_int, POINTER(c_ushort), POINTER(c_char_p)]
        return_code = self.libcaenhvwrapper.CAENHV_GetBdParamInfo(self.caen,
                                                            c_num_sys_props,
                                                            byref(c_bd_param_list))

        #print(c_bd_param_list.value)
        self.check_return(return_code, "bd params failed")


        print(type(c_bd_param_list))
        print(sizeof(c_bd_param_list))
        print(type(c_bd_param_list.value))
        print(c_bd_param_list.value)
        x = cast(c_bd_param_list, (POINTER(c_char * 300)))
        print(type(x))
        print("here")
        #print(type(c_bd_param_list[0]))
        #print(type(c_bd_param_list[0].contents))
        #print(c_bd_param_list.raw)
        print(type(x.contents))
        print(sizeof(x.contents))
        print((x.contents))
        for i in range(300):
            print(x.contents[i])
        print("ok")
        y = c_char_p(0x7f93253e8440)

        print(y)
        print(type(y))
        print(y.value)

        print(type(x.contents.contents))
        print(sizeof(x.contents.contents))
        print((x.contents.contents))

        print(type(x.contents.value))
        print(sizeof(x.contents.value))
        print((x.contents.value))
        print(type(x.contents[0]))
        print(sizeof(c_bd_param_list.contents))
        print(type(c_bd_param_list.contents.value))
        print(sizeof(c_bd_param_list.contents.value))
        print(c_bd_param_list.contents.decode('utf-8'))
        print("works")
        print(c_bd_param_list.value.decode('utf-8'))

        print(c_bd_param_list.value)
        #print(type(c_bd_param_list[0]))
        print(type(c_bd_param_list.contents.value))
        print(c_bd_param_list.contents.value)
        print(type(c_bd_param_list.contents.value))

    def check_return(self, ret, message = None):
        if (ret != 0):
            if (message):
                print(f"{self.prefix} --> {message}")
            sys.exit(f"{self.prefix} --> Attempt to communicate with CAEN R8033DM resulted in error code {hex(ret)}")
