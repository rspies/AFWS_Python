# created by Ryan Spies 
# 7/18/2017
# Python 2.7
# Bokeh updated to 0.12.6
# Description: generate an interactive plot
# Output to html file for viewing interactive plot
# Pandas Resample function: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.resample.html
# Pandas Rolling function: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.rolling.html

from bokeh.plotting import Figure, output_file, save #importing figure (lower case f) results in increasing file size with each plot
from bokeh.models import Range1d, DatetimeTickFormatter, HoverTool, BoxAnnotation, DataRange1d
from bkcharts import Bar, Area
from bokeh.models.glyphs import VBar
from bokeh.layouts import column, gridplot
from bokeh.palettes import Set1
from bokeh.models import Label

import os
from datetime import timedelta
import pandas as pd
import collections
import datetime
import numpy as np
import precip_bin_data ## my module for binning precip

os.chdir("..")
maindir = os.getcwd() + os.sep + 'data' + os.sep
################## User Input ########################
#min_date = datetime.datetime(2013,1,1); max_date = datetime.datetime(2017,7,1); 
min_date = datetime.datetime(2013,9,11,18); max_date = datetime.datetime(2013,9,12,18)

plot_type = 'rolling'           # choices: 'interval' or 'rolling'
flow_stg = 'stage'              # choices: 'stream' for streamflow or 'stage' for gauge height
precip_site_region = 'James_Creek' # choices: 'James_Creek' is the 7 thiessen gages and 'James_Creek_extra' is 7 gages plus 4 extra
max_win = '120'                 # choices: '120','360', or '1440' -> these are the upper bounds for the grouped alarm durations
output_date_list = 'false'      # print output of all alarm dates to txt file - choices: 'true' or 'false'
pbin = '5'                      # precip bin time in minutes
thresh_type = 'Modified'        # choices: 'Modified' (focused on 2013 exceed) or 'UDFCD' (default)
######################################################
if thresh_type == 'Modified':
    roll_wins = [4320,1440,720,360,180,120,60,10] # window for rolling accumulation (minutes) # 10,60,120,180,360,720,1440,4320
if thresh_type == 'UDFCD':
    roll_wins = [1440,360,120,60,10]         # window for rolling accumulation (minutes) # 10,60,120,360,1440

if plot_type == 'rolling':
    thresh ={'10':0.5, '30':0.75,'60':1.0,'120':1.5,'180':2.0,'360':3.0,'720':4.0,'1440':5.0,'4320':10.0}
    sat_thresh = {'60':0.5,'120':0.75,'180':0.75,'1440':2.0,'4320':3.5}
######################################################
udfcd_thresh ={'10':0.5,'60':1.0,'120':3.0,'360':5.0,'1440':5.0,'4320':10.0}
jc_stg_thresh = {'bankfull':0.88,'minor':3.0,'moderate':3.9,'major':5.7}
precip_names = {'4180':'Gold Lk','4850':'Porp Mt','4190':'Slaught','4220':'Flings','4270':'Cann Mt','4710':'Ward','4770':'Cal Rnc',
                '4150':'Gold Hl','4240':'Sunset','4160':'Sunshine','4230':'Gold Ag'}
count = 0
#############################################################################
### STREAMFLOW DATA ###    
## Define the steamflow/stage data file 
input_dir = maindir + os.sep + 'James_Creek_streamflow_data' 
if flow_stg == 'stream':
    input_file = input_dir + os.sep + 'onerain_JamesCreek_Jamestown_10017_Flow_rate_7a.txt'
    ptitle = ' Inst Streamflow (CFS)  w/ Rainfall Alert Flags'; yax = 'Streamflow (CFSD)'; units = 'cfs'
if flow_stg == 'stage':
    input_file = input_dir + os.sep + 'ALERT2_sensor_7_15861_2_EventData.csv'
    ptitle = ' Inst Stream Stage (FT) w/ Rainfall Alert Flags'; yax = 'Stage (FT)'; units = 'ft'

print input_file
basin = 'James Creek'
site_num = input_file.split('_')[-4]
read_file = open(input_file, 'r')
test = pd.read_csv(read_file,sep=',',skiprows=1,
            usecols=[0,2],parse_dates=['date'],names=['date', 'OBS'])

