# created by Ryan Spies 
# 7/18/2017
# Python 2.7
# Bokeh updated to 0.12.6
# Description: generate an interactive bokeh plot of streamflow or stage data (option for multiple gauges). 
# Key Features: bokeh plot options
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
pstart = datetime.datetime.now()
################## User Input ########################
min_date = datetime.datetime(2010,9,11,12); max_date = max_date = datetime.datetime(2016,9,15) #datetime.datetime(2017,7,1); min_date = datetime.datetime(2013,1,1)#
#min_date = datetime.datetime(2013,9,11,12); max_date = max_date = datetime.datetime(2013,9,13)
basins = ['JamesCreek','SVrainDiv','StVrain_Ward','StVrain','LowerLeftHand'] ## options: 'JamesCreek','SVrainDiv','Rowena','LowerLeftHand','StVrain','StVrain_Ward'
flow_stg = 'flow' # choices: 'flow' for streamflow or 'stage' for gauge height
######################################################
if 'StVrain' in basins:
    maxQ = 6000
else:
    maxQ = 3500
if flow_stg == 'stage':
    jc_stg_thresh = {'bankfull':0.88,'minor':3.0,'moderate':3.9,'major':5.7, 'ptop':12, 'max_Q':10} ## NOTE! These are for post 2013 JC gauge rating (see rating diff spreadsheet)
    ptitle = ' Inst Stream Stage (FT)'; yax = 'Stage (FT)'; units = 'ft'
if flow_stg == 'flow':
    jc_stg_thresh = {'bankfull':300,'minor':1252,'moderate':1785,'major':3000, 'ptop':maxQ, 'max_Q':maxQ} #obtained from Kate Malers email 9/26/17
    ptitle = ' Inst Streamflow (CFS)'; yax = 'Streamflow (CFSD)'; units = 'cfs'

### Define limit of y-axis
if 'LowerLeftHand' in basins and flow_stg=='stage':
    max_Q = 10.0
else:
    max_Q = jc_stg_thresh['max_Q']
    
# create a new plot
print 'Creating streamflow bokeh plot...'
p1 = Figure(
   tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
   y_range = DataRange1d(start=0,end=max_Q), x_range = Range1d(start=min_date,end=max_date),
   title='James Creek' + ptitle, x_axis_type="datetime",
   x_axis_label='Date', y_axis_label=yax,plot_width=1400, plot_height=500, lod_factor=20, lod_threshold=50)
