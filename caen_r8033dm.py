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

        c_slot_num = c_ushort(0)
        c_bd_param_list = c_char_p()
        #Function takes in a **char type as the parameter list. It will write back an array of char arrays
        return_code = self.libcaenhvwrapper.CAENHV_GetBdParamInfo(self.caen,
                                                            c_slot_num,
                                                            byref(c_bd_param_list))

        self.check_return(return_code, "bd params failed")

        #Cast as a pointer to 10 char arrays. The type is
        #<class 'caen_r8033dm.LP_c_char_Array_10'>
        #You need to just "know" that each parameter fills 10 chars, either with terminating null characters or gibberish
        #I confirmed by reading out the full memory block, and also through the example C script

        par_array = cast(c_bd_param_list, (POINTER(c_char * 10)))

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
        print(board_params)

    def check_return(self, ret, message = None):
        if (ret != 0):
            if (message):
                print(f"{self.prefix} --> {message}")
            sys.exit(f"{self.prefix} --> Attempt to communicate with CAEN R8033DM resulted in error code {hex(ret)}")
