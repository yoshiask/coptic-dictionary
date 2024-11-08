from collections import defaultdict
import re
from flask import Flask, request, render_template
from html import escape
from helper import separate_coptic, strip_hyphens, get_annis_query
from model import check_tla_exists, retrieve_related, retrieve_entries, retrieve_network_data, retrieve_entry_data, retrieve_collocates, first_orth, second_orth, parse_entry, get_lemmas_for_word

app = Flask(__name__)

@app.route('/about', methods=['GET'])
def about():
    return render_template('template.html', static="about")

@app.route('/help', methods=['GET'])
def help():
    return render_template('template.html', static="help")

@app.route('/', methods=['GET'])
@app.route('/search', methods=['GET'])
def search():
    return render_template('template.html', static="search")

@app.route('/results', methods=['GET'])
def results():
    params = {}
    word = request.args.get("coptic", "").strip()
    dialect = request.args.get("dialect", "any").strip()
    pos = request.args.get("pos", "any").strip()
    definition = request.args.get("definition", "").strip()
    def_search_type = request.args.get("def_search_type", "exact sequence").strip()
    def_lang = request.args.get("def_lang", "any").strip()
    related = request.args.get("related", "").strip()
    quick_string = request.args.get("quick_search", "").strip()
    page = request.args.get("page", "1").strip()

    try:
        page = abs(int(page))
    except ValueError:
        page = 1
    params["page"] = page

    tla_search = None
    if quick_string:
        separated = separate_coptic(quick_string)
        print(f"Separated: {separated}")
        def_search_type = "all words"
        word = " ".join(separated[0])
        definition = " ".join(separated[1])
        m = re.match(r'(C[0-9]+)$', definition)
        if m:
            tla_search = m.group(1)
            print(f"Found TLA: {tla_search}")
            if not check_tla_exists(tla_search):
                tla_search = None

    word = strip_hyphens(word)
    print(f"word: {word}, definition: {definition}, tla_search: {tla_search}")

    entries = retrieve_entries(word, dialect, pos, definition, def_search_type, def_lang, params=params, tla_search=tla_search)
    related_entries = retrieve_related(word)
    lemmas = get_lemmas_for_word(word)

    if entries:
        entry_xml_id = entries[0]['xml_id']
        lemma = entries[0]['Name']
    else:
        entry_xml_id = ""
        lemma = ""

    return render_template('template.html', entries=entries, related_entries=related_entries, params=params, entry_xml_id=entry_xml_id, lemma=lemma, lemmas=lemmas)

@app.route('/network_thumb', methods=['GET'])
def network_thumb():
    word = escape(request.args.get("word", "")).replace("(", "").replace(")", "").replace("=", "").replace("<", "").strip()
    pos = escape(request.args.get("pos", "--")).replace("(", "").replace(")", "").replace("=", "").strip()
    tla = escape(request.args.get("tla", "--")).replace("(", "").replace(")", "").replace("=", "").strip()

    if pos not in ["N", "V", "VSTAT", "VIMP", "PREP"] or len(word.strip()) == 0:
        return '<div class="content">No network data found for your query</div>'

    rows = retrieve_network_data(word, pos)
    if len(rows) < 1:
        return '<div class="content">No network data found for your query</div>'

    output = ["||".join(list(row)[:-1] + [str(row[-1])]) for row in rows]
    tsv = "%%".join(output) + "\n"

    return render_template('network_thumb.html', tsv=tsv, word=word, tla=tla)

@app.route('/entry', methods=['GET'])
def entry():
    tla_id = escape(request.args.get("tla", "")).replace("(", "").replace(")", "").replace("=", "").strip()
    entry = retrieve_entry_data(tla_id)
    if not entry:
        return '<div class="content">No entry found for your query</div>'

    orth_entries = parse_entry(entry)
    collocates = retrieve_collocates(entry['Name'])

    return render_template('template.html', entry=entry, orth_entries=orth_entries, collocates=collocates)

if __name__ == "__main__":
    app.run(debug=True)