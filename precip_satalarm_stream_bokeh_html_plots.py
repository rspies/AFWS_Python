# created by Ryan Spies 
# 9/18/2017
# Python 2.7
# Bokeh updated to 0.12.6
# Description: generate an interactive bokeh plot with streamflow line and rainfall alert bar overlays. 
# Uses conditional saturation calculations to produce saturation based threshold values.
# Key Features: Pandas dataframe calculations (drop, subract, isin); bokeh plot options
# Output to html file for viewing interactive plot
# Pandas Resample function: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.resample.html
# Pandas Rolling function: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.rolling.html

from bokeh.plotting import Figure, output_file, save #importing figure (lower case f) results in increasing file size with each plot
from bokeh.models import Range1d, DatetimeTickFormatter, HoverTool, BoxAnnotation, DataRange1d
#from bkcharts import Bar, Area
#from bokeh.models.glyphs import VBar
#from bokeh.layouts import column, gridplot
#from bokeh.palettes import Set1
from bokeh.models import Label

import os
from datetime import timedelta
import pandas as pd
import collections
import datetime
import csv
import numpy as np
import precip_bin_data ## my module for binning precip

os.chdir("..")
maindir = os.getcwd() + os.sep + 'data' + os.sep
pstart = datetime.datetime.now()
################## User Input ########################
#min_date = datetime.datetime(1999,1,1); max_date = datetime.datetime(2013,8,31)
#min_date = datetime.datetime(1999,1,1); max_date = datetime.datetime(2016,10,1)
#min_date = datetime.datetime(2013,9,1); max_date = datetime.datetime(2013,9,30);
#min_date = datetime.datetime(2013,10,1); max_date = datetime.datetime(2016,10,1); 
min_date = datetime.datetime(2013,9,11,12); max_date = datetime.datetime(2013,9,13,0)

plot_type = 'rolling'           # choices: 'interval' or 'rolling'
flow_stg = 'flow'              # choices: 'flow' for streamflow or 'stage' for gauge height
precip_site_region = 'James_Creek' # choices: 'James_Creek' is the 7 thiessen gages and 'James_Creek_extra' is 7 gages plus 4 extra
#max_win = '360'                 # choices: '120','360', or '1440' -> these are the upper bounds for the grouped alarm durations
output_date_list = 'true'      # print output of all alarm dates to txt file - choices: 'true' or 'false'
make_plot = 'true'             # option to generate a bokeh plot
pbin = '5'                      # precip bin time in minutes
thresh_type = 'Modified'           # choices: 'Modified' (focused on 2013 exceed) or 'UDFCD' (default)
alarm_type = 'sat_alarms'       # choices: 'sat_alarms' or 'static_alarms'
basin = 'James Creek'           # used for plot titles
test_name = 'mod2'
prec_stations = ['4180','4190','4220','4270','4710','4770','4850']
######################################################

if test_name == 'mod1':
    if thresh_type == 'Modified':
        roll_wins = [4320,1440,720,360,180,120,60,10]   # window for rolling accumulation (minutes) # 10,60,120,180,360,720,1440,4320
        thresh ={'10':0.5, '30':0.75,'60':1.0,'120':1.5,'180':2.0,'360':3.0,'720':4.0,'1440':5.0,'4320':10.0}
        sat_thresh = {'60':0.5,'120':0.75,'180':0.75,'1440':2.0,'4320':3.5}
    if thresh_type == 'UDFCD':
        roll_wins = [4320,1440,360,120,60,10]           # window for rolling accumulation (minutes) # 10,60,120,360,1440
        thresh ={'10':0.5,'60':1.0,'120':3.0,'360':5.0,'1440':5.0,'4320':10.0}
        sat_thresh = {'60':0.5,'120':0.75,'180':0.75,'1440':2.0,'4320':3.5}