# remove bad data points (JC above 8ft stage)          
if flow_stg == 'stage':
    test = test[test.OBS < 8.0]

### trim the data to the desired date range    
test = test[(test.date > min_date) & (test.date < max_date)]

### assign column data to variables
print 'Populating data arrays for obs streamflow...'

date_data_raw = test['date'].tolist()  # convert to list (indexible)
discharge_raw = test['OBS'].tolist()
read_file.close()

# find min/max dates
#max_date = max(date_data_raw);min_date = min(date_data_raw)

# fill missing data with nan (search daily)
dictionary = collections.OrderedDict(dict(zip(date_data_raw, discharge_raw)))
check_dates = []
for each in date_data_raw:
    check_dates.append(each.date())
date_iter = min_date.date(); iter_step = timedelta(days=1)
while date_iter < max_date.date():
    if date_iter not in check_dates:
        dictionary[datetime.datetime(date_iter.year,date_iter.month,date_iter.day,12,0)]=float('nan')
    date_iter += iter_step
sort_data = collections.OrderedDict(sorted(dictionary.items()))
date_data = sort_data.keys(); discharge = sort_data.values()

# find max flow for plotting limit
max_find = []
max_find.append(np.nanmax(discharge))
max_Q = int(max(max_find)) + 1

# create a new plot
# log plot add this:  y_axis_type="log"
print 'Creating streamflow bokeh plot...'
p1 = Figure(
   tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
   y_range = DataRange1d(start=0,end=max_Q), x_range = Range1d(start=min_date,end=max_date),
   title=basin + ptitle, x_axis_type="datetime",
   x_axis_label='Date', y_axis_label=yax,plot_width=1400, plot_height=400, lod_factor=20, lod_threshold=50
)                                       #presentation: plot_width=2000

### OneRain default JC stage thresholds
stg_box_major = BoxAnnotation(top=8, bottom=jc_stg_thresh['major'], fill_color='purple', fill_alpha=0.25)
p1.add_layout(stg_box_major)
stg_box_mod = BoxAnnotation(top=jc_stg_thresh['major'], bottom=jc_stg_thresh['moderate'], fill_color='red', fill_alpha=0.25)
p1.add_layout(stg_box_mod)
stg_box_minor = BoxAnnotation(top=jc_stg_thresh['moderate'], bottom=jc_stg_thresh['minor'], fill_color='orange', fill_alpha=0.25)
p1.add_layout(stg_box_minor)
stg_box_bf = BoxAnnotation(top=jc_stg_thresh['minor'], bottom=jc_stg_thresh['bankfull'], fill_color='yellow', fill_alpha=0.15)
p1.add_layout(stg_box_bf)

### Add text annotation for the flood levels
text_bf = Label(x=55, y=jc_stg_thresh['bankfull'], x_units='screen', y_units='data', text="Bankfull",render_mode='canvas',level='glyph',x_offset=10)
text_min = Label(x=55, y=jc_stg_thresh['minor'], x_units='screen', y_units='data', text="Minor",render_mode='canvas',level='glyph',x_offset=10)
text_mod = Label(x=55, y=jc_stg_thresh['moderate'], x_units='screen', y_units='data', text="Moderate",render_mode='canvas',level='glyph',x_offset=10)
text_maj = Label(x=55, y=jc_stg_thresh['major'], x_units='screen', y_units='data', text="Major",render_mode='canvas',level='glyph',x_offset=10)
p1.add_layout(text_bf); p1.add_layout(text_min); p1.add_layout(text_mod); p1.add_layout(text_maj)

# hover tool
hover = HoverTool(tooltips=[
            ("Flow",'@y ' + units)],
            mode='vline') #("Date","@x")],           
p1.add_tools(hover)

### axis font size 
p1.title.text_font_size = "19pt"
p1.xaxis.axis_label_text_font_size = "19pt"
p1.xaxis.major_label_text_font_size = "14pt"
p1.yaxis.axis_label_text_font_size = "19pt"
p1.yaxis.major_label_text_font_size = "14pt"
#p1.toolbar_location = None

p1.xaxis.formatter=DatetimeTickFormatter(
minsec=["%Y-%m-%d %H:%M:%S"],
minutes=["%Y-%m-%d %H:%M"],
hourmin=["%Y-%m-%d %H:%M"],
hours=["%Y-%m-%d %H:%M"],
days=["%Y-%m-%d"],
months=["%Y-%m-%d"],
years=["%Y-%m"],)

