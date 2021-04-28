import emails, random, os, re
import shutil
from os.path import dirname, abspath
import subprocess
from odf.opendocument import OpenDocumentText
from odf.text import P
from stat_eml import traiter_mails

chemin_actuel = dirname(abspath(__file__))
rand = random.randint(1, 10)
nb_mails = random.randint(100, 200)
rand_2 = random.randint(1, 10)
url_OK = "https://guthib.com/"
url_NOK = "https://guthib.com/nok"
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

lorem = """Les érudits ont amèrement reproché à Guillaume, moine de l’abbaye
de Jumiège, d’avoir reproduit dans les premiers livres de son
Histoire des Normands, la plupart des fables dont son prédécesseur
Dudon, doyen de Saint-Quentin, avait déjà rempli la sienne. Si
Guillaume n’eût ainsi fait, cette portion de son ouvrage
n’existerait pas, car il n’aurait rien eu à y mettre; il a
recueilli les traditions de son temps sur l’origine, les exploits,
les aventures des anciens Normands et de leurs chefs; aucun peuple
n’en sait davantage, et n’a des historiens plus exacts sur le
premier âge de sa vie. A voir la colère de dom Rivet et de ses
doctes confrères, il semblerait que Dudon et Guillaume aient eu le
choix de nous raconter des miracles ou des faits, une série de
victoires romanesques ou une suite d’événemens réguliers, et que
leur préférence pour la fable soit une insulte à notre raison,
comme si elle était obligée d’y [p. vj] croire. Il y a à quereller
de la sorte les vieux chroniqueurs une ridicule pédanterie; ils
ont fait ce qu’ils pouvaient faire; ils nous ont transmis ce qu’on
disait, ce qu’on croyait autour d’eux: vaudrait-il mieux qu’ils
n’eussent point écrit, qu’aucun souvenir des temps fabuleux ou
héroïques de la vie des nations ne fût parvenu jusqu’à nous, et
que l’histoire n’eût commencé qu’au moment où la société aurait
possédé des érudits capables de la soumettre à leur critique pour
en assurer l’exactitude? A mon avis, il y a souvent plus de
vérités historiques à recueillir dans ces récits où se déploie
l’imagination populaire que dans beaucoup de savantes
dissertations.
"""



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
    print("Fait dossiers")

folder()

def create_dummy_pdf(nombre):
    for x in range(1,nombre):
        bashCommand = "dummypdf -f ./dummy/test_{a}.pdf -n {b}".format(a=str(x), b=str(random.randint(1, 20)))
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
    print("Fait PDF")
    
def create_dummy_odt(lorem, iter, rand):
    for x in range(1, iter):
        textdoc = OpenDocumentText()
        texte = lorem * rand
        p = P(text=texte)
        textdoc.text.addElement(p)
        textdoc.save("./dummy/test_{a}".format(a=str(x)), True)
    print("Fait ODT")

def create_dummy_mails(lorem, iter, rand):
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
        lorem = orig
        lorem_inser = list(filter(None, re.split("\s", lorem)))
        nb = random.randint(0, 1)
        nb_lien = random.randint(0, 1)
        nb_noms = random.randint(0, 1)
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
        if type(x//2) is not float:
            message = emails.html(html="<p>{a}</p>".format(a=(lorem*rand)),
                                subject=lorem[:20] + "_" + str(iter),
                                mail_from=('Some Name', adress[random.randint(0, len(adress)-1)]))
            if nb == 0:
                random_odt = random.choice(liste_odt)
                message.attach(data=open(random_odt, 'rb'), filename=random_odt)
            else:
                random_pdf = random.choice(liste_pdf)
                message.attach(data=open(random_pdf, 'rb'), filename=random_pdf)
        else:
            message = emails.html(html="<p>{a}</p>".format(a=(lorem*rand)),
                                subject=lorem[:20] + "_" + str(iter),
                                mail_from=('Some Name', adress[random.randint(0, len(adress)-1)]))
        s = message.as_string()
        with open("./dummy/dummy_mails/test_{a}.eml".format(a=str(x)), "w") as mail:
            mail.write(s)
    print("Fait mails")

create_dummy_pdf(rand)
create_dummy_odt(lorem, rand, rand_2)
create_dummy_mails(lorem, nb_mails, rand_2)
    
output = os.path.join(chemin_actuel,"resultat","resultat_test.csv")
source = os.path.join(chemin_actuel,"dummy","dummy_mails")

traiter_mails(source, output)