if test_name == 'mod2':
    if thresh_type == 'Modified':
        roll_wins = [4320,1440,360,180,120,60,10]       # window for rolling accumulation (minutes) # 10,60,120,180,360,720,1440,4320
        thresh ={'10':0.5, '60':1.0,'120':1.75,'180':2.5,'360':3.0,'1440':5.0,'4320':10.0}
        sat_thresh = {'60':0.5,'120':0.75,'180':1.0,'1440':2.0,'4320':3.5}
    if thresh_type == 'UDFCD':
        roll_wins = [4320,1440,360,120,60,10]           # window for rolling accumulation (minutes) # 10,60,120,360,1440
        thresh ={'10':0.5,'60':1.0,'120':3.0,'360':5.0,'1440':5.0,'4320':10.0}
        sat_thresh = {'60':0.5,'120':0.75,'180':1.0,'1440':2.0,'4320':3.5}
######################################################
#udfcd_thresh ={'10':0.5,'60':1.0,'120':3.0,'360':5.0,'1440':5.0,'4320':10.0}
precip_names = {'4180':'Gold Lk','4850':'Porp Mt','4190':'Slaught','4220':'Flings','4270':'Cann Mt','4710':'Ward','4770':'Cal Rnc',
                '4150':'Gold Hl','4240':'Sunset','4160':'Sunshine','4230':'Gold Ag'}
count = 0
#############################################################################
### STREAMFLOW DATA ###    
## Define the steamflow/stage data file 
input_dir = maindir + os.sep + 'James_Creek_streamflow_data' + os.sep
if flow_stg == 'flow':
    jc_stg_thresh = {'bankfull':300,'minor':1252,'moderate':1785,'major':3000, 'ptop':3500, 'max_Q':3500} #obtained from Kate Malers email 9/26/17
    input_file = 'merge_onerain_JamesCreek_Jamestown_flow_1999_2017.csv' #'onerain_JamesCreek_Jamestown_10017_Flow_rate_7a.txt'
    ptitle = ' Inst Streamflow (CFS)  w/ Rainfall Alert Flags (' + thresh_type + ') ' + str(min_date.date()) + u"\u2013" + str(max_date.date()); yax = 'Streamflow (CFSD)'; units = 'cfs'
if flow_stg == 'stage':
    jc_stg_thresh = {'bankfull':0.88,'minor':3.0,'moderate':3.9,'major':5.7, 'ptop':12, 'max_Q':8} ## NOTE! These are for post 2013 JC gauge rating (see rating diff spreadsheet)
    input_file = 'ALERT2_sensor_7_15861_2_EventData.csv'
    ptitle = ' Inst Stream Stage (FT) w/ Rainfall Alert Flags (' + thresh_type + ') ' + str(min_date.date()) + u"\u2013" + str(max_date.date()); yax = 'Stage (FT)'; units = 'ft'

print input_file
### check if pickled df already exists
if input_file[:-4] in os.listdir(maindir + 'pickle_data' + os.sep + flow_stg):
    print('Found pickle df - importing...')
    test = pd.read_pickle(maindir + 'pickle_data' + os.sep + flow_stg + os.sep + input_file[:-4])
else:
    print('Reading flow/stage file...')
    read_file = open(input_dir + input_file, 'r')
    print('Parsing flow/stage file...')
    test = pd.read_csv(read_file,sep=',',skiprows=1, na_filter=True,
                usecols=[0,2],parse_dates=['date'],names=['date', 'OBS'])
    read_file.close()
test.dropna(inplace=True)


### remove bad data points (JC above 8ft stage)          
if flow_stg == 'stage':
    test = test[test.OBS < 8.0]

### trim the data to the desired date range    
test = test[(test.date > min_date) & (test.date < max_date)]

### assign column data to variables
print 'Populating data arrays for obs streamflow...'
date_data_raw = test['date'].tolist()  # convert to list (indexible)
discharge_raw = test['OBS'].tolist()

### find min/max dates
#max_date = max(date_data_raw);min_date = min(date_data_raw)

### fill missing data with nan (search raw data for missing hours)
print('Filling data gaps with n/a...')
dictionary = collections.OrderedDict(dict(zip(date_data_raw, discharge_raw)))
check_dates = []
for each in date_data_raw:
    check_dates.append(each.date()) #replace(minute=0,second=0)) ## create check list of dates + hours (drop min and sec)
date_iter = min_date; iter_step = timedelta(days=1)    ## set timedelta search interval to 1day or 1 hour 
while date_iter < max_date:
    if date_iter.date() not in check_dates:
        dictionary[datetime.datetime(date_iter.year,date_iter.month,date_iter.day,12,0)]=float('nan')
    date_iter += iter_step
