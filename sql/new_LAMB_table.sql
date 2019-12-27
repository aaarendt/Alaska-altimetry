-- this code is run just once when creating a new table in the database to store the Laser Altimetry Mass Balance (lamb) data

-- run this code with admin level access

CREATE TABLE lamb (lambid serial PRIMARY KEY, glimsid character varying(14), date1 date, date2 date, interval smallint, volmodel real, vol25diff real,vol75diff real, balmodel real, bal25diff real, bal75diff real,e integer[],dz real[],dz25 real[],dz75 real[],aad real[],masschange real[], massbal real[],numdata integer[]);