#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import xml.etree.ElementTree as ET
import copy
import sys
import os

""" extract_brut(filenames,variable,newfile="extraction brute", liaison_type="LF1_LF3")
    Cette fonction permet, a partir d'un fichier _VC.eaf de créer un fichier .csv contenant une extraction brute des
    occurences de la variable donnée
    Entrées:
        filenames: Ensemble de chemin d'accès aux fichiers à traiter (Array)
        variable: Variable à traiter (String)
        newfile: Nom à donner au nouveau fichier (String)
    Sorties:
        Création d'un fichier .csv d'extraction brute
"""

def extract_brut(filenames,variable,newfile="extraction brute", liaison_type="LF1_LF3"):
    #On crée les dossiers de sortie si nécessaire
    if not os.path.exists('./Sortie'):
        os.mkdir('./Sortie')
    if not os.path.exists('./Sortie/Extraction_Brute'):
        os.mkdir('./Sortie/Extraction_Brute')
    #On ouvre le fichier .csv ou on va écrire
    fichier=open("Sortie/Extraction_Brute/"+newfile+"_"+variable+".csv",mode="w",encoding="UTF-8")
    #On crée la ligne de titre et on l'inscrit en tête du fichier .csv

    # Modification de l'en-tête du tableau
    # Si l'utilisateur choisit "Liaisons facultatives", deux colonnes supplémentaires sont ajoutées : "mot1" et "mot2"
    if variable == "lf":
        lignetitre = ["variable", "variante", "nom_fichier.eaf", "periodes_projet", "periodes_ecole",
                      "num_class", "id_dylnet", "transcription_tour_de_parole", "transcription_énoncé",
                      "mot1", "mot2", "activité", "interlocuteur", "situation"]
    else:
        lignetitre = ["variable", "variante", "nom_fichier.eaf", "periodes_projet", "periodes_ecole",
                      "num_class", "id_dylnet", "transcription_tour_de_parole", "transcription_énoncé",
                      "activité", "interlocuteur", "situation"]

    fichier.write(";".join(lignetitre)+"\n")
    #on analyse chacun des fichiers donnés en entrée
    for filename in filenames:
        log_file=open("log.log",mode="a")
        log_file.write(filename.split("/")[-1:][0]+" -"+variable+" -brute\n")
        log_file.close()
        #On récupère l'arbre XML de chaque fichier puis la racine de cet arbre
        tree=ET.parse("./uploads/"+filename,ET.XMLParser(encoding='utf-8'))
        root=tree.getroot()
        #On récupère les bornes temporelles de chacunes des annotations du fichier
        #et on les met de côté pour plus tard
        positiontime=0
        for child in root:
            if child.tag=="TIME_ORDER":
                break
            else:
                positiontime+=1
        timecode={}
        for child in root[positiontime]:

            time=child.attrib.get("TIME_VALUE")
            ID=child.attrib.get("TIME_SLOT_ID")
            if time in timecode.keys():
                timecode[time].append(ID)
            else:
                timecode[time]=[ID]
        #On crée une nouvelle ligne ou seront mises les données
        new_filename=re.search('([^\/.]*?.eaf)',filename)
        new_filename=new_filename.group(1)

        if variable == "lf":
            nouvelleligne = [variable, "", new_filename, "", "", "", "", "", "", "", "", "", "", ""]
        else:
            nouvelleligne = [variable, "", new_filename, "", "", "", "", "", "", "", ""]

        #On récupère la date et on l'analyse pour trouver la periode
        date=new_filename[3:11]
        date=int(date)
        if date>=20170901 and date<=20171231:
            nouvelleligne[3]="P0"
            nouvelleligne[4]="rentree-A1"
        elif date>=20180401 and date<=20180630:
            nouvelleligne[3]="P1"
            nouvelleligne[4]="fin-A1"
        elif date>=20180901 and date<=20181231:
            nouvelleligne[3]="P1"
            nouvelleligne[4]="rentree-A2"
        elif date>=20190401 and date<=20190630:
            nouvelleligne[3]="P2"
            nouvelleligne[4]="fin-A2"
        elif date>=20190901 and date<=20190930:
            nouvelleligne[3]="P2"
            nouvelleligne[4]="rentree-A3"
        elif date>=20191001 and date<=20200301:
            nouvelleligne[3]="P3"
            nouvelleligne[4]="fin-A3"
        #On récupère l'identifiant de la classe et de la personne
        nouvelleligne[5]="CL-"+new_filename[0:2]
        nouvelleligne[6]="ID-"+new_filename[19:23]
        #en fonction de la variable donnée, on appelle la fonction correspondante
        if variable=="enonces":
            extraction_enonces(root,fichier,nouvelleligne,timecode)
        elif variable=="tu":
            extraction_tu(root,fichier,nouvelleligne,timecode)
        elif variable=="I-dans-il":
            extraction_I_dans_il(root,fichier,nouvelleligne,timecode)
        elif variable=="il-complet":
            extraction_il_complet(root,fichier,nouvelleligne,timecode)
        elif variable=="schwa":
            extraction_schwa(root,fichier,nouvelleligne,timecode)
        elif variable=="rl":
            extraction_rl(root,fichier,nouvelleligne,timecode)
        elif variable=="@o":
            extraction_onomatopee(root,fichier,nouvelleligne,timecode)
        elif variable=="@s":
            extraction_mots_etrangers(root,fichier,nouvelleligne,timecode)
        elif variable=="@c":
            extraction_mots_enfantins(root,fichier,nouvelleligne,timecode)
        elif variable=="catégories-grammaticales":
            extraction_cat_gram(root,fichier,nouvelleligne,timecode)
        elif variable=="liaison-fausse":
            extraction_liaisons_fausses(root,fichier,nouvelleligne,timecode)
        elif variable=="oui-ouais":
            extraction_oui_ouais(root,fichier,nouvelleligne,timecode)
        elif variable=="non-nan":
            extraction_non_nan(root,fichier,nouvelleligne,timecode)
        elif variable=="on-nous":
            extraction_on_nous(root,fichier,nouvelleligne,timecode)
        elif variable=="neg":
            extraction_negation(root,fichier,nouvelleligne,timecode)
        elif variable=="neg-pas":
            extraction_negation_pas(root,fichier,nouvelleligne,timecode)
        elif variable=="lf":
            extraction_liaisons_facultatives(root, fichier, nouvelleligne, timecode, liaison_type)




    #on ferme le fichier .csv
    fichier.close()

