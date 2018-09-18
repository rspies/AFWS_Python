# created by Ryan Spies
# Lynker Technologies, LLC 
# 5/28/2018
# Python 2.7
# Description: This script reads csv files from "pair_qin_sqin.py"
# Finds the start and end of the observed hourly QIN record, # of valid data points, and % of total available.
# Performs statistical calculations between SQIN and QIN and outputs summary data to csv file

import os
import pandas as pd
import numpy as np
import datetime
import calendar

import calc_errors
pstart = datetime.datetime.now()
############################### User input ###################################
##############################################################################
##### IMPORTANT: Make sure to call the correct .csv output columns ######
comids = ['13584','2889214','12932'] #['2888976','2888956','2889346','2888790','2889124','2888748']
comid_name = {'2888976':'JamesCreek_Jamestown',
                  '2888956':'Lower_Lefthand',
                  '2889346':'Orodell_Fourmile_Creek',
                  '2888790':'SSt_Vrain_at_Berry_Rdg_',
                  '2889124':'Rowena_Left_Hand',
                  '2888748':'SSt_Vrain_Little_Narrows',
                  '13584':'Big_Thompson_Estes',
                  '2889214':'Boulder_Creek_75th',
                  '12932':'Big_Thompson_Loveland'}
indir = os.getcwd() + os.sep + 'QIN_SQIN' + os.sep
summary_dir = os.getcwd() + os.sep + 'statQIN_NWM' + os.sep
start = 1993
end = 2016
years = range(start,end+2,1) # process years defined by start/end (+2 buffer for calculating totals)
months = range(3,11,1) # process months Mar-Oct
flow_ranges=[[0.01,5.0],[5.0,20.0],[20.0,50.0],[50.0,100.0],[100.0,200.0],[200.0,300.0],[300.0,500.0],[500.0,1000.0],[1000.0,5000.0],[5000.0,10000.0]]
fill_data = True            # option to use obs data with filled gaps in missing hourly data
data_group = '1hr'              # aggregate data time window
############ End User input ##################################################

if fill_data == True:
    indir = indir + data_group + '_filled' + os.sep
    summary_dir = summary_dir + data_group + '_filled' + os.sep
else:
    indir = indir + data_group + '_nofill' + os.sep
    summary_dir = summary_dir + data_group + '_nofill' + os.sep

