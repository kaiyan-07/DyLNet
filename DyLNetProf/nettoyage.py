import re
import xml.etree.ElementTree as ET
import copy

"""nettoye(tree)
    Cette fonction permet de nettoyer le fichier XML lu auparavant grâce au script normalize.py 
    Entrée:
        tree: Arbre XML extrait d'un fichier _VA.eaf et normalisé (ElementTree) 
    Sortie:
        tree: Arbre XML avec la ligne ID_DylNet nettoye ajoutée (ElementTree)
    Cette fonction ne peut pas être exécutée toute seule et est appellée
    depuis le script enrichissement.py
"""

def nettoye(tree):
    #On extrait la racine de l'arborescence XML
    root=tree.getroot()
    #On recherche la position de la ligne sur laquelle le script va s'appliquer
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="Normalisation":
            break
        else:
            position+=1
    #On copie la ligne qui va nous servir de base pour travailler dessus 
    #sans modifier l'original
    line=copy.deepcopy(root[position])
    #On insère la nouvelle ligne dans l'arbre
    root.insert(position,line)
    position+=1
    #On parcourt chacun des éléments qui composent la ligne
    for child in root[position]:
        for c in child:
            for ele in c:
                #On supprime toutes les occurences de (il) et (ils)	
                ele.text = re.sub("\(ils?\)","",ele.text)
                #On supprime les double espaces qui peuvent résulter de cette suppression
                ele.text = re.sub("(\s{2,})"," ", ele.text)
                #On supprime tous les crochets et leur contenu
                #On supprime toutes les parenthèses
                ele.text = re.sub("(\[.*?\])|\(|\)", "", ele.text)
                #On traite les amorces, les onomatopées ainsi que les mots étrangers
                ele.text = re.sub("([a-z-âéàçèïêùûîôA-Z']*--)","aaa", ele.text)
                ele.text = re.sub("([a-z-âéàçèïêùûîôA-Z']*@o)","ooo", ele.text)
                ele.text = re.sub("([a-z-âéàçèïêùûîôA-Z']*@s)","sss", ele.text)
                #On remplace toute borne ne contenant que des xxx par un symbole spécial
                #pour ensuite les supprimer
                if re.search("^(\s?x{3,}[\s.?])+\s?$",ele.text):
                    # ~ print ("removed",ele.text)
                    # ~ root[position].remove(child)
                    ele.text="$$$"
                #On efface tout énonce qui ne contient que des xxx
                
                ele.text = re.sub("(?<=[.?])\s?(xxx[\s]?)+[.?]","",ele.text)
                ele.text = re.sub("^\s?(xxx[\s]?)+[.?]","",ele.text)
                #On nettoie les espaces superflus qui peuvent résulter de cette suppression
                ele.text = re.sub("(\s{2,})"," ", ele.text)
                
    #On supprime les bornes marquées auparavant           
    for child in root[position].findall("ANNOTATION"):
        for c in child:
            for ele in c:
                if re.search("\$\$\$",ele.text):
                    root[position].remove(child)
    #On change le nom de la nouvelle ligne crée
    new_id=re.sub('_normalise','',root[position].attrib.get("TIER_ID"))
    root[position].set("TIER_ID",new_id+"_nettoye")
    #On change le type linguistique duquel dépend la nouvelle ligne
    root[position].set("LINGUISTIC_TYPE_REF","Nettoyage")
    #On change l'identifiant de chaque annotation
    for child in root[position]:
        for c in child:
            new_id=re.sub('_normalise','',c.attrib.get("ANNOTATION_ID"))
            c.set("ANNOTATION_ID",c.attrib.get("ANNOTATION_ID")+"_nettoye")
    #On crée une copie d'un type linguistique
    position=0
    for child in root:
        if child.tag=="LINGUISTIC_TYPE" and child.attrib.get("LINGUISTIC_TYPE_ID")=="Normalisation":
            break
        else:
            position+=1
    newline=copy.deepcopy(root[position])
    #On change l'identifiant de la copie
    newline.set("LINGUISTIC_TYPE_ID","Nettoyage")
    #On ajoute la copie dans l'arborescence XML
    root.insert(position+1,newline)
    return tree

