# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 2018

@author: Dylan Brenneis
"""
#Imports
import os
import csv

#Initialize variables
directory = "H:/Dylan Brenneis/Compensatory Movements Study/BrachIOPlexus Logs csv/Pro00077893-03-18-1"
current_dir = ""
ProParticipant = "Pro00077893-03-18-1"
dir_list = []

#MAIN LOOP
#Loop through the directories for the participants we care about
for ppt in ["00", "05", "27", "35", "42", "45", "53", "56", "69", "80", "82", "95", "96"]:
        participant = ProParticipant + ppt
        current_dir = directory + ppt
        dir_list = []
        dir_list = os.listdir(current_dir)
        for trial in dir_list:
                Orig_name = current_dir + "/" + trial
                Save_name = directory + ppt + "/" + trial[:-6]
                trial_number = trial[-6:-4]
                if trial_number[0] == "_":
                        trial_number = trial_number[0] + "0" + trial_number[1]
                else:
                        pass
                Save_name = Save_name + trial_number + ".csv"
                #rename the file
                os.rename(Orig_name,Save_name)