# created by Ryan Spies
# Lynker Technologies, LLC 
# 5/28/2018
# Python 2.7
# Description: Module to bin streamflow data for hourly calculations
# OneRain James Creek observations are measured on irregular intervals during low flow periods
# option to fill gaps up to 12-hours with previous observed reading

import pandas as pd
import os

##############################################################################
os.chdir("..")
input_dir = os.getcwd() + os.sep + 'data' + os.sep + 'James_Creek_streamflow_data' + os.sep
output_dir = os.getcwd() + os.sep + 'NWM_data_analysis' + os.sep + 'obs_flow' + os.sep

#input_files = ['merge_onerain_JamesCreek_Jamestown_flow_1999_2017.csv',
#               'onerain_LowerLefthand_10018_Flow_rate_7A.txt',
#               'onerain_S._St._Vrain_at_Berry_Rdg_10021_Flow_rate_4463.txt',
#               'onerain_Rowena_4430_Flow_rate_4433_2013_2017.txt',
#               'onerain_Little_Narrows_4470_Flow_rate_4473.txt',
#               'usgs_06727500_Orodell_Fourmile_Creek.csv']
input_files = ['usgs_06741510_Big_Thom_Loveland.csv',
               'usgs_06730200_Boulder_Creek_75th.csv',
               'usgs_402114105350101_Big_Thom_Estes.csv']

bin_minutes = '60'
header=1                        # head rows in data file to skip
usecols=[0,2]                   # columns to read data (date,variable) -- using different columns for usgs files (see below)
fill_option = True              # option to fill gaps in missing hourly data
##############################################################################
if fill_option == False:
    fill_outdir = '1hr_nofill'
else:
    fill_outdir = '1hr_filled'

for input_file in input_files:
    print(input_file)
    if input_file[:4].lower() == 'usgs':  # use different column numbers for usgs downloaded QIN files
        usecols=[2,4]
    print 'binning data: ' + bin_minutes 
    #basin = input_file.split('_')[1]
    #site_num = input_file.split('_')[-4]
    read_file = open(input_dir + input_file, 'r')
    data_read = pd.read_csv(read_file,sep=',',skiprows=header,
                usecols=usecols,parse_dates=['date'],names=['date', 'flow'])
                
       # Convert that column into a datetime datatype
    data_read['date'] = pd.to_datetime(data_read['date'])
    data_read.index = data_read['date']
    ### group data into time interval bins, store data in the right side of the bin and include the far right interval in the accumulation
    ### https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.resample.html
    group_data = data_read.groupby(pd.TimeGrouper(bin_minutes+'Min',closed='right',label='right'))['flow'].mean()
    
    ### fill data gaps between report intervals (often several hours during low flow periods)
    ### https://pandas.pydata.org/pandas-docs/version/0.21/generated/pandas.DataFrame.fillna.html
    if fill_option == True:
        print('Performing missing data fill/interpolate...')
        #fill_group_data = group_data.fillna(method='ffill',limit=12) # limit filling to forward fill 12 values
        fill_group_data = group_data.interpolate(method='linear',limit_direction='forward',limit=12,limit_area='inside') # limit filling to forward fill 12 values
    
    ### convert series back to dataframe
    if fill_option == True:
        group_data_df = fill_group_data.to_frame()
        group_data_df['date'] = fill_group_data.index
    else:
        group_data_df = group_data.to_frame()
        group_data_df['date'] = group_data.index
    read_file.close()
    
    ### write processed dataframe to csv
    ### https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.to_csv.html
    print 'writing data to csv...'
    group_data_df.to_csv(output_dir + fill_outdir + os.sep +'1hr_' + input_file[:-4] + '.csv',columns=['date','flow'],index=False,float_format='%.2f')
print 'Complete!!'