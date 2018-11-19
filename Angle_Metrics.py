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
directory = "H:/Dylan Brenneis/Compensatory Movements Study/Testing/Pro00077893-03-18-1"
Bento_directory = "H:/Dylan Brenneis/Compensatory Movements Study/BrachIOPlexus Logs csv/Pro00077893-03-18-1"
Savedir = "H:/Dylan Brenneis/Compensatory Movements study/Testing/Angle Metrics/"
current_dir = ""
Bento_current_dir = ""
ProParticipant = "Pro00077893-03-18-1"
dir_list = []
Bento_dir_list = []
joint_names = ["K:Cluster:TrunkFE", "K:Cluster:TrunkLatBend", "K:Cluster:TrunkAxRot", "K:Cluster:PrmryShoFE", "K:Cluster:PrmryShoAbAd", "K:Cluster:PrmryShoIERot"]
column_names = ["M:RHND:RHND1:X","M:RHND:RHND1:Y","M:RHND:RHND1:Z","K:Cluster:TrunkFE", "K:Cluster:TrunkLatBend", "K:Cluster:TrunkAxRot", "K:Cluster:PrmryShoFE", "K:Cluster:PrmryShoAbAd", "K:Cluster:PrmryShoIERot"]
Bento_joint_names = ["POS3", "POS4"]
Bento_joint_names_real = ["WristRot","WristR/UDev"]
Bento_column_names = ["POS3","POS4","VEL5"]

# Sample rate and desired cutoff frequencies (in Hz).
fs = 120.0
Bento_fs = 250
highcut = 10.0
Bento_highcut = 10.0
buffer_time = 50 #how many timesteps at the beginning of the file to ignore due to filter settling effects
Bento_buffer_time = 50

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
                                data_dict[item].append(float(row[col_numbers[i]]))
                                i = i+1
                return data_dict

#Same as getcolumns, but for Bento Data.
def getbentocolumns(name):
        with open(Bento_current_dir + "/" + trial, "rb") as csvfile:
                reader = csv.reader(csvfile,delimiter = ",")
                col_numbers = getbentocolumnnums(reader) #read the first line only; get the important column numbers from the header
                data_dict = {}
                for item in Bento_column_names: #initialize a dictionary with keys being the column header names
                        data_dict[item] = [] 
                for row in reader: #run through the .csv saving the important column information in the dictionary
                        i = 0
                        for item in Bento_column_names:
                                data_dict[item].append(float(row[col_numbers[i]]))
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

#same as getcolumnnums, but for Bento data
def getbentocolumnnums(reader):
        for row in reader:
                importantcols = []
                for i in range(len(row)):
                        for name in Bento_column_names:
                                if row[i] == name:
                                        importantcols.append(i)
                return importantcols

#finds resultant hand speed for all positions in time
def gethandvel(data_dict):
        handvel = {"M:RHND:RHND1:X":[],"M:RHND:RHND1:Y":[],"M:RHND:RHND1:Z":[]}
        for item in ["M:RHND:RHND1:X","M:RHND:RHND1:Y","M:RHND:RHND1:Z"]:
                position = butter_lowpass_filter(linearfill(data_dict[item]), highcut, fs, order = 6)
                for i in range(len(position)-1):
                        handvel[item].append((position[i+1]-position[i]) * 120) #position data comes in at 120Hz
        resultantvel = []
        for i in range(len(handvel["M:RHND:RHND1:X"])):
                resultantvel.append(np.sqrt(np.square(handvel["M:RHND:RHND1:X"][i]) + np.square(handvel["M:RHND:RHND1:Y"][i]) + np.square(handvel["M:RHND:RHND1:Z"][i])))
        return resultantvel

#gives the hand velocity that triggers the start and end of trials. 5% of peak velocity (or 5% of 1500 mm/s, whichever is lower)
def gettriggervel(handvel):
        peak = max(handvel[buffer_time:len(handvel)])
        peak = min([peak,1500])
        return 0.05 * peak

#fills and filters the gripper velocity from the bento data
def getgrippervel(data):
        return butter_lowpass_filter(linearfill(data["VEL5"]),Bento_highcut,Bento_fs,order = 6)

