import unittest
import sqlite3 as lite
from model import get_con

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

if __name__ == '__main__':
    unittest.main()
