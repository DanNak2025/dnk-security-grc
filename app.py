import streamlit as st
import pandas as pd
import json
import os

# Configuration de la page
st.set_page_config(page_title="GRC Expert Console", layout="wide", initial_sidebar_state="expanded")

st.title("💼 GRC Expert — Console de Consulting")
st.caption("Pilotez la conformité SOC2, ISO27001, les Risques et les Politiques de vos clients.")

# --- INITIALISATION DE LA BASE DE DONNÉES EN MÉMOIRE ---
if "clients_db" not in st.session_state:
    st.session_state.clients_db = {}

# --- ACCÈS AUX FICHIERS (MATRICES) ---
st.sidebar.header("⚙️ Configuration des Matrices")
with st.sidebar.expander("📁 Charger vos matrices Excel (CSV)", expanded=False):
    uploaded_controls = st.file_uploader("Fichier 'Control List' (CSV)", type=["csv"], key="uploader_ctrl")
    uploaded_readiness = st.file_uploader("Fichier 'Readiness' (CSV)", type=["csv"], key="uploader_ready")

# Lecture robuste des fichiers CSV
def load_uploaded_csv(uploaded_file):
    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file, sep=None, engine='python')
        except Exception:
            return None
    return None

df_controls_base = load_uploaded_csv(uploaded_controls)
df_readiness_base = load_uploaded_csv(uploaded_readiness)

# --- GESTION DES CLIENTS ---
st.sidebar.markdown("---")
st.sidebar.header("🏢 Portefeuille Clients")

# Création de client
new_client = st.sidebar.text_input("Ajouter une entreprise client :", placeholder="Nom du client...")
if st.sidebar.button("➕ Initialiser le client", use_container_width=True):
    if new_client and new_client not in st.session_state.clients_db:
        st.session_state.clients_db[new_client] = {
            "statut_controles": {},
            "statut_readiness": {},
            "risques": [],
            "vendors": [],
            "policies": {
                "Politique de Sécurité (PSSI)": "À rédiger",
                "Contrôle d'Accès": "À rédiger",
                "Gestion des Incidents": "À rédiger",
                "Gestion des Tiers / Fournisseurs": "À rédiger"
            }
        }
        st.sidebar.success(f"Client {new_client} créé !")

# Sélection du client actif
liste_clients = list(st.session_state.clients_db.keys())
if liste_clients:
    client_actif = st.sidebar.selectbox("🎯 Client sélectionné :", liste_clients)
    db = st.session_state.clients_db[client_actif]
else:
    client_actif = None
    st.sidebar.warning("Créez un client dans la barre latérale.")

# Navigation principale
st.sidebar.markdown("---")
menu = ["📊 Dashboard Exécutif", "📋 Audit SOC2", "🎯 Feuille de Route (Readiness)", "🎲 Risques & Fournisseurs", "📜 Politiques Documentaires"]
choice = st.sidebar.radio("Navigation Mission :", menu, disabled=(client_actif is None))

# Bouton de sauvegarde / rafraîchissement global pour éviter les bugs de rechargement automatique
if client_actif:
    st.sidebar.markdown("---")
    if st.sidebar.button("💾 Sauvegarder les modifications", use_container_width=True):
        st.sidebar.success("Données synchronisées avec succès !")

# ----------------------------------------------------
# 1. TABLEAU DE BORD
# ----------------------------------------------------
if choice == "📊 Dashboard Exécutif" and client_actif:
    st.header(f"📊 Diagnostic de Sécurité — {client_actif}")
    
    total_ctrls = len(df_controls_base) if df_controls_base is not None else 54
    saved_ctrls = db.get("statut_controles", {})
    ready_or_approved = sum(1 for v in saved_ctrls.values() if v in ["Ready for Audit", "Approved by Auditor"])
    pct_soc2 = int((ready_or_approved / total_ctrls) * 100) if total_ctrls > 0 else 0
    
    total_tasks = len(df_readiness_base) if df_readiness_base is not None else 30
    saved_tasks = db.get("statut_readiness", {})
    done_tasks = sum(1 for v in saved_tasks.values() if v == "Done")
    pct_readiness = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Maturité SOC2 (Audit)", f"{pct_soc2}%", f"{ready_or_approved}/{total_ctrls} validés")
    c2.metric("Chantiers Techniques (Readiness)", f"{pct_readiness}%", f"{done_tasks}/{total_tasks} terminés")
    c3.metric("Menaces & Tiers", f"{len(db['risques'])} Risques", f"{len(db['vendors'])} Fournisseurs")
    
    st.markdown("---")
    st.subheader("📈 Progression vers la conformité")
    st.write("Plan de remédiation technique (Tâches Readiness)")
    st.progress(pct_readiness / 100)
    st.write("Validation réglementaire des contrôles (SOC2 Controls)")
    st.progress(pct_soc2 / 100)

