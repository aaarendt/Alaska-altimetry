-- export glacier wide mass balance (m w.e. / yr) of final results of Larsen et al (2015)
copy ( 
select rgiid, a3.glimsid, massbal from modern
join
(select glimsid, massbal from ergi
join 
(select ergiid, s/a * 0.85 as massbal
from
(select ergiid,sum(mean*area) as s,sum(area) as a from public.altimetryextrapolation
group by "ergiid"
order by "ergiid") as a1) as a2
on
(ergi.ergiid = a2.ergiid)) as a3
on 
(modern.glimsid = a3.glimsid)

)
TO 'C:\work\AlaskaAltimetry.csv' DELIMITER ',' CSV HEADER;
