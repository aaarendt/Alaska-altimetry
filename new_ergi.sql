DROP MATERIALIZED VIEW public.new_ergi;
CREATE MATERIALIZED VIEW public.new_ergi AS

-- code to generate polygons from RGI "enhanced" for altimetry work (ergi)
-- two types of cases are covered: merging multiple polygons, or reassigning types 

-- for polygon merging: first give all polygons to be merged the same rgiid, then
-- GROUP BY rgiid and apply ST_Union
 
-- aaarendt 20160103

SELECT merged.rgiid AS rgiid, merged.area AS area, merged.geom AS geom, modern.glactype AS glactype_modern, modern.name,
-- These control statements reassign glacier types
-- some glaciers need to be considered different types for altimetry purposes (e.g. "paleo-tidewater") 
CASE
   WHEN merged.rgiid = 'RGI40-1.09783' THEN '9199' -- Harriman
   WHEN merged.rgiid = 'RGI40-1.10402' THEN '9199' -- Bryn Mawr
   WHEN merged.rgiid = 'RGI40-1.13538' THEN '9299' -- Tana
   WHEN merged.rgiid = 'RGI40-1.20791' THEN '9119' -- La Perouse
   WHEN merged.rgiid = 'RGI40-1.12683' THEN '9199' -- Art Lewis
   WHEN merged.rgiid = 'RGI40-1.20783' THEN '9199' -- Reid
   WHEN merged.rgiid = 'RGI40-1.01390' THEN '9199' -- Taku
   WHEN merged.rgiid = 'RGI40-1.10188' THEN '9199' -- Cascade
   WHEN merged.rgiid = 'RGI40-1.10355' THEN '9199' -- Wellesley
   WHEN merged.rgiid = 'RGI40-1.10836' THEN '9199' -- Shoup
   WHEN merged.rgiid = 'RGI40-1.23643' THEN '9199' -- Moraine/Apron
   ELSE modern.glactype
END
AS glactype_ergi
FROM modern 
JOIN 
(SELECT m.newrgiid AS rgiid, sum(m.area) AS area, ST_Union(m.geom) as geom FROM
(SELECT rgiid, area, geom,
  CASE 
  -- These control statements merge RGI glaciers for altimetry purposes
     WHEN rgiid = 'RGI40-1.23641' THEN 'RGI40-1.13538' -- Tana
     WHEN rgiid = 'RGI40-1.27101' THEN 'RGI40-1.13987' -- Tana Lobe Bremner
     WHEN rgiid = 'RGI40-1.19542' THEN 'RGI40-1.19825' -- Double
     WHEN rgiid = 'RGI40-1.26715' THEN 'RGI40-1.19814' -- Blockade
     WHEN rgiid = 'RGI40-1.23655' THEN 'RGI40-1.20985' -- Grand Plateau
	 WHEN (rgiid = 'RGI40-1.26723' OR rgiid = 'RGI40-1.27102') THEN 'RGI40-1.01390' -- Taku / Hole-in-the Wall
     WHEN (rgiid = 'RGI40-1.27103' OR rgiid = 'RGI40-1.23662') THEN 'RGI40-1.01522' -- Llewellyn
     WHEN rgiid = 'RGI40-1.23656' THEN 'RGI40-1.20984' -- fairweather
     WHEN rgiid = 'RGI40-1.26732' THEN 'RGI40-1.21011' -- Melbern / Grand Pacific
     WHEN rgiid = 'RGI40-1.23665' THEN 'RGI40-1.03890' -- Sawyer
     ELSE rgiid
  END 
  AS newrgiid
  FROM modern) AS m GROUP BY m.newrgiid) as merged
  ON merged.rgiid = modern.rgiid;