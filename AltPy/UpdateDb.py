import os
import sys
import re

sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

def get_ftp_data(connectionString_ftp, connectionString_db, glacierNames, tempDirectory):
    '''
    Instantiaties a connection to a remote FTP site to acquire the raw altimetry data

    Parameters
    ----------
    connectionString_ftp: a list of key value pairs containing username, password, hostname
                    needed to connect to the ftp site
    connectionString_db: a list of key value pairs containing username, password, hostname, port
                    needed to connect to the postgres database
    glacierNames: a pandas dataframe of glacier names that you want to acquire
                name: (string) Note, use the "first name" only, e.g. 
                            "Tsina" not "Tsina Glacier".
                glimsid: (string) the Global Land Ice Measurements from Space ID 
    tempDirectory: a temporary location to store the raw lamb data files (mmm...raw lamb)

    Actions: updates the AWS database with records imported from UAF

    Returns: indication of whether the upload was a success
    
    '''
    import paramiko
    import AltPy.Altimetry as alt
    
    cs = connectionString_ftp

    paramiko.util.log_to_file("paramiko.log")

    # Open a transport
    host,port = cs['host'],22
    transport = paramiko.Transport((host,port))

    # Auth    
    username,password = cs['username'],cs['password']
    transport.connect(None,username,password)

    # Go!    
    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        engine,cursor = alt.ConnectDb(connectionString_db)
    except:
        return 'can not connect to the database'

    for glacierName in glacierNames['name']:
        sftp.chdir('/home/laser/analysis/' + glacierName + '/results/')
        for fileName in sftp.listdir():
            if fileName.endswith(".output.txt"):
                sftp.get(fileName, tempDirectory + fileName)
                # I guess previously we were looking these up in the ice2oceans db?
                #glimsid = (str(lambList.loc[lambList["name"] == glacierName]["glimsid"].values[0])) 
                glimsid = glacierNames[glacierNames['name']==glacierName]['glimsid'].values[0]
                sql = lamb_sql_generator(tempDirectory + fileName, glimsid, 'lamb')
                cursor.execute(sql)  
    engine.commit() 
    cursor.close()
    return 'data successfully uploaded'
 

def lamb_sql_generator(lambfile,glimsid,tableName):
    '''
    This generates the SQL necessary to INSERT new lines of LAMB data to the database.

    Parameters
    ----------
    lambfile: (string) the full name of the text file stored on the UAF ftp server to be ingested
    glimsid: (string) the Global Land Ice Measurements from Space ID 
    tableName: (string) the name of the table in the database into which the data will be uploaded
    
    Returns: a SQL string to be passed to the database for data ingest

    Notes: this is a low-level way to generate SQL strings but it works. Future upgrades should consider using pandas/geopandas or SQLAlchemy

    '''

    import numpy as np
    import time
    from time import mktime
    import datetime

    #READING LAMBFILE INTO DICTIONARY    
    data = ReadLambFile(lambfile)

    data['date1'] = datetime.date.fromtimestamp(mktime(time.strptime(data['date1'],"%Y-%m-%d %H:%M:%S")))
    data['date2'] = datetime.date.fromtimestamp(mktime(time.strptime(data['date2'],"%Y-%m-%d %H:%M:%S")))
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
            
            if type(data[key]) == np.ndarray:
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


def ReadLambFile(lambfile):

    '''
    This function has all the low-level code needed to import the UAF altimetry raw data files

    Parameters
    ----------
    lambfile: (string) the full name of the text file stored on the UAF ftp server to be ingested
    
    Returns: a dictionary with all the data formatted for ingest into the database


    '''

    import datetime
    import numpy as np
    import re
    import os
    
    f = open(lambfile)
    
    f.readline()# header trashed
    
    # reading glacierwide data on line 1
    (year1,jday1,year2,jday2,volmodel,vol25diff,vol75diff,balmodel,bal25diff,bal75diff) = [float(field) for field in f.readline().split()]
    
    # converting to datetime objects
    date1 = datetime.datetime(int(year1), 1, 1) + datetime.timedelta(int(jday1) - 1)
    date2 = datetime.datetime(int(year2), 1, 1) + datetime.timedelta(int(jday2) - 1)
    
    # vertically binned data - READING
    e=np.array([])
    dz=np.array([])
    dz25=np.array([])
    dz75=np.array([])
    aad=np.array([])
    masschange=np.array([])
    massbal=np.array([])
    numdata=np.array([])
    f.readline()  #second header trashed
    for line in f:
        (e_add,dz_add,dz25_add,dz75_add,aad_add,masschange_add,massbal_add,numdata_add) = [float(field) for field in line.split()]
        e = np.append(e,int(e_add))
        dz = np.append(dz,dz_add)
        dz25 = np.append(dz25,dz25_add)
        dz75 = np.append(dz75,dz75_add)
        aad = np.append(aad,aad_add)
        masschange = np.append(masschange,masschange_add)
        massbal = np.append(massbal,massbal_add)
        numdata = np.append(numdata,numdata_add)
    e[2] = e[2].astype(int)
    e[1] = e[1].astype(int)
    # DEALING WITH THE FACT THAT LAMB BINNING LABLES THE BOTTOM OF THE BIN AND WE WANT THE CENTER
    e += (e[2]-e[1])/2    
    numdata = numdata.astype(int)   
    
    #GETTING GLACIER NAME FROM FILENAME
    name = re.findall('(^[^\.]+)\.',os.path.basename(lambfile))[0]
    
    date1 = str(date1)
    date2 = str(date2)
    volmodel = str(volmodel)
    vol25diff = str(vol25diff)
    vol75diff = str(vol75diff)
    balmodel = str(balmodel)
    bal25diff = str(bal25diff)
    bal75diff = str(bal75diff)
    e = e.astype(int).astype(str)
    dz = dz.astype(str)
    dz25 = dz25.astype(str)
    dz75 = dz75.astype(str)
    aad = aad.astype(str)
    masschange = masschange.astype(str)
    massbal = massbal.astype(str)
    numdata = numdata.astype(str) 
    glimsid = str(0)

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

