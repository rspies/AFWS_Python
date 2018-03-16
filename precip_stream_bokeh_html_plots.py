# created by Ryan Spies 
# 7/18/2017
# Python 2.7
# Bokeh updated to 0.12.6
# Description: generate an interactive bokeh grid plot with streamflow and rainfall rolling accumulation line plots. 
# Uses rolling window time duration accumulation calculation and data binning.
# Key Features: Pandas dataframe calculations (drop, subract, isin); bokeh plot options
# Output to html file for viewing interactive plot
# Pandas Resample function: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.resample.html
# Pandas Rolling function: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.rolling.html

from bokeh.plotting import Figure, output_file, save #importing figure (lower case f) results in increasing file size with each plot
from bokeh.models import Range1d, DatetimeTickFormatter, HoverTool, BoxAnnotation, DataRange1d
from bkcharts import Bar, Area
from bokeh.models.glyphs import VBar
from bokeh.layouts import column, gridplot
from bokeh.palettes import Category20
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
min_date = datetime.datetime(1999,1,1,12); max_date = datetime.datetime(2010,1,1,12)  #datetime.datetime(2017,7,1); min_date = datetime.datetime(2013,1,1)#
plot_type = 'rolling'   # choices: 'interval' or 'rolling'
basin = 'JamesCreek'
flow_stg = 'flow'       # choices: 'flow' for streamflow or 'stage' for gauge height
roll_wins = [60,120,180,360,720,1440,4320] # window for rolling accumulation (minutes) # 10,60,120,180,360,720,1440,4320 ##,120,180,360,720,1440,4320
pbin = '20'             # precip bin time in minutes (larger bin keeps file sizes smaller when looking at longer periods!!!)
prec_stations = ['4180','4190','4220','4270','4710','4770','4850']

if plot_type == 'rolling':
    thresh ={'10':0.5, '30':0.75,'60':1.0,'120':1.5,'180':2.0,'360':3.0,'720':4.0,'1440':5.0,'4320':10.0}
######################################################
udfcd_thresh ={'10':0.5,'60':1.0,'120':3.0,'360':5.0,'1440':5.0,'4320':10.0,'180':4.0,'720':5.0}
precip_names = {'4180':'Gold Lk','4850':'Porp Mt','4190':'Slaught','4220':'Flings','4270':'Cann Mt','4710':'Ward','4770':'Cal Rnc',
                '4150':'Gold Hl','4240':'Sunset','4160':'Sunshine','4230':'Gold Ag'}

### STREAMFLOW DATA ###    
## Define the steamflow/stage data file 
input_dir = maindir + os.sep + 'James_Creek_streamflow_data' + os.sep
if flow_stg == 'flow':
    jc_stg_thresh = {'bankfull':300,'minor':1252,'moderate':1785,'major':3000, 'ptop':3500, 'max_Q':3500} #obtained from Kate Malers email 9/26/17
if flow_stg == 'stage':
    jc_stg_thresh = {'bankfull':0.88,'minor':3.0,'moderate':3.9,'major':5.7, 'ptop':12, 'max_Q':8} ## NOTE! These are for post 2013 JC gauge rating (see rating diff spreadsheet)

### Check if directory stucture exists for output and create if needed
output_dir = maindir + os.sep + 'interactive_plots' + os.sep + flow_stg + '_precip' + os.sep
if os.path.isdir(output_dir + str(min_date.date()) + '_' + str(max_date.date())) == False:
    os.makedirs(output_dir + str(min_date.date()) + '_' + str(max_date.date()))

