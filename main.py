import datetime, json, eml_parser, os, csv, spacy, re, requests, zipfile, lxml, hashlib
from bs4 import BeautifulSoup
from io import StringIO
from lxml import etree
from datetime import timezone, date
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
from zipfile import ZipFile
import shutil

# URL à éviter à mettre éventuellement à jour 
url_a_eviter = ['http://www.chartes.psl.eu', 'https://fr.linkedin.com/in/victor-meynaud-72b2a3113/fr', 'http://www.enc-sorbonne.fr']

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
                    except UnicodeError: # Erreur en cas d'URL trop longue ou de problème d'encodage
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
    # On peut avoir des erreur si l'API met trop de temps à répondre, si elle est down ou renvoie un JSON malformé
    except: 
        # Ou s'il y a une erreur dans le JSON
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
    except UnboundLocalError: 
        # Si l'API a mis trop de temps à répondre ou s'il y a un problème
        # dans le JSON renvoyé
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
    # print(frequence.items())
    # On crée un dict du type {mot:fréquence}
    freq_dict = dict((word, freq) for word, freq in frequence.items())
    # On classe par ordre décroissant
    freq_dict = dict(sorted(freq_dict.items(), key=lambda item: item[1], reverse=True))
    print(freq_dict)
    # On prend le top cinq des mots les plus fréquents
    # Le top est limité à 3 selon les recommandaitions des AN pour la balise "tag" (SEDA 2.1)
    top_trois = []
    for key, value in freq_dict.items():
        top_trois.append(key)
    top_trois = top_trois[0:3]
    # top_trois = freq_dict[0:3]
    # top_trois = top_trois.keys()
    # top_trois = sorted(freq_dict.keys(), reverse=True)[0:3]
    print(top_trois)
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
    
"""
def test_seda(path):
     Fonction qui teste si le document est valide au schéma SEDA 2.1 (schéma téléchargé le 06/05/21)
    Au 20/05/21 il est normal que la balise OriginatingSystemIdReplyTo ne soit pas dans le SEDA
    
    print("Document testé en tant que manifeste SEDA 2.1 : " + str(path))
    xml_file = lxml.etree.parse(path)
    schema_loc = os.path.join(chemin_actuel, "seda", "seda-2.1-main.xsd")
    xml_validator = lxml.etree.XMLSchema(file=schema_loc)
    xml_validator.assert_(xml_file)
    # Le code crashera avec message d'erreur précis si le manifeste n'est pas conforme au SEDA
    print("Votre manifeste est valide par rapport au SEDA 2.1!") """
    
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
        relaxng.assertValid(doc)
        print("Votre manifeste est conforme au profil minimum ADAMANT!")

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
    documentation = """Enrichissement du manifeste SEDA par le Bureau des Archives du Conseil d'Etat via un script rédigé dans le langage de 
    programmation Python. Pour le corps chaque courriel (fichier .eml), le script réalise une tokenisation (on évite de prendre en compte les mots
    grammaticaux etc.), une lemmatisation (le fait de ramener chaque mot à sa forme du dictionaire) et un évitement des noms propres.
    Le script calcule ensuite la fréquence de chaque mot dans le courriel et associe audit courriel les trois mots les plus fréquents
    via la balise 'tag' dans le manifeste SEDA.
    """    
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
        # print(archive_unit)
        # On trouve le content de l'archve unit (là où on insèrera les informations)
        archive_unit_content = archive_unit.findChild("Content")
        writer = archive_unit_content.findChild("Writer")
        # Parfois l'expéditeur d'un mail n'est pas renseigné
        if writer is None:
            writer = archive_unit_content.findChild("Title")
        soup_extend = ""
        try:
            # On ajoute à la soupe une str XML bien formée
            for mot in df["top_trois_mots"][index].split(","):
                soup_extend += '<Tag>{x}</Tag>'.format(x=mot)
                count += 1
        except AttributeError: #En cas de cellule vide dans la colonne top 3 mots
            pass
        # Insérer avant le Title peut causer des erreurs si RESIP n'a pas détecté de Title dans le mail
        writer.insert_after(soup_extend)
    print("Nombre de balises <tag> ajoutées : " + str(count))
    print("Documentation de l'enrichissement du manifest...")
    descriptive = soup.find("DescriptiveMetadata")
    content = descriptive.findChild("Content")
    date = dt.isoformat()
    # heure = utc_time.now()
    # current_time = heure.strftime("%H:%M:%S")
    soup_extend = "<Event><EventType>Enrichissement des métadonnées au niveau de chaque message via un script Python</EventType><EventDateTime>{x}</EventDateTime><EventDetail>{y}</EventDetail></Event>".format(x=str(date), y=documentation)
    content.append(soup_extend)
    with open(nouv_man, "w+") as text_file:
        # Correction de ce que le beautifier de Beautiful Soup ne fait pas
        # On corrige l'encodage pour les balises tag et event
        # Syntaxe pour préserver les entités XML générées par RESIP en n'encodant pas les accents français et en ne mettant pas
        # d'entitées pour les balises rajoutées.
        string = str(soup.prettify(formatter='minimal'))
        string = re.sub("&lt;Tag&gt;", "<Tag>", string)
        string = re.sub("&lt;/Tag&gt;", "</Tag>", string)
        # string = re.sub("&^([^;\\W]*([^;\\w]|$))", "&amp;", string)
        text_file.write(string)
    manifest.close()
    print("Génération terminée")
    return nouv_man
            
