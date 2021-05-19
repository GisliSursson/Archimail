import datetime, json, eml_parser, os, csv, spacy, re, requests, zipfile, lxml
from bs4 import BeautifulSoup
from io import StringIO
from lxml import etree
from datetime import timezone
from typing import Dict
import pandas as pd
from bs4 import BeautifulSoup
from os.path import dirname, abspath
from ast import literal_eval
import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from spacy.lang.fr.stop_words import STOP_WORDS as spacy_stop
import time

# Calcul du timestamp de lancement du script (UTC)
dt = datetime.datetime.now(timezone.utc)
utc_time = dt.replace(tzinfo=timezone.utc)
start_time = utc_time.now()

# Natural language processing
# On deux listes de stopwords (mots-outils à éviter)
spacy_fr = spacy.load('fr_core_news_md')
nltk_stop = nltk.corpus.stopwords.words('french')
# On décide que l'on doit supprimer toutes les formes des verbes être et avoir qui servent dans 
# la plupart des cas à construire des conjugaisons et ne sont donc pas signifiants. Formes récupérées
# sur Wikitionary.
autres_stop = ['être', 'avoir', 'suis','es','est','sommes','êtes','sont','étais','était','étions','étiez',
               'étaient','fus','fut','fûmes','fûtes','furent','serai','seras'
               ,'sera','serons','serez','seront','serais','serais','serait','serions','seriez','seraient',
               'sois','sois','soit','soyons','soyez','soient','fusse','fusses','fût','fussions','fussiez','fussent',
               'ai','as','a','avons','avez','ont','avais','avais','avait','avions','aviez','avaient','eus','eus',
               'eut','eûmes','eûtes','eurent','aurai','auras','aura','aurons','aurez',
               'auront','aurais','aurais','aurait','aurions','auriez','auraient', 'aie','aies','ait','ayons','ayez',
               'aient','eusse','eusses','eût','eussions','eussiez','eussent']
# Ajout manuel de stopwords qui ne semblent pas être dans les frameworhttp status code E+017
# URLs qui sont dans les signatures, évitées pour gagner du temps. 
url_a_eviter = ['http://www.chartes.psl.eu', 'https://fr.linkedin.com/in/victor-meynaud-72b2a3113/fr', 'http://www.enc-sorbonne.fr']
# Ajout manuel de stopwords qui ne semblent pas être dans les frameworks utilisés
autres_sw = ['www', 'https', 'http', 'je', 'tu', 'il', 'nous', 'vous', 'ils', 'elle', 'elles', 'on', 'leur', 'leurs', 'moi', 'toi',
             'mon','ma','mes','ton','ta','tes','son','sa','ses','person','notre','nos','votre','vos','leur','leurs', 'très']
# Chemin où le script est exécuté
chemin_actuel = dirname(abspath(__file__))

def trouver_url(texte):
    """Fonction qui applique ici les recommandations INTERPARES pour la pérennisation numérique des liens
    
    :param texte: corps du mail à parser
    :type texte: str
    :return liste_uri: liste des uri trouvés
    :rtype liste_uri: list
    :return liste_statut: liste des codes HTTP
    :rtype liste_uri: list
    :return liste_date_test: liste des timestamps
    :rtype liste_uri: list
    :return liste_pers: liste des subdomain + domain + top-level domain
    :rtype liste_uri: list
    """
    # On trouve les URL avec une regex non greedy
    url_group = re.findall(r"""(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s<>"']{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s<>"']{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s<>"']{2,}|www\.[a-zA-Z0-9]+\.[^\s<>"']{2,})""", texte)
    if url_group:
        # On met les résultats des recherchers dans des listes au cas où il y aurait plus d'une URL dans un mail
        liste_uri = []
        liste_statut = []
        liste_date_test = []
        liste_pers = []
        for url in url_group:
            url = str(url)
            uri = url
            # On évite de considérer "www.example.com" et "www.example.com/" comme deux URL différentes
            if uri[-1] == "/" or uri[-1] == "\t" or uri[-1] == "→":
                uri = url[:-1]
            # On évite les URL à éviter
            if uri not in url_a_eviter:
                if uri not in liste_uri:
                    uri_testee = uri
                    try:
                        # Charger que le header est plus court que charger toute la page
                        # On cherche les infos voulues...
                        req = requests.head(uri_testee, timeout=5)
                        statut = str(req.status_code)
                        date_test = str(utc_time.now())
                        pers = str(re.findall(r'/{2}([a-zA-Z0-9\.-]+\.[a-z]{2,3})?', uri_testee)[0])
                        # ... on les append dans les listes
                        liste_uri.append(uri_testee)
                        liste_statut.append(statut)
                        liste_date_test.append(date_test)
                        liste_pers.append(pers)
                    # Erreur retournée si le code renvoyé n'est pas du HTTP standard (requests.exceptions.ConnectionError)
                    except requests.exceptions.ConnectionError:
                        pass
                    # Au cas où un site aurait été mis dans le corps du texte (sans http)
                    except requests.exceptions.MissingSchema:
                        pass
                    except requests.exceptions.ReadTimeout: # Erreur si la réponse est trop lente
                        pass
                    except requests.exceptions.InvalidURL: # Erreur qui peut être causée par un problème d'encodage
                        pass
                    except requests.exceptions.InvalidSchema: # Erreur qui peut être causée par un problème d'encodage
                        pass
                else:
                    pass
            else:
                pass
        # Si aucune URL n'est trouvée, la fonction retourne rien. Les cellules correspondantes dans le CSV seront donc vides    
        return liste_uri, liste_statut, liste_date_test, liste_pers   

