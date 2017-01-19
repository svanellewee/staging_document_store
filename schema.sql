DROP SCHEMA IF EXISTS public CASCADE;
DROP SCHEMA IF EXISTS staging_document_store CASCADE;
CREATE SCHEMA IF NOT EXISTS staging_document_store;

SET search_path=staging_document_store;

CREATE TABLE IF NOT EXISTS full_document (
       full_document_id SERIAL PRIMARY KEY,
       full_document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS difference_document (
       difference_document_id SERIAL PRIMARY KEY,
       difference_document JSONB NOT NULL,
       full_document_id INTEGER NOT NULL,
       update_time timestamp DEFAULT NOW(),
       FOREIGN KEY (full_document_id) REFERENCES full_document(full_document_id) ON DELETE CASCADE
);