for basin in basins:
    count = 0
 
    ## Define the steamflow/stage data file 
    input_dir = maindir + os.sep + 'James_Creek_streamflow_data' + os.sep
    if flow_stg == 'flow':
        if basin == 'JamesCreek':
            input_file = 'merge_onerain_JamesCreek_Jamestown_flow_1999_2017.csv'
        if basin == 'SVrainDiv':
            input_file = 'DWR_lefthdco_stvraindiv_2000_2016.csv'
        if basin == 'Rowena':
            input_file = 'onerain_Rowena_4430_Flow_rate_4433_2013_2017.txt'
        if basin == 'LowerLeftHand':
            input_file = 'onerain_LowerLefthand_10018_Flow_rate_7A.txt'
        if basin == 'StVrain':
            input_file = 'onerain_S._St._Vrain_at_Berry_Rdg_10021_Flow_rate_4463.txt'
        if basin == 'StVrain_Ward':
            input_file = 'DWR_sstvrain_nrward_2000_2017.csv'
    
    if flow_stg == 'stage':
        if basin == 'JamesCreek':
            input_file = 'ALERT2_sensor_7_15861_2_EventData.csv'
        if basin == 'Rowena':
            input_file = 'onerain_Rowena_4430_Stage_4433.txt'
        if basin == 'LowerLeftHand':
            input_file = 'onerain_Lower_Lefthand_10018_Stage_7.txt'
    
    print input_file  
    #site_num = input_file.split('_')[-4]
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
    
    # remove bad data points (JC above 8ft stage)          
    if flow_stg == 'stage':
        if basin == 'JamesCreek' or basin == 'Rowena':
            test = test[test.OBS < 8.0]
        if basin == 'LowerLeftHand':
            test = test[test.OBS < 10.0]
    
    ### trim the data to the desired date range    
    test = test[(test.date > min_date) & (test.date < max_date)]
    
    ### assign column data to variables
    print 'Populating data arrays for obs streamflow...'
    
    date_data_raw = test['date'].tolist()  # convert to list (indexible)
    discharge_raw = test['OBS'].tolist()
    read_file.close()
    
    # find min/max dates
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
    
    # find max flow for plotting limit
    #max_find = []
    #max_find.append(np.nanmax(discharge))
    #max_Q = int(max(max_find)) + 1
    
    #p1.background_fill_color = "grey"
    #p1.background_fill_alpha = 0.2
    
    ### OneRain default JC stage thresholds
    if basin == 'JamesCreek':
        stg_box_major = BoxAnnotation(top=jc_stg_thresh['ptop'], bottom=jc_stg_thresh['major'], fill_color='purple', fill_alpha=0.2)
        p1.add_layout(stg_box_major)
        stg_box_mod = BoxAnnotation(top=jc_stg_thresh['major'], bottom=jc_stg_thresh['moderate'], fill_color='red', fill_alpha=0.2)
        p1.add_layout(stg_box_mod)
        stg_box_minor = BoxAnnotation(top=jc_stg_thresh['moderate'], bottom=jc_stg_thresh['minor'], fill_color='orange', fill_alpha=0.2)
        p1.add_layout(stg_box_minor)
        stg_box_bf = BoxAnnotation(top=jc_stg_thresh['minor'], bottom=jc_stg_thresh['bankfull'], fill_color='yellow', fill_alpha=0.05)
        p1.add_layout(stg_box_bf)
        
        ### Add text annotation for the flood levels
        text_bf = Label(x=75, y=jc_stg_thresh['bankfull'], x_units='screen', y_units='data', text="Bankfull",render_mode='canvas',level='glyph',x_offset=10)
        text_min = Label(x=75, y=jc_stg_thresh['minor'], x_units='screen', y_units='data', text="Minor",render_mode='canvas',level='glyph',x_offset=10)
        text_mod = Label(x=75, y=jc_stg_thresh['moderate'], x_units='screen', y_units='data', text="Moderate",render_mode='canvas',level='glyph',x_offset=10)
        text_maj = Label(x=75, y=jc_stg_thresh['major'], x_units='screen', y_units='data', text="Major",render_mode='canvas',level='glyph',x_offset=10)
        # text_maj = Label(x=min_date, y=jc_stg_thresh['major'], text="Major",render_mode='canvas',level='glyph',x_offset=10) #used this to have annotation tied to graph (moved w/ graph)
        p1.add_layout(text_bf); p1.add_layout(text_min); p1.add_layout(text_mod); p1.add_layout(text_maj)

    
    # add some plotting renderers
    if basin == 'JamesCreek':
        p1.line(date_data, discharge, legend="James Creek @ JT", name='Q', line_width=3, line_color = "blue")
    if basin == 'SVrainDiv':
        p1.line(date_data, discharge, legend="S. St Vrain Div", name='Q', alpha=0.7, line_width=2, line_color = "green")
    if basin == 'Rowena':
        p1.line(date_data, discharge, legend="Rowena", name='Q', line_width=2, alpha=0.7, line_color = "purple")
    if basin == 'LowerLeftHand':
        p1.line(date_data, discharge, legend="Lower Left Hand", name='Q', line_width=2, alpha=0.7, line_color = "orange") #line_dash = 'dashed'
    if basin == 'StVrain':
        p1.line(date_data, discharge, legend="S. St Vrain @ Berry Rdg", name='Q', line_width=2, alpha=0.7, line_color = "brown") #line_dash = 'dashed'
    if basin == 'StVrain_Ward':
        p1.line(date_data, discharge, legend="S. St Vrain nr Ward", name='Q', line_width=2, alpha=0.7, line_color = "aqua") #line_dash = 'dashed'


    #p.circle(date_data, discharge, legend="Observed - QME", fill_color="white", size=3)
    #p.line(date_data, Q_calib, legend="Simulated - SQME", line_width=3, line_color="red")
    #p.circle(date_data, Q_calib, legend="Simulated - SQME", fill_color="red", line_color="red", size=3)
    #p.line(x, y2, legend="y=10^x^2", line_color="orange", line_dash="4 4")
    
    # add plot for estimated high water mark
    if flow_stg == 'stage' and 'JamesCreek' in basins:
        date_hw = [datetime.datetime(2013,9,12,11),datetime.datetime(2013,9,12,23)]
        stage_hw = [8.0,8.0]
    if flow_stg == 'flow' and 'JamesCreek' in basins:
        date_hw = [datetime.datetime(2013,9,12,11),datetime.datetime(2013,9,12,23)]
        stage_hw = [3300,3300]  # estimate obtained from Memo: CDOT/CWCB Hydrology Investigation Phase One – 2013 Flood Peak Flow Determinations
    p1.line(date_hw, stage_hw, legend="JT Estimated Peak " + flow_stg.title(), line_width=3, line_dash = 'dashed', line_color = "blue")
    
    # hover tool
    hover = HoverTool(tooltips=[
                ("Flow",'@y ' + units)],
                mode='vline') #("Date","@x")],           
    p1.add_tools(hover)
    #p1.toolbar_location = None
    
    ### axis font size 
    p1.title.text_font_size = "15pt"
    p1.xaxis.axis_label_text_font_size = "15pt"
    p1.xaxis.major_label_text_font_size = "10pt"
    p1.yaxis.axis_label_text_font_size = "15pt"
    p1.yaxis.major_label_text_font_size = "12pt"
    
    p1.legend.location = "top_right"
    
    p1.xaxis.formatter=DatetimeTickFormatter(
    minsec=["%Y-%m-%d %H:%M:%S"],
    minutes=["%Y-%m-%d %H:%M"],
    hourmin=["%Y-%m-%d %H:%M"],
    hours=["%Y-%m-%d %H:%M"],
    days=["%Y-%m-%d"],
    months=["%Y-%m-%d"],
    years=["%Y-%m"],)
    
    count += 1
    
# output to static HTML file
ftext = ''
for site in basins:
    ftext = ftext + '_' + site
output_file(maindir + os.sep + 'interactive_plots' + os.sep + flow_stg + '_gauges' + os.sep +  str(min_date.date()) + '_' + str(max_date.date()) +  '_stream' + ftext + '.html')
# show the results
#show(p)
print 'Saving plot...'
save(p1)
pend = datetime.datetime.now()
runtime = pend-pstart
print('Script runtime: ' + str(runtime.seconds) + ' seconds')   