def remplacer_man(manifest):
    print("Suppression de l'ancien manifeste et remplacement par le nouveau enrichi...")
    # os.remove(manifest)
    os.remove(manifest)
    os.rename(os.path.join(source, "manifest_new.xml"), os.path.join(source, "manifest.xml"))
    print("Remplacement effectué")

def zipDir(dirPath, zipPath):
    print("Recompression du SIP...")
    zipf = zipfile.ZipFile(zipPath , mode='w')
    lenDirPath = len(dirPath)
    for root, _ , files in os.walk(dirPath):
        for file in files:
            filePath = os.path.join(root, file)
            zipf.write(filePath , filePath[lenDirPath :] )
    zipf.close()
    print("Compression du SIP terminée")

def strip_xml(xml):
    print("Suppression des espaces blancs inutiles dans le nouveau manifeste...")
    tree = etree.parse(xml)
    root = tree.getroot()
    for elem in root.iter('*'):
        if elem.text is not None:
            elem.text = elem.text.strip()
    with open(xml, 'wb') as f:
        tree.write(f, encoding='utf-8')
    print("Suppression terminée")

def doc_url(manifest):
    """Documentation dans le manifeste de la génération du CSV sur les URL
    """
    print("Documentation dans le manifeste de la génération du CSV de pérennisation des URL...")
    documentation = """Fichier généré automatiquement via un script écrit dans le langage Python par le Bureau des Archives du
    Conseil d'Etat. Le fichier CSV (comma separated values), pour chaque courriel, indique les 3 mots-clefs qui ont été déterminés et insérés dans le manifeste. 
    Le script réalise également une opération de pérennisation des URL (Uniform Resource Locator) selon les recommandations du groupe de recherche
    INTERPARES. Dans le corps des mails, les URL sont détectées via une expression régulière. Le script inscrit dans le CSV le
    code HTTP renvoyé (permettant de vérifier si l'URL est encore active lors du traitement par les Archives), la date
    du test et le nom du site (sous la forme subdomain + domain + top-level domain). De plus, le script teste aussi la disponibilité
    de l'URL en question sur l'API de la Wayback Machine (Internet Archive). Si l'archive existe, il écrit dans le CSV la disponibilité 
    de l'API, l'URL de la page archivée, la date de la page archivée et le code HTTP.
    """
    manifest_ouvert = open(manifest, "r")
    source_xml = manifest_ouvert.read()
    soup = BeautifulSoup(source_xml, 'xml')
    # Création de l'Event de documentation au niveau le plus haut de la description
    descriptive = soup.find("DescriptiveMetadata")
    content = descriptive.findChild("Content")
    date = dt.isoformat()
    soup_extend = "<Event><EventType>Génération d'un fichier CSV de pérennisation des URL</EventType><EventDateTime>{x}</EventDateTime><EventDetail>{y}</EventDetail></Event>".format(x=str(date), y=documentation)
    content.append(soup_extend)
    # Génération de la documentation au niveau du DataObjectGroup et de l'ArchiveUnit
    cible = os.path.join(source, "content", "urls.csv")
    with open(cible) as file:
        content = file.read()
        hash = hashlib.sha512(content.encode()).hexdigest()
    # Détermination du dernier ID (numériquement) généré par RESIP
    liste_files = [name for name in sorted(os.listdir(os.path.join(source, "content")))]
    liste_files = liste_files[:-1]
    liste_id_files = []
    for element in liste_files:
        for letter in element:
            if letter.isnumeric() == False:
                element = element.replace(letter, "")
        liste_id_files.append(element)
    for element in liste_id_files:
        element = int(element)
    liste_id_files.sort(key=int)
    # L'ID du binary data object créé (et donc aussi le nom du fichier correspondant) sera égal à l'id du dernier fichier 
    # (avant urls.csv) dans le dossier content +2 
    last_id = liste_id_files[-1]
    binary_data_obj_id = int(last_id) + 3
    data_obj_group_id = binary_data_obj_id - 1
    archive_unit_id = binary_data_obj_id + 1
    id_string = 'ID' + str(binary_data_obj_id) + ".csv"
    os.rename(cible, os.path.join(source, "content", id_string))
    date = dt.isoformat()
    archive_unit_glob = soup.find("ArchiveUnit", {"id":"ID10"})
    #dern_arch_unit = archive_unit_glob.find_all("div")[-1]
    soup_extend =""" 
    <ArchiveUnit id="{a}">
          <Content>
            <DescriptionLevel>Item</DescriptionLevel>
            <Title>urls.csv</Title>
            <Event>
              <EventType>Création</EventType>
              <EventDateTime>{b}</EventDateTime>
              <EventDetail>Généré via un script Python par le Bureau des Archives</EventDetail>
            </Event>
          </Content>
          <DataObjectReference>
            <DataObjectGroupReferenceId>{c}</DataObjectGroupReferenceId>
          </DataObjectReference>
        </ArchiveUnit>
    """.format(a="ID"+str(archive_unit_id), c="ID"+str(data_obj_group_id), b=str(date))
    archive_unit_glob.append(soup_extend)
    descri_meta = soup.find("DescriptiveMetadata")
    soup_extend = """<DataObjectGroup id="{a}">
      <BinaryDataObject id="{b}">
        <DataObjectVersion>BinaryMaster_1</DataObjectVersion>
        <Uri>content/{c}.csv</Uri>
        <MessageDigest algorithm="SHA-512">{d}</MessageDigest>
        <Size>24040</Size>
        <FormatIdentification>
          <FormatLitteral>Comma Separated Values</FormatLitteral>
          <MimeType>text/csv</MimeType>
          <FormatId>x-fmt/18</FormatId>
        </FormatIdentification>
        <FileInfo>
          <Filename>urls.csv</Filename>
          <LastModified>{e}</LastModified>
        </FileInfo>
      </BinaryDataObject>
    </DataObjectGroup>""".format(a="ID"+str(data_obj_group_id), b="ID"+str(binary_data_obj_id), c="ID"+str(binary_data_obj_id), d=hash, e=str(date))
    descri_meta.insert_before(soup_extend)
    with open(manifest, "w") as text_file:
        # Pour éviter d'encoder les entités générées par RESIP
        string = str(soup.prettify(formatter = None))
        # string = string.replace("&", "&amp;")
        string = re.sub(r"<OriginatingSystemId>(.*?)</OriginatingSystemId>", "<OriginatingSystemId>&lt;\\1&gt;</OriginatingSystemId>", string, flags=re.DOTALL)
        string = re.sub(r"<OriginatingSystemIdReplyTo>(.*?)</OriginatingSystemIdReplyTo>", "<OriginatingSystemIdReplyTo>&lt;\\1&gt;</OriginatingSystemIdReplyTo>", string, flags=re.DOTALL)
        string = re.sub(r"&lt;\s*?<", "&lt;", string, flags=re.DOTALL)
        string = re.sub(r">\s*?&gt;", "&gt;", string, flags=re.DOTALL)
        # string = re.sub("&lt;Event&gt;", "<Event>", string)
        # string = re.sub("&lt;/Event&gt;", "</Event>", string)
        # string = re.sub("&lt;EventType&gt;", "<EventType>", string)
        # string = re.sub("&lt;/EventType&gt;", "</EventType>", string)
        # string = re.sub("&lt;EventDateTime&gt;", "<EventDateTime>", string)
        # string = re.sub("&lt;/EventDateTime&gt;", "</EventDateTime>", string)
        # string = re.sub("&lt;EventDetail&gt;", "<EventDetail>", string)
        # string = re.sub("&lt;/EventDetail&gt;", "</EventDetail>", string)
        # Traitement des esperluettes qui ne sont pas dans des entités
        string = re.sub("&(?![a-z]+;)", "&amp;", string)
        # Certaines personnes utilisent les chevrons comme "quotes"
        string = re.sub("<<", "&lt;&lt;", string)
        string = re.sub(">>", "&gt;&gt;", string)
        text_file.write(string)
    print("Documentation terminée")
    
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
        print("Début de l'analyse des fichiers des courriels...")
        # On parse les noms de tous les fichiers du SIP
        for root, dirs, files in os.walk(source, topdown=True):
            for index, name in enumerate(files):
                filename = os.path.join(root, name)
                # Si le fichier est un mail    
                if filename.endswith(".eml"):
                    mail += 1
                    print("Mails traités : " + str(mail))
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
        print("Nombre total de mails traités : " + str(mail))
        print("Nombre d'URL traitées : " + str(nb_url))
        # print("Nombre de ZIP décompressés : " + str(nb_zip))
        print("Nombre d'éléments détectés comme des noms propres : " + str(nb_noms))
        print("Nombre de requêtes réussies faites à Internet Archive : " + str(nb_wb))
        try:
            print("Temps de calcul : " + str(utc_time.now() - start_time))
        except:
            pass

