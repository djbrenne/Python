# -*- coding: utf-8 -*-
"""
Created on Sun Nov 18 2018

@author: Dylan Brenneis
"""
#Imports
import os
import csv

#Initialize variables
directory = "H:/Dylan Brenneis/Compensatory Movements Study/BrachIOPlexus Logs/Pro00077893-03-18-1"
current_dir = ""
ProParticipant = "Pro00077893-03-18-1"
dir_list = []
Savedir = "H:/Dylan Brenneis/Compensatory Movements Study/BrachIOPlexus Logs csv/"

#creates a file with the participant number as the file name, and appropriate header
def createfile(Save_name):
        with open(Save_name, "wb") as writefile:
                writefile.write("TIMESTAMP,ELAPSED MS,SWITCH_SIG,JOINT_CONTROLLED,IMU_X,IMU_Y,IMU_Z,MYO_CH4,MYO_CH7,POS3,VEL3,LOAD3,POS4,VEL4,LOAD4,POS5,VEL5,LOAD5\n")

#converts the file to .csv
def convertfile(Orig_name,Save_name):
        with open(Orig_name, "rb") as readfile, open(Save_name, "ab") as writefile:
                stripped = (line.strip() for line in readfile)
                lines = (line.split(",") for line in stripped if line)
                writer = csv.writer(writefile)
                writer.writerows(lines)

#MAIN LOOP
#Loop through the directories for the participants we care about
for ppt in ["05", "27", "35", "42", "45", "53", "56", "69", "80", "82", "95", "96"]:
        participant = ProParticipant + ppt
        current_dir = directory + ppt
        dir_list = []
        dir_list = os.listdir(current_dir)
        for trial in dir_list:
                Orig_name = current_dir + "/" + trial
                Save_name = Savedir + participant + "/" + trial[:-4] + ".csv"
                #create a new .csv file for the trial (overwrite if one exists)
                createfile(Save_name)
                #open the .txt file, and write it line by line into the .csv
                convertfile(Orig_name,Save_name)