def liste_en_str(liste):
    """Fonction à transformer une liste en str, chaque élément de la liste étant séparé par une virgule
    
    :param liste: liste à stringify
    :type liste: list
    :return string: liste stringifiée
    :rtype string: str
    """
    if len(liste) == 1:
        string = str(liste[0])
    else:
        string = ','.join(str(valeur) for valeur in liste)
    return string

# Difficile de ne pas attraper autre chose que les noms en regex.
def trouver_noms_propres(texte):
    """Fonction utilisant une librairie de Natural Language Processing pour détecter les noms propres. Le but est d'éviter que
    des noms propres ne se retrouvent dans les métadonnées pour des raisons de protection des données personnelles. 
    
    :param texte: corps d'un mail
    :type texte: str
    :return index: nombre servant à réaliser un comptage global
    :rtype index: int
    :return liste_noms: liste des noms propres trouvés (uniques)
    :rtype string: list
    """
    sp = spacy_fr(texte)
    pers_list = []
    mauvais_char = False
    index = 0
    # L'algorithme de Spacy attribue le label "PER" à ce qu'il pense être un nom de personne (reconnaissance d'entités nommées)
    pers_list.append([element for element in sp.ents if element.label_ == 'PER'])
    # Pb: matche aussi les noms de personnages "historiques", les titres ("monsieur") et ceux dans les url
    liste_noms = []
    try:
        # PB : 23/04 laisse passer certains noms propres
        for element in pers_list:
            for nom in element:
                nom_str = str(nom.text)
                for lettre in nom_str:
                    if lettre.isnumeric() or lettre in [";", "/", "_", "<", ">", "^"]:
                        mauvais_char = True
                        break
                if mauvais_char is False:
                    liste_noms.append(nom_str)
                    index += 1
        return index, list(set(liste_noms))
    # Si aucun nom propre n'a été trouvé
    except:
        return index, None

def url_wayback(url):
    """Fonction faisant une requête à la Wayback Availability JSON API. Si l'URL a été archivées, l'API retourne 
    l'enregistrement le plus récent. Sinon elle retourne un dict vide. Si la Wayback Machine n'a rien d'archivé pour l'URL testée
    la fonction retourne 4 None. 
    
    :param url: URL à tester
    :type url: str
    :return status: code HTTP
    :rtype status: str
    :return available: élément "available" du dict JSON retourné par l'API (DEF A TROUVER)
    :rtype available: str (bool)
    :return url_2: URL de l'archive
    :rtype available: str
    :return time: timestamp de l'archive
    :rtype available: str
    """
    url_api = "http://archive.org/wayback/available?url=" + url
    # print(url_api)
    try:
        req = requests.get(url_api, timeout=5)
        resp = json.loads(str(req.text))
    except requests.exceptions.ReadTimeout or requests.exceptions.ConnectTimeout: # Si l'API a mis trop de temps à répondre
        pass
    # Si elle ne trouve rien, l'API retourne un dict vide. 
    try:
        if resp["archived_snapshots"] != {}:
            status = resp["archived_snapshots"]["closest"]["status"]
            available = resp["archived_snapshots"]["closest"]["available"]
            url_2 = resp["archived_snapshots"]["closest"]["url"]
            time = resp["archived_snapshots"]["closest"]["timestamp"]
            return str(status), str(available), str(url_2), str(time)
        else: # Si l'API retourne une liste vide
            status = None
            available = None
            url_2 = None
            time = None
            return status, available, url_2, time
    except UnboundLocalError: # Si l'API a mis trop de temps à répondre
        status = None
        available = None
        url_2 = None
        time = None
        return status, available, url_2, time

