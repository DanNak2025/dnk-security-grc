import streamlit as st
import pandas as pd
import os
import json

# Configuration de la page
st.set_page_config(page_title="DNK Security - GRC Platform", layout="wide")
st.title("🛡️ DNK Security - Plateforme GRC Interne")

# --- CONTEXTE ET PERSISTANCE DES DONNÉES ---
SAVE_FILE = "etat_grc.json"

# Fonction pour charger l'avancement sauvegardé
def load_grc_state():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {"controles_coches": {}, "risques": []}

# Fonction pour sauvegarder l'avancement
def save_grc_state(state):
    with open(SAVE_FILE, "w") as f:
        json.dump(state, f)

# Initialisation de l'état
if 'grc_state' not in st.session_state:
    st.session_state.grc_state = load_grc_state()

# Chargement de vos matrices Excel/CSV de référence
@st.cache_data
def load_excel_template(filename):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return None

df_controls = load_excel_template("1 - SOC2_ControlList - DNK Security.xlsx - Control List.csv")
df_readiness = load_excel_template("1 - SOC2_ControlList - DNK Security.xlsx - Readiness.csv")

# --- MENU DE NAVIGATION ---
menu = ["📊 Tableau de Bord & Readiness", "📋 Registre des Contrôles SOC2", "🎲 Registre des Risques"]
choice = st.sidebar.selectbox("Navigation GRC", menu)

# ----------------------------------------------------
# 1. TABLEAU DE BORD & READINESS
# ----------------------------------------------------
if choice == "📊 Tableau de Bord & Readiness":
    st.header("📈 État de Préparation de l'Entreprise")
    
    if df_controls is not None:
        total_controls = len(df_controls)
        coches = st.session_state.grc_state.get("controles_coches", {})
        total_valides = sum(1 for v in coches.values() if v is True)
        
        # Pourcentage de conformité réel
        score_conformite = int((total_valides / total_controls) * 100) if total_controls > 0 else 0
        total_risques = len(st.session_state.grc_state.get("risques", []))
        
        # Affichage des indicateurs clés (KPIs)
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Contrôles SOC2 Audités", value=f"{total_valides} / {total_controls}")
        col2.metric(label="Score de Conformité Global", value=f"{score_conformite}%")
        col3.metric(label="Risques Internes Identifiés", value=total_risques)
        
        st.markdown("**Progression de la mise en conformité :**")
        st.progress(score_conformite / 100)
        st.write("")
    else:
        st.error("⚠️ Fichier 'Control List.csv' introuvable.")

    # Affichage de votre fichier "Readiness" de référence
    st.subheader("🎯 Objectifs et Jalons de Préparation (Readiness)")
    if df_readiness is not None:
        st.dataframe(df_readiness, use_container_width=True)
    else:
        st.info("Ajoutez le fichier 'Readiness.csv' pour afficher vos indicateurs spécifiques ici.")

# ----------------------------------------------------
# 2. REGISTRE DES CONTRÔLES SOC2 (INTERACTIF)
# ----------------------------------------------------
elif choice == "📋 Registre des Contrôles SOC2":
    st.header("📋 Évaluation Continue des Contrôles SOC2")
    st.write("Cochez les contrôles actuellement en place au sein de DNK Security. Vos modifications sont sauvegardées en temps réel.")

    if df_controls is not None:
        # Moteur de recherche rapide
        search_query = st.text_input("🔍 Rechercher un contrôle par mot-clé ou ID :", "")
        
        df_filtered = df_controls.copy()
        id_col = df_filtered.columns[0] # Identifiant unique (ex: critère CC1.1)
        desc_col = df_filtered.columns[1] if len(df_filtered.columns) > 1 else id_col
        
        if search_query:
            mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            df_filtered = df_filtered[mask]
            
        st.write(f"Affichage de **{len(df_filtered)}** contrôles.")
        
        # Boucle d'affichage interactif
        coches = st.session_state.grc_state.get("controles_coches", {})
        
        for idx, row in df_filtered.iterrows():
            ctrl_id = str(row[id_col])
            ctrl_desc = str(row[desc_col])
            
            # Récupérer l'état sauvegardé ou False par défaut
            deja_coche = coches.get(ctrl_id, False)
            
            with st.container():
                col_check, col_text = st.columns([1, 15])
                
                # Case à cocher pour ce contrôle
                nouveau_statut = col_check.checkbox("", value=deja_coche, key=f"ctrl_{ctrl_id}")
                col_text.markdown(f"**{ctrl_id}** — {ctrl_desc}")
                
                # Sauvegarde immédiate si l'utilisateur interagit
                if nouveau_statut != deja_coche:
                    coches[ctrl_id] = nouveau_statut
                    st.session_state.grc_state["controles_coches"] = coches
                    save_grc_state(st.session_state.grc_state)
                    st.toast(f"💾 Contrôle {ctrl_id} mis à jour !", icon="✅")
                
                st.divider()
    else:
        st.error("⚠️ Impossible de charger la liste des contrôles. Vérifiez la présence du fichier 'Control List.csv'.")

# ----------------------------------------------------
# 3. REGISTRE DES RISQUES
# ----------------------------------------------------
elif choice == "🎲 Registre des Risques":
    st.header("🎲 Registre des Risques de l'Entreprise")
    st.write("Identifiez, qualifiez et suivez les risques de sécurité pour DNK Security.")
    
    # Formulaire d'ajout de risque
    with st.form("risk_form_internal", clear_on_submit=True):
        st.subheader("⚠️ Déclarer un nouveau risque")
        intitule = st.text_input("Description du risque (ex: Fuite de données, Panne serveur...)")
        
        col1, col2 = st.columns(2)
        with col1:
            vraisemblance = st.slider("Vraisemblance (1 = Rare, 5 = Presque certain)", 1, 5, 3)
        with col2:
            impact = st.slider("Impact (1 = Mineur, 5 = Critique)", 1, 5, 3)
            
        submit = st.form_submit_button("Ajouter au registre")
        
    if submit and intitule:
        score = vraisemblance * impact
        severite = "Critique" if score >= 15 else "Moyen" if score >= 8 else "Faible"
        
        # Ajout à la liste et sauvegarde
        st.session_state.grc_state["risques"].append({
            "Description": intitule,
            "Vraisemblance": vraisemblance,
            "Impact": impact,
            "Score": score,
            "Sévérité": severite
        })
        save_grc_state(st.session_state.grc_state)
        st.success("Risque enregistré avec succès !")

    # Affichage du tableau des risques existants
    liste_risques = st.session_state.grc_state.get("risques", [])
    if liste_risques:
        st.subheader("Risques actuellement sous surveillance")
        df_risques = pd.DataFrame(liste_risques)
        
        # Colorer les lignes selon le score de risque pour une meilleure lisibilité
        st.dataframe(df_risques, use_container_width=True)
    else:
        st.info("Aucun risque enregistré pour le moment. Utilisez le formulaire ci-dessus.")
