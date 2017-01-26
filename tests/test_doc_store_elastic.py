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
    pass

def store_document(document_json):
    pass

def update_document(document_id, document_json):  # who did this? other metadata?
    pass

def get_document_changes(document_id, timestamp=None):
    pass

def get_head_document(document_id):
    pass

def get_document(document_id, timestamp=None):
    pass

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
