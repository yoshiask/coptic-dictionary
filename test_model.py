import unittest
import sqlite3 as lite
from model import get_con
from model import parse_entry
from helper import get_annis_query
from model import process_orthstring

class TestDatabase(unittest.TestCase):

    def test_open_database(self):
            try:
                con = get_con()
                con.close()
            except lite.Error as e:
                self.fail(f"Failed to open database: {e}")

    def test_tables_exist(self):
            con = get_con()
            with con:
                cur = con.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cur.fetchall()
                table_names = [table[0] for table in tables]
                self.assertIn('entries', table_names, "Table 'entries' does not exist in the database")

    def test_parse_entry(self):
        entry = ['C3173', 'ⲉⲣⲁⲧ⸗~^^form1', 'entry1', 'Präp.', 'other_data']
        expected_output = [
            {
                'distinct_orth': 'ⲉⲣⲁⲧ⸗',
                'geo_string': '~^^form1',
                'form_id': 'form1',
                'morphology': 'Präp.',
                'annis_query': 'expected_query'
            }
        ]
        result = parse_entry(entry)
        self.assertEqual(result, expected_output)

        
    def test_process_orthstring(self):
        orthstring = 'orth1~^^form1\north2~^^form2'
        expected_output = {
            'orth1': ['~^^form1'],
            'orth2': ['~^^form2']
        }
        result = process_orthstring(orthstring)
        self.assertEqual(result, expected_output)

        orthstring = 'orth1~^^form1\north1~^^form2'
        expected_output = {
            'orth1': ['~^^form1', '~^^form2']
        }
        result = process_orthstring(orthstring)
        self.assertEqual(result, expected_output)

        orthstring = 'orth1~^^form1\north2~^^form2\north3~^^form3'
        expected_output = {
            'orth1': ['~^^form1'],
            'orth2': ['~^^form2'],
            'orth3': ['~^^form3']
        }
        result = process_orthstring(orthstring)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()
