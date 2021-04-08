from typing import Dict
import pandas as pd

df = pd.read_csv('metadata.csv', sep=';', error_bad_lines=False)

def supprimer_ponctuation(texte: str) -> str: 
    """ Supprimer les caractères de ponctuation d'un texte
    
    :param texte: Texte à nettoyer
    :type texte: str
    :returns: Texte sans ponctuation
    :rtype: str
    """
    ponctuation = '!@#$%^&*()_-+={}[]:;"\'|<>,.?/~`'
    for marqueur in ponctuation:
        texte = str(texte).replace(marqueur, "")
    return texte

def supprimer_separateurs(texte):
    """ Cette fonction remplace les apostrophes, les sauts de ligne et les traits d'unions par des espaces
    
    :param texte: Texte à nettoyer
    :type texte: str
    :returns: Texte simplifié
    :rtype: str
    """
    cible = '\'-\n'
    for i in cible:
        texte = str(texte).replace(i, " ")
    return texte

def statistiques_mots(texte: str) -> Dict[str, int]:
    """ Création d'un dictionnaire où les clefs sont les mots et les valeurs leurs occurences dans un texte
    
    :param texte_url: url vers son fichier
    :type mots: str
    :returns: Dictionnaire où les clefs sont les mots et les valeurs le nombre d'occurrences
    :rtype: dict
    """
    texte_liste = str(texte).split()
    dico_stat = {}
    for mot in texte_liste:
        if mot not in dico_stat:
            dico_stat[mot] = texte.count(mot)
    return dico_stat

# Définition de la colonne cible (où est le contenu textuel)
# print(df["Content.TextContent"])
# col_cible = df["Content.TextContent"]
# Création d'une nouvelle colonne vide où seront placés les mots clefs au fur et à mesure
df.insert(df.columns.get_loc("Content.TextContent") + 1, "Content.Keywords", None)

for index, cell in enumerate(df["Content.TextContent"]):
    contenu = supprimer_ponctuation(cell)
    contenu = supprimer_separateurs(contenu)
    dico_stat = statistiques_mots(contenu)
    dico_trie = sorted(dico_stat.keys(), reverse=True)[0:4]
    df["Content.Keywords"][index] = ','.join(dico_trie)
    print(df["Content.Keywords"][index])

df.to_csv('metadata_traite.csv', sep=';')

# TAF : supprimer mots grammaticaux, gérer les accents, vérifier doc sorted(dict)