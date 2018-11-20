# -*- coding: utf-8 -*-
"""
Created on Fri Nov 16 2018

@author: Dylan Brenneis
"""
#Imports
import os
import csv
import numpy as np
from scipy.signal import butter, lfilter, freqz
import matplotlib.pyplot as plt


#Initialize variables
directory = "H:/Dylan Brenneis/Compensatory Movements Study/BrachIOPlexus Logs csv/Pro00077893-03-18-1"
Savedir = "H:/Dylan Brenneis/Compensatory Movements study/Testing/Bento_Metrics/"
current_dir = ""
ProParticipant = "Pro00077893-03-18-1"
dir_list = []
metric_names = ["SWITCH_SIG", "JOINT_CONTROLLED"]
column_names = ["SWITCH_SIG", "JOINT_CONTROLLED","VEL5"]

# Sample rate and desired cutoff frequencies (in Hz).
fs = 250.0
highcut = 10.0
buffer_time = 50 #how many timesteps at the beginning of the file to ignore due to filter settling effects

#Saves all the important columns in the .csv file
def getcolumns(name):
    with open(current_dir + "/" + trial, "rb") as csvfile:
        reader = csv.reader(csvfile,delimiter = ",")
        col_numbers = getcolumnnums(reader) #read the first line only; get the important column numbers from the header
        data_dict = {}
        for item in column_names: #initialize a dictionary with keys being the column header names
            data_dict[item] = [] 
        for row in reader: #run through the .csv saving the important column information in the dictionary
            i = 0
            for item in column_names:
                data_dict[item].append(row[col_numbers[i]])
                i = i+1
        return data_dict

#Gets the column number of the important columns
def getcolumnnums(reader):
    for row in reader:
        importantcols = []
        for i in range(len(row)):
            for name in column_names:
                if row[i] == name:
                    importantcols.append(i)
        return importantcols

#fills and filters the gripper velocity from the bento data
def getgrippervel(data):
    return butter_lowpass_filter(linearfill(list(np.float_(data["VEL5"]))),highcut,fs,order = 6)

#Converts the encoder position data from the servos to joint angles
def convert_to_angles(column,joint_type):
        
    if joint_type == "POS3":
        column = column - np.nanmean(column) #since the true rotation angle is some combination of biological wrist rotation and bento arm rotation, set the average angle to zero for now and consider the implications.
    elif joint_type == "POS4": #2045 is defined as 0 degrees. Up is positive angle, down is negative.
        column = column - 2045
    degree_col = column / 11.361111111111111 #11.36111111 degrees per encoder tick   
    return degree_col

#This function returns the metrics.
def metrics(name,item):
    if name == "SWITCH_SIG": #count the number of switches
        item = list(np.int_(item))
        metric = list(item).count(1)
    elif name == "JOINT_CONTROLLED": #count the number of timesteps for which the wrist is directly controlled, multiplied by 3.5 ms per timestep
        item = list(np.int_(item))
        metric = list(item).count(4) * 0.0035
    else:
        metric = np.nanmean(item)
    return metric

#Makes a list of the strings to write the line of data that will be printed to the csv
def getdataline(task,intervention,trialtime,metriclist):
    dataline = [task,intervention,trialtime]
    for i in range(len(metriclist)):
        dataline.append(metriclist[i])
    return dataline

#determines the task given the trial name
def gettask(trialname):
    if "Pasta" in trialname:
        return "Pasta"
    elif "Cups" in trialname:
        return "Cups"
    else:
        return "Other"

#determines the intervention type given the trial name
def getintervention(trialname):
    if "AL" in trialname:
        return "AL"
    elif "SS" in trialname:
        return "SS"
    elif "F" in trialname:
        return "FW"
    else:
        return "Other"

#trims the column of data to include the trial only (no before start or after end movement):
def trim(trialstart,trialend,column):
    return column[trialstart:trialend]

#Builds the filter
def butter_lowpass(highcut, fs, order=5):
    nyq = 0.5 * fs
    high = highcut / nyq
    b, a = butter(order, high, btype='low')
    return b, a

