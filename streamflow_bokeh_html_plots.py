# created by Ryan Spies 
# 7/18/2017
# Python 2.7
# Bokeh updated to 0.12.6
# Description: generate an interactive bokeh streamflow plot
# Output to html file for viewing interactive plot

from bokeh.plotting import Figure, output_file, save #importing figure (lower case f) results in increasing file size with each plot
from bokeh.models import Range1d, DatetimeTickFormatter, HoverTool, DataRange1d
import os
from datetime import timedelta
import pandas as pd
import collections
import datetime

os.chdir("..")
maindir = os.getcwd() + os.sep + 'data' + os.sep
################## User Input ########################
loc = ''
plot_type = 'normal' # choices: 'log' or 'normal'
######################################################
input_dir = maindir + os.sep + 'streamflow_station_data_OneRain' 

for input_file in os.listdir(input_dir+ os.sep):
    print input_file
    basin = input_file.split('_')[1]
    site_num = input_file.split('_')[-4]
    read_file = open(input_dir + os.sep + input_file, 'r')
    test = pd.read_csv(read_file,sep=',',skiprows=1,
                usecols=[0,2],parse_dates=['date'],names=['date', 'OBS'])
    ### assign column data to variables
    print 'Populating data arrays for obs & calibrated streamflow...'
    
    date_data_raw = test['date'].tolist()  # convert to list (indexible)
    discharge_raw = test['OBS'].tolist()
    read_file.close()
    
    # find min/max dates
    max_date = max(date_data_raw);min_date = min(date_data_raw)
    
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
    max_find.append(max(discharge))
    max_Q = int(max(max_find)) + 5
    
    # output to static HTML file
    output_file(maindir + os.sep + 'interactive_plots' + os.sep + basin + '_streamflow.html')
        
    # create a new plot
    # log plot add this:  y_axis_type="log"
    print 'Creating bokeh plot...'
    if plot_type != 'log':
        p = Figure(
           tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
           y_range = DataRange1d('auto'), x_range = Range1d(start=date_data[0],end=date_data[-1]),
           title=basin + ' Inst Streamflow (CFS)', x_axis_type="datetime",
           x_axis_label='Date', y_axis_label='Streamflow (CFSD)',plot_width=1300, plot_height=600, lod_factor=20, lod_threshold=50
        )
    elif plot_type == 'log':
        p = Figure(
           tools="wheel_zoom,xpan,xbox_zoom,reset,resize,save",
           y_range = Range1d(start=0,end=max_Q,bounds=(0,max_Q)), x_range = Range1d(start=date_data[0],end=date_data[-1],
           bounds=(min_date,max_date)),
           title=basin + ' Inst Streamflow (CFS)', x_axis_type="datetime",
           x_axis_label='Date', y_axis_label='Streamflow (CFSD)', y_axis_type="log", plot_width=1300, plot_height=600, lod_factor=20, lod_threshold=50
        )
    #p.y_range = DataRange1d(bounds=(0,150))
    
    # add some renderers
    p.line(date_data, discharge, legend="Observed", name='Q', line_width=3, line_color = "blue")
    #p.circle(date_data, discharge, legend="Observed - QME", fill_color="white", size=3)
    #p.line(date_data, Q_calib, legend="Simulated - SQME", line_width=3, line_color="red")
    #p.circle(date_data, Q_calib, legend="Simulated - SQME", fill_color="red", line_color="red", size=3)
    #p.line(x, y2, legend="y=10^x^2", line_color="orange", line_dash="4 4")
    
    # hover tool
#    hover = HoverTool(tooltips=[
#                ("Flow",'@y cfs')],
#                mode='vline') #("Date","@x")],
#                
#    p.add_tools(hover)
    #p.circle(date_data, discharge, fill_color="white", size=4)
    
    p.xaxis.formatter=DatetimeTickFormatter(
    minsec=["%Y-%m-%d %H:%M:%S"],
    minutes=["%Y-%m-%d %H:%M"],
    hourmin=["%Y-%m-%d %H:%M"],
    hours=["%Y-%m-%d %H:%M"],
    days=["%Y-%m-%d"],
    months=["%Y-%m-%d"],
    years=["%Y-%m"],
    )
    
    # show the results
    #show(p)
    print 'Saving plot...'
    save(p)