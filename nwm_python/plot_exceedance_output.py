# created by Ryan Spies 
# 7/18/2017
# Python 2.7
# Qick plot generated for displyaing exceedance probabilities for SQIN & QIN
# Copied from: https://www.mariokrapp.com/blog/tag/python/index.html

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import stats
import os
import math
import matplotlib
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter, FixedLocator

matplotlib.style.use('bmh')
############################### User input ###################################
##############################################################################
##### IMPORTANT: Make sure to call the correct .csv output columns ######
comids = ['2888976','2888956','2889346','2888790','2889124','2888748','13584','2889214','12932']
#comids = ['2888976']
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
save_dir = os.getcwd() + os.sep + 'QIN_SQIN' + os.sep + 'exceedance_plots' + os.sep

fill_data = True            # option to use obs data with filled gaps in missing hourly data
data_group = '1hr'              # aggregate data time window
data_types = ['QIN','SQIN']     # this specifies which variables are plotted on each plt instance
#plt_num = {'QIN':[221,223,222,224],'SQIN':[221,223,222,224]}   # use this to plot each data_type on its own plt
plt_num = {'QIN':[241,243,242,244],'SQIN':[245,247,246,248]}    # use this to plot all subplots on a single plt
############ End User input ##################################################

if fill_data == True:
    indir = indir + data_group + '_filled' + os.sep
    outdir = save_dir + data_group + '_filled' + os.sep
else:
    indir = indir + data_group + '_nofill' + os.sep
    outdir = save_dir + data_group + '_nofill' + os.sep

for comid in comids:
    csv_files = os.listdir(indir)
    if comid + '_SQIN_QIN.csv' in csv_files:
        print('Processing - ' + comid)
        csv_read = open(indir + os.sep + comid + '_SQIN_QIN.csv','r')
        #fnm  = 'elbe.csv'
        #df = pd.read_csv(csv_read,index_col=0,infer_datetime_format=True,parse_dates=True)
        df = pd.read_csv(csv_read,sep=',',skiprows=1, na_filter=True,
                usecols=[0,1,2],parse_dates=['date'],names=['date', 'QIN','SQIN'],na_values=[' ','','NA','na',-999,'-999'])
        all_qin = df['QIN'].tolist()
        all_sqin = df['SQIN'].tolist()
        date_qin = df['date'].tolist() 
        sqin = []; qin = []; dates_trim = []; count = 0                 
        ## check SQIN and QIN data for overlapping valid data - (replace with nan where no overlapp)
        for each in all_qin:
            if float(each) >= 0.01 and str(each) != 'nan' and float(all_sqin[count]) >= 0:          # ignore data less than 0??         
                qin.append(each)
                sqin.append(all_sqin[count])
                dates_trim.append(date_qin[count])
            else: 
                qin.append(np.nan)
                sqin.append(np.nan)
                dates_trim.append(date_qin[count])
            count += 1
        ### define plt instance
        fig = plt.figure(figsize=(17,7))
        for data_type in data_types:
            if data_type == 'SQIN':
                raw = pd.Series(sqin).dropna()
                flow_plot = sqin
            if data_type == 'QIN':
                raw = pd.Series(qin).dropna()    
                flow_plot = qin
            # define consistent max flow for consistent plotting ranges btw SQIN/QIN
            maxQ = int(math.ceil(max(pd.Series(qin).dropna()) / 100.0)) * 100
            #raw = df[data_type].dropna()
            ser = raw.sort_values()
            
            X = np.linspace(0.,max(ser.values)*1.1,100.)
            s, loc, scale = stats.lognorm.fit(ser.values)
            
            cum_dist = np.linspace(0.,1.,len(ser))
            ser_cdf = pd.Series(cum_dist, index=ser)
            ep = 1. - ser_cdf
            
            ax1 = plt.subplot(plt_num[data_type][0])
            ser_cdf.plot(ax=ax1,drawstyle='steps',label=data_type +' data')
            ax1.plot(X,stats.lognorm.cdf(X, s, loc, scale),label='lognormal')
            ax1.set_xlabel('Discharge')
            ax1.set_ylabel('CDF')
            plt.xlim(xmax=maxQ) 
            ax1.legend(loc=0,framealpha=0.5,fontsize=12)
            
            ax2 = plt.subplot(plt_num[data_type][2])
            # calc number of bins (split by 25cfs & 100cfs ranges)
            bin_max = int((math.ceil(max(pd.Series(raw)) / 100.0)) * 100)
            if maxQ <= 1000:
                bin_seq = range(0,bin_max,25)
            else:
                bin_seq = range(0,bin_max,100)
            ax2.hist(ser.values, bins=bin_seq, normed=True, label=data_type +' data')
            ax2.plot(X,stats.lognorm.pdf(X, s, loc, scale),label='lognormal')
            ax2.set_ylabel('Probability Density')
            ax2.set_xlabel('Discharge')
            plt.xlim(xmax=maxQ)
            ax2.legend(loc=0,framealpha=0.5,fontsize=12)
            
            A = np.vstack([ep.values, np.ones(len(ep.values))]).T
            [m, c], resid = np.linalg.lstsq(A, ser.values)[:2]
            print m, c
            r2 = 1 - resid / (len(ser.values) * np.var(ser.values))
            print r2
            
            ax3 = plt.subplot(plt_num[data_type][1])
            ax3.semilogx(100.*ep,ser.values,ls='',marker='o',label=data_type +' data')
            ax3.plot(100.*(1.-stats.lognorm.cdf(X, s, loc, scale)),X,label='lognormal')
            minorLocator = FixedLocator([.5,1,2,5,10,20,50,100])
            ax3.xaxis.set_major_locator(minorLocator)
            ax3.xaxis.set_major_formatter(ScalarFormatter())
            ax3.xaxis.set_major_formatter(FormatStrFormatter("%0.1f"))
            ax3.set_xlim(.5,100)
            ax3.set_xlabel('Exceedance Probability (%)')
            ax3.set_ylabel('Discharge')
            ax3.invert_xaxis()
            plt.ylim(ymax=maxQ)
            ax3.legend(loc=0,framealpha=0.5,fontsize=12)
            
            ax4 = plt.subplot(plt_num[data_type][3])
            ax4.plot(df['date'],df[data_type],label=data_type +' all data')
            ax4.plot(dates_trim,flow_plot,color='orange',label=data_type +' eval only',alpha=0.6)
            ax4.set_xlabel('time')
            ax4.set_ylabel('Discharge')
            plt.ylim(ymax=maxQ)
            ax4.legend(loc=0,framealpha=0.5,fontsize=12)
        
        if len(data_types) == 1:
            label=pname=data_type
        else:
            label = 'QIN & SQIN'
            pname = 'QIN_SQIN'
        plt.suptitle(comid_name[comid] + ' ' + label + ' Discharge Analysis (flow > 0)',y=1.01,fontsize=14)
        
        plt.tight_layout()
        fig.savefig(outdir + comid_name[comid] +'_' + pname + '_exceedance.png',transparent=False,dpi=200,bbox_inches='tight')