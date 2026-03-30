#!/usr/bin/python
# -*- coding: UTF-8 -*-

import xml.etree.ElementTree as ET
import re
import copy

""" normalize(tree)
    Cette fonction permet de normaliser un fichier .eaf 
    Entrée:
        tree: Arbre XML extrait d'un fichier _VA.eaf (ElementTree) 
    Sorties:
        tree: Arbre XML avec la ligne *ID_Dylnet_normalise ajoutée (ElementTree)
        fichier_errone: Variable indiquant si le fichier comporte une annotation vide ou non (Boolean)
    Cette fonction ne peut pas être exécutée toute seule et est appellée
    depuis le script enrichissement.py
"""


def normalize(tree):   
	#On cree une variable dont on change l'état si le fichier est erroné (si il a une annotation vide)
    fichier_errone=False
    #Extraction de la racine de l'arbre XML
    root =tree.getroot()
    #On recherche la position de la ligne sur laquelle le script va s'appliquer
    position=0
    for child in root:
        if child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="praat":
            break
        elif child.tag=="TIER" and child.attrib.get("LINGUISTIC_TYPE_REF")=="default-lt":
            break
        else:
            position+=1
    #On récupère une copie la ligne ID_Dylnet
    line=copy.deepcopy(root[position])
    #On insère la copie dans l'arbre XML
    root.insert(position,line)
    position+=1
    #on récupère l'identifiant
    ID=line.attrib.get("TIER_ID")
    #Si le premier caractère n'est pas un * on l'ajoute
    if ID[0]!="*":
        ID="*"+ID
        line.set("TIER_ID", ID)
    #On crée un tableau contenant toutes les erreurs communes et leur corrections
    erreurscorrigees={"\(y\)":"","\(que\)":"","\(elle\)":"","\(c\'\)":"",\
    "\\bah@(?:\s|\.|\?)":"ah@o","PRENOMS":"PRENOM","PRENON":"PRENOM","\\bbah@(?:\s|\.|\?)":"bah@o","\\bouah@(?:\s|\.|\?)":"ouah@o",\
    "\\beh@(?:\s|\.|\?)":"eh@o","\\baïe@(?:\s|\.|\?)":"aïe@o","\\boh@(?:\s|\.|\?)":"oh@o","\\beuh@(?:\s|\.|\?)":"euh@o","\\bhé@(?:\s|\.|\?)":"hé@o","\\bboum@(?:\s|\.|\?)":"boum@o",\
    "\\bchut@(?:\s|\.|\?)":"chut@o","\\bhop@(?:\s|\.|\?)":"hop@o","\\bleu(?:\s|\.|\?)":"leu@o","\\batchoum(?:\s|\.|\?)":"atchoum@o",\
    "\\beh(?:\s|\.|\?)":"eh@o","\\boh(?:\s|\.|\?)":"oh@o","\\bhein(?:\s|\.|\?)":"hein@o","\\baïe(?:\s|\.|\?)":"aïe@o","\\beuh(?:\s|\.|\?)":"euh@o",\
    "\\bben(?:\s|\.|\?)":"ben@o","\\bbah(?:\s|\.|\?)":"bah@o","\\bha(?:\s|\.|\?)":"ha@o","\\bcot(?:\s|\.|\?)":"cot@o",\
    "\\bcodec(?:\s|\.|\?)":"codec@o","hahaha":"hahaha@o","stop@o":"stop","allez@o":"allez",\
    "allô&o":"allo","yeah@s":"yeah@o","p\(e\)tit":"petit","p\(e\)tits":"petits",\
    "p\(e\)tite":"petite","p\(e\)tites":"petites","parc\(e\)":"parce",\
    "pa\(r\)c\(e\)":"parc(e)","s\(e\)ra":"sera","v\(e\)nir":"venir",\
    "b\(e\)soin":"besoin","d\(e\)dans":"dedans","liv\(r\)e":"liv(re)",\
    "liv\(r\)es":"liv(res)","met\(tre\)":"mett(re)","r\(e\)garde":"regarde",\
    "e\(lle\)":"elle","enl\(e\)ver":"enlever","peut-êt\(r\)e":"peut-êt(re)",\
    "regar\(de\)":"regarde","lett\(r\)e":"lett(re)","lett\(r\)es":"lett(res)",\
    "lett\(re\)s":"lett(res)","r\(e\)voir":"revoir","c\(e\)t":"cet",\
    "d\(e\)ssous":"dessous","m\(a\)man":"maman","d\(é\)jà":"déjà",\
    "rega\(rde\)":"regarde","am\(e\)ner":"amener",\
    "p\(eu\)t-êt\(r\)e":"peut-êt(re)","pa\(r\)ce":"parce",\
    "r\(e\)garder":"regarder","vot\(r\)e":"vot(re)","\(a\)llez":"allez",\
    "enl\(e\)vé":"enlevé","mat\(e\)las":"matelas","mont\(r\)e":"mont(re)",\
    "possib\(l\)e":"possib(le)","prom\(e\)nons":"promenons","quelqu\(e\)":"quelque",\
    "s\(e\)rait":"serait","abimé":"abîmé","arb\(r\)e":"arb(re)","d\(e\)mander":"demander",\
    "d\(e\)ssus":"dessus","descend\(r\)e":"descend(re)","emm\(e\)ner":"emmener",\
    "enl\(e\)vez":"enlevez","arb\(r\)es":"arb(res)","chamb\(r\)e":"chamb(re)",\
    "not\(r\)e":"not(re)","quat\(r\)e":"quat(re)","maint\(e\)nant":"maintenant",\
    "s\(e\)rai":"serai","aut\(r\)e":"aut(re)","fai\(re\)":"faire","êt\(r\)e":"êt(re)",\
    "\\b(qu\(i\)(?:\s|\.|\?)|qu\(i\)$)":"qui","t-shirt":"tee-shirt","tee-shirt@s":"tee-shirt",\
    "t-shirts":"tee-shirts","c\(el\)ui":"celui","\\bouai\\b":"ouais",\
    "ouais@o":"ouais","\\bok@s":"ok","\\bprout@o":"prout","maitresse":"maîtresse",\
    "maitre":"maître","mait\(re\)":"maît(re)","mait\(res\)":"maît(res)",\
    "mait\(r\)e":"maît(re)","mait\(r\)es":"maît(res)","mamouth":"mammouth",\
    "week end":"week-end","entraine":"entraîne","boite":"boîte",\
    "boites":"boîtes","boitier":"boîtier","dinette":"dînette","bétise":"bêtise",\
    "allô":"allo","allô@o":"allo","regar\(de\)":"regarde","regar\(d\)e":"regarde",\
    "spiderman":"spider-man","Spiderman":"spider-man","spiderman@s":"spider-man",\
    "wake":"wake@s","xxxx":"xxx","\\bxx\\b":"xxx","\[\[":"\[","\]\]":"\]","\|":"\[",\
    "enlève-toi":"enlève toi","en-haut":"en haut","donnez-moi":"donnez moi","asseyez-vous":"asseyez vous",\
    "au-dessous":"au dessous","là-dedans":"là dedans",\
    "celui-là":"celui là","montrez-moi":"montrez moi","lance-toi":"lance toi",\
    "laissez-moi":"laissez moi","attendez-mo":"attendez moi","assied-toi":"assied toi",\
    "accroche-toi":"accroche toi","recule-toi":"recule toi","fois-ci":"fois ci",\
    "deux-là":"deux là","celles-là":"celles là","tais-toi":"tais toi",\
    "en-dessous":"en dessous","regarde-moi":"regarde moi","assis-toi":"assis toi",\
    "viens-là":"viens là","au-dessus":"au dessus","regardez-moi":"regardez moi",\
    "dis-donc":"dis donc","arrête-toi":"arrête toi","dis-moi":"dis moi",\
    "attends-moi":"attends moi","tais-toi":"tais toi","va-t\'en":"va t\'en","lève-toi":"lève toi",\
    "là-dessus":"là dessus","ceux-là":"ceux là","celle-ci":"celle ci","par-là":"par là",\
    "par-dessus":"par dessus","là-haut":"là haut","pousse-toi":"pousse toi",\
    "laisse-moi":"laisse moi","dépêche-toi":"dépêche toi","mets-toi":"mets toi",\
    "là-dedans":"là dedans","celle-là":"celle là","vas-y":"vas y","celui-là":"celui là",\
    "donne-moi":"donne moi","est c\(e\)-qu\(e\)":"est c(e) qu(e)",\
    "est ce-qu\(e\)":"est ce qu(e)","est ce-que":"est ce que","est-c\(e\) qu\(e\)":"est c(e) qu(e)",\
    "est-ce qu\(e\)":"est ce qu(e)","est-c\(e\) que":"est c(e) que",\
    "est-ce que":"est ce que","est-c\(e\)-qu\(e\)":"est c(e) qu(e)",\
    "est-ce-qu\(e\)":"est ce qu(e)","est-c\(e\)-que":"est c(e) que",\
    "est-ce-que":"est ce que","est-ce":"est ce","est-c\(e\)":"est c(e)",\
    "assieds-toi":"assieds toi","s'i\(l\) vous-plâit":"s\'i(l) vous plâit",\
    "s'i\(l\)-vous plâit":"s'i(l)-vous-plâit","s'i\(l\) vous-plait":"s'i(l)-vous-plâit",\
    "s'i\(l\)-vous plait":"s\'i(l) vous plâit","s'i\(l\)-vous-plait":"s\'i(l) vous plâit",\
    "s'i\(l\) vous plait":"s\'i(l) vous plâit","s'\(il\) vous-plâit":"s\'(il) vous plâit",\
    "s'\(il\)-vous plâit":"s\'(il) vous plâit","s'\(il\)-vous-plâit":"s\'(il) vous plâit",\
    "s'\(il\) vous-plait":"s\'(il) vous plâit","s'\(il\)-vous plait":"s\'(il) vous plâit",\
    "s'\(il\)-vous-plait":"s\'(il) vous plâit","s'\(il\) vous plait":"s\'(il) vous plâit",\
    "s'il vous-plâit":"s\'il vous plâit","s'il-vous plâit":"s\'il vous plâit",\
    "s'il-vous-plâit":"s\'il vous plâit","s'il vous-plait":"s\'il vous plâit",\
    "s'il-vous plait":"s\'il vous plâit","s'il-vous-plait":"s\'il vous plâit",\
    "s'il vous plait":"s\'il vous plâit","s'i\(l\) te-plâit":"s\'i(l) te plâit",\
    "s'i\(l\)-te plâit":"s\'i(l) te plâit","s'i\(l\)-te-plâit":"s\'i(l) te plâit",\
    "s'i\(l\) te-plait":"s\'i(l) te plâit","s'i\(l\)-te plait":"s\'i(l) te plâit",\
    "s'i\(l\)-te-plait":"s\'i(l) te plâit","s'i\(l\) te plâit":"s\'i(l) te plâit",\
    "s'\(il\) te-plâit":"s\'(il) te plâit","s'\(il\)-te plâit":"s\'(il) te plâit",\
    "s'\(il\)-te-plâit":"s\'(il) te plâit","s'\(il\) te-plait":"s\'(il) te plâit",\
    "s'\(il\)-te plait":"s\'(il) te plâit","s'\(il\)-te-plait":"s\'(il) te plâit",\
    "s'\(il\) te plait":"s\'(il) te plâit" 
    }
    #On parcourt l'arbre XML
    for child in root[position]:
        for c in child:
            for ele in c:
                #On ajoute un message d'erreur si on rencontre une annotation vide
                if ele.text==None or ele.text==" ":
                    ele.text="$"
                    fichier_errone=True
                #A l'aide du tableau crée précédemment, on nettoie toutes les erreurs communes
                for key,value in erreurscorrigees.items():
                    ele.text=re.sub(key,value,ele.text)
                #Si on trouve deux ou plus espaces, on les remplace par un seul
                ele.text = re.sub("(\s{2,})"," ", ele.text)
                #Si on ne trouve pas de marqueur de fin on ajoute un "."
                ele.text = re.sub("(\w)\s?$","\g<1>.", ele.text)
                #Si on trouve deux marqueurs de fin identiques, on en supprime un
                ele.text = re.sub("\.\.",".",ele.text)
                ele.text = re.sub("\?\?","?",ele.text)
                #Si on trouve des espaces avant le marqueur de fin on les efface    
                ele.text = re.sub("(\s+\.)",".",ele.text)
                ele.text = re.sub("(\s+\?)","?",ele.text)
                #On remplace toute occurence de la séquence "t'as" par "t(u) as"
                #Règle obsolète car trop de bruit, conservée au cas où
                # ~ ele.text = re.sub("(t'as)", "t(u) as",ele.text)
                #On remplace la séquence i(ls) par i(l)s
                ele.text = re.sub("(i\(ls\))","i(l)s",ele.text)
                #On supprime tous les points d'exclamation si ils sont suivis
                #ou précédés par un séparateur d'énoncé
                ele.text = re.sub("(\.!|\.\s!|!\.|!\s\.)", ".",ele.text)
                ele.text = re.sub("(\?!|\?\s!|!\?|!\s\?)", "?",ele.text)
                #Si le point d'exclamation est isolé, on le remplace par un point simple
                ele.text = re.sub("(!|\s!)", ".",ele.text)
                #On supprime les (ne) , (n') et (n)  
                ele.text = re.sub("(\(ne\)|\(n'\)|\(n\))","" ,ele.text)
                #On supprime le "n'" dans toute occurence de la séquence on n'+voyelle
                ele.text = re.sub("(on) n'([aàâeéèêiîoôuùûyh])", "\g<1> \g<2>", ele.text)
                #On supprime tout espace avant ou après une apostrophe
                ele.text = re.sub('\'\s|\s\'', '\'', ele.text)
                #On remplace toute occurence de "'&" par "&'"
                ele.text = re.sub("'\&amp|'\&","\&'",ele.text)
                 #On traite les marqueurs de doute
                ele.text = re.sub("[a-z-âéàçèïêù@ûîôA-Z'\-())?]*\&amp;|(\>\&amp;)|[a-z-âéàçèïêù@ûîôA-Z'\-())?]*\&|(\>\&)", "xxx", ele.text)
    #On change l'identifiant de la nouvelle ligne
    root[position].set("TIER_ID",root[position].attrib.get("TIER_ID")+"_normalise")
    #On change le type linguistique duquel dépend la nouvelle ligne
    root[position].set("LINGUISTIC_TYPE_REF","Normalisation")
    #On change l'identifiant de chaque annotation
    for child in root[position]:
        for c in child:
            c.set("ANNOTATION_ID",c.attrib.get("ANNOTATION_ID")+"_normalise")
    #On crée une copie d'un type linguistique
    position=0
    for child in root:
        if child.tag=="LINGUISTIC_TYPE" and child.attrib.get("LINGUISTIC_TYPE_ID")=="praat":
            break
        elif child.tag=="LINGUISTIC_TYPE" and child.attrib.get("LINGUISTIC_TYPE_ID")=="default-lt":
            break
        else:
            position+=1
    newline=copy.deepcopy(root[position])
    #On change l'identifiant de la copie
    newline.set("LINGUISTIC_TYPE_ID","Normalisation")
    #On ajoute la copie dans l'arborescence XML
    root.insert(position+1,newline)                             
    return tree,fichier_errone