for roll_win in roll_wins:
    ### STREAMFLOW DATA ###    
    ## Define the steamflow/stage data file 
    input_dir = maindir + os.sep + 'James_Creek_streamflow_data' + os.sep
    if flow_stg == 'flow':
        input_file = 'merge_onerain_JamesCreek_Jamestown_flow_1999_2017.csv'
        ptitle = ' Inst Streamflow (CFS)'; yax = 'Streamflow (CFSD)'; units = 'cfs'
    if flow_stg == 'stage':
        if basin == 'JamesCreek':
            input_file = 'ALERT2_sensor_7_15861_2_EventData.csv'
        if basin == 'Rowena':
            input_file = 'onerain_Rowena_4430_Stage_4433.txt'
        if basin == 'LowerLefthand':
            input_file = 'onerain_Lower_Lefthand_10018_Stage_7.txt'
        ptitle = ' Inst Stream Stage (FT)'; yax = 'Stage (FT)'; units = 'ft'
    
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
    
    # remove bad data points (JC above 8ft stage)          
    if flow_stg == 'stage':
        if basin == 'JamesCreek' or basin == 'Rowena':
            test = test[test.OBS < 8.0]
        if basin == 'LowerLefthand':
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
    if plot_type != 'log':
        p1 = Figure(
           tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
           y_range = DataRange1d(start=0,end=max_Q), x_range = Range1d(start=min_date,end=max_date),
           title=basin + ptitle, x_axis_type="datetime",
           x_axis_label='Date', y_axis_label=yax,plot_width=1300, plot_height=350, lod_factor=20, lod_threshold=50
        )
    elif plot_type == 'log':
        p1 = Figure(
           tools="wheel_zoom,xpan,xbox_zoom,reset,resize,save",
           y_range = Range1d(start=0,end=max_Q,bounds=(0,max_Q)), x_range = Range1d(start=date_data[0],end=date_data[-1],
           bounds=(min_date,max_date)),
           title=basin + ptitle, x_axis_type="datetime",
           x_axis_label='Date', y_axis_label=yax, y_axis_type="log", plot_width=1300, plot_height=600, lod_factor=20, lod_threshold=50
        )
    #p1.background_fill_color = "grey"
    #p1.background_fill_alpha = 0.2
    
    ### OneRain default JC stage thresholds
    stg_box_major = BoxAnnotation(top=jc_stg_thresh['ptop'], bottom=jc_stg_thresh['major'], fill_color='purple', fill_alpha=0.25)
    p1.add_layout(stg_box_major)
    stg_box_mod = BoxAnnotation(top=jc_stg_thresh['major'], bottom=jc_stg_thresh['moderate'], fill_color='red', fill_alpha=0.25)
    p1.add_layout(stg_box_mod)
    stg_box_minor = BoxAnnotation(top=jc_stg_thresh['moderate'], bottom=jc_stg_thresh['minor'], fill_color='orange', fill_alpha=0.25)
    p1.add_layout(stg_box_minor)
    stg_box_bf = BoxAnnotation(top=jc_stg_thresh['minor'], bottom=jc_stg_thresh['bankfull'], fill_color='yellow', fill_alpha=0.15)
    p1.add_layout(stg_box_bf)
    
    ### Add text annotation for the flood levels
    text_bf = Label(x=95, y=jc_stg_thresh['bankfull'], x_units='screen', y_units='data', text="Bankfull",render_mode='canvas',level='glyph',x_offset=10)
    text_min = Label(x=95, y=jc_stg_thresh['minor'], x_units='screen', y_units='data', text="Minor",render_mode='canvas',level='glyph',x_offset=10)
    text_mod = Label(x=95, y=jc_stg_thresh['moderate'], x_units='screen', y_units='data', text="Moderate",render_mode='canvas',level='glyph',x_offset=10)
    text_maj = Label(x=95, y=jc_stg_thresh['major'], x_units='screen', y_units='data', text="Major",render_mode='canvas',level='glyph',x_offset=10)
    p1.add_layout(text_bf); p1.add_layout(text_min); p1.add_layout(text_mod); p1.add_layout(text_maj)

    
    # add some plotting renderers
    p1.line(date_data, discharge, legend="Obs - " + yax.split()[0], name='Q', line_width=3, line_color = "blue")
    #p.circle(date_data, discharge, legend="Observed - QME", fill_color="white", size=3)
    #p.line(date_data, Q_calib, legend="Simulated - SQME", line_width=3, line_color="red")
    #p.circle(date_data, Q_calib, legend="Simulated - SQME", fill_color="red", line_color="red", size=3)
    #p.line(x, y2, legend="y=10^x^2", line_color="orange", line_dash="4 4")
    
    # add plot for estimated high water mark
    if flow_stg == 'stage' and basin == 'JamesCreek':
        date_hw = [datetime.datetime(2013,9,12,11),datetime.datetime(2013,9,12,23)]
        stage_hw = [8.0,8.0]
    if flow_stg == 'flow' and basin == 'JamesCreek':
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
    p1.xaxis.major_label_text_font_size = "12pt"
    p1.yaxis.axis_label_text_font_size = "15pt"
    p1.yaxis.major_label_text_font_size = "12pt"
    
    p1.legend.location = "bottom_right"
    
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
    input_dir = maindir + os.sep + 'James_Creek_precip_sites_historical'
    header=1                        # precip header rows in data file to skip
    usecols=[0,2]                   # precip columns to read data (date,variable)
    ##### create a new plot instance
    if plot_type == 'interval':
        title_str = pbin + '-Minute Binned Precip (in)'
    if plot_type == 'rolling':
        title_str = pbin + '-Minute Binned Precip (in) -> ' + str(roll_win) + '-Minute Rolling Sum'
        if roll_win == 1440:
            thresh_plot_ax = 10
        elif roll_win == 4320:
            thresh_plot_ax = 13
        else:
            thresh_plot_ax = udfcd_thresh[str(roll_win)]+0.5
    p2 = Figure(
               tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
               y_range = Range1d(start=0,end=thresh_plot_ax), x_range=p1.x_range,
               title=title_str, x_axis_type="datetime",
               x_axis_label='Date', y_axis_label='Precipitation (in)',plot_width=1300, plot_height=350, lod_factor=30, lod_threshold=50
            )
            
    #    p2.background_fill_color = "grey"
    #    p2.background_fill_alpha = 0.2
    ### axis font size 
    p2.title.text_font_size = "15pt"
    p2.xaxis.axis_label_text_font_size = "15pt"
    p2.xaxis.major_label_text_font_size = "12pt"
    p2.yaxis.axis_label_text_font_size = "15pt"
    p2.yaxis.major_label_text_font_size = "12pt"

    ### add interval bounding boxes for user-input precip thresholds    
    if plot_type == 'interval':
        box = BoxAnnotation(top=14, bottom=thresh[pbin], fill_color='magenta', fill_alpha=0.2)
    if plot_type == 'rolling':
        box = BoxAnnotation(top=14, bottom=thresh[str(roll_win)], fill_color='magenta', fill_alpha=0.2)
    p2.add_layout(box)
    
    ### UDFCD default alarms/thresholds (defined at top)
    udfcd_box = BoxAnnotation(top=14, bottom=udfcd_thresh[str(roll_win)], fill_color='blue', fill_alpha=0.1)
    p2.add_layout(udfcd_box)
    
    ### Add text annotation for current rainfall alarms
    text_rain = Label(x=95, y=udfcd_thresh[str(roll_win)], x_units='screen', y_units='data', text="UDFCD Alarm",render_mode='canvas',level='glyph',x_offset=10,text_font_size='10pt')
    p2.add_layout(text_rain)
    if thresh[str(roll_win)] != udfcd_thresh[str(roll_win)]:
        text_new_rain = Label(x=95, y=thresh[str(roll_win)], x_units='screen', y_units='data', text="Modified Alarm",render_mode='canvas',level='glyph',x_offset=10,text_font_size='10pt')
        p2.add_layout(text_new_rain)
    
    count = -1
    for input_file in os.listdir(input_dir+ os.sep):
        in_file = input_dir + os.sep + input_file    
        site = input_file.split('_')[1]
        if site in prec_stations:
            count += 1
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
            
            # find max precip for plotting limit
            max_find = []
            max_find.append(np.nanmax(df.precip))
            max_Q = int(float(max(max_find))*3)
            
            print 'Creating precip bokeh plot...'
        
            ### add some renderers
            #p=Area(df, legend="top_right")
            #glyph = VBar(x='date', top='top', bottom=0, width = 5.5, fill_color="firebrick")
            #p.add_glyph(ColumnDataSource(dict(date=df['date'],top=df['precip'])), glyph)
            ###p2.vbar(x=df['date'],width=0, bottom=0,top=df['precip'], color="firebrick")
            #p=Bar(df, values='precip', legend="top_right")
            if plot_type == 'rolling':
                #p2.circle(df['date'], df['rolling'], legend=precip_names[site] + " Accum Precip", fill_color=Set1[len(os.listdir(input_dir+ os.sep))][count], size=5)
                p2.line(df['date'], df['rolling'], legend=precip_names[site] + " Accum Precip", line_color=Category20[len(prec_stations)+1][count])
            else:
                #p2.circle(df['date'], df['precip'], legend=precip_names[site] + " Accum Precip", fill_color=Set1(len(os.listdir(input_dir+ os.sep)))[count], size=5)
                p2.line(df['date'], df['precip'], legend=precip_names[site] + " Accum Precip", line_color=Category20(len(prec_stations)+1)[count])
        
            #p.circle(date_data, Q_calib, legend="Simulated - SQME", fill_color="red", line_color="red", size=3)
            #p.line(x, y2, legend="y=10^x^2", line_color="orange", line_dash="4 4")
    
            # hover tool
        #        hover = HoverTool(tooltips=[
        #                    ("Precip",'@y{0.00} in')],
        #                    mode='vline') #("Date","@x")],
        #                    
        #       p2.add_tools(hover)
            #p.circle(date_data, discharge, fill_color="white", size=4)
            p2.toolbar_location = None
            p2.xaxis.formatter=DatetimeTickFormatter(
            minsec=["%Y-%m-%d %H:%M:%S"],
            minutes=["%Y-%m-%d %H:%M"],
            hourmin=["%Y-%m-%d %H:%M"],
            hours=["%Y-%m-%d %H:%M"],
            days=["%Y-%m-%d"],
            months=["%Y-%m-%d"],
            years=["%Y-%m"],
            )
        
    s = gridplot([p2],[p1],toolbar_location='right')#column(p2, p1)
    # output to static HTML file
    if plot_type == 'interval':
        output_file(maindir + os.sep + 'interactive_plots' + os.sep + flow_stg + '_precip' + os.sep + str(min_date.date()) + '_' + str(max_date.date()) + os.sep + basin + '_stream_precip_' +pbin + 'min_' + plot_type + '.html')
    if plot_type == 'rolling':
        output_file(maindir + os.sep + 'interactive_plots' + os.sep + flow_stg + '_precip' + os.sep +  str(min_date.date()) + '_' + str(max_date.date()) + os.sep + basin + '_stream_precip_' +pbin + 'min_' + plot_type + '_' + str(roll_win) + 'min.html')
    # show the results
    #show(p)
    print 'Saving plot...'
    save(s)