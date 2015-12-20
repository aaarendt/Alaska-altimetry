import psycopg2
import ppygis
import scipy.stats.mstats as mstats
import scipy.stats as stats
from scipy.stats import distributions
import warnings
import re
import numpy as N
import datetime as dtm
import os
from types import *
import simplekml as kml
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter
import scipy.stats as stats
import matplotlib as mpl
import matplotlib.colors as colors
import matplotlib.colorbar as clbr
import matplotlib.cm as cmx
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
import time
import itertools
from itertools import product as iterproduct
import sys
import StringIO
from types import *
import settings as s
from base64 import b64decode as readpassword
    
def test(a):
   """docstring
   test
   """
   if a == 1:
     return "test 1"
   else:
     return "test some other number"
 

def ConnectDb(server=None, get_host=None, get_user=None, get_dbname=None, verbose=False):
    """====================================================================================================
    Altimetry.Altimetry.ConnectDb

    Evan Burgess 2015-04-22
    ====================================================================================================
    Purpose:
        Connect to a postgres database.  
    
    Returns: 
            If get_host,get_user, or get_dbname are NOT SET, ConnectDb will return a psycopg2 connection and 
            cursor to the database as a list.  If 'server' is not specified ConnectDb will connect to the 
            defaulthost' as declared in settings.py.  The user can specify a different server
            by updating settings.py with the proper information and then specifying the name of the proper
            dictionary object with the keyword server.
                   
    connection,cursor = ConnectDb(**kwargs)
  
    KEYWORD ARGUMENTS:
        server            Set to True to request that data be returned by column instead of row.
        get_host,
        get_user,
        get_dbname        If set to True, the function will alter modes and instead return the requested
                          information for the server of interest (either the default server or the one specified).  
                          Only one of these 3 keywords can be set to True at one time.

    ==================================================================================================== 
    """
    if server == None:server='defaulthost'

    serv = getattr(s,server)

    st = "dbname='%s' host='%s' user='%s' password='%s'" % (serv['dbname'],serv['host'],serv['user'],readpassword(serv['password']))

    if get_host != None and get_user == None and get_dbname == None: return serv['host']
    if get_host == None and get_user != None and get_dbname == None: return serv['user']
    if get_host == None and get_user == None and get_dbname != None: return serv['dbname']
    
    if verbose: print st     
    
    if get_host==None and get_user == None and get_dbname == None:
        conn = psycopg2.connect(st)
        cur = conn.cursor()
        return conn,cur
    
def kurtosistest_evan(a, axis=0):

    """====================================================================================================
    Altimetry.Altimetry.kurtosistest_evan

    Evan Burgess 2015-04-22
    ====================================================================================================
    Purpose:
    Calculates a kurtosis Z value and probability value that the distribution of data input has 
    non-normal kurtosis.  This funtion is similar to scipy.stats.kurtosistest except the scipy version will 
    throw an error if the dataset gets too small along one axis whereas here we just return a nan.  

                  
    Z,pvalue = kurtosistest_evan(array, axis=0)
  
    KEYWORD ARGUMENTS:
        a               An array of data
        axis            The axis over which to calculate the kurtosis.  This defaults to the 0 axis.            

    RETURNS:
        Z,p             A test Z score and p-value
    ====================================================================================================    
    """
    #a, axis = stats._chk_asarray(a, axis)
    n = N.ma.count(a,axis=axis)
    if N.min(n) < 5 and n.size==1:
        raise ValueError(
            "kurtosistest requires at least 5 observations; %i observations"
            " were given." % N.min(n))
    elif N.min(n) < 8 and n.size>1:
        warnings.warn("kurtosistest requires at least 5 observations; Outputting masked array")
    if N.min(n) < 20:
        warnings.warn(
            "kurtosistest only valid for n>=20 ... continuing anyway, n=%i" %
            N.min(n))
    b2 = mstats.kurtosis(a, axis, fisher=False)
    E = 3.0*(n-1) / (n+1)
    varb2 = 24.0*n*(n-2)*(n-3) / ((n+1)*(n+1)*(n+3)*(n+5))
    x = (b2-E)/ N.ma.sqrt(varb2)
    try:sqrtbeta1 = 6.0*(n*n-5*n+2)/((n+7)*(n+9)) * N.sqrt((6.0*(n+3)*(n+5)) / (n*(n-2)*(n-3)))
    except Warning: pass
    A = 6.0 + 8.0/sqrtbeta1 * (2.0/sqrtbeta1 + N.sqrt(1+4.0/(sqrtbeta1**2)))
    term1 = 1 - 2./(9.0*A)
    denom = 1 + x* N.ma.sqrt(2/(A-4.0))
    if N.ma.isMaskedArray(denom):
        # For multi-dimensional array input
        denom[denom < 0] = N.ma.masked
    elif denom < 0:
        denom = N.ma.masked
    
    term2 = N.ma.power((1-2.0/A)/denom,1/3.0)
    Z = (term1 - term2) / N.sqrt(2/(9.0*A))
    if N.min(n) < 5 and n.size>1: 
        return N.ma.masked_array(Z,mask=n<8), N.ma.masked_array(2 * distributions.norm.sf(N.abs(Z)),mask=n<8)
    else:
        return Z, 2 * distributions.norm.sf(N.abs(Z))
    
    
def skewtest_evan(a, axis=0):
    """=================================================================================================
    Altimetry.Altimetry.skewtest_evan

    Evan Burgess 2015-04-22
    ====================================================================================================
    Purpose:
    Calculates a skew Z value and probability value that the distribution of data input has 
    non-normal skew.  This funtion is similar to scipy.stats.skewtest except the scipy version will 
    throw an error if the dataset gets too small along one axis whereas here we just return a nan.  

                  
    Z,pvalue = skewtest_evan(array, axis=0)
  
    KEYWORD ARGUMENTS:
        a               An array of data
        axis            The axis over which to calculate the kurtosis.  This defaults to the 0 axis.            

    RETURNS:
        Z,p             A test Z score and p-value
    ====================================================================================================    
    """
    #a, axis = _chk_asarray(a, axis)
    if axis is None:
        a = a.ravel()
        axis = 0
    b2 = mstats.skew(a,axis)
    n = N.ma.count(a,axis=axis)
    if N.min(n) < 8 and n.size==1:
        raise ValueError(
            "skewtest is not valid with less than 8 samples; %i samples"
            " were given." % N.min(n))
    elif N.min(n) < 8 and n.size>1:
        warnings.warn("WARNING: Outputting masked array as some rows have less than the 8 samples required")
    y = b2 * N.ma.sqrt(((n+1)*(n+3)) / (6.0*(n-2)))
    try:beta2 = (3.0*(n*n+27*n-70)*(n+1)*(n+3)) / ((n-2.0)*(n+5)*(n+7)*(n+9))
    except Warning:pass
    
    W2 = -1 + N.ma.sqrt(2*(beta2-1))
    try:delta = 1/N.ma.sqrt(0.5* N.ma.log(W2))
    except Warning:pass
    try:alpha = N.ma.sqrt(2.0/(W2-1))
    except Warning:pass
    y = N.ma.where(y == 0, 1, y)
    Z = delta*N.ma.log(y/alpha + N.ma.sqrt((y/alpha)**2+1))
    if N.min(n) < 8 and n.size>1: 
        return N.ma.masked_array(Z,mask=n<8), N.ma.masked_array(2 * distributions.norm.sf(N.abs(Z)),mask=n<8)
    else:
        return Z, 2 * distributions.norm.sf(N.abs(Z))


def GetSqlData(select,bycolumn=True):
    """====================================================================================================
        Altimetry.Altimetry.GetSqlData

        Evan Burgess 2013-08-22
        ====================================================================================================
        Purpose:
            Extract data from postgres database using sql query and return data organized by either row or column.  

        Returns: 
            If data is returned by row (default) the requested data will be stored as a list of dictionaries where each row in
            the output table is stored as a dictionary where the keys are the column names.  If you set aliases in your sql
            query, the key names will follow those aliases.  If you request bycolumn, each column in the output table is
            accessed though a dictionary where the key is the column name.  Each column of data is stored in that
            dictionary as a list or as a numpy array.  Special data formats are supported:        

     If you request a MULTIPOLYGON geometry, the geometry will be extracted into a list of coordinates for the
     outer ring and another list of inner rings (which is another list of coordinates).  Data is stored in the 
     dictionary as keys 'inner' and 'outer'.  If there are no inner rings, None is returned.
               
    GetSqlData(select,bycolumn = False):   

    ARGUMENTS:        
        select              Any postgresql select statement as string including ';'  
    KEYWORD ARGUMENTS:
        bycolumn            Set to True to request that data be returned by column instead of row.
    ====================================================================================================        
    """
    #connect to database and execute sql and retrieve data
    conn,cur = ConnectDb()
    cur.execute(select)
    fields = [d.name for d in cur.description]

    data = cur.fetchall()
    if len(data)==0:return None

    if bycolumn:
        data = zip(*data)      
        dic = {}
        while fields:
            field = fields.pop(0)
            
            #IF DATA IS GEOM OR GEOG
            if re.search('geog|geom',field,re.IGNORECASE):
                geoms = data.pop(0)
                dic[field] = [ppygis.Geometry.read_ewkb(poly) for poly in geoms]
                if hasattr(dic[field][0], 'polygons'):
                    outerring = dic[field][0].polygons[0].rings.pop(0)
                    dic['outer'] = [[point.x,point.y] for point in outerring.points]
                    dic['inner'] = [[[point.x,point.y] for point in ring.points] for ring in dic[field][0].polygons[0].rings]
                elif hasattr(dic[field][0], 'x'):
                    dic['x'] = [item.x for item in dic[field]]
                    dic['y'] = [item.y for item in dic[field]]
            else:dic[field] = N.array(data.pop(0))
            
        return dic
    else:
       lst = [] 
       while data:
            dic = {}
            row = data.pop(0)
            
            for i,field in enumerate(fields):
            
                #IF DATA IS GEOM OR GEOG
                if re.search('geog|geom',field,re.IGNORECASE):
                    dic[field] = ppygis.Geometry.read_ewkb(row[i])
                    outerring = dic[field].polygons[0].rings.pop(0)
                    dic['outer'] = [[point.x,point.y] for point in outerring.points]
                    dic['inner'] = [[[point.x,point.y] for point in ring.points] for ring in dic[field].polygons[0].rings]

                elif type(row[i]) == list or type(row[i]) == tuple:
                    dic[field] = N.array(row[i])
                else:
                    dic[field] = row[i]
            lst.append(dic)
       return lst

