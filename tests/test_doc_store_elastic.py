import unittest
import json_merge_patch as jsonmp
import requests
import pprint
import json
import datetime
import time


def _create_patch(new_doc, previous_doc):
    return jsonmp.create_patch(new_doc, previous_doc)

def _apply_patch(orig_doc, change_doc):
    return jsonmp.merge(orig_doc, change_doc)

CONNECTION_STRING='http://{docker_machine_ip}:9200'.format(docker_machine_ip='192.168.99.100')


def setup_db():
    requests.delete("{}/staging_document_store/".format(CONNECTION_STRING))
    requests.delete("{}/staging_document_store/full_document/".format(CONNECTION_STRING))
    requests.delete("{}/staging_document_store/difference_document/".format(CONNECTION_STRING))
    settings = {
        "mappings": {
            "full_document": {
                "properties": {
                    "date": {
                        "type": "date",
                        "format": "yyy-MM-dd HH:mm:ss.SSSSSS||yyyy-MM-dd||epoch_millis"                        
                    }
                }
            },
            "difference_document": {
                "properties": {
                    "date": {
                        "type": "date",
                        "format": "yyy-MM-dd HH:mm:ss.SSSSSS||yyyy-MM-dd||epoch_millis"                        
                        
                    }
                }
            }
            
        }
    }
    response = requests.put("{}/staging_document_store/".format(CONNECTION_STRING),
                            json=settings)
    pprint.pprint(json.loads(response.text))
    
def store_document(orig_document_json):
    document_json = {}
    document_json.update({"document": {k:v for k,v in orig_document_json.items()}})
    document_json.update({"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")})
    response = requests.post("{}/staging_document_store/full_document/".format(CONNECTION_STRING),
                            json=document_json)
    return response.json()['_id']

def update_document(document_id, orig_document_json):  # who did this? other metadata?
    document_json = {}
    document_json.update({"document": {k:v for k,v in orig_document_json.items()}})
    document_json.update({"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")})
    current_document = get_head_document(document_id)
    
    difference = _create_patch(document_json['document'], current_document)
    if not difference:
        return None
    
    difference_document = {}
    difference_document.update({"document_id": document_id})
    difference_document.update({"document": difference})
    difference_document.update({"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")})
    response = requests.put("{}/staging_document_store/full_document/{}".format(CONNECTION_STRING, document_id),
                             json=document_json)
    if response.status_code == 400:
        raise Exception("Update not made")
    
    response_difference = requests.post("{}/staging_document_store/difference_document/".format(CONNECTION_STRING),
                                        json=difference_document)
    if response_difference.status_code == 400:
        raise Exception("Difference not built")
    
    difference_id = response_difference.json()['_id']
    return difference_document['date'], difference_id, difference_document['document']

def get_document_changes(document_id, timestamp=None):
    pass

def get_head_document(document_id):
    response = requests.get("{}/staging_document_store/full_document/{}".format(CONNECTION_STRING,document_id))
    return response.json()['_source']['document']
    

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
