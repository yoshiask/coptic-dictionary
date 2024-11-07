import sqlite3 as lite
import re
from collections import defaultdict

def get_con():
    return lite.connect('alpha_kyima_rc1.db')

def regexp(expr, item):
    return re.search(expr.lower(), item.lower(), flags=re.UNICODE) is not None

def check_tla_exists(tla_search):
    con = get_con()
    con.create_function("REGEXP", 2, regexp)
    with con:
        cur = con.cursor()
        cur.execute("SELECT xml_id FROM entries WHERE xml_id=?", (tla_search,))
        rows = cur.fetchall()
        return len(rows) > 0

def retrieve_related(word):
    sql_command = 'SELECT * FROM entries WHERE Etym LIKE ? ORDER BY Ascii'
    parameters = ['%' + word + '%']
    con = get_con()
    con.create_function("REGEXP", 2, regexp)
    with con:
        cur = con.cursor()
        cur.execute(sql_command, parameters)
        return cur.fetchall()

def retrieve_entries(word, dialect, pos, definition, def_search_type, def_lang, search_desc="", params=None, tla_search=None):
    if params is None:
        params = {}
    sql_command = 'SELECT * FROM entries WHERE '
    constraints = []
    parameters = []

    if len(word) > 0:
        try:
            re.compile(word)
            op = 'REGEXP'
        except:
            op = '='

        if dialect == 'any':
            word_search_string = r'.*\n' + word + r'~.*'
        else:
            word_search_string = r'.*\n' + word + r'~' + dialect + r'?\n.*'

        word_constraint = "entries.Search " + op + " ?"
        parameters.append(word_search_string)
        if " " in word:
            word_constraint = "(" + word_constraint + " OR entries.oRef = ?)"
            parameters.append(word)
        constraints.append(word_constraint)

    elif dialect != 'any':
        dialect_constraint = "entries.Search REGEXP ?"
        constraints.append(dialect_constraint)
        parameters.append(r'.*~' + dialect + r'?(\^\^[^\n]*)*\n')

    if pos != 'any':
        pos_constraint = "entries.POS = ?"
        constraints.append(pos_constraint)
        parameters.append(pos)

    if definition:
        if def_search_type == 'exact sequence' and tla_search is None:
            def_search_string = r'.*\b' + definition + r'\b.*'
            try:
                re.compile(def_search_string)
                op = 'REGEXP'
            except:
                op = '='
            if def_lang == 'any':
                def_constraint = "(entries.En " + op + " ? OR entries.De " + op + " ? OR entries.Fr " + op + " ?)"
                constraints.append(def_constraint)
                parameters.append(def_search_string)
                parameters.append(def_search_string)
                parameters.append(def_search_string)
            elif def_lang == 'en':
                def_constraint = "entries.En " + op + " ?"
                constraints.append(def_constraint)
                parameters.append(def_search_string)
            elif def_lang == 'fr':
                def_constraint = "entries.Fr " + op + " ?"
                constraints.append(def_constraint)
                parameters.append(def_search_string)
            elif def_lang == 'de':
                def_constraint = "entries.De " + op + " ?"
                constraints.append(def_constraint)
                parameters.append(def_search_string)

        elif def_search_type == 'all words' and tla_search is None:
            words = definition.split(' ')
            for one_word in words:
                try:
                    re.compile(one_word)
                    op = 'REGEXP'
                except:
                    op = '='
                def_search_string = r'.*\b' + one_word + r'\b.*'
                if def_lang == 'any':
                    def_constraint = "(entries.En " + op + " ? OR entries.De " + op + " ? OR entries.Fr " + op + " ?)"
                    constraints.append(def_constraint)
                    parameters.append(def_search_string)
                    parameters.append(def_search_string)
                    parameters.append(def_search_string)
                elif def_lang == 'en':
                    def_constraint = "entries.En " + op + " ?"
                    constraints.append(def_constraint)
                    parameters.append(def_search_string)
                elif def_lang == 'fr':
                    def_constraint = "entries.Fr " + op + " ?"
                    constraints.append(def_constraint)
                    parameters.append(def_search_string)
                elif def_lang == 'de':
                    def_constraint = "entries.De " + op + " ?"
                    constraints.append(def_constraint)
                    parameters.append(def_search_string)

    if tla_search is not None:
        constraints.append("xml_id = ?")
        parameters.append(tla_search)

    if constraints:
        sql_command += " AND ".join(constraints)
    else:
        sql_command = 'SELECT * FROM entries ORDER BY Ascii'

    print(f"SQL Command: {sql_command}")
    print(f"Parameters: {parameters}")

    con = get_con()
    con.create_function("REGEXP", 2, regexp)
    with con:
        cur = con.cursor()
        cur.execute(sql_command, parameters)
        return cur.fetchall()

def retrieve_network_data(word, pos):
    con = get_con()
    with con:
        cur = con.cursor()
        cur.execute("SELECT pos, word, phrase, freq FROM networks WHERE pos=? AND word=? ORDER BY freq DESC LIMIT 20", (pos, word))
        rows = cur.fetchall()
    return rows

def retrieve_entry_data(tla_id):
    con = get_con()
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM entries WHERE xml_id=?", (tla_id,))
        entry = cur.fetchone()
    return entry