sort_data = collections.OrderedDict(sorted(dictionary.items()))
date_data = sort_data.keys(); discharge = sort_data.values()

### find max flow for plotting limit
max_find = []
max_find.append(np.nanmax(discharge))
max_Q_find = int(max(max_find)) + 1
max_Q = max(max_Q_find,jc_stg_thresh['max_Q'])

### create a new plot
## log plot add this:  y_axis_type="log"
if make_plot == 'true':
    print 'Creating streamflow bokeh plot...'
    p1 = Figure(
       tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
       y_range = DataRange1d(start=0,end=max_Q), x_range = Range1d(start=min_date,end=max_date),
       title=basin + ptitle, x_axis_type="datetime",
       x_axis_label='Date', y_axis_label=yax,plot_width=1400, plot_height=500, lod_factor=20, lod_threshold=50
    )                                       #presentation: plot_width=2000
    
    ### OneRain default JC stage thresholds
    stg_box_major = BoxAnnotation(top=jc_stg_thresh['ptop'], bottom=jc_stg_thresh['major'], fill_color='purple', fill_alpha=0.25)
    p1.add_layout(stg_box_major)
    stg_box_mod = BoxAnnotation(top=jc_stg_thresh['major'], bottom=jc_stg_thresh['moderate'], fill_color='red', fill_alpha=0.25, line_dash='dashed',line_alpha=0.3,line_color='black')
    p1.add_layout(stg_box_mod)
    stg_box_minor = BoxAnnotation(top=jc_stg_thresh['moderate'], bottom=jc_stg_thresh['minor'], fill_color='orange', fill_alpha=0.25)
    p1.add_layout(stg_box_minor)
    stg_box_bf = BoxAnnotation(top=jc_stg_thresh['minor'], bottom=jc_stg_thresh['bankfull'], fill_color='yellow', fill_alpha=0.15, line_dash='dashed',line_alpha=0.3,line_color='black')
    p1.add_layout(stg_box_bf)
    
    ### Add text annotation for the flood levels
    text_bf = Label(x=95, y=jc_stg_thresh['bankfull'], x_units='screen', y_units='data', text="Bankfull",render_mode='canvas',level='glyph',x_offset=10)
    text_min = Label(x=95, y=jc_stg_thresh['minor'], x_units='screen', y_units='data', text="Minor",render_mode='canvas',level='glyph',x_offset=10)
    text_mod = Label(x=95, y=jc_stg_thresh['moderate'], x_units='screen', y_units='data', text="Moderate",render_mode='canvas',level='glyph',x_offset=10)
    text_maj = Label(x=95, y=jc_stg_thresh['major'], x_units='screen', y_units='data', text="Major",render_mode='canvas',level='glyph',x_offset=10)
    p1.add_layout(text_bf); p1.add_layout(text_min); p1.add_layout(text_mod); p1.add_layout(text_maj)
    
    ### hover tool
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
    ########################
    print 'Creating streamflow bokeh plot...'
    p2 = Figure(
       tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
       y_range = DataRange1d(start=0,end=max_Q), x_range = Range1d(start=min_date,end=max_date),
       title=basin + ptitle, x_axis_type="datetime",
       x_axis_label='Date', y_axis_label=yax,plot_width=1400, plot_height=500, lod_factor=20, lod_threshold=50
    )                                       #presentation: plot_width=2000
    
    ### OneRain default JC stage thresholds
    stg_box_major = BoxAnnotation(top=jc_stg_thresh['ptop'], bottom=jc_stg_thresh['major'], fill_color='purple', fill_alpha=0.25)
    p2.add_layout(stg_box_major)
    stg_box_mod = BoxAnnotation(top=jc_stg_thresh['major'], bottom=jc_stg_thresh['moderate'], fill_color='red', fill_alpha=0.25, line_dash='dashed',line_alpha=0.3,line_color='black')
    p2.add_layout(stg_box_mod)
    stg_box_minor = BoxAnnotation(top=jc_stg_thresh['moderate'], bottom=jc_stg_thresh['minor'], fill_color='orange', fill_alpha=0.25)
    p2.add_layout(stg_box_minor)
    stg_box_bf = BoxAnnotation(top=jc_stg_thresh['minor'], bottom=jc_stg_thresh['bankfull'], fill_color='yellow', fill_alpha=0.15, line_dash='dashed',line_alpha=0.3,line_color='black')
    p2.add_layout(stg_box_bf)
    
    ### Add text annotation for the flood levels
    text_bf = Label(x=95, y=jc_stg_thresh['bankfull'], x_units='screen', y_units='data', text="Bankfull",render_mode='canvas',level='glyph',x_offset=10)
    text_min = Label(x=95, y=jc_stg_thresh['minor'], x_units='screen', y_units='data', text="Minor",render_mode='canvas',level='glyph',x_offset=10)
    text_mod = Label(x=95, y=jc_stg_thresh['moderate'], x_units='screen', y_units='data', text="Moderate",render_mode='canvas',level='glyph',x_offset=10)
    text_maj = Label(x=95, y=jc_stg_thresh['major'], x_units='screen', y_units='data', text="Major",render_mode='canvas',level='glyph',x_offset=10)
    p2.add_layout(text_bf); p2.add_layout(text_min); p2.add_layout(text_mod); p2.add_layout(text_maj)
    
    ### hover tool
    hover = HoverTool(tooltips=[
                ("Flow",'@y ' + units)],
                mode='vline') #("Date","@x")],           
    p2.add_tools(hover)
    
    ### axis font size 
    p2.title.text_font_size = "19pt"
    p2.xaxis.axis_label_text_font_size = "19pt"
    p2.xaxis.major_label_text_font_size = "14pt"
    p2.yaxis.axis_label_text_font_size = "19pt"
    p2.yaxis.major_label_text_font_size = "14pt"
    #p1.toolbar_location = None
    
    p2.xaxis.formatter=DatetimeTickFormatter(
    minsec=["%Y-%m-%d %H:%M:%S"],
    minutes=["%Y-%m-%d %H:%M"],
    hourmin=["%Y-%m-%d %H:%M"],
    hours=["%Y-%m-%d %H:%M"],
    days=["%Y-%m-%d"],
    months=["%Y-%m-%d"],
    years=["%Y-%m"],)
    
    ##############################
    print 'Creating streamflow bokeh plot...'
    p3 = Figure(
       tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
       y_range = DataRange1d(start=0,end=max_Q), x_range = Range1d(start=min_date,end=max_date),
       title=basin + ptitle, x_axis_type="datetime",
       x_axis_label='Date', y_axis_label=yax,plot_width=1400, plot_height=500, lod_factor=20, lod_threshold=50
    )                                       #presentation: plot_width=2000
    
    ### OneRain default JC stage thresholds
    stg_box_major = BoxAnnotation(top=jc_stg_thresh['ptop'], bottom=jc_stg_thresh['major'], fill_color='purple', fill_alpha=0.25)
    p3.add_layout(stg_box_major)
    stg_box_mod = BoxAnnotation(top=jc_stg_thresh['major'], bottom=jc_stg_thresh['moderate'], fill_color='red', fill_alpha=0.25, line_dash='dashed',line_alpha=0.3,line_color='black')
    p3.add_layout(stg_box_mod)
    stg_box_minor = BoxAnnotation(top=jc_stg_thresh['moderate'], bottom=jc_stg_thresh['minor'], fill_color='orange', fill_alpha=0.25)
    p3.add_layout(stg_box_minor)
    stg_box_bf = BoxAnnotation(top=jc_stg_thresh['minor'], bottom=jc_stg_thresh['bankfull'], fill_color='yellow', fill_alpha=0.15, line_dash='dashed',line_alpha=0.3,line_color='black')
    p3.add_layout(stg_box_bf)
    
    ### Add text annotation for the flood levels
    text_bf = Label(x=95, y=jc_stg_thresh['bankfull'], x_units='screen', y_units='data', text="Bankfull",render_mode='canvas',level='glyph',x_offset=10)
    text_min = Label(x=95, y=jc_stg_thresh['minor'], x_units='screen', y_units='data', text="Minor",render_mode='canvas',level='glyph',x_offset=10)
    text_mod = Label(x=95, y=jc_stg_thresh['moderate'], x_units='screen', y_units='data', text="Moderate",render_mode='canvas',level='glyph',x_offset=10)
    text_maj = Label(x=95, y=jc_stg_thresh['major'], x_units='screen', y_units='data', text="Major",render_mode='canvas',level='glyph',x_offset=10)
    p3.add_layout(text_bf); p3.add_layout(text_min); p3.add_layout(text_mod); p3.add_layout(text_maj)
    
    ### hover tool
    hover = HoverTool(tooltips=[
                ("Flow",'@y ' + units)],
                mode='vline') #("Date","@x")],           
    p3.add_tools(hover)
    
    ### axis font size 
    p3.title.text_font_size = "19pt"
    p3.xaxis.axis_label_text_font_size = "19pt"
    p3.xaxis.major_label_text_font_size = "14pt"
    p3.yaxis.axis_label_text_font_size = "19pt"
    p3.yaxis.major_label_text_font_size = "14pt"
    #p1.toolbar_location = None
    
    p3.xaxis.formatter=DatetimeTickFormatter(
    minsec=["%Y-%m-%d %H:%M:%S"],
    minutes=["%Y-%m-%d %H:%M"],
    hourmin=["%Y-%m-%d %H:%M"],
    hours=["%Y-%m-%d %H:%M"],
    days=["%Y-%m-%d"],
    months=["%Y-%m-%d"],
    years=["%Y-%m"],)

