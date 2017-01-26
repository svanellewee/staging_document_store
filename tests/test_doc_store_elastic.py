import unittest
import psycopg2;
import ujson
import json_merge_patch as jsonmp
import requests
import pprint
import json

def _create_patch(new_doc, previous_doc):
    return jsonmp.create_patch(new_doc, previous_doc)

def _apply_patch(orig_doc, change_doc):
    return jsonmp.merge(orig_doc, change_doc)

CONNECTION_STRING='http://{docker_machine_ip}:9200'.format(docker_machine_ip='192.168.99.100')


def setup_db():
    request =requests.delete("{}/staging_document_store/".format(CONNECTION_STRING))
    request =requests.delete("{}/staging_document_store/full_document/".format(CONNECTION_STRING))
    request =requests.delete("{}/staging_document_store/difference_document/".format(CONNECTION_STRING))
    #pprint.pprint(json.loads(request.text))
    
def store_document(document_json):
    response = requests.post("{}/staging_document_store/full_document/".format(CONNECTION_STRING),
                            json=document_json)
    return response.json()['_id']

def update_document(document_id, document_json):  # who did this? other metadata?
    current_document = get_head_document(document_id)
    difference_document = _create_patch(document_json, current_document)
    if not difference_document:
        return None

    response = requests.put("{}/staging_document_store/full_document/{}".format(CONNECTION_STRING, document_id),
                             json=document_json)
    if response.status_code == 400:
        raise Exception("Update not made")
    
    response_difference = requests.post("{}/staging_document_store/difference_document/".format(CONNECTION_STRING),
                                        json=difference_document)
    if response_difference.status_code == 400:
        raise Exception("Difference not built")
    difference_id = response_difference.json()['_id']
    return document_id, difference_id, difference_document

def get_document_changes(document_id, timestamp=None):
    pass

def get_head_document(document_id):
    response = requests.get("{}/staging_document_store/full_document/{}".format(CONNECTION_STRING,document_id))
    return response.json()['_source']
    

def get_document(document_id, timestamp=None):
    return get_head_document(document_id)

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
        import pdb; pdb.set_trace()
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
