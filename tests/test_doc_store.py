import unittest
import psycopg2;
import ujson
import json_merge_patch as jsonmp

def _create_patch(new_doc, previous_doc):
    return jsonmp.create_patch(new_doc, previous_doc)

def _apply_patch(orig_doc, change_doc):
    return jsonmp.merge(orig_doc, change_doc)

CONNECTION_STRING='dbname={dbname} user={user} host={docker_machine_ip}'.format(dbname='docstore',
                                                                                user='postgres',
                                                                                docker_machine_ip='192.168.99.100')



def setup_db():
    with psycopg2.connect(CONNECTION_STRING) as conn:
        cur = conn.cursor()
        cur.execute("""
        TRUNCATE staging_document_store.full_document CASCADE
        """)
        cur.execute("""
        TRUNCATE staging_document_store.difference_document CASCADE
        """)

def store_document(document_json):
    with psycopg2.connect(CONNECTION_STRING) as conn:
        curs = conn.cursor()
        curs.execute("""
              SET search_path=staging_document_store;
           INSERT INTO full_document (full_document)
           VALUES (%s)
        RETURNING full_document_id
        """, (ujson.dumps(document_json),))
        full_document_id = curs.fetchone()[0]
        return full_document_id


def update_document(document_id, document_json):  # who did this? other metadata?
    with psycopg2.connect(CONNECTION_STRING) as conn:
        curs = conn.cursor()

        curs.execute("""
           SET search_path=staging_document_store;
        SELECT full_document
          FROM full_document
         WHERE full_document_id=%s
        """, (document_id,))
        current_document = curs.fetchone()[0]
        difference_document = _create_patch(document_json, current_document)
        if not difference_document:
            return None

        curs.execute("""
           SET search_path=staging_document_store;
        UPDATE full_document
           SET full_document=%s
        """, (ujson.dumps(document_json),))

        curs.execute("""
              SET search_path=staging_document_store;
           INSERT INTO difference_document (full_document_id, difference_document)
           VALUES (%s, %s)
        RETURNING difference_document_id, update_time
        """, (document_id, ujson.dumps(difference_document)))
        difference_id, update_time = curs.fetchone()
        return update_time, difference_id, difference_document


def get_document_changes(document_id, timestamp=None):
    with psycopg2.connect(CONNECTION_STRING) as conn:
        cur = conn.cursor()
        cur.execute("""
           SELECT difference_document
             FROM staging_document_store.difference_document
            WHERE full_document_id=%(document_id)s AND
                  update_time > coalesce(%(timestamp)s, now())
         ORDER BY update_time DESC
        """, {"document_id": document_id,
              "timestamp": timestamp})
        return cur


def get_head_document(document_id):
    with psycopg2.connect(CONNECTION_STRING) as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT full_document
          FROM staging_document_store.full_document
         WHERE full_document_id=%(document_id)s
        """, {"document_id": document_id})
        return cur.fetchone()[0]

def get_document(document_id, timestamp=None):
    head_document = get_head_document(document_id)
    if not timestamp:
        return head_document

    def apply_changes(total_doc, current_doc):
        return _apply_patch(total_doc, current_doc[0])

    changes = get_document_changes(document_id, timestamp=timestamp)
    _changes = changes.fetchall()
    return reduce(apply_changes, _changes, head_document)

class DocStoreTestAgain(unittest.TestCase):
    test_document = {"colour": "green",
                     "name": "Frog"}

    updated_document_1 = {"colour": "green",
                          "name": "Frog",
                          "class": "amphibian"}

    updated_document_2 = {"colour": "green",
                          "class": "amphibian"}

    def setUp(self):
        setup_db()

    def test_doc_add(self):
        document_id = store_document(self.test_document)
        self.assertTrue(document_id is not None)

        result_document = get_document(document_id)
        self.assertEquals(result_document, self.test_document)

    def test_doc_update(self):
        document_id = store_document(self.test_document)
        self.assertTrue(document_id is not None)

        timestamp_1, difference_id, difference = update_document(document_id,
                                                                 self.updated_document_1)
        result_document = get_document(document_id)
        self.assertEquals(result_document, self.updated_document_1)

        timestamp_2, difference_id, difference = update_document(document_id,
                                                                 self.updated_document_2)
        result_document = get_document(document_id)
        self.assertEquals(result_document, self.updated_document_2)

        doc_timestamp_1 = get_document(document_id, timestamp_1)
        self.assertEquals(doc_timestamp_1, self.updated_document_1)


    def test_doc_non_update(self):
        """
        Should not do anything
        """
        document_id = store_document(self.test_document)
        self.assertTrue(document_id is not None)
        result = update_document(document_id, self.test_document)
        self.assertIsNone(result)
