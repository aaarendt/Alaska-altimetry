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
cs = getattr(s,'localhost_SurfaceBook')

engine = create_engine('postgresql://' + cs['user'] + ':' + cs['password'] + '@' + cs['host'] + ':' + cs['port'] + '/' + cs['dbname'])

# just do this once
engine.execute("CREATE TABLE lambtest (gid serial PRIMARY KEY, rgiid character varying(14), date1 date, date2 date, \
               interval smallint, volmodel real, vol25diff real,vol75diff real, balmodel real, bal25diff real, \
               bal75diff real,e integer[],dz real[],dz25 real[],dz75 real[],aad real[],masschange real[], \
               massbal real[],numdata integer[]);")

# connection string info from settings.py
cs = getattr(s,'BairdUAF')

sftp = pysftp.Connection(cs['host'], username=cs['user'], password=cs['password'])

notInRGI = []
with sftp.cd('/home/laser/analysis/'):
    folderList = sftp.listdir()
    for glacierName in folderList:
        print(glacierName)
        if sftp.exists(glacierName + '/results'):
            with (sftp.cd(glacierName + '/results/')):
                for fileName in sftp.listdir():
                    if fileName.endswith(".output.txt"):
                        sftp.get(fileName)
                        query = "SELECT rgiid from modern WHERE name LIKE '" + glacierName + "%'"
                        try:
                            rgiid = str(alt.GetSqlData(query)['rgiid'][0])
                        except:
                            notInRGI.append(glacierName)
                        sql = udb.lamb_sql_generator(fileName, rgiid, 'lambtest')
                        engine.execute(sql)

surveyeddata = alt.GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,
                           as_object=True)
surveyeddata.fix_terminus()
surveyeddata.normalize_elevation()
surveyeddata.calc_dz_stats()

#Now to partition the dataset as done in Larsen etal by glacier type.
#We excluding surgers and outlier glaciers because we don't want those glaciers to affect 
#   mean profiles used for extrapolation.
types = ["gltype=0","gltype=1","gltype=2"]
lamb,userwheres,notused,whereswo,notswo = alt.partition_dataset(types,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
results = alt.extrapolate('testing',lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False) 