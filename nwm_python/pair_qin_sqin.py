# created by Ryan Spies
# Lynker Technologies, LLC 
# 5/28/2018
# Python 2.7
# Description: Module to pair hourly flow data from NWM simulation and hourly gage observed data
# Converting NWM SQIN data from cms to cfs and shifting timestamp (assumed UTC to local/Denver)

import pandas as pd
import os
from dateutil import tz
################################ Input Variables ####################################
input_sqin_dir = os.getcwd() + os.sep + 'comid_flow' + os.sep
input_qin_dir = os.getcwd() + os.sep + 'obs_flow' + os.sep
output_dir = os.getcwd() + os.sep + 'QIN_SQIN' + os.sep
comids = ['13584','2889214','12932'] #['2888976','2888956','2889346','2888790','2889124','2888748','2888974','2889068'] # 2889068 and 2888974 are used for JC upstream segments (Little and Central James Creek)
comid_obs_pair = {'2888976':'1hr_merge_onerain_JamesCreek_Jamestown_flow_1999_2017.csv',
                  '2888974':'1hr_merge_onerain_JamesCreek_Jamestown_flow_1999_2017.csv',
                  '2889068':'1hr_merge_onerain_JamesCreek_Jamestown_flow_1999_2017.csv',
                  '2888956':'1hr_onerain_LowerLefthand_10018_Flow_rate_7A.csv',
                  '2889346':'1hr_usgs_06727500_Orodell_Fourmile_Creek.csv',
                  '2888790':'1hr_onerain_S._St._Vrain_at_Berry_Rdg_10021_Flow_rate_4463.csv',
                  '2889124':'1hr_onerain_Rowena_4430_Flow_rate_4433_2013_2017.csv',
                  '2888748':'1hr_onerain_Little_Narrows_4470_Flow_rate_4473.csv',
                  '13584':'1hr_usgs_402114105350101_Big_Thom_Estes.csv',
                  '2889214':'1hr_usgs_06730200_Boulder_Creek_75th.csv',
                  '12932':'1hr_usgs_06741510_Big_Thom_Loveland.csv'}                 
years = range(1993,2017,1)
fill_data = False              # option to use data with filled gaps in missing hourly data
data_group = '1hr'              # aggregate data time window
#####################################################################################
if fill_data == True:
    input_qin_dir = input_qin_dir + '1hr_filled' + os.sep
    output_dir = output_dir + data_group + '_filled' + os.sep
else:
    input_qin_dir = input_qin_dir + '1hr_nofill' + os.sep
    output_dir = output_dir + data_group + '_nofill' + os.sep

for comid in comids:
    print('Parsing nwm-sqin data...')
    for year in years:
        print('Processing: ' + str(year))
        sqin_read = open(input_sqin_dir + str(year) + os.sep + comid + '_flow.csv','r')
        sdf = pd.read_csv(sqin_read,usecols=[0,1], header = 1, parse_dates=[0],names=['date','nwm_sqin'],na_values=[' ','','na','NA','-999'])
        sdf.nwm_sqin*= 35.3147 #### !!!!! convert simulated flow (cms) to cfs !!!!! ####
        if year == years[0]:
            sqin_df = sdf
        else:
            ## merge dataframes (https://pandas.pydata.org/pandas-docs/stable/merging.html)
            sqin_df = pd.concat([sqin_df,sdf])
        sqin_read.close()
        
    # convert NWM UTC timestep to local (mountain time zone)
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Denver')
    sqin_df['date'] = sqin_df['date'].dt.tz_localize(from_zone).dt.tz_convert(to_zone)
    sqin_df['date'] = sqin_df['date'].dt.tz_localize(None)
    
    print('Parsing obs-qin data...')
    qin_read = open(input_qin_dir + comid_obs_pair[comid],'r')
    qin_df = pd.read_csv(qin_read,usecols=[0,1], header = 1, parse_dates=[0],names=['date','obs_qin'],na_values=[' ','','na','NA','-999'])
    qin_read.close()
    
    if data_group == '6hr':
        bin_minutes='360'
        ### group data into time interval bins, store data in the right side of the bin and include the far right interval in the accumulation
        ### https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.resample.html
        #qin_df['date'] = pd.to_datetime(qin_df['date'])
        qin_df.index = qin_df['date']
        #sqin_df['date'] = pd.to_datetime(sqin_df['date'])
        sqin_df.index = sqin_df['date']
        qin_df = qin_df.groupby(pd.TimeGrouper(bin_minutes+'Min',closed='right',label='right'))['obs_qin'].mean()
        sqin_df = sqin_df.groupby(pd.TimeGrouper(bin_minutes+'Min',closed='right',label='right'))['nwm_sqin'].mean()
        qin_df =qin_df.to_frame().reset_index()
        sqin_df =sqin_df.to_frame().reset_index()
    
    ## merge sqin and qin dataframes (keeping all )
    ## https://pandas.pydata.org/pandas-docs/stable/merging.html
    join_df = sqin_df.merge(qin_df,how='outer')     
    #join_df = qin_df.join(sqin_df,how='outer')
    

    ## write output to csv file
    join_df.to_csv(output_dir + comid + '_SQIN_QIN.csv',columns=['date','obs_qin','nwm_sqin'],index=False,float_format='%.2f')
    print('Completed!!')