###################################################################################
#### PRECIP DATA PARSE #####
input_dir = maindir + os.sep + precip_site_region + '_precip_sites_historical'
header=1                        # precip header rows in data file to skip
usecols=[0,2]                   # precip columns to read data (date,variable)
d24 = pd.DataFrame(); d72 = pd.DataFrame()  
summary_stv=[];summary_tai=[];summary_sac=[];summary_sai=[] # used for summary csv file output
summary_ctv=[];summary_cai=[];summary_cac=[];summary_oai=[] # used for summary csv file output
dts_dict_static_dates={}; dts_dict_sat_dates={} # used for summary csv list of dates

### Check if directory stucture exists for output and create if needed
output_dir = maindir + os.sep + 'interactive_plots' + os.sep + flow_stg + '_precip_alarm' + os.sep + test_name + os.sep
if os.path.isdir(output_dir + str(min_date.date()) + '_' + str(max_date.date())) == False:
    os.makedirs(output_dir + str(min_date.date()) + '_' + str(max_date.date()))
    os.makedirs(output_dir + str(min_date.date()) + '_' + str(max_date.date()) + os.sep + 'print_alarms')
if os.path.isdir(output_dir + str(min_date.date()) + '_' + str(max_date.date())  + os.sep + alarm_type) == False:
    os.makedirs(output_dir + str(min_date.date()) + '_' + str(max_date.date()) + os.sep + alarm_type)
    
