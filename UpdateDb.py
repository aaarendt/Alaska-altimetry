import psycopg2
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
#import ConfigParser

# Kilroy asks if this is needed?
#cfg = ConfigParser.ConfigParser()
#cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

#from Altimetry import *


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
    
    #print "***************\n%s" % e
        
    e = e.astype(int)
    e += (e[2]-e[1])/2    # DEALING WITH THE FACT THAT LAMB BINNING LABLES THE BOTTOM OF THE BIN AND WE WANT THE CENTER
    
    #print e
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
        dic['name'] = name 
        return dic
    else:
        out = LambOut(name,date1,date2,volmodel,vol25diff,vol75diff,balmodel,bal25diff,bal75diff,e,dz,dz25,dz75,aad,masschange,massbal,numdata)
        return out

##############################################################################################
##IMPORT LAMB FILE TO DATABASE
##############################################################################################
def import_lamb_file_to_db(lambfile,db):
    #READING LAMBFILE INTO DICTIONARY    
    data = ReadLambFile(lambfile, as_string = 1, as_dict = 1)
    
    #OPENING DATABASE 
    if isinstance(db,psycopg2._psycopg.cursor):cur=db
    else:conn,cur = ConnectDb()
    
    try:
        #print 'SELECT gid FROM glnames WHERE name = %s' % data['name']
        #print str(GetSqlData("SELECT gid FROM glnames WHERE name = '%s'" % data['name'])['gid'][0])
        data['glid'] = str(GetSqlData("SELECT gid FROM glnames WHERE name = '%s'" % data['name'])['gid'][0])
    except:
        print("%s not used because not in glnames." % lambfile)
        return

    del data['name']
    
    
    data['date1'] = datetime.fromtimestamp(mktime(time.strptime(data['date1'],"%Y-%m-%d %H:%M:%S")))
    data['date2'] = datetime.fromtimestamp(mktime(time.strptime(data['date2'],"%Y-%m-%d %H:%M:%S")))
    data['interval'] = (data['date2'] - data['date1']).days
    data['date1'] = re.sub('T.*$','',data['date1'].isoformat())
    data['date2'] = re.sub('T.*$','',data['date2'].isoformat())
    
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
                #s = re.sub(" 00:00:00","'",data[key])
                #print data[key]
                if re.search('\d{4}\-\d{2}\-\d{2}',data[key]): data[key] = "'"+data[key]+"'" 
                values = values + ', ' + data[key]
            else:values = values + ', ' + str(data[key])
            
                
    #STRING FORMATTING FOR SQL
    insert = re.sub('^, ', '', insert)
    values = re.sub('^, ', '', values)
    values = re.sub('\{', "'{", values)
    values = re.sub('\}', "}'", values)
    ss = re.sub(', $', '', ss)
    #print '----------------'                
    #print insert
    #print values
    #print ss
    
    sql = "INSERT INTO lamb ("+insert+") VALUES (" + values + ");" # Note: no quotes
    cur.execute(sql)
    
    # Make the changes to the database persistent
    conn.commit()
    
    # Close communication with the database only if db name is given
    if not isinstance(db,psycopg2._psycopg.cursor):
        cur.close()
        conn.close()
        
##############################################################################################
##restart_lamb_table
##############################################################################################
def RestartLambTable(globpath): 
    """====================================================================================================
Altimetry.UpdateDb.RestartLambTable
Evan Burgess 2013-08-22
====================================================================================================
Purpose:
    Update the lamb table by searching through the glob path listed for files with the name format *output.txt.  
    All of these files are read into the table. The name is used to match a gid in the existing glnames table. 
    SO IF YOU CHANGE THE GLNAMES TABLE RUN UpdateGlnamesRegions BEFORE RUNNING THIS!!
    
Returns: Nothing
RestartLambTable(globpath = Altimetry.lambpath) 
KEYWORD ARGUMENTS:
    globpath            The full pathname used to search for lamb output files eg.  
                        /home/laser/analysis/*/results*.output.txt
====================================================================================================        
        """ 
    lambfiles = glob.glob(globpath)
    db='altimetry'
    conn,cur = ConnectDb()    
    cur.execute("DROP TABLE IF EXISTS lamb")
    cur.execute("CREATE TABLE lamb (gid serial PRIMARY KEY, glid smallint, date1 date, date2 date, interval smallint, volmodel real, vol25diff real,vol75diff real, balmodel real, bal25diff real,bal75diff real,e integer[],dz real[],dz25 real[],dz75 real[],aad real[],masschange real[],massbal real[],numdata integer[]);")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('Importing lamb output files:')
    for (i,lambfile) in enumerate(lambfiles):
        print(lambfile)
        import_lamb_file_to_db(lambfile,db)