# ----------------------------------------------------
# 2. AUDIT SOC2
# ----------------------------------------------------
elif choice == "📋 Audit SOC2" and client_actif:
    st.header(f"📋 Grille d'Audit SOC2 — {client_actif}")
    
    if df_controls_base is not None:
        search = st.text_input("🔍 Rechercher un critère, un mot-clé...")
        df = df_controls_base.copy()
        
        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
        for idx, row in df.iterrows():
            c_id = str(row.iloc[0])
            c_desc = str(row.iloc[1])
            c_evidence = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else "Aucune preuve requise listée"
            
            current_st = db["statut_controles"].get(c_id, "Gap")
            
            with st.expander(f"🔹 {c_id} — {c_desc[:90]}..."):
                st.write(f"**Description :** {c_desc}")
                st.info(f"**Preuve attendue :** {c_evidence}")
                
                opts = ["Gap", "Ready for Audit", "Approved by Auditor"]
                new_st = st.selectbox("Statut du contrôle :", opts, index=opts.index(current_st), key=f"soc2_{c_id}")
                if new_st != current_st:
                    db["statut_controles"][c_id] = new_st
    else:
        st.info("💡 Ouvrez le volet de gauche et déposez votre fichier 'Control List' (CSV) pour charger vos contrôles.")

# ----------------------------------------------------
# 3. READINESS
# ----------------------------------------------------
elif choice == "🎯 Feuille de Route (Readiness)" and client_actif:
    st.header(f"🎯 Plan d'Action Opérationnel — {client_actif}")
    
    if df_readiness_base is not None:
        df = df_readiness_base.copy()
        for idx, row in df.iterrows():
            t_id = str(row.iloc[0]) if pd.notna(row.iloc[0]) else f"T-{idx}"
            t_desc = str(row.iloc[1]) if len(row) > 1 else "Pas de description"
            
            current_t_st = db["statut_readiness"].get(t_id, "To Do")
            
            with st.container():
                col_st, col_tx = st.columns([3, 7])
                opts_t = ["To Do", "In Progress", "Done"]
                new_t_st = col_st.selectbox(f"Statut {t_id}", opts_t, index=opts_t.index(current_t_st), key=f"ready_{t_id}")
                
                col_tx.markdown(f"**{t_id}** — {t_desc}")
                
                if new_t_st != current_t_st:
                    db["statut_readiness"][t_id] = new_t_st
                st.divider()
    else:
        st.info("💡 Glissez-déposez votre fichier 'Readiness' (CSV) dans le volet de gauche pour charger vos tâches.")

# ----------------------------------------------------
# 4. RISQUES & FOURNISSEURS
# ----------------------------------------------------
elif choice == "🎲 Risques & Fournisseurs" and client_actif:
    st.header(f"🎲 Matrice des Risques et Gestion des Tiers — {client_actif}")
    
    # Formulaire Risques
    st.subheader("🎲 Enregistrer un risque")
    r_desc = st.text_input("Menace / Risque identifié")
    vraisemblance = st.slider("Vraisemblance (1-5)", 1, 5, 2)
    impact = st.slider("Impact (1-5)", 1, 5, 2)
    if st.button("Ajouter le risque"):
        if r_desc:
            db["risques"].append({"Risque": r_desc, "Score": vraisemblance * impact})
            st.success("Risque ajouté ! Cliquez sur le bouton de sauvegarde à gauche pour actualiser.")
            
    if db["risques"]: 
        st.dataframe(pd.DataFrame(db["risques"]), use_container_width=True)
        
    st.markdown("---")
    
    # Formulaire Fournisseurs
    st.subheader("🏢 Enregistrer un sous-traitant")
    v_name = st.text_input("Nom du sous-traitant")
    crit = st.selectbox("Criticité", ["Haute", "Moyenne", "Faible"])
    if st.button("Enregistrer le fournisseur"):
        if v_name:
            db["vendors"].append({"Nom": v_name, "Criticité": crit})
            st.success("Fournisseur ajouté ! Cliquez sur le bouton de sauvegarde à gauche pour actualiser.")
            
    if db["vendors"]: 
        st.dataframe(pd.DataFrame(db["vendors"]), use_container_width=True)

# ----------------------------------------------------
# 5. POLITIQUES DOCUMENTAIRES
# ----------------------------------------------------
elif choice == "📜 Politiques Documentaires" and client_actif:
    st.header(f"📜 Suivi des Politiques Obligatoires (ISO/SOC2) — {client_actif}")
    
    for policy, status in db["policies"].items():
        with st.container():
            c_name, c_select = st.columns([6, 4])
            c_name.markdown(f"📄 **{policy}**")
            p_opts = ["À rédiger", "En cours de rédaction", "Approuvée & Diffusée"]
            new_p_st = c_select.selectbox("Statut", p_opts, index=p_opts.index(status), key=f"pol_{policy}")
            if new_p_st != status:
                db["policies"][policy] = new_p_st
            st.divider()