for roll_win in roll_wins:
    print_dates = []; dts_dict={}; dts_dict_static=[]; dts_dict_sat=[]           # used for outputing list of all alarm date/times
    sat_count=0; static_count=0       # used for outputing list of all alarm date/times
    if output_date_list == 'true':
        write_dates=open(output_dir + str(min_date.date()) + '_' + str(max_date.date()) + os.sep + 'print_alarms' + os.sep + precip_site_region.replace('_',"") + '_stream_precip_' +pbin + 'min_' + plot_type + '_' + str(roll_win) + '_' + thresh_type + '_' + alarm_type + '.txt','w')
        write_dates.write(str(roll_win)+' Minute Alarms\n')    
    for input_file in os.listdir(input_dir+ os.sep):
        in_file = input_dir + os.sep + input_file    
        site = input_file.split('_')[1]
        if site in prec_stations:
            site_name = precip_names[site]
            ### check if pickled df already exists
            if input_file[:-4] + '_' + str(roll_win) in os.listdir(maindir + 'pickle_data' + os.sep + 'historical_precip' + os.sep + pbin + 'min_bin'):
                print('\nFound pickle df - importing ' + site + '...')
                print site_name + ' -> ' + input_file[:-4]
                df = pd.read_pickle(maindir + 'pickle_data' + os.sep + 'historical_precip' + os.sep + pbin + 'min_bin' + os.sep + input_file[:-4]+ '_' + str(roll_win))
            else:
                print '\nReading precip raw data file...'
                print site_name + ' -> ' + input_file
                df = precip_bin_data.bin_precip(in_file,pbin,header,usecols)
                #df['tooltip'] = [x.strftime("%Y-%m-%d %H:%M:%S") for x in df['date']]
            
                ### use the rolling window calculation to generate precip time series
                if plot_type == 'rolling':
                    print("Performing rolling accumulation calculation for window: " + str(roll_win))
                    df['rolling'] = df.precip.rolling(window=roll_win,freq='min',min_periods=1,closed='right').sum()
                    
            ### trim the data to the desired date range
            df = df[(df.date > min_date) & (df.date < max_date)]
            
            ### remove non-number instances 
            da=df[np.isfinite(df['rolling'])]
            ### remove non-alarm data points (below defined threshold) 
            if alarm_type == 'sat_alarms':
                if roll_win == 4320:
                    d72[site] = da['rolling']                                                   # create a copy of full 72-hour df
                    d72['date'] = df['date']
                    dm = df[np.isfinite(df['rolling'])]                                                                    # create copy for plotting 72sat (not alerts)
                    dm.drop(dm[dm['rolling'] < sat_thresh[str(roll_win)]].index, inplace=True)       # drop all instances below the 3-day saturation threshold 
                    da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)      # drop all instances below the 3-day normal static alert threshold
                elif roll_win == 1440:
                    d24[site] = da['rolling']                                                   # create a copy of full 24-hour df
                    d24['date'] = df['date']
                    dm = df[np.isfinite(df['rolling'])]                                                                    # create copy for plotting 24sat (not alerts)
                    dm.drop(dm[dm['rolling'] < sat_thresh[str(roll_win)]].index, inplace=True)       # drop all instances below the 1-day saturation threshold (2.0in)
                    da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)      # drop all instances below the 1-day normal alert threshold
                elif roll_win <= 180 and roll_win > 10:
                    ##### calcs for sat threshold exceedance
                    ds = da.copy()                                                              # create a copy of full dataframe for current roll_win
                    #dt = da.copy()                                                             # orig copy for debugging
                                                                
                    ### calc 24 and 72 hour sat timeseries (subtraction from window)               
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
                    ### calculate static thresh instances
                    da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)      # separate df for dropping instances below normal static threshold
    
                else:
                    da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)
            else:
                da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)
    
            #if thresh_type == 'UDFCD':
            #    da.drop(da[da['rolling'] < udfcd_thresh[str(roll_win)]].index, inplace=True)
            
            if make_plot == 'true':
                print 'Add data to bokeh plot...'  
                ### add some renderers
                ### Add a transparent bar for each rainfall exceedence instance
                #if max_win == '120':        
                if roll_win <= 120:
                    if alarm_type == 'static_alarms':
                        p1.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=(max_Q), color="green", legend=str(roll_win)+ '-min Static Alert', line_alpha=0,alpha=0.08) #da['rolling'
                    if alarm_type == 'sat_alarms':
                        p1.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=(max_Q/2), color="green", legend=str(roll_win)+ '-min Static Alert', line_alpha=0,alpha=0.08) #da['rolling'
                        if roll_win > 10:
                            p1.vbar(x=ds['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=(max_Q/2),top=max_Q, color="blue", legend=str(roll_win)+ '-min Sat Alert',line_alpha=0,alpha=0.08) #da['rolling'
          
                #if max_win == '360':
                if roll_win > 120 and roll_win <=360:
                    if alarm_type == 'static_alarms':
                        p2.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=(max_Q), color="green", legend=str(roll_win)+ '-min Static Alert', line_alpha=0,alpha=0.08) #da['rolling'
                    if alarm_type == 'sat_alarms':
                        p2.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=(max_Q/2), color="green", legend=str(roll_win)+ '-min Static Alert', line_alpha=0,alpha=0.08) #da['rolling'
                        if roll_win == 180:
                            p2.vbar(x=ds['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=(max_Q/2),top=max_Q, color="blue", legend=str(roll_win)+ '-min Sat Alert', line_alpha=0,alpha=0.08) #da['rolling'
    
        
                #if max_win == '1440':
                if roll_win > 360 and roll_win <=4320:
                    if alarm_type == 'static_alarms':
                        p3.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=max_Q, color="magenta", legend=str(roll_win)+ '-min Static Alert', line_alpha=0,alpha=0.08)
                    if alarm_type == 'sat_alarms':
                        p3.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=(max_Q/2), color="magenta", legend=str(roll_win)+ '-min Static Alert', line_alpha=0,alpha=0.08)
                        if str(roll_win) in sat_thresh:
                            p3.vbar(x=dm['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=(max_Q/2),top=max_Q, color="aqua", legend=str(roll_win)+ '-min Sat Alert', line_alpha=0,alpha=0.08) #da['rolling'
        
            
            ### add dates to a list to print out alarm instances
            if output_date_list == 'true':
                print_dates+=(list(set(da['date'])))
                static_count+=len((list(set(da['date']))))
                for dts in da['date']:                  # create dictionary of alarm datetimes with station_names
                    if str(dts) in dts_dict:
                        dts_dict[str(dts)].append(site_name + '(' + str(da.loc[dts,"rolling"]) +')')
                    else:
                        dts_dict[str(dts)] = [site_name + '(' + str(da.loc[dts,"rolling"]) +')']
                    if str(dts) not in dts_dict_static: # create list of only static alert instances (date&time)
                        dts_dict_static.append(str(dts))
                    if str(dts.date()) not in dts_dict_static_dates: # create list of only static alert instances (date)
                        dts_dict_static_dates[str(dts.date())]=[roll_win]
                    else: # create list of only sat alert instances (date only)
                        if roll_win not in dts_dict_static_dates[str(dts.date())]:
                            dts_dict_static_dates[str(dts.date())].append(roll_win)
                ### add saturated threshold exceeded timestamps to list
                if 60 <= roll_win <= 180 and alarm_type == 'sat_alarms':               
                    print_dates+=(list(set(ds['date'])))
                    sat_count+=len((list(set(ds['date']))))
                    for dts in ds['date']:              # create dictionary of alarm datetimes with station_names
                        if str(dts) in dts_dict:
                            dts_dict[str(dts)].append(site_name+'_sat'+ '(' + str(ds.loc[dts,"rolling"]) +')')
                        else:
                            dts_dict[str(dts)] = [site_name+'_sat'+ '(' + str(ds.loc[dts,"rolling"]) +')']
                        if str(dts) not in dts_dict_sat: # create list of only sat alert instances (date&time)
                            dts_dict_sat.append(str(dts))
                        if str(dts.date()) not in dts_dict_sat_dates: # create list of only sat alert instances (date only)
                            dts_dict_sat_dates[str(dts.date())]=[roll_win]
                        else: # create list of only sat alert instances (date only)
                            if roll_win not in dts_dict_sat_dates[str(dts.date())]:
                                dts_dict_sat_dates[str(dts.date())].append(roll_win)
    
    ### write out txt file with all unique time steps of alarms for each duration
    if output_date_list == 'true':                 
        write_dates.write('Standard Threshold Value: ' + str(thresh[str(roll_win)]) + '\n')
        summary_stv.append(str(thresh[str(roll_win)]))
        if str(roll_win) in sat_thresh and alarm_type == 'sat_alarms':
            write_dates.write('Saturated Threshold Value: ' + str(sat_thresh[str(roll_win)]) + '\n')
            summary_ctv.append(str(sat_thresh[str(roll_win)]))
        else:
            summary_ctv.append('')
        write_dates.write('Total Alarm Date/Time Instances: ' + str(len(set(print_dates))) + '\n')
        summary_tai.append(str(len(set(print_dates))))
        write_dates.write('Standard Alarm Count: ' + str(static_count) + '\n')
        summary_sac.append(str(static_count))
        write_dates.write('Standard Alarm Date/Time Instances: ' + str(len(dts_dict_static)) + '\n')
        summary_sai.append(str(len(dts_dict_static)))
        if alarm_type == 'sat_alarms':
            write_dates.write('Saturated Alarm Count: ' + str(sat_count) + '\n')
            summary_cac.append(str(sat_count))
            write_dates.write('Saturated Alarm Date/Time Instances: ' + str(len(dts_dict_sat)) + '\n')
            summary_cai.append(str(len(dts_dict_sat)))
            write_dates.write('Overlapping Sat/Static Alarm Date/Time Instances: ' + str((len(dts_dict_sat)+len(dts_dict_static))-len(set(print_dates))) + '\n')
            summary_oai.append(str((len(dts_dict_sat)+len(dts_dict_static))-len(set(print_dates))))
        for each in sorted(set(print_dates)):
            str1 = ','.join(dts_dict[str(each)])    # create a string with all stations in each datetime list
            write_dates.write(str(each) + ': ' + str1 + '\n')
        write_dates.close()
        
## create a summary csv 
if output_date_list == 'true':   
    summary = open(output_dir +  str(min_date.date()) + '_' + str(max_date.date()) + os.sep + 'print_alarms' + os.sep + 'summary_' +precip_site_region.replace('_',"") + '_stream_precip_' +pbin + 'min_' + plot_type + '_' + thresh_type + '_' + alarm_type + '.csv','wb')
    summary.write('Analysis Period: ' + str(min_date.date()) + ' <--> ' + str(max_date.date())+'\n')
    ws=csv.writer(summary)
    summary.write('Rolling Window,')
    ws.writerow(roll_wins)
    summary.write('Standard Threshold Value,')
    ws.writerow(summary_stv)
    summary.write('Saturated Threshold Value,')
    ws.writerow(summary_ctv)
    summary.write('Total Alarm Date/Time Instances,')
    ws.writerow(summary_tai)
    summary.write('Standard Alarm Date/Time Instances,')
    ws.writerow(summary_sai)
    summary.write('Saturated Alarm Date/Time Instances,')
    ws.writerow(summary_cai)
    summary.write('Overlapping Sat/Static Alarm Date/Time Instances,')
    ws.writerow(summary_oai)
    summary.write('Standard Alarm Count,')
    ws.writerow(summary_sac)
    summary.write('Saturated Alarm Count,')
    ws.writerow(summary_cac)
    summary.write('\nStandared Alert Dates:\n')
    for day in sorted(dts_dict_static_dates):
        summary.write(day + ',')
        ws.writerow(dts_dict_static_dates[day])        
    summary.write('\nSaturated Alert Dates:\n')
    for day in sorted(dts_dict_sat_dates):
        summary.write(day + ',')
        ws.writerow(dts_dict_sat_dates[day])        
    summary.close()

if make_plot == 'true':
    ### plot observed stage data
    p1.line(date_data, discharge, legend="Obs - " + yax.split()[0], name='Q', line_width=3, line_color = "black") 
    p2.line(date_data, discharge, legend="Obs - " + yax.split()[0], name='Q', line_width=3, line_color = "black") 
    p3.line(date_data, discharge, legend="Obs - " + yax.split()[0], name='Q', line_width=3, line_color = "black") 
    
    # output to static HTML file  
    print('Saving html plot file...')     
    if plot_type == 'rolling':
        output_file(output_dir + str(min_date.date()) + '_' + str(max_date.date()) + os.sep +  alarm_type + os.sep + precip_site_region.replace('_',"") + '_stream_precip_' +pbin + 'min_' + plot_type + '_all_alarms_' + thresh_type + '_criteria120.html')
        save(p1)
        output_file(output_dir + str(min_date.date()) + '_' + str(max_date.date()) + os.sep +  alarm_type + os.sep + precip_site_region.replace('_',"") + '_stream_precip_' +pbin + 'min_' + plot_type + '_all_alarms_' + thresh_type + '_criteria360.html')
        save(p2)
        output_file(output_dir + str(min_date.date()) + '_' + str(max_date.date()) + os.sep +  alarm_type + os.sep + precip_site_region.replace('_',"") + '_stream_precip_' +pbin + 'min_' + plot_type + '_all_alarms_' + thresh_type + '_criteria1440.html')
        save(p3)
        
## calculate script runtime length       
pend = datetime.datetime.now()
runtime = pend-pstart
print('Script runtime: ' + str(runtime.seconds) + ' seconds')        
### show the results
#show(p)
