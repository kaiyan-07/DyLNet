#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import xml.etree.ElementTree as ET
import copy
#dépendance a indiquer dans le manuel
import treetaggerwrapper
#dépendance du module "six" sur les anciennes versions de python

"""tag(tree)
    Cette fonction permet de tagger avec TreeTagger le fichier XML
    nettoyé auparavant grâce au script nettoyage.py 
    Entrée:
        tree: Arbre XML extrait d'un fichier _VA.eaf, normalisé et nettoyé(ElementTree) 
    Sortie:
        tree: Arbre XML avec la ligne ID_DylNet tagging ajoutée (ElementTree)
    Cette fonction ne peut pas être exécutée toute seule et est appellée
    depuis le script enrichissement.py
"""

def tag(tree):
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
	root.insert(position,line)
	position+=1
	#On indique les paramètres utilisés par TreeTagger pour l'annotation
	tagger=treetaggerwrapper.TreeTagger(TAGLANG = 'fr', TAGINENC = "utf8", TAGOUTENC = 'utf8', TAGPARFILE="spoken-french.par")
	mots=[]
	#On parcourt tous les éléments de l'arbre
	for child in root[position]:
		for c in child:
			for ele in c:
				mots=[]
				#On appelle TreeTagger pour annoter les mots
				tags=tagger.tag_text(ele.text)
				#On crée une nouvelle ligne mot|cat|lemme
				for tag in tags:
					mots.append("|".join(tag.split("\t")))
				ele.text=" ".join(mots)
	#On change le nom de la nouvelle ligne crée
	new_id=re.sub('_nettoye','',root[position].attrib.get("TIER_ID"))
	root[position].set("TIER_ID",new_id+"_tagging")
	#On change le type linguistique duquel dépend la nouvelle ligne
	root[position].set("LINGUISTIC_TYPE_REF","Tagging")
	for child in root[position]:
		for c in child:
			new_id=re.sub('_nettoye','',c.attrib.get("ANNOTATION_ID"))
			c.set("ANNOTATION_ID",new_id+"_tagging")
	#On crée une copie d'un type linguistique
	position=0
	#On change l'identifiant de chaque annotation
	for child in root:
		if child.tag=="LINGUISTIC_TYPE" and child.attrib.get("LINGUISTIC_TYPE_ID")=="Nettoyage":
			break
		else:
			position+=1
	newline=copy.deepcopy(root[position])
	#On change l'identifiant de la copie
	newline.set("LINGUISTIC_TYPE_ID","Tagging")
	#On ajoute la copie dans l'arborescence XML
	root.insert(position+1,newline)

	return tree

