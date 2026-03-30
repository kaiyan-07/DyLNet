# -*- coding: utf-8 -*-

import os
import ast
import unicodedata
from datetime import datetime
from flask import *
from enrichissement import enrichissement
from werkzeug.utils import secure_filename
from zipfile import ZipFile
from negations import lancement_negations
from LF_LEX import lancement_LF_LEX
from LF_MOR import lancement_LF_MOR
from extraction_brute import extract_brut
from extraction_regroupements import extract_organisee_reg
from analyse_liaison import analyser_liaisons
import stat
from collections import Counter
import csv
from flask import Response

#Creation de l'app
app = Flask(__name__,template_folder='Templates', static_folder='Static')

#Création des dossiers indispensable
if not os.path.exists('uploads'):
    os.mkdir("uploads")
if not os.path.exists('Sortie'):
    os.mkdir("Sortie")
if not os.path.exists('Static/Telechargements'):
    os.mkdir("Static/Telechargements")
#Configuration initiale
app.config.from_mapping(SECRET_KEY='18062021')
#Definition du fichier de télechargement
path = os.getcwd()
app.config["UPLOAD_FOLDER"] = os.path.join(path, 'uploads')

#Definition des extensions de fichiers autorisées (.eaf seulement devrait suffire normalement)
ALLOWED_EXTENSIONS = ('eaf')

#Vérification de la conformité d'un fichier
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Fonction pour l'harmonisation de l'ordre alphabétique
#Pour que les lettres accentuées soient bien triées
def u_to_str(u):
    return unicodedata.normalize("NFKD", u).encode("ascii", "ignore")

#Page d'acceuil
@app.route('/')
def index():
    date = datetime.now()
    h = date.hour
    m = date.minute
    s = date.second
    return render_template("index.html",heure=h,minute=m,seconde=s)

#Page d'enrichissement
@app.route('/enrichissement')
def enrich():
    return render_template("pageenrich.html")

#Page des téléchargements
@app.route('/telechargements')
def telecharge():
    for fichier in os.listdir("./Static/Telechargements"):
        flash("./Telechargements/"+fichier)
    return render_template("pagetelecharg.html")

#Vidage du fichier des téléchargements
@app.route('/effacertele', methods= ['POST'])
def effacertele():
    for fichier in os.listdir("./Static/Telechargements"):
        os.remove("./Static/Telechargements/"+fichier)
    flash("$fichier(s) effacé(s)")
    return redirect(url_for("telecharge"))

#Lancement du script d'enrichissement
@app.route('/runenrich', methods = ['POST'])
def runenrich():
    #On vérifie qu'il y a bien au moins un fichier
    if 'enrich_file' not in request.files:
            flash('Pas de fichier séléctionné, veuillez sélectionner au moins un fichier')
            return redirect(url_for("enrich"))

    liste_errones=[]
    #On récupère la liste des fichiers du formulaire
    fichiers = request.files.getlist('enrich_file')

    #On stocke de façon temporaire les fichiers
    for fichier in fichiers:
        if fichier and allowed_file(fichier.filename):
            nomfichier = secure_filename(fichier.filename)
            fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier))
            # os.chmod(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier), stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
        else:
            flash("fichier invalide: "+fichier.filename)
    #On lance l'enrichissement, ce qui crée les fichiers de résultat
    for fichier in os.listdir(app.config['UPLOAD_FOLDER']):
        fichier_errone=enrichissement("./uploads/"+fichier)
        flash("enrichi fichier : "+fichier)
        if fichier_errone:
            flash ("fichier : "+fichier+" comporte une annotation vide")
        os.remove("./uploads/"+fichier)

    #On récupère les fichiers crées, en fait un fichier zip et on en propose
    #le téléchargement à l'utilisateur
    nomzipfile="./Static/Telechargements/sortie_enrichissement-"+datetime.now().strftime("%Y%m%d%H%M%S")+".zip"
    zippedfile=ZipFile(nomzipfile,"w")
    for fichier in os.listdir("./Sortie/Enrichis"):
        zippedfile.write("./Sortie/Enrichis/"+fichier)
        os.remove("./Sortie/Enrichis/"+fichier)
    zippedfile.close()
    flash("Le fichier de téléchargement a été créé et peut être retrouvé depuis la page de teléchargement")

    return redirect(url_for("enrich"))

