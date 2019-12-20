import pandas as pd
import Altimetry as alt
import UpdateDb as udb
import pandas as pd
import paramiko

# just do this once
engine.execute("CREATE TABLE lamb (lambid serial PRIMARY KEY, glimsid character varying(14), date1 date, date2 date, \
               interval smallint, volmodel real, vol25diff real,vol75diff real, balmodel real, bal25diff real, \
               bal75diff real,e integer[],dz real[],dz25 real[],dz75 real[],aad real[],masschange real[], \
               massbal real[],numdata integer[]);")

# get the list of glaciers to read in; for now just a single glacier for testing 

lambList = ['Tsina']

paramiko.util.log_to_file("paramiko.log")

# Open a transport
host,port = cs['host'],22
transport = paramiko.Transport((host,port))

# Auth    
username,password = cs['username'],cs['password']
transport.connect(None,username,password)

# Go!    
sftp = paramiko.SFTPClient.from_transport(transport)

sftp.chdir('/home/laser/analysis/')

for glacierName in lambList:
    print(glacierName)
    sftp.chdir(glacierName + '/results/')
    for fileName in sftp.listdir():
            if fileName.endswith(".output.txt"):
                sftp.get(fileName, fileName)
                glimsid = (str(lambList.loc[lambList["name"] == glacierName]["glimsid"].values[0])) 
                sql = udb.lamb_sql_generator(fileName, glimsid, 'lamb')
                engine.execute(sql)


surveyeddata = alt.GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True, as_object=True)
surveyeddata.fix_terminus()
surveyeddata.normalize_elevation()
surveyeddata.calc_dz_stats()

types = ["gltype=0","gltype=1","gltype=2"]
lamb,userwheres,notused,whereswo,notswo = alt.partition_dataset(types,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
results = alt.extrapolate('guest',lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True)  
=surveyeddata,keep_postgres_tbls=False) 


