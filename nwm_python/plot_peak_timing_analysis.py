#Created on January 6, 2015
#@author: rspies
# Python 2.7
# This script plots the mean pbias for the period surrounding an event of a specified magnitude.
# Numerous events are chosen at each basin based on the criteria that eliminate smaller events
# and events that may be impacted by multiple events.

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import numpy.ma as ma
maindir = os.getcwd()

############################### User input ###################################
##############################################################################
##### IMPORTANT: Make sure to call the correct CHPS .csv output columns ######
#####    and specify the calibration period in next section 
basin_ids = [] # run individual basin(s) -> otherwise leave empty []
variable = '1hr_filled' # 'QME_SQME' or 'QIN_SQIN'
ignore_basins = []
resolution = 350 #350->(for report figs) 100->for CHPS fx help tab display (E19)
plt.ioff()  #Turn interactive plot mode off (don't show figures)
yr_start  = 1999; yr_end = 2016 # specify the first and last year to analyze
csv_loc = os.getcwd() + os.sep + 'QIN_SQIN' + os.sep + variable + os.sep
out_dir = os.getcwd() + os.sep + 'QIN_SQIN' + os.sep + 'peak_analysis_plots' +  os.sep + variable + os.sep 
out_list =  out_dir + 'peak_event_analysis.txt'
comid_names = {'2888976':'JamesCreek_Jamestown',
                  '2888956':'Lower_Lefthand',
                  '2889346':'Orodell_Fourmile_Creek',
                  '2888790':'SSt_Vrain_at_Berry_Rdg_',
                  '2889124':'Rowena_Left_Hand',
                  '2888748':'SSt_Vrain_Little_Narrows',
                  '13584':'Big_Thompson_Estes',
                  '2889214':'Boulder_Creek_75th',
                  '12932':'Big_Thompson_Loveland'}
#comid_names = {'2888976':'JamesCreek_Jamestown'}
################  Define the corresponding column of data in the csv file  #################
write_date_list = open(out_list,'w') 
if basin_ids == []:
    csv_files = os.listdir(csv_loc)
    for csv_file in csv_files:
        if csv_file.endswith(".csv"):
            basin_num = csv_file.split('_')[0]
            if basin_num in comid_names:
                basin_ids.append(basin_num)
#basin_ids = ['ASCW1'] # <- use this to run individual basin
if '1hr' in variable:
    step = 1 # data time step
    period = 10
if '6hr' in variable:
    step = 6 # data time step
    period = 3
