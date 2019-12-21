# this file will be decommissioned soon

surveyeddata = alt.GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True, as_object=True)
surveyeddata.fix_terminus()
surveyeddata.normalize_elevation()
surveyeddata.calc_dz_stats()

types = ["gltype=0","gltype=1","gltype=2"]
lamb,userwheres,notused,whereswo,notswo = alt.partition_dataset(types,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
results = alt.extrapolate('guest',lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True)  
=surveyeddata,keep_postgres_tbls=False) 


