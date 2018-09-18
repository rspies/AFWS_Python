# created by Ryan Spies 
# 5/30/2018
# Python 2.7
# Bokeh updated to 0.12.6
# Description: generate an interactive bokeh plot of QIN/SQIN flow data for visual analysis of NWM performance 
# Key Features: bokeh plot options
# Output to html file for viewing interactive plot


from bokeh.plotting import Figure, output_file, save #importing figure (lower case f) results in increasing file size with each plot
from bokeh.models import Range1d, DatetimeTickFormatter, HoverTool, BoxAnnotation, DataRange1d
from bokeh.models import Label
from bokeh.layouts import gridplot

import os
import pandas as pd
import datetime
import numpy as np

pstart = datetime.datetime.now()
################## User Input ########################
indir = os.getcwd() + os.sep + 'QIN_SQIN' + os.sep
outdir = os.getcwd() + os.sep +'QIN_SQIN' + os.sep + 'bokeh_plots' + os.sep
#min_date = datetime.datetime(2010,9,11,12); max_date = max_date = datetime.datetime(2016,9,15) #datetime.datetime(2017,7,1); min_date = datetime.datetime(2013,1,1)#
min_date = datetime.datetime(1999,1,1); max_date = max_date = datetime.datetime(2016,10,1)
basins = {'JamesCreek':'2888976','St_Vrain_Berry':'2888790','Rowena':'2889124','LowerLeftHand':'2888956','Orodell':'2889346','St_Vrain_Narrows':'2888748','Big_Thom_Estes':'13584','Boulder_Creek_75th':'2889214','Big_Thom_Loveland':'12932'} ## options: 'JamesCreek','SVrainDiv','Rowena','LowerLeftHand','StVrain','StVrain_Ward'
basins = {'JamesCreek':'2888976'}
comid_name = {'2888976':'JamesCreek_Jamestown',
                  '2888956':'Lower Lefthand',
                  '2889346':'Orodell Fourmile Creek',
                  '2888790':'South St Vrain at Berry Rdg',
                  '2889124':'Rowena Left Hand',
                  '2888748':'South St Vrain Little_Narrows',
                  '13584':'Big Thompson Estes (USGS)',
                  '2889214':'Boulder Creek 75th (USGS)',
                  '12932':'Big Thompson Loveland (USGS)'}
fill_data = True            # option to use obs data with filled gaps in missing hourly data
nws_alert_plot = True       # option to plot the NWS warn/advisory products as points (James Creek only)
plot_precip = True          # option to plot the mean precip from the 7 rain gauges
log_scale = False            # option to plot the flow y-axis in log scale
######################################################
if fill_data == True:
    indir = indir + '1hr_filled' + os.sep
    outdir = outdir + '1hr_filled' + os.sep
else:
    indir = indir + '1hr_nofill' + os.sep
    outdir = outdir + '1hr_nofill' + os.sep
 
ptitle = ' 1-hour Streamflow (CFS)'; yax = 'Streamflow (CFS)'; units = 'cfs'
    