#Page des négations
@app.route('/negations')
def negations():
    return render_template("pageneg.html")

#Lancement de l'analyse des négations
@app.route('/runneg', methods = ['POST'])
def runneg():
    #On vérifie qu'il y a bien au moins un fichier
    if 'negation_file' not in request.files:
            flash('Pas de fichier séléctionné, veuillez sélectionner au moins un fichier')
            return redirect(url_for("negations"))
    #On récupère la liste des fichiers du formulaire
    fichiers = request.files.getlist('negation_file')
    type_neg= request.form["type_neg"]
    variables= request.form.getlist("type_neg")
    #si pas=0, si complet=1, si les deux=2
    """if type_neg=="neg_pas":
        type_neg=0
    elif type_neg=="neg_tout":
        type_neg=1
    elif type_neg=="neg_deux":
        type_neg=2"""
    if "neg_pas" in variables:
        if "neg_tout" in variables:
            type_neg=2
        else:
            type_neg=0
    if "neg_tout" in variables:
        if "neg_pas" in variables:
            type_neg=2
        else:
            type_neg=1
    if type_neg not in (0,1,2):
        flash('veuillez sélectionner au moins un type de négation')
        return redirect(url_for("negations"))
    #On stocke de façon temporaire les fichiers
    for fichier in fichiers:
        if fichier and allowed_file(fichier.filename):
            nomfichier = secure_filename(fichier.filename)
            fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier))
            # os.chmod(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier), stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
        else:
            flash("fichier invalide: "+fichier.filename)
    #On lance l'enrichissement, ce qui crée les fichiers de résultat
    for fichier in os.listdir(app.config['UPLOAD_FOLDER']):
        lancement_negations("./uploads/"+fichier,type_neg)
        flash("negations fichier : "+fichier)
        os.remove("./uploads/"+fichier)

    #On récupère les fichiers crées, en fait un fichier zip (a mettre dans dossier téléchargements), et on en propose
    #le téléchargement à l'utilisateur
    nomzipfile="./Static/Telechargements/sortie_negations-"+datetime.now().strftime("%Y%m%d%H%M%S")+".zip"
    zippedfile=ZipFile(nomzipfile,"w")
    for fichier in os.listdir("./Sortie/Negations"):
        zippedfile.write("./Sortie/Negations/"+fichier)
        os.remove("./Sortie/Negations/"+fichier)
    zippedfile.close()
    flash("Le fichier de téléchargement a été crée et peut être retrouvé depuis la page de teléchargement")

    return redirect(url_for("negations"))

#Page des liaisons
@app.route('/liaisons')
def liaisons():
    return render_template("pageliai.html")

#Lancement analyse des liaisons
@app.route('/runliai', methods = ['POST'])
def runliai():
    if 'liaison_file' not in request.files:
            flash('Pas de fichier séléctionné, veuillez sélectionner au moins un fichier')
            return redirect(url_for("liaisons"))
    #On récupère la liste des fichiers du formulaire
    fichiers = request.files.getlist('liaison_file')
    type_liai= request.form["type_liai"]

    #On récupère le type de liaison
    if type_liai=="LF_LEX":
        type_liai=0
    elif type_liai=="LF_MOR":
        type_liai=1
    #On stocke de façon temporaire les fichiers
    for fichier in fichiers:
        if fichier and allowed_file(fichier.filename):
            nomfichier = secure_filename(fichier.filename)
            fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier))
            # os.chmod(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier), stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
        else:
            flash("fichier invalide: "+fichier.filename)
    #On lance l'enrichissement, ce qui crée les fichiers de résultat
    for fichier in os.listdir(app.config['UPLOAD_FOLDER']):
        #LF_LEX
        if type_liai==0:
            lancement_LF_LEX("./uploads/"+fichier)
            flash("lf_lex fichier : "+fichier)
        #LF_MOR
        elif type_liai==1:
            lancement_LF_MOR("./uploads/"+fichier)
            flash("lf_mor fichier : "+fichier)
        os.remove("./uploads/"+fichier)

    #On récupère les fichiers crées, en fait un fichier zip (a mettre dans dossier téléchargements), et on en propose
    #le téléchargement à l'utilisateur
    if type_liai==0:
        nomzipfile="./Static/Telechargements/sortie_LF_LEX-"+datetime.now().strftime("%Y%m%d%H%M%S")+".zip"
    if type_liai==1:
        nomzipfile="./Static/Telechargements/sortie_LF_MOR-"+datetime.now().strftime("%Y%m%d%H%M%S")+".zip"
    zippedfile=ZipFile(nomzipfile,"w")
    #LFLEX et LFMOR: different fichiers sortie
    if type_liai==0:
        for fichier in os.listdir("./Sortie/LF_LEX"):
            zippedfile.write("./Sortie/LF_LEX/"+fichier)
            os.remove("./Sortie/LF_LEX/"+fichier)
    elif type_liai==1:
        for fichier in os.listdir("./Sortie/LF_MOR"):
            zippedfile.write("./Sortie/LF_MOR/"+fichier)
            os.remove("./Sortie/LF_MOR/"+fichier)
    zippedfile.close()
    flash("Le fichier de téléchargement a été crée et peut être retrouvé depuis la page de teléchargement")

    return redirect(url_for("liaisons"))