##################################################################################################################  
##################################################################################################################    
def GetLambData(removerepeats=True, days_from_year = 30,interval_min = 0,interval_max = None ,earliest_date = None,\
latest_date = None, userwhere = "",verbose = False,orderby=None,longest_interval=False,get_geom=False,\
by_column=True,as_object=False,generalize=None,results=False,density=0.850, density_err= 0.06,acrossgl_err=0.0,get_hypsometry=False,get_glimsid=False):
    """====================================================================================================
    Altimetry.Altimetry.GetLambData
    Evan Burgess 2013-08-22
    ====================================================================================================
    Purpose:
        This is the primary function to extract Laser Altimetry Mass Balance (LAMB) data from the database.  
        The key point to understand is that this code does not calculate mass balance from the raw LiDAR point 
        clouds that are also stored in ice2oceans postgres database. Instead, GetLambData queries a table called
        lamb that contains the surface elevation profiles change rate profiles for each glacier over each 
        possible interval.  Each profile was in this table was generated using a semi-manual step (discussed 
        in Arendt et al., (2002) and Johnson et all. (2013)), where a user defines a bin size, a glacier 
        polygon etc and then runs a matlab script called 'lamb' to generate a top-bottom profile of surface
        elevation change rates.  This script also outputs the along profile IQR of the measured surface 
        elevation change and the mass balance integrated across the user defined glacier polygon.  All of this
        data is included in the lamb table and output by GetLambData.  The only part of 'lamb' used by Larsen 
        et al., is the elevation change rate profile and the IQR for each glacier. This script will retrieve 
        Lambdata for any group of glaciers and survey intervals.  It contains kwargs for you filter what
        intervals you would like.  It will also return the glacier polygon from the RGI (the one used in
        Larsen et al., [2015] not Johnson et al. [2013]), the glacier hypsometry, and the Larsen et al., 2015 
        mass balance estimate.
    
    Returns: 
        A dictionary or a lamb object with all attributes available in lamb as well as glacier parameters
        available in ergi_mat_view for the selection of surveyed glacier intervals chosen.

    lamb_data = GetLambData(*args,**kwargs)    

    KEYWORD ARGUMENTS:        
        removerepeats       Set to True to  select only the shortest/non-overlapping intervals for each glacier.  
                            Set to false to include all data.  Default Value=True
                        
        longest_interval    Set to True to  retreive only the single longest interval available for each glacier.
                        
        days_from_year      Set the number of days away from 365 to be considered.  For example if you want annual 
                            intervals to be within month of each other leave default of 30. If you want sub-annual 
                            (seasonal data) set to 365.  Default Value = 30
                        
        interval_min        Minimum length of interval in years. This is a rounded value so inputing 1 will include
                            an interval of 0.8 years if it passes the days_from_year threshold above. Default = 0 
                        
        interval_max        Maximum length of interval in years. This is a rounded value so inputing 3 will include
                            an interval of 3.1 years if it passes the days_from_year threshold  above. Default = None
                        
        earliest_date       Earliest date of first acquistion. Enter as string 'YYYY-MM-DD'. Default = None
    
        latest_date         Latest date of second acquistion. Enter as string 'YYYY-MM-DD'. Default = None
    
        userwhere = ""      Enter as string.  User can input additional queries as a string to a where statement. Any fields in 
                            ergi_mat_view or lamb are valid
                            Example input:"name NOT LIKE '%Columbia%' AND area > 10"
                        
        verbose             Verbose output. Default = True
    
        get_geom            Set to True to retrieve the geometry of the glacier polygon
    
        generalize          Set to a value to simplify geometries
               
        by_column           Get data organized by column instead of by lamb file (Default=True)
    
        as_object           Get data output as a LambObject.  Only works if by_column = True (Default=True)
    
        get_glimsid         Set to true to retrieve each glaciers glimsid as well.
    
        results             Set to true to retrieve the mass balance of the glacier as is estimated by Larsen et. 
                            al. (2015)
                        
        orderby             List of fields in which you would like to order your sample by.  For example: 
                            ['name','area DESC'].  Requesting a specific order will slow the query.
                        
        get_hypsometry      Retrieve the glacier hypsometry as available in ergibins.  This will add three fields
                            to the output: bins,normbins,and binned_area.  See ergibins for explanations of these
                            fields.
    
    ====================================================================================================        
    """
    #LIST OF FIELDS TO QUERY
    # Kilroy says: there has to be better way to get this list of columns. Pandas?
    fields = [
    'lamb.lambid',
    'lamb.ergiid',
    'lamb.date1',
    'lamb.date2',
    'lamb.interval',
    'lamb.volmodel',
    'lamb.vol25diff',
    'lamb.vol75diff',
    'lamb.balmodel',
    'lamb.bal25diff',
    'lamb.bal75diff',
    'ergi_mat_view.surge',
    'ergi_mat_view.gltype',
    'ergi_mat_view.name',
    'ergi_mat_view.region',
    'lamb.e',
    'lamb.dz',
    'lamb.dz25',
    'lamb.dz75',
    'lamb.aad',
    'lamb.masschange',
    'lamb.massbal',
    'lamb.numdata',
    'ergi_mat_view.max::real',
    'ergi_mat_view.min::real',
    'ergi_mat_view.continentality',
    'ergi_mat_view.area::double precision']

    #LIST OF TABLES TO QUERY
    tables = [
    "FROM lamb",
    "LEFT JOIN ergi_mat_view ON lamb.ergiid=ergi_mat_view.ergiid"]
    
    if get_glimsid:
        fields.append('ergi.glimsid')
        tables.append("INNER JOIN ergi ON ergi_mat_view.ergiid=ergi.ergiid")
    
    #OPTION TO RETRIEVE GLACIER POLYGON    
    if get_geom:
        if generalize != None: 
            fields.append("ST_Simplify(ergi_mat_view.albersgeom, %s) as albersgeom" % generalize)
        else: 
            fields.append("ergi_mat_view.albersgeom as albersgeom")

    #OPTION TO RETRIEVE ALTIMETRY RESULTS FOR THIS GLACIER 
    if results:
        fields.extend(["rlt.rlt_totalGt","rlt.rlt_totalkgm2","rlt.rlt_errGt","rlt.rlt_errkgm2","rlt.rlt_singlerrGt","rlt.rlt_singlerrkgm2"])
        
        tables.append("""LEFT JOIN (SELECT ergiid,
        SUM(area)/1000000. as area,
        SUM(mean*area)/1e9*%5.3f::real as rlt_totalGt,
        SUM(mean*area)/SUM(area)*%5.3f::real as rlt_totalkgm2,
        (((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 
        + (%5.3f)^2)^0.5::real as rlt_errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)
        *SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as rlt_errkgm2,
        (((((SUM(singl_std*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)
        *SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as rlt_singlerrkgm2,
        (((((SUM(singl_std*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2
        + (%5.3f)^2)^0.5::real as rlt_singlerrGt FROM altimetryextrapolation GROUP BY ergiid) AS rlt ON ergi_mat_view.ergiid=rlt.ergiid""" % (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,density_err,density,density,acrossgl_err,density_err,density,density,acrossgl_err))

    #OPTION TO RETRIEVE ONLY THE LONGEST INTERVAL
    orderby_init = []   
    if longest_interval:
        removerepeats = False
        distinct = "DISTINCT ON (lamb.ergiid)"
        orderby_init.extend(["lamb.ergiid","lamb.interval DESC"])
    else:
        distinct = ''
        #THIS ORDER IS NEEDED TO REMOVE REPEATS IF THIS OPTION IS SELECTED.  DATA WILL BE REODERED IF SPECIFIED BY THE USER
        orderby_init.extend(["ergi_mat_view.name","lamb.date1","lamb.interval"])
    
    #LIST OF WHERE STATEMENTS
    wheres = []
    if days_from_year != None: wheres.append("((interval %% 365) > %s OR (interval %% 365) < %s)" % (365-days_from_year,days_from_year))
    if interval_min != None:   wheres.append("ROUND(interval/365.) >= %s" % interval_min)
    if interval_max != None:   wheres.append("ROUND(interval/365.) <= %s" % interval_max)
    if earliest_date != None:  wheres.append("date1 >= '%s'" % earliest_date)
    if latest_date != None:    wheres.append("date2 <= '%s'" % latest_date)
    
    #ADDING USER SPECIFIED WHERE
    if userwhere!='':wheres.append(userwhere)
    if len(wheres)!=0:wheres[0] = "WHERE %s" % wheres[0]

    #INITIAL ORDER BY NEEDED FOR removerepeats
    if len(orderby_init)!=0:orderby_init[0] = "ORDER BY %s" % orderby_init[0]
    
    #MAKING THE SELECT QUERY
    select = "SELECT %s %s %s %s %s;" % (distinct,",".join(fields),' '.join(tables),' AND '.join(wheres),",".join(orderby_init))
    if verbose:print(select)
    s = GetSqlData(select,bycolumn=False)

    #IF NO DATA WAS RETURNED, END AND RETURNED NONE
    if type(s)==NoneType: return None

    #REMOVING REPEATS IF THAT OPTION WAS SELECTED
    deletelist = []
    keeplist = []
    lastgl = ''
    lastdate = dtm.date(1900,1,1)
    
    if removerepeats:
        if verbose: print'Filtering lamb entries:'
       
        #LOOPING THROUGH AND FINDING THE REPEATS
        for i,row in enumerate(s):

            if row['name'] == lastgl:
                if row['date1'] < lastdate:
                    deletelist.append(i)
                    if verbose:print '  ',row['name'],row['date1'],row['date2'],'-- Omitted'
                else:
                    lastdate = row['date2']
                    if verbose:print row['name'],row['date1'],row['date2']
                    keeplist.append(row['lambid'])
            else: 
                lastgl = row['name']
                lastdate = row['date2']
                if verbose:print row['name'],row['date1'],row['date2']
                keeplist.append(row['lambid'])
        
        #DELETING THE REPEATS
        s = N.delete(N.array(s),deletelist)
             
    if orderby == None:
        
        if get_hypsometry:
            for i in s:
                hyps = GetSqlData("SELECT area::real as binned_area,bins::real,normbins::real FROM ergibins WHERE ergiid='%s' ORDER BY normbins" % i['ergiid'])
                for key in ('binned_area','bins','normbins'):i[key]=hyps[key]

        if by_column:s = LambToColumn(s)
    else:
        if not re.search("^\s*ORDER BY",orderby[0], re.IGNORECASE): orderby[0]="ORDER BY %s" % orderby[0]
        print "NOTE: Choosing orderby lengthens the querytime of GetLambData"
        lambids = [str(i['lambid']) for i in s]
        s = GetSqlData("SELECT %s %s WHERE lamb.lambid IN ('%s') %s;" % (",".join(fields),' '.join(tables),"','".join(lambids),",".join(orderby)), bycolumn=by_column)
        
        if get_hypsometry:
            s['binned_area'] = []
            s['bins'] = []
            s['normbins'] = []
            for ergiidt in s['ergiid']:
                hyps = GetSqlData("SELECT area::real as binned_area,bins::real,normbins::real FROM ergibins WHERE ergiid='%s' ORDER BY normbins" % ergiidt)
                s['binned_area'].append(hyps['binned_area'])
                s['bins'].append(hyps['bins'])
                s['normbins'].append(hyps['normbins'])
                                                                
    if len(s) == 0: return None

    if as_object:
        if type(s) == dict:
            s=LambObject(s)
            print 'object'
        elif type(s) == list or type(s) == N.ndarray:
            s = [LambObject(row) for row in s]
            print 'list'
       
    return s  
      
