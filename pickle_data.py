# created by Ryan Spies 
# 3/7/2018
# Python 2.7

import os
import datetime
import pandas as pd
import precip_bin_data ## my module for binning precip

os.chdir("..")
maindir = os.getcwd() + os.sep + 'data' + os.sep
pstart = datetime.datetime.now()

################## User Input ########################
variable = 'historical_precip'              # choices: 'flow' for streamflow or 'stage' for gauge height
if variable == 'flow':
    input_dir = maindir + os.sep + 'James_Creek_streamflow_data' + os.sep
if variable == 'historical_precip':
    input_dir = maindir + os.sep + 'James_Creek_precip_sites_historical' + os.sep
    pbin = '20'                      # precip bin time in minutes 
    header=1                        # head rows in data file to skip
    usecols=[0,2]                   # columns to read data (date,variable)
    roll_wins = [4320,1440,720,360,180,120,60,10]
input_files = []
######################################################

### STREAMFLOW DATA ###    
## Define the steamflow/stage data file 
#input_file = 'merge_onerain_JamesCreek_Jamestown_flow_1999_2017.csv' #'onerain_JamesCreek_Jamestown_10017_Flow_rate_7a.txt'
if variable == 'flow':
    for input_file in os.listdir(input_dir):
        print input_file
        print('Reading flow/stage file...')
        read_file = open(input_dir + input_file, 'r')
        print('Parsing flow/stage file...')
        test = pd.read_csv(read_file,sep=',',skiprows=1, na_filter=True,
                    usecols=[0,2],parse_dates=['date'],names=['date', 'OBS'])
        test.dropna(inplace=True)
        read_file.close()
        
        print 'Pickling data...'
        test.to_pickle(maindir + 'pickle_data' + os.sep + variable + os.sep+ input_file[:-4])
        
### PRECIP DATA ###    
#input_file = 'merge_onerain_JamesCreek_Jamestown_flow_1999_2017.csv' #'onerain_JamesCreek_Jamestown_10017_Flow_rate_7a.txt'
if variable == 'historical_precip':
    for input_file in os.listdir(input_dir+ os.sep):
        in_file = input_dir + os.sep + input_file    
        print('Reading flow/stage file...')
        df = precip_bin_data.bin_precip(in_file,pbin,header,usecols)
        print 'Pickling binned data...'
        df.to_pickle(maindir + 'pickle_data' + os.sep + variable + os.sep + pbin + 'min_bin' + os.sep+ input_file[:-4])
        
        ### use the rolling window calculation to generate precip time series
        for roll_win in roll_wins:
            print("Performing rolling accumulation calculation for window: " + str(roll_win))
            df['rolling'] = df.precip.rolling(window=roll_win,freq='min',min_periods=1,closed='right').sum()
            print 'Pickling rolling accum data...'
            df.to_pickle(maindir + 'pickle_data' + os.sep + variable + os.sep + pbin + 'min_bin' + os.sep + input_file[:-4]+'_'+str(roll_win))

print 'Script completed!!'
pend = datetime.datetime.now()
runtime = pend-pstart
print('Script runtime: ' + str(runtime.seconds) + ' seconds')       