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
Savedir = "H:/Dylan Brenneis/Compensatory Movements study/Testing/Angle Metrics/"
current_dir = ""
ProParticipant = "Pro00077893-03-18-1"
dir_list = []
joint_names = ["K:Cluster:TrunkFE"]#, "K:Cluster:TrunkLatBend", "K:Cluster:TrunkAxRot", "K:Cluster:PrmryShoFE", "K:Cluster:PrmryShoAbAd", "K:Cluster:PrmryShoIERot"]
column_names = ["M:RHND:RHND1:X","M:RHND:RHND1:Y","M:RHND:RHND1:Z","K:Cluster:TrunkFE", "K:Cluster:TrunkLatBend", "K:Cluster:TrunkAxRot", "K:Cluster:PrmryShoFE", "K:Cluster:PrmryShoAbAd", "K:Cluster:PrmryShoIERot"]
# Sample rate and desired cutoff frequencies (in Hz).
fs = 120.0
highcut = 10.0

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

#Gets the column number of the important columns
def getcolumnnums(reader):
        for row in reader:
                importantcols = []
                for i in range(len(row)):
                        for name in column_names:
                                if row[i] == name:
                                        importantcols.append(i)
                return importantcols


#This function returns the data only from the column of the specified header
def columnread(header):
        return reader[header]

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
#reads the column data, and returns it in a list
def read(column):
        columnreader = columnread(column)
        return columnreader[1:len(columnreader)]

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
def getstart(data_dict):
        return 50 #past the filter settling time

#determines the end of the trial based on something else
def getend(data_dict):
        return len(data_dict['M:RHND:RHND1:X']) #use the whole trial for now

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
                        while np.isnan(column[i+j]) and i + j <= len(column): #look ahead until you see real data or the end of the column
                                j = j + 1
                        new_value = (column[i+j]-column[i-1]) / (j+1) + column[i-1] #linear interpolation, knowing everything behind has already been filled                   
                else:
                        new_value = value
                column[i] = new_value
        return column



#Loop through the directories for the participants we care about
for ppt in ["00"]:#, "35", "42", "45", "53", "80", "96"]:
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
                #filter the data

                #find the row of trial start
                trialstart = getstart(data_dict)
                #find the row of trial end
                trialend = getend(data_dict) 
                
                #for each joint angle type, get the metrics and write to a single line
                for i in range(len(joint_names)):
                        #read the column for the joint angle 
                        #column = read(joint_names[i])
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
                        plt.figure(1)
        
        #Plot the filter characteristics
        plt.clf()
        for order in [3, 6, 9]:
                b, a = butter_lowpass(highcut, fs, order=order)
                w, h = freqz(b, a, worN=2000)
                plt.plot((fs * 0.5 / np.pi) * w, abs(h), label="order = %d" % order)

        plt.plot([0, 0.5 * fs], [np.sqrt(0.5), np.sqrt(0.5)],
                 '--', label='sqrt(0.5)')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Gain')
        plt.grid(True)
        plt.legend(loc='best')

        
        plt.figure(2)
        plt.clf()
        #Plot the data being filtered as raw
        t_raw = np.linspace(0, len(filledcolumn),len(filledcolumn))
        plt.plot(t_raw, filledcolumn, label='Raw data')
        #plot filtered data
        t_flt = np.linspace(0, len(trimmedcolumn),len(trimmedcolumn))
        plt.plot(t_flt, trimmedcolumn, label='Filtered signal')
        plt.xlabel('time (seconds)')
        plt.grid(True)
        plt.axis('tight')
        plt.legend(loc='upper left')
        plt.show()
                        



                
                
                
                   