""" trouver_positions(root)
    Cette fonction permet de récupèrer la position des trois lignes nécessaires
    au traitement: la ligne 'Activité', la ligne 'Interlocuteur' et
    la ligne 'Situation Langagière'
    Entrées:
        root: racine d'un arbre XML (ElementTree)
    Sorties:
        positionactivite: Position de la ligne 'Activité' (Integer)
        positioninterlocuteur: Position de la ligne 'Interlocuteur' (Integer)
        positionsituation: Position de la ligne 'Situation Langagière' (Integer)
"""


def trouver_positions(root):
    #On cherche la position de chacune des trois lignes
    positionactivite=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("TIER_ID")=="Activité en cours":
            break
        else:
            positionactivite+=1

    positioninterlocuteur=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("TIER_ID")=="Interlocuteur":
            break
        else:
            positioninterlocuteur+=1

    positionsituation=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("TIER_ID")=="Situation langagière":
            break
        else:
            positionsituation+=1
    return(positionactivite,positioninterlocuteur,positionsituation)

""" trouver_contexte(root,timecodes,element,positionactivite,positioninterlocuteur,positionsituation)
    Cette fonction permet de récupèrer le contexte d'un tour de parole,
    c'est-à-dire le contenu des lignes 'Activité','Interlocuteur' et 'Situation Langagière'
    qui lui correspondent
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        element: l'element qu'on est en train d'etudier (ElementTree)
        positionactivite: Position de la ligne 'Activité' (Integer)
        positioninterlocuteur: Position de la ligne 'Interlocuteur' (Integer)
        positionsituation: Position de la ligne 'Situation Langagière' (Integer)
    Sorties:
        activite : Le contenu de la borne sur la ligne 'Activité' correspondant
        à l'élément etudié (String)
        interlocuteur : Le contenu de la borne sur la ligne 'Activité' correspondant
        à l'élément etudié (String)
        situation : Le contenu de la borne sur la ligne 'Activité' correspondant
        à l'élément etudié (String)
"""


