-- export binned glacier wide mass balance (m / yr) of final results of Larsen et al (2015), surveyed glaciers only
copy ( 
select rgiid, a3.glimsid, bins, name, massbal from modern
join
(select glimsid, massbal, bins from ergi
join 
(select ergiid, s as massbal, bins
from
(select ergiid,mean as s, bins from public.altimetryextrapolation
where surveyed = 'true') as a1) as a2
on
(ergi.ergiid = a2.ergiid)) as a3
on 
(modern.glimsid = a3.glimsid)
order by rgiid, bins
)
TO 'C:\work\AlaskaAltimetry_myr_surveyed_binned.csv' DELIMITER ',' CSV HEADER;
