#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import xml.etree.ElementTree as ET
import copy
import os
import datas
import regex as regexp

""" LF_LEX(tree)
    Cette fonction permet d'ajouter les lignes LF_LEX et LF_LEX_Codee à
    un arbre XML
    Entrée:
        tree: Arbre XML enrichi (ElementTree)
    Sorties:
        tree: Arbre XML avec les lignes LF_LEX et LF_LEX_Codee ajoutées
"""

def LF_LEX(tree):
    #On récupère la racine de l'arbre XML
    root=tree.getroot()
    #On récupère la position de la ligne sur laquelle on veut travailler
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1
    #On crée une copie de cette ligne
    line=copy.deepcopy(root[position])
    #On insère la copie dans l'arbre
    root.insert(position+1,line)
    position+=1
    #On change l'identifiant de la ligne copiée ainsi que celui de toutes les annotations de la ligne
    root[position].set("LINGUISTIC_TYPE_REF","LF_LEX")
    for child in root[position]:
        for c in child:
            new_id=re.sub('_nettoye','',c.attrib.get("ANNOTATION_ID"))
            c.set("ANNOTATION_ID",new_id+"_LF_LEX")
    new_id=re.sub('_nettoye','',root[position].attrib.get("TIER_ID"))
    root[position].set("TIER_ID",new_id+"_LF_LEX")
    #On parcourt chacun des tours de parole

    for child in root[position]:
        for c in child:
            for ele in c:
                # Activation du débug
                debug = False
                for toDebug in datas.toDebug:
                    if re.search(toDebug, ele.text):
                        debug = True
                # On recherche tous les contextes de liaisons possibles
                if re.search(datas.patternRegexp,ele.text):
                    if debug:
                        print("\n#####################\n" + ele.text)
                    occurrences=regexp.findall(datas.patternRegexp, ele.text, overlapped=True)
                    # Pour chaque contexte, on récupère les trois mots avant et après le contexte
                    atLeastOneMatch=False
                    for occurrence in occurrences:
                        # On définit une variable qui nous indique si le contexte est valide ou non
                        contexte_valide=True
                        # On récupère le mot1 et le mot2 de liaison
                        mot1=occurrence[1]
                        mot2=occurrence[3]
                        if debug:
                            print("mot1 > " + mot1)
                            print("mot2 > " + mot2)
                        # le mot1 ne provoque pas un contexte d'enchaînement
                        if re.search(datas.patternEnchainement, mot1):
                            if debug:
                                print("mot1 in patternEnchainement")
                            contexte_valide=False
                        # le mot1 ne provoque pas un contexte d'enchaînement (est un amalgame mot + apostrophe + ils/elles/on/en)
                        if re.search(datas.patternApostrophePronom, mot1):
                            if debug:
                                print("mot1 in patternApostrophePronom")
                            contexte_valide=False
                        # le mot1 n'appartient pas a la liste des déterminants pouvant provoquer une LO
                        if contexte_valide and mot1 in datas.list1b:
                            if debug:
                                print("mot1 in list1b")
                            contexte_valide=False
                        # le mot1 n'est pas en majuscules
                        if contexte_valide and mot1.isupper():
                            contexte_valide=False
                            if debug:
                                print("mot1 is upper")
                        # les mot1 ni les mot2 font partie de la liste de pronoms qui peuvent provoquer une LO
                        if contexte_valide and (mot1 in datas.list1c or mot2 in datas.list1cbis):
                            contexte_valide=False
                            if debug:
                                print("mot1 is list1c ou list1cbis")
                        # le mot1 n'est pas un mot qui rend la liaison impossible ou obligatoire
                        if contexte_valide and mot1 in datas.list1d:
                            if debug:
                                print("mot1 in datas.list1d")
                            contexte_valide=False
                        # les deux mots ne sont pas identiques
                        if contexte_valide and mot1==mot2:
                            contexte_valide=False
                            if debug:
                                print("mot1==mot2")
                        # le mot2 n'est pas un mot rendant la liaison impossible
                        if contexte_valide and mot2 in datas.list1e:
                            contexte_valide=False
                            if debug:
                                print("mot1 in list1e")
                        if contexte_valide and  re.search(datas.pattern1e, mot2):
                            contexte_valide=False
                            if debug:
                                print("mot1 in pattern1e")

                        #On crée une expression régulière nous permettant de récupèrer le mot suivant
                        regex2=occurrence[0]+"[\s']([a-z-âàéàçèïêùûîôA-Z\d]+)"
                        mot3=re.search(regex2,ele.text)
                        #Si il y un mot suivant, on vérifie que la séquence
                        #mot1 mot2 mot3 ne fait pas partie d'une expression figée
                        #imposant ou empêchant la liaison
                        if mot3:
                            mot3=mot3.group(1)
                            if (mot1,mot2,mot3) in datas.list1g:
                                contexte_valide=False
                                if debug:
                                    print("mot1 in list1g")
                        #On vérifie que la séquence mot1 mot2 ne fait pas
                        #partie d'une expression figée imposant ou empêchant la liaison
                        if (mot1,mot2) in datas.list1g:
                            contexte_valide=False
                            if debug:
                                print("mot1 in list1g")
                        #Si le contexte est valide, on ajoute le codage
                        #[LF] entre le mot1 et le mot2
                        if contexte_valide:
                            nouvelle_liaison=mot1+"\g<1>[LF]\g<1>"+mot2
                            regex3=mot1+"([\s'])"+mot2
                            lastText=ele.text
                            ele.text=re.sub(regex3,nouvelle_liaison,ele.text)

                            ## Exclusion des cas avec des polylexicaux en mot1
                            for polylexical in datas.list1h:
                                regexpPolyl = polylexical+"\s\[LF\]"
                                if re.search(regexpPolyl, ele.text):
                                    ele.text=re.sub(regexpPolyl,polylexical,ele.text)
                                    contexte_valide = False



                        #Si le contexte est invalide mais que présence de "vous allez, nous allons, tu vas" suivi de "y", on ajoute le codage
                        #[LF] avant le "y"
                        if contexte_valide == False:
                            for key, value in datas.list1i.items():
                                if re.search(key, ele.text):
                                    ele.text=re.sub(key,value,ele.text)
                                    contexte_valide = True

                        if debug and contexte_valide:
                            print("Contexte Valide : " + ele.text)
    #On récupère l'ensemble des bornes temporelles afin de créer de nouvelles
    #annotations
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
        timecodes[ID]=[time]
    longueur_initiale=len(timecodes)
    #On récupère la ligne LF_LEX que l'on vient de créer
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="LF_LEX":
            break
        else:
            position+=1
    line=copy.deepcopy(root[position])
    #On insère la copie dans l'arbre
    root.insert(position+1,line)
    positioncopie=position+1
    root[positioncopie].set("LINGUISTIC_TYPE_REF","LF_LEX_Codee")
	    #On remplit cette copie d'annotations vides qui seront ensuite remplies
    #et on change l'identifiant de la ligne et des annotations
    for child in root[positioncopie]:
        for c in child:
            new_id=re.sub('_LF_LEX','',c.attrib.get("ANNOTATION_ID"))
            c.set("ANNOTATION_ID",new_id+"_LF_LEX_codee")
            c.set("TIME_SLOT_REF1","#")
            c.set("TIME_SLOT_REF2","#")
            for ele in c:
                ele.text="#"
    new_id=re.sub('_LF_LEX','',root[positioncopie].attrib.get("TIER_ID"))
    root[positioncopie].set("TIER_ID",new_id+"_LF_LEX_codee")
    position_actuelle=0
	#On parcourt la ligne LF_LEX
    for child in root[position]:
        for c in child:
            for ele in c:
                #On récupère les bornes temporelles de chaque tour de parole
                start_time=c.get("TIME_SLOT_REF1")
                start_time_num=timecodes[start_time]
                end_time=c.get("TIME_SLOT_REF2")
                start_time_num=timecodes[end_time]
                #On cherche si il y a des contextes de LF dans le tour de parole
                if re.search("\[LF\]",ele.text):
                    #Si il y a des contextes de LF, on les copie dans une
                    #des bornes vides de la ligne LF_LEX_codee
                    for e in root[positioncopie][position_actuelle]:
                        e.set("TIME_SLOT_REF1",start_time)
                        e.set("TIME_SLOT_REF2",end_time)
                        for elem in e:
                            elem.text=ele.text
                        position_actuelle+=1



    #On crée un nouveau type linguistique en en copiant un autre
    position=0
    for child in root:
        if child.tag=="LINGUISTIC_TYPE" and child.attrib.get("LINGUISTIC_TYPE_ID")=="Négation":
            break
        else:
            position+=1
    newline=copy.deepcopy(root[position])
    #On change l'identifiant de la copie
    newline.set("LINGUISTIC_TYPE_ID","LF_LEX")
    #On ajoute la copie dans l'arborescence XML
    root.insert(position+1,newline)
    position=0
    for child in root:
        if child.tag=="LINGUISTIC_TYPE" and child.attrib.get("LINGUISTIC_TYPE_ID")=="LF_LEX":
            break
        else:
            position+=1
    newline=copy.deepcopy(root[position])
    #On change l'identifiant de la copie
    newline.set("LINGUISTIC_TYPE_ID","LF_LEX_Codee")
    #On ajoute la copie dans l'arborescence XML
    root.insert(position+1,newline)
    position_order=0
    for child in root:
        if child.tag=="TIME_ORDER":
            break
        else:
            position_order+=1
    #On met à jour la liste des bornes temporelles
    for key in timecodes.keys():
        if int(key[2:])>longueur_initiale:
            newtimecode=copy.deepcopy(root[position_order][0])
            newtimecode.set("TIME_SLOT_ID",key)
            newtimecode.set("TIME_VALUE",timecodes[key])
            root[position_order].insert(len(root[position_order]),newtimecode)
    #On efface toutes les annotations vides de la ligne LF_LEX_codee
    for child in root[positioncopie].findall("ANNOTATION"):
        for c in child:
            if c.get("TIME_SLOT_REF1")=="#":
                root[positioncopie].remove(child)
    return tree

