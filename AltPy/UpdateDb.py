import re
import numpy as N
from time import mktime
from datetime import datetime
from time import mktime
import time
import os
import glob
import datetime as dtm
import sys
import Altimetry as alt
import json

sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

##############################################################################################
##READ LAMB FILE
##############################################################################################
def ReadLambFile(lambfile,as_dict = None,as_string = None):

    f = open(lambfile)
    
    f.readline()#header trashed
    
    #reading glacierwide data on line 1
    (year1,jday1,year2,jday2,volmodel,vol25diff,vol75diff,balmodel,bal25diff,bal75diff) = [float(field) for field in f.readline().split()]
    
    #converting to datetime objects
    date1 = dtm.datetime(int(year1), 1, 1) + dtm.timedelta(int(jday1) - 1)
    date2 = dtm.datetime(int(year2), 1, 1) + dtm.timedelta(int(jday2) - 1)
    
    #vertically binned data - READING
    e=N.array([])
    dz=N.array([])
    dz25=N.array([])
    dz75=N.array([])
    aad=N.array([])
    masschange=N.array([])
    massbal=N.array([])
    numdata=N.array([])
    f.readline()  #second header trashed
    for line in f:
        (e_add,dz_add,dz25_add,dz75_add,aad_add,masschange_add,massbal_add,numdata_add) = [float(field) for field in line.split()]
        e = N.append(e,e_add)
        dz = N.append(dz,dz_add)
        dz25 = N.append(dz25,dz25_add)
        dz75 = N.append(dz75,dz75_add)
        aad = N.append(aad,aad_add)
        masschange = N.append(masschange,masschange_add)
        massbal = N.append(massbal,massbal_add)
        numdata = N.append(numdata,numdata_add)
    
    e = e.astype(int)
    e += (e[2]-e[1])/2    # DEALING WITH THE FACT THAT LAMB BINNING LABLES THE BOTTOM OF THE BIN AND WE WANT THE CENTER
    numdata = numdata.astype(int)   
    
    #GETTING GLACIER NAME FROM FILENAME
    name = re.findall('(^[^\.]+)\.',os.path.basename(lambfile))[0]
    
    if as_string == 1:
        date1 = str(date1)
        date2 = str(date2)
        volmodel = str(volmodel)
        vol25diff = str(vol25diff)
        vol75diff = str(vol75diff)
        balmodel = str(balmodel)
        bal25diff = str(bal25diff)
        bal75diff = str(bal75diff)
        e = e.astype(str)
        dz = dz.astype(str)
        dz25 = dz25.astype(str)
        dz75 = dz75.astype(str)
        aad = aad.astype(str)
        masschange = masschange.astype(str)
        massbal = massbal.astype(str)
        numdata = numdata.astype(str) 
        glimsid = str(0)
        
    if as_dict == 1:
        dic={} 
        dic['date1'] = date1
        dic['date2'] = date2
        dic['volmodel'] = volmodel
        dic['vol25diff'] = vol25diff
        dic['vol75diff'] = vol75diff
        dic['balmodel'] = balmodel
        dic['bal25diff'] = bal25diff
        dic['bal75diff'] = bal75diff
        dic['e'] = e
        dic['dz'] = dz
        dic['dz25'] = dz25
        dic['dz75'] = dz75
        dic['aad'] = aad
        dic['masschange'] = masschange
        dic['massbal'] = massbal
        dic['numdata'] = numdata
        dic['glimsid'] = glimsid
    return dic


###############################################################################################
## lamb_sql_generator
##
## This generates the SQL necessary to INSERT new lines of LAMB data to the database.
###############################################################################################


def lamb_sql_generator(lambfile,glimsid,tableName):
    
    #READING LAMBFILE INTO DICTIONARY    
    data = ReadLambFile(lambfile, as_string = 1, as_dict = 1)
   
    data['date1'] = datetime.fromtimestamp(mktime(time.strptime(data['date1'],"%Y-%m-%d %H:%M:%S")))
    data['date2'] = datetime.fromtimestamp(mktime(time.strptime(data['date2'],"%Y-%m-%d %H:%M:%S")))
    data['interval'] = (data['date2'] - data['date1']).days
    data['date1'] = re.sub('T.*$','',data['date1'].isoformat())
    data['date2'] = re.sub('T.*$','',data['date2'].isoformat())
    data['glimsid'] = glimsid
    
    #STRINGS FOR INSERT SQL STATEMENT
    insert = ''
    values = ''
    ss = ''          
    
    #LOOPING THROUGH EACH FIELD OF DATA AND ADDING TO THE INSERT AND VALUE STRINGS
    for (i,key) in enumerate(data.keys()):
            insert = insert + ', ' + key
            ss = ss+ '%s, '
            
            if type(data[key]) == N.ndarray:
                s = str(data[key])
                s = re.sub('\[\'','{',s)
                s = re.sub('\'\]','}',s)
                s = re.sub("'\n? \n?'",", ",s)
                s = re.sub("\n","",s)
                values = values + ', ' + s
            elif type(data[key]) == str:
                if re.search('\d{4}\-\d{2}\-\d{2}',data[key]): data[key] = "'"+data[key]+"'" 
                if key == 'glimsid': 
                    data[key] = "'"+data[key]+"'" # Kilroy
                values = values + ', ' + data[key]
            else:values = values + ', ' + str(data[key])
            
                
    #STRING FORMATTING FOR SQL
    insert = re.sub('^, ', '', insert)
    values = re.sub('^, ', '', values)
    values = re.sub('\{', "'{", values)
    values = re.sub('\}', "}'", values)
    ss = re.sub(', $', '', ss)
    
    sql = "INSERT INTO " + tableName + " ("+insert+") VALUES (" + values + ");" # Note: no quotes
    return sql        