from datetime import datetime
import emails, random, os, re
import shutil
from os.path import dirname, abspath
import subprocess
from odf.opendocument import OpenDocumentText
from odf.text import P
from main import traiter_mails as generation_csv
import pandas as pd
import pytest

# Script servant à tester Archimail à partir de données factices. Le script de test lance le script principal qui génère le CSV 
# rassemblant les métadonnées générées. Le script de test vérifie ensuite la validité de ces métadonnées dans le CSV.

chemin_actuel = dirname(abspath(__file__))
rand = random.randint(1, 10)
nb_mails = random.randint(100, 200)
print("Nombre de mails factices à générer : " + str(nb_mails))
rand_2 = random.randint(1, 10)
# URL qui sert de base à ce qui sera inséré dans les mails (ID généré aléatoirement) qui pourra être valide ou invalide
wikidata = "https://www.wikidata.org/wiki/Q"
# Adresses dummy pour populate les mails
adress = ["timlinux@hotmail.com",
"timtroyr@me.com",
"smcnabb@live.com",
"gozer@outlook.com",
"kohlis@att.net",
"dgatwood@icloud.com",
"snunez@me.com",
"lydia@aol.com",
"imightb@outlook.com",
"danny@aol.com",
"dieman@aol.com",
"gator@me.com"]

# Textes d'auteurs français du XIXe siècle issus du projet Gutenberg. Ils servent à populate les dummy mails.
lorem = {1:"""Les érudits ont amèrement reproché à Guillaume, moine de l’abbaye
de Jumiège, d’avoir reproduit dans les premiers livres de son
Histoire des Normands, la plupart des fables dont son prédécesseur
Dudon, doyen de Saint-Quentin, avait déjà rempli la sienne. Si
Guillaume n’eût ainsi fait, cette portion de son ouvrage
n’existerait pas, car il n’aurait rien eu à y mettre; il a
recueilli les traditions de son temps sur l’origine, les exploits,
les aventures des anciens Normands et de leurs chefs; aucun peuple
n’en sait davantage, et n’a des historiens plus exacts sur le
premier âge de sa vie. 
""",
2:"""Il y a aujourd'hui trois cent quarante-huit ans six mois et dix-neuf
jours que les Parisiens s'éveillèrent au bruit de toutes les cloches
sonnant à grande volée dans la triple enceinte de la Cité, de
l'Université et de la Ville.""",
3:"""D'un saut formidable, la bête atteignit la gorge du mannequin,
et, les pattes sur les épaules, se mit à la déchirer.
Elle retombait, un morceau de sa proie à la gueule, puis
s'élançait de nouveauif __name__ == "__main__":, enfonçait ses crocs dans les cordes,
arrachait quelques parcelles de nourriture, retombait encore,
et rebondissait, acharnée. Elle enlevait le visage
par grands coups de dents, mettait en lambeaux le col
entier.""",
4:"""A son tour, de son bras tendu, il désignait dans la nuit le village
dont le jeune homme avait deviné les toitures.  Mais les six berlines
étaient vides, il les suivit sans un claquement de fouet, les jambes
raidies par des rhumatismes; tandis que le gros cheval jaune repartait
tout seul, tirait pesamment entre les rails, sous une nouvelle
bourrasque, qui lui hérissait le poil.""",
5:"""C'est une loi de l'histoire: un monde qui finit, se ferme et s'expie
par un saint. Le plus pur de la race en porte les fautes, l'innocent
est puni. Son crime, à l'innocent, c'est de continuer un ordre
condamné à périr, c'est de couvrir de sa vertu une vieille injustice
qui pèse au monde. À travers la vertu d'un homme, l'injustice sociale
est frappée. Les moyens sont odieux; contre Louis le Débonnaire, ce
fut le parricide. Ses enfants couvrirent de leurs noms les nations
diverses qui voulaient s'arracher de l'Empire.""",
6:"""
Tout enfant, j'allais rêvant Ko-Hinnor,
Somptuosité persane et papale,
Héliogabale et Sardanapale!
Mon désir créait sous des toits en or,
Parmi les parfums, au son des musiques,
Des harems sans fin, paradis physiques!"""
}

# Noms propres dummy
noms = ["Pierre de Ronsard",
"Joachim Du Bellay",
"Victor Hugo",
"Marie de France",
"Charles Baudelaire",
"Arthur Rimbaud",
"Paul Verlaine",
"Guillaume Apollinaire",
"Paul Eluard",
"Georges Sand"]

