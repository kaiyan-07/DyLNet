import stanza
import re
import xml.etree.ElementTree as ET
import copy

""" stanza_analysis(tree)
    Cette fonction utilise Stanza pour analyser linguistiquement un fichier XML 
    et ajouter une nouvelle couche d'annotations au format CoNLL-U avec "|" comme séparateur.

    Entrée:
        tree: Arbre XML extrait d'un fichier _VA.eaf, normalisé et nettoyé (ElementTree)

    Sortie:
        tree: Arbre XML avec une nouvelle couche "Stanza" contenant les annotations suivantes :

        (ElementTree)
        Format de sortie (CoNLL-U avec "|" comme séparateur):
        ID | FORM | LEMMA | UPOS | XPOS | FEATS | HEAD | DEPREL | DEPS | MISC
"""

def stanza_analysis(tree, nlp=None):

    # Initialiser Stanza si ce n'est pas déjà fait
    if nlp is None:
        try:
            nlp = stanza.Pipeline(lang='fr', processors='tokenize,mwt,pos,lemma,depparse', tokenize_no_ssplit=True)
        except Exception as e:
            raise RuntimeError(f"Échec de l'initialisation du pipeline Stanza : {e}")

    # Récupérer la racine de l'arborescence XML
    root = tree.getroot()

    # Trouver l'index du "Nettoyage" tier dans l'arbre XML
    position = 0
    for child in root:
        if child.tag == "TIER" and child.attrib.get("LINGUISTIC_TYPE_REF") == "Nettoyage":
            break
        else:
            position += 1

    # Copier la ligne sur laquelle on va travailler
    line = copy.deepcopy(root[position])

    # Insérer la copie dans l'arbre
    root.insert(position, line)
    position += 1

    # Parcourir tous les éléments de l'arbre
    for annotation in root[position]:
        for alignable in annotation.findall("ALIGNABLE_ANNOTATION"):
            element = alignable.find("ANNOTATION_VALUE")
            if element is not None and element.text and element.text.strip():
                text = element.text.strip()
                try:
                    # Exécuter l'analyse NLP avec Stanza
                    doc = nlp(text)

                    # Liste pour stocker les annotations formatées
                    annotations = []

                    for sentence in doc.sentences:
                        for word in sentence.words:
                            token = word.parent
                            start_char = str(token.start_char) if hasattr(token, 'start_char') else "_"
                            end_char = str(token.end_char) if hasattr(token, 'end_char') else "_"

                            attributes = [
                                str(word.id or '_'),  # ID
                                str(word.text or '_'),  # FORM (mot original)
                                str(word.lemma or '_'),  # LEMMA (lemmatisation)
                                str(word.upos or '_'),  # UPOS (catégorie grammaticale universelle)
                                str(word.xpos or '_'),  # XPOS (catégorie spécifique)
                                str(word.feats or '_'),  # FEATS (morphologie)
                                str(word.head or '_'),  # HEAD (mot gouverneur dans la dépendance)
                                str(word.deprel or '_'),  # DEPREL (relation syntaxique)
                                '_',  # DEPS (dépendances améliorées, généralement `_`)
                                f'start_char={start_char}|end_char={end_char}'  # MISC (autres informations)
                            ]
                            # Ajouter la ligne avec `|` comme séparateur
                            annotations.append("|".join(attributes))

                        # Ajouter une ligne vide pour séparer les phrases
                        annotations.append("")

                    # Mettre à jour le texte de l'élément XML avec les annotations Stanza
                    element.text = "\n".join(annotations)

                except Exception as e:
                    element.text = f"Erreur de traitement NLP : {e}"

    # Modifier le nom de la nouvelle ligne créée
    new_id = re.sub('_nettoye', '', root[position].attrib.get("TIER_ID"))
    root[position].set("TIER_ID", new_id + "_stanza")

    # Changer le type linguistique de la nouvelle ligne
    root[position].set("LINGUISTIC_TYPE_REF", "Stanza")

    # Mettre à jour l'identifiant de chaque annotation
    for annotation in root[position]:
        for alignable in annotation.findall("ALIGNABLE_ANNOTATION"):
            new_id = re.sub('_nettoye', '', alignable.attrib.get("ANNOTATION_ID"))
            alignable.set("ANNOTATION_ID", new_id + "_stanza")

    # Trouver la position du type linguistique "Nettoyage"
    position = 0
    for child in root:
        if child.tag == "LINGUISTIC_TYPE" and child.attrib.get("LINGUISTIC_TYPE_ID") == "Nettoyage":
            break
        else:
            position += 1

    # Créer une copie du type linguistique
    newline = copy.deepcopy(root[position])

    # Modifier l'identifiant du type linguistique copié
    newline.set("LINGUISTIC_TYPE_ID", "Stanza")

    # Ajouter la copie dans l'arborescence XML
    root.insert(position + 1, newline)

    return tree