def traitement_nlt(texte): 
    """ xxx

    """
    try:
        texte = nltk.clean_html(texte)
    except:
        pass
    # On évite la ponctuation (regex)
    tokenizer = nltk.RegexpTokenizer(r'\w+')
    # On tokenise les mots
    text_tokens = tokenizer.tokenize(texte)
    # On enlève les mots outils français (le mot à garder ne doit pas être dans l'une
    # ou dans l'autre des 4 listes de mots à retirer)
    tokens_sans_sw_un = [mot for mot in text_tokens if not mot in spacy_stop]
    tokens_sans_sw_deux = [mot for mot in tokens_sans_sw_un if not mot in nltk_stop]
    tokens_sans_sw_trois = [mot for mot in tokens_sans_sw_deux if not mot in autres_stop]
    tokens_sans_sw = [mot for mot in tokens_sans_sw_trois if not mot in autres_sw]
    # On supprime les mots qui ont une longueur d'une seule lettre. Ce sont soit des mots outils qui aurait passé les filtres
    # précédents , soit des fautes de frappe.
    tokens_sans_sw = [mot for mot in tokens_sans_sw if len(mot) > 1]
    # On enlève les mots dans lesquels il y a des chiffres. Cela permet d'éviter de renvoyer des mots
    # comme "17h30". On supprime également les mots d'une lettre. 
    tokens_iterable = set(tokens_sans_sw)
    for element in tokens_iterable:
        for letter in element:
             if letter.isnumeric():
                try:
                    tokens_sans_sw.remove(element)
                except:
                    pass
    # On calcule la fréquence d'apparition des mots
    frequence = nltk.FreqDist(tokens_sans_sw)
    # On crée un dict du type {mot:fréquence}
    freq_dict = dict((word, freq) for word, freq in frequence.items())
    # On prend le top cinq des mots les plus fréquents
    # Le top est limité à 3 selon les recommandaitions des AN pour la balise "tag" (SEDA 2.1)
    top_trois = sorted(freq_dict.keys(), reverse=True)[0:3]
    # Classement par ordre alphabétique
    top_trois = sorted(top_trois)
    # On utilise Spacy pour la lemmatisation car il est mieux entraîné pour le français que 
    # NLTK.
    liste_lem = []
    # On crée une liste des lemmes des cinq mots les plus fréquents. Par exemple, si le mot est "chantait",
    # le lemme sera "chanter".
    for element in top_trois:
        sp = spacy_fr(element)
        for element in sp:
            lemme = element.lemma_
            liste_lem.append(lemme)
    return liste_lem


def extraire_contenu_mail(mail):
    """Fonction utilisant la librairie Python EMLParser transformant un mail (str) en un dict parsable
    
    :param mail: mail à parser (format eml)
    :type mail: str
    :return parsed_eml: mail parsé
    :rtype status: dict
    """
    with open(mail, 'rb') as mail_ouvert:
        raw_email = mail_ouvert.read()
        ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=False)
        parsed_eml = ep.decode_email_bytes(raw_email)
        return parsed_eml

def unzip(path):
    """ A SUPPRIMER
    """
    dirname = os.path.dirname(path)
    file = os.path.basename(path)
    new_dir = str(file) + "_unzip"
    new_path = os.path.join(dirname, new_dir)
    os.mkdir(new_path)
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(new_path)
    os.remove(path)
    return 1

def doc_unzip(path):
    """ A SUPPRIMER

    """
    id = os.path.basename(path)
    id = re.sub("\..+", "", id)
    
def test_seda(path):
    """ Fonction qui teste si le document est valide au schéma SEDA 2.1 (schéma téléchargé le 06/05/21)
    """
    print("Document testé en tant que manifeste SEDA 2.1 : " + str(path))
    xml_file = lxml.etree.parse(path)
    schema_loc = os.path.join(chemin_actuel, "seda", "seda-2.1-main.xsd")
    xml_validator = lxml.etree.XMLSchema(file=schema_loc)
    xml_validator.assert_(xml_file)
    # Le code crashera avec message d'erreur précis si le manifeste n'est pas conforme au SEDA
    print("Votre manifeste est valide par rapport au SEDA 2.1!")
    
def test_profil_minimum(path):
    """ Fonction qui teste si le document est conforme au profil minimum ADAMANT (version du SEDA 2.1 spécifique à ADAMANT). 
    Schéma RNG transmis le 18/05/21.
    """
    print("Document testé par rapport au profil minimum ADAMANT : " + str(path))
    schema = os.path.join(chemin_actuel, "seda", "profil_minimum_avant_enrichissement.rng")
    with open(path) as doc:
        relaxng_doc = etree.parse(schema)
        relaxng = etree.RelaxNG(relaxng_doc)
        doc = etree.parse(doc)
        if relaxng.validate(doc) == True:
            print("Votre manifeste est conforme au profil minimum ADAMANT!")
        else:
            raise Exception("Votre manifeste n'est pas valide par rapport au profil minimum ADAMANT!")

