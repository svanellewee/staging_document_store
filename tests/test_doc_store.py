import unittest
import psycopg2;
import ujson
import json_merge_patch as jsonmp
import pprint
import contextlib


def get_changes(full_document_id, number_of_versions=1):
    with psycopg2.connect('dbname=docstore') as conn:
        cur = conn.cursor()
        cur.execute("""
          SELECT difference_document
            FROM staging_document_store.difference_document dd,
                 staging_document_store.full_document fd
           WHERE dd.full_document_id=fd.full_document_id AND
                 dd.full_document_id=%(full_document_id)s
        ORDER BY dd.difference_document_id DESC
           LIMIT %(number_of_versions)s
        """, {"full_document_id": full_document_id,
              "number_of_versions": number_of_versions})
        return cur


def get_full_document(full_document_id):
    with psycopg2.connect('dbname=docstore') as conn:
        cur = conn.cursor()
        cur.execute("""
          SELECT full_document
            FROM staging_document_store.full_document fd
        WHERE fd.full_document_id=%(full_document_id)s
        """, {"full_document_id": full_document_id})
        return cur.fetchone()[0]

def get_document(full_document_id, number_of_versions=1):
    changes = get_changes(full_document_id=full_document_id,
                          number_of_versions=number_of_versions)
    document = get_full_document(full_document_id)
    def apply_changes(total, current):
        return jsonmp.merge(current, total)
    return reduce(apply_changes, [i[0] for i in changes.fetchall()], document)

@contextlib.contextmanager
def iterate_diffs(document_id):
    with psycopg2.connect('dbname=docstore') as conn:
        curs = conn.cursor()
        curs.execute("""
        SET search_path=staging_document_store;
        SELECT difference_document
        FROM difference_document
        WHERE full_document_id=%s
        ORDER BY update_time DESC
        """, (document_id,))
        yield curs.fetchall()

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

    test_document_removal_2 = { "lead_guitar":"Billy Howerdel",
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
            cur.execute("TRUNCATE staging_document_store.difference_document CASCADE");

    # def test_doc_store(self):
    #     expected =  {"bass": "Matt McJunkins",
    #                  "drums": "Jeff Friedl",
    #                  "lead_guitar": "Billy Howerdel",
    #                  "rhythm_guitar": "James Iha"}
    #     doc_id = store_document(self.test_document_current)


    def test_diff_store_removal(self):
        doc_id = store_document(self.test_document_current)
        update_document(doc_id, self.test_document_removal)
        update_document(doc_id, self.test_document_removal_2)

        expected_total_diffs = [({u'bass': u'Matt McJunkins'},),
                                ({u'rhythm_guitar': u'James Iha'},)]
        answer1 = list(get_changes(doc_id, None))
        self.assertEquals(expected_total_diffs, answer1)

        expected_diffs = [({u'bass': u'Matt McJunkins'},)]
        answer2 = list(get_changes(doc_id, 1))
        self.assertEquals(expected_diffs, answer2)

        #import pdb; pdb.set_trace()
        d = get_full_document(doc_id)
        dd = get_document(doc_id)
        import pdb; pdb.set_trace()
        dd2 = get_document(doc_id, None)
        import pdb; pdb.set_trace()
        x =123
    # def test_diff_store_addition(self):
    #     doc_id = store_document(self.test_document_current)
    #     doc_id = update_document(doc_id, self.test_document_addition)


    # def test_diff_store_removal_addition(self):
    #     doc_id = store_document(self.test_document_current)
    #     doc_diff1 = update_document(doc_id, self.test_document_removal)
    #     doc_diff2 = update_document(doc_id, self.test_document_addition)
    #     with iterate_diffs(doc_id) as vals:
    #         for v in vals:
    #             print v
