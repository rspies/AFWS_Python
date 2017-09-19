# created by Ryan Spies 
# 7/18/2017
# Python 2.7
# Bokeh updated to 0.12.6
# Description: generate an interactive bokeh plot with streamflow line and rainfall alert bar overlays. 
# Applies a user input list of static rainfall thresholds to generate an overlaying transparent alert bars.
# Key Features: Pandas dataframe calculations; bokeh plot options
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
max_date = datetime.datetime(2013,9,12,18); min_date = datetime.datetime(2013,9,11,18) #max_date = datetime.datetime(2017,7,1); min_date = datetime.datetime(2013,1,1)#
plot_type = 'rolling'           # choices: 'interval' or 'rolling'
flow_stg = 'stage'              # choices: 'stream' for streamflow or 'stage' for gauge height
precip_site_region = 'James_Creek' # choices: 'James_Creek' is the 7 thiessen gages and 'James_Creek_extra' is 7 gages plus 3 extra
max_win = '120'                 # choices: '120','360', or '1440' -> these are the upper bounds for the grouped alarm durations
output_date_list = 'false'      # print output of all alarm dates to txt file
pbin = '5'                      # precip bin time in minutes
thresh_type = 'Modified'        # choices: 'Modified' (focused on 2013 exceed) or 'UDFCD' (default)
######################################################
if thresh_type == 'Modified':
    roll_wins = [10,60,120,180,360,720,1440] # window for rolling accumulation (minutes) # 10,60,120,180,360,720,1440,4320
if thresh_type == 'UDFCD':
    roll_wins = [10,60,120,360,1440]         # window for rolling accumulation (minutes) # 10,60,120,360,1440

if plot_type == 'rolling':
    thresh ={'10':0.5, '30':0.75,'60':1.0,'120':1.5,'180':2.0,'360':3.0,'720':4.0,'1440':5.0,'4320':10.0}
######################################################
udfcd_thresh ={'10':0.5,'60':1.0,'120':3.0,'360':5.0,'1440':5.0,'4320':10.0}
jc_stg_thresh = {'bankfull':0.88,'minor':3.0,'moderate':3.9,'major':5.7}
precip_names = {'4180':'Gold Lk','4850':'Porp Mt','4190':'Slaught','4220':'Flings','4270':'Cann Mt','4710':'Ward','4770':'Cal Rnc',
                '4150':'Gold Hl','4240':'Sunset','4160':'Sunshine'}
count = 0
#############################################################################
### STREAMFLOW DATA ###    
## Define the steamflow/stage data file 
input_dir = maindir + os.sep + 'James_Creek_streamflow_data' 
if flow_stg == 'stream':
    input_file = input_dir + os.sep + 'onerain_JamesCreek_Jamestown_10017_Flow_rate_7a.txt'
    ptitle = ' Inst Streamflow (CFS)  w/ Alarm Exceedance Count'; yax = 'Streamflow (CFSD)'; units = 'cfs'
if flow_stg == 'stage':
    input_file = input_dir + os.sep + 'ALERT2_sensor_7_15861_2_EventData.csv'
    ptitle = ' Inst Stream Stage (FT) w/ Alarm Exceedance Count'; yax = 'Stage (FT)'; units = 'ft'

print input_file
basin = 'JamesCreek'
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
   x_axis_label='Date', y_axis_label=yax,plot_width=2000, plot_height=400, lod_factor=20, lod_threshold=50
)

### OneRain default JC stage thresholds
stg_box_major = BoxAnnotation(top=8, bottom=jc_stg_thresh['major'], fill_color='purple', fill_alpha=0.2)
p1.add_layout(stg_box_major)
stg_box_mod = BoxAnnotation(top=jc_stg_thresh['major'], bottom=jc_stg_thresh['moderate'], fill_color='red', fill_alpha=0.2)
p1.add_layout(stg_box_mod)
stg_box_minor = BoxAnnotation(top=jc_stg_thresh['moderate'], bottom=jc_stg_thresh['minor'], fill_color='orange', fill_alpha=0.2)
p1.add_layout(stg_box_minor)
stg_box_bf = BoxAnnotation(top=jc_stg_thresh['minor'], bottom=jc_stg_thresh['bankfull'], fill_color='yellow', fill_alpha=0.05)
p1.add_layout(stg_box_bf)