class LambObject:
    """====================================================================================================
    Altimetry.Altimetry.LambObject
    Evan Burgess 2015-04-22
    ====================================================================================================
    Laser Altimetry Mass Balance Class
            This class contains various attributes and methods that apply to a laser altimetry interval on a
            single glacier mass balance or a colection of laser altimetry mass balances on many glaciers 
            and/or on many intervals. See table comments for explanations of each variable.
    """
    def __init__(self, indata):
        
        #print indata.keys()
        for i,key in enumerate(indata.keys()):
            if 'lambid' in indata.keys():self.lambid = indata['lambid']
            if 'ergiid' in indata.keys():self.ergiid = indata['ergiid']
            if 'gid' in indata.keys():self.gid = indata['gid']
            if 'glid' in indata.keys():self.glid = indata['glid']
            if 'date1' in indata.keys():self.date1 = indata['date1']
            if 'date2' in indata.keys():self.date2 = indata['date2']
            if 'interval' in indata.keys():self.interval = indata['interval']
            if 'volmodel' in indata.keys():self.volmodel = indata['volmodel']
            if 'vol25diff' in indata.keys():self.vol25diff = indata['vol25diff']
            if 'vol75diff' in indata.keys():self.vol75diff = indata['vol75diff']
            if 'balmodel' in indata.keys():self.balmodel = indata['balmodel']
            if 'bal25diff' in indata.keys():self.bal25diff = indata['bal25diff']
            if 'bal75diff' in indata.keys():self.bal75diff = indata['bal75diff']
            if 'surge' in indata.keys():self.surge = indata['surge']
            if 'tidewater' in indata.keys():self.tidewater = indata['tidewater']
            if 'lake' in indata.keys():self.lake = indata['lake']
            if 'river' in indata.keys():self.river = indata['river']
            if 'name' in indata.keys():self.name = indata['name']
            if 'region' in indata.keys():self.region = indata['region']
            if 'e' in indata.keys():self.e = indata['e']
            if 'dz' in indata.keys():self.dz = indata['dz']
            if 'dz25' in indata.keys():self.dz25 = indata['dz25']
            if 'dz75' in indata.keys():self.dz75 = indata['dz75']
            if 'aad' in indata.keys():self.aad = indata['aad']
            if 'masschange' in indata.keys():self.masschange = indata['masschange']
            if 'massbal' in indata.keys():self.massbal = indata['massbal']
            if 'geom' in indata.keys():self.geom = indata['geom']
            if 'geog' in indata.keys():self.geog = indata['geog']
            if 'min' in indata.keys():self.min = indata['min']
            if 'max' in indata.keys():self.max = indata['max']
            if 'glaciertype' in indata.keys():self.glaciertype = indata['glaciertype']
            if 'gltype' in indata.keys():self.gltype = indata['gltype']
            if 'numdata' in indata.keys():self.numdata = indata['numdata']
            if 'glimsid' in indata.keys():self.glimsid = indata['glimsid']
            if 'continentality' in indata.keys():self.continentality = indata['continentality']
            #if 'eb_best_flx' in indata.keys():self.eb_best_flx = indata['eb_best_flx']
            #if 'eb_high_flx' in indata.keys():self.eb_high_flx = indata['eb_high_flx']
            #if 'eb_low_flx' in indata.keys():self.eb_low_flx = indata['eb_low_flx']
            #if 'eb_bm_flx' in indata.keys():self.eb_bm_flx = indata['eb_bm_flx']
            if 'eb_bm_err' in indata.keys():self.eb_bm_err = indata['eb_bm_err']
            if 'smb' in indata.keys():self.smb = indata['smb']
            if 'area' in indata.keys():self.area = indata['area']
            if 'bm_length' in indata.keys():self.bm_length = indata['bm_length']
            if 'rlt_totalgt' in indata.keys():self.rlt_totalgt = indata['rlt_totalgt']
            if 'rlt_errgt' in indata.keys():self.rlt_errgt = indata['rlt_errgt']
            if 'rlt_totalkgm2' in indata.keys():self.rlt_totalkgm2 = indata['rlt_totalkgm2']
            if 'rlt_errkgm2' in indata.keys():self.rlt_errkgm2 = indata['rlt_errkgm2']
            if 'rlt_singlerrkgm2' in indata.keys():self.rlt_singlerrkgm2 = indata['rlt_singlerrkgm2']
            if 'rlt_singlerrgt' in indata.keys():self.rlt_singlerrgt = indata['rlt_singlerrgt']     
            if 'binned_area' in indata.keys():self.binned_area = indata['binned_area']
            if 'bins' in indata.keys():self.bins = indata['bins']
            if 'normbins' in indata.keys():self.normbins = indata['normbins']    
            
    def convert085(self):
        """Convert attributes dz,dz25 and dz75 to units of water equivalent instead of 
        surface elevation change.
        """
        self.dz = [dz * 0.85 for dz in self.dz]
        self.dz25 = [dz * 0.85 for dz in self.dz25]
        self.dz75 = [dz * 0.85 for dz in self.dz75]
            

    def normalize_elevation(self,gaussian = None):
        """====================================================================================================
        Altimetry.Altimetry.normalize_elevation

        Evan Burgess 2015-04-22
        ====================================================================================================
        Purpose:
        Normalize the elevation range in the elevation bins listed in lamb.  This normalization assumes the 
        max and min elevation is that available in the ergi table fields max and min.  This function 
        creates and updates the class attributes: self.norme,self.normdz,self.norm25,self.norm75,
        self.survIQRs. This works for an individual glacier or a group within the object.
                  
        normalize_elevation(self,gaussian = None)
  
        KEYWORD ARGUMENTS:
            gaussian        Set to True to place a gaussian smooth over the normalized data

        RETURNS:
            self.norme,self.normdz,self.norm25,self.norm75,self.survIQRs
    
            norme           The normalized elevation of each bin where 0.00 is the glacier bottom
                            1 is the glacier top. 
            normdz,norm25,
            norm75,
            survIQRs        Respectively, the elevation change rate profile, 1st, and 3rd quartiles, and IQR
                            of the profile on the normalized scale norme                    
        ====================================================================================================    
        """        
        if type(self.name) == list:
        
            #mn = N.min([N.min(x) for x in self.e])
            #mx = N.max([N.max(x) for x in self.e])
            
       	    self.norme = N.arange(0,1,0.01,dtype=N.float32)
       	
            self.normdz = []
            self.norm25 = []
            self.norm75 = []
            self.survIQRs = []
            
            for j,obj in enumerate(self.dz):
            
                if gaussian != None:
                    interval = self.e[j][1]-self.e[j][0]
                    sigma_intervals = gaussian / interval
                    
                    y = gaussian_filter(obj,sigma_intervals)
                    y25 = gaussian_filter(self.dz25[j],sigma_intervals)
                    y75 = gaussian_filter(self.dz75[j],sigma_intervals)
                else: 
                    y = obj
                    y25 = self.dz25[j]
                    y75 = self.dz75[j]
                
                e = self.e[j].astype(N.float32)
                #x = (e-N.min(e))/(N.max(e)-N.min(e))
                x = (e-self.min[j])/(self.max[j]-self.min[j])
                
                normdzhold = N.interp(self.norme,x,y)
                new25shold = N.interp(self.norme,x,y25)
                new75shold = N.interp(self.norme,x,y75)
                iqr = new75shold - new25shold 
                #print 'ehrererasdfa'
                
                
                if type(obj) == N.ma.core.MaskedArray: 
                     #print 'masked!!!!'
                     mask = N.interp(self.norme,x,N.ma.getmask(obj).astype(float),N.nan,N.nan).round().astype(bool)
                     normdzhold = N.ma.masked_array(normdzhold,mask)
                     new25shold = N.ma.masked_array(new25shold,mask)
                     new75shold = N.ma.masked_array(new75shold,mask)
                     iqr = N.ma.masked_array(iqr,mask)
                
                self.normdz.append(normdzhold)
                self.norm25.append(new25shold)         
                self.norm75.append(new75shold) 
                self.survIQRs.append(iqr)

               
            return self.norme,self.normdz,self.norm25,self.norm75,self.survIQRs
        else:
                  
            #mn = N.min([N.min(x) for x in self.e])
            #mx = N.max([N.max(x) for x in self.e])
            
       	    self.norme = N.arange(0,1,0.01,dtype=N.float32)
       	
            #self.normdz = []
            #self.norm25 = []
            #self.norm75 = []
            #self.survIQRs = []
            
            #for j,obj in enumerate(self.dz):
            
            if gaussian != None:
                interval = self.e[1]-self.e[0]
                sigma_intervals = gaussian / interval
                
                y = gaussian_filter(self.dz,sigma_intervals)
                y25 = gaussian_filter(self.dz25,sigma_intervals)
                y75 = gaussian_filter(self.dz75,sigma_intervals)
            else: 
                y = self.dz
                y25 = self.dz25
                y75 = self.dz75
            
            e = self.e.astype(N.float32)
            #x = (e-N.min(e))/(N.max(e)-N.min(e))
            x = (e-self.min)/(self.max-self.min)    
                    
            normdzhold = N.interp(self.norme,x,y,N.nan,N.nan)
            new25shold = N.interp(self.norme,x,y25,N.nan,N.nan)
            new75shold = N.interp(self.norme,x,y75,N.nan,N.nan)
            iqr = new75shold - new25shold 
            #print 'ehrererasdfa'
            if type(self.dz) == N.ma.core.MaskedArray: 
                #print 'masked!!!!'
                mask = N.interp(self.norme,x,N.ma.getmask(self.dz).astype(float),N.nan,N.nan).round().astype(bool)
                normdzhold = N.ma.masked_array(normdzhold,mask)
                new25shold = N.ma.masked_array(new25shold,mask)
                new75shold = N.ma.masked_array(new75shold,mask)
                iqr = N.ma.masked_array(iqr,mask)
            
            self.normdz=normdzhold
            self.norm25=new25shold        
            self.norm75=new75shold
            self.survIQRs=iqr
            
        return self.norme,self.normdz,self.norm25,self.norm75,self.survIQRs
        
    def calc_mb(self,units='area normalized'):
        """====================================================================================================
        Altimetry.Altimetry.calc_mb

        Evan Burgess 2015-04-22
        ====================================================================================================
        Purpose:
        Adds a new attribute to the object self.mb which is a glacier mass balance estimate given the lamb 
        data, a normalized surface elevation change profile (from normalize_elevation) and a glacier hypsometry
        (run GetLambData with 'get_hypsometry=True').  This works for an individual glacier or a group within 
        the object.
                  
        calc_mb(self,units='area normalized')
  
        KEYWORD ARGUMENTS:
            units        Set to True to place a gaussian smooth over the normalized data

        RETURNS:
            self.norme,self.normdz,self.norm25,self.norm75,self.survIQRs
    
            norme           The normalized elevation of each bin where 0.00 is the glacier bottom
                            1 is the glacier top. 
            normdz,norm25,
            norm75,
            survIQRs        Respectively, the elevation change rate profile, 1st, and 3rd quartiles, and IQR
                            of the profile on the normalized scale norme                    
        ====================================================================================================    
        """        
        if not 'binned_area' in dir(self):raise "ERROR: Need to first run GetLambData with 'get_hypsometry=True'"
        if not 'normdz' in dir(self):raise "ERROR: need to run normalize_elevation method first."
        if not type(self.name) == list:raise "ERROR: Object needs to be BY column"
        
        binvol = []
        for binarea,nomdz,nobin in zip(self.binned_area,self.normdz,self.normbins):
            if units == 'area normalized':
                binvol.append(N.sum(binarea*nomdz[(nobin*100).astype(int)])/N.sum(binarea)*0.85)
            elif units == 'gt':
                binvol.append(N.sum(binarea*nomdz[(nobin*100).astype(int)])/1e9*0.85)
            else:raise "ERROR: units key must be 'area normalized' or 'gt'"
        self.mb = N.array(binvol)
        
    def calc_dz_stats(self,masked_array=False,too_few=None):
        """====================================================================================================
        Altimetry.Altimetry.calc_dz_stats

        Evan Burgess 2015-04-22
        ====================================================================================================
        Purpose:
        Calculates various statistics for the sample within the object. Requires that one normalize_elevation 
        first.
                  
        calc_dz_stats(self,masked_array=False,too_few=None)
  
        KEYWORD ARGUMENTS:
            units        Set to True to place a gaussian smooth over the normalized data

        RESULT:
              Adds the following attributes to the lamb object:
                  quadsum          Quadrature sum of the sample along profile (m/yr) along the normalized profile.  
                                   Used as an estimate of surveyed glacier uncertainty for the region when 
                                   integrated over all surveyed glaciers in this sample.   
                  dzs_std          Standard Deviation along the normalized profile. 
                  dzs_mean         Mean surface elevation change rate (m/yr) along the normalized profile.
                  dzs_median       Median surface elevation change rate (m/yr) along the normalized profile.
                  dzs_madn         NormalizedMAD of surface elevation change rate (m/yr) along the normalized profile.
                  dzs_sem          Standar error of the mean (m/yr) along the normalized profile. Used as an estimate 
                                   of surveyed glacier uncertainty for the region when integrated over all 
                                   unsurveyed glaciers
                  normalp          P-value probablitiy of normality along profile
                  skewz/p          Z-score and p-value for test of whether the sample elevation change rates
                                   have a skew that is non-normal along profile
                  kurtz/p          Z-score and p-value for test of whether the sample elevation change rates
                                   have a skew that is non-normal along profile.
                  skew             The skew of the distribution along profile.
                  kurtosis         The kurtosis of the distribution along profile.
                  percentile_5     The 5th percentile of the distribution along profile (m/yr).
                  quartile_1       The first quartile of the distribution along profile (m/yr).
                  percentile_33    The 33rd percentile of the distribution along profile (m/yr).
                  percentile_66    The 66th percentile of the distribution along profile (m/yr).
                  quartile_3       The 3rd quartile of the distribution along profile (m/yr).
                  percentile_95    The 95th percentile of the distribution along profile (m/yr).     
        ====================================================================================================    
        """        
        if not type(self.name) == list:raise "ERROR: Object needs to be BY column"
        if not hasattr(self, 'normdz'):raise "ERROR: need to run normalize_elevation method first."
    
        newys2 = N.c_[self.normdz]
   
        if type(self.normdz[0]) == N.ma.core.MaskedArray: 
            mask = N.c_[[list(N.ma.getmask(x)) for x in self.normdz]]
            newys2 = N.ma.masked_array(newys2,mask)
            
        #if masked_array: 
        #    newys2 = N.ma.masked_array(newys2,N.isnan(newys2))
            #survIQR = N.ma.masked_array(survIQR,N.isnan(new25))
        
          
            #if label != None: label = "%s N=%s" % (label,len(s))
            #newys3 = N.ma.masked_array(newys2,N.isnan(newys2))
    
        if type(self.normdz[0]) == N.ma.core.MaskedArray:
            survIQRs2 = N.c_[self.survIQRs]
            mask = N.c_[[list(N.ma.getmask(x)) for x in self.survIQRs]]
            survIQRs2 = N.ma.masked_array(survIQRs2,mask)
            
            self.dzs_n = N.sum((mask == False).astype(int),axis=0)
            dzs_n_nozero= N.where(N.logical_or(self.dzs_n==0,self.dzs_n==1),N.nan,self.dzs_n)
            self.quadsum = N.ma.sqrt(N.ma.sum((survIQRs2.T*0.7413)**2,axis=1))/N.sqrt(dzs_n_nozero*(dzs_n_nozero-1))
            #print N.ma.sum((survIQRs2.T*0.7413)**2,axis=1)
        else: 
            self.dzs_n = len(self.normdz)
            dzs_n_nozero= N.where(N.logical_or(self.dzs_n==0,self.dzs_n==1),N.nan,self.dzs_n)
            self.quadsum = N.sqrt(N.sum(((N.array(self.survIQRs).T)*0.7413)**2,axis=1))/N.sqrt(dzs_n_nozero*(dzs_n_nozero-1))  #SCALING TO A STANDARD DEVIATION EQUIVALENT then calculating quadrature sum


        self.dzs_std = N.ma.std(newys2,axis=0)

        self.dzs_sem = self.dzs_std/N.ma.sqrt(dzs_n_nozero)
        self.dzs_mean = N.ma.mean(newys2,axis=0)
        self.dzs_madn = mad(newys2,axis=0,normalized=True)
        self.dzs_median = N.ma.median(newys2,axis=0)
        
        #IF THERE ARE TOO FEW VALUES TO PRODUCE A MEAN THEN EXTEND USING THE LAST GOOD MEAN ESTIMATE.
        #print "type too feww %s" % too_few
        if type(too_few) != NoneType:
            wenough = N.where(self.dzs_n>too_few)[0]
            x = N.arange(len(self.dzs_n))[wenough]

            quadsum = self.quadsum[wenough]
            dzs_std = self.dzs_std[wenough]
            dzs_sem = self.dzs_sem[wenough]
            dzs_mean = self.dzs_mean[wenough]
            dzs_madn = self.dzs_madn[wenough]
            dzs_median = self.dzs_median[wenough]

            self.quadsum = N.interp(N.arange(len(self.dzs_n)),x,quadsum)
            self.dzs_std = N.interp(N.arange(len(self.dzs_n)),x,dzs_std)
            self.dzs_sem = N.interp(N.arange(len(self.dzs_n)),x,dzs_sem)
            self.dzs_mean = N.interp(N.arange(len(self.dzs_n)),x,dzs_mean)
            self.dzs_madn = N.interp(N.arange(len(self.dzs_n)),x,dzs_madn)
            self.dzs_median = N.interp(N.arange(len(self.dzs_n)),x,dzs_median)
         
        self.normalp=[] 
        for ty in newys2.T:
            if type(self.normdz[0]) == N.ma.core.MaskedArray: ty = ty.compressed()  # remove masked values since shapiro doesn't deal with masks
            if ty.size > 2:
                Wstat,pval1 = stats.shapiro(ty)
                self.normalp.append(pval1)
            else:  self.normalp.append(N.nan)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")    
            self.skewz,self.skewp = skewtest_evan(N.ma.masked_array(newys2,mask=N.isnan(newys2)),axis=0)

            self.kurtz,self.kurtp = kurtosistest_evan(newys2,axis=0)  
            self.skew = stats.skew(newys2,axis=0)
            self.kurtosis = stats.kurtosis(newys2,axis=0)
        
        self.percentile_5, self.quartile_1,self.percentile_33,self.percentile_66,self.quartile_3,self.percentile_95 = mstats.mquantiles(newys2,prob=[0.05,0.25,0.33,0.66,0.75,0.95],axis=0)
        self.interquartile_rng = self.quartile_3-self.quartile_1
        
        #quadrat method to find variance between regions. Stastical Methods in Geography Rogerson pg 157
        regions = list(set(self.region))
        ptspercell = N.array([N.where(N.array(self.region) == x)[0].size for x in regions])
        var = (N.sum((ptspercell - N.mean(ptspercell))**2))/(ptspercell.size-1)   
        self.quadratcluster = var/N.mean(ptspercell)
          
    def calc_residuals_zscores(self):
        """Calculate along profile z-scores of surface elevation change rates.  Creates two new attributes self.resids and self.zscores."""
        if not hasattr(self, 'normdz'):raise "ERROR: need to run normalize_elevation method first."
        if not hasattr(self, 'dzs_mean'):raise "ERROR: need to run calc_dz_stats method first."
        
        self.resids=[]
        self.zscores=[]
        for curve in self.normdz:self.resids.append(curve-self.dzs_mean)
        for curve in self.resids:self.zscores.append(curve/self.dzs_std)
    
    def get_approx_location(self):
        """Finds the approximate location of the first overflight in each bin.  This is useful for plotting the surface elevation
        change data on a map.  We say approximate location because this isn't the actual flightline, rather this script just finds the LIDAR
        crossing point with the elevation closest to each bin's middle elevation and assigns that point as the location.  The values are not
        returned rather the output coordinates are added as attributes to the object:
                    self.approxlon
                    self.approxlat
        """
        
        self.approxlon=[]
        self.approxlat=[]
        
        for k,gid in enumerate(self.gid):
            print k
            xpts=GetSqlData("SELECT z1,geog from xpts WHERE lambid=%s" % gid)
            
            print 'len xpts',len(xpts['z1'])
            
            srt = N.argsort(xpts['z1'])
            sortd = [xpts['z1'][item] for item in srt]
            sortgeog = [xpts['geog'][item] for item in srt]
            
            normz = (sortd - N.min(self.e[k]))/(N.max(self.e[k])-N.min(self.e[k]))
            
            #print 'normz',len(normz)
            #print 'e',N.max(self.e[k]),N.min(self.e[k])
            #print 'sorted',N.max(sortd),N.min(sortd)
            #print 'normz',N.max(normz),N.min(normz)
            #print 'normk',self.norme[k]
            
            x=[xy.x for xy in sortgeog]
            y=[xy.y for xy in sortgeog]
            
            self.approxlon.append(N.interp(self.norme, normz, x,N.nan,N.nan))
            self.approxlat.append(N.interp(self.norme, normz, y,N.nan,N.nan))
          
    def fix_terminus(self,slope=-0.05,error=1):
        """====================================================================================================
        Altimetry.Altimetry.fix_terminus

        Evan Burgess 2015-04-22
        ====================================================================================================
        Purpose:
        Correct profile/s for a retreating terminus as exemplified in figure S11.
                  
        fix_terminus(slope=-0.05,error=1)
  
        KEYWORD ARGUMENTS:
            slope       The threshold used to determine how steep the reduction in thinning rate needs to be 
                        to qualify as a section that needs to be corrected.  I played with this a lot and the
                        default value of -0.05 worked best.
            error       The 1 quartile width to set as the error for the corrected portion of the profile

        RETURNS:
        This does not return anything rather it just 'fixes the surface elevation change profiles in the
        object.  Specifically it changes dz,dz25 and dz75.                
        ===================================================================================================
        """
        if not type(self.numdata) == list:
            cumulative = N.cumsum(self.numdata)
            
            for i,val in enumerate(cumulative):
                if val != 0:break
        
            self.dz = N.where(cumulative == 0, N.nan,self.dz)
            self.dz25 = N.where(cumulative == 0, N.nan,self.dz25)
            self.dz75 = N.where(cumulative == 0, N.nan,self.dz75)
            
            deriv = N.ediff1d(self.dz)
                        
            for i,bn in enumerate(deriv):
                if not N.isnan(bn):
                    if bn < slope and self.dz[i]<0.1: 
                        self.dz[i]=N.nan
                    else:break
            nanreplace = N.isnan(self.dz)
            self.dz = N.where(nanreplace, self.dz[i],self.dz)
            self.dz25 = N.where(nanreplace, self.dz25[i]-error,self.dz25)
            self.dz75 = N.where(nanreplace, self.dz75[i ]+error,self.dz75)
            return deriv
            
        else:
            for j in xrange(len(self.numdata)):
                
                cumulative = N.cumsum(self.numdata[j])
                
                for i,val in enumerate(cumulative):
                    if val != 0:break
            
                self.dz[j] = N.where(cumulative == 0, N.nan,self.dz[j])
                self.dz25[j] = N.where(cumulative == 0, N.nan,self.dz25[j])
                self.dz75[j] = N.where(cumulative == 0, N.nan,self.dz75[j])
                
                deriv = N.ediff1d(self.dz[j])#ediff1d
                #print lambobj.dz
                #print deriv
                
                for i,bn in enumerate(deriv):
                    if not N.isnan(bn):
                        if bn < slope and self.dz[j][i]<0.1: 
                            self.dz[j][i]=N.nan
                        else:break
                nanreplace = N.isnan(self.dz[j])
                #print 'self.dz',self.dz[j]
                #print 'i',i
                self.dz[j] = N.where(nanreplace, self.dz[j][i],self.dz[j])
                self.dz25[j] = N.where(nanreplace, self.dz25[j][i] - error,self.dz25[j])
                self.dz75[j] = N.where(nanreplace, self.dz75[j][i] + error,self.dz75[j])
                
    def remove_upper_extrap(self,remove_bottom=True,erase_mean=True,add_mask=True):
        """The LAMB matlab code extrapolates  to the glacier head and glacier terminus when data does not make it 
        all of the way to the top or bottom.  While this is appropriate for individual glacier mass balance, 
        it isn't really appropriate when using a profile to extrapolate to other glaciers because one is making 
        big assumptions about mass change in areas that are unsurveyed.  So this method removes those extrapolations
        by masking the top and bottom although removing the bottom is optional with the keyword remove_bottom.
        """
        
        if type(self.name)==list:
            for i in xrange(len(self.name)):
                cum = self.numdata[i].cumsum()
                
                if remove_bottom:
                    logic = N.logical_and(self.numdata[i]==0,N.logical_or(cum==cum[0],cum==cum[-1]))  
                else:
                    logic = N.logical_and(self.numdata[i]==0,cum==cum[-1])
                #print'****************'
                #print logic
                #print N.c_[logic,self.numdata[i]]
                #print'****************'    
                if erase_mean:self.dz[i] = N.ma.masked_array(self.dz[i],logic)
                self.dz25[i] = N.ma.masked_array(self.dz25[i],logic)
                self.dz75[i] = N.ma.masked_array(self.dz75[i],logic)

                self.mask=logic
        else:
            for i in xrange(len(self.name)):
                cum = self.numdata.cumsum()
                
                if remove_bottom:
                    logic = N.logical_and(self.numdata==0,N.logical_or(cum==cum[0],cum==cum[-1]))  
                else:
                    logic = N.logical_and(self.numdata==0,cum==cum[-1])
                #print'****************'
                #print logic
                #print N.c_[self.e,logic,self.numdata]
                #print'****************'    
                if erase_mean:self.dz = N.ma.masked_array(self.dz,logic)
                self.dz25 = N.ma.masked_array(self.dz25,logic)
                self.dz75 = N.ma.masked_array(self.dz75,logic)

                self.mask=logic

    def extend_upper_extrap(self):
        """LAMB fexcludes a portition of the glacier hypsometry if a part of it goes up really high on a peak.  Since we are using the RGI this can 
        leave bins with no values.  For these cases where this is a problem, this will extend the top of the lamb profile to the top of the ERGI glacier bins.
        """
        if not hasattr(self, 'kurtosis'):raise "ERROR: need to run calc_dz_stats method first."
        
        if not (self.dzs_n != 1).all():
            
            w = N.where(self.dzs_n ==1)[0]
            #if len(w) > 10: raise "ERROR: more than 10% of glaciers with only one glacier surveyed"
            
            top = [x for x in w if x >50]
            bottom = [x for x in w if x <=50]
            
            if len(top)>0: 
                repltop = N.min(N.array(top))-1   
                #print top, repltop
                #self.survIQRs2[top]=self.survIQRs2[repltop]
                self.quadsum[top]=self.quadsum[repltop]
                self.dzs_std[top]=self.dzs_std[repltop]
                self.dzs_sem[top]=self.dzs_sem[repltop]
                #self.dzs_mean[top]=self.dzs_mean[repltop]
                #self.dzs_madn[top]=self.dzs_madn[repltop]
                #self.dzs_median[top]=self.dzs_median[repltop]
                ##self.normalp[top]=self.normalp[repltop]
                #self.skewz[top]=self.skewz[repltop]
                #self.skewp[top]=self.skewp[repltop]
                #self.kurtz[top]=self.kurtz[repltop]
                #self.kurtp[top]=self.kurtp[repltop]
                #self.skew[top]=self.skew[repltop]
                #self.kurtosis[top]=self.kurtosis[repltop]
                #self.percentile_5[top]=self.percentile_5[repltop]
                #self.quartile_1[top]=self.quartile_1[repltop]
                #self.percentile_33[top]=self.percentile_33[repltop]
                #self.percentile_66[top]=self.percentile_66[repltop]  
                #self.quartile_3[top]=self.quartile_3[repltop]
                #self.percentile_95[top]=self.percentile_95[repltop]
                #self.interquartile_rng[top]=self.interquartile_rng[repltop]
                #
                    
            if len(bottom)>0:
                replbottom = N.max(N.array(bottom))+1
                self.quadsum[bottom]=self.quadsum[replbottom]
                self.dzs_std[bottom]=self.dzs_std[replbottom]
                self.dzs_sem[bottom]=self.dzs_sem[replbottom]            
            
            
        if not (self.dzs_n != 0).all():
            
            w = N.where(self.dzs_n ==0)[0]
            
            top = [x for x in w if x >50]
            bottom = [x for x in w if x <=50]
            
            if len(top)>0: 
                repltop = N.min(N.array(top))-1   
                self.quadsum[top]=self.quadsum[repltop]
                self.dzs_std[top]=self.dzs_std[repltop]
                self.dzs_sem[top]=self.dzs_sem[repltop]
                self.dzs_mean[top]=self.dzs_mean[repltop]
                self.dzs_madn[top]=self.dzs_madn[repltop]
                self.dzs_median[top]=self.dzs_median[repltop]
                self.skewz[top]=self.skewz[repltop]
                self.skewp[top]=self.skewp[repltop]
                self.kurtz[top]=self.kurtz[repltop]
                self.kurtp[top]=self.kurtp[repltop]
                self.skew[top]=self.skew[repltop]
                self.kurtosis[top]=self.kurtosis[repltop]
                self.percentile_5[top]=self.percentile_5[repltop]
                self.quartile_1[top]=self.quartile_1[repltop]
                self.percentile_33[top]=self.percentile_33[repltop]
                self.percentile_66[top]=self.percentile_66[repltop]  
                self.quartile_3[top]=self.quartile_3[repltop]
                self.percentile_95[top]=self.percentile_95[repltop]
                self.interquartile_rng[top]=self.interquartile_rng[repltop]
                                   
            if len(bottom)>0:
                replbottom = N.max(N.array(bottom))+1

                self.quadsum[bottom]=self.quadsum[replbottom]
                self.dzs_std[bottom]=self.dzs_std[replbottom]
                self.dzs_sem[bottom]=self.dzs_sem[replbottom]
                self.dzs_mean[bottom]=self.dzs_mean[replbottom]
                self.dzs_madn[bottom]=self.dzs_madn[replbottom]
                self.dzs_median[bottom]=self.dzs_median[replbottom]
                self.skewz[bottom]=self.skewz[replbottom]
                self.skewp[bottom]=self.skewp[replbottom]
                self.kurtz[bottom]=self.kurtz[replbottom]
                self.kurtp[bottom]=self.kurtp[replbottom]
                self.skew[bottom]=self.skew[replbottom]
                self.kurtosis[bottom]=self.kurtosis[replbottom]
                self.percentile_5[bottom]=self.percentile_5[replbottom]
                self.quartile_1[bottom]=self.quartile_1[replbottom]
                self.percentile_33[bottom]=self.percentile_33[replbottom]
                self.percentile_66[bottom]=self.percentile_66[replbottom]  
                self.quartile_3[bottom]=self.quartile_3[replbottom]
                self.percentile_95[bottom]=self.percentile_95[replbottom]
                self.interquartile_rng[bottom]=self.interquartile_rng[replbottom]
                