############################################################            
###########################################################
for basin_id in basin_ids:
    print basin_id
    write_date_list.write(basin_id + '\t')
    file_read = open(csv_loc + basin_id + '_SQIN_QIN.csv', 'r') 

    ###### tab delimitted CHPS calibrated AND Observed dishcarge text file into panda arrays ###########
    ### replaces hour time stamp with zero to create a mean daily value -> match obs data
    test = pd.read_csv(file_read,sep=',',skiprows=1,
            usecols=[0,1,2],parse_dates=['date'],names=['date', 'OBS', 'SQIN'])
    file_read.close()
    ### assign column data to variables
    print 'Populating data arrays for calibrated dishcarge... and converting to daily values'
    
    date_calib = test['date'].tolist()                  # convert to list (indexible)
    SQIN = test['SQIN'].tolist()
    QIN = test['OBS'].tolist()
    date_QIN = []; date_SQIN = []; new_date = []; count = 0                        # read the data into a dictionary (more efficient processing)
    for each_day in date_calib:
        if yr_start <= int(each_day.year) <= yr_end:
            if float(SQIN[count]) >= 0:# or float(QIN[count]) >= 0:          # ignore periods with sim and obs missing data (less than 0) 
                date_SQIN.append(SQIN[count])
                date_QIN.append(float(QIN[count]))
                new_date.append(each_day)
        count += 1
    
    avg_flow = np.nanmean(date_QIN)
    std_flow = np.nanstd(date_QIN)
    print 'Mean flow: ' + str(avg_flow)
    if avg_flow == np.nan: # check if data is available 
        print 'No observed data available... skipped basin'
    else: # check if data is available 
        thresh = int(round(avg_flow + (3*std_flow),0))
    #    if 0 <= avg_flow <= 10:
    #        thresh = 40
    #    elif 10 <= avg_flow <= 20:
    #        thresh = 60
    #    elif 20 <= avg_flow <= 40:
    #        thresh = 120
    #    elif 40 <= avg_flow <= 60:
    #        thresh = 200
    #    elif 60 <= avg_flow <= 100:
    #        thresh = 250
    #    elif 100 <= avg_flow <= 200:
    #        thresh = 300
    #    else:
    #        thresh = 400   
         
        #### iterate through obs streamflow data and pull out events that meet thresh criteria ####       
        # create blank arrays for future calcs
        obs_matrix = np.empty((0,(period*2+1)),dtype=float)
        sim_matrix = np.empty((0,(period*2+1)),dtype=float)
        
        actual_index = 0; tot_events = 0
        for obs in date_QIN:
            #### find streamflow values > than set threshold (isolate larger events)
            #### also ignore peak events at the very begining and end of analysis period 
            if obs > thresh and actual_index >= period and actual_index < (len(date_QIN) - period):
                #### find event peak within the window period specified above
                #### e.g. value at time1 must be > all values within +- 5 time steps
                if obs >= max(date_QIN[actual_index + 1:actual_index + period]) and obs > max(date_QIN[actual_index - period: actual_index]):
                    #print obs
                    event = np.array(date_QIN[actual_index-period:(actual_index+period+1)])
                    #event = ma.masked_less(event,6)
                    event_sim = np.array(date_SQIN[actual_index-period:(actual_index+period+1)])
                    list_index = 0
                    #### perform check to see if there are any dips in hydrograph indicating multiple events impacting the hydrograph
                    for each in event:
                        if list_index != 0:
                            if each > thresh:
                                status = 'ok' 
                            elif max(event[list_index:]) > thresh and max(event[0:list_index]) > thresh:
                                status = 'nogo'
                                break
                        list_index += 1
                    #print status
                    if status == 'ok':
                        obs_matrix = np.vstack((obs_matrix,event))
                        obs_matrix = ma.masked_less(obs_matrix,1)
                        sim_matrix = np.vstack((sim_matrix,event_sim))
                        tot_events += 1
                        print new_date[actual_index]
                        write_date_list.write(str(new_date[actual_index]) + ', ')
            actual_index += 1
        print 'Number of events analyzed: ' + str(tot_events)
        write_date_list.write('\n')
        
        # matrix calculations
        matrix_pbias = ((sim_matrix - obs_matrix)/obs_matrix)*100
        array_pbias = np.mean(matrix_pbias, axis=0)
        
        # column mean for obs and sim
        obs_mean = []; sim_mean = []
        for col in obs_matrix.T:
            avg_obs = col.mean()
            obs_mean.append(avg_obs)
        for col in sim_matrix.T:
            avg_sim = col.mean()
            sim_mean.append(avg_sim)
    
        # create x array to use for labels (6hr or 1hr timestep)
        x = range(period*-1,period+1,1)
        x_labels = []
        for each in x:
            x_labels.append(each*step)
            
        ############################# create plot(s) ##########################################
        #######################################################################################        
        ### create image: aspect set to auto (creates a square plot with any data)
        ### vmin->sets values less than 0 to missing
        #fig, ax1 = plt.subplots()
        fig = plt.figure()
        fig.subplots_adjust(hspace=.2)
        ax1 = fig.add_subplot(211)
        if step == 1:
            ax1.bar(x_labels, array_pbias, color='b', width=0.9,align='center')
        if step == 6:
            ax1.bar(x_labels, array_pbias, color='b', width=4)#,align='center')
            
        #### axis properties ###
        ax1.tick_params(axis='y', which='major', labelsize=8)
        ax1.tick_params(axis='x', which='major', labelsize=7)
        
        #### axis adjustments ####
        ax1.xaxis.grid(b=True, which='major', color='0.6', linestyle='--',linewidth='0.5')
        ax1.yaxis.grid(b=True, which='major', color='0.6', linestyle='--',linewidth='0.5')
    
        #### modify xaxis ticks to daily ticks
        if step == 6 or step == 24:
            daily_ticks = np.arange((period*-step)-24,(period*step)+48,24)
            if 0 not in daily_ticks:
                daily_ticks = np.arange((period*-step)-12,(period*step)+36,24)
        if step == 1:
            daily_ticks = np.arange((period*-step),(period*step)+1,1)
        plt.xticks(daily_ticks)
        
        #### plot vertical line at 0 (time of peak)
        min_yax = (ax1.axis())[2]
        max_yax = (ax1.axis())[3]
        ax1.set_autoscale_on(False) # have to turn off autoscale otherwise xlims change
        plt.plot((0,0),(min_yax,max_yax),'r-',linewidth = '2.0')
        plt.plot((min(daily_ticks),max(daily_ticks)),(0,0),'k-',linewidth = '1.25')
        
        #### axis and title properties ###
        #ax1.set_xlabel('Time from Peak (hrs)',fontsize=8)
        plt.xlim(min(x)-step,max(x)+step)
        ax1.set_ylabel('Simulated Mean Percent Bias (%)',fontsize=7)
        ax1.set_title(comid_names[basin_id] + ': ' + str(yr_start) + '-' + str(yr_end) + ' (analyzed ' + str(tot_events) + ' events >= ' + str(thresh) + ' CMS)',fontsize=11)
        ##################################################################
        ### obs/sim mean
        ax2 = fig.add_subplot(212)
        # plot spaghetti of all events
        row_count = 0; corr_list = []
        for row in sim_matrix:
            corr_list.append(np.corrcoef(row,obs_matrix[row_count])[1][0])
            row_count += 1
            if row_count == 1:
                ax2.plot(x_labels,row,lw='0.1',color='blue', label='simulated events')
            else:
                ax2.plot(x_labels,row,lw='0.1',color='blue')
        ax2.plot(x_labels,obs_mean,'orange',lw=2,label='observed mean')
        ax2.plot(x_labels,sim_mean,'blue',lw=2,label='simulated mean')
        
        #### axis adjustments ####
        ax2.xaxis.grid(b=True, which='major', color='0.6', linestyle='--',linewidth='0.5')
        ax2.yaxis.grid(b=True, which='major', color='0.6', linestyle='--',linewidth='0.5')
        #### axis properties ###
        ax2.tick_params(axis='y', which='major', labelsize=8)
        ax2.tick_params(axis='x', which='major', labelsize=7)
        
        #### modify xaxis ticks to daily ticks
        plt.xticks(daily_ticks)
        #### plot vertical line at 0 (time of peak)
        min_yax = (ax2.axis())[2]
        max_yax = (ax2.axis())[3]
        ax2.set_autoscale_on(False) # have to turn off autoscale otherwise xlims change
        plt.plot((0,0),(min_yax,max_yax),'r-',linewidth = '2.0')
        
        ### statistics box
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax2.text(0.85, 0.95, 'Corr Coef: ' + str("%.2f" % np.average(corr_list)), fontsize=8, transform=ax2.transAxes,
                verticalalignment='top', bbox=props)
        
        #### axis and title properties ###
        plt.xlim(min(x)-step,max(x)+step)
        ax2.set_xlabel('Time from Peak (hrs)',fontsize=8)
        ax2.set_ylabel('Streamflow (CMSD)',fontsize=7)
        ax2.legend(loc="upper left",shadow=True,fontsize=6)
    
        fig_out = out_dir + basin_id + '_' + comid_names[basin_id] + '_peak_analysis.png'
        plt.savefig(fig_out, dpi=resolution, bbox_inches='tight')
        plt.clf()
        #print 'Figure saved to: ' + out_dir  + 'correlation_plots\\' + basin_id + '_daily_correlation.png'
write_date_list.close()
print 'Finished!'