#Converts the encoder position data from the servos to joint angles
def convert_to_angles(column,joint_type):
        
        if joint_type == "POS3":
                column = column - np.nanmean(column) #since the true rotation angle is some combination of biological wrist rotation and bento arm rotation, set the average angle to zero for now and consider the implications.
        elif joint_type == "POS4": #2045 is defined as 0 degrees. Up is positive angle, down is negative.
                column = column - 2045
        degree_col = column / 11.361111111111111 #11.36111111 degrees per encoder tick   
        return degree_col

#This function returns the metrics of the joint angles in a list [max,min,range,mean,median]. Strings, rounded to 4 decimal places.
def metrics(joint_angles):
        metric_list = []
        metric_list.append(str(round(np.nanmax(joint_angles),4)))
        metric_list.append(str(round(np.nanmin(joint_angles),4)))
        metric_list.append(str(round(np.nanmax(joint_angles)-np.nanmin(joint_angles),4)))
        metric_list.append(str(round(np.nanmean(joint_angles),4)))
        metric_list.append(str(round(np.nanmedian(joint_angles),4)))
        return metric_list

#Makes a list of the strings to write the line of data that will be printed to the csv
def getdataline(task,intervention,jointName,metriclist):
        dataline = [task,intervention,jointName]
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
                writefile.write("TASK,INTERVENTION,JOINT,MAX,MIN,RANGE,MEAN,MEDIAN")

#writes the given line of data to csv with the participant number as the file name
def writetocsv(Savedir,participant,data):
        with open(Savedir + participant + ".csv", "a") as writefile:
                datastring = ",".join(data)
                writefile.write("\n" + datastring)

#determines the start of the trial based on hand velocity
def getstart(handvel,triggervel):
        for i in range(buffer_time,len(handvel)): 
                if handvel[i] >= triggervel and handvel[i-1] < handvel[i]:
                        return i
                elif i == len(handvel)-1: #if never triggered
                        return i #will result in len_1 data sequence, should still work but be obvious that it's erroneous
                else:
                        pass

#determines the start of the trial for Bento data based on gripper velocity (immediately after the full open/full close synchronization procedure)
def getbentostart(data):
        triggercheck1 = False
        triggercheck2 = False
        for i in range(Bento_buffer_time,len(data)):
                if data[i] < -100 and not triggercheck1: # the velocity goes down past -100 before coming back up past 0
                        triggercheck1 = True 
                if data[i] > 0 and triggercheck1: # once past 0, when the velocity comes back down we start the trial
                        triggercheck2 = True
                if data[i] < 1.0 and triggercheck1 and triggercheck2: # in case it doesn't get to exactly 0, it should still trigger
                        return i
                elif i == len(data): #if never triggered
                        return i # will result in len_1 data sequence, should still work but be obvious that it's erroneous
                else:
                        pass

#determines the end of the trial for Bento data based on gripper velocity (1 s after last hand open, or the end of the data file.)
def getbentoend(data):
        i = len(data) - 1
        while i >=0:
                if data[i] > 25:
                        return min(i + 250, len(data)) #250 timesteps ~ 1s at a 3-4 ms timestep
                else:
                        i -= 1
        return len(data)

