#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import xml.etree.ElementTree as ET
import copy
import os

""" LF_MOR(tree)
    Cette fonction permet d'ajouter les lignes LF_MOR et LF_MOR_Codee à
    un arbre XML
    Entrée:
        tree: Arbre XML enrichi (ElementTree)
    Sorties:
        tree: Arbre XML avec les lignes LF_MOR et LF_MOR_Codee ajoutées
"""

def LF_MOR(tree):
    #On récupère la racine de l'arbre XML
    root=tree.getroot()
    #On récupère la position de la ligne sur laquelle on veut travailler
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Nettoyage":
            break
        else:
            position+=1
    #On récupère la position de la ligne de tagging
    positiontagging=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Tagging":
            break
        else:
            positiontagging+=1
    position_actuelle=0
    #On crée une copie de cette ligne
    line=copy.deepcopy(root[position])
    #On insère la copie dans l'arbre
    root.insert(position+1,line)
    position+=1
    positiontagging+=1
    #On change l'identifiant de la ligne copiée ainsi que celui de toutes
    #les annotations de la ligne
    root[position].set("LINGUISTIC_TYPE_REF","Liaison")
    for child in root[position]:
        for c in child:
            new_id=re.sub('_nettoye','',c.attrib.get("ANNOTATION_ID"))
            c.set("ANNOTATION_ID",new_id+"_LF_MOR")
    new_id=re.sub('_nettoye','',root[position].attrib.get("TIER_ID"))
    root[position].set("TIER_ID",new_id+"_LF_MOR")
    #On parcourt chacun des tours de parole
    for child in root[position]:
        for c in child:
            for ele in c:
                # On recherche tous les contextes de négation possibles
                if re.search("((d'accord|d'abord|d'ailleurs|([a-z-âàéàçèïêùûîôA-Z\d]+')?([a-z-âàéàçèïêùûîôA-Z\d]+[dtsxznrp]))([\s])(aujourd'hui|[aàâeéèêiîoôuùûyh][a-z-âàéàçèïêùûîôA-Z\d]*))",ele.text):
                    occurences=re.findall("((d'accord|d'abord|d'ailleurs|([a-z-âàéàçèïêùûîôA-Z\d]+')?([a-z-âàéàçèïêùûîôA-Z\d]+[dtsxznrp]))([\s])(aujourd'hui|[aàâeéèêiîoôuùûyh][a-z-âàéàçèïêùûîôA-Z\d]*))",ele.text)
                    # Pour chaque contexte, on récupère les trois mots avant et après le contexte
                    for occurence in occurences:
                        #Occurence[3] indique une potentielle séquence suivie d'une apostrophe précedant le mot1
                        if occurence[3]!="":
                            contexte_liaison=[occurence[0],occurence[3],occurence[4],occurence[5]]
                        else:
                            contexte_liaison=[occurence[0],occurence[1],occurence[4],occurence[5]]
                        #On définit une variable qui nous indique si le
                        #contexte est valide ou non
                        contexte_valide=True
                        #On récupère le mot1 et le mot2 de liaison
                        mot1=contexte_liaison[1]
                        mot2=contexte_liaison[3]
                        #On vérifie que le mot1 ne provoque pas un contexte d'enchaînement
                        if re.search("[uoiayôîïûâ]r\\b",mot1):
                            contexte_valide=False
                        #On vérifie que le mot1 n'appartient pas a la liste
                        #des déterminants pouvant provoquer une LO
                        if mot1 in ["un", "des", "les", "mon", "ton", "son", "mes", "tes", "ses", "nos", "vos", "leurs", "ces", "deux", "trois", "six", "dix", "aux", "quels", "quelles", "aucun", "quelques", "d'un"]:
                            contexte_valide=False
                        #On vérifie que le mot1 n'est pas en majuscules
                        if mot1.isupper():
                            contexte_valide=False
                        #On vérifie que le mot1 n'est pas précédé d'une séquence
                        #suivie d'une apostrophe lorsqu'il commence par une voyelle
                        if occurence[3]!="" and mot1[0] in ["a", "à", "â","e","é", "è", "ê", "i", "î", "o", "ô", "u", "ù", "û", "y", "h"]:
                            contexte_valide=False
                        #On vérifie que ni les mot1 ni les mot2 font partie de la
                        #liste de pronoms qui peuvent provoquer une LO
                        if mot1 in ["nous","vous","ils","elles"] or mot2 in ["nous","vous","ils","elles"]:
                            contexte_valide=False
                        #On vérifie que le mot1 n'est pas un mot qui rend
                        #la liaison impossible ou obligatoire
                        if mot1 in ["qu'on", "l'on", "nan", "on", "autour", "avoir", "car", "cet", "couleur", "hier", "huit", "noir", "ouvrir", "partir", "pour", "super", "sur", "voir", "et", "alors", "non", "stop", "en", "sinon", "xxx", "sss", "maintenant"]:
                            contexte_valide=False
                        #On vérifie que les deux mots ne sont pas identiques
                        if mot1==mot2:
                            contexte_valide=False
                        #On vérifie que le mot2 n'est pas un mot rendant la liaison impossible
                        if mot2 in ["oui","ouais","où","ooo","aaa"]:
                            contexte_valide=False
                        #On crée une expression régulière nous permettant de récupèrer le mot suivant
                        regex2=occurence[0]+"[\s']([a-z-âàéàçèïêùûîôA-Z\d]+)"
                        mot3=re.search(regex2,ele.text)
                        #Si il y un mot suivant, on vérifie que la séquence
                        #mot1 mot2 mot3 ne fait pas partie d'une expression figée
                        #imposant ou empêchant la liaison
                        if mot3:
                            mot3=mot3.group(1)
                            if (mot1,mot2,mot3) in [("tout","à","coup"),("tout","à","l"),("tout","à","fait"),("temps","en","temps"),("moins","en","moins"),("mieux","en","mieux"),("tout","en","bas"),("vis","à","vis")]:
                                contexte_valide=False
                        #On vérifie que la séquence mot1 mot2 ne fait pas
                        #partie d'une expression figée imposant ou empêchant la liaison
                        if (mot1,mot2) in [("bien","entendu"),("bas","âge"),("tout","un"),("sans","arrêt"),("quant","aux"),("toute","une"),("quand","à"),("bien","évidemment"),("vous","autres"),("nous","autres"),("tout","en"),("en","haut")]:
                            contexte_valide=False
                        #Si le contexte est valide, on ajoute le codage
                        #[LF] entre le mot1 et le mot2
                        #On recherche la catégorie grammaticale et le lemme du mot1
                        #et du mot2
                        for e in root[positiontagging][position_actuelle]:
                            for element in e:
                                if re.search(mot1+"\|((?:[a-z-âéàçèïêùûîôA-Z\.\?]+)(?::[a-z-âéàçèïêùûîôA-Z\.\?]+)?)\|(@?[a-z-âéàçèïêùûîôA-Z\.\?]+@?)",element.text) is not None:
                                    cat_mot1=re.search(mot1+"\|((?:[a-z-âéàçèïêùûîôA-Z\.\?]+)(?::[a-z-âéàçèïêùûîôA-Z\.\?]+)?)\|(@?[a-z-âéàçèïêùûîôA-Z\.\?]+@?)",element.text).group(1)
                                    lemme1=re.search(mot1+"\|((?:[a-z-âéàçèïêùûîôA-Z\.\?]+)(?::[a-z-âéàçèïêùûîôA-Z\.\?]+)?)\|(@?[a-z-âéàçèïêùûîôA-Z\.\?]+@?)",element.text).group(2)
                                    cat_mot2=re.search(mot2+"\|((?:[a-z-âéàçèïêùûîôA-Z\.\?]+)(?::[a-z-âéàçèïêùûîôA-Z\.\?]+)?)\|(@?[a-z-âéàçèïêùûîôA-Z\.\?]+@?)",element.text).group(1)
                                    lemme2=re.search(mot2+"\|((?:[a-z-âéàçèïêùûîôA-Z\.\?]+)(?::[a-z-âéàçèïêùûîôA-Z\.\?]+)?)\|(@?[a-z-âéàçèïêùûîôA-Z\.\?]+@?)",element.text).group(2)
                                else:
                                    cat_mot1="err"
                                    lemme1="err"
                                    cat_mot2="err"
                                    lemme2="err"
                        #On vérifie que le contexte n'est pas un pronom suivi d'un verbe
                        #ou l'inverse
                        if (cat_mot1=="PRO:cls" or cat_mot1=="PRO:clo") and cat_mot2[0:3]=="VER":
                            contexte_valide=False

                        if (cat_mot2=="PRO:cls" or cat_mot2=="PRO:clo") and cat_mot1[0:3]=="VER":
                            contexte_valide=False

                        #On vérifie que le contexte de liaison n'est pas "dedans" suivi d'un verbe
                        if mot1=="dedans" and cat_mot2[0:3]=="VER":
                            contexte_valide=False
                        #On vérifie que le mot1 et le mot2 ne sont pas tous les deux des verbes

                        if cat_mot1[0:3]=="VER" and cat_mot2[0:3]=="VER":
                            #Si les deux mots sont des verbes, on vérifie si
                            #le mot1 fait partie d'une certaine liste d'exceptions
                            if lemme1 not in ["être","avoir","aller","falloir","pouvoir","ajouter","faire","devoir","sembler","paraitre","paraître","vouloir","savoir","venir"] and cat_mot1!="VER:infi":
                                contexte_valide=False

                        #On vérifie que le mot1 n'est pas un nom
                        if cat_mot1[0:3]=="NOM":
                            contexte_valide=False

                        if contexte_valide:
                            nouvelle_liaison=mot1+"\g<1>[LF]\g<1>"+mot2
                            regex3=mot1+"([\s'])"+mot2
                            ele.text=re.sub(regex3,nouvelle_liaison,ele.text)


        position_actuelle+=1
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
    #On récupère la ligne LF_MOR que l'on vient de créer
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Liaison":
            break
        else:
            position+=1
    line=copy.deepcopy(root[position])
    #On insère la copie dans l'arbre
    root.insert(position+1,line)
    positioncopie=position+1
    #On remplit cette copie d'annotations vides qui seront ensuite remplies
    #et on change l'identifiant de la ligne et des annotations
    for child in root[positioncopie]:
        for c in child:
            new_id=re.sub('_LF_MOR','',c.attrib.get("ANNOTATION_ID"))
            c.set("ANNOTATION_ID",new_id+"_LF_MOR_codee")
            c.set("TIME_SLOT_REF1","#")
            c.set("TIME_SLOT_REF2","#")
            for ele in c:
                ele.text="#"
    new_id=re.sub('_LF_MOR','',root[positioncopie].attrib.get("TIER_ID"))
    root[positioncopie].set("TIER_ID",new_id+"_LF_MOR_codee")
    position_actuelle=0
    #On parcourt la ligne LF_MOR
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
                    #des bornes vides de la ligne LF_MOR_codee
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
    newline.set("LINGUISTIC_TYPE_ID","Liaison")
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
    #On efface toutes les annotations vides de la ligne LF_MER_codee
    for child in root[positioncopie].findall("ANNOTATION"):
        for c in child:
            if c.get("TIME_SLOT_REF1")=="#":
                root[positioncopie].remove(child)
    return tree

