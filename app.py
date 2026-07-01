import streamlit as st
import pandas as pd
import os

# Configuration de la page GRC
st.set_page_config(page_title="DNK Security - SOC2 GRC", layout="wide")
st.title("🛡️ DNK Security - Plateforme GRC & Suivi SOC2")

# --- CHARGEMENT DES DONNÉES EXCEL/CSV ---
@st.cache_data
def load_grc_data(filename):
    if os.path.exists(filename):
        # On lit le CSV en ignorant les lignes vides potentielles
        df = pd.read_csv(filename)
        return df
    return None

# Chargement de vos deux fichiers clés
df_controls = load_grc_data("1 - SOC2_ControlList - DNK Security.xlsx - Control List.csv")
df_readiness = load_grc_data("1 - SOC2_ControlList - DNK Security.xlsx - Readiness.csv")

# Menu latéral
menu = ["📊 Dashboard Readiness", "📋 Liste des Contrôles (Control List)", "🎲 Gestion des Risques"]
choice = st.sidebar.selectbox("Navigation", menu)

# ----------------------------------------------------
# 1. DASHBOARD READINESS
# ----------------------------------------------------
if choice == "📊 Dashboard Readiness":
    st.header("📈 État de Préparation Audit SOC2")
    
    if df_readiness is not None:
        st.write("Voici le résumé de votre niveau de maturité actuel issu de votre fichier Excel.")
        
        # Affichage propre des données brutes de préparation
        st.dataframe(df_readiness, use_container_width=True)
        
        # Optionnel : Si le fichier contient des données numériques, Streamlit peut générer un graphique rapide
        st.subheader("Visualisation de l'avancement")
        st.info("💡 Les données ci-dessus représentent vos jalons de préparation (Readiness).")
    else:
        st.error("⚠️ Le fichier 'Readiness.csv' est introuvable. Assurez-vous qu'il est bien dans le même dossier.")

# ----------------------------------------------------
# 2. LISTE DES CONTRÔLES (CONTROL LIST)
# ----------------------------------------------------
elif choice == "📋 Liste des Contrôles (Control List)":
    st.header("🔍 Registre Complet des Contrôles SOC2")
    
    if df_controls is not None:
        # Barre de recherche textuelle globale
        search_query = st.text_input("🔍 Rechercher un contrôle (par mot-clé, ID, critère...)", "")
        
        # Filtrer le DataFrame si une recherche est tapée
        if search_query:
            # On cherche dans toutes les colonnes textuelles
            mask = df_controls.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            filtered_df = df_controls[mask]
        else:
            filtered_df = df_controls

        # Métriques rapides sur la liste affichée
        st.write(f"Affichage de **{len(filtered_df)}** lignes sur un total de {len(df_controls)} contrôles.")
        
        # Affichage sous forme de tableau interactif et triable
        st.dataframe(filtered_df, use_container_width=True)
        
        # Mode d'inspection ligne par ligne (Pratique pour les audits)
        st.subheader("👀 Inspecteur de Contrôle Unique")
        selected_index = st.selectbox("Sélectionner une ligne à inspecter en détail :", filtered_df.index)
        
        if selected_index is not None:
            row_data = filtered_df.loc[selected_index]
            with st.container():
                st.markdown(f"### Détails de la ligne {selected_index}")
                # Affichage sous forme de fiches clés/valeurs claires
                for col_name, val in row_data.items():
                    if pd.notna(val):
                        st.markdown(f"**{col_name} :** {val}")
    else:
        st.error("⚠️ Le fichier 'Control List.csv' est introuvable. Assurez-vous qu'il est bien dans le même dossier.")

# ----------------------------------------------------
# 3. GESTION DES RISQUES
# ----------------------------------------------------
elif choice == "🎲 Gestion des Risques":
    st.header("🎲 Registre Interne des Risques")
    st.write("Ce module vous permet de lister les risques de l'entreprise parallèlement à vos contrôles SOC2.")
    
    if 'risk_db' not in st.session_state:
        st.session_state.risk_db = []
        
    with st.form("risk_form", clear_on_submit=True):
        risk_title = st.text_input("Description du risque")
        col1, col2 = st.columns(2)
        with col1:
            likelihood = st.slider("Vraisemblance (1-5)", 1, 5, 3)
        with col2:
            impact = st.slider("Impact (1-5)", 1, 5, 3)
        submit = st.form_submit_button("Ajouter")
        
    if submit and risk_title:
        score = likelihood * impact
        st.session_state.risk_db.append({"Risque": risk_title, "Score": score})
        st.success("Risque ajouté !")
        
    if st.session_state.risk_db:
        st.dataframe(pd.DataFrame(st.session_state.risk_db))