def trouver_contexte(root,timecodes,element,positionactivite,positioninterlocuteur,positionsituation):
    #On récupère les bornes temporelles de l'element actuellement étudié
    limits=[element.attrib.get("TIME_SLOT_REF1"),element.attrib.get("TIME_SLOT_REF2")]
    #On recherche ces bornes temporelles dans la liste des bornes temporelles
    for time in timecodes.keys():
        if limits[0] in timecodes[time]:
            limits[0]=timecodes[time]
        if limits[1] in timecodes[time]:
            limits[1]=timecodes[time]
    #On récupère l'activité en cours
    activite="Indéterminée"
    for child_activite in root[positionactivite]:
        for a in child_activite:
            for ele_a in a:
                if a.attrib.get("TIME_SLOT_REF1") in limits[0] and a.attrib.get("TIME_SLOT_REF2") in limits[1]:
                    activite=ele_a.text
                    #Si la ligne Activité est vide, on donne "Indéterminée" comme valeur par défaut
                    if activite==None:
                        activite="Indéterminée"
    #On traite certaines erreurs qui apparaîssent parfois dans cette ligne
    if activite=="Récréation Récréation":
        activite="Récréation"
    if activite=="En classe En classe":
        activite="En classe"
    if activite[-1]==" ":
        activite=activite[:-1]
    if activite[0]==" ":
        activite=activite[1:]
    #on récupère l'interlocuteur
    interlocuteur="Indéterminé"
    for child_interlocuteur in root[positioninterlocuteur]:
        for i in child_interlocuteur:
            for ele_i in i:
                if i.attrib.get("TIME_SLOT_REF1") in limits[0] and i.attrib.get("TIME_SLOT_REF2") in limits[1]:
                    interlocuteur=ele_i.text
    #Si la ligne Interlocuteur est vide, on donne "Indéterminée" comme valeur par défaut
    if interlocuteur==None:
        interlocuteur="Indéterminé"
    #On corrige certaines erreurs qui apparaîssent parfois dans cette ligne
    if interlocuteur=="Adulte autre":
        interlocuteur="Adulte"
    if interlocuteur=="ATSEM classe":
        interlocuteur="Atsem classe"
    if interlocuteur=="un ou plusieurs enfant(s) un ou plusieurs enfant(s)":
        interlocuteur="un ou plusieurs enfant(s)"
    if interlocuteur=="un ou plusieurs enfant(s) Indéterminé":
        interlocuteur="Indéterminé"
    if interlocuteur=="Auto Auto":
        interlocuteur="Auto"
    if interlocuteur[-1]==" ":
        interlocuteur=interlocuteur[:-1]
    if interlocuteur[0]==" ":
        interlocuteur=interlocuteur[1:]
    #Si elle est présente, on récupère la situation langagière
    situation="Pas de situation langagière"
    if len(limits[0])>3:
        for child_situation in root[positionsituation]:
            for s in child_situation:
                for ele_s in s:
                    if s.attrib.get("TIME_SLOT_REF1") in limits[0] and s.attrib.get("TIME_SLOT_REF2") in limits[1]:
                        situation=ele_s.text
                        if situation==None:
                            situation="Pas de situation langagière"
    #On corrige certaines erreurs qui apparaîssent parfois dans cette ligne
    if situation[-1]==" ":
        situation=situation[:-1]
    if situation=="Récitation Récitation":
        situation="Récitation"
    return activite,interlocuteur,situation

