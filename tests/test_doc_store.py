import unittest
import psycopg2;
import ujson
import json_merge_patch as jsonmp
import pprint


def store_document(document):
    with psycopg2.connect('dbname=docstore') as conn:
        curs = conn.cursor()
        curs.execute("""
        SET search_path=staging_document_store;
        INSERT INTO full_document (full_document)
        VALUES (%s)
        RETURNING full_document_id
        """, (ujson.dumps(document),))
        full_document_id = curs.fetchone()[0]
        return full_document_id


def update_document(document_id, new_document):
    with psycopg2.connect('dbname=docstore') as conn:
        curs = conn.cursor()
        
        curs.execute("""
        SET search_path=staging_document_store;
        SELECT full_document 
        FROM full_document
        WHERE full_document_id=%s
        """, (document_id,))
        current_document = curs.fetchone()[0]
        
        curs.execute("""
        SET search_path=staging_document_store;
        UPDATE full_document 
        SET full_document=%s
        """, (ujson.dumps(new_document),))

        difference_document = jsonmp.create_patch(new_document, current_document)
        curs.execute("""
        SET search_path=staging_document_store;
        INSERT INTO difference_document (full_document_id, difference_document)
        VALUES (%s, %s)
        """, (document_id, ujson.dumps(difference_document)))
        
        return difference_document

class DocStoreTest(unittest.TestCase):

    test_document_current = { "lead_guitar":"Billy Howerdel",
                              "rhythm_guitar": "James Iha",
                              "bass": "Matt McJunkins",
                              "drums":  "Jeff Friedl" }
    
    test_document_removal = { "lead_guitar":"Billy Howerdel",
                              "bass": "Matt McJunkins",
                              "drums":  "Jeff Friedl" }


    test_document_addition = { "lead_guitar":"Billy Howerdel",
                               "rhythm_guitar": "James Iha",
                               "bass": "Matt McJunkins",
                               "backing_vocals": "Jeordie White",
                               "drums":  "Jeff Friedl" }
    


    def setUp(self):
        with psycopg2.connect('dbname=docstore') as conn:
            cur = conn.cursor()
            cur.execute("TRUNCATE staging_document_store.full_document CASCADE");
            
    def test_doc_store(self):
        doc_id = store_document(self.test_document_current)
        
    def test_diff_store_removal(self):
        doc_id = store_document(self.test_document_current)
        doc_id = update_document(doc_id, self.test_document_removal)
        

    def test_diff_store_addition(self):
        doc_id = store_document(self.test_document_current)
        doc_id = update_document(doc_id, self.test_document_addition)


    def test_diff_store_removal_addition(self):
        doc_id = store_document(self.test_document_current)
        doc_id = update_document(doc_id, self.test_document_removal)
        doc_id = update_document(doc_id, self.test_document_addition)
        

        
