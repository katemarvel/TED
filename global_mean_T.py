import CMIP5_tools as cmip5

### Import the usual suspects
import glob
import sys
import os
import numpy as np
import string


### Import things from cdutil
import MV2 as MV
import cdms2 as cdms
import cdtime,cdutil,genutil
#from eofs.cdms import Eof
#from eofs.multivariate.cdms import MultivariateEof

### plotting
import matplotlib.pyplot as plt
import matplotlib.cm as cm


### Set classic Netcdf (ver 3)
cdms.setNetcdfShuffleFlag(0)
cdms.setNetcdfDeflateFlag(0)
cdms.setNetcdfDeflateLevelFlag(0)


global crunchy
import socket
if socket.gethostname().find("crunchy")>=0:
    crunchy = True
else:
    crunchy = False





###############

#def crunch():
truestart = cdtime.comptime(1900,1,1)
historical_files = np.array(cmip5.get_datafiles("historical","tas"))
r1 = np.where(np.array([x.split(".")[3].split("i")[0]=="r1" for x in historical_files]))
H = historical_files[r1].tolist()
for fname in H:
    f = cdms.open(fname)
    st = cmip5.start_time(f["tas"])
    if cdtime.compare(st,truestart)>=0:
        print fname
        H.remove(fname)
    f.close()



rcp85_files = np.array(cmip5.get_datafiles("rcp85","tas"))
r1r85 = np.where(np.array([x.split(".")[3].split("i")[0]=="r1" for x in rcp85_files]))
R = rcp85_files[r1r85]

Hrips = [x.split(".")[1]+"."+x.split(".")[3] for x in H]
Rrips = [x.split(".")[1]+"."+x.split(".")[3] for x in R]
overlap=np.intersect1d(Hrips,Rrips)
L = len(overlap)
BIG = MV.zeros((L,200))+1.e20
i=0
for rip in np.intersect1d(Hrips,Rrips):
    Hfname = H[Hrips.index(rip)]
    Rfname = R[Rrips.index(rip)]
    fh = cdms.open(Hfname)
    fr = cdms.open(Rfname)

    th  = cdutil.averager(fh("tas"),axis='xy')
    start_h = cmip5.start_time(th)
    stop_h = cmip5.stop_time(th)
    
    cdutil.setTimeBoundsMonthly(th)
    #ref = cdutil.YEAR.climatology(th(time=('1951-1-1','1980-12-31')))

    #dep_h = cdutil.YEAR.departures(th,ref=ref)(time=(truestart,'2005-12-31'))
    dep_h = cdutil.YEAR(th)(time=(truestart,'2005-12-31'))
    
    tr  = cdutil.averager(fr("tas"),axis='xy')
    start_r = cmip5.start_time(tr)
    stop_r = cmip5.stop_time(tr)
    
    cdutil.setTimeBoundsMonthly(tr)
    

    #dep_r = cdutil.YEAR.departures(tr,ref=ref)(time=(start_r,'2099-12-31'))
    dep_r = cdutil.YEAR(tr))(time=(start_r,'2099-12-31'))
    try:
        BIG[i] = MV.concatenate((dep_h,dep_r))
    except:
        print rip
        print  MV.concatenate((dep_h,dep_r)).shape
        continue
    i+=1
    
T = np.arange(1900,2100)
tax = cdms.createAxis(T)

tax.units = 'years since 0001-1-1'
tax.designateTime()

BIG2 = MV.masked_where(np.abs(BIG)>1.e10,BIG)
modax = cdms.createAxis(np.arange(L))
modax.models = str(overlap.tolist())

BIG2.setAxis(0,modax)
BIG2.setAxis(1,tax)
BIG2.id = "tas"
BIG2.name="tas"

fw = cdms.open("TAS.nc","w")
fw.write(BIG2)
fw.close()