def unzip(path):
    for root, dirs, files in os.walk(path, topdown=True):
        for name in files:
            filename = os.path.join(root, name)
            if filename.endswith(".zip"):
                with ZipFile(filename, 'r') as zip:
                    print('Décompression du ZIP...')
                    cible = os.path.join(chemin_actuel, "sip_tempdir")
                    zip.extractall(cible)
                    print('Décompression terminée')

source = os.path.join(chemin_actuel, "sip_tempdir")
output = os.path.join(chemin_actuel, "sip_tempdir", "content", "urls.csv")
if __name__ == '__main__':
    unzip(os.path.join(chemin_actuel,"sip"))
    traiter_mails(source, output)
    manifest = os.path.join(source, "manifest.xml")
    nouv_man = enrichir_manifeste(output, manifest)
    doc_url(nouv_man)
    # test_seda(nouv_man)
    cible_content = os.path.join(source, "content")
    cible_xml = os.path.join(chemin_actuel,source, "manifest_new.xml")
    liste_zip = [cible_content, cible_xml]
    sip = source
    strip_xml(cible_xml)
    test_profil_minimum(nouv_man)
    remplacer_man(manifest)
    today = date.today()
    date = today.strftime("%d%m%Y")
    nom_sip = "SIP_" + str(date) + ".zip"
    zipDir(sip, nom_sip)
    print("Suppresion des fichiers temporaires...")
    shutil.rmtree(source)
    print("Suppresion effectuée")
    print("Script terminé avec succès")