### Add text annotation for the flood levels
text_bf = Label(x=min_date, y=jc_stg_thresh['bankfull'], text="Bankfull",render_mode='canvas',level='glyph',x_offset=10)
text_min = Label(x=min_date, y=jc_stg_thresh['minor'], text="Minor",render_mode='canvas',level='glyph',x_offset=10)
text_mod = Label(x=min_date, y=jc_stg_thresh['moderate'], text="Moderate",render_mode='canvas',level='glyph',x_offset=10)
text_maj = Label(x=min_date, y=jc_stg_thresh['major'], text="Major",render_mode='canvas',level='glyph',x_offset=10)
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
for roll_win in roll_wins:
    print_dates = [] # used for outputing list of all alarm date/times
    if output_date_list == 'true':
        write_dates=open(maindir + os.sep + 'interactive_plots' + os.sep + flow_stg + '_precip_alarm' + os.sep +  str(min_date.date()) + '_' + str(max_date.date()) + os.sep + 'print_alarms' + os.sep + basin + '_stream_precip_' +pbin + 'min_' + plot_type + '_' + str(roll_win) + '_' + thresh_type + '.txt','w')
        write_dates.write(str(roll_win)+' Minute Alarms\n')    
    for input_file in os.listdir(input_dir+ os.sep):
        in_file = input_dir + os.sep + input_file    
        site = input_file.split('_')[1]
        print input_file
        df = precip_bin_data.bin_precip(in_file,pbin)
        #df['tooltip'] = [x.strftime("%Y-%m-%d %H:%M:%S") for x in df['date']]
        
        ### use the rolling window calculation to generate precip time series
        if plot_type == 'rolling':
            print("Performing rolling accumulation calculation for window: " + str(roll_win))
            df['rolling'] = df.precip.rolling(window=roll_win,freq='min',min_periods=1,closed='right').sum()
                
        ### trim the data to the desired date range
        df = df[(df.date > min_date) & (df.date < max_date)]
        
        # remove non-alarm data points (below defined threshold) 
        #df = df.drop(df[df.rolling > 1.0].value)  
        da=df[np.isfinite(df['rolling'])]
        if thresh_type == 'Modified':
            da.drop(da[da['rolling'] < thresh[str(roll_win)]].index, inplace=True)
        if thresh_type == 'UDFCD':
            da.drop(da[da['rolling'] < udfcd_thresh[str(roll_win)]].index, inplace=True)
        
        
        print 'Creating precip bokeh plot...'
    
        ### add some renderers
        #p=Area(df, legend="top_right")
        #glyph = VBar(x='date', top='top', bottom=0, width = 5.5, fill_color="firebrick")
        #p.add_glyph(ColumnDataSource(dict(date=df['date'],top=df['precip'])), glyph)
    
        ### Add a transparent bar for each rainfall exceedence instance
        if max_win == '120':        
            if roll_win <= 120:
                p1.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=10, color="green", line_alpha=0,alpha=0.08) #da['rolling'
        if max_win == '360':
            if roll_win > 120 and roll_win <=360:
                p1.vbar(x=da['date'],width=datetime.timedelta(minutes=int(pbin)), bottom=0,top=10, color="orange", line_alpha=0,alpha=0.08) #da['rolling'
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
        
    ### write out txt file with all unique time steps of alarms for each duration
    if output_date_list == 'true':
        write_dates.write('Total Alarms: ' + str(len(set(print_dates))) + '\n')
        for each in sorted(set(print_dates)):
            write_dates.write(str(each) + '\n')
        write_dates.close()

### plot observed stage data
p1.line(date_data, discharge, legend="Obs - " + yax.split()[0], name='Q', line_width=3, line_color = "blue") 

# output to static HTML file
if plot_type == 'rolling':
    output_file(maindir + os.sep + 'interactive_plots' + os.sep + flow_stg + '_precip_alarm' + os.sep +  str(min_date.date()) + '_' + str(max_date.date()) + os.sep + precip_site_region.replace('_',"") + '_stream_precip_' +pbin + 'min_' + plot_type + '_all_alarms_' + thresh_type + '_criteria'+max_win+'font.html')
# show the results
#show(p)
print 'Saving plot...'
save(p1)