def LambToColumn(data):
    """Convert a dictionary output by GetLambData from rows to columns.  This function is used by GetLambData if the
    'by_column keyword is present.
    """
    out = {}
    for j,column in enumerate(data[0].keys()):out[column]=[]
        
    for i,row in enumerate(data):
        for j,column in enumerate(row.keys()):
            out[column].append(row[column])
    
    for j,column in enumerate(data[0].keys()):
        
        if type(out[column][-1]) == int and type(out[column][0]) == int or \
        type(out[column][-1]) == float and type(out[column][0]) == float:
            #print 'yes'
            try:
                out[column] = N.array(out[column][:])
            except:pass
    return out
    
def partition_dataset(*args,**kwargs):
    """====================================================================================================
    Altimetry.Altimetry.partition_dataset
    Evan Burgess 2013-08-22
    ====================================================================================================
    Purpose:
        This is a convience function that simplifies partitioning the altimetry dataset in anyway the user would like.  
        Simply this function loops through GetLambData and returns a list of Lamb objects.  This function
        assumes you are using the longest interval available for each glacier.  This function is meant to be
        used in conjuction with extrapolate.  Together these two functions will allow the user to estimate the 
        regional mass balance using any set of data and partitioning that they choose.      

    Returns: 
        A 5 element list of the following:lamb,userwheres,notused,whereswo,notswo
        
            lamb        A list of LambObjects for each of the partitioned groups specfied in the paritioning argument
                        These are in the same order as in partitioning argument.  If any of the groups requested have
                        no glaciers in them, that LambObject is excluded. 
                     
            userwheres  The where statements that were used to filter altimetry intervals for each group.  This 
                        combines the where statments in partitioning, apply_to_all and interval_min/max .  Note if no
                        glaciers exist in that group, the where is not output here, and instead will come out in
                        notused.
                    
            notused     If any of the groups specifieid by partitioning have no glaciers in them, that where 
                        statement is returned here.
                    
            whereswo    Same as userwheres but does not include the where statements associated with the apply_to_all
                        argument.  This is useful when used with extrapolate.
                    
            notswo      Same as notused but does not include the where statements associated with the apply_to_all
                        argument.

      
    EXAMPLE:
        lamb,userwheres,notused,whereswo,notswo = partition_dataset(["gltype=0","gltype=1","gltype=2"],
            interval_max=10,interval_min=5,
            applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
    
    ARGUMENT:
        partitioning    A list of strings that would go into where statements that describe each partition individually.  
                        In the example above, in larsen et al. we divide our extrapolation by terminus type. So we
                        have three groups, each with a where statement that says either "gltype=0","gltype=1",
                        or "gltype=2".  These are listed in this first argument.  Do not include the "WHERE or ANDs."
                        This list must be as long as the number of groups you are partitioning.
                    
    KEYWORD ARGUMENTS:
        apply_to_all    There may also be requirments that apply to all of the groups.  In our example above, we don't 
                        want surge glaciers or a few specific outliers.  Requirements for all groups are listed here, as
                        in the example above.  You can list as many or as few (None) as you want.
        
        interval_min
        interval_max    This has a similar effect to apply to all, it is just a easier way to specify requirements
                        on the interval length. Numbers can be entered as an int. (Default = 5,30 for min and max
                        respectively) 

        too_few         When calculating kurtosis we normaly require samples to be larger than 4.  If you happen
                        to be choosing groups with a sample size smaller than 4 set this to None and ignore the 
                        Kurtosis, and for that matter skew etc. as that is a really small sample.  (Default = 4)                    
    ====================================================================================================        
    """

    for k in kwargs:
        if k not in ['interval_min','interval_max','applytoall','too_few']:raise "ERROR: Unidentified keyword present"
    lamb = [] 
    userwheres=[]
    userwheres2=[]
    notused = []
    notused2 = []
    zones=[]
    
    if 'interval_max' in kwargs.keys():intervalsmax = kwargs['interval_max']
    else:intervalsmax=30
    
    if 'interval_min' in kwargs.keys():min_interval = kwargs['interval_min']
    else:interval_min=5
    
    if 'too_few' not in kwargs.keys(): too_few=4
    else: too_few=kwargs['too_few']
    
    print 'too_few %s' % too_few

    for items in iterproduct(*list(args)):
        userwhere =  " AND ".join(items)

        if kwargs:
            if not type(kwargs['applytoall'])==list:kwargs['applytoall']=[kwargs['applytoall']]
            userwhere2 = userwhere+" AND "+" AND ".join(kwargs['applytoall'])
            print userwhere2
            
        out = GetLambData(verbose=False,longest_interval=True,interval_max=intervalsmax,interval_min=interval_min,by_column=True,as_object=True, userwhere=userwhere2,get_hypsometry=True)
        if type(out)!=NoneType:
            userwheres2.append(userwhere2)
            userwheres.append(userwhere)
            lamb.append(out)
            lamb[-1].fix_terminus()
            lamb[-1].remove_upper_extrap(remove_bottom=False)
            lamb[-1].normalize_elevation()
            lamb[-1].calc_dz_stats(too_few=too_few)
            lamb[-1].extend_upper_extrap()
            lamb[-1].calc_mb()
                       
        else:
            notused.append(userwhere)
            notused2.append(userwhere2)
    return lamb,userwheres2,notused2,userwheres,notused