def donnees_perso(parsed_mail, path):
    # A SUPPRIMER
    cibles = ["perso", "personnel", "vacance", "enfant"]
    objet = (parsed_mail["header"]["subject"]).lower()
    corps = (parsed_mail["body"][0]["content"]).lower()
    with open("donnees_personnelles.csv", "w") as file:
        f = csv.writer(file, delimiter=",")
        for mot in cibles:
            if mot in objet or mot in corps:
                f.writerow(path)

def enrichir_manifeste(csv, manifest):
    """Fonction qui, à partir du CSV récapitulatif des métadonnées, enrichi le manifeste SEDA en y insérant les mots clefs
    pour chaque mail
    
    :param csv: chemin csv file
    :type csv: str
    :param csv: chemin xml file
    :type manifest: str
    :return nouv_man: chemin vers nouveau fichier XML créé
    :rtype status: str
    """
    print("Génération du manifeste enrichi...")
    count = 0
    nouv_man = manifest.replace(".xml", "") + "_new.xml"
    manifest = open(manifest, "r")
    source_xml = manifest.read()
    soup = BeautifulSoup(source_xml, 'xml')
    df = pd.read_csv(csv, sep=";", error_bad_lines=True)
    for index, line in enumerate(df["nom_fichier"]):
        # On récupère l'ID du binary data object correspondant à l'email en cours de traitement
        id_binary_data_object = re.findall(r"(ID[0-9]+)\.eml$", line)[0]
        # On trouve le binary data object correspondant au fichier en cours de traitement
        bdo_tag = soup.find("BinaryDataObject", {"id":id_binary_data_object})
        # On récupère l'id du data object group correspondant
        id_data_object_group = bdo_tag.find_parent("DataObjectGroup")["id"]
        # On accède à l'archive unit via la balise DataObjectGroupReferenceId
        reference_id = soup.find("DataObjectGroupReferenceId", string = id_data_object_group)
        # Une fois qu'on a le DataObjectGroupReferenceId, on remonte à l'archive unit correspondante
        archive_unit = reference_id.find_parent("ArchiveUnit")
        # On trouve le content de l'archve unit (là où on insèrera les informations)
        archive_unit_content = archive_unit.findChild("Content")
        soup_extend = ""
        try:
            # On ajoute à la soupe une str XML bien formée
            for mot in df["top_trois_mots"][index].split(","):
                soup_extend += '<Tag>{x}</Tag>'.format(x=mot)
                count += 1
        except AttributeError: #En cas de cellule vide dans la colonne top 3 mots
            pass
        archive_unit_content.append(soup_extend)
    print("Nombre de balises <tag> ajoutées : " + str(count))
    with open(nouv_man, "w+") as text_file:
        # Correction de ce que le beautifier de Beautiful Soup ne fait pas
        string = str(soup)
        string = re.sub("&lt;", "<", string)
        string = re.sub("&gt;", ">", string)
        string = re.sub("&", "&amp;", string)
        text_file.write(string)
    manifest.close()
    return nouv_man
            
def remplacer_man():
    print("Suppression de l'ancien manifeste et remplacement par le nouveau...")
    os.remove("manifest.xml")
    os.rename('manifest_new.xml','manifest.xml')

