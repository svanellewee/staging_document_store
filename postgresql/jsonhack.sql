/* Basic flow of jsonb document versioner POC
	1) Generate test data
	2) Populate slowly changing dimension type 2 table using pentaho
	3) Copy data to jsonb supported table
	4) Test queries

*/

/*
Generate test data
*/

WITH blah AS
(
SELECT 10-generate_series(1,20) as numbers
), blah2 AS
(
SELECT 
	generate_series(1,2) AS id,
	now()-numbers*INTERVAL '1 hour' as date_created,
		CASE WHEN numbers = 1 THEN 'kosie pompies'::text
		     ELSE 'not piet pompies'::text 
		END AS username,
	((numbers*random())/4)::int::text AS thingthatchange
	FROM blah
), blah3 AS
(
SELECT 
	id,
	date_created,
	('{"name": "'  || username || '", "thingthatchange": "' || thingthatchange || '"}')::jsonb
FROM blah2
)
-- SELECT distinct jsonb FROM blah3;
INSERT INTO jsonbversioning SELECT * FROM blah3;

/*
Populate slowly changing dimension type 2 table using pentaho
*/
RUN TOOL

/*
Copy data to jsonb supported table
*/

CREATE TABLE public.jsonb_dim2
(
  jsonb_dim_id bigint NOT NULL DEFAULT nextval('jsonb_dim_jsonb_dim_id_seq'::regclass),
  version integer,
  date_from timestamp without time zone,
  date_to timestamp without time zone,
  id integer,
  date_created timestamp without time zone,
  data jsonb,
  last_insert_update timestamp without time zone,
  last_version character(1)
)
WITH (
  OIDS=FALSE
);

INSERT INTO jsonb_dim2 SELECT jsonb_dim_id,version,date_from,date_to,id,date_created,data::jsonb,last_insert_update,last_version FROM jsonb_dim


/*
Test queries
*/

-- DOCUMENT QUERIES
-- GET LATEST VERSION OF DOCUMENT id=1
SELECT data 
FROM jsonb_dim2
WHERE id=1
AND last_version='Y';

-- GET PREVIOUS VERSION OF DOCUMENT id=1 (full row)
SELECT * FROM jsonb_dim2
WHERE id=1
AND last_version='N'
ORDER BY jsonb_dim_id DESC
LIMIT 1

-- GET DOCUMENT AT SPESIFIC DATE TIME
SELECT * FROM jsonb_dim2
WHERE id=1
AND date_from < '2017-01-26 20:06:30'
AND date_to > '2017-01-26 20:06:30'

-- FIELD QUERIES
-- GET LATEST value of name for id=1
SELECT data->'name' AS username
FROM jsonb_dim2
WHERE id=1
AND last_version='Y';

SELECT data->'thingthatchange' AS thingthatchange
FROM jsonb_dim2
WHERE id=1
AND last_version='Y';

-- GET DATA WHERE name changed for id=2
WITH ids AS (
SELECT jsonb_dim_id FROM
( 
	SELECT jsonb_dim_id,data->'name' AS val, LAG(data->'name') OVER (ORDER BY jsonb_dim_id) as prev_val 
	FROM jsonb_dim2
	WHERE id=2
) blah
WHERE val <> COALESCE(prev_val,val)
)
SELECT * FROM jsonb_dim2
INNER JOIN ids USING (jsonb_dim_id)

-- GET DATA WHERE name changed for id=2
WITH ids AS (
SELECT jsonb_dim_id FROM
( 
	SELECT jsonb_dim_id,data->'thingthatchange' AS val, LAG(data->'thingthatchange') OVER (ORDER BY jsonb_dim_id) as prev_val 
	FROM jsonb_dim2
	WHERE id=2
) blah
WHERE val <> COALESCE(prev_val,val)
)
SELECT * FROM jsonb_dim2
INNER JOIN ids USING (jsonb_dim_id)

-- GET WHAT CHANGED at version 6 of id 2
WITH ids AS (
	SELECT *, LAG(data) OVER (ORDER BY jsonb_dim_id) as prev_val 
	FROM jsonb_dim2
	WHERE id=2
)
SELECT jsonb_diff_val(data,prev_val) FROM ids
-- WHERE version=6

/*
DIFF FUNCTION
*/

CREATE OR REPLACE FUNCTION jsonb_diff_val(val1 JSONB,val2 JSONB)
RETURNS JSONB AS $$
DECLARE
  result JSONB;
  v RECORD;
BEGIN
   result = val1;
   FOR v IN SELECT * FROM jsonb_each(val2) LOOP
     IF result @> jsonb_build_object(v.key,v.value)
        THEN result = result - v.key;
     ELSIF result ? v.key THEN CONTINUE;
     ELSE
        result = result || jsonb_build_object(v.key,'null');
     END IF;
   END LOOP;
   RETURN result;
END;
$$ LANGUAGE plpgsql;