def coords_to_polykml (outputfile, inpt,inner=None, name=None,setcolors=None):
    """Outputs polygons to a kml. Warning this isn't super robust.  But here you can enter an 
    output filepath and an input geometry that would be returned by GetSqlData. Sspefically it will
    take geometries as dictionariers with 'outer' and 'inner' keys to include the 
    outer ring and the inner rings.  This also allows you to set the polygon color.  You can 
    set setcolors='random' and it will make each polygon a random color instead of the same color. 
    """
    colors = ['e6d8ad','8A2BE2','A52A2A','DEB887','5F9EA0','7FFF00','D2691E','FF7F50','6495ED','FFF8DC','DC143C','00FFFF','00008B','008B8B','B8860B','A9A9A9','006400','BDB76B','8B008B','556B2F','FF8C00','9932CC','8B0000','E9967A','8FBC8F','483D8B','2F4F4F','00CED1','9400D3','FF1493','00BFFF','696969','1E90FF','B22222','FFFAF0','228B22','FF00FF','DCDCDC','F8F8FF','FFD700','DAA520','808080']        
    print len(colors)
    c = 0
    #START KML FILE
    kmlf = kml.Kml()
    
    if type(inpt) == dict:
        lst = [inpt]
    
    elif type(inpt) == list:

        if type(inpt[0]) ==list:

            lst=[{}]
            lst[0]['outer'] = inpt
            lst[0]['inner'] = inner
        else: lst = inpt
    
    for i,poly in enumerate(lst):
        
        if not 'name' in poly.keys():
            poly['name']='Glacier'

        if type(poly['inner']) == list: 
            test = type(poly['inner'][0])
        else: 
            test = type(poly['inner'])
            
        if test == NoneType:
            pol = kmlf.newpolygon(name=poly['name'],outerboundaryis=poly['outer'])
        else:
            pol = kmlf.newpolygon(name=poly['name'],outerboundaryis=poly['outer'],innerboundaryis=poly['inner'])

        #APPEARANCE FORMATTING
        if setcolors == 'random': 
            #print 'random'
            color = colors[c]
            if c < 41:c += 1
            else:c=0
        else: color = colors[0]
        pol.style.polystyle.color = kml.Color.hexa(color+'55')
        pol.style.polystyle.outline = 0
            
    kmlf.savekmz(outputfile) 
    
    