#determines the end of the trial based on hand velocity
def getend(handvel,triggervel):
        for i in range(len(handvel)-buffer_time):
                j = len(handvel) - i - 1
                if handvel[j] >= triggervel and handvel[j-1] < handvel[i]:
                        return j
                elif i == len(handvel)-buffer_time-1: #if never triggered
                        return len(handvel) #give the whole trial length

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
for ppt in ["00"]:#35", "42", "45", "53", "80", "96"]:
        participant = ProParticipant + ppt
        current_dir = directory + ppt
        Bento_current_dir = Bento_directory + ppt
        dir_list = []
        Bento_dir_list = []
        dir_list = os.listdir(current_dir)
        Bento_dir_list = os.listdir(Bento_current_dir)
        #create a new .csv file for the participant (overwrite if one exists)
        createfile(Savedir,participant)
        

        #for each trial in the participant folder
        for trial in dir_list:
                #read the file, saving only the pertinent columns
                data_dict = getcolumns(current_dir + "/" + trial)
                Bento_data_dict = getbentocolumns(Bento_current_dir + "/"+ trial)                               
                #determine the task type of the trial
                task = gettask(trial)
                #determine the intervention (AL, SS, FW) of the trial
                intervention = getintervention(trial)   
                #get hand velocity information
                handvel = gethandvel(data_dict)
                triggervel = gettriggervel(handvel)
                grippervel = getgrippervel(Bento_data_dict)
                #find the row of trial start
                trialstart = getstart(handvel,triggervel)
                bento_trialstart = getbentostart(grippervel)
                #find the row of trial end
                trialend = getend(handvel,triggervel)
                bento_trialend = getbentoend(grippervel) 
                
                #for each joint angle type, get the metrics and write to a single line
                for i in range(len(joint_names)):
                        #fill the column, removing NaNs
                        filledcolumn = linearfill(data_dict[joint_names[i]])
                        #filter the column
                        filteredcolumn = butter_lowpass_filter(filledcolumn, highcut, fs, order = 6)
                        #trim the column for trial data only
                        trimmedcolumn = trim(trialstart,trialend,filteredcolumn)
                        #get the metrics from the column
                        measures = metrics(trimmedcolumn)                        
                        #get the data all into a single line
                        dataline = getdataline(task,intervention,joint_names[i],measures)
                        #print to .csv
                        writetocsv(Savedir,participant,dataline)
                #for each joint angle type in the Bento Data, also get the metrics and write to a single line
                for i in range(len(Bento_joint_names)):
                        #fill the column, removing NaNs
                        filledcolumn = linearfill(Bento_data_dict[Bento_joint_names[i]])
                        #filter the column
                        filteredcolumn = butter_lowpass_filter(filledcolumn, Bento_highcut, Bento_fs, order = 6)
                        #trim the column for trial data only
                        trimmedcolumn = trim(bento_trialstart,bento_trialend,filteredcolumn)
                        #convert the position encoder data to angles
                        convertedcolumn = convert_to_angles(trimmedcolumn,Bento_joint_names[i])
                        #get the metrics from the column
                        measures = metrics(convertedcolumn)
                        #get the data all into a single line
                        dataline = getdataline(task,intervention,Bento_joint_names_real[i],measures)
                        #print to .csv
                        writetocsv(Savedir,participant,dataline)
                        
                        #plot the hand velocity for each trial, and save to .png
                        plt.figure(1)
                        plt.clf()
                        t = np.linspace(0, len(grippervel), len(grippervel))
                        plt.plot(t, grippervel, label = 'Gripper Velocity')
                        t_jointangle = np.linspace(0, len(convertedcolumn), len(convertedcolumn))
                        plt.plot(t_jointangle, convertedcolumn, label = 'Joint Angle')
                        t_raw = np.linspace(0,len(Bento_data_dict[Bento_joint_names[i]]), len(Bento_data_dict[Bento_joint_names[i]]))
                        plt.plot(t_raw, Bento_data_dict[Bento_joint_names[i]], label = "Raw")
                        plt.title(trial)
                        plt.ylabel('Velocity (mm/s)')
                        plt.xlabel('Timestep')
                        plt.grid(True)
                        plt.axis('tight')
                        plt.legend(loc = 'best')
                        plt.savefig(Savedir + "Hand Velocity test Figures/" + trial + ".png")
                        plt.show()
                
                #trial_length = [str(trialend - trialstart),str(triggervel)]
                #writetocsv(Savedir,participant,trial_length)


        
#  plt.clf()
        #Plot the data being filtered as raw
#        t_raw = np.linspace(0, len(handvel),len(handvel))
#        plt.plot(t_raw, handvel, label='Hand Velocity')
#        #plot filtered data
#        t_flt = np.linspace(0, len(trimmedcolumn),len(trimmedcolumn))
#        plt.plot(t_flt, trimmedcolumn, label='Filtered signal')
#        plt.xlabel('time (seconds)')
#        plt.grid(True)
#        plt.axis('tight')
#        plt.legend(loc='upper left')
#        plt.savefig(Savedir +  participant + ".png")
#        plt.show()
                        



                
                
                
                   

