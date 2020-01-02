-- code to generate polygons from RGI "enhanced" for altimetry work (ergi)
-- this should only need to be run once when setting up database files for the first time

-- two types of cases are covered: merging multiple polygons, or reassigning types 

-- for polygon merging: first give all polygons to be merged the same rgiid, then
-- GROUP BY rgiid and apply ST_Union
 
-- The first set of control (CASE) statements reassign glacier types because some glaciers need to be considered different types for altimetry purposes (e.g. "paleo-tidewater") 

-- The second set of control statements merge RGI glaciers for altimetry purposes

-- Anthony Arendt 20160103

-- This code works only on RGI v4.0. Latest version 6.0 has different type assignments.

-- Arendt 20200102

CREATE TABLE ergi AS
SELECT merged.glimsid AS glimsid, merged.max AS max, merged.min AS min, merged.area AS area, merged.geom AS albersgeom, modern.name, 
CASE
   WHEN merged.glimsid = 'G211470E60937N' THEN '9199' -- Harriman
   WHEN merged.glimsid = 'G212133E61251N' THEN '9199' -- Bryn Mawr
   WHEN merged.glimsid = 'G217826E60615N' THEN '9299' -- Tana
   WHEN merged.glimsid = 'G222808E58557N' THEN '9119' -- La Perouse
   WHEN merged.glimsid = 'G221141E59910N' THEN '9199' -- Art Lewis
   WHEN merged.glimsid = 'G223177E58740N' THEN '9199' -- Reid
   WHEN merged.glimsid = 'G225722E58651N' THEN '9199' -- Taku
   WHEN merged.glimsid = 'G211808E61161N' THEN '9199' -- Cascade
   WHEN merged.glimsid = 'G212065E61198N' THEN '9199' -- Wellesley
   WHEN merged.glimsid = 'G213582E61227N' THEN '9199' -- Shoup
   WHEN merged.glimsid = 'G218421E60063N' THEN '9199' -- Moraine/Apron
   ELSE modern.glactype
END
AS gltype
FROM modern 
JOIN 
(SELECT m1.newglimsid AS glimsid, sum(m1.area) AS area, max(m1.elev_max) as max, min(m1.elev_min) as min, ST_Union(m1.geom) as geom FROM
(SELECT m.glimsid, m.area, m.geom, madd.elev_max, madd.elev_min,
  CASE 
     WHEN m.glimsid = 'G216935E60607N' THEN 'G217826E60615N' -- Tana
     WHEN m.glimsid = 'G216662E60771N' THEN 'G216711E60765N' -- Tana Lobe Bremner
     WHEN m.glimsid = 'G207356E60652N' THEN 'G207302E60702N' -- Double
     WHEN m.glimsid = 'G207434E60990N' THEN 'G207457E61035N' -- Blockade
     WHEN m.glimsid = 'G222190E59103N' THEN 'G222265E59003N' -- Grand Plateau
	 WHEN (m.glimsid = 'G225944E58696N' OR m.glimsid = 'G225891E58652N') THEN 'G225722E58651N' -- Taku / Hole-in-the Wall
     WHEN (m.glimsid = 'G225914E58943N' OR m.glimsid = 'G225716E59080N') THEN 'G225796E59001N' -- Llewellyn
     WHEN m.glimsid = 'G222248E58857N' THEN 'G222258E58826N' -- fairweather
     WHEN m.glimsid = 'G222647E59132N' THEN 'G222486E59176N' -- Melbern / Grand Pacific
     WHEN m.glimsid = 'G227251E57936N' THEN 'G227097E57898N' -- Sawyer
     ELSE m.glimsid
  END 
  AS newglimsid
  FROM modern AS m
  JOIN
  (SELECT elev_max, elev_min, glimsid FROM modernadditional) as madd
  ON madd.glimsid = m.glimsid) AS m1 GROUP BY m1.newglimsid) AS merged
  ON merged.glimsid = modern.glimsid;

-- Run this after the table above to assign a primary key to the new ergi table

ALTER TABLE ergi ADD COLUMN ergiid SERIAL;
UPDATE ergi SET ergiid = nextval(pg_get_serial_sequence('ergi','ergiid'));
ALTER TABLE ergi ADD PRIMARY KEY(ergiid);