def mad (inpu,axis=None,normalized=False):
    """Calculates a Median Absolute Deviation of an input dataset.  MAD can be calculated along a single axis
    if specfied by the axis keyword.  If you would like a normalized MAD (MADn) then set the keyword normalized=True
    """
    
    data = N.ma.masked_array(inpu,N.isnan(inpu))

    if axis == None:
        out = N.ma.median(N.ma.abs(data-N.ma.median(data)))
        if normalized: return 1.4826*out
        else: return out
    else:
        out = []
        print data.shape
        med = N.ma.median(data,axis=axis)

        if axis==1:
            out = N.ma.median(N.ma.abs(data-med[:,None]),axis=1)
        elif axis==0:
            out = N.ma.median(N.ma.abs(data-med[None,:]),axis=0)

        if normalized: return 1.4826*out
        else: return out
       
def extrapolate(user,groups,selections,insert_surveyed_data=None, keep_postgres_tbls=False, export_shp=None,density=0.850, density_err= 0.06,acrossgl_err=0.0):
    """====================================================================================================
    Altimetry.Altimetry.extrapolate
    Evan Burgess 2013-08-22
    ====================================================================================================
    Purpose:
        This function extrapolates to unsurveyed glaciers and returns estimates of mass balance for all glaciers,
        including surveyed glaciers in the ERGI. This function is intended to work with partition dataset where
        partition dataset splits the altimetry dataset up into samples and then this function applies those
        sample mean curves to glaciers of choice.  There are some subltetys to how this works so pay attention here.
        In effort to give the user the maximum flexibility this function will allow you to give yourself results
        that make no sense.  So you must be careful and also examine your outputs.  There is an example below:
        
            
    extrapolate(user,groups,selections,insert_surveyed_data=None, extrap_tbl='extrapolation_curves',keep_postgres_tbls=False, 
        export_shp=None,density=0.850, density_err= 0.06,acrossgl_err=0.0)
    
    ARGUMENTS:
        user            Input a string that states the user name.  This funtion will output a table with the name 
                        alt_result_[user]X where X is 1 or if the user has a table already this script will not over-
                        write so the number will be increased incrementally.  This will prevent different users from
                        confusing their results.
                    
        groups          A list lamb objects output by partition dataset, each element in the list is a single curve
                        that the user intends to apply to some group of glaciers.  It is critical here to note that 
                        the glaciers that receive a specifc elevation profile do NOT need to be at all related to the
                        glaciers that made the profile.  This will be clarified further on.  
                    
        selections      A list of strings that specify where statements that describe where each group from the group 
                        argument should be applied.  This should be of the same length and same intended order of the lamb
                        list presented for the groups argument.  The KEY here is that the user must insure that the 
                        selections together, include EVERY SINGLE glacier in the ergi AND don't ever have overlapping
                        selections either.  Said another way the selections list must be comprehsive of the glacier 
                        inventory and each selection is mututally exclusive of the others.  See the example below for 
                        further clarification.
                    
                    
    KEYWORD ARGUMENTS:
        insert_surveyed_data    Set to a lamb object that includes glaciers, for which, you would like to insert the
                                actual surveyed glacier profile into the regional estimate.  If this keyword is left 
                                blank, we use the extrapolation curves are applied to all glaciers in the selections
                                argument even if they were surveyed glaciers (Default = None)
                    
        
        keep_postgres_tbls      Set to True if the user wishes to retain the output dataset (Default=False).  If so,
                                this table will be called alt_result_[user]X
                            
        export_shp              Set to a pathname if the user would like to output the table as a shpfile for viewing 
                                in a GIS.
    
        density                 Set to the assumed density (Default=0.85)
    
        density_err             Set to the assumed density uncertainty (Default=0.06)
    
        acrossgl_err            Set to the assumed across glacier uncertainty (Default=0.0)
                    
    
    Returns: 
            A dictionary of dictionaries containing partitioned mass balance results. Where glaciers are 
            divided in the following ways:
            A dictionary with the following keys regardless of your partitioned choices:
            
                bysurveyed          Mass balance of glaciers divided by whether they were 
                                    'surveyed' or 'unsurveyed' for the data input.
                bytype              Same but divided by terminus type
                all                 Same but the region as a whole.
                bytype_survey       Same but divided by terminus type and whether they were
                                    'surveyed' or 'unsurveyed' for the data input.
            
                Within each of these groups the summed mass balance is presented in another dictionary with keys:

    area        Total area of group
    totalkgm2   Mean mass balance in m w eq/yr  (yes it says kgm2)
    errkgm2     Mean mass balance error in m w eq/yr  (yes it says kgm2)
    totalgt     Total mass balance Gt/yr 
    errgt       Total mass balance error Gt/yr. Note this does not include the 50% 
                increase in error for tidewater glaciers nor the area
                dependency correction that is discused in larsen et al.  Those 
                should to be added manually if the user wishes.
            
    If the keyword keep_postgres_tbls=True, the result table will be retained in the database and will allow
    the user to query and view this table (in a GIS) to evaluate the extrapolation further.         
      
    EXAMPLE USE WITH GetLambData AND partition_dataset:
    
        surveyeddata = GetLambData(verbose=False,longest_interval=True,interval_max=30,
        interval_min=5,by_column=True,as_object=True)
        surveyeddata.fix_terminus()
        surveyeddata.normalize_elevation()
        surveyeddata.calc_dz_stats()
    
        types = ["gltype=0","gltype=1","gltype=2"]
        lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,
        applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
        print extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False)  
    
        Here the user is first retreiving all of the surveyed glacier data in one 
        lambobject to be applied those glaciers individually as surveyeddata.
    
        Next the user is partitioning the dataset as done in larsen etal by glacier type, 
        we excluding surgers and outlier glaciers because we don't want
        those glaciers to affect the mean profile within the group that will be used for extrapolation.
        
        Lastly, we run extrapolate on those groups, this applies the group extrapolation 
        to each group but we use the where statements include exceptions 
        like surgers. To reiterate, we ran partition_dataset on land/lake/tide w/o surgers.
        But we apply those same curves to land/lake/tides but to all glaciers
        including surgers.  Here, ther user has then inserted the surveyed data so surveyed glacier mass 
        balance is included on an individual glacier basis.  Lastly here we drop the output_table, 
        please do this as the output table is several Gb. 
         
    ====================================================================================================        
    """

    #ENSURING STATS HAVE BEEN RUN ON GROUP FIRST
    for grp in groups:
        if not hasattr(grp,'interquartile_rng'):raise "Run statistics on groups first"
    
    tablename = create_extrapolation_table(user=user) 
  
    ######################################################
    #NOW INSERTING DATA THAT APPLIES TO THE GROUP OF GLACIERS INCLUDING UNSURVEYED GLACIERS AND ERROR FOR SURVEYED GLACIERS
    
    buffer2 = StringIO.StringIO()
    buffer2.write("BEGIN;\n")
       
    #UNSURVEYED GLACIER DATA INTO RESULT TABLE    
    for grp,sel in zip(groups,selections):
        
        for i in N.linspace(0,99,100):
            
            #SETTING WHICH BINS WILL GET THE STATS APPLIED
            wheres=[]
            if sel!='':wheres.append(sel)
            
            #SINCE THE DATA IS SCALED TO 0-100 THERE IS ACTUALLY A POSSIBILITY OF 101 VALUES.  
            # SINCE THEY ARE ALL 0 UP AT THE TOP WE JUST EXTEND THAT TO THE TOP BIN.
            if i != 99:
                wheres.append("normbins={norme:.2}".format(norme=grp.norme[i]))
            else:
                wheres.append("normbins IN (0.99,1)")
                
            #IF USERS DON'T SPECIFY SURVEYED DATA TO INSERT, WE WILL JUST EXTRAPOLATE TO SURVEYED GLACIERS
            wheres2 = wheres[:]
            if type(insert_surveyed_data)!=NoneType: 
                wheres2.append("ergiid NOT IN (%s)" % ','.join(grp.ergiid.astype(str)))        
            
            where = " AND ".join(wheres2)

            #THE UPDATE STATEMENT FOR UNSURVEYED DATA ONLY

            buffer2.write("""UPDATE {table} \nSET (mean,median,std,sem,iqr,q1,q3,perc5,perc95,surveyed,error) = 
    ({mean},{median},{std},{sem},{iqr},{q1},{q3},{perc5},{perc95},{surveyed},{error})
    WHERE {where};\n""".format(
            mean=grp.dzs_mean[i],median=grp.dzs_median[i],std=grp.dzs_std[i],sem=grp.dzs_sem[i],
                    iqr=grp.interquartile_rng[i],q1=grp.quartile_1[i],q3=grp.quartile_3[i],perc5=grp.percentile_5[i],
                    perc95=grp.percentile_95[i],surveyed="'f'",error=grp.dzs_sem[i],
                    table=tablename,norme=grp.norme[i],where=where))
            
            #IF SURVEYED GLACIER DATA IS PROVIDED WE NEED TO INSERT THE GROUP SURVEYED GLACIER ERROR
            #THIS IS SEPARATE FROM THE UNCERTAINTY FOR INDIVIDUAL GLACIERS
            
            if type(insert_surveyed_data)!=NoneType: 
                wheres.append("ergiid IN (%s)" % ','.join(grp.ergiid.astype(str)))        
            
                where = " AND ".join(wheres)
                
                # INSERTING SURVEYED UNCERTAINTY AS THAT UNCERTAINTY IS FOR THE GROUP AND NOT THE 
                # INDIVIDUAL GLACIERS THUS EASIEST TO DO HERE
                buffer2.write("""UPDATE {table} \nSET (quadsum,error) = ({quadsum},{quadsum}) 
                WHERE {where};\n""".format(quadsum=grp.quadsum[i],table=tablename,where=where))
            
    buffer2.write("COMMIT;\n")
    buffer2.seek(0)
    
    #UPDATING TABLE WITH UNSURVEYED GLACIER DATA
    print "Commiting data for unsurveyed glaciers..."
    conn,cur = ConnectDb()
    cur.execute(buffer2.read())
    conn.commit()
    cur.close()
    buffer=None
    

    #######################################################
    buffer = StringIO.StringIO()
    buffer.write("BEGIN;\n")
       
    #SURVEYED GLACIER DATA INTO RESULT TABLE.  HERE WE ARE INSERTING THE SURVEYED DATA FOR SPECFIC GLACIERS   
    if type(insert_surveyed_data)!=NoneType:
        for eid,ergid in enumerate(insert_surveyed_data.ergiid):
            for i in N.linspace(0,99,100):
                
                #SINCE THE DATA IS SCALED TO 0-100 THERE IS ACTUALLY A POSSIBILITY OF 101 VALUES. 
                # SINCE THEY ARE ALL 0 UP AT THE TOP WE JUST EXTEND THAT TO THE TOP BIN.
                if i != 99:
                    where = "ergiid={ergiid} AND normbins={norme:.2}".format(ergiid=ergid, norme=insert_surveyed_data.norme[i])
                else:
                    where = "ergiid={ergiid} AND normbins IN (0.99,1)".format(ergiid=ergid, 
                                                                              norme=insert_surveyed_data.norme[i])
                    
                
                #THE UPDATE QUERY FOR SURVEYED DATA ONLY
                buffer.write("""UPDATE {table} \nSET (mean,surveyed,singl_std) = 
                ({mean},{surveyed},{singl_std}) WHERE {where};\n""".format(
                mean=insert_surveyed_data.normdz[eid][i],quadsum=insert_surveyed_data.quadsum
                        [i],surveyed="'t'",error=insert_surveyed_data.quadsum[i],
                        table=tablename,where=where,singl_std=insert_surveyed_data.survIQRs[eid][i]))
 
    buffer.write("COMMIT;\n")
    buffer.seek(0)
    
    #UPDATING TABLE WITH SURVEYED GLACIER DATA
    print "Commiting data for surveyed glaciers..."
    conn,cur = ConnectDb()
    cur.execute(buffer.read())
    conn.commit()
    cur.close()
    buffer=None
        
    #THE USER CAN EXPORT THE OUTPUT TABLE AS A SHAPEFILE IF REQUESTED               
    if type(export_shp) != NoneType:
        print "Exporting To Shpfile"
        sys.stdout.flush()
        os.system("%s -f %s -h localhost altimetry %s" % (init.pgsql2shppath,export_shp,tablename))

    print "Summing up totals" 
    sys.stdout.flush()
    start_time = time.time()
    out = {}
    #GETTING STATS TO OUTPUT
    out['bysurveyed'] =    GetSqlData("SELECT surveyed,SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY surveyed;" %         (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,tablename))
    out['bytype_survey'] = GetSqlData("SELECT gltype, surveyed, SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype,surveyed;" % (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,tablename))
    out['bytype'] =        GetSqlData("SELECT gltype,           SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype;" %          (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,tablename))
    out['all'] =           GetSqlData("SELECT                   SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s;" %                          (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,tablename))
        
    if not keep_postgres_tbls:remove_extrap_tables(user,tables=tablename)

    return out
        
                        
