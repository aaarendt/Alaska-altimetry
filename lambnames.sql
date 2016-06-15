-- one time transfer of lamb_rgi to database, and retrieving the glimsids

-- lambrgi = pd.read_excel(r"c:\work\src\ingestAltimetry\lamb_rgi.xlsx") # Kilroy
-- lambrgi.to_sql('lambnames',engine)

-- the xlsx file comes from Christian with rgiid so need to join to get glimsid

ALTER TABLE lambnames ADD PRIMARY KEY(index);
ALTER TABLE lambnames ADD COLUMN glimsid character varying(254);
UPDATE lambnames AS ln
SET glimsid = m.glimsid
FROM 
(SELECT glimsid,rgiid FROM modern) AS m
WHERE ln.rgiid = m.rgiid;