""" lancement_LF_MOR(filename)
    Cette fonction permet d'extraire l'arbre XML d'un fichier _VC.eaf
    et de lancer le traitement des liaisons facultatives
    Entrée:
        filename: Chemin d'accès au fichier (String)
    Sorties:
        Création d'un fichier _VD.eaf avec les lignes LF_MOR et LF_MOR_codee
        ajoutées
"""

def lancement_LF_MOR(filename):
    if re.search("_VC",filename):
        # parcours du fichier
        originaltree = ET.parse(filename,ET.XMLParser(encoding='utf-8'))
        # on copie l'arbre original afin de ne pas modifier le fichier d'origine
        tree=copy.deepcopy(originaltree)
        #On lance la fonction de traitement des liaisons facultatives
        #sur la copie de l'arbre XML
        tree=LF_MOR(tree)
        #On crée les dossiers de sortie si nécessaire
        if not os.path.exists('./Sortie'):
            os.mkdir('./Sortie')
        if not os.path.exists('./Sortie/LF_MOR'):
            os.mkdir('./Sortie/LF_MOR')
        #On crée le nouveau nom du fichier puis on l'enregistre
        new_filename=re.search('([^\/.]*?.eaf)',filename)
        new_filename=new_filename.group(1)
        new_filename=re.sub('_VC','_VD_MOR',new_filename)
        new_filename="Sortie/LF_MOR/"+new_filename
        tree.write(new_filename,encoding="utf-8")
