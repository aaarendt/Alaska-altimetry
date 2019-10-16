-- generates normalized bins from ergibins
-- probably not the most elegant solution but this works

ALTER TABLE ergibins ADD COLUMN normbins numeric;
UPDATE ergibins AS eb
SET normbins = m.normbins 
FROM
(SELECT b.glimsid, b.bins,
CASE 
WHEN round((b.bins - e.min) / (e.max - e.min) , 2) > 0.99 THEN 0.99
WHEN round((b.bins - e.min) / (e.max - e.min) , 2) < 0.0 THEN 0.0
ELSE round((b.bins - e.min) / (e.max - e.min) , 2) 
END
AS normbins
FROM ergibins AS b
JOIN ergi_mat_view as e
ON e.glimsid = b.glimsid
ORDER BY glimsid, bins) AS m
WHERE eb.glimsid = m.glimsid AND eb.bins = m.bins