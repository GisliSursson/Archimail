import emails, random, os
from os.path import dirname, abspath
import subprocess
from odf.opendocument import OpenDocumentText
from odf.text import P
from stat_eml import traiter_mails

chemin_actuel = dirname(abspath(__file__))
rand = random.randint(0, 10)
nb_mails = random.randint(100, 200)
rand_2 = random.randint(0, 10)
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

try:
    directory = "resultat"
    dir_par_dummy = "dummy"
    dir_dummy_mails = "dummy_mails"
    parent_dir = "/home/User/Documents"
    path = os.path.join(chemin_actuel, directory)
    os.mkdir(path)
    path_2 = os.path.join(chemin_actuel, dir_par_dummy, dir_dummy_mails)
    os.mkdir(path_2)
    print("creations")
except:
    pass

def create_dummy_pdf(nombre):
    for x in range(1,nombre):
        bashCommand = "dummypdf -f ./dummy/test_{a}.pdf -n {b}".format(a=str(x), b=str(random.randint(1, 20)))
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()

lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin nibh eros, finibus nec nisl id, rhoncus fringilla ligula. Aenean vel eleifend urna. Quisque a est vestibulum, semper elit ac, fermentum nisl. Donec mattis purus id turpis porttitor, non fringilla dolor dictum. Morbi aliquet, felis vulputate hendrerit fermentum, odio nulla dignissim ex, non euismod elit urna eu augue. Etiam vel quam dui. Sed dictum fermentum eros, et bibendum tortor cursus nec. Maecenas et nunc mollis urna cursus cursus. Donec a ullamcorper ipsum."
      
def create_dummy_odt(lorem, iter, rand):
    for x in range(1, iter):
        textdoc = OpenDocumentText()
        texte = lorem * rand
        p = P(text=texte)
        textdoc.text.addElement(p)
        textdoc.save("./dummy/test_{a}".format(a=str(x)), True)

def create_dummy_mails(lorem, iter, rand):
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
        nb = random.randint(0, 1)
        nb_lien = random.randint(0, 5)
        pos = random.randint(0, len(lorem)-1)
        lorem = (lorem[:pos] + ' ' + url_OK + " " + lorem[pos:] + lorem[:pos] + ' ' + url_NOK + " " + lorem[pos:])*nb_lien
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
        m = message.as_message()
        s = m.as_string()
        with open("./dummy/dummy_mails/test_{a}.eml".format(a=str(x)), "w") as mail:
            mail.write(s)
        

create_dummy_pdf(rand)
create_dummy_odt(lorem, rand, rand_2)


create_dummy_mails(lorem, nb_mails, rand_2)
    
output = os.path.join(chemin_actuel,"resultat","resultat_test.csv")
print(output)
source = os.path.join(chemin_actuel,"dummy","dummy_mails")
print(source)

traiter_mails(source, output)
