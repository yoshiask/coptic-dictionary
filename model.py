import sqlite3 as lite
import re
from collections import defaultdict
from helper import get_annis_query

def get_con():
    con = lite.connect('alpha_kyima_rc1.db')
    con.row_factory = lite.Row
    return con

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
    sql_command = 'SELECT * FROM entries WHERE Etym REGEXP ? ORDER BY Ascii'
    parameters = ['.*' + word + '.*']
    con = get_con()
    con.create_function("REGEXP", 2, regexp)
    with con:
        cur = con.cursor()
        cur.execute(sql_command, parameters)
        return cur.fetchall()

def get_lemmas_for_word(word):
    con = get_con()
    with con:
        cur = con.cursor()
        cur.execute("SELECT lemma, pos FROM lemmas WHERE word=?", (word,))
        lemmas = cur.fetchall()
    return lemmas

def parse_lemma(lemma):
    match = re.search(r'~\^\^([A-Za-z0-9_]+)', lemma)
    if match:
        return match.group(1)
    return lemma

def process_orthstring(orthstring):
    orth_geo_dict = defaultdict(list)
    orth = "NONE"
    parts = orthstring.split('\n')
    for orth_geo_string in parts:
        orth_geo = re.match(r'^(.*)~(.?\^\^([A-Za-z0-9_]*))$', orth_geo_string)
        if orth_geo is not None:
            orth = orth_geo.group(1)
            orth_geo_dict[orth].append('~' + orth_geo.group(2))
    return orth_geo_dict

def extract_lemma(lemma):
    match = re.match(r'^(.*?)~', lemma)
    if match:
        return match.group(1)
    return lemma

def retrieve_entries(word, dialect, pos, definition, def_search_type, def_lang, params=None, tla_search=None):
    if params is None:
        params = {}
    sql_command = 'SELECT xml_id, Name, * FROM entries WHERE '
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
        sql_command = 'SELECT xml_id, Name, * FROM entries ORDER BY Ascii'

    print(f"SQL Command: {sql_command}")
    print(f"Parameters: {parameters}")
    parameters = ['.*ⲉⲣⲁⲧ~.*']
    con = get_con()
    con.create_function("REGEXP", 2, regexp)

    with con:
        cur = con.cursor()
        cur.execute(sql_command, parameters)
        entries = cur.fetchall()

    parsed_entries = []
    for entry in entries:
        parsed_entry = dict(entry)
        parsed_entry['Name'] = extract_lemma(entry['Name'])
        orth_geo_dict = process_orthstring(entry['Search'])
        for distinct_orth, geo_strings in orth_geo_dict.items():
            for geo_string in geo_strings:
                form_id = ""
                if "^^" in geo_string:
                    geo_string, form_id = geo_string.split("^^")
                parsed_entry['distinct_orth'] = distinct_orth
                parsed_entry['geo_string'] = geo_string
                parsed_entry['form_id'] = form_id
                parsed_entries.append(parsed_entry)

    # Remove duplicates
    unique_entries = {entry['xml_id']: entry for entry in parsed_entries}.values()

    return list(unique_entries)

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
    if entry:
        entry = dict(entry)
        entry['Name'] = extract_lemma(entry['Name'])
    return entry

def retrieve_collocates(lemma):
    con = get_con()
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM collocates WHERE lemma=?", (lemma,))
        collocates = cur.fetchall()
    return collocates

def first_orth(orthstring):
    first_orth = re.search(r'\n(.*?)~', orthstring)
    if first_orth is not None:
        return first_orth.group(1)
    else:
        return "NONE"

def second_orth(orthstring):
    first_search = re.search(r'\n(.*?)~', orthstring)
    if first_search is not None:
        first = first_search.group(1)
    else:
        first = ""

    second_orth = re.search(r'\n(.*?)[^\n]*\n(.*?)~', orthstring)
    sub_entries = re.findall(r'\n(.*?)~', orthstring)
    distinct_entries = set(sub_entries)
    if len(distinct_entries) > 1:
        return second_orth.group(2)
    else:
        return first

def parse_entry(entry):
    orths = entry['Search'].split('\n')
    orth_entries = []
    for orth in orths:
        orth_geo = re.match(r'^(.*)~(.?\^\^([A-Za-z0-9_]*))$', orth)
        if orth_geo is not None:
            orth_entry = {
                'distinct_orth': orth_geo.group(1),
                'geo_string': '~' + orth_geo.group(2),
                'form_id': orth_geo.group(3),
                'morphology': entry['POS'],
                'annis_query': get_annis_query(orth_geo.group(1), entry['oRef'], entry['POS'])
            }
            orth_entries.append(orth_entry)
    return orth_entries