def folder():
    """ Création de dossiers qui contiendront les données de test """
    directory = "resultat"
    dir_par_dummy = "dummy"
    dir_dummy_mails = "dummy_mails"
    path = os.path.join(chemin_actuel, directory)
    path_2 = os.path.join(chemin_actuel, dir_par_dummy)
    path_3 = os.path.join(chemin_actuel, dir_par_dummy, dir_dummy_mails)
    if os.path.exists(path):
        shutil.rmtree(path)
        os.mkdir(path)
    else:
        os.mkdir(path)
    if os.path.exists(path_2):
        shutil.rmtree(path_2)
        os.mkdir(path_2)
        os.mkdir(path_3)
    else:
        os.mkdir(path_2)
        os.makedirs(path_3)
    print("Faits dossiers")

folder()

def create_dummy_pdf(nombre):
    """ Création de pièces jointes dummy PDF """
    for x in range(1,nombre):
        bashCommand = "dummypdf -f ./dummy/test_{a}.pdf -n {b}".format(a=str(x), b=str(random.randint(1, 20)))
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
    print("Fait PDF")
    
def create_dummy_odt(lorem, iter, rand):
    """ Création de pièces jointes ODT dummy """
    lorem_rand = random.randint(1, 6)
    lorem_rand_2 = random.randint(1, 6)
    for x in range(1, iter):
        textdoc = OpenDocumentText()
        texte = lorem[lorem_rand] + lorem[lorem_rand_2]
        p = P(text=texte)
        textdoc.text.addElement(p)
        textdoc.save("./dummy/test_{a}".format(a=str(x)), True)
    print("Fait ODT")

