#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import xml.etree.ElementTree as ET
import copy
import os

""" negation_complet(tree)
    Cette fonction permet d'ajouter la ligne Négations à un arbre XML
    fourni en entrée

    Entrée:
        tree: Arbre XML enrichi (ElementTree)
    Sorties:
        tree: Arbre XML avec la ligne Négations ajoutée
"""

def negation_complet(tree):
    #On définit une liste des exceptions
    exception1="(le|la|les|l'|un|une|des|d'|du|de la|des|de l'|au|aux|du|\
    ce|cet|cette|ces|mon|ton|son|ma|ta|sa|mes|tes|ses|notre|votre|leur|\
    nos vos|leurs|quel|quelle|quels|quelles|un|deux|trois|quatre|cinq|\
    six|sept|huit|neuf|onze|douze|treize|quatorze|quinze|seize|vingt|\
    trente|quarante|cinquante|soixante|cent|mille|premier|deuxième|\
    second|troisième|quatrième|cinquième|sixième|septième|huitième|\
    neuvième|dixième|onzième|douzième|treizième|quatorzième|quinzième|\
    seizième|vingtième|trentième|quarantième|cinquantième|soixantième|\
    centième|millième|millionième|milliardième|énième|aucun|aucune|\
    aucuns|aucunes|maint|mainte|maints|maintes|quel que|quelle que|\
    quels que|quelles que|tel|telle|tels|telles|tout|toute|tous|toutes|\
    chaque|plusieurs|divers|autre|autres|mêmes|quelque|quelques|\
    quelconque|quelconques|certain|certaine|certains|certaines|divers|\
    diverse|divers|diverses|différent|différente|différents|différentes|nul|nulle|nuls|nulles|ou)"
    #On récupère la racine de l'arborescence XML
    root=tree.getroot()
    #On copie la ligne sur laquelle on va travailler
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1
    line=copy.deepcopy(root[position])
    #On insère la copie dans l'arbre
    root.insert(position+2,line)
    position+=2
    root[position].set("LINGUISTIC_TYPE_REF","Négation")
    #On change le nom de la ligne et de toutes les annotations
    for child in root[position]:
        for c in child:
            new_id=re.sub('_nettoye','',c.attrib.get("ANNOTATION_ID"))
            c.set("ANNOTATION_ID",new_id+"_Négation")
    new_id=re.sub('_nettoye','',root[position].attrib.get("TIER_ID"))
    root[position].set("TIER_ID",new_id+"_Négation")
    #On parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                newtext=""
                i=0
                #On recherche les mots de négation
                while re.search("\\b(pas|jamais|personne|rien|aucune?s?)(\s|\.|\?)",ele.text):
                    ele.text=re.sub("\\b(pas|jamais|personne|rien|aucune?s?)(\s|\.|\?)","\g<1>{"+str(i)+"}\g<2>",ele.text,count=1)
                    i+=1
                #Pour chaque mot de négation trouvé, on vérife qu'il n'est pas une exception
                for j in range(0,i):
                    #On definit une variable qui indique si le contexte est valide ou non
                    contexte_correct=True
                    #Exception 1:Le mot de négation n'est pas un mot de négation selon son contexte
                    if re.search("\\b"+exception1+"\s(pas|jamais|personne|rien|ooo pas|ooo jamais|ooo personne|ooo rien)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 2:Traitement de "Pour rien", "Sans rien" et "Même rien"
                    if re.search("\\b(pour|même|sans)\s(ooo rien|rien)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 3:On retire les cas ou "pas" n'est pas un mot de négation
                    if re.search("\\b(faux|grand|petit|premier|dernier|au|cent|mauvais|non|et|mais|nan|oui)\s(pas|ooo pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 4:Idem pour "personne"
                    if re.search("(pour|même|grande|petite|permière|dernière|mauvaise|autre|par|sans)\s(personne|ooo personne)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 5:Iden pour "jamais"
                    if re.search("(comme|du|même|plus que|sans|à tout|à|si|au grand)\s(jamais|ooo jamais)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 6:On traite l'expression "dans pas longtemps"
                    if re.search("dans pas\{"+str(j)+"\} longtemps",ele.text):
                        contexte_correct=False
                    #Exception 7:On traite les expressions sans aucun(e)(s)
                    if re.search("(sans|sans ooo)\saucune?s?\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 8:On traite les cas où "pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo pas|pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo pas|pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 8.1:On traite les cas où "même pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo même pas|même ooo pas|même pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo même pas|même ooo pas|même pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
					#Exception 8.2:On traite les cas où "toujours pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo toujours pas|toujours ooo pas|toujours pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo toujours pas|toujours ooo pas|toujours pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
					#Exception 8.3:On traite les cas où "donc pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo donc pas|donc ooo pas|donc pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo donc pas|donc ooo pas|donc pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
					#Exception 8.4:On traite les cas où "sinon pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo sinon pas|sinon ooo pas|sinon pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo sinon pas|sinon ooo pas|sinon pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 9:On traite les cas où le mot négatif est isolé ou bien est seulement avec des onomatopées et/ou des amorces
                    if re.search("^\s?(ooo\s|aaa\s)?(pas|jamais|personne|rien|aucune?s?)\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text) or re.search("[.?]\s?(ooo\s|aaa\s)?(pas|jamais|personne|rien|aucune?s?)\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text):
                        contexte_correct=False
                    #Exception 10:On traite les expressions en "plus" si elles sont isolées ou seulement avec des onomatopées/amorces
                    if re.search("^\s?(ooo\s|aaa\s)?plus\s(personne|jamais|aucune?s?)\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text) or re.search("[.?]\s?(ooo\s|aaa\s)?plus\s(personne|jamais|aucune?s?)\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text):
                        contexte_correct=False
                    #Exception 11:On traite "Pas plus", "Pas beaucoup" et "jamais plus" si elles sont isolées ou seulement avec des onomatopées/amorces
                    if re.search("^\s?(ooo\s|aaa\s)?(pas|jamais)\s(plus|beaucoup)\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text) or re.search("[.?]\s?(ooo\s|aaa\s)?(pas|jamais)\s(plus|beaucoup)\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text):
                        contexte_correct=False
                    #Exception 12:On traite l'expression "jamais de la vie"
                    if re.search("jamais\{"+str(j)+"\}\sde\sla\svie",ele.text):
                        contexte_correct=False
                    #Exception 13:On traite les cas où "On" est suivi d'un voyelle
                    if re.search("\\bon\\b\s(?:n')?(?:([aàâeéèêiîoôuùûyh][a-z-âàéàçèïêùûîôA-Z\d]*)['\s])(?:\w+\s){0,2}(pas|jamais|personne|rien|aucune?s?)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 14:On traite les mots2 de négation dédoublés
                    #Exception 14.1: "jamais" dédoublé
                    if re.search("jamais\{"+str(j)+"\}\sjamais\{"+str(j+1)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 14.2: "personne" dédoublé
                    if re.search("personne\{"+str(j)+"\}\spersonne\{"+str(j+1)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 14.3: "rien" dédoublé
                    if re.search("rien\{"+str(j)+"\}\srien\{"+str(j+1)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 14.4: "aucun(es)" dédoublé
                    if re.search("aucune?s?\{"+str(j)+"\}\saucune?s?\{"+str(j+1)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 14.5: "pas" dédoublé
                    if re.search("pas\{"+str(j)+"\}\spas\{"+str(j+1)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 15: On traite les expressions "n'importe" et "n'en déplaise à"
                    if re.search("(n'importe|n'en déplaise à)\s(pas|jamais|personne|rien|aucune?s?)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 15bis: On traite l'expression "n'est-ce-pas"
                    if re.search("n'est-ce-pas\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Si on a un contexte correct, on cherche si le ne est réalisé ou pas et on ajoute le codage correspondant
                    if contexte_correct:
                        if re.search("\\b(ne|n’|n'|n'|n)\\b\s?(?:([a-z-âàéàçèïêùûîôA-Z\d]+)?(?:\s|')?){0,4}\\b(pas|jamais|personne|rien|aucune?s?)\\b\{"+str(j)+"\}",ele.text)\
                        or re.search("\\b(pas|jamais|personne|rien|aucune?s?)\\b\{"+str(j)+"\}\s\\b(ne|n’|n'|n'|n)\\b",ele.text):
                            ele.text=re.sub("(pas|jamais|personne|rien|aucune?s?)\{"+str(j)+"\}","\g<1>[NN1]",ele.text)
                        else:
                            ele.text=re.sub("(pas|jamais|personne|rien|aucune?s?)\{"+str(j)+"\}","\g<1>[NN0]",ele.text)
                    else:
                        ele.text=re.sub("(pas|jamais|personne|rien|aucune?s?)\{"+str(j)+"\}","\g<1>",ele.text)
    return tree

""" negation_pas(tree)
    Cette fonction permet d'ajouter la ligne Négations_pas à un arbre XML
    fourni en entrée

    Entrée:
        tree: Arbre XML enrichi (ElementTree)
    Sorties:
        tree: Arbre XML avec la ligne Négations_pas ajoutée
"""

#Harmoniser avec complet
def negation_pas(tree):
    #On définit une liste des exceptions
    exception1="(le|la|les|l'|un|une|des|d'|du|de la|des|de l'|au|aux|du|\
    ce|cet|cette|ces|mon|ton|son|ma|ta|sa|mes|tes|ses|notre|votre|leur|\
    nos vos|leurs|quel|quelle|quels|quelles|un|deux|trois|quatre|cinq|\
    six|sept|huit|neuf|onze|douze|treize|quatorze|quinze|seize|vingt|\
    trente|quarante|cinquante|soixante|cent|mille|premier|deuxième|\
    second|troisième|quatrième|cinquième|sixième|septième|huitième|\
    neuvième|dixième|onzième|douzième|treizième|quatorzième|quinzième|\
    seizième|vingtième|trentième|quarantième|cinquantième|soixantième|\
    centième|millième|millionième|milliardième|énième|aucun|aucune|\
    aucuns|aucunes|maint|mainte|maints|maintes|quel que|quelle que|\
    quels que|quelles que|tel|telle|tels|telles|tout|toute|tous|toutes|\
    chaque|plusieurs|divers|autre|autres|mêmes|quelque|quelques|\
    quelconque|quelconques|certain|certaine|certains|certaines|divers|\
    diverse|divers|diverses|différent|différente|différents|différentes|nul|nulle|nuls|nulles|ou)"
    #On récupère la racine de l'arborescence XML
    root=tree.getroot()
    #On copie la ligne sur laquelle on va travailler
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1
    line=copy.deepcopy(root[position])
    #On insère la copie dans l'arbre
    root.insert(position+2,line)
    position+=2
    root[position].set("LINGUISTIC_TYPE_REF","Négation")
    #On change le nom de la ligne et de toutes les annotations
    for child in root[position]:
        for c in child:
            new_id=re.sub('_nettoye','',c.attrib.get("ANNOTATION_ID"))
            c.set("ANNOTATION_ID",new_id+"_NégationPAS")
    new_id=re.sub('_nettoye','',root[position].attrib.get("TIER_ID"))
    root[position].set("TIER_ID",new_id+"_NégationPAS")
    #On parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                newtext=""
                i=0
                #On recherche les mots de négation
                while re.search("\\bpas(\s|\.|\?)",ele.text):
                    ele.text=re.sub("\\b(pas)(\s|\.|\?)","\g<1>{"+str(i)+"}\g<2>",ele.text,count=1)
                    i+=1
                #Pour chaque mot de négation trouvé, on vérife qu'il n'est pas une exception
                for j in range(0,i):
                    #On definit une variable qui indique si le contexte est valide ou non
                    contexte_correct=True
                    #Exception 1:Le mot de négation n'est pas un mot de négation selon son contexte
                    if re.search("\\b"+exception1+"\s(pas|ooo pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 2:On retire les cas ou "pas" n'est pas un mot de négation
                    if re.search("\\b(faux|grand|petit|premier|dernier|au|cent|mauvais|non|et|mais|nan|oui)\s(pas|ooo pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 3:On traite l'expression "dans pas longtemps"
                    if re.search("dans pas\{"+str(j)+"\} longtemps",ele.text):
                        contexte_correct=False
                    #Exception 4:On traite les cas où "pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo pas|pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo pas|pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
					#Exception 4.1:On traite les cas où "même pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo même pas|même pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo même pas|même pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
					#Exception 4.2:On traite les cas où "toujours pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo toujours pas|toujours ooo pas|toujours pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo toujours pas|toujours ooo pas|toujours pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
					#Exception 4.3:On traite les cas où "donc pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo donc pas|donc ooo pas|donc pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo donc pas|donc ooo pas|donc pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
					#Exception 4.4:On traite les cas où "sinon pas" est en début d'énoncé ou de ligne
                    if re.search("^\s?(ooo sinon pas|sinon ooo pas|sinon pas)\{"+str(j)+"\}",ele.text) or re.search("[.?]\s?(ooo sinon pas|sinon ooo pas|sinon pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 5:On traite les cas où le mot négatif est isolé ou bien est seulement avec des onomatopées et/ou des amorces
                    if re.search("^\s?(ooo\s|aaa\s)?pas\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text) or re.search("[.?]\s?(ooo\s|aaa\s)?pas\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text):
                        contexte_correct=False
                    #Exception 6:On traite "Pas plus" et "Pas beaucoup" si elles sont isolées ou seulement avec des onomatopées/amorces
                    if re.search("^\s?(ooo\s|aaa\s)?pas\splus\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text) or re.search("[.?]\s?(ooo\s|aaa\s)?pas\splus\{"+str(j)+"\}(\sooo|\saaa)?\s?(?:\.|\?)",ele.text):
                        contexte_correct=False
                    #Exception 7:On traite les cas où "On" est suivi d'un voyelle
                    if re.search("\\bon\\b\s(?:n')?(?:([aàâeéèêiîoôuùûyh][a-z-âàéàçèïêùûîôA-Z\d]*)['\s])(?:\w+\s){0,2}(pas)\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 8:On traite les mots2 de négation dédoublés
                    if re.search("pas\{"+str(j)+"\}\spas\{"+str(j+1)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 9: On traite les expressions "n'importe" et "n'en déplaise à"
                    if re.search("(n'importe|n'en déplaise à)\spas\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Exception 9bis: On traite l'expression "n'est-ce-pas"
                    if re.search("n'est-ce-pas\{"+str(j)+"\}",ele.text):
                        contexte_correct=False
                    #Si on a un contexte correct, on cherche si le ne est réalisé ou pas
                    if contexte_correct:
                        if re.search("\\b(ne|n’|n'|n'|n)\\b\s?(?:([a-z-âàéàçèïêùûîôA-Z\d]+)?(?:\s|')?){0,4}\\b(pas|jamais|personne|rien|aucune?s?)\\b\{"+str(j)+"\}",ele.text):
                            ele.text=re.sub("(pas)\{"+str(j)+"\}","\g<1>[NN1]",ele.text)
                        else:
                            ele.text=re.sub("(pas)\{"+str(j)+"\}","\g<1>[NN0]",ele.text)
                    else:
                        ele.text=re.sub("(pas)\{"+str(j)+"\}","\g<1>",ele.text)
    return tree

""" negations(tree,i)
    Cette fonction permet d'appeller un ou les deux scripts de négation

    Entrée:
        tree: Arbre XML enrichi (ElementTree)
        i: Indicateur qui indique quel(s) scripts appliquer (Integer)
            i=0 N'applique que le script en "pas"
            i=1 Applique le script complet
            i=2 Applique les deux scripts
    Sorties:
        tree: Arbre XML avec la ou les lignes de négation ajoutée (ElementTree)
"""
def negations(tree,i):
    #On choisit quel traitement appliquer en fonction de l'indicateur de mode
    #et on appelle le/les script(s) correspondant
    if i==0:
        tree=negation_pas(tree)
    elif i==1:
        tree=negation_complet(tree)
    elif i==2:
        tree=negation_pas(tree)
        tree=negation_complet(tree)
    position=0
    root=tree.getroot()
    #On crée un nouveau type linguistique en en copiant un autre
    for child in root:
        if child.tag=="LINGUISTIC_TYPE" and child.attrib.get("LINGUISTIC_TYPE_ID")=="Nettoyage":
            break
        else:
            position+=1
    newline=copy.deepcopy(root[position])
    #On change l'identifiant de la copie
    newline.set("LINGUISTIC_TYPE_ID","Négation")
    #On ajoute la copie dans l'arborescence XML
    root.insert(position+2,newline)
    return tree

""" lancement_negations(filename,negs)
    Cette fonction permet d'extraire l'arbre XML d'un fichier _VB.eaf
    et de lancer le traitement des négations
    Entrée:
        filename: Chemin d'accès au fichier (String)
        negs: Indicateur qui indique quel(s) scripts appliquer (Integer)
            negs=0 N'applique que le script en "pas"
            negs=1 Applique le script complet
            negs=2 Applique les deux scripts
    Sorties:
        Création d'un fichier _VC.eaf avec la ou les lignes de négation
        ajoutées
"""

def lancement_negations(filename,negs):
    #On vérifie si le fichier est bien un fichier _VB.eaf
    if re.search("_VB",filename):
        #On parcourt le fichier
        originaltree = ET.parse(filename,ET.XMLParser(encoding='utf-8'))
        #On copie l'arbre original afin de ne pas modifier le fichier d'origine
        tree=copy.deepcopy(originaltree)
        #On appelle la fonction qui va appliquer le traitement approprié
        tree=negations(tree,negs)
        #Si nécessaire, on crée les dossiers de sortie
        if not os.path.exists('./Sortie'):
            os.mkdir('./Sortie')
        if not os.path.exists('./Sortie/Negations'):
            os.mkdir('./Sortie/Negations')
        #On crée le nom du nouveau fichier
        new_filename=re.search('([^\/.]*?.eaf)',filename)
        new_filename=new_filename.group(1)
        new_filename=re.sub('_VB','_VC',new_filename)
        new_filename="Sortie/Negations/"+new_filename
        #On enregistre le nouveau fichier
        tree.write(new_filename,encoding="utf-8")
