import datetime, json, eml_parser, os
import pandas as pd
from bs4 import BeautifulSoup
from os.path import dirname, abspath

chemin_actuel = dirname(abspath(__file__))

def extraire_contenu_mail(mail):
    with open(mail, 'rb') as mail_ouvert:
        raw_email = mail_ouvert.read()
        ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=False)
        parsed_eml = ep.decode_email_bytes(raw_email)
        parsed_eml = str(parsed_eml)
        return json.dumps(parsed_eml)

for root, dirs, files in os.walk(os.path.join(chemin_actuel,"perso","mail_enc"), topdown=True):
    for name in files:
        filename = os.path.join(root, name)
        if filename.endswith(".eml"):
            data = extraire_contenu_mail(filename)
            print(type(data))


