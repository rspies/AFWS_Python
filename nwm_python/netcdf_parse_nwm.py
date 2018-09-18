# created by Ryan Spies
# Lynker Technologies, LLC 
# 5/28/2018
# Python 2.7
# Description: parse through all NWM retrospective simulated output netcdf files.
# Houlry files are parsed for NHD/COMID reaches and data is output to annual files by id
# Note: v1.0 NWM data appears to have some missing data in files - flow array index = 0 (2000-2004)

import os
from netCDF4 import Dataset
import numpy as np
from datetime import datetime

pstart = datetime.now()
outdir = os.getcwd() + os.sep + 'comid_flow' + os.sep
indir = os.getcwd() + os.sep + 'nwmretro' + os.sep
years = range(1993,2017,1)
#ids = [2889846,2889674,2889080,2889076,2889068,2888974,2888976,2889066,2888996,2889078,2889044]  # James Creek reaches
ids = [2888956,2888694,2889346]

print('Reading netcdf files...')
for year in years:                                  # loop through annual directories
    data = {}; allhours = []; missing_data = []
    hour_files = os.listdir(indir + str(year))
    for each in hour_files:
        hour_netcdf = indir + os.sep + str(year) + os.sep + each
        print(each)
        nc = Dataset(hour_netcdf)                   # read netcdf file to memory
        dt = datetime.strptime(getattr(nc,'model_output_valid_time'),"%Y-%m-%d_%H:%M:%S") # parse datetime string from attributes
        allhours.append(dt)
        #print nc.variables['streamflow'].units
        flows = nc.variables['streamflow'][:]       # read all streamflow data to array
        comids = nc.variables['feature_id'][:]      # read all reachid/comid data to array
        if len(flows) == 0:                         # crete a list of nc files with missing data (array len = 0)
            missing_data.append(dt)
            print('!!!! No data for file !!!!')
        else:
            for reachid in ids:
                comid = np.where(comids==reachid)[0]    # look up index for chosen reach ids from all ids
                flow = flows[0][comid][0]               # look up flow value from reachid index
                #flow = nc.variables['streamflow'][0][comid][0]
                if dt in data:
                    data[dt].update({str(reachid):flow})
                else:
                    data[dt]={str(reachid):flow}

    print('Writing data to comid csv files...')
    ## write output to a csv for each comid
    allhours_sorted = sorted(allhours) # sorted list of datetime for processing in chronological order
    for reachid in ids:
        output = open(outdir + os.sep + str(year) + os.sep + str(reachid) + '_flow.csv','w')
        output.write('datetime' + ',' + 'flow_m3s\n')
        for hour in allhours_sorted:
            if hour in data:                            # check that data exists for timestep
                output.write(str(hour) + ',' + str("%.3f" % data[hour][str(reachid)]) + '\n')
            else:                                       # replace missing flow data hours with "NA"
                output.write(str(hour) + ',' + str('NA') + '\n')
            #print str(reachid) + ' -> ' + str(data[hour][str(reachid)])
        output.close()
    ## create txt log of missing date/times 
    if len(missing_data) > 0:
        log_miss = open(outdir + os.sep + str(year) + os.sep + 'missing_flow_data_log.txt','w')
        log_miss.write('Follwoing date/times were not processed due to flow array = 0\n')
        log_miss.write('Total missing instances for year: ' + str(len(missing_data)) + '\n')
        for miss_time in missing_data:
            log_miss.write(str(miss_time) + '\n')
        log_miss.close()
    
## calculate script runtime length       
pend = datetime.now()
runtime = pend-pstart
print('Script runtime: ' + str(runtime.seconds) + ' seconds')


## use this to read the metadata info
'''
date_file = os.getcwd() + os.sep +'201506220600_streamflow.nc'
nc = Dataset(data_file)  # read netcdf file to memory
print nc.dimensions.keys()
print('\n')
print nc.dimensions['time']
print('\n')
print nc.variables.keys()
print('\n')
print nc.variables['streamflow']
print('\n')
print nc.variables['feature_id']
print('\n')
for attr in nc.ncattrs():
    print attr, '=', getattr(nc, attr)
'''     