def glaciertype_to_gltype(indata):
    out = []
    for i in indata:
        if re.search('land',i):out.append(0)
        elif re.search('tidewater',i):out.append(1)
        elif re.search('lake',i):out.append(2)
    return out
    
def full_plot_extrapolation_curves(data,samples_lim=None,err_lim=None,color=None):
    """====================================================================================================
    Altimetry.Altimetry.full_plot_extrapolation_curves
    Evan Burgess 2015-04-22
    ====================================================================================================
    Purpose:
        Plot statistics for a lambobject. This is the function used in Figures S8-S10     

    Returns: 
        A matplotlib figure class
         
    ARGUMENT:
        data            A lamb object with at least normalize_elevation() and calc_dz_stats run.
                    
    KEYWORD ARGUMENTS:
        samples_lim     Set the y_axis limit of number of samples plot
        
        err_lim         Set the y_axis limit for the error plot (right axis). 
        color           color of the lines in the top plot
    ====================================================================================================        
    """
    #INPUT VARIABLES
    alphafill = 0.1
    if type(color)==NoneType: color='k'
    
    #FIGURE SETTINGS 
    fig = plt.figure(figsize=[6,10])
    ax = fig.add_axes([0.11,0.59,0.79,0.4])
    plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
    
    #TOP PLOT
    for dz in data.normdz:ax.plot(data.norme,dz,'-',color=color,linewidth=0.5,alpha=0.5)
    ax.plot(data.norme,data.dzs_mean,'-k',linewidth=2,label='Mean')
    ax.plot(data.norme,data.dzs_median,'--k',linewidth=2,label='Median')

    ax.plot(data.norme,data.dzs_mean+data.dzs_sem,'-r',linewidth=0.7,label= "Unsurveyed Error Estimate")
    ax.plot(data.norme,data.dzs_mean-data.dzs_sem,'-r',linewidth=0.7)
    ax.fill_between(data.norme,data.dzs_mean+data.dzs_std,data.dzs_mean-data.dzs_std,alpha=alphafill,color= 'black',lw=0.01)
    
    #LIMITS, LABELS, LEGEND
    ax.set_ylabel("Elevation Change (m w. eq. yr"+"$\mathregular{^{-1})}$")
    ax.set_ylim([-10,3])
    ax.set_xlim([0,1])
    ax.set_ylim([-10,12])    
    plt.legend(loc=4,fontsize=11)
    
    #BOTTOM PLOT
    ax2 = fig.add_axes([0.11,0.13,0.79,0.15])
    plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
    
    #PLOTTING 
    ax2.plot(data.norme,N.zeros(data.norme.size),'-',color='grey')
    ax2.plot(data.norme,N.array(data.kurtosis)-3,'k--',label='Excess Kurtosis',lw=1.5)     
    ax2.plot(data.norme,N.array(data.skew),'k-',label='Skewness',lw=1.2)
    
    #LIMITS, LABELS, LEGEND
    ax2.set_ylim([-6,6])
    ax2.set_ylabel('Test Statistic',color='k')
    ax2.set_xlabel('Normalized Elevation')
    plt.legend(loc='upper center', bbox_to_anchor=(0.24, -0.3),ncol=1, fancybox=False, shadow=False,fontsize=11)
    
    #ADDING SECOND Y AXIS AND PLOTTING
    ax3 = ax2.twinx()
    ax3.plot(data.norme,N.zeros(data.norme.size)+0.05,'-',color='grey')
    ax3.plot(data.norme,N.sqrt(N.array(data.normalp)),'r-',label='Shapiro-Wilk')

    #FORMATTING THAT AXIS, LIMITS AND LEGEND
    for t in ax3.get_yticklabels():t.set_color('r')
    ax3.set_ylabel('p-values',color='r')
    ax3.set_ylim([0,1.1])
    plt.legend(loc='upper center', bbox_to_anchor=(0.78, -0.3),ncol=2, fancybox=False, shadow=False,fontsize=11) 
    
          
    #MIDDLE PLOT
    ax4 = fig.add_axes([0.11,0.38,0.79,0.18])
    ax4.plot(data.norme,data.dzs_n,'k',label='n Samples')

    #LIMITS LABELS, LEGEND
    ax4.set_ylabel('N Samples')
    ax4.set_ylim([0,N.max(data.dzs_n)*1.1])
    ax4.set_ylim(samples_lim)
    plt.legend(loc='upper center',bbox_to_anchor=(0.24, -0.1),ncol=1, fancybox=False, shadow=False,fontsize=11) 
    
    #ADDING SECOND Y AXIS AND PLOTTING
    ax5 = ax4.twinx()
    ax5.plot(data.norme,data.quadsum,'b-',label='Surveyed Error Estimate')
    ax5.plot(data.norme,data.dzs_sem,'r-',label='Unsurveyed Error Estimate')
    ax5.set_ylim(err_lim)
    ax5.set_ylabel("Uncertainty (m w. eq. yr"+"$\mathregular{^{-1})}$")
    
    #LEGEND
    plt.legend(loc='upper center',bbox_to_anchor=(0.78, -0.1),ncol=1, fancybox=False, shadow=False,fontsize=11) 
    
    #ANNOTATING PLOTS WITH ABCs
    ax.text(0.03,0.94,"A",fontsize=15, fontweight='bold',transform=ax.transAxes)
    ax4.text(0.03,0.83,"B",fontsize=15, fontweight='bold',transform=ax4.transAxes)
    ax2.text(0.03,0.83,"C",fontsize=15, fontweight='bold',transform=ax2.transAxes)
 
    return fig
    