""" lancement_LF_LEX(filename)
    Cette fonction permet d'extraire l'arbre XML d'un fichier _VC.eaf
    et de lancer le traitement des liaisons facultatives
    Entrée:
        filename: Chemin d'accès au fichier (String)
    Sorties:
        Création d'un fichier _VD.eaf avec les lignes LF_LEX et LF_LEX_codee
        ajoutées
"""

def lancement_LF_LEX(filename):
    if re.search("_VC", filename):
        # parcours du fichier
        originaltree = ET.parse(filename,ET.XMLParser(encoding='utf-8'))
        # on copie l'arbre original afin de ne pas modifier le fichier d'origine
        tree=copy.deepcopy(originaltree)
        #On lance la fonction de traitement des liaisons facultatives
        #sur la copie de l'arbre XML
        #On crée le nouveau nom du fichier puis on l'enregistre
        new_filename=re.search('([^\/.]*?.eaf)',filename)
        new_filename=new_filename.group(1)
        new_filename=re.sub('_VC','_VD_LEX',new_filename)
        #stat_filename="Sortie/Stats/"+new_filename
        new_filename="Sortie/LF_LEX/"+new_filename

        tree=LF_LEX(tree)
        #On crée les dossiers de sortie si nécessaire
        if not os.path.exists('./Sortie'):
            os.mkdir('./Sortie')
        if not os.path.exists('./Sortie/LF_LEX'):
            os.mkdir('./Sortie/LF_LEX')

        tree.write(new_filename,encoding="utf-8")