def create_dummy_mails(lorem, iter, rand):
    """ Création des mails dummy """
    orig = lorem
    liste_odt = []
    liste_pdf = []
    for root, dirs, files in os.walk(os.path.join("./dummy")):
        for name in files:
            filename = os.path.join(root, name)
            if filename.endswith(".odt"):
                liste_odt.append(str(filename))
            elif filename.endswith(".pdf"):
                liste_pdf.append(str(filename))
            else:
                pass
    for x in range(1, iter):
        lorem_rand = random.randint(1, 6)
        lorem = orig[lorem_rand]
        lorem_inser = list(filter(None, re.split("\s", lorem)))
        nb = random.randint(0, 1)
        nb_lien = random.randint(0, 1)
        nb_noms = random.randint(0, 1)
        id_wikidata = random.randint(1, 999)
        url_OK = wikidata + str(id_wikidata)
        url_NOK = wikidata + "nok" + str(id_wikidata)
            # Permet de splitter sur les mots en évitants les éventuels problèmes d'encodage de la str
        if nb_lien != 0:
            pos = random.randint(0, len(lorem_inser)-1)
            pos_2 = random.randint(0, len(lorem_inser)-1)
            lorem_inser.insert(pos, url_OK)
            lorem_inser.insert(pos_2, url_NOK)
        if nb_noms != 0:
            pos_3 = random.randint(0, len(lorem_inser)-1)
            nom = random.choice(noms)
            lorem_inser.insert(pos_3, nom)
        try:
            string = ""
            for element in lorem_inser:
                string = string + " " + element
            #string = ' '.join(str(valeur) for valeur in lorem)
            lorem = string
        except TypeError: #Si ni nom, ni lien
            pass
        if type(x//2) is not float: # Moyen de sélectionner un mail sur 2
            message = emails.html(html="<p>{a}</p>".format(a=(lorem*rand)),
                                subject=lorem[:20] + "_" + str(iter),
                                mail_from=('Some Name', adress[random.randint(0, len(adress)-1)]))
            if nb == 0:
                if len(liste_odt) != 0:
                    random_odt = random.choice(liste_odt)
                    message.attach(data=open(random_odt, 'rb'), filename=random_odt)
            else:
                if len(liste_pdf) != 0:
                    random_pdf = random.choice(liste_pdf)
                    message.attach(data=open(random_pdf, 'rb'), filename=random_pdf)
        else:
            message = emails.html(html="<p>{a}</p>".format(a=(lorem*rand)),
                                subject=lorem[:20] + "_" + str(iter),
                                mail_from=('Some Name', adress[random.randint(0, len(adress)-1)]))
        s = message.as_string()
        with open("./dummy/dummy_mails/ID{a}.eml".format(a=str(x)), "w") as mail:
            mail.write(s)
    print("Faits dummy mails")

create_dummy_pdf(rand)
create_dummy_odt(lorem, rand, rand_2)
create_dummy_mails(lorem, nb_mails, rand_2)
    
output_test = os.path.join(chemin_actuel,"resultat","resultat_test.csv")
source_test = os.path.join(chemin_actuel,"dummy","dummy_mails")

generation_csv(source_test, output_test)

# Transformation du CSV en dataframe

df = pd.read_csv(output_test, sep=";", error_bad_lines=True)


# Paramétrage des tests

@pytest.fixture
def regex_url():
    return """(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s<>"']{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s<>"']{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s<>"']{2,}|www\.[a-zA-Z0-9]+\.[^\s<>"']{2,})"""
@pytest.fixture
def noms(): 
    return df["nom_fichier"]
@pytest.fixture
def top():
    return df["top_trois_mots"]
@pytest.fixture
def http():
    return df["resultat_test_URL"]
@pytest.fixture
def date():
    return df["date_test_URL"]
@pytest.fixture
def wb():
    return df["internet_archive_status"]
@pytest.fixture
def wb_dispo():
    return df["internet_archive_dispo"]
@pytest.fixture
def wb_url():
    return df["internet_archive_url"]
@pytest.fixture
def wb_time():
    return df["internet_archive_timestamp"]
    
# Lancement des tests. Chaque fonction teste une cellule prise au hasard dans une colonne du CSV. Chaque test est répété plusieurs
# fois.
def test_noms(noms):
    """ Test de la bonne syntaxe des noms de fichier """
    rand = random.randint(1, len(noms)-1)
    cible = str(noms[rand])
    assert re.search('ID[0-9]+\.eml', cible) is not None
    
def test_top(top):
    """ Test de la bonne syntaxe des 3 mots-clefs """
    rand = random.randint(1, len(top)-1)
    cible = top[rand]
    if cible is not None:
        cible = str(cible)
    assert re.search('[a-zA-ZÀ-ÿ]+,[a-zA-ZÀ-ÿ]+,[a-zA-ZÀ-ÿ]+', cible) is not None

def test_htttp(http):
    """ Test de la validité des codes HTTP renvoyés """
    rand = random.randint(1, len(http)-1)
    cible = http[rand]
    try :
        liste_codes = cible.split(",")
        for code in liste_codes:
            assert code.isnumeric() == True
    except AttributeError: # Si il n'y a eu aucune URL repérée dans le mail
        pass
    
def test_date(date):
    """ Test de la validité des dates des tests des URL """
    rand = random.randint(1, len(date)-1)
    cible = date[rand]
    try :
        liste_dates = cible.split(",")
        for date in liste_dates:
            assert date.isinstance(datetime)
    except AttributeError: # Si il n'y a eu aucune URL repérée dans le mail
        pass 
    
def test_wb(wb):
    """ Test de la validité des codes renvoyés par la Wayback Machine"""
    rand = random.randint(1, len(wb)-1)
    cible = wb[rand]
    try :
        liste_codes = cible.split(",")
        for code in liste_codes:
            if code != "None":
                assert code.isinstance(int) 
    except AttributeError: # Si il n'y a eu aucune URL repérée dans le mail
        pass

def test_wb_dispo(wb_dispo):
    """ Test de la validité des codes renvoyés par la Wayback Machine"""
    rand = random.randint(1, len(wb_dispo)-1)
    cible = wb_dispo[rand]
    try :
        liste_codes = cible.split(",")
        for code in liste_codes:
            if code != "None":
                assert code.isinstance(bool)
    except AttributeError: # Si il n'y a eu aucune URL repérée dans le mail
        pass

def test_wb_url(wb_url):
    """ Test de la validité des URL renvoyées par la Wayback Machine"""
    rand = random.randint(1, len(wb_url)-1)
    cible = wb_url[rand]
    regex = """(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s<>"']{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s<>"']{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s<>"']{2,}|www\.[a-zA-Z0-9]+\.[^\s<>"']{2,})"""
    try :
        liste = cible.split(",")
        for element in liste:
            if str(element) != "None":
                assert re.search(regex, str(element)) is not None
    except AttributeError: # Si il n'y a eu aucune URL repérée dans le mail
        pass

def test_wb_time(wb_time):
    """ Test de la validité des dates des tests des URL """
    rand = random.randint(1, len(wb_time)-1)
    cible = wb_time[rand]
    try :
        liste_dates = cible.split(",")
        for date in liste_dates:
            if date != "None":
                assert date.isinstance(datetime) 
    except AttributeError: # Si il n'y a eu aucune URL repérée dans le mail
        pass 