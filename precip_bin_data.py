# created by Ryan Spies 
# 7/20/2017
# Python 2.7
# Description: Module to bin precipitation data for station calculations

import pandas as pd


def bin_precip(input_file,bin_minutes):
#for input_file in os.listdir(input_dir+ os.sep):
    print 'binning precip data: ' + bin_minutes 
    #basin = input_file.split('_')[1]
    #site_num = input_file.split('_')[-4]
    read_file = open(input_file, 'r')
    data_read = pd.read_csv(read_file,sep=',',skiprows=12,
                usecols=[1,3],parse_dates=['date'],names=['date', 'precip'])
                
   # Convert that column into a datetime datatype
    data_read['date'] = pd.to_datetime(data_read['date'])
    data_read.index = data_read['date']
    ### group data into time interval bins, store data in the right side of the bin and include the far right interval in the accumulation
    ### https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.resample.html
    group_data = data_read.groupby(pd.TimeGrouper(bin_minutes+'Min',closed='right',label='right'))['precip'].sum()
    
    ### convert series back to dataframe
    group_data_df = group_data.to_frame()
    group_data_df['date'] = group_data_df.index
    read_file.close()
    #data_read.groupby(data_read.index.hour).sum()
    return group_data_df
