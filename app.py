import streamlit as st
import pandas as pd
import os
import json

# Configuration de la page
st.set_page_config(page_title="BizGRC Multi-Clients", layout="wide")
st.title("🛡️ BizGRC - Plateforme GRC Multi-Clients")

# --- GESTION DE LA PERSISTANCE (DOSSIER CLIENTS) ---
DATA_DIR = "clients_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Chargement des matrices Excel d'origine (Modèles de base)
@st.cache_data
def load_base_template(filename):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return None

df_base_controls = load_base_template("1 - SOC2_ControlList - DNK Security.xlsx - Control List.csv")
df_base_readiness = load_base_template("1 - SOC2_ControlList - DNK Security.xlsx - Readiness.csv")

# ----------------------------------------------------
# GESTION DES CLIENTS (Sidebar)
# ----------------------------------------------------
st.sidebar.header("🏢 Gestion des Clients")

# Liste des clients existants (basée sur les fichiers sauvegardés)
existing_clients = [f.replace(".json", "") for f in os.listdir(DATA_DIR) if f.endswith(".json")]

# Ajouter un nouveau client
new_client = st.sidebar.text_input("➕ Ajouter un nouveau client :")
if st.sidebar.button("Créer le compte client"):
    if new_client and new_client not in existing_clients:
        # Initialisation des données du client avec le modèle de base
        initial_data = {
            "nom": new_client,
            "statuts_controles": {} # Stockera l'état {ID_Controle: True/False}
        }
        with open(os.path.join(DATA_DIR, f"{new_client}.json"), "w") as f:
            json.dump(initial_data, f)
        st.sidebar.success(f"Client '{new_client}' créé !")
        st.rerun()

# Sélection du client actif
if existing_clients:
    client_actif = st.sidebar.selectbox("🎯 Client Actif :", existing_clients)
else:
    client_actif = None
    st.sidebar.warning("Veuillez créer un premier client pour commencer.")

# Menu principal de navigation
st.sidebar.markdown("---")
menu = ["📊 Tableau de bord Client", "📋 Audit & Contrôles SOC2", "🎲 Registre des Risques Client"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# Chargement des données du client sélectionné
def load_client_data(client_name):
    path = os.path.join(DATA_DIR, f"{client_name}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def save_client_data(client_name, data):
    path = os.path.join(DATA_DIR, f"{client_name}.json")
    with open(path, "w") as f:
        json.dump(data, f)

# ----------------------------------------------------
# 1. TABLEAU DE BORD CLIENT
# ----------------------------------------------------
if choice == "📊 Tableau de bord Client":
    if client_actif:
        st.header(f"📊 Tableau de bord — {client_actif}")
        client_data = load_client_data(client_actif)
        
        if df_base_controls is not None:
            total_controls = len(df_base_controls)
            # Compter les contrôles cochés pour ce client
            statuts = client_data.get("statuts_controles", {})
            controles_valides = sum(1 for v in statuts.values() if v is True)
            
            # Calcul du score d'avancement réel du client
            score_avancement = int((controles_valides / total_controls) * 100) if total_controls > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Total des contrôles à auditer", value=total_controls)
            col2.metric(label="Contrôles Validés", value=f"{controles_valides} / {total_controls}")
            col3.metric(label="Score de Conformité SOC2", value=f"{score_avancement}%")
            
            st.progress(score_avancement / 100)
            
            # Affichage de la feuille "Readiness" de base pour référence
            if df_base_readiness is not None:
                st.subheader("🎯 Objectifs de préparation (Référentiel Global)")
                st.dataframe(df_base_readiness, use_container_width=True)
        else:
            st.error("Modèle 'Control List.csv' introuvable.")
    else:
        st.info("Veuillez sélectionner ou créer un client dans la barre latérale.")

# ----------------------------------------------------
# 2. AUDIT & CONTRÔLES SOC2 (INTERACTIF)
# ----------------------------------------------------
elif choice == "📋 Audit & Contrôles SOC2":
    if client_actif:
        st.header(f"📋 Audit des contrôles pour : {client_actif}")
        client_data = load_client_data(client_actif)
        
        if df_base_controls is not None:
            # Recherche
            search_query = st.text_input("🔍 Filtrer les contrôles :", "")
            
            # Copie pour manipulation
            df_display = df_base_controls.copy()
            id_col = df_display.columns[0] # Première colonne comme ID unique
            desc_col = df_display.columns[1] if len(df_display.columns) > 1 else id_col
            
            if search_query:
                mask = df_display.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
                df_display = df_display[mask]
                
            st.write(f"Veuillez évaluer les contrôles ci-dessous. Vos modifications sont enregistrées pour **{client_actif}**.")
            
            # Formulaire pour sauvegarder les changements d'état
            statuts_actuels = client_data.get("statuts_controles", {})
            
            for idx, row in df_display.iterrows():
                ctrl_id = str(row[id_col])
                ctrl_desc = str(row[desc_col])
                
                # Récupérer l'état déjà enregistré pour ce client (False par défaut)
                deja_coche = statuts_actuels.get(ctrl_id, False)
                
                with st.container():
                    col_check, col_text = st.columns([1, 12])
                    
                    # Case à cocher interactive
                    nouveau_statut = col_check.checkbox("", value=deja_coche, key=f"check_{client_actif}_{ctrl_id}")
                    col_text.markdown(f"**{ctrl_id}** — {ctrl_desc}")
                    
                    # Si le statut change, on met à jour le dictionnaire du client
                    if nouveau_statut != deja_coche:
                        statuts_actuels[ctrl_id] = nouveau_statut
                        client_data["statuts_controles"] = statuts_actuels
                        save_client_data(client_actif, client_data)
                        st.toast(f"Statut mis à jour pour {ctrl_id}", icon="💾")
                    
                    st.divider()
        else:
            st.error("Fichier 'Control List.csv' manquant.")
    else:
        st.info("Sélectionnez un client dans la barre latérale.")

# ----------------------------------------------------
# 3. REGISTRE DES RISQUES CLIENT
# ----------------------------------------------------
elif choice == "🎲 Registre des Risques Client":
    if client_actif:
        st.header(f"🎲 Gestion des Risques — {client_actif}")
        client_data = load_client_data(client_actif)
        
        # Initialiser la liste des risques pour ce client si elle n'existe pas
        if "risques" not in client_data:
            client_data["risques"] = []
            
        with st.form("risk_form_client", clear_on_submit=True):
            st.subheader("Signaler un risque propre à ce client")
            intitule = st.text_input("Description de l'incident / risque")
            vraisemblance = st.slider("Vraisemblance (1-5)", 1, 5, 3)
            impact = st.slider("Impact (1-5)", 1, 5, 3)
            submit = st.form_submit_button("Enregistrer le risque")
            
        if submit and intitule:
            score = vraisemblance * impact
            client_data["risques"].append({
                "Description": intitule,
                "Score": score,
                "Sévérité": "Haute" if score >= 15 else "Moyenne" if score >= 8 else "Faible"
            })
            save_client_data(client_actif, client_data)
            st.success("Risque ajouté au registre du client !")
            
        # Affichage du registre du client
        if client_data["risques"]:
            st.subheader("Risques en cours de suivi")
            st.dataframe(pd.DataFrame(client_data["risques"]), use_container_width=True)
    else:
        st.info("Sélectionnez un client dans la barre latérale.")
