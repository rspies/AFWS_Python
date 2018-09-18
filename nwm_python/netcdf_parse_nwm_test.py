# created by Ryan Spies 
# 5/242018
# Python 2.7

import os
from netCDF4 import Dataset
import numpy as np
from datetime import datetime

outdir = os.getcwd() + os.sep + 'comid_flow' + os.sep
years = range(1993,2017,1)
years = [2015]
ids = [2889846,2889674,2889080,2889076,2889068,2888974,2888976,2889066,2888996,2889078,2889044]
ids = [2889846]
data = {}

for reachid in ids:
    date_file = os.getcwd() + os.sep +'201506220600_streamflow.nc'
    #date_file = os.getcwd() + os.sep +'200004040500_streamflow.nc'
    nc = Dataset(date_file)
    
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
    
    dt = datetime.strptime(getattr(nc,'model_output_valid_time'),"%Y-%m-%d_%H:%M:%S")
    #print nc.variables['streamflow'].units
    flows = nc.variables['streamflow'][:]
    comids = nc.variables['feature_id'][:]
    comid = np.where(comids==reachid)[0]
    print comid
    flow = flows[0][comid][0]
    if dt in data:
        data[dt].update({str(reachid):flow})
    else:
        data[dt]={str(reachid):flow}
'''
for reachid in ids:
    output = open(outdir + str(reachid) + '_flow.csv','w')
    output.write('datetime' + ',' + 'flow_m3s\n')
    for hour in data:
        output.write(str(hour) + ',' + str("%.3f" % data[hour][str(reachid)]) + '\n')
    print str(reachid) + ' -> ' + str(data[hour][str(reachid)])
    output.close()
'''