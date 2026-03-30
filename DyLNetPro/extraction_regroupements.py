
#!/usr/bin/python
# -*- coding: UTF-8 -*-
#prérequis:python 3.7 ou plus (ordre des dict)

#expliquer dans doc comment étendre fichier de correspondance

# les importations nécessaires
import re
import xml.etree.ElementTree as ET
import copy
import datas
import sys
import os
import math


""" extract_organise_reg(filenames,variable,newfile="extraction brute",regroupements="",limit=None,limit_value=None)
    Cette fonction permet, a partir d'un fichier _VC.eaf de créer un fichier .csv contenant une extraction organisée avec
    des regoupement

    Entrées:
        filenames: Ensemble de chemin d'accès aux fichiers à traiter (Array)
        variable: Variable à traiter (String)
        newfile: Nom à donner au nouveau fichier
        regroupements: type de regroupement (String)
        limit: quelle limite appliquer (Int)
            0=pas de limite
            10= limite énonces
            20= limite mots
            30= limite temps de parole (en secondes)
        limit_value: la valeur de la limite (String)
        traitement_liaison: Indique si il faut lancer le traitement spécial des liaisons facultatives (Boolean)
        liaison_list: Indique le mot1 et mot2 choisis par l'utilisateur pour le traitement spécial des liaisons facultatives (List)
    Sorties:
        Création d'un fichier .csv d'extraction organisée avec regroupement
"""
def extract_organisee_reg(filenames,variable,newfile="extraction organisee par regroupements",regroupements="",limit=None,limit_value=None,traitement_liaison=False,liaison_list=[]):
    # si le dossier de sortie n'exite pas on le crée
    if not os.path.exists('./Sortie'):
        os.mkdir('./Sortie')
    if not os.path.exists('./Sortie/Extraction_Organisee_Reg'):
        os.mkdir('./Sortie/Extraction_Organisee_Reg')

    #On ouvre le fichier .csv ou on va écrire
    #nom à modifier ici
    #ajout limite au nom
    #ajout regroupements au nom
    if regroupements=="":
        texte_regroupement="pas-regroupement"
    else:
        texte_regroupement="regroupement"
        if "a" in regroupements:
            texte_regroupement+="-contexte"
        if "b" in regroupements:
            texte_regroupement+="-variable"
        if "c" in regroupements:
            texte_regroupement+="-sexe"
    texte_limite="pas-limite"
    if limit==10 and variable=="lme":
        texte_limite="limite_"+str(limit_value)+"-enonces"
    if limit==20 and (variable=="rtt" or variable=="lme"):
        texte_limite="limite_"+str(limit_value)+"-tokens"
    if limit==30 and variable=="lme":
        texte_limite="limite_"+str(limit_value)+"-millisecondes-parole"
    fichier=open("Sortie/Extraction_Organisee_Reg/"+newfile+"_"+variable+"_"+texte_regroupement+"_"+texte_limite+".csv",mode="w",encoding="UTF-8")
    if "a" in regroupements:
        modele=creertableau_regroupements(variable,regroupements)
    else:
        modele=creertableau(variable,regroupements)
    ID_to_niveau={}
    #on importe le fichier .csv qui contient les correspondances
            #ID-Niveau
    fichier_correspondance=open("input/Infos_ID_niv_scol_periodes.csv",mode="r",encoding="UTF-8")
    for line in fichier_correspondance.readlines():
        donnees=line.split(";")
        if donnees[0]!="ID_dylnet":
            ID_to_niveau[donnees[0]]=donnees[1:]
    fichier_correspondance.close()

    #on crée la ligne de titre qui sera remplie plus tard
    lignetitre=["id_dylnet","niv-scol","num-class","compo-class","annee","periodes-projet","periodes-ecole","Nb-fichiers","temps-parole(milisecondes)", "Nb-mots"]
    # Vérifier si les colonnes "temps-parole(milisecondes)" et "Nb-mots" doivent être exclues

    if variable not in ["ADJ","ADV","AUX","DET","EPE","ETR","FNO","INT","KON","LOC","MLT","NAM","NOM","NUM","PRO","PRP","PRT","SYM","TRC","VER","SENT"]:
        for clef in modele.keys():
            lignetitre.append(clef)
        fichier.write(";".join(lignetitre)+"\n")
    else:
        for clef in modele.keys():
            if re.search(variable,clef):
                lignetitre.append(clef)
        fichier.write(";".join(lignetitre)+"\n")
    #on analyse chacun des fichiers donnés en entrée
    idperiode2file={}
    #On crée une nouvelle ligne ou seront mises les données
    for filename in filenames:
        log_file=open("log.log",mode="a")
        log_file.write(filename.split("/")[-1:][0]+" -"+variable+" -regroupement\n")
        log_file.close()
        nomdefichier=re.search('([^\/.]*?.eaf)',filename)
        #on récupère le nom du fichier
        nomdefichier=nomdefichier.group(1)
        #on récupère l'ID
        identifiant=nomdefichier[19:23]
        #On récupère la date et on l'analyse pour trouver la periode
        date=nomdefichier[3:11]
        date=int(date)
        if date>=20170901 and date<=20171231:
            periode_ecole="rentree-A1"
        elif date>=20180401 and date<=20180630:
            periode_ecole="fin-A1"
        elif date>=20180901 and date<=20181231:
            periode_ecole="rentree-A2"
        elif date>=20190401 and date<=20190630:
            periode_ecole="fin-A2"
        elif date>=20190901 and date<=20190930:
            periode_ecole="rentree-A3"
        elif date>=20191001 and date<=20200301:
            periode_ecole="fin-A3"
        if (identifiant,periode_ecole) in idperiode2file.keys():
            idperiode2file[(identifiant,periode_ecole)].append("./uploads/"+filename)
        else:
            idperiode2file[(identifiant,periode_ecole)]=["./uploads/"+filename]
    personne_actuelle=1
    for cle in idperiode2file.keys():
        fichier_actuel=1
        print ("analyse des fichiers de la personne",str(personne_actuelle),"sur",str(len(idperiode2file)))
        personne_actuelle+=1
        types={}
        #selon le type de regroupement on appelle la fonction creer tableau correspondante
        #if "a" in regroupements:
        if "a" in regroupements:
            occurences=creertableau_regroupements(variable,regroupements)
        else:
            occurences=creertableau(variable,regroupements)
        #initialisation
        tempsparole=0
        nbmots=0
        nbenonces=0
        for filename in idperiode2file[cle]:
            if variable=="lme" and limit==10 and nbenonces>=limit_value:
                print("limite enonces atteinte")
                break
            if (variable=="rtt" or variable=="lme") and limit==20 and nbmots>=limit_value:
                print("limite tokens atteinte")
                break
            if variable=="lme" and limit==30 and tempsparole>=limit_value:
                print("limite temps atteinte")
                break
            fichier_actuel+=1
            tree=ET.parse(filename,ET.XMLParser(encoding='utf-8'))
            root=tree.getroot()
            positiontime=0
            for child in root:
                if child.tag=="TIME_ORDER":
                    break
                else:
                    positiontime+=1
            timecodes={}
            for child in root[positiontime]:

                time=child.attrib.get("TIME_VALUE")
                ID=child.attrib.get("TIME_SLOT_ID")
                if time in timecodes.keys():
                    timecodes[time].append(ID)
                else:
                    timecodes[time]=[ID]
            nomdefichier=re.search('([^\/.]*?.eaf)',filename)
            nomdefichier=nomdefichier.group(1)
            #On crée une nouvelle ligne ou seront mises les données
            nouvelleligne=["","","","","","","","","",""]
            #on remplit la colonne ID
            nouvelleligne[0]="ID-"+nomdefichier[19:23]
            #on remplit la colonne 3
            nouvelleligne[2]="CL-"+nomdefichier[0:2]
            #remplissage de la colonne 4 selon la classe
            if nouvelleligne[2] in ("CL-11","CL-12","CL-21","CL-22","CL-31","CL-32"):
                nouvelleligne[3]="PS"

            elif nouvelleligne[2] in ("CL-13","CL-23"):
                nouvelleligne[3]="PS-MS"

            elif nouvelleligne[2] in("CL-14","CL-24","CL-33","CL-34"):
                nouvelleligne[3]="MS"

            elif nouvelleligne[2] in ("CL-15","CL-16","CL-25","CL-35"):
                nouvelleligne[3]="MS-GS"

            elif nouvelleligne[2] in ("CL-17","CL-26","CL-27","CL-36","CL-37"):
                nouvelleligne[3]="GS"
        #On récupère la date et on l'analyse pour trouver la periode
            date=nomdefichier[3:11]
            date=int(date)
            if date>=20170901 and date<=20171231:
                nouvelleligne[4]="A1"
                nouvelleligne[5]="P0"
                nouvelleligne[6]="rentree-A1"
            elif date>=20180401 and date<=20180630:
                nouvelleligne[4]="A1"
                nouvelleligne[5]="P1"
                nouvelleligne[6]="fin-A1"
            elif date>=20180901 and date<=20181231:
                nouvelleligne[4]="A2"
                nouvelleligne[5]="P1"
                nouvelleligne[6]="rentree-A2"
            elif date>=20190401 and date<=20190630:
                nouvelleligne[4]="A2"
                nouvelleligne[5]="P2"
                nouvelleligne[6]="fin-A2"
            elif date>=20190901 and date<=20190930:
                nouvelleligne[4]="A3"
                nouvelleligne[5]="P2"
                nouvelleligne[6]="rentree-A3"
            elif date>=20191001 and date<=20200301:
                nouvelleligne[4]="A3"
                nouvelleligne[5]="P3"
                nouvelleligne[6]="fin-A3"
            nouvelleligne[7]=str(len(idperiode2file[cle]))
            #on remplit la colonne 2 selon le niveau du locuteur
            # ~ nouvelleligne[0]= "ID-****"
            # ~ nouvelleligne[4]= periode
            #modifications temporaires pour tester sans les colonnes A0
            """if nouvelleligne[4]=="A0":
                nouvelleligne[1]=ID_to_niveau[nouvelleligne[0]][0]"""
            if nouvelleligne[4]=="A1":
                nouvelleligne[1]=ID_to_niveau[nouvelleligne[0]][0]
            elif nouvelleligne[4]=="A2":
                nouvelleligne[1]=ID_to_niveau[nouvelleligne[0]][2]
            elif nouvelleligne[4]=="A3":
                nouvelleligne[1]=ID_to_niveau[nouvelleligne[0]][4]

            positionnettoye=0
            for child in root:
                if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
                    break
                else:
                    positionnettoye+=1
             #on parcourt les tours de parole
            for child in root[positionnettoye]:
                for c in child:
                    for ele in c:
                        debut=0
                        fin=0
                        #on récupère les bornes temporels+
                        limits=[c.attrib.get("TIME_SLOT_REF1"),c.attrib.get("TIME_SLOT_REF2")]
                        for time in timecodes.keys():
                            if limits[0] in timecodes[time]:
                                debut=int(time)
                            if limits[1] in timecodes[time]:
                                fin=int(time)
                        tempsparole+=fin-debut
         #on parcourt les tours de parole
            for child in root[positionnettoye]:
                for c in child:
                    for ele in c:
                        #on crée une copie profonde
                        tourdeparole=copy.deepcopy(ele.text)
                        tourdeparole=re.sub("(xxx|ooo|aaa|sss)","",tourdeparole)
                        #tokenisation
                        tokens=re.findall("(aujourd'hui|d'accord|d'abord|d'ailleurs|rock'n'roll|quelqu'un|c'est-à-dire|[a-z-âàéàçèïêùûîôA-Z\d]+)",tourdeparole)
                        for token in tokens:
                            nbmots+=1
                        #comptage enonces
                        liste_enonces=re.findall(".*?(\.|\?)",tourdeparole)
                        for enonce in liste_enonces:
                            nbenonces+=1

            #en fonction de la variable donnée, on appelle la fonction correspondante
            if variable=="enonces":
                extraction_enonces(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="tu":
                extraction_tu(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="I-dans-il":
                extraction_I_dans_il(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="il-complet":
                extraction_il_complet(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="schwa":
                extraction_schwa(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="rl":
                extraction_rl(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="@o":
                extraction_onomatopee(root,nouvelleligne,timecodes,occurences,regroupements,variable)
            elif variable=="@s":
                extraction_mots_etrangers(root,nouvelleligne,timecodes,occurences,regroupements,variable)
            elif variable=="@c":
                extraction_mots_enfantins(root,nouvelleligne,timecodes,occurences,regroupements,variable)
            elif variable in ["ADJ","ADV","AUX","DET","EPE","ETR","FNO","INT","KON","LOC","MLT","NAM","NOM","NUM","PRO","PRP","PRT","SYM","TRC","VER","SENT"]:
                extraction_cat_gram(root,nouvelleligne,timecodes,occurences,variable,regroupements)
            elif variable=="liaison-fausse":
                extraction_liaisons_fausses(root,nouvelleligne,timecodes,occurences,regroupements,variable)
            elif variable=="oui-ouais":
                extraction_oui_ouais(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="non-nan":
                extraction_non_nan(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="on-nous":
                extraction_on_nous(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="neg":
                extraction_negation(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="neg-pas":
                extraction_negation_pas(root,nouvelleligne,timecodes,occurences,regroupements)
            elif variable=="tokens":
                extraction_tokens(root,nouvelleligne,timecodes,occurences,regroupements,variable)
            elif variable=="types":
                extraction_types(root,nouvelleligne,timecodes,occurences,types,regroupements,variable)
            elif variable=="rtt":
                extraction_rtt(root,nouvelleligne,timecodes,occurences,types,regroupements,variable,limit,limit_value)
            elif variable=="lme":
                extraction_lme(root,nouvelleligne,timecodes,occurences,regroupements,variable,limit,limit_value)
            elif variable=="temps":
                extraction_temps(root,nouvelleligne,timecodes,occurences,regroupements,variable)
            elif variable=="lf":
                extraction_liaisons_facultatives(root,nouvelleligne,timecodes,occurences,regroupements,traitement_liaison,liaison_list)
            #ajouter les nouvelle variables
        if variable=="rtt":
            temp={}
            for key in occurences.keys():
                if re.search("rtt_",key):
                    if occurences[key]!=0:
                        temp[key]=types[key]/occurences[key]
                        temp[re.sub("rtt_","rttg_",key)]=types[key]/math.sqrt(occurences[key])
                        temp[re.sub("rtt_","types_",key)]=types[key]
                        temp[re.sub("rtt_","tokens_",key)]=occurences[key]
                    else:
                        temp[key]="NA"
                        temp[re.sub("rtt_","rttg_",key)]="NA"
                        temp[re.sub("rtt_","types_",key)]=0
                        temp[re.sub("rtt_","tokens_",key)]=occurences[key]
            occurences=temp
            occurences=temp

        if variable=="lme":
            temp={}
            duree_avec_limite = occurences["duree_avec_limite"]
            for key in occurences.keys():
                if re.search("enonces",key):
                    if occurences[key]!=0 and occurences[key]!="NA" and occurences[re.sub("enonces_","tokens_",key)]!=0 and occurences[re.sub("enonces_","tokens_",key)]!="NA":
                        temp[re.sub("enonces_","lme_",key)]=occurences[re.sub("enonces_","tokens_",key)]/occurences[key]
                        temp[key]=occurences[key]
                        temp[re.sub("enonces_","tokens_",key)]=occurences[re.sub("enonces_","tokens_",key)]
                    else:
                        temp[re.sub("enonces_","lme_",key)]="NA"
                        temp[key]=occurences[key]
                        temp[re.sub("enonces_","tokens_",key)]="NA"
            occurences=temp
        if variable in ["ADJ","ADV","AUX","DET","EPE","ETR","FNO","INT","KON","LOC","MLT","NAM","NOM","NUM","PRO","PRP","PRT","SYM","TRC","VER","SENT"]:
            temp={}
            for key in occurences.keys():
                if re.search(variable,key):
                    temp[key]=0
            for key in occurences.keys():
                if re.search("instances",key):
                    if occurences[key]!=0 and occurences[re.sub("instances_","tokens_",key)]!=0:
                        temp[re.sub("instances_",variable+"_",key)]=occurences[key]/occurences[re.sub("instances_","tokens_",key)]
                    else:
                        temp[re.sub("instances_",variable+"_",key)]="NA"
            occurences=temp


        #repmlissage des colonnes 9 (tempsparole) et 10(nb_mots)
        if not limit:
            nouvelleligne[8] = str(tempsparole)
            nouvelleligne[9] = str(nbmots)
        elif limit==30 and duree_avec_limite>=limit_value:
            nouvelleligne[8]= str(duree_avec_limite)
            nouvelleligne[9] = "NA"
        else:# en cas de limit par enonces ou mots
            nouvelleligne[8] = "NA"
            nouvelleligne[9] = "NA"

        for key in occurences:
            nouvelleligne.append(str(occurences[key]))
            # ecriture dans le fichier .csd
        fichier.write(";".join(nouvelleligne) + "\n")
     #on ferme le fichier
    fichier.close()



""" creertableau(variable,regroupements)
    Cette fonction permet de créer un tableau qui contient toutes les variantes de
    la variable dans les 140 contextes possibles
    Entrées:
        variable: Variable à traiter (String)
        regroupements: type de regroupemenr (String)
    Sorties:
        tableau: Tableau contenant toutes les combinaisons de variante et
        de contexte (Dict)
"""

def creertableau(variable,regroupements):
    #liste des contextes possibles
    contextes = datas.contextes
    contextes_reduits = datas.contextes_reduits
    tableau={}
    #On crée une variable pour indiquer si il faut inverser la construction du tableau
    inversion=False
    #selon la variable on affecte la variante
    #On cherche si il est nécessaire d'utiliser la version réduite des colonnes
    if variable=="rl" or variable=="schwa" or variable=="neg" or "c" in regroupements:
        reduction=True
    else:
        reduction=False
    if variable=="@o":
        variantes=["@o"]
    elif variable=="@s":
        variantes=["@s"]
    elif variable=="@c":
        variantes=["@c"]
    elif variable=="tu":
        variantes=["tu","t-u"]
    elif variable=="I-dans-il":
        variantes=["il","i-l","ils","i-ls"]
    elif variable=="il-complet":
        variantes=["il-produit","il-suppr","ils-produit","ils-suppr"]
    elif variable=="enonces":
        variantes=["enonces-point","enonces-interrog"]
    elif variable=="schwa" and "b" in regroupements:
        variantes=["e-produit","e-suppr"]
    elif variable=="schwa":
        variantes=["je","j-e","ce","c-e","de","d-e","le","l-e","me","m-e",\
        "ne","n-e","se","s-e","te","t-e","que","qu-e"]
    elif variable=="rl" and "b" in regroupements:
        variantes=["r-produit","r-suppr","l-produit","l-suppr"]
    elif variable=="rl":
        variantes=["bre","b-re","ble","b-le","cre","c-re","cle","c-le",\
        "dre","d-re","tre","t-re","fle","f-le","gre","g-re","gle","g-le",\
        "pre","p-re","ple","p-le","vre","v-re"]
    elif variable=="liaison-fausse":
        variantes=["liaison-fausse"]
    elif variable=="oui-ouais":
        variantes=["oui","ouais","mouais"]
    elif variable=="non-nan":
        variantes=["non","nan"]
    elif variable=="on-nous":
        variantes=["nous-on","nous","on"]
    elif variable=="neg":
        variantes=["pas[NN0]","pas[NN1]","jamais[NN0]","jamais[NN1]","personne[NN0]","personne[NN1]",\
        "rien[NN0]","rien[NN1]","aucun[NN0]","aucun[NN1]","aucune[NN0]","aucune[NN1]","aucunes[NN0]","aucunes[NN1]",\
        "aucuns[NN0]","aucuns[NN1]"]
    elif variable=="neg-pas":
        variantes=["pas[NN0]","pas[NN1]"]
    elif variable=="tokens":
        variantes=["tokens"]
    elif variable=="types":
        variantes=["types"]
    elif variable=="rtt":
        variantes=["rtt","rttg","types","tokens"]
        inversion=True
    elif variable=="lme":
        variantes=["lme","enonces","tokens"]
        inversion=True
    elif variable in ["ADJ","ADV","AUX","DET","EPE","ETR","FNO","INT","KON","LOC","MLT","NAM","NOM","NUM","PRO","PRP","PRT","SYM","TRC","VER","SENT"]:
        variantes=["tokens","instances",variable]
    elif variable=="temps":
        variantes=["temps"]
    elif variable=="lf":
        variantes=["LF1","LF3"]
    #analyse par sexe du locuteur: on ajoute Homme/Femme/Inconnu et Mixte après
    #chaque contexte
    if "c" in regroupements:
        contextes_sexe=[]
        for contexte in contextes_reduits:
            for sexe in ["H","F","I","M"]:
                contextes_sexe.append(contexte+"_"+sexe)
        contextes_reduits=contextes_sexe
    if inversion:
        if reduction:
            for contexte in contextes_reduits:
                for variante in variantes:
                    tableau[variante+"_"+contexte]=0
            return tableau
        else:
            for contexte in contextes:
                for variante in variantes:
                    tableau[variante+"_"+contexte]=0
            return tableau
    else:
        if reduction:
            for variante in variantes:
                for contexte in contextes_reduits:
                    tableau[variante+"_"+contexte]=0
            return tableau
        else:
            for variante in variantes:
                for contexte in contextes:
                    tableau[variante+"_"+contexte]=0
            return tableau

""" creertableau_regroupements(variable,regroupements)
    Cette fonction permet de créer un tableau qui contient toutes les variantes de
    la variable dans les contextes possibles après le regroupement
    Entrées:
        variable: Variable à traiter (String)
        regroupements: type de regroupemenr (String)
    Sorties:
        tableau: Tableau contenant toutes les combinaisons de variante et
        de contexte (Dict)
"""

def creertableau_regroupements(variable,regroupements):
    contextes = datas.contextes_regroupements
    tableau={}
    #On crée une variable pour indiquer si il faut inverser la construction du tableau
    inversion=False
    if variable=="@o":
        variantes=["@o"]
    elif variable=="@s":
        variantes=["@s"]
    elif variable=="@c":
        variantes=["@c"]
    elif variable=="tu":
        variantes=["tu","t-u"]
    elif variable=="I-dans-il":
        variantes=["il","i-l","ils","i-ls"]
    elif variable=="il-complet":
        variantes=["il-produit","il-suppr","ils-produit","ils-suppr"]
    elif variable=="enonces":
        variantes=["enonces-point","enonces-interrog"]
    elif variable=="schwa" and "b" in regroupements:
        variantes=["e-produit","e-suppr"]
    elif variable=="schwa":
        variantes=["je","j-e","ce","c-e","de","d-e","le","l-e","me","m-e",\
        "ne","n-e","se","s-e","te","t-e","que","qu-e"]
    elif variable=="rl" and "b" in regroupements:
        variantes=["r-produit","r-suppr","l-produit","l-suppr"]
    elif variable=="rl":
        variantes=["bre","b-re","ble","b-le","cre","c-re","cle","c-le",\
        "dre","d-re","tre","t-re","fle","f-le","gre","g-re","gle","g-le",\
        "pre","p-re","ple","p-le","vre","v-re"]
    elif variable=="liaison-fausse":
        variantes=["liaison-fausse"]
    elif variable=="oui-ouais":
        variantes=["oui","ouais","mouais"]
    elif variable=="non-nan":
        variantes=["non","nan"]
    elif variable=="on-nous":
        variantes=["nous-on","nous","on"]
    elif variable=="neg":
        variantes=["pas[NN0]","pas[NN1]","jamais[NN0]","jamais[NN1]","personne[NN0]","personne[NN1]",\
        "rien[NN0]","rien[NN1]","aucun[NN0]","aucun[NN1]","aucune[NN0]","aucune[NN1]","aucunes[NN0]","aucunes[NN1]",\
        "aucuns[NN0]","aucuns[NN1]"]
    elif variable=="neg-pas":
        variantes=["pas[NN0]","pas[NN1]"]
    elif variable=="tokens":
        variantes=["tokens"]
    elif variable=="types":
        variantes=["types"]
    elif variable=="rtt":
        variantes=["rtt","rttg","types","tokens"]
        inversion=True
    elif variable=="lme":
        variantes=["lme","enonces","tokens"]
        inversion=True
    elif variable in ["ADJ","ADV","AUX","DET","EPE","ETR","FNO","INT","KON","LOC","MLT","NAM","NOM","NUM","PRO","PRP","PRT","SYM","TRC","VER","SENT"]:
        variantes=["tokens","instances",variable]
    elif variable=="temps":
        variantes=["temps"]
    elif variable=="lf":
        variantes=["LF1","LF3"]
    #analyse par sexe du locuteur: on ajoute Homme/Femme/Inconnu et Mixte après
    #chaque contexte
    if "c" in regroupements:
        contextes_sexe=[]
        for contexte in contextes:
            for sexe in ["H","F","I","M"]:
                contextes_sexe.append(contexte+"_"+sexe)
        contextes=contextes_sexe
    if inversion:
        for contexte in contextes:
            for variante in variantes:
                tableau[variante+"_"+contexte]=0
        return tableau
    else:
        for variante in variantes:
            for contexte in contextes:
                tableau[variante+"_"+contexte]=0
        return tableau

""" trouver_positions(root)
    Cette fonction permet de récupèrer la position des quatre lignes nécessaires
    au traitement: la ligne 'Activité', la ligne 'Interlocuteur',
    la ligne 'Situation Langagière' et la ligne 'Sexe'
    Entrées:
        root: racine d'un arbre XML (ElementTree)
    Sorties:
        positionactivite: Position de la ligne 'Activité' (Integer)
        positioninterlocuteur: Position de la ligne 'Interlocuteur' (Integer)
        positionsituation: Position de la ligne 'Situation Langagière' (Integer)
        positionsexe: Position de la ligne 'Sexe' (Integer)
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

    positionsexe=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("TIER_ID")=="Sexe":
            break
        else:
            positionsexe+=1
    return(positionactivite,positioninterlocuteur,positionsituation,positionsexe)


""" trouver_contexte(root,timecodes,element,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
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
        positionsexe: Position de la ligne 'Sexe' (Integer)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        activite : Le contenu de la borne sur la ligne 'Activité' correspondant
        à l'élément etudié (String)
        interlocuteur : Le contenu de la borne sur la ligne 'Activité' correspondant
        à l'élément etudié (String)
        situation : Le contenu de la borne sur la ligne 'Activité' correspondant
        à l'élément etudié (String)
"""

def trouver_contexte(root,timecodes,element,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=False):
    #On récupère les bornes temporelles de l'element actuellement étudié
    limits=[element.attrib.get("TIME_SLOT_REF1"),element.attrib.get("TIME_SLOT_REF2")]
    #On récupère l'id de l'élément actuel:
    id=element.attrib.get("ANNOTATION_ID").split("_")[0]
    #On recherche ces bornes temporelles dans la liste des bornes temporelles
    for time in timecodes.keys():
        if limits[0] in timecodes[time]:
            limits[0]=timecodes[time]
        if limits[1] in timecodes[time]:
            limits[1]=timecodes[time]
    #on récupère l'activité en cours
    activite="Indéterminée"
    for child_activite in root[positionactivite]:
        for a in child_activite:
            for ele_a in a:
                if a.attrib.get("ANNOTATION_REF")==id:
                    activite=ele_a.text
                else:
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
                if i.attrib.get("ANNOTATION_REF")==id:
                    interlocuteur=ele_i.text
                else:
                    if i.attrib.get("TIME_SLOT_REF1") in limits[0] and i.attrib.get("TIME_SLOT_REF2") in limits[1]:
                        interlocuteur=ele_i.text
    #Si la ligne Activité est vide, on donne "Indéterminée" comme valeur par défaut
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
    #si présente, on récupère la situation linguistique
    situation="Pas de situation langagière"

    #if len(limits[0])>3:
    for child_situation in root[positionsituation]:
        for s in child_situation:
            for ele_s in s:
                if s.attrib.get("ANNOTATION_REF")==id:
                    situation=ele_s.text
                else:
                    if s.attrib.get("TIME_SLOT_REF1") in limits[0] and s.attrib.get("TIME_SLOT_REF2") in limits[1]:
                        situation=ele_s.text
    if situation==None:
        situation="Pas de situation langagière"
                        # ~ situation="Pas de situation langagière"
    #On corrige certaines erreurs qui apparaîssent parfois dans cette ligne
    if situation[-1]==" ":
        situation=situation[:-1]
    if situation=="Récitation Récitation":
        situation="Récitation"
    contextes = datas.contextes_non_corriges
    contextescorriges = datas.contextes
    contextesreduits = datas.contextes_reduits

    if "c" in regroupements:
        for child_sexe in root[positionsexe]:
            for j in child_sexe:
                for ele_j in j:
                    if j.attrib.get("ANNOTATION_REF")==id:
                        sexe=ele_j.text
                    else:
                        if j.attrib.get("TIME_SLOT_REF1") in limits[0] and j.attrib.get("TIME_SLOT_REF2") in limits[1]:
                            sexe=ele_j.text
        sexe=sexe[0]
        contextes2=[]
        contextesreduits2=[]
        for contexte in contextes:
            for option in ["H","F","I","M"]:
                contextes2.append(contexte+"#"+option)
        for contexte in contextesreduits:
            for option in ["H","F","I","M"]:
                contextesreduits2.append(contexte+"_"+option)
        contexte=activite+"#"+interlocuteur+"#"+situation+"#"+sexe
        contexte=contextesreduits2[contextes2.index(contexte)]
        #dans l'attente d'une meilleure solution, on ajoute le sexe aux elements renvoyés
        return contexte,sexe
    else:
        if reduits:
            contexte=activite+"#"+interlocuteur+"#"+situation
            contexte=contextesreduits[contextes.index(contexte)]
            return contexte
        else:
            contexte=activite+"#"+interlocuteur+"#"+situation
            contexte=contextescorriges[contextes.index(contexte)]
            return contexte

"""trouver_contexte_regroupements(root,timecodes,element,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
    Cette fonction permet de récupèrer le contexte d'un tour de parole,
    c'est-à-dire le contenu des lignes 'Activité','Interlocuteur' et 'Situation Langagière'
    qui lui correspondent, et d'ajuster ce contenu afin de le faire correspondre aux regroupements demandés
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        element: l'element qu'on est en train d'etudier (ElementTree)
        positionactivite: Position de la ligne 'Activité' (Integer)
        positioninterlocuteur: Position de la ligne 'Interlocuteur' (Integer)
        positionsituation: Position de la ligne 'Situation Langagière' (Integer)
        positionsexe: Position de la ligne 'Sexe' (Integer)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        activite : Le contenu de la borne sur la ligne 'Activité' correspondant
        à l'élément etudié (String)
        interlocuteur : Le contenu de la borne sur la ligne 'Activité' correspondant
        à l'élément etudié (String)
        situation : Le contenu de la borne sur la ligne 'Activité' correspondant
        à l'élément etudié (String)
"""
def trouver_contexte_regroupements(root,timecodes,element,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements):
    limits=[element.attrib.get("TIME_SLOT_REF1"),element.attrib.get("TIME_SLOT_REF2")]
    for time in timecodes.keys():
        if limits[0] in timecodes[time]:
            limits[0]=timecodes[time]
        if limits[1] in timecodes[time]:
            limits[1]=timecodes[time]
    id=element.attrib.get("ANNOTATION_ID").split("_")[0]
    #on récupère l'activité en cours
    activite="Indéterminée"
    for child_activite in root[positionactivite]:
        for a in child_activite:
            for ele_a in a:
                if a.attrib.get("ANNOTATION_REF")==id:
                    activite=ele_a.text
                else:
                    if a.attrib.get("TIME_SLOT_REF1") in limits[0] and a.attrib.get("TIME_SLOT_REF2") in limits[1]:
                        activite=ele_a.text
    if activite==None:
        activite="Indéterminée"
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
                if i.attrib.get("ANNOTATION_REF")==id:
                    interlocuteur=ele_i.text
                else:
                    if i.attrib.get("TIME_SLOT_REF1") in limits[0] and i.attrib.get("TIME_SLOT_REF2") in limits[1]:
                        interlocuteur=ele_i.text
    if interlocuteur==None:
        interlocuteur="Indéterminé"
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
    #si présente, on récupère la situation linguistique
    situation="Pas de situation langagière"
    #if len(limits[0])>3:
    for child_situation in root[positionsituation]:
        for s in child_situation:
            for ele_s in s:
                if s.attrib.get("ANNOTATION_REF")==id:
                    situation=ele_s.text
                else:
                    if s.attrib.get("TIME_SLOT_REF1") in limits[0] and s.attrib.get("TIME_SLOT_REF2") in limits[1]:
                        situation=ele_s.text
    if situation==None:
        situation="Pas de situation langagière"
        # ~ situation="Pas de situation langagière"
    if situation[-1]==" ":
        situation=situation[:-1]
    if situation=="Récitation Récitation":
        situation="Récitation"
    if activite not in ["En classe","Récréation"]:
        activite="?"
    if interlocuteur in ["Enseignant classe","Atsem classe","Adulte"]:
        interlocuteur="Adultes"
    elif interlocuteur in ["un ou plusieurs enfant(s)","Classe entière"]:
        interlocuteur="Enfants"
    else:
        interlocuteur="?"
    if situation in ["Récitation","Lecture (uniquement adulte)","Consigne (uniquement adulte)"]:
        situation="Avec situation"
    else:
        situation="Sans situation"
    if "c" in regroupements:
        for child_sexe in root[positionsexe]:
            for j in child_sexe:
                for ele_j in j:
                    if j.attrib.get("ANNOTATION_REF")==id:
                        sexe=ele_j.text
                    else:
                        if j.attrib.get("TIME_SLOT_REF1") in limits[0] and j.attrib.get("TIME_SLOT_REF2") in limits[1]:
                            sexe=ele_j.text
        sexe=sexe[0]
        contextes = datas.contextes_non_corriges_regroupements
        contextescorriges = datas.contextes_regroupements
        contextes2=[]
        contextescorriges2=[]
        for contexte in contextes:
            for option in ["H","F","I","M"]:
                contextes2.append(contexte+"#"+option)
        for contexte in contextescorriges:
            for option in ["H","F","I","M"]:
                contextescorriges2.append(contexte+"_"+option)
        contexte=activite+"#"+interlocuteur+"#"+situation+"#"+sexe
        if not re.search("\?",contexte):
            contexte=contextescorriges2[contextes2.index(contexte)]
        #dans l'attente d'une meilleure solution, on ajoute le sexe aux elements renvoyés
        return contexte,sexe
    else:
        contexte=activite+"#"+interlocuteur+"#"+situation
        if not re.search("\?",contexte):
            # contextes=["En classe#Adultes#Avec situation","En classe#Adultes#Sans situation","En classe#Enfants#Avec situation","En classe#Enfants#Sans situation","Récréation#Adultes#Avec situation","Récréation#Adultes#Sans situation","Récréation#Enfants#Avec situation","Récréation#Enfants#Sans situation"]
            # contextescorriges=["EnClasse-Adultes-AvecSituation","EnClasse-Adultes-SansSituation","EnClasse-Enfants-AvecSituation","EnClasse-Enfants-SansSituation","Recre-Adultes-AvecSituation","Recre-Adultes-SansSituation","Recre-Enfants-AvecSituation","Recre-Enfants-SansSituation"]
            contextes = datas.contextes_non_corriges_regroupements
            contextescorriges = datas.contextes_regroupements
            contexte=contextescorriges[contextes.index(contexte)]
    return contexte


""" extraction_enonces(root,fichier,nouvelleligne,timecodes, occurences, regroupements)
    Cette fonction extrait tous les énoncés de chaque tour de parole et indique
    si ce sont des énoncés déclaratifs ou interrogatifs
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        regroupements: le type de regroupements à appliquer (String)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""
def extraction_enonces(root,nouvelleligne,timecodes,occurences,regroupements):
        #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1


    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on divise chaque tour de parole en fonction des énoncés
                instances=re.findall(".*?(\.|\?)",tourdeparole)
                for instance in instances:
                    if not re.match("^(\s?xxx[\s.?])+$",instance):
                        if re.search ("\.",instance):
                            variante="enonces-point"
                        elif re.search("\?",instance):
                            variante="enonces-interrog"
                        if "c" not in regroupements:
                            occurences[variante+"_global"]+=1
                        #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                        if "c" in regroupements:
                            if "a" in regroupements:
                                contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                occurences[variante+"_global_"+sexe]+=1
                                if not re.search("\?",contexte):
                                    occurences[variante+"_"+contexte]+=1
                            else:
                                contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                occurences[variante+"_global_"+sexe]+=1
                                occurences[variante+"_"+contexte]+=1
                        else:
                            if "a" in regroupements:
                                contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                if not re.search("\?",contexte):
                                    occurences[variante+"_"+contexte]+=1
                            else:
                                contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                occurences[variante+"_"+contexte]+=1
                        # ajuster le total
                        occurences[variante + "_global"] = sum(
                            value for key, value in occurences.items() if key.startswith(
                                variante + "_") and key != variante + "_global")
    elementcourant+=1

""" extraction_tu(root,fichier,nouvelleligne,timecodes,occurences, regroupements)
    Cette fonction extrait toutes les occurrences de "tu" dans les fichiers
    et indique si le u est réalisé ou non
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""
def extraction_tu(root,nouvelleligne,timecodes,occurences,regroupements):
        #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on cherches tous les instances de tu dans les tours de paroles
                instances=re.findall("\\b(t\(u\)|tu)[\s|.?]",tourdeparole)
                for instance in instances:
                    if re.search ("t\(u\)",instance):
                        variante="t-u"
                    elif re.search("tu",instance):
                        variante="tu"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_"+contexte]+=1
                    occurences[variante + "_global"] = sum(value for key, value in occurences.items() if key.startswith(
                        variante + "_") and key != variante + "_global")
    elementcourant+=1

""" extraction_I_dans_il(root,fichier,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction extrait toutes les occurences de "il/ils" dans les fichiers
    et indique si le mot entier est réalisé ou si seulement le i initial l'est
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""


def extraction_I_dans_il(root,nouvelleligne,timecodes,occurences,regroupements):
            #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on cherches tous les instances de ils dans les tours de paroles
                instances=re.findall("(?<!\()\\b(i\(l\)s?|ils?)\W",tourdeparole)
                for instance in instances:
                    if re.search("i\(l\)s",instance):
                        variante="i-ls"
                    elif re.search("ils",instance):
                        variante="ils"
                    elif re.search("i\(l\)",instance):
                        variante="i-l"
                    elif re.search("il",instance):
                        variante="il"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variante + "_global"] = sum(value for key, value in occurences.items() if key.startswith(
                        variante + "_") and key != variante + "_global")
    elementcourant+=1

""" extraction_il_complet(root,fichier,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction extrait toutes les occurences de "il/ils" dans les fichiers
    et indique si le mot est réalisé ou non
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""

def extraction_il_complet(root,nouvelleligne,timecodes,occurences,regroupements):
                #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on cherches tous les instances de ils dans les tours de paroles
                instances=re.findall("(\(ils?\)|\\bils?\\b(?!\)))",tourdeparole)
                for instance in instances:
                    if re.search("\(ils\)",instance):
                        variante="ils-suppr"
                    elif re.search("ils",instance):
                        variante="ils-produit"
                    elif re.search("\(il\)",instance):
                        variante="il-suppr"
                    elif re.search("il",instance):
                        variante="il-produit"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_"+contexte]+=1
                            #ajuster le total
                    occurences[variante + "_global"] = sum(value for key, value in occurences.items() if key.startswith(
                        variante + "_") and key != variante + "_global")
    elementcourant+=1

""" extraction_schwa(root,fichier,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction extrait tous les contextes ou un e pourrait être remplacée par un schwa
    et indique si c'est le cas ou non
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""

def extraction_schwa(root,nouvelleligne,timecodes,occurences,regroupements):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1
    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les schwa dans chaque tour de parole
                instances=re.findall("\\b([j|c|d|l|m|n|s|t]\(e\)|[j|c|d|l|m|n|s|t]e|que|qu\(e\))[\s|.?]",tourdeparole)
               # on parcourt les instances
                for instance in instances:

                    if "b" in regroupements:
                        if re.search("\we",instance):
                            variante="e-produit"
                        elif re.search("\w\(e\)",instance):
                            variante="e-suppr"
                    else:
                        if re.search("je",instance):
                            variante="je"
                        elif re.search("j\(e\)",instance):
                            variante="j-e"
                        elif re.search("ce",instance):
                            variante="ce"
                        elif re.search("c\(e\)",instance):
                            variante="c-e"
                        elif re.search("de",instance):
                            variante="de"
                        elif re.search("d\(e\)",instance):
                            variante="d-e"
                        elif re.search("le",instance):
                            variante="le"
                        elif re.search("l\(e\)",instance):
                            variante="l-e"
                        elif re.search("me",instance):
                            variante="me"
                        elif re.search("m\(e\)",instance):
                            variante="m-e"
                        elif re.search("ne",instance):
                            variante="ne"
                        elif re.search("n\(e\)",instance):
                            variante="n-e"
                        elif re.search("se",instance):
                            variante="se"
                        elif re.search("s\(e\)",instance):
                            variante="s-e"
                        elif re.search("te",instance):
                            variante="te"
                        elif re.search("t\(e\)",instance):
                            variante="t-e"
                        elif re.search("que",instance):
                            variante="que"
                        elif re.search("qu\(e\)",instance):
                            variante="qu-e"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            occurences[variante+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variante + "_global"] = sum(value for key, value in occurences.items() if key.startswith(
                        variante + "_") and key != variante + "_global")
    elementcourant+=1

""" extraction_rl(root,fichier,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction extrait tous les mots se terminant en -re ou -le
    et indique si cette terminaison est réalisée ou non
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""

def extraction_rl(root,nouvelleligne,timecodes,occurences,regroupements):
   #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1


    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les rl dans chaque tour de parole
                instances=re.findall("\\b[a-z-âéàçèïêùûîôA-Z]+([b|c|g|p][r|l]es?(?:nt)?|fles?(?:nt)?|[d|t|v]re?(?:nt)?|[b|c|g|p]\([r|l]es?n?t?\)|f\(les?(?:nt)?\)|[d|t|v]\(re?(?:nt)?\))[\s|.?]",tourdeparole)
                for instance in instances:
                    if re.search("bres?n?t?",instance):
                        variante="bre"
                    elif re.search("b\(res?n?t?\)",instance):
                        variante="b-re"
                    elif re.search("bles?n?t?",instance):
                        variante="ble"
                    elif re.search("b\(les?n?t?\)",instance):
                        variante="b-le"
                    elif re.search("cres?n?t?",instance):
                        variante="cre"
                    elif re.search("c\(res?n?t?\)",instance):
                        variante="c-re"
                    elif re.search("cles?n?t?",instance):
                        variante="cle"
                    elif re.search("c\(les?n?t?\)",instance):
                        variante="c-le"
                    elif re.search("dres?n?t?",instance):
                        variante="dre"
                    elif re.search("d\(res?n?t?\)",instance):
                        variante="d-re"
                    elif re.search("tres?n?t?",instance):
                        variante="tre"
                    elif re.search("t\(res?n?t?\)",instance):
                        variante="t-re"
                    elif re.search("fles?n?t?",instance):
                        variante="fle"
                    elif re.search("f\(les?n?t?\)",instance):
                        variante="f-le"
                    elif re.search("gres?n?t?",instance):
                        variante="gre"
                    elif re.search("g\(res?n?t?\)",instance):
                        variante="g-re"
                    elif re.search("gles?n?t?",instance):
                        variante="gle"
                    elif re.search("g\(les?n?t?\)",instance):
                        variante="g-le"
                    elif re.search("pres?n?t?",instance):
                        variante="pre"
                    elif re.search("p\(res?n?t?\)",instance):
                        variante="p-re"
                    elif re.search("ples?n?t?",instance):
                        variante="ple"
                    elif re.search("p\(les?n?t?\)",instance):
                        variante="p-le"
                    elif re.search("vres?n?t?",instance):
                        variante="vre"
                    elif re.search("v\(res?n?t?\)",instance):
                        variante="v-re"
                    if "b" in regroupements:
                        if variante in ["bre","cre","dre","tre","gre","pre","vre"]:
                            variante="r-produit"
                        elif variante in ["b-re","c-re","d-re","t-re","g-re","p-re","v-re"]:
                            variante="r-suppr"
                        elif variante in ["ble","cle","fle","gle","ple"]:
                            variante="l-produit"
                        elif variante in ["b-le","c-le","f-le","g-le","p-le"]:
                            variante="l-suppr"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            occurences[variante+"_"+contexte]+=1
                    #ajuster le total
                    occurences[variante + "_global"] = sum(value for key, value in occurences.items() if key.startswith(
                        variante + "_") and key != variante + "_global")
    elementcourant+=1

"""	extraction_onomatopee(root,fichier,nouvelleligne,timecodes,occurences,regroupements,variable)
    Cette fonction extrait toutes les onomatopées et indique leur forme
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""

def extraction_onomatopee(root,nouvelleligne,timecodes,occurences,regroupements,variable):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1


    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les onomatopées dans chaque tour de parole
                instances=re.findall("([a-z-éàçèïïêûîôA-Z']*@o)",tourdeparole)
                for instance in instances:
                    if "c" not in regroupements:
                        occurences[variable+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            occurences[variable+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variable + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variable + "_") and key != variable + "_global")

    elementcourant+=1

"""	extraction_mots_etrangers(root,fichier,nouvelleligne,timecodes,occurences,regroupements,variable)
    Cette fonction extrait tous les mots étrangers et indique leur forme
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""


def extraction_mots_etrangers(root,nouvelleligne,timecodes,occurences,regroupements,variable):
        #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les mots étrangers dans chaque tour de parole
                instances=re.findall("([a-z-éàçèïïêûîôA-Z']*@s)",tourdeparole)
                for instance in instances:
                    if "c" not in regroupements:
                        occurences[variable+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            occurences[variable+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variable + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variable + "_") and key != variable + "_global")
    elementcourant+=1


"""	extraction_mots_enfantins(root,fichier,nouvelleligne,timecodes,occurences,regroupements,variable)
    Cette fonction extrait tous les mots enfantins et indique leur forme
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv

"""


def extraction_mots_enfantins(root,nouvelleligne,timecodes,occurences,regroupements,variable):
            #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1
    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les mots enfantins dans chaque tour de parole
                instances=re.findall("([a-z-éàçèïïêûîôA-Z']*@c)",tourdeparole)
                for instance in instances:
                    if "c" not in regroupements:
                        occurences[variable+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            occurences[variable+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variable + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variable + "_") and key != variable + "_global")
    elementcourant+=1


""" extraction_liaisons_fausses(root,fichier,nouvelleligne,timecodes,occurences,regroupements,variable)
    Cette fonction extrait tous les cas de fausses liaisons dans le fichier
    et indique leur forme ainsi que leur contexte
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv


"""

def extraction_liaisons_fausses(root,nouvelleligne,timecodes,occurences,regroupements,variable):
        #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1


    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les fausses liaisons dans chaque tour de parole
                instances=re.findall("([a-z-âéàçèïêùûîôA-Z\.\?]+\s\[\w\][a-z-âéàçèïêùûîôA-Z\.\?]+)",tourdeparole)
                for instance in instances:
                    if "c" not in regroupements:
                        occurences[variable+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            occurences[variable+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variable + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variable + "_") and key != variable + "_global")
    elementcourant+=1

"""	extraction_oui_ouais(root,fichier,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction extrait et sépare toutes les occurrences des mots
    "oui" et "ouais"
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""

def extraction_oui_ouais(root,nouvelleligne,timecodes,occurences,regroupements):
            #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les occurences de oui/ouais dans chaque tour de parole
                instances=re.findall("\\b(oui|ouais|mouais)\\b",tourdeparole)
                for instance in instances:
                    if re.search ("oui",instance):
                        variante="oui"
                    elif re.search("mouais",instance):
                        variante="mouais"
                    elif re.search("ouais",instance):
                        variante="ouais"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variante + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variante + "_") and key != variante + "_global")
    elementcourant+=1

"""extraction_non_nan(root,fichier,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction extrait et sépare toutes les occurrences des mots
    "non" et "nan"
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""

def extraction_non_nan(root,nouvelleligne,timecodes,occurences,regroupements):
                #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1


    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les occurences de non/nan dans chaque tour de parole
                instances=re.findall("\\b(non|nan)\\b",tourdeparole)
                for instance in instances:
                    if re.search ("non",instance):
                        variante="non"
                    elif re.search("nan",instance):
                        variante="nan"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variante + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variante + "_") and key != variante + "_global")
    elementcourant+=1


""" extraction_on_nous(root,fichier,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction extrait et sépare toutes les occurrences des mots
    "on" et "nous" en dehors de l'expression "nous on" ainsi que toutes les occurences
    de cette expression
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""
def extraction_on_nous(root,nouvelleligne,timecodes,occurences,regroupements):
                    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les occurences de on/nous dans chaque tour de parole
                instances=re.findall("\\b(nous\\b(?!\son)|(?<!nous\s)on\\b|nous on)\\b",tourdeparole)
                for instance in instances:
                    if re.search ("nous on",instance):
                        variante="nous-on"
                    elif re.search("nous",instance):
                        variante="nous"
                    elif re.search("on",instance):
                        variante="on"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variante + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variante + "_") and key != variante + "_global")
    elementcourant+=1

""" extraction_negation(root,fichier,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction extrait tous les contextes de négation repérés auparavant
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""

def extraction_negation(root,nouvelleligne,timecodes,occurences,regroupements):
                        #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Négation":
            break
        else:
            position+=1


    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les négations dans chaque tour de parole
                instances=re.findall("\\b([a-z-âéàçèïêùûîôA-Z\.\?]+\[NN0\]|[a-z-âéàçèïêùûîôA-Z\.\?]+\[NN1\])",tourdeparole)
                for instance in instances:
                    if re.search ("pas\[NN0\]",instance):
                        variante="pas[NN0]"
                    elif re.search("pas\[NN1\]",instance):
                        variante="pas[NN1]"
                    elif re.search("jamais\[NN0\]",instance):
                        variante="jamais[NN0]"
                    elif re.search("jamais\[NN1\]",instance):
                        variante="jamais[NN1]"
                    elif re.search("personne\[NN0\]",instance):
                        variante="personne[NN0]"
                    elif re.search("personne\[NN1\]",instance):
                        variante="personne[NN1]"
                    elif re.search("rien\[NN0\]",instance):
                        variante="rien[NN0]"
                    elif re.search("rien\[NN1\]",instance):
                        variante="rien[NN1]"
                    elif re.search("aucunes\[NN0\]",instance):
                        variante="aucunes[NN0]"
                    elif re.search("aucunes\[NN1\]",instance):
                        variante="aucunes[NN1]"
                    elif re.search("aucuns\[NN0\]",instance):
                        variante="aucuns[NN0]"
                    elif re.search("aucuns\[NN1\]",instance):
                        variante="aucuns[NN1]"
                    elif re.search("aucune\[NN0\]",instance):
                        variante="aucune[NN0]"
                    elif re.search("aucune\[NN1\]",instance):
                        variante="aucune[NN1]"
                    elif re.search("aucun\[NN0\]",instance):
                        variante="aucun[NN0]"
                    elif re.search("aucun\[NN1\]",instance):
                        variante="aucun[NN1]"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements,reduits=True)
                            occurences[variante+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variante + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variante + "_") and key != variante + "_global")
    elementcourant+=1

""" extraction_negation_pas(root,fichier,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction extrait tous les contextes de négation en "pas" repérés auparavant
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        fichier: le fichier .csv que l'on est en train de créer (File)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements: le type de regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv"""

def extraction_negation_pas(root,nouvelleligne,timecodes,occurences,regroupements):
                            #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Négation" and re.search("PAS",child.attrib.get("TIER_ID")):
            break
        else:
            position+=1

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les négations en pas dans chaque tour de parole
                instances=re.findall("\\b([a-z-âéàçèïêùûîôA-Z\.\?]+\[NN0\]|[a-z-âéàçèïêùûîôA-Z\.\?]+\[NN1\])",tourdeparole)
                for instance in instances:
                    if re.search ("pas\[NN0\]",instance):
                        variante="pas[NN0]"
                    elif re.search("pas\[NN1\]",instance):
                        variante="pas[NN1]"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variante + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variante + "_") and key != variante + "_global")
    elementcourant+=1


""" extraction_tokens(root,nouvelleligne,timecodes,occurences,regroupements,variable)
    Cette fonction extrait tous les mots
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: tableau des occurences
        variable: la variable à traiter
        regroupements : regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv"""

def extraction_tokens(root,nouvelleligne,timecodes,occurences,regroupements,variable):
        #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1


    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on supprimes les mots etrangers,enfantins et les onomatopées
                tourdeparole=re.sub("(xxx|ooo|aaa|sss)","",tourdeparole)
                #on cherches tous les tokens dans chaque tour de parole
                instances=re.findall("(aujourd'hui|d'accord|d'abord|d'ailleurs|rock'n'roll|quelqu'un|c'est-à-dire|[a-z-âàéàçèïêùûîôA-Z\d]+)",tourdeparole)
                for instance in instances:
                    if "c" not in regroupements:
                        occurences[variable+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            occurences[variable+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_"+contexte]+=1
                    # ajuster le total
                    occurences[variable + "_global"] = sum(
                        value for key, value in occurences.items() if key.startswith(
                            variable + "_") and key != variable + "_global")
    elementcourant+=1


""" extraction_types(root,nouvelleligne,timecodes,occurences,types,regroupements,variable)
    Cette fonction compte le nombre des types
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: tableau des occurences
        types: tableau contenant tous les types rencontrés dans les fichiers de la personne (Dict)
        variable: la variable à traiter
        regroupements : regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv"""

def extraction_types(root,nouvelleligne,timecodes,occurences,types,regroupements,variable):
            #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1
    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                #{cle_global=1, cle_contexte1=1, cle_contexte2=1}
                #copie profonde
                tourdeparole=copy.deepcopy(ele.text)
                    #on supprime les onomatopées, mots étrangers et enfantins dans chaque tour de parole
                tourdeparole=re.sub("(xxx|ooo|aaa|sss)","",tourdeparole)
                instances=re.findall("(aujourd'hui|d'accord|d'abord|d'ailleurs|rock'n'roll|quelqu'un|c'est-à-dire|[a-z-âàéàçèïêùûîôA-Z\d]+)",tourdeparole)
                for instance in instances:
                    """if instance+"_global" not in types.keys():
                        occurences[variable+"_global"]+=1
                        types[instance+"_global"]=1
                    #on récupère les bornes temporelles afin de trouver le contexte de chaque tour de parole
                    if "a" in regroupements:
                        contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                        if not re.search("\?",contexte):
                            if instance+"_"+contexte not in types.keys():
                                occurences[variable+"_"+contexte]+=1
                                types[instance+"_"+contexte]=1
                    else:
                        contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                        if instance+"_"+contexte not in types.keys():
                                occurences[variable+"_"+contexte]+=1
                                types[instance+"_"+contexte]=1"""
                    #TOMOD
                    if "c" not in regroupements:
                        if instance+"_global" not in types.keys():
                            occurences[variable+"_global"]+=1
                            types[instance+"_global"]=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if instance+"_global_"+sexe not in types.keys():
                                occurences[variable+"_global_"+sexe]+=1
                                types[instance+"_global_"+sexe]=1
                            if not re.search("\?",contexte):
                                if instance+"_"+contexte not in types.keys():
                                    occurences[variable+"_"+contexte]+=1
                                    types[instance+"_"+contexte]=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if instance+"_global_"+sexe not in types.keys():
                                occurences[variable+"_global_"+sexe]+=1
                                types[instance+"_global_"+sexe]=1
                            if instance+"_"+contexte not in types.keys():
                                occurences[variable+"_"+contexte]+=1
                                types[instance+"_"+contexte]=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                if instance+"_"+contexte not in types.keys():
                                    occurences[variable+"_"+contexte]+=1
                                    types[instance+"_"+contexte]=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if instance+"_"+contexte not in types.keys():
                                    occurences[variable+"_"+contexte]+=1
                                    types[instance+"_"+contexte]=1
                        # ajuster le total
                        occurences[instance + "_global"] = sum(
                            value for key, value in occurences.items() if key.startswith(
                                instance + "_") and key != instance + "_global")
    elementcourant+=1




""" extraction_rtt(root,nouvelleligne,timecodes,occurences,types,regroupements,variable,limit,limit_value)
    Cette fonction permet de calculer le rtt
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: tableau des occurences
        types: tableau contenant tous les types rencontrés dans les fichiers de la personne (Dict)
        variable: la variable à traiter
        limit: quelle limite appliquer (Int)
            0=pas de limite
            10= limite énonces
            20= limite mots
            30= limite temps de parole (en secondes)
        limit_value: la valeur de la limite (String)
       regroupements : regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv"""

def extraction_rtt(root,nouvelleligne,timecodes,occurences,types,regroupements,variable,limit,limit_value):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1

    nb_tokens_vus=0
    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                if limit==20 and nb_tokens_vus>=limit_value:
                    break
                tourdeparole=copy.deepcopy(ele.text)
                #on supprime les onomatopées, mots étrangers et enfantins dans chaque tour de parole
                tourdeparole=re.sub("(xxx|ooo|aaa|sss)","",tourdeparole)
                instances=re.findall("(aujourd'hui|d'accord|d'abord|d'ailleurs|rock'n'roll|quelqu'un|c'est-à-dire|[a-z-âàéàçèïêùûîôA-Z\d]+)",tourdeparole)
                for instance in instances:
                    nb_tokens_vus+=1
                    if "c" not in regroupements:
                        occurences[variable+"_global"]+=1
                        if instance+"_global" not in types.keys():
                            types[instance+"_global"]=1
                            if variable+"_global" in types.keys():
                                types[variable+"_global"]+=1
                            else:
                                types[variable+"_global"]=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            if instance+"_global_"+sexe not in types.keys():
                                types[instance+"_global_"+sexe]=1
                                if variable+"_global_"+sexe in types.keys():
                                    types[variable+"_global_"+sexe]+=1
                                else:
                                    types[variable+"_global_"+sexe]=1
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                                if instance+"_"+contexte not in types.keys():
                                    types[instance+"_"+contexte]=1
                                    if variable+"_"+contexte in types.keys():
                                        types[variable+"_"+contexte]+=1
                                    else:
                                        types[variable+"_"+contexte]=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_global_"+sexe]+=1
                            if instance+"_global_"+sexe not in types.keys():
                                types[instance+"_global_"+sexe]=1
                                if variable+"_global_"+sexe in types.keys():
                                    types[variable+"_global_"+sexe]+=1
                                else:
                                    types[variable+"_global_"+sexe]=1
                            occurences[variable+"_"+contexte]+=1
                            if instance+"_"+contexte not in types.keys():
                                types[instance+"_"+contexte]=1
                                if variable+"_"+contexte in types.keys():
                                    types[variable+"_"+contexte]+=1
                                else:
                                    types[variable+"_"+contexte]=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variable+"_"+contexte]+=1
                                if instance+"_"+contexte not in types.keys():
                                    types[instance+"_"+contexte]=1
                                    if variable+"_"+contexte in types.keys():
                                        types[variable+"_"+contexte]+=1
                                    else:
                                        types[variable+"_"+contexte]=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variable+"_"+contexte]+=1
                            if instance+"_"+contexte not in types.keys():
                                types[instance+"_"+contexte]=1
                                if variable+"_"+contexte in types.keys():
                                    types[variable+"_"+contexte]+=1
                                else:
                                    types[variable+"_"+contexte]=1

                        # changer le total en affectant la somme de tous les variable_contexte
                        occurences[variable + "_global"] = sum(
                            value for key, value in occurences.items() if key.startswith(
                                variable + "_") and key != variable + "_global")

                        types[variable + "_global"] = sum(value for key, value in types.items() if key.startswith(
                                variable + "_") and key != variable + "_global")






    elementcourant += 1
    # On invalide des echantillons dont le total est inferieur à la limite




""" extraction_lme(root,nouvelleligne,timecodes,occurences,regroupements,variable,limit,limit_value)
    Cette fonction permet de calculer la lme
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: tableau des occurences
        variable: la variable à traiter
        regroupements : regroupements à appliquer (String)
        limit: quelle limite appliquer (Int)
            0=pas de limite
            10= limite énonces
            20= limite mots
            30= limite temps de parole (en secondes)
        limit_value: la valeur de la limite (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv"""
def extraction_lme(root,nouvelleligne,timecodes,occurences,regroupements,variable,limit,limit_value):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1

    elementcourant=0
    nb_enonces_vus=0
    nb_tokens_vus=0
    duree_totale=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on supprime les mots étrangers
                enonces=re.findall("(.*?)(?:\.|\?)",tourdeparole)
                limite_temps=[c.attrib.get("TIME_SLOT_REF1"),c.attrib.get("TIME_SLOT_REF2")]
                for time in timecodes.keys():
                    if limite_temps[0] in timecodes[time]:
                        debut=int(time)
                    if limite_temps[1] in timecodes[time]:
                        fin=int(time)
                # conversion en seconde
                duree_totale+=int(fin-debut)
                occurences["duree_avec_limite"] = duree_totale
                for enonce in enonces:
                    #ne s'arrêtera pas au milieu d'un énoncé
                    if limit==10 and nb_enonces_vus>=limit_value:
                        break
                    if limit==20 and nb_tokens_vus>=limit_value:
                        break
                    if limit==30 and duree_totale>=limit_value:
                        break
                    nb_enonces_vus+=1
                    #On exclut tout énonce comportant au moins une marque xxx
                    if not re.search("xxx",enonce):
                        #On comptabilise les tokens
                        instances=re.findall("(aujourd'hui|d'accord|d'abord|d'ailleurs|rock'n'roll|quelqu'un|c'est-à-dire|[a-z-âàéàçèïêùûîôA-Z\d]+)",enonce)
                        for instance in instances:
                            if "c" not in regroupements:
                                nb_tokens_vus += 1
                            #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                            if "c" in regroupements:
                                if "a" in regroupements:
                                    contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                    nb_tokens_vus+=1
                                    occurences["tokens_global_"+sexe]+=1
                                    if not re.search("\?",contexte):
                                        occurences["tokens_"+contexte]+=1
                                else:
                                    contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                    nb_tokens_vus+=1
                                    occurences["tokens_global_"+sexe]+=1
                                    occurences["tokens_"+contexte]+=1
                            else:
                                if "a" in regroupements:
                                    contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                    if not re.search("\?",contexte):
                                        occurences["tokens_"+contexte]+=1
                                else:
                                    contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                    occurences["tokens"+"_"+contexte]+=1
                        if "c" not in regroupements:
                            nb_tokens_vus +=1
                        #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                        if "c" in regroupements:
                            if "a" in regroupements:
                                contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                occurences["enonces_global_"+sexe]+=1
                                if not re.search("\?",contexte):
                                    occurences["enonces_"+contexte]+=1
                            else:
                                contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                occurences["enonces_global_"+sexe]+=1
                                occurences["enonces_"+contexte]+=1
                        else:
                            if "a" in regroupements:
                                contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                if not re.search("\?",contexte):
                                    occurences["enonces_"+contexte]+=1
                            else:
                                contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                occurences["enonces_"+contexte]+=1
                        # Deux manières à ajuster le total dans les fichiers selon si y a de la limite
                        # En cas de refroupement pas de limite
                        if not limit:
                            occurences[variable + "_global"] = sum(
                                value for key, value in occurences.items() if key.startswith(
                                    variable + "_") and key != variable + "_global")
                        # En cas de limite
                        if limit:
                            occurences["enonces_global"] = nb_enonces_vus
                            occurences["tokens_global"] = nb_tokens_vus



    # On invalide des echantillons dont le total est inferieur à la limite
    if limit == 10 and nb_enonces_vus < limit_value:
        occurences["enonces_global"] = "NA"
        occurences["tokens_global"] = "NA"
    elif limit == 20 and nb_tokens_vus < limit_value:
        occurences["enonces_global"] = "NA"
        occurences["tokens_global"] = "NA"
    elif limit == 30 and duree_totale < limit_value:
        occurences["enonces_global"] = "NA"
        occurences["tokens_global"] = "NA"
    else:
        occurences["enonces_global"] = nb_enonces_vus
        occurences["tokens_global"] = nb_tokens_vus

    elementcourant+=1


""" extraction_cat_gram(root,nouvelleligne,timecodes,occurences,variable,regroupements)
    Cette fonction extrait la catégorie grammaticale de tous les mots
    étiquettés par TreeTagger
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecode: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: tableau des occurences
        variable: la variable à traiter
        regroupements : regroupements à appliquer (String)
    Sorties:
        Ajout de nouvelles lignes au fichier .csv
"""
def extraction_cat_gram(root,nouvelleligne,timecodes,occurences,variable,regroupements):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Tagging":
            break
        else:
            position+=1

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                    #on recherche les onomatopées dans chaque tour de parole
                instances=re.findall("(aujourd'hui|d'accord|d'abord|d'ailleurs|rock'n'roll|quelqu'un|c'est-à-dire|[a-z-âàéàçèïêùûîôA-Z\d]+)",tourdeparole)
                for instance in instances:
                    if "c" not in regroupements:
                        occurences["tokens_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences["tokens_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences["tokens_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences["tokens_global_"+sexe]+=1
                            occurences["tokens_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences["tokens_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences["tokens_"+contexte]+=1

                instances=re.findall("[a-z-âéàçèïêùûîôA-Z\.\?]+\|([a-z-âéàçèïêùûîôA-Z\.\?]+)(?::[a-z-âéàçèïêùûîôA-Z\.\?]+)?\|[a-z-âéàçèïêùûîôA-Z\.\?]+",tourdeparole)
                for instance in instances:
                    if re.search(variable,instance):
                        if "c" not in regroupements:
                            occurences["instances_global"]+=1
                        #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                        if "c" in regroupements:
                            if "a" in regroupements:
                                contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                occurences["instances_global_"+sexe]+=1
                                if not re.search("\?",contexte):
                                    occurences["instances_"+contexte]+=1
                            else:
                                contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                occurences["instances_global_"+sexe]+=1
                                occurences["instances_"+contexte]+=1
                        else:
                            if "a" in regroupements:
                                contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                if not re.search("\?",contexte):
                                    occurences["instances_"+contexte]+=1
                            else:
                                contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                                occurences["instances_"+contexte]+=1

                        # ajouster le total dans les fichiers regroupés
                        occurences["instances_global"] = sum(
                            value for key, value in occurences.items() if key.startswith(
                                "instances_") and key != "instances_global")

    elementcourant+=1

"""

    extraction_temps(root,nouvelleligne,timecodes,occurences,regroupements,variable)
        Cette fonction comptabilise le temps de parole en fonction du contexte
        Entrées:
        root: racine d'un arbre XML (ElementTree)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        variable: la variable à étudier (String)
        regroupements : regroupements à appliquer (String)
    Sorties:
        Comptage du temps de parole en fonction du contexte inscrit dans le
        tableau des occurences

"""

def extraction_temps(root,nouvelleligne,timecodes,occurences,regroupements,variable):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1


    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                #On récupère les identifiants des bornes temporelles
                limite_temps=[c.attrib.get("TIME_SLOT_REF1"),c.attrib.get("TIME_SLOT_REF2")]
                for time in timecodes.keys():
                    if limite_temps[0] in timecodes[time]:
                        debut=int(time)
                    if limite_temps[1] in timecodes[time]:
                        fin=int(time)
                duree_enonce=fin-debut
                if "c" in regroupements:
                    if "a" in regroupements:
                        contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                        occurences[variable+"_global_"+sexe]+=duree_enonce
                        if not re.search("\?",contexte):
                            occurences[variable+"_"+contexte]+=duree_enonce
                    else:
                        contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                        occurences[variable+"_global_"+sexe]+=duree_enonce
                        occurences[variable+"_"+contexte]+=duree_enonce
                else:
                    if "a" in regroupements:
                        contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                        if not re.search("\?",contexte):
                            occurences[variable+"_"+contexte]+=duree_enonce
                    else:
                        contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                        occurences[variable+"_"+contexte]+=duree_enonce
                # changer le total en affectant la somme de tous les variable_contexte
                occurences[variable + "_global"] = sum(
                    value for key, value in occurences.items() if key.startswith(
                        variable + "_") and key != variable + "_global")

    elementcourant+=1

""" extraction_liaisons_facultatives(root,nouvelleligne,timecodes,occurences,regroupements)
    Cette fonction compte toutes les occurrences des marqueurs de liaisons
    facultatives dans les fichiers
    Entrées:
        root: racine d'un arbre XML (ElementTree)
        nouvelleligne: la nouvelle ligne que l'on souhaite ajouter au fichier (Array)
        timecodes: la liste des bornes temporelles récupérées auparavant (Dict)
        occurences: le tableau qui comptabilise toutes les occurences en foncton du contexte (Dict)
        regroupements : regroupements à appliquer (String)
        traitement_liaison: Indique si il faut lancer le traitement spécial des liaisons facultatives (Boolean)
        liaison_list: Indique le mot1 et mot2 choisis par l'utilisateur pour le traitement spécial des liaisons facultatives (List)
    Sorties:
        Ajout du nombre d'occurences de chaque variable en fonction du contexte
        au tableau des occurences
"""

def extraction_liaisons_facultatives(root,nouvelleligne,timecodes,occurences,regroupements,traitement_liaison,liaison_list):
    #on met de coté la nouvelle ligne crée auparavant
    lignebase=nouvelleligne
    positionactivite,positioninterlocuteur,positionsituation,positionsexe=trouver_positions(root)
    #on récupère les lignes du fichier eaf dont on a besoin
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="LF_LEX_Codee":
            break
        else:
            position+=1

    elementcourant=0
    #on parcourt tous les tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                tourdeparole=copy.deepcopy(ele.text)
                #on recherche les occurences des marqueurs de liaison dans chaque tour de parole
                if traitement_liaison:
                    #Pas de mot1, seulement mot2 (mot1 est vide)
                    if liaison_list[0]=="":
                        instances=re.findall("\[LF[1|3]\]\s"+liaison_list[1]+"['.!\s]",tourdeparole)
                    #Pas de mot2, seulement mot1 (mot2 est vide)
                    elif liaison_list[1]=="":
                        instances=re.findall("['.!\s]?"+liaison_list[0]+"\s\[LF[1|3]\]",tourdeparole)
                    #Les deux mots (aucun n'est vide)
                    else:
                        instances=re.findall("['.!\s]?"+liaison_list[0]+"\s\[LF[1|3]\]\s"+liaison_list[1]+"['.!\s]",tourdeparole)
                else:
                    instances=re.findall("\[LF[1|3]\]",tourdeparole)
                for instance in instances:
                    #Pour chaque occurence, on vérifie le type de marqueur
                    if re.search ("\[LF1\]",instance):
                        variante="LF1"
                    elif re.search("\[LF3\]",instance):
                        variante="LF3"
                    if "c" not in regroupements:
                        occurences[variante+"_global"]+=1
                    #on fait appel au fonction nécessaire selon si on a un regroupement ou pas
                    if "c" in regroupements:
                        if "a" in regroupements:
                            contexte,sexe=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte,sexe=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_global_"+sexe]+=1
                            occurences[variante+"_"+contexte]+=1
                    else:
                        if "a" in regroupements:
                            contexte=trouver_contexte_regroupements(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            if not re.search("\?",contexte):
                                occurences[variante+"_"+contexte]+=1
                        else:
                            contexte=trouver_contexte(root,timecodes,c,positionactivite,positioninterlocuteur,positionsituation,positionsexe,regroupements)
                            occurences[variante+"_"+contexte]+=1
                    # changer le total en affectant la somme de tous les variable_contexte 
                    occurences[variante + "_global"] = sum(value for key, value in occurences.items() if key.startswith(
                        variante + "_") and key != variante + "_global")

    elementcourant+=1