for basin in basins:
    
    count = 0
    ## Define the steamflow QIN/SQIN data file 
    input_file = indir + basins[basin] + '_SQIN_QIN.csv'
        
    print input_file  
    print('Reading flow/stage file...')
    read_file = open(input_file, 'r')
    print('Parsing flow/stage file...')
    test = pd.read_csv(read_file,sep=',',skiprows=1, na_filter=True,
                usecols=[0,1,2],parse_dates=['date'],names=['date', 'QIN','SQIN'],na_values=[' ','','NA','na',-999,'-999'])
    read_file.close()
    
    ### trim the data to the desired date range    
    test = test[(test.date > min_date) & (test.date < max_date)]
    
    ### assign column data to variables
    print 'Populating data arrays for plotting...'
    date_read = test['date'].tolist()  # convert to list (indexible)
    qin_read = test['QIN'].tolist()
    sqin_read = test['SQIN'].tolist() 
    
    ### find max qin/sqin flow value to use as plotting limit
    offset = 100
    maxQ = int(round(max([np.nanmax(qin_read),np.nanmax(sqin_read)]),-2)) + offset
    
    # create a new plot
    print 'Creating streamflow bokeh plot...'
    if log_scale == True:
        yax_type="log"; ylabel='_log'
    else:
        yax_type="linear"; ylabel=''
    p1 = Figure(
       tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
       y_range = DataRange1d(start=0,end=maxQ), x_range = Range1d(start=min_date,end=max_date),
       title=comid_name[basins[basin]] + ptitle, x_axis_type="datetime",active_scroll="xwheel_zoom",
       x_axis_label='Date', y_axis_label=yax,plot_width=1400, plot_height=500, lod_factor=20, lod_threshold=50,y_axis_type=yax_type)
    
    ### OneRain default JC stage thresholds
    if basin == 'JamesCreek':
        jc_stg_thresh = {'bankfull':300,'minor':1252,'moderate':1785,'major':3000, 'ptop':maxQ, 'max_Q':maxQ} #obtained from Kate Malers email 9/26/17

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
        
        ### plot options for Little and Central James segments
        print('Parsing JC upstream segment SQIN and creating plot renders...')
        input_file_little = indir + '2888974_SQIN_QIN.csv' ## Little James
        input_file_central = indir + '2889068_SQIN_QIN.csv' ## Central James
        read_file_little = open(input_file_little, 'r')
        read_file_central = open(input_file_central, 'r')
        JC_read_little = pd.read_csv(read_file_little,sep=',',skiprows=1, na_filter=True,
                    usecols=[0,1,2],parse_dates=['date'],names=['date', 'QIN','SQIN'],na_values=[' ','','NA','na',-999,'-999'])
        JC_read_central = pd.read_csv(read_file_central,sep=',',skiprows=1, na_filter=True,
                    usecols=[0,1,2],parse_dates=['date'],names=['date', 'QIN','SQIN'],na_values=[' ','','NA','na',-999,'-999'])
        read_file_little.close()
        read_file_central.close()
        ### trim the data to the desired date range    
        JC_read_little = JC_read_little[(JC_read_little.date > min_date) & (JC_read_little.date < max_date)]
        JC_read_central = JC_read_central[(JC_read_central.date > min_date) & (JC_read_central.date < max_date)]       
        ### assign column data to variables
        sqin_read_little = JC_read_little['SQIN'].tolist() 
        sqin_read_central = JC_read_central['SQIN'].tolist() 
        date_read_little = JC_read_little['date'].tolist()  # convert to list (indexible)
        date_read_central = JC_read_central['date'].tolist()  # convert to list (indexible)
        # add some plotting renderers
        p1.line(date_read_little, sqin_read_little, legend='SQIN-Little JC', line_width=2.5, line_color = "cyan")
        p1.line(date_read_central, sqin_read_central, legend='SQIN-Central JC', line_width=2.5, line_color = "magenta")

    # add some plotting renderers
    p1.line(date_read, sqin_read, legend='SQIN', line_width=4, line_color = "green",alpha=0.8)
    p1.line(date_read, qin_read, legend='QIN', line_width=3, line_color = "black",alpha=0.8)
    #p1.circle(date_read,qin_read,fill_color="black",alpha=0.5,size=8)
    
    # add plot for estimated high water mark
