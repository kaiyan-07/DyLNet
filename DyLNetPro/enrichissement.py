#!/usr/bin/python
# -*- coding: UTF-8 -*-

from normalisation import normalize
from nettoyage import nettoye
from tagging import tag
from stanza_analyse import stanza_analysis
import os
import re
import xml.etree.ElementTree as ET
import copy

"""
enrichissement(name)
    This function enriches a _VA.eaf file by adding lines for normalization, cleaning, and tagging.

    Parameters:
        name: Path to the file to process (String)
    Returns:
        fichier_errone: Boolean indicating if the file contains an empty annotation
        Creates an enriched _VB.eaf file.
"""


def enrichissement(name):
    # Verify the file is a _VA.eaf file
    if re.search("_VA", name):
        # Parse the original file
        original_tree = ET.parse(name, ET.XMLParser(encoding='ut'
                                                             'f-8'))
        # Deep copy the original tree to avoid modifying the original file
        tree = copy.deepcopy(original_tree)

        # Run enrichment scripts
        tree, fichier_errone = normalize(tree)
        tree = nettoye(tree)
        tree = tag(tree)
        tree = stanza_analysis(tree)

        # Ensure output directories exist
        output_dir = './Sortie/Enrichis'
        os.makedirs(output_dir, exist_ok=True)

        # Create the name for the new file
        new_filename = re.sub('_VA', '_VB', os.path.basename(name))
        new_filepath = os.path.join(output_dir, new_filename)

        # Save the enriched file
        tree.write(new_filepath, encoding="utf-8")
        return fichier_errone