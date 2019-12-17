import pandas as pd
import pysftp
import Altimetry as alt
import UpdateDb as udb
from sqlalchemy import create_engine
from matplotlib.pyplot import *
import matplotlib.pyplot as plt
import settings as s
import pandas as pd

# connection string info from settings.py
cs = getattr(s,'defaulthost')

engine = create_engine('postgresql://' + cs['user'] + ':' + cs['password'] + '@' + cs['host'] + ':' + cs['port'] + '/' + cs['dbname'])

# just do this once
engine.execute("CREATE TABLE lamb (lambid serial PRIMARY KEY, glimsid character varying(14), date1 date, date2 date, \
               interval smallint, volmodel real, vol25diff real,vol75diff real, balmodel real, bal25diff real, \
               bal75diff real,e integer[],dz real[],dz25 real[],dz75 real[],aad real[],masschange real[], \
               massbal real[],numdata integer[]);")

# connection string info from settings.py
cs = getattr(s,'BairdUAF')

sftp = pysftp.Connection(cs['host'], username=cs['user'], password=cs['password'])

# get the list of glaciers to read in 

lambList = pd.read_sql('lambnames',engine)
 
with sftp.cd('/home/laser/analysis/'):
    for glacierName in lambList['name']:
        print(glacierName)
        if sftp.exists(glacierName + '/results'):
            with (sftp.cd(glacierName + '/results/')):
                for fileName in sftp.listdir():
                    if fileName.endswith(".output.txt"):
                        sftp.get(fileName)
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