read_file.close()

###################################################################################
#### PRECIP DATA #####
input_dir = maindir + os.sep + precip_site_region + '_precip_sites'
d24 = pd.DataFrame(); d72 = pd.DataFrame()  
for roll_win in roll_wins:
    print_dates = []; dts_dict={} # used for outputing list of all alarm date/times
    if output_date_list == 'true':
        write_dates=open(maindir + os.sep + 'interactive_plots' + os.sep + flow_stg + '_precip_alarm' + os.sep +  str(min_date.date()) + '_' + str(max_date.date()) + os.sep + 'print_alarms' + os.sep + precip_site_region.replace('_',"") + '_stream_precip_' +pbin + 'min_' + plot_type + '_' + str(roll_win) + '_' + thresh_type + '_sat_alarms.txt','w')
        write_dates.write(str(roll_win)+' Minute Alarms\n')    
    for input_file in os.listdir(input_dir+ os.sep):
        in_file = input_dir + os.sep + input_file    
        site = input_file.split('_')[1]
        site_name = precip_names[site]
        print '\n'
        print site_name + ' -> ' + input_file
        df = precip_bin_data.bin_precip(in_file,pbin)
        #df['tooltip'] = [x.strftime("%Y-%m-%d %H:%M:%S") for x in df['date']]
        
        ### use the rolling window calculation to generate precip time series
        if plot_type == 'rolling':
            print("Performing rolling accumulation calculation for window: " + str(roll_win))
            df['rolling'] = df.precip.rolling(window=roll_win,freq='min',min_periods=1,closed='right').sum()
                
        ### trim the data to the desired date range
        df = df[(df.date > min_date) & (df.date < max_date)]
        
        # remove non-number instances 
        da=df[np.isfinite(df['rolling'])]
        # remove non-alarm data points (below defined threshold) 
        if thresh_type == 'Modified':
            if roll_win == 4320:
                d72[site] = da['rolling']                                                   # create a copy of full 72-hour df
                d72['date'] = df['date']
                da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)      # drop all instances below the 3-day normal static alert threshold
            elif roll_win == 1440:
                d24[site] = da['rolling']                                                   # create a copy of full 24-hour df
                d24['date'] = df['date']
                #dm.drop(dm[dm['rolling'] < sat_thresh[str(roll_win)]].index, inplace=True) # drop all instances below the 1-day saturation threshold (2.0in)
                da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)      # drop all instances below the 1-day normal alert threshold
            elif roll_win <= 180 and roll_win > 10:
                ##### calcs for sat threshold exceedance
                ds = da.copy()                                                              # create a copy of full dataframe for current roll_win
                #dt = da.copy()                                                             # orig copy for debugging
                                                            
                ## calc 24 and 72 hour sat timeseries (subtraction from window)               
                dsub24 = d24.copy()                                                           # create a second copy of the 24-hr df to perform subtraction on
                dsub72 = d72.copy()                                                           # create a second copy of the 72-hr df to perform subtraction on
                print('Len 24dsub: ' + str(len(dsub24)))
                dsub24[str(site)+'sub'] = d24[site].subtract(ds['rolling'])                   # create a new df column that subtracts the current roll_win from the 24hr accum -> estimate for sat conditions prior to roll_win
                dsub24.drop(dsub24[dsub24[str(site)+'sub'] < sat_thresh[str(1440)]].index, inplace=True)  # drop all instances below the 1-day saturation threshold (2.0in)
                dsub72[str(site)+'sub'] = d72[site].subtract(ds['rolling'])                   # create a new df column that subtracts the current roll_win from the 72hr accum -> estimate for sat conditions prior to roll_win
                dsub72.drop(dsub72[dsub72[str(site)+'sub'] < sat_thresh[str(4320)]].index, inplace=True)  # drop all instances below the 3-day saturation threshold (4.0in)

                if len(ds) > 0:
                    print('Mod Len 24dsub: ' + str(len(dsub24)) + ' - ' + str(min(dsub24['date'])))
                print('Len ds: ' + str(len(ds)) + ' - ' + str(min(ds['date'])))
                
                ds['sat24'] = (ds['date'].isin(dsub24['date'])).astype(int)                 # add a true/false (convert to int) column of instances where 1-day saturation thresh is exceeded
                ds['sat72'] = (ds['date'].isin(dsub72['date'])).astype(int)                 # add a true/false (convert to int) column of instances where 3-day saturation thresh is exceeded                 
                ds['sat'] = ds['sat24'] + ds['sat72']                                       # add int columns for sat24 true/false and sat72 true/false
                #dt = ds.copy()                 
                ds.drop(ds[ds['rolling'] < sat_thresh[str(roll_win)]].index, inplace=True)  # drop all instances of values below the reduced "sat conditions" theshold
                ds.drop(ds[ds['sat'] < 1].index, inplace=True)                              # drop all instances of periods that do not meet the 1-day and 3-day saturated thresh (<1)
                if len(ds) > 0:
                    print('Mod Len ds: ' + str(len(ds)) + ' - ' + str(min(ds['date'])))
                ## calculate static thresh instances
                da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)      # separate df for dropping instances below normal static threshold

            else:
                da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)

        if thresh_type == 'UDFCD':
            da.drop(da[da['rolling'] < udfcd_thresh[str(roll_win)]].index, inplace=True)
        
        
        print 'Add data to bokeh plot...'
    
        ### add some renderers
        ### Add a transparent bar for each rainfall exceedence instance
        if max_win == '120':        
            if roll_win <= 120:
                p1.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=10, color="green", line_alpha=0,alpha=0.08) #da['rolling'
                if roll_win > 10:
                    p1.vbar(x=ds['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=10, color="blue", line_alpha=0,alpha=0.08) #da['rolling'
  
        if max_win == '360':
            if roll_win > 120 and roll_win <=360:
                p1.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=10, color="orange", line_alpha=0,alpha=0.08) #da['rolling'
                if roll_win == 180:
                    p1.vbar(x=ds['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=10, color="blue", line_alpha=0,alpha=0.08) #da['rolling'


        if max_win == '1440':
            if roll_win > 360 and roll_win <=1440:
                p1.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=10, color="magenta", line_alpha=0,alpha=0.08)

#        elif roll_win <= 360:
#            p1.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=10, color="orange", line_alpha=0,alpha=0.08) #da['rolling'
#        else:
#            p1.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=10, color="magenta", line_alpha=0,alpha=0.08) #da['rolling'
        #p=Bar(df, values='precip', legend="top_right")
        count += 1
        
        ### add dates to a list to print out alarm instances
        print_dates+=(list(set(da['date'])))
        for dts in da['date']:                  # create dictionary of alarm datetimes with station_names
            if str(dts) in dts_dict:
                dts_dict[str(dts)].append(site_name)
            else:
                dts_dict[str(dts)] = [site_name]
        if 60 <= roll_win <= 180:               # add saturated threshold exceeded timestamps to list
            print_dates+=(list(set(ds['date'])))
            for dts in ds['date']:              # create dictionary of alarm datetimes with station_names
                if str(dts) in dts_dict:
                    dts_dict[str(dts)].append(site_name+'_sat')
                else:
                    dts_dict[str(dts)] = [site_name+'_sat']
            
    ### write out txt file with all unique time steps of alarms for each duration
    if output_date_list == 'true':
        write_dates.write('Total Alarms: ' + str(len(set(print_dates))) + '\n')
        for each in sorted(set(print_dates)):
            str1 = ','.join(dts_dict[str(each)])    # create a string with all stations in each datetime list
            write_dates.write(str(each) + ': ' + str1 + '\n')
        write_dates.close()

### plot observed stage data
p1.line(date_data, discharge, legend="Obs - " + yax.split()[0], name='Q', line_width=3, line_color = "black") 

# output to static HTML file
if plot_type == 'rolling':
    output_file(maindir + os.sep + 'interactive_plots' + os.sep + flow_stg + '_precip_alarm' + os.sep + str(min_date.date()) + '_' + str(max_date.date()) + os.sep +  'sat_alarms' + os.sep + precip_site_region.replace('_',"") + '_stream_precip_' +pbin + 'min_' + plot_type + '_all_alarms_' + thresh_type + '_criteria'+max_win+'.html')
# show the results
#show(p)
print 'Saving plot...'
save(p1)