def create_extrapolation_table(user=None,schema=None,table=None):
    """====================================================================================================
    Altimetry.Altimetry.create_extrapolation_table
    Evan Burgess 2015-04-22
    ====================================================================================================
    Purpose:
        This function creates an extrapolation table and controls the names of the tables such that they will 
        not be confused between users. The point here is that altimetryextrapolation table is reserved for 
        results in Larsen et al. 2015.  As users play with the data and other extrapolations they can rerun
        the same code to create new tables that should not be confused.  This code makes a table called:
            alt_results_[user]X  where X is 1 if this user has no existing table with their name and will
            incrementally increase if the user has tables already written.

    Returns: 
        The new created table name as a string.
         
    ARGUMENTS:
        user            A username to be inserted into the table  (REQUIRED)
                    

        schema          Set the schema. (DEFAULT='public')
        
        table           The user can force another table name here but this tablename will not be 
                        recognized by remove_extrap_tables.
    ====================================================================================================        
    """
    if user==None:raise "ERROR: Must Specify User"
    
    if schema==None: schema = 'public'
    if table==None:
        
        #LOOKING FOR TABLES THIS USER HAS CREATED.  IF THE USER HAS MORE THAN ONE TABLE OPEN THEN NUMBERS WILL INCREASE SEQUENTIALLY  THIS RETURNS THE NEXT TABLE NUMBER AVAILABLE
        n = GetSqlData("SELECT substring(table_name FROM 'alt_result_{user}(\d+)') FROM information_schema.tables WHERE table_name SIMILAR TO 'alt_result_{user}\d+';".format(user=user))
        if n==None:table = "alt_result_{user}1".format(user=user)
        else: 
            number = N.array(n['substring']).astype(int).max()+1
            table = "alt_result_{user}{number}".format(user=user,number=number)        
    
    sql = """
SELECT b.ergibinsid as resultid,b.ergiid,b.area,e.area as glarea,b.albersgeom,b.bins,b.normbins,e.gltype,e.surge,e.name,e.region INTO {schema}.{table} FROM ergibins as b INNER JOIN ergi_mat_view AS e ON b.ergiid=e.ergiid;

CREATE SEQUENCE {table}_resultid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--ALTER TABLE {schema}.{table}_resultid_seq OWNER TO {user};
ALTER SEQUENCE {table}_resultid_seq OWNED BY {table}.resultid;
ALTER TABLE ONLY {table} ALTER COLUMN resultid SET DEFAULT nextval('{table}_resultid_seq'::regclass);
ALTER TABLE ONLY {table}
    ADD CONSTRAINT {table}_pkey PRIMARY KEY (resultid);
CREATE INDEX {table}ergiid ON {table} USING btree (ergiid);
CREATE INDEX {table}normbins ON {table} USING btree (normbins);
CREATE INDEX {table}gltype ON {table} USING btree (gltype);
CREATE INDEX {table}region ON {table} USING btree (region);
CREATE INDEX {table}glarea ON {table} USING btree (glarea);

CREATE INDEX {table}geom ON {table} USING gist (albersgeom);
ALTER TABLE ONLY {table}
    ADD CONSTRAINT {table}fkergi FOREIGN KEY (ergiid) REFERENCES ergi(ergiid) MATCH FULL;
ALTER TABLE {table} ADD COLUMN mean double precision;
ALTER TABLE {table} ADD COLUMN median real;
ALTER TABLE {table} ADD COLUMN std real;
ALTER TABLE {table} ADD COLUMN sem double precision; 
ALTER TABLE {table} ADD COLUMN quadsum double precision; 
ALTER TABLE {table} ADD COLUMN iqr double precision;  
ALTER TABLE {table} ADD COLUMN stdlow real; 
ALTER TABLE {table} ADD COLUMN stdhigh real; 
ALTER TABLE {table} ADD COLUMN q1 real; 
ALTER TABLE {table} ADD COLUMN q3 real; 
ALTER TABLE {table} ADD COLUMN  perc5 real;
ALTER TABLE {table} ADD COLUMN  perc95 real;
ALTER TABLE {table} ADD COLUMN  surveyed boolean;
ALTER TABLE {table} ADD COLUMN  error double precision;
ALTER TABLE {table} ADD COLUMN  singl_std real;

COMMENT ON TABLE {table} IS 'This table is not raw data, it is a results table that is regenerated anytime someone runs extrapolate.  It can be exported as a shapefile as contains all of the information one needs to interpret the altimetry results in Larsen et al., 2015, both on the glacier scale and on the regional scale. When doing analysis, it is often easiest just to query this table.  This table has many duplicate fields but it doesn''''t really work to make it a vew because it is generated with a lot of python in addition to SQL.  It could just entail added fields to ergibins but since this table is changed everytime the extrapolation is run, I think it is better to keep ergibins untouched and change this table more so.  My experience was this runs way faster as well.  The units in this table are still (m/yr) so must be multiplied by 0.85 to get volume.';
COMMENT ON COLUMN {table}.resultid IS 'Primary Key';
COMMENT ON COLUMN {table}.ergiid IS 'Foreign Key to ergi';
COMMENT ON COLUMN {table}.name IS 'Glacier Name';
COMMENT ON COLUMN {table}.gltype IS 'Terminus Type 0=land, 1=tide,2=lake';
COMMENT ON COLUMN {table}.surge IS 'Surge Type?';
COMMENT ON COLUMN {table}.glarea IS 'Total Glacier Area (not area of bin/polygon)';
COMMENT ON COLUMN {table}.bins IS 'Middle elevation of bins (m)';
COMMENT ON COLUMN {table}.normbins IS 'Nomalized position of bins (from ergibins)';
COMMENT ON COLUMN {table}.area IS 'Area of bin/polygon (m**2)';
COMMENT ON COLUMN {table}.region IS 'Region defined by Larsen et al. 2015';
COMMENT ON COLUMN {table}.mean IS 'Rate of surface elevation change (m/yr)  For unsurveyed glaciers this is the sample mean, for surveyed glaciers this is the lamb median line.';
COMMENT ON COLUMN {table}.median IS 'For unsurveyed glaciers this is the median of the sample, disregard for surveyed glaciers (m/yr)';
COMMENT ON COLUMN {table}.std IS 'For unsurveyed glaciers this is the STDDEV of the sample, disregard for surveyed glaciers  (m/yr)';
COMMENT ON COLUMN {table}.sem IS 'For unsurveyed glaciers this is the SEM of the sample, disregard for surveyed glaciers (m/yr)';
COMMENT ON COLUMN {table}.quadsum IS '?';
COMMENT ON COLUMN {table}.iqr IS 'For unsurveyed glaciers this is the IQR of the sample, disregard for surveyed glaciers (m/yr)';
COMMENT ON COLUMN {table}.stdlow IS 'For unsurveyed glaciers this is the STDDEV, low boundary of the sample, disregard for surveyed glaciers (m/yr)';
COMMENT ON COLUMN {table}.stdhigh IS 'For unsurveyed glaciers this is the STDDEV, high boundary of the sample, disregard for surveyed glaciers (m/yr)';
COMMENT ON COLUMN {table}.q1 IS 'For unsurveyed glaciers this is the first quartile of the sample, disregard for surveyed glaciers (m/yr)';
COMMENT ON COLUMN {table}.q3 IS 'For unsurveyed glaciers this is the third quartile of the sample, disregard for surveyed glaciers (m/yr)';
COMMENT ON COLUMN {table}.perc5 IS 'For unsurveyed glaciers this is the 5th percentile of the sample, disregard for surveyed glaciers (m/yr)';
COMMENT ON COLUMN {table}.perc95 IS 'For unsurveyed glaciers this is the 95th percentile of the sample, disregard for surveyed glaciers (m/yr)';
COMMENT ON COLUMN {table}.surveyed IS 'Was the glacier surveyed?';
COMMENT ON COLUMN {table}.error IS 'This error is the SEM for unsurveyed glaciers and the quadrature sum for surveyed glaciers  (m/yr)';
COMMENT ON COLUMN {table}.albersgeom IS 'Alaska Albers Geometry';
COMMENT ON COLUMN {table}.singl_std IS 'Error of a single glacier (m/yr)';
COMMENT ON COLUMN {table}.region IS 'Region defined by Larsen et al. 2015';
""".format(table=table,schema=schema,user=user)
    #print sql
    buffer = StringIO.StringIO()
    buffer.write(sql)
    buffer.seek(0)
   
    conn,cur = ConnectDb()
    cur.execute(buffer.read())
    conn.commit()
    conn.set_isolation_level(0)
    cur.execute("VACUUM (ANALYZE) %s" % table)
    conn.commit()
    conn.set_isolation_level(1)
    cur.close()

    return table

def remove_extrap_tables(user,tables=None,schemas=None):
    """====================================================================================================
    Altimetry.Altimetry.remove_extrap_tables
    Evan Burgess 2015-04-22
    ====================================================================================================
    Purpose:
        This function removes extrapolation table/s created by the specified user and the naming convention
        created by create_extrapolation_table.  If just a user is specified, this removes all tables by
        that user.  However, a list of tables as strings can be input to remove specfic tables only.  

         
    ARGUMENTS:
        user            A username for which their tables are to be deleted  (REQUIRED)

        schema          Set the schema. This can be left blank as the script can figure that out.
        
        tables          A list of specific tables to remove. 
    ====================================================================================================        
    """
    #LOOKING FOR TABLES BY THIS USER
    if type(tables)==NoneType:
        #print "SELECT table_schema, substring(table_name FROM '(alt_result_{user}\d+)') as t FROM information_schema.tables WHERE table_name SIMILAR TO 'alt_result_{user}\d+';".format(user=user)
        t = GetSqlData("SELECT table_schema, substring(table_name FROM '(alt_result_{user}\d+)') as t FROM information_schema.tables WHERE table_name SIMILAR TO 'alt_result_{user}\d+';".format(user=user))
        if type(t)==NoneType:
            print "No tables by this user to delete."
            return
        tables = t['t']
        schemas = t['table_schema']
    elif type(schemas)==NoneType:
        if type(tables)==list:
            if len(tables)>1:tables2 = "','".join(list(tables))
            if len(tables)==1:tables2 = tables[0]
        else: 
            tables2=tables
            
        schemas = GetSqlData("SELECT table_schema FROM information_schema.tables WHERE table_name IN ('{tables}');".format(tables=tables2))['table_schema']

    sql = """ALTER TABLE ONLY {schema}.{table} DROP CONSTRAINT IF EXISTS {table}fkergi;
DROP INDEX IF EXISTS {schema}.{table}geom;
DROP INDEX IF EXISTS {schema}.{table}ergiid;
DROP INDEX IF EXISTS {schema}.{table}normbins;
DROP INDEX IF EXISTS {schema}.{table}gltype;
DROP INDEX IF EXISTS {schema}.{table}region;
DROP INDEX IF EXISTS {schema}.{table}glarea;
ALTER TABLE ONLY {schema}.{table} DROP CONSTRAINT IF EXISTS {table}_pkey;
ALTER TABLE {schema}.{table} ALTER COLUMN resultid DROP DEFAULT;
DROP SEQUENCE IF EXISTS {schema}.{table}_resultid_seq;
DROP TABLE {schema}.{table};
"""

    if type(tables) in (list, N.ndarray):
        if len(tables)>1:outsql = "\n".join([sql.format(table=t,schema=s) for t,s in zip(tables,schemas)])
        else: outsql = sql.format(table=tables[0],schema=schemas[0])
    else:outsql = sql.format(table=tables,schema=schemas[0])
    #print outsql
    buffer = StringIO.StringIO()
    buffer.write(outsql)
    buffer.seek(0)
   
    conn,cur = ConnectDb()
    cur.execute(buffer.read())
    conn.commit()
    cur.close()

def destable(table):
    """Prints the full comment fields of a table.  Just specify the table name.
    """

    def hard_return(a,length = 70):
    
        if len(a)<length:return a
        
        hard = len(a)/length
        cut = []
        last=0
        for m in re.finditer(r"\s+", a):
            pos = int(m.start() % length)
            if pos < last:cut.append(m.end())
            last=pos
            
        out = []
        last = 0
        for i in cut:
            out.append(a[last:i])
            last=i
        out.append(a[last:])
        return "\n                |                 |  ".join(out)
        
    oid=GetSqlData("""SELECT c.oid
    FROM pg_catalog.pg_class c
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname ~ '^(%s)$'
    AND pg_catalog.pg_table_is_visible(c.oid);
    """ % table)['oid'][0]
    
    
    des = GetSqlData("""SELECT a.attname,
    pg_catalog.format_type(a.atttypid, a.atttypmod),
    pg_catalog.col_description(a.attrelid, a.attnum)
    FROM pg_catalog.pg_attribute a
    WHERE a.attrelid = '%s' AND a.attnum > 0 AND NOT a.attisdropped
    ORDER BY a.attnum;""" % oid)
    
    tdes = GetSqlData("""SELECT description FROM pg_description JOIN pg_class ON pg_description.objoid = pg_class.oid
    WHERE relname = '%s' AND objsubid=0;""" % table)['description'][0]
    
    
    
    comment = [hard_return(d)for d in des['col_description']]

    print "Table Name: %s" % table
    print "Table Description: \n\n\t%s\n\n" % (tdes)
    print "     Column     |    Data Type    |           Description"
    print "----------------+-----------------+---------------------------------"
    for t,f,c in zip(des['attname'],des['format_type'],comment):
        print "%15s | %15s | %s" % (t,f,c)
    