""" extraction_enonces(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait tous les énoncés de chaque tour de parole et indique
    si ce sont des énoncés déclaratifs ou interrogatifs
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""
def extraction_enonces(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    if not re.match("^(\s?xxx[\s.?])+$",enonce):
                    #on parcourt les énoncés et on regarde quel symbole les termine
                        nouvelleligne=lignebase
                        #on remplit la nouvelle ligne avec les données trouvées
                        if re.search("\.",enonce):
                            nouvelleligne[1]="enonces-point"
                        elif re.search("\?",enonce):
                            nouvelleligne[1]="enonces-interrog"
                        nouvelleligne[7]=tourdeparole
                        nouvelleligne[8]=enonce
                        activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                        nouvelleligne[9]=activite
                        nouvelleligne[10]=interlocuteur
                        nouvelleligne[11]=situation
                        fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

""" extraction_tu(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait toutes les occurrences de "tu" dans les fichiers
    et indique si le u est réalisé ou non
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""
def extraction_tu(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    #on recherche les occurences de tu dans chaque énoncé
                    if re.search("\\b(t\(u\))|\\b(tu)\\b",enonce):
                        occurences=re.findall("\\b(t\(u\))|\\b(tu)\\b",enonce)
                        liste_occurences=[]
                        for occurence in occurences:
                            for instance in occurence:
                                if instance!="":
                                    liste_occurences.append(instance)
                        for occurence in liste_occurences:
                            nouvelleligne=lignebase
                            #on remplit la nouvelle ligne avec les données trouvées
                            if re.search("((\s|^)t\(u\)(\s|$))",occurence):
                                nouvelleligne[1]="t-u"
                            elif re.search("((\s|^)tu(\s|$))",occurence):
                                nouvelleligne[1]="tu"
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1


""" extraction_I_dans_il(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait toutes les occurences de "il/ils" dans les fichiers
    et indique si le mot entier est réalisé ou si seulement le i initial l'est
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""

def extraction_I_dans_il(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                # ~ enonces=re.split("\.|\?",tourdeparole)
                for enonce in enonces:
                    #on recherche les occurences de il dans chaque énoncé
                    if re.search("\\b(i\(l\)s?)|(?<!\()\\b(ils?)\\b",enonce):
                        occurences=re.findall("\\b(i\(l\)s?)|(?<!\()\\b(ils?)\\b",enonce)
                        liste_occurences=[]
                        for occurence in occurences:
                            for instance in occurence:
                                if instance!="":
                                    liste_occurences.append(instance)
                        for occurence in liste_occurences:
                            nouvelleligne=lignebase
                            #on remplit la nouvelle ligne avec les données trouvées
                            #On vérifie si chaque il est réalisé ou non
                            if re.search("i\(l\)s",occurence):
                                nouvelleligne[1]="i-ls"
                            elif re.search("ils",occurence):
                                nouvelleligne[1]="ils"
                            elif re.search("i\(l\)",occurence):
                                nouvelleligne[1]="i-l"
                            elif re.search("il",occurence):
                                nouvelleligne[1]="il"
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

""" extraction_il_complet(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait toutes les occurences de "il/ils" dans les fichiers
    et indique si le mot est réalisé ou non
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""

def extraction_il_complet(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                # ~ enonces=re.split("\.|\?",tourdeparole)
                for enonce in enonces:
                    #que les tu prévocaliques?
                    #on recherche les occurences de il dans chaque énoncé
                    if re.search("(\(ils?\))|\\b(ils?)\\b",enonce):
                        occurences=re.findall("(\(ils?\))|\\b(ils?)\\b",enonce)
                        liste_occurences=[]
                        for occurence in occurences:
                            for instance in occurence:
                                if instance!="":
                                    liste_occurences.append(instance)
                        for occurence in liste_occurences:
                            nouvelleligne=lignebase
                            #on remplit la nouvelle ligne avec les données trouvées
                            #On vérifie si chaque il est réalisé ou non
                            if re.search("\(ils\)",occurence):
                                nouvelleligne[1]="ils-suppr"
                            elif re.search("ils",occurence):
                                nouvelleligne[1]="ils-produit"
                            elif re.search("\(il\)",occurence):
                                nouvelleligne[1]="il-suppr"
                            elif re.search("il",occurence):
                                nouvelleligne[1]="il-produit"

                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

""" extraction_schwa(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait tous les contextes ou un e pourrait être remplacée par un schwa
    et indique si c'est le cas ou non
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""

def extraction_schwa(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                # ~ enonces=re.split("\.|\?",tourdeparole)
                for enonce in enonces:
                    #que les tu prévocaliques?
                    #on recherche les occurences des mots ou un schwa pourrait apparaître dans chaque énoncé
                    if re.search("\\b([j|c|d|l|m|n|s|t]\(e\))|\\b([j|c|d|l|m|n|s|t]e)\\b|\\b(que)\\b|\\b(qu\(e\))",enonce):
                        occurences=re.findall("\\b([j|c|d|l|m|n|s|t]\(e\))|\\b([j|c|d|l|m|n|s|t]e)\\b|\\b(que)\\b|\\b(qu\(e\))",enonce)
                        liste_occurences=[]
                        for occurence in occurences:
                            for instance in occurence:
                                if instance!="":
                                    liste_occurences.append(instance)
                        for occurence in liste_occurences:
                            #on remplit la nouvelle ligne avec les données trouvées
                            #On vérifie si le e est réalisé ou non dans chacun des contextes
                            if re.search("j\(e\)",occurence):
                                nouvelleligne[1]="j-e"
                            elif re.search("je",occurence):
                                nouvelleligne[1]="je"
                            elif re.search("c\(e\)",occurence):
                                nouvelleligne[1]="c-e"
                            elif re.search("ce",occurence):
                                nouvelleligne[1]="ce"
                            elif re.search("d\(e\)",occurence):
                                nouvelleligne[1]="d-e"
                            elif re.search("de",occurence):
                                nouvelleligne[1]="de"
                            elif re.search("l\(e\)",occurence):
                                nouvelleligne[1]="l-e"
                            elif re.search("le",occurence):
                                nouvelleligne[1]="le"
                            elif re.search("m\(e\)",occurence):
                                nouvelleligne[1]="m-e"
                            elif re.search("me",occurence):
                                nouvelleligne[1]="me"
                            elif re.search("n\(e\)",occurence):
                                nouvelleligne[1]="n-e"
                            elif re.search("ne",occurence):
                                nouvelleligne[1]="ne"
                            elif re.search("s\(e\)",occurence):
                                nouvelleligne[1]="s-e"
                            elif re.search("se",occurence):
                                nouvelleligne[1]="se"
                            elif re.search("t\(e\)",occurence):
                                nouvelleligne[1]="t-e"
                            elif re.search("te",occurence):
                                nouvelleligne[1]="te"
                            elif re.search("qu\(e\)",occurence):
                                nouvelleligne[1]="qu-e"
                            elif re.search("que",occurence):
                                nouvelleligne[1]="que"
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

""" extraction_rl(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait tous les mots se terminant en -re ou -le
    et indique si cette terminaison est réalisée ou non
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""

def extraction_rl(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                # ~ enonces=re.split("\.|\?",tourdeparole)
                for enonce in enonces:
                    #que les tu prévocaliques?
                    #on recherche les occurences de mots en -le ou -re dans chaque énoncé
                    if re.search("\\b[a-z-âéàçèïêùûîôA-Z]+([b|c|g|p][r|l]es?(?:nt)?|fles?(?:nt)?|[d|t|v]re?(?:nt)?|[b|c|g|p]\([r|l]es?n?t?\)|f\(les?(?:nt)?\)|[d|t|v]\(re?(?:nt)?\))[\s|.?]",enonce):
                        occurences=re.findall("\\b[a-z-âéàçèïêùûîôA-Z]+([b|c|g|p][r|l]es?(?:nt)?|fles?(?:nt)?|[d|t|v]re?(?:nt)?|[b|c|g|p]\([r|l]es?n?t?\)|f\(les?(?:nt)?\)|[d|t|v]\(re?(?:nt)?\))[\s|.?]",enonce)
                        for occurence in occurences:
                            #on remplit la nouvelle ligne avec les données trouvées
                            #On cherche si la terminaison est réalisée ou non dans les occurences
                            if re.search("bres?n?t?",occurence):
                                nouvelleligne[1]="bre"
                            elif re.search("b\(res?n?t?\)",occurence):
                                nouvelleligne[1]="b-re"
                            elif re.search("bles?n?t?",occurence):
                                nouvelleligne[1]="ble"
                            elif re.search("b\(les?n?t?\)",occurence):
                                nouvelleligne[1]="b-le"
                            elif re.search("cres?n?t?",occurence):
                                nouvelleligne[1]="cre"
                            elif re.search("c\(res?n?t?\)",occurence):
                                nouvelleligne[1]="c-re"
                            elif re.search("cles?n?t?",occurence):
                                nouvelleligne[1]="cle"
                            elif re.search("c\(les?n?t?\)",occurence):
                                nouvelleligne[1]="c-le"
                            elif re.search("dres?n?t?",occurence):
                                nouvelleligne[1]="dre"
                            elif re.search("d\(res?n?t?\)",occurence):
                                nouvelleligne[1]="d-re"
                            elif re.search("tres?n?t?",occurence):
                                nouvelleligne[1]="tre"
                            elif re.search("t\(res?n?t?\)",occurence):
                                nouvelleligne[1]="t-re"
                            elif re.search("fles?n?t?",occurence):
                                nouvelleligne[1]="fle"
                            elif re.search("f\(les?n?t?\)",occurence):
                                nouvelleligne[1]="f-le"
                            elif re.search("gres?n?t?",occurence):
                                nouvelleligne[1]="gre"
                            elif re.search("g\(res?n?t?\)",occurence):
                                nouvelleligne[1]="g-re"
                            elif re.search("gles?n?t?",occurence):
                                nouvelleligne[1]="gle"
                            elif re.search("g\(les?n?t?\)",occurence):
                                nouvelleligne[1]="g-le"
                            elif re.search("pres?n?t?",occurence):
                                nouvelleligne[1]="pre"
                            elif re.search("p\(res?n?t?\)",occurence):
                                nouvelleligne[1]="p-re"
                            elif re.search("ples?n?t?",occurence):
                                nouvelleligne[1]="ple"
                            elif re.search("p\(les?n?t?\)",occurence):
                                nouvelleligne[1]="p-le"
                            elif re.search("vres?n?t?",occurence):
                                nouvelleligne[1]="vre"
                            elif re.search("v\(res?n?t?\)",occurence):
                                nouvelleligne[1]="v-re"
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1


"""	extraction_onomatopee(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait toutes les onomatopées et indique leur forme
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""

def extraction_onomatopee(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    #on recherche les onomatopées dans chaque énoncé
                    if re.search("([a-z-éàçèïïêûîôA-Z']*@o)",enonce):
                        occurences=re.findall("([a-z-éàçèïïêûîôA-Z']*@o)",enonce)
                        for occurence in occurences:
                            nouvelleligne=lignebase
                            #on remplit la nouvelle ligne avec les données trouvées
                            nouvelleligne[1]=re.sub("([a-z-éàçèïïêûîôA-Z']*)@o","\g<1>",occurence)
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1


"""	extraction_mots_etrangers(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait tous les mots étrangers et indique leur forme
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""


def extraction_mots_etrangers(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    #on recherche les mots étrangers dans chaque énoncé
                    if re.search("([a-z-éàçèïïêûîôA-Z']*@s)",enonce):
                        occurences=re.findall("([a-z-éàçèïïêûîôA-Z']*@s)",enonce)
                        for occurence in occurences:
                            nouvelleligne=lignebase
                            #on remplit la nouvelle ligne avec les données trouvées
                            nouvelleligne[1]=re.sub("([a-z-éàçèïïêûîôA-Z']*)@s","\g<1>",occurence)
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

"""	extraction_mots_enfantins(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait tous les mots enfantins et indique leur forme
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""


def extraction_mots_enfantins(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    #on recherche les mots enfantins dans chaque énoncé
                    if re.search("(\[\S+@c\][a-z-âéàçèïêùûîôA-Z]+)",enonce):
                        occurences=re.findall("(\[\S+@c\][a-z-âéàçèïêùûîôA-Z]+)",enonce)
                        for occurence in occurences:
                            nouvelleligne=lignebase
                            #on remplit la nouvelle ligne avec les données trouvées
                            nouvelleligne[1]=re.sub("(\[\S+@c\][a-z-âéàçèïêùûîôA-Z]+)","\g<1>",occurence)
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

""" extraction_cat_gram(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait la catégorie grammaticale de tous les mots
    étiquettés par TreeTagger
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""

def extraction_cat_gram(root,fichier,nouvelleligne,timecode):
                #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Tagging":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.\|[a-z-âéàçèïêùûîôA-Z\.\?]+\|\.|[^.?]*\?\|[a-z-âéàçèïêùûîôA-Z\.\?]+\|\?)",tourdeparole)
                # ~ enonces=re.split("\.|\?",tourdeparole)
                for enonce in enonces:
                    #on recherche la catégorie grammaticale de tous les mots du tour de parole
                    if re.search("[a-z-âéàçèïêùûîôA-Z\.\?]+\|([a-z-âéàçèïêùûîôA-Z\.\?]+):[a-z-âéàçèïêùûîôA-Z\.\?]+\|[a-z-âéàçèïêùûîôA-Z\.\?]+|[a-z-âéàçèïêùûîôA-Z\.\?]+\|([a-z-âéàçèïêùûîôA-Z\.\?]+)\|[a-z-âéàçèïêùûîôA-Z\.\?]+",enonce):
                        occurences=re.findall("[a-z-âéàçèïêùûîôA-Z\.\?]+\|([a-z-âéàçèïêùûîôA-Z\.\?]+):[a-z-âéàçèïêùûîôA-Z\.\?]+\|[a-z-âéàçèïêùûîôA-Z\.\?]+|[a-z-âéàçèïêùûîôA-Z\.\?]+\|([a-z-âéàçèïêùûîôA-Z\.\?]+)\|[a-z-âéàçèïêùûîôA-Z\.\?]+",enonce)
                        liste_occurences=[]
                        for occurence in occurences:
                            for instance in occurence:
                                if instance!="":
                                    liste_occurences.append(instance)
                        for occurence in liste_occurences:
                            # ~ #on remplit la nouvelle ligne avec les données trouvées
                            nouvelleligne[1]=occurence
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1


""" extraction_liaisons_fausses(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait tous les cas de fausses liaisons dans le fichier
    et indique leur forme ainsi que leur contexte
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv


"""

def extraction_liaisons_fausses(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    #on recherche les occurences de liaisons fausses
                    if re.search("([a-z-âéàçèïêùûîôA-Z\.\?]+\s\[\w\][a-z-âéàçèïêùûîôA-Z\.\?]+)",enonce):
                        occurences=re.findall("([a-z-âéàçèïêùûîôA-Z\.\?]+\s\[\w\][a-z-âéàçèïêùûîôA-Z\.\?]+)",enonce)
                        for occurence in occurences:
                            #on remplit la nouvelle ligne avec les données trouvées
                            nouvelleligne[1]=occurence
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

"""	extraction_oui_ouais(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait et sépare toutes les occurrences des mots
    "oui" et "ouais"
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""

def extraction_oui_ouais(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    #on recherche les occurences de oui, ouais et mouais
                    if re.search("\\b(oui|ouais|mouais)\\b",enonce):
                        occurences=re.findall("\\b(oui|ouais|mouais)\\b",enonce)
                        for occurence in occurences:
                            # ~ #on remplit la nouvelle ligne avec les données trouvées
                            nouvelleligne[1]=occurence
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

"""extraction_non_nan(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait et sépare toutes les occurrences des mots
    "non" et "nan"
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""

def extraction_non_nan(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                # ~ enonces=re.split("\.|\?",tourdeparole)
                for enonce in enonces:
                    #on recherche les occurences de non et nan
                    if re.search("\\b(non|nan)\\b",enonce):
                        occurences=re.findall("\\b(non|nan)\\b",enonce)
                        for occurence in occurences:
                            #on remplit la nouvelle ligne avec les données trouvées
                            nouvelleligne[1]=occurence
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

""" extraction_on_nous(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait et sépare toutes les occurrences des mots
    "on" et "nous" en dehors de l'expression "nous on" ainsi que toutes les occurences
    de cette expression
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""

def extraction_on_nous(root,fichier,nouvelleligne,timecode):
        #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1

    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    #on recherche les occurences de on, nous et de l'expression nous on
                    if re.search("\\b(\\bnous\\b(?!\son)|(?<!nous\s)\\bon\\b|\\bnous on)\\b",enonce):
                        occurences=re.findall("\\b(\\bnous\\b(?!\son)|(?<!nous\s)\\bon\\b|\\bnous on)\\b",enonce)
                        for occurence in occurences:
                            #on remplit la nouvelle ligne avec les données trouvées
                            if occurence=="on":
                                nouvelleligne[1]="on"
                            elif occurence=="nous":
                                nouvelleligne[1]="nous"
                            elif occurence=="nous on":
                                nouvelleligne[1]="nous-on"
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

""" extraction_negation(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait tous les contextes de négation repérés auparavant
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""

def extraction_negation(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Négation":
            break
        else:
            position+=1
    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    #on recherche les occurences de négations
                    if re.search("\\b([a-z-âéàçèïêùûîôA-Z\.\?]+\[NN0\]|[a-z-âéàçèïêùûîôA-Z\.\?]+\[NN1\])",enonce):
                        occurences=re.findall("\\b([a-z-âéàçèïêùûîôA-Z\.\?]+\[NN0\]|[a-z-âéàçèïêùûîôA-Z\.\?]+\[NN1\])",enonce)
                        for occurence in occurences:
                            #on remplit la nouvelle ligne avec les données trouvées
                            nouvelleligne[1]=occurence
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

""" extraction_negation_pas(root,fichier,nouvelleligne,timecode)
    Cette fonction extrait tous les contextes de négation en "pas" repérés auparavant
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv"""

def extraction_negation_pas(root,fichier,nouvelleligne,timecode):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne

    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Négation" and re.search("PAS",child.attrib.get("TIER_ID")):
            break
        else:
            position+=1
    positionactivite,positioninterlocuteur,positionsituation=trouver_positions(root)

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                enonces=re.findall("([^.?]*\.|[^.?]*\?)",tourdeparole)
                for enonce in enonces:
                    #on recherche les occurences de négations
                    if re.search("\\b([a-z-âéàçèïêùûîôA-Z\.\?]+\[NN0\]|[a-z-âéàçèïêùûîôA-Z\.\?]+\[NN1\])",enonce):
                        occurences=re.findall("\\b([a-z-âéàçèïêùûîôA-Z\.\?]+\[NN0\]|[a-z-âéàçèïêùûîôA-Z\.\?]+\[NN1\])",enonce)
                        for occurence in occurences:
                            #on remplit la nouvelle ligne avec les données trouvées
                            nouvelleligne[1]=occurence
                            nouvelleligne[7]=tourdeparole
                            nouvelleligne[8]=enonce
                            activite,interlocuteur,situation=trouver_contexte(root,timecode,c,positionactivite,positioninterlocuteur,positionsituation)
                            nouvelleligne[9]=activite
                            nouvelleligne[10]=interlocuteur
                            nouvelleligne[11]=situation
                            fichier.write(";".join(nouvelleligne)+"\n")
    elementcourant+=1

"""extraction_liaisons_facultatives(root, fichier, nouvelleligne, timecode, liaison_type="LF1_LF3")
    Cette fonction extrait et sépare toutes les occurrences de liaisons facultatives.
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
        liaison_type : type de liaison sélectionné par l'utilisateur ("LF1", "LF3" ou "LF1_LF3")
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""


def extraction_liaisons_facultatives(root, fichier, nouvelleligne, timecode, liaison_type="LF1_LF3"):
    lignebase = nouvelleligne

    position = 0
    for child in root:
        if child.tag == "TIER" and child.attrib.get("LINGUISTIC_TYPE_REF") == "LF_LEX_Codee":
            break
        else:
            position += 1

    positionactivite, positioninterlocuteur, positionsituation = trouver_positions(root)

    elementcourant = 0
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole = copy.deepcopy(ele.text)
                enonces = re.findall(r"([^.?]*\.|[^.?]*\?)", tourdeparole)

                for enonce in enonces:
                    pattern = r"(.*?)\s?([a-z-âàéàçèïêùûîôA-Z\d]+)\s(\[LF[13]\])\s([a-z-âàéàçèïêùûîôA-Z\d]+)"

                    start = 0
                    while True:
                        match = re.search(pattern, enonce[start:])
                        if not match:
                            break
                        contexte = match.groups()
                        type_liaison = contexte[2].strip("[]")
                        if liaison_type == "LF1" and type_liaison != "LF1":
                            start += match.end(2)
                            continue
                        if liaison_type == "LF3" and type_liaison != "LF3":
                            start += match.end(2)
                            continue
                        nouvelleligne = lignebase.copy()
                        mot1, mot2 = contexte[1], contexte[3]
                        activite, interlocuteur, situation = trouver_contexte(root, timecode, c, positionactivite,
                                                                              positioninterlocuteur, positionsituation)
                        nouvelleligne[1] = type_liaison
                        nouvelleligne[7] = tourdeparole
                        nouvelleligne[8] = enonce
                        nouvelleligne[9] = mot1
                        nouvelleligne[10] = mot2
                        nouvelleligne[11] = activite
                        nouvelleligne[12] = interlocuteur
                        nouvelleligne[13] = situation
                        fichier.write(";".join(nouvelleligne) + "\n")
                    #Avance l'index pour chercher les autres occurences
                        start += match.end(2)

    elementcourant += 1