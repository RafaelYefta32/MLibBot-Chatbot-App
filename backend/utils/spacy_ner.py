import spacy

nlp = spacy.load("xx_ent_wiki_sm")

def extract_entities(text: str):
    doc = nlp(text)
    ents = [(ent.text, ent.label_) for ent in doc.ents]
    return ents