for comid in comids:
    csv_files = os.listdir(indir)
    if comid + '_SQIN_QIN.csv' in csv_files:
        print('Processing - ' + comid)
        summary_out = open(summary_dir + os.sep + data_group + '_statqin_summary_' + comid + '_' + comid_name[comid] + '.csv','w')
        summary_out.write(comid_name[comid] + '\n')
        summary_out.write('Year' + ',' + 'Timestep' + ',' + '#obs' + ',' + 'Avg QIN (cfs)' + ',' + 'Avg SQIN (cfs)' + ',' + 'Bias (cfs)' + ',' + '% Bias' + ',' 
                        + 'MAE (cfs)' + ',' + 'RMSE (cfs)' + ',' + 'Corr Coef' + ',' + 'Nash Sut\n')

        csv_read = open(indir + os.sep + comid + '_SQIN_QIN.csv','r')
        ###### tab delimitted CHPS QIN dishcarge CSV file into panda arrays ###########
        df_all = pd.read_csv(csv_read,header = 1, parse_dates=[0],names=['date','QIN','SQIN'],na_values=[' ','','NA','na',-999,'-999'])
        ### parse flow data by years
        for year in years:
            print('Processing: ' + str(year))
            test = df_all[(df_all['date'] >= str(year)+'-01-01') & (df_all['date'] <= str(year) +'-12-31')]
            if year == end+1: # this is used to process stats for the full period
                test = df_all
                year = 'Avg'
            if len(test) > 0:                                   # check that date range has some data
                date_qin = test['date'].tolist()                  # convert to list (indexible)
                timestep = int((date_qin[1] - date_qin[0]).total_seconds()/3600)  # calculate the timestep between the data points
                all_qin = test['QIN'].tolist()
                all_sqin = test['SQIN'].tolist()
                sqin = []; qin = []; count = 0                 # read the data into a dictionary (more efficient processing)
                for each in all_qin:
                    if float(each) >= 0.01 and str(each) != 'nan' and float(all_sqin[count]) >= 0:          # ignore data less than 0          
                        qin.append(each)
                        sqin.append(all_sqin[count])
                    count += 1
                csv_read.close() 
                    
                ###### calculate stats #####
                print('Calculating statistics...')
                if len(qin) > 0 and len(sqin) > 0:
                    avg_qin = "%.2f" %  np.mean(qin); avg_sqin = "%.2f" % np.mean(sqin)
                    bias = "%.2f" % calc_errors.pct_bias(qin,sqin)[0]
                    pbias = "%.2f" % calc_errors.pct_bias(qin,sqin)[1]
                    mae = "%.2f" %calc_errors.ma_error(qin,sqin)
                    rmse = "%.2f" %calc_errors.rms_error(qin,sqin)[0]
                    corr_coef = calc_errors.corr_coef(qin,sqin)
                    nash_sut = calc_errors.nash_sut(qin,sqin)
                else:
                    pbias=bias=mae=corr_coef=nash_sut=avg_qin=avg_sqin=rmse= '#N/A'
                
                ###### write summary to output csv #######
                summary_out.write(str(year) + ',' + str(timestep) + ',' + str(len(qin)) + ',' + str(avg_qin) + ',' + str(avg_sqin) + ',' + str(bias) + ',' 
                            + str(pbias) + ',' + str(mae) + ',' + str(rmse) + ',' + str(corr_coef) + ',' + str(nash_sut) + ',' + '\n')
            else:
                print('No data available for year...')
                
        #######################################################################        
        ### parse flow data by months
        summary_out.write('\n' + 'Month' + ',' + 'Month#' + ',' + '#obs' + ',' + 'Avg QIN (cfs)' + ',' + 'Avg SQIN (cfs)' + ',' + 'Bias (cfs)' + ',' + '% Bias' + ',' 
                        + 'MAE (cfs)' + ',' + 'RMSE (cfs)' + ',' + 'Corr Coef' + ',' + 'Nash Sut\n')
        for month in months:
            print('Processing: ' + calendar.month_abbr[month])
            month_test = df_all
            if len(test) > 0:
                date_qin = month_test['date'].tolist()                  # convert to list (indexible)
                all_qin = month_test['QIN'].tolist()
                all_sqin = month_test['SQIN'].tolist()
                sqin = []; qin = []; count = 0                 # read the data into a dictionary (more efficient processing)
                for step in date_qin:
                    if step.month == month:  ## check that datetime is equal to processing month
                         ## ignore missing data and obs data equal to 0
                        if float(all_qin[count]) >= 0.01 and str(all_qin[count]) != 'nan' and float(all_sqin[count]) >= 0:          
                            qin.append(all_qin[count])
                            sqin.append(all_sqin[count])
                    count += 1
                csv_read.close() 
                    
                ###### calculate stats #####
                print('Calculating statistics...')
                if len(qin) > 0 and len(sqin) > 0:
                    avg_qin = "%.2f" %  np.mean(qin); avg_sqin = "%.2f" % np.mean(sqin)
                    bias = "%.2f" % calc_errors.pct_bias(qin,sqin)[0]
                    pbias = "%.2f" % calc_errors.pct_bias(qin,sqin)[1]
                    mae = "%.2f" %calc_errors.ma_error(qin,sqin)
                    rmse = "%.2f" %calc_errors.rms_error(qin,sqin)[0]
                    corr_coef = calc_errors.corr_coef(qin,sqin)
                    nash_sut = calc_errors.nash_sut(qin,sqin)
                else:
                    pbias=bias=mae=corr_coef=nash_sut=avg_qin=avg_sqin=rmse= '#N/A'
                
                ###### write summary to output csv #######
                summary_out.write(calendar.month_abbr[month] + ',' + str(month) + ',' + str(len(qin)) + ',' + str(avg_qin) + ',' + str(avg_sqin) + ',' + str(bias) + ',' 
                            + str(pbias) + ',' + str(mae) + ',' + str(rmse) + ',' + str(corr_coef) + ',' + str(nash_sut) + ',' + '\n')
            else:
                print('No data available for month...')
                summary_out.write(calendar.month_abbr[month] + ',' + str(month) + '\n')
                
        #######################################################################
        ### parse by flow ranges
        summary_out.write('\n' + 'Flow Range Analysis\n')
        summary_out.write('Min Flow (cfs)' + ',' + 'Max Flow (cfs)' + ',' + '#obs' + ',' + 'Avg QIN (cfs)' + ',' + 'Avg SQIN (cfs)' + ',' + 'Bias (cfs)' + ',' + '% Bias' + ',' 
                        + 'MAE  (cfs)' + ',' + 'RMSE (cfs)' + ',' + 'Corr Coef' + ',' + 'Nash Sut\n')
        for flow_range in flow_ranges:
            print('Processing: flow range ' + str(flow_range[0]) + ' - ' + str(flow_range[1]))
            flow_test = df_all[(df_all['QIN'] >= flow_range[0]) & (df_all['QIN'] < flow_range[1])]
            if len(flow_test) > 0:                                      # check dataframe has data
                date_qin = flow_test['date'].tolist()                   # convert to list (indexible)
                all_qin = flow_test['QIN'].tolist()
                all_sqin = flow_test['SQIN'].tolist()
                sqin = []; qin = []; count = 0                          # read the data into a dictionary (more efficient processing)
                for each in all_qin:
                    if float(each) >= 0 and str(each) != 'nan' and float(all_sqin[count]) >= 0:          # ignore data less than 0          
                        qin.append(each)
                        sqin.append(all_sqin[count])
                    count += 1
                csv_read.close() 
                    
                ###### calculate stats #####
                print('Calculating statistics...')
                if len(qin) > 0 and len(sqin) > 0: # checks that not all data is missing
                    avg_qin = "%.2f" %  np.mean(qin); avg_sqin = "%.2f" % np.mean(sqin)
                    bias = "%.2f" % calc_errors.pct_bias(qin,sqin)[0]
                    pbias = "%.2f" % calc_errors.pct_bias(qin,sqin)[1]
                    mae = "%.2f" %calc_errors.ma_error(qin,sqin)
                    rmse = "%.2f" %calc_errors.rms_error(qin,sqin)[0]
                    corr_coef = calc_errors.corr_coef(qin,sqin)
                    nash_sut = calc_errors.nash_sut(qin,sqin)
                else:
                    pbias=bias=mae=corr_coef=nash_sut=avg_qin=avg_sqin=rmse= '#N/A'
                
                ###### write summary to output csv #######
                summary_out.write(str(flow_range[0]) + ',' + str(flow_range[1]) + ',' + str(len(qin)) + ',' + str(avg_qin) + ',' + str(avg_sqin) + ',' + str(bias) + ',' 
                            + str(pbias) + ',' + str(mae) + ',' + str(rmse) + ',' + str(corr_coef) + ',' + str(nash_sut) + ',' + '\n')
            else:
                print('No data available for flow range...')
                summary_out.write(str(flow_range[0]) + ',' + str(flow_range[1]) + '\n')
                    
        summary_out.close()
print 'Finished!'
print 'CHECK UNITS IN ORIGINAL DATA!!!'
## calculate script runtime length       
pend = datetime.datetime.now()
runtime = pend-pstart
print('Script runtime: ' + str(runtime.seconds) + ' seconds')