#Page d'analyse brut
@app.route('/analysebrut')
def analysebrut():
    return render_template("pageanalysebrut.html")

#Lancement analyse brut
@app.route('/runbrut', methods = ['POST'])
def runbrut():
    if 'brut_file' not in request.files:
            flash('Pas de fichier séléctionné, veuillez sélectionner au moins un fichier')
            return redirect(url_for("analysebrut"))
    #On récupère la liste des fichiers du formulaire
    fichiers = request.files.getlist('brut_file')
    variables= request.form.getlist("choix_variable")

    # Ajouter une variable de type de liaison permettant à l'utilisateur de choisir le type de Liaisons Facultatives à extraire.
    # Par défaut, il est défini sur "LF1 + LF3".
    liaison_type = request.form.get("liaison_type", "LF1_LF3")

    # On stocke de façon temporaire les fichiers
    for fichier in fichiers:
        if fichier and allowed_file(fichier.filename):
            nomfichier = secure_filename(fichier.filename)
            fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier))
            # os.chmod(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier), stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
        else:
            flash("fichier invalide: "+fichier.filename)
    for variable in variables:
    # On stocke de façon temporaire les fichiers
    # On lance l'enrichissement, ce qui crée les fichiers de résultat
    # Passage du type de liaison à la fonction extract_brut()
        extract_brut(filenames=os.listdir(app.config['UPLOAD_FOLDER']), variable=variable,
            newfile="extraction brute",
            liaison_type=liaison_type)
        flash(variable + " fait")
    for fichier in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove("./uploads/"+fichier)

    #On récupère les fichiers crées, en fait un fichier zip (a mettre dans dossier téléchargements), et on en propose
    #le téléchargement à l'utilisateur
    nomzipfile="./Static/Telechargements/sortie_brut-"+datetime.now().strftime("%Y%m%d%H%M%S")+".zip"
    zippedfile=ZipFile(nomzipfile,"w")
    for fichier in os.listdir("./Sortie/Extraction_Brute"):
        zippedfile.write("./Sortie/Extraction_Brute/"+fichier)
        os.remove("./Sortie/Extraction_Brute/"+fichier)
    zippedfile.close()
    flash("Le fichier de téléchargement a été crée et peut être retrouvé depuis la page de teléchargement")

    return redirect(url_for("analysebrut"))

#Page des analyses organisées, avec et sans regroupement
@app.route('/analyseorg')
def analyseorg():
    return render_template("pageanalyseorg.html")

