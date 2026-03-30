import re
import xml.etree.ElementTree as ET
import copy
import sys
import os

""" analyser_liaisons(names)
    Cette fonction permet, à partir d'une liste de fichiers VD_LEXC.eaf, de creer
    une liste contenant les informations sur chaque contexte de liaison facultative

    Entrée:
        names:Liste de chemins d'accès aux fichiers à traiter (List)
    Sorties:
        info_liaisons: tableau associatif contenant les informations suivantes:

        (Dict)
"""

def analyser_liaisons(names):
    info_liaisons={}
    id=0
    for filename in names:
        tree=ET.parse("./uploads/"+filename,ET.XMLParser(encoding='utf-8'))
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
        position_liai=0
        for child in root:
            if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="LF_LEX_Codee":
                break
            else:
                position_liai+=1

        for child in root[position_liai]:
            for c in child:
                for ele in c:
                    tourdeparole=copy.deepcopy(ele.text)
                    #on divise chaque tour de parole en fonction des énoncés
                    contextes=re.findall("([^.!]*?)\s?([a-z-âàéàçèïêùûîôA-Z\d]+)\s(\[LF[13]\])\s([a-z-âàéàçèïêùûîôA-Z\d]+)([^.!]*)",tourdeparole)

                    for contexte in contextes:
                        mot1=contexte[1]
                        mot2=contexte[3]
                        contexte_prec=contexte[0]
                        contexte_suiv=contexte[4]
                        type_liaison=contexte[2]
                        temps1=c.attrib.get("TIME_SLOT_REF1")
                        temps2=c.attrib.get("TIME_SLOT_REF2")
                        info_liaisons[(mot1,mot2,id)]=(temps1,temps2,filename,contexte_prec,type_liaison,contexte_suiv)
                        id+=1
    #exemple du format de sortie:
    #{('est', 'à', 0): ('ts227', 'ts237', '21-20181008-070000-0218-4832-00-part02-R_VD_LEXC.eaf', "c'", '[LF3]', ' mon bébé'),
    #('quand', 'elle', 1): ('ts973', 'ts983', '21-20181008-070000-0218-4832-00-part02-R_VD_LEXC.eaf', ' elle la jette', '[LF3]', ' se lève')}
    dict_svg=open("svg_dict.txt","w",encoding="utf8")
    dict_svg.write( str(info_liaisons) )
    dict_svg.close()