#actually filters the data
def butter_lowpass_filter(data, highcut, fs, order=5):
    b, a = butter_lowpass(highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

#creates a file with the participant number as the file name, and appropriate header
def createfile(Savedir,participant):
    with open(Savedir + participant + ".csv", "wb") as writefile:
        writefile.write("TASK,INTERVENTION,TRIAL_LENGTH,SWITCHES,TIME_CNTRL_WRST")

#writes the given line of data to csv with the participant number as the file name
def writetocsv(Savedir,participant,data):
    with open(Savedir + participant + ".csv", "a") as writefile:
        datastring = ",".join(data)
        writefile.write("\n" + datastring)

#determines the start of the trial for Bento data based on gripper velocity (immediately after the full open/full close synchronization procedure)
def getstart(data):
    triggercheck1 = False
    triggercheck2 = False
    for i in range(buffer_time,len(data)):
        if data[i] < -100 and not triggercheck1: # the velocity goes down past -100 before coming back up past 0
            triggercheck1 = True 
        if data[i] > 0 and triggercheck1: # once past 0, when the velocity comes back down we start the trial
            triggercheck2 = True
        if data[i] < 1.0 and triggercheck1 and triggercheck2: # in case it doesn't get to exactly 0, it should still trigger
            return i
        elif i == len(data) - 1: #if never triggered
            return i # will result in len_1 data sequence, should still work but be obvious that it's erroneous
        else:
            pass
    return len(data) - 1

#determines the end of the trial for Bento data based on gripper velocity (1 s after last hand open, or the end of the data file.)
def getend(data):
    i = len(data) - 1
    while i >=0:
        if data[i] > 25:
            return min(i + 250, len(data)) #250 timesteps ~ 1s at a 3-4 ms timestep
        else:
            i -= 1
    return len(data)

#fills in NaN data with interpolated values
def linearfill(column):
    for i in range(len(column)):
        value = column[i]                
        if i == 0: #don't interpolate the first value
            new_value = value
        elif i == len(column) - 1: # don't interpolate the last value
            new_value = value
        elif np.isnan(value):
            j = 1 
            while np.isnan(column[i+j]) and i + j < len(column) - 1: #look ahead until you see real data or the end of the column
                j = j + 1
            new_value = (column[i+j]-column[i-1]) / (j+1) + column[i-1] #linear interpolation, knowing everything behind has already been filled                   
        else:
            new_value = value
        column[i] = new_value
    return column


#MAIN LOOP
#Loop through the directories for the participants we care about
for ppt in ["82", "95", "96"]:#"05", "27", "35", "42", "45", "53", "56", "69", "80", 
    participant = ProParticipant + ppt
    current_dir = directory + ppt
    dir_list = []
    dir_list = os.listdir(current_dir)
    #create a new .csv file for the participant (overwrite if one exists)
    createfile(Savedir,participant)

    #for each trial in the participant folder
    for trial in dir_list:
        #read the file, saving only the pertinent columns
        data_dict = getcolumns(current_dir + "/" + trial)                               
        #determine the task type of the trial
        task = gettask(trial)
        #determine the intervention (AL, SS, FW) of the trial
        intervention = getintervention(trial)   
        #get gripper velocity information
        grippervel = getgrippervel(data_dict)
        #find the row of trial start
        trialstart = getstart(grippervel)
        #find the row of trial end
        trialend = getend(grippervel)
        #find total trial time
        trialtime = str((trialend - trialstart) * 0.0035) #3-4 ms per timestep
        #initialize the metric_list
        metric_list = []
                
        #for each joint angle type, get the metrics and write to a single line
        for i in range(len(metric_names)):
            #fill the column, removing NaNs
            #filledcolumn = linearfill(data_dict[metric_names[i]])
            #filter the column
            #filteredcolumn = butter_lowpass_filter(filledcolumn, highcut, fs, order = 6)
            #trim the column for trial data only
            trimmedcolumn = trim(trialstart,trialend,data_dict[metric_names[i]])
            #get the metrics from the column
            measures = metrics(metric_names[i],trimmedcolumn)                        
            #get the data all into a single line
            metric_list.append(str(measures))
        
        #create the writeline for the trial
        dataline = getdataline(task,intervention,trialtime,metric_list)
        #print to .csv
        writetocsv(Savedir,participant,dataline)
                        
            #plot the hand velocity for each trial, and save to .png
            #plt.figure(1)
            #plt.clf()
            #t = np.linspace(0, len(grippervel), len(grippervel))
            #plt.plot(t, grippervel, label = 'Gripper Velocity')
            #t_jointangle = np.linspace(0, len(convertedcolumn), len(convertedcolumn))
            #plt.plot(t_jointangle, convertedcolumn, label = 'Joint Angle')
            #t_raw = np.linspace(0,len(Bento_data_dict[Bento_metric_names[i]]), len(Bento_data_dict[Bento_metric_names[i]]))
            #plt.plot(t_raw, Bento_data_dict[Bento_metric_names[i]], label = "Raw")
            #plt.title(trial)
            #plt.ylabel('Velocity (mm/s)')
            #plt.xlabel('Timestep')
            #plt.grid(True)
            #plt.axis('tight')
            #plt.legend(loc = 'best')
            #plt.savefig(Savedir + "Hand Velocity test Figures/" + trial + ".png")
            #plt.show()
                        



                
                
                
                   