#    if basin == 'JamesCreek':
#        date_hw = [datetime.datetime(2013,9,12,11),datetime.datetime(2013,9,12,23)]
#        stage_hw = [3300,3300]  # estimate obtained from Memo: CDOT/CWCB Hydrology Investigation Phase One – 2013 Flood Peak Flow Determinations
#    p1.line(date_hw, stage_hw, legend="JT Estimated Peak Flow" , line_width=3, line_dash = 'dashed', line_color = "blue")
    
    # hover tool
    ## https://bokeh.pydata.org/en/latest/docs/user_guide/tools.html
    hover = HoverTool(tooltips=[
                ("Flow","$y{0.1f} " + units)],
                mode='mouse',formatters={'date':'datetime'}) #("Date","@x")],           
    p1.add_tools(hover)
    #p1.toolbar_location = None
    
    # add plot points for NWS warn products
    if nws_alert_plot == True and basin == 'JamesCreek':
        print('Plotting NWS warn points...')  
        read_nws = open(os.getcwd() + os.sep + 'nws_warns' + os.sep + 'JamesCreek_NWS_alerts.csv', 'r')
        parse_nws = pd.read_csv(read_nws,sep=',',header=0,usecols=[4,5],parse_dates=['Datetime_issued'])
        read_nws.close()
        dt_issue = parse_nws['Datetime_issued'].tolist()
        plot_pos = parse_nws['plot_pos'].tolist()
        p1.square(dt_issue,6,legend='NWS Alert',line_color="orange",fill_color="orange",alpha=0.9,size=9)
    
    
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
    
    #### Opitional plot for PRECIP DATA #####
    if plot_precip == True:
        print('Processing gauge network precip data for subplot')
        input_dir = 'D:\Projects\Jamestown_AFWS\data\pickle_data\historical_precip' + os.sep 
        pbin = '20'; roll_win = 120
        header=1                        # precip header rows in data file to skip
        usecols=[0,1]                   # precip columns to read data (date,variable)
        ##### create a new plot instance
        title_str = pbin + '-Minute Binned Precip (in) -> ' + str(roll_win) + '-Minute Rolling Sum'
        p2 = Figure(
                   tools="xwheel_zoom,xpan,xbox_zoom,reset,resize,save",
                   y_range = Range1d(start=0,end=3), x_range=p1.x_range,
                   title=title_str, x_axis_type="datetime",
                   x_axis_label='Date', y_axis_label='Precipitation (in)',plot_width=1400, plot_height=230, lod_factor=20, lod_threshold=50
                )
                
        ### axis font size 
        p2.title.text_font_size = "15pt"
        p2.xaxis.axis_label_text_font_size = "15pt"
        p2.xaxis.major_label_text_font_size = "10pt"
        p2.yaxis.axis_label_text_font_size = "15pt"
        p2.yaxis.major_label_text_font_size = "12pt"
        
        input_file = 'JC_gauges_avg_' + str(roll_win) 
        df = pd.read_pickle(input_dir + pbin + 'min_bin_avg_stations' + os.sep + input_file)
        ### trim the data to the desired date range
        df = df[(df.index > min_date) & (df.index < max_date)]
        
        # create precip plot render
        p2.line(df.index, df.values, legend="Mean Precip", line_color="blue",line_width=3)

        p2.toolbar_location = None
        p2.xaxis.formatter=DatetimeTickFormatter(
        minsec=["%Y-%m-%d %H:%M:%S"],
        minutes=["%Y-%m-%d %H:%M"],
        hourmin=["%Y-%m-%d %H:%M"],
        hours=["%Y-%m-%d %H:%M"],
        days=["%Y-%m-%d"],
        months=["%Y-%m-%d"],
        years=["%Y-%m"],)
        
        s = gridplot([p1],[p2],toolbar_location='right')#column(p2, p1)
        # output to static HTML file
        print('Saving output html file...')
        output_file(outdir + comid_name[basins[basin]] + '_' +  str(min_date.year) + '_' + str(max_date.year) + ylabel + '_stream_precip.html')
        save(s)

    else:
        # output to static HTML file
        print('Saving output html file...')
        output_file(outdir + comid_name[basins[basin]] + '_' +  str(min_date.year) + '_' + str(max_date.year) + ylabel + '_stream.html')
        save(p1)
    
pend = datetime.datetime.now()
runtime = pend-pstart
print('Script runtime: ' + str(runtime.seconds) + ' seconds')   