#Lancement analyse organisées
@app.route('/runorg', methods = ['POST'])
def runorg():
    if 'org_file' not in request.files:
            flash('Pas de fichier séléctionné, veuillez sélectionner au moins un fichier')
            return redirect(url_for("analyseorg"))
    #On récupère la liste des fichiers du formulaire
    fichiers = request.files.getlist('org_file')
    variables= request.form.getlist("choix_variable")
    regroupement= request.form["org_regr"]
    types_reg=request.form.getlist('type_reg')
    type_limit=request.form["limit"]
    limit_value=request.form["limit_value"]
    for fichier in fichiers:
        if fichier and allowed_file(fichier.filename):
            nomfichier = secure_filename(fichier.filename)
            fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier))
            # os.chmod(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier), stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
        else:
            flash("fichier invalide: "+fichier.filename)
    regs=""
    #On choisit les options de l'analyse en fonction des informations récupérées du formulaire
    if regroupement=="reg":
        if "reg_a" in types_reg:
            regs+="a"
        if "reg_b" in types_reg:
            regs+="b"
        if "reg_c" in types_reg:
            regs+="c"
    if type_limit=="no_limit":
        type_limit=0
    elif type_limit=="limit_eno":
        type_limit=10
    elif type_limit=="limit_tok":
        type_limit=20
    elif type_limit=="limit_tps":
        type_limit=30
    for variable in variables:
        if variable=="catégories_grammaticales":
            for variante in ["ADJ","ADV","AUX","DET","EPE","ETR","FNO","INT","KON","LOC","MLT","NAM","NOM","NUM","PRO","PRP","PRT","SYM","TRC","VER","SENT"]:
                extract_organisee_reg(os.listdir(app.config['UPLOAD_FOLDER']),variante,regroupements=regs)
        else:
            if type_limit!=0:
                extract_organisee_reg(os.listdir(app.config['UPLOAD_FOLDER']),variable,regroupements=regs,limit=type_limit,limit_value=int(limit_value))
            else:
                extract_organisee_reg(os.listdir(app.config['UPLOAD_FOLDER']),variable,regroupements=regs)
        flash(variable+" fait")
    for fichier in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove("./uploads/"+fichier)

    #On récupère les fichiers crées, en fait un fichier zip (a mettre dans dossier téléchargements), et on en propose
    #le téléchargement à l'utilisateur
    nomzipfile="./Static/Telechargements/sortie_organisee-"+datetime.now().strftime("%Y%m%d%H%M%S")+".zip"
    zippedfile=ZipFile(nomzipfile,"w")
    for fichier in os.listdir("./Sortie/Extraction_Organisee_Reg"):
        zippedfile.write("./Sortie/Extraction_Organisee_Reg/"+fichier)
        os.remove("./Sortie/Extraction_Organisee_Reg/"+fichier)
    zippedfile.close()
    flash("Le fichier de téléchargement a été crée et peut être retrouvé depuis la page de teléchargement")

    return redirect(url_for("analyseorg"))

#Page des liaisons
@app.route('/analyseliai')
def analyseliai():
    mot1_choisi=""
    mot2_choisi=""
    try:
        #on ouvre le dictionnaire qui contient la sauvegarde des données si il existe
        #dictionnaire stocké sous la forme d'un fichier texte que l'on interpète pour recupérer le dict
        dictio=ast.literal_eval(open("svg_dict.txt","r",encoding="utf8").read())
    except Exception:
        dictio=""
        mot1_uniques=[]
        mot2_uniques=[]

    if dictio!="":
        #On sépare les mot1 et mot2 uniques
        mot1_uniques=[]
        mot2_uniques=[]
        for key in dictio.keys():
            if key[0] not in mot1_uniques:
                mot1_uniques.append(key[0])
            if key[1] not in mot2_uniques:
                mot2_uniques.append(key[1])
        #On trie par ordre alphabétique
        mot1_uniques.sort(key=u_to_str)
        mot2_uniques.sort(key=u_to_str)
    return render_template("pageanalyseliai.html",dictio=dictio,mots1=mot1_uniques,mots2=mot2_uniques,mot1choisi=mot1_choisi,mot2choisi=mot2_choisi)

#affichage des liaisons correspondant aux mots choisis et aux type de liaison par l'utilisateur
@app.route('/runaffichageliai', methods=['POST'])
def affichageliai():
    try:
        dictio=ast.literal_eval(open("svg_dict.txt", "r", encoding="utf8").read())
    except Exception:
        dictio=""

    if dictio!="":
        mot1_uniques=[]
        mot2_uniques=[]

        # On récupère les choix de l'utilisateur
        mot1_choisi=request.form["mot1"]
        if mot1_choisi=="pas_mot1":
            mot1_choisi=""

        mot2_choisi=request.form["mot2"]
        if mot2_choisi=="pas_mot2":
            mot2_choisi=""

        # Création des listes des mots uniques
        for key in dictio.keys():
            if key[0] not in mot1_uniques:
                mot1_uniques.append(key[0])
            if key[1] not in mot2_uniques:
                mot2_uniques.append(key[1])
        mot1_uniques.sort(key=u_to_str)
        mot2_uniques.sort(key=u_to_str)

        # On récupère le type de liaison sélectionné, par défaut: tout (LF1+LF3)
        lf_type_choisi = request.form.get("lf_type", "tout")  # Ajout de cette ligne

        # On filtre les données en fonction des choix de l'utilisateur
        dictio_filtre_fichier = {k: v for k, v in dictio.items() if
                                 (lf_type_choisi == "tout" or v[4] == lf_type_choisi) and
                                 (mot1_choisi == "" or k[0] == mot1_choisi) and
                                 (mot2_choisi == "" or k[1] == mot2_choisi)}

        # On filtre les statistiques en fonction du type de liaison
        dictio_filtre_stats = {k: v for k, v in dictio.items() if lf_type_choisi == "tout" or v[4] == lf_type_choisi}

        # Analyse statistique : comptage des occurrences des mots
        mot1_counter_stats = Counter(k[0] for k in dictio_filtre_stats.keys())
        mot2_counter_stats = Counter(k[1] for k in dictio_filtre_stats.keys())
        mot1_mot2_counter = Counter(f"{k[0]} {k[1]}" for k in dictio_filtre_stats.keys())

        # Fonction pour calculer les pourcentages
        def compute_percentage(counter):
            total = sum(counter.values()) if counter else 1  # Évite la division par 0
            return list((k, v, f"{(v / total) * 100:.2f}%") for k, v in counter.items())

        mot1_stats = compute_percentage(mot1_counter_stats)
        mot2_stats = compute_percentage(mot2_counter_stats)
        mot1_mot2_stats = compute_percentage(mot1_mot2_counter)

        # Stockage des statistiques dans la session pour le téléchargement
        session["mot1_stats"] = mot1_stats
        session["mot2_stats"] = mot2_stats
        session["mot1_mot2_stats"] = mot1_mot2_stats

        # Tri des statistiques par fréquence (décroissant) et ordre ascii en cas d'égalité
        mot1_stats.sort(key=lambda item: (-item[1], u_to_str(item[0])))
        mot2_stats.sort(key=lambda item: (-item[1], u_to_str(item[0])))
        mot1_mot2_stats.sort(key=lambda item: (-item[1], u_to_str(item[0])))

        return render_template("pageanalyseliai.html",
                               dictio=dictio,
                               mots1=mot1_uniques, mots2=mot2_uniques,
                               mot1choisi=mot1_choisi, mot2choisi=mot2_choisi,
                               lf_type_choisi=lf_type_choisi,  # 🔹 Ajout pour garder la sélection
                               mot1_stats=mot1_stats,
                               mot2_stats=mot2_stats,
                               mot1_mot2_stats=mot1_mot2_stats,
                               dictio_filtre_fichier=dictio_filtre_fichier)


#Analyse des fichiers pour récupérer contextes de liaison
@app.route('/runanalyseliai', methods = ['POST'])
def runanalyseliai():
    #On vérifie qu'il y a bien au moins un fichier
    if 'a_liai_file' not in request.files:
            flash('Pas de fichier séléctionné, veuillez sélectionner au moins un fichier')
            return redirect(url_for("analyseliai"))

    #On récupère la liste des fichiers du formulaire
    fichiers = request.files.getlist('a_liai_file')

    #On stocke de façon temporaire les fichiers
    for fichier in fichiers:
        if fichier and allowed_file(fichier.filename):
            nomfichier = secure_filename(fichier.filename)
            fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier))
            # os.chmod(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier), stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
            os.chmod(os.path.join(app.config['UPLOAD_FOLDER'], nomfichier), stat.S_IRWXU | stat.S_IRWXG)
        else:
            flash("fichier invalide: "+fichier.filename)
    #On lance l'enrichissement, ce qui crée la sauvegarde du dictionnaire contenant toutes les liaisons
    analyser_liaisons(os.listdir(app.config['UPLOAD_FOLDER']))

    for fichier in os.listdir(app.config['UPLOAD_FOLDER']):
        flash("analysé fichier : "+fichier)
        #os.remove("./uploads/"+fichier)
    return redirect(url_for("analyseliai"))

#Suppression du fichier des liaisons
@app.route('/effacerliai', methods= ['POST'])
def effacerliai():
    os.remove("svg_dict.txt")
    for fichier in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove("./uploads/"+fichier)
    flash("fichiers effacés")
    return redirect(url_for("analyseliai"))

#Extraction des liaisons selon les choix de l'utilisateur
@app.route('/extractliai', methods = ['POST'])
def extractliai():
    regroupement= request.form["org_regr"]
    regs=""
    types_reg=request.form.getlist('type_reg')
    if regroupement=="reg":
        if "reg_a" in types_reg:
            regs+="a"
        if "reg_b" in types_reg:
            regs+="b"
        if "reg_c" in types_reg:
            regs+="c"
    types_reg=request.form.getlist('type_reg')
    mot1=request.form["mot1analyse"]
    mot2=request.form["mot2analyse"]
    extract_organisee_reg(os.listdir(app.config['UPLOAD_FOLDER']),"lf",regroupements=regs,traitement_liaison=True,liaison_list=[mot1,mot2])

    #On récupère les fichiers crées, en fait un fichier zip (a mettre dans dossier téléchargements), et on en propose
    #le téléchargement à l'utilisateur
    nomzipfile="./Static/Telechargements/sortie_analyse_liaisons-"+datetime.now().strftime("%Y%m%d%H%M%S")+".zip"
    zippedfile=ZipFile(nomzipfile,"w")
    for fichier in os.listdir("./Sortie/Extraction_Organisee_Reg"):
        zippedfile.write("./Sortie/Extraction_Organisee_Reg/"+fichier)
        os.remove("./Sortie/Extraction_Organisee_Reg/"+fichier)
    zippedfile.close()
    flash("Le fichier de téléchargement a été crée et peut être retrouvé depuis la page de teléchargement")

    return redirect(url_for("analyseliai"))

@app.route('/generate_stats_zip', methods=['POST'])
def generate_stats_zip():
    mot1_stats = session.get("mot1_stats", [])
    mot2_stats = session.get("mot2_stats", [])
    mot1_mot2_stats = session.get("mot1_mot2_stats", [])

    if not (mot1_stats or mot2_stats or mot1_mot2_stats):
        flash("Aucune donnée à télécharger.")
        return redirect(url_for("analyseliai"))

    telechargement_dir = "./Static/Telechargements"
    os.makedirs(telechargement_dir, exist_ok=True)

    csv_filename = f"statistiques_liaisons_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    csv_filepath = os.path.join(telechargement_dir, csv_filename)

    # Écriture des données dans un fichier CSV
    with open(csv_filepath, "w", encoding="utf-8") as f:
        f.write("Mot 1,Fréquence,Pourcentage,Mot 2,Fréquence,Pourcentage,Mot 1,Mot 2,Fréquence,Pourcentage\n")

        for i in range(max(len(mot1_stats), len(mot2_stats), len(mot1_mot2_stats))):
            row = []

            if i < len(mot1_stats):
                row.extend(mot1_stats[i])
            else:
                row.extend(["", "", ""])

            if i < len(mot2_stats):
                row.extend(mot2_stats[i])
            else:
                row.extend(["", "", ""])

            if i < len(mot1_mot2_stats):
                mot1, mot2 = mot1_mot2_stats[i][0].split(' ')
                row.append(mot1)
                row.append(mot2)
                row.append(mot1_mot2_stats[i][1])
                row.append(mot1_mot2_stats[i][2])
            else:
                row.extend(["", "", "", ""])

            f.write(",".join(map(str, row)) + "\n")

    zip_filename = f"sortie_statistiques_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
    zip_filepath = os.path.join(telechargement_dir, zip_filename)

    with ZipFile(zip_filepath, "w") as zippedfile:
        zippedfile.write(csv_filepath, os.path.basename(csv_filepath))
    os.remove(csv_filepath)

    flash(f"Le fichier de téléchargement a été créé et peut être retrouvé depuis la page de téléchargement")
    return redirect(url_for("analyseliai"))


#Lancement de l'app
app.run(host = "localhost", port = 5000)