def traiter_mails(source, output):
    """Fonction qui parse les mails et exécute les fonctions définies ci-dessus. Elle écrit les résultats dans un fichier CSV
    récapitulaitf. 
    
    :param source: chemin vers le SIP
    :type source: str
    :param output: chemin vers le CSV qui sera créé (avec le nom voulu)
    :type outpu: str
    """
    with open(output, 'w') as f:
        writer = csv.writer(f, delimiter = ";")
        # Colonnes qui seront dans le CSV
        liste_col = ['nom_fichier', 'top_trois_mots', 'url(s)', 'resultat_test_URL', 'date_test_URL', 'responsable_URL', "internet_archive_status"
                    , "internet_archive_dispo", "internet_archive_url", "internet_archive_timestamp"]
        writer.writerow(liste_col)
        # Compteurs globaux    
        mail = 0
        nb_url = 0
        nb_noms = 0 
        nb_wb = 0 
        nb_zip = 0
        # On parse les noms de tous les fichiers du SIP
        for root, dirs, files in os.walk(source, topdown=True):
            for index, name in enumerate(files):
                filename = os.path.join(root, name)
                if filename.endswith(".zip"):
                    # On part du principe qu'il n'y a pas d'eml dans les zip
                    count = unzip(filename)
                    nb_zip += count
                # Si le fichier est un mail    
                if filename.endswith(".eml"):
                    mail += 1
                    liste_val = []
                    # On transforme le mail en données structurées
                    data = extraire_contenu_mail(filename)
                    texte = data["body"][0]["content"]
                    # On recherche les éventuels noms propres
                    compte_nom, liste_noms = trouver_noms_propres(texte)
                    if liste_noms:
                        # On supprime les noms propres trouvés (s'il y en a)
                        for nom in liste_noms:
                            texte = texte.replace(nom, "")
                    nb_noms += compte_nom
                    # Le "nom" de chaque fichier sera le chemin relatif à l'intérieur du SIP
                    parent_dir = filename.split(os.path.sep)[-2]
                    liste_val.append(parent_dir + "/" + name)
                    # On lance le calcul des mots-clefs
                    top = traitement_nlt(texte)
                    string = ','.join(str(valeur) for valeur in top)
                    liste_val.append(string)
                    try:
                        liste_test = []
                        # On ne lance pas la fonction sur texte_sans_nom au cas où des noms auraient été supprimés d'URL
                        # S'il y a des noms dans les URL dans le CSV de métadonnées, il y a peu de risques de diffusion 
                        # à une personne non autorisée contrairement aux métadonnées qui se trouvent dans le manifeste
                        liste_uri, liste_statut, liste_date_test, liste_pers = trouver_url(texte)
                        # liste_uri sera une liste vide si il n'y avait dans le mail que des URL marquées comme à éviter
                        if len(liste_uri) != 0:
                            # On insère les données pour les URL (si URL il y a)
                            nb_url += len(liste_uri)
                            uri = liste_en_str(liste_uri)
                            statut = liste_en_str(liste_statut)
                            date_test = liste_en_str(liste_date_test)
                            pers = liste_en_str(liste_pers)
                            liste_test.append(uri)
                            liste_test.append(str(statut))
                            liste_test.append(date_test)
                            liste_test.append(pers)
                            liste_val += liste_test
                            liste_wb = []
                            liste_stat_wb = []
                            liste_avai_wb = []
                            liste_lien_wb = []
                            liste_time_wb = []
                            # On insère les données relatives à la Wayback Machine (le cas échéant)
                            for uris in liste_uri:
                                status, available, lien, time = url_wayback(uris)
                                if status is not None:
                                    liste_stat_wb.append(status)
                                    liste_avai_wb.append(available)
                                    liste_lien_wb.append(lien)
                                    liste_time_wb.append(time)
                                    nb_wb += 1
                                else:
                                    liste_stat_wb.append(str(status))
                                    liste_avai_wb.append(str(available))
                                    liste_lien_wb.append(str(lien))
                                    liste_time_wb.append(str(time))
                            try:
                                stat_wb_str = liste_en_str(liste_stat_wb)
                                avai_wb_str = liste_en_str(liste_avai_wb)
                                lien_wb_str = liste_en_str(liste_lien_wb)
                                time_wb_str = liste_en_str(liste_time_wb)
                                liste_wb.append(stat_wb_str)
                                liste_wb.append(avai_wb_str)
                                liste_wb.append(lien_wb_str)
                                liste_wb.append(time_wb_str)
                            except NameError:
                                pass
                            try: 
                                liste_val += liste_wb
                            except:
                                pass
                    # Si aucune URL a été trouvée dans le mail, trouver_url retourne None
                    except TypeError:
                        pass
                    # On écrit dans le CSV
                    writer.writerow(liste_val)
        print("Nombre de mails traités : " + str(mail))
        print("Nombre d'URL traitées : " + str(nb_url))
        # print("Nombre de ZIP décompressés : " + str(nb_zip))
        print("Nombre d'éléments détectés comme des noms propres : " + str(nb_noms))
        print("Nombre de requêtes réussies faites à Internet Archive : " + str(nb_wb))
        try:
            print("Temps de calcul : " + str(utc_time.now() - start_time))
        except:
            pass

output = os.path.join(chemin_actuel,"perso","test_1905.csv")
source = os.path.join(chemin_actuel,"perso","sip")
traiter_mails(source, output)
manifest = os.path.join(source, "manifest.xml")
nouv_man = enrichir_manifeste(output, manifest)
test_seda(nouv_man)
test_profil_minimum(nouv_man)
#remplacer_man()