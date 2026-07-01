import streamlit as st
import pandas as pd
import os
import json

# Configuration de la plateforme de consulting
st.set_page_config(page_title="Cabinet GRC - Console Consultant", layout="wide")
st.title("💼 Console Consultant — Plateforme GRC Multi-Clients")

# --- MULTI-TENANCY : PERSISTANCE PAR CLIENT ---
DATA_DIR = "clients_grc_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_default_blank_state(client_name):
    return {
        "client_name": client_name,
        "statut_controles": {},  # ID: Statut
        "statut_readiness": {},  # ID: Statut
        "risques": [],
        "vendors": [],
        "policies": {
            "Politique de Sécurité de l'Information (PSSI)": "À rédiger",
            "Politique de Contrôle d'Accès": "À rédiger",
            "Politique de Gestion des Incidents": "À rédiger",
            "Politique de Sécurité des Ressources Humaines": "À rédiger",
            "Politique de Gestion des Fournisseurs": "À rédiger"
        }
    }

def load_client_file(client_name):
    path = os.path.join(DATA_DIR, f"{client_name}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return get_default_blank_state(client_name)

def save_client_file(client_name, data):
    path = os.path.join(DATA_DIR, f"{client_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- CHARGEMENT DES RÉFÉRENTIELS (VOS MATRICES EXCEL) ---
@st.cache_data
def load_csv_template(filename):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return None

df_controls_base = load_csv_template("1 - SOC2_ControlList - DNK Security.xlsx - Control List.csv")
df_readiness_base = load_csv_template("1 - SOC2_ControlList - DNK Security.xlsx - Readiness.csv")

# --- SIDEBAR : ESPACE CONSULTANT ---
st.sidebar.subheader("🏢 Espace Consultant")
existing_clients = [f.replace(".json", "") for f in os.listdir(DATA_DIR) if f.endswith(".json")]

# Formulaire d'ajout de client
with st.sidebar.expander("➕ Ajouter un nouveau client"):
    new_client_name = st.text_input("Nom de l'entreprise :", key="new_client_input")
    if st.button("Créer l'espace client"):
        if new_client_name and new_client_name not in existing_clients:
            blank_state = get_default_blank_state(new_client_name)
            save_client_file(new_client_name, blank_state)
            st.success(f"Espace {new_client_name} créé !")
            st.rerun()

# Sélection du client sur lequel vous travaillez
if existing_clients:
    client_actif = st.sidebar.selectbox("🎯 Client en cours d'accompagnement :", existing_clients)
    db = load_client_file(client_actif)
else:
    client_actif = None
    st.sidebar.warning("Veuillez créer un premier client pour commencer.")

# Menu des modules de la mission
st.sidebar.markdown("---")
st.sidebar.subheader("📋 Modules de la Mission")
menu = [
    "📊 Tableau de Bord Client",
    "📋 Contrôles SOC2 (Audit)",
    "🎯 Préparation (Readiness)",
    "🎲 Gestion des Risques & Tiers",
    "📜 Politiques & ISO27001"
]
choice = st.sidebar.radio("Naviguer vers :", menu, disabled=(client_actif is None))

# ----------------------------------------------------
# 1. TABLEAU DE BORD CLIENT
# ----------------------------------------------------
if choice == "📊 Tableau de Bord Client" and client_actif:
    st.header(f"📊 Tableau de Bord Diagnostic — {client_actif}")
    st.write("Vue synthétique de l'état de conformité de votre client face aux exigences d'audit.")
    
    if df_controls_base is not None:
        total_ctrls = len(df_controls_base.dropna(subset=[df_controls_base.columns[1]]))
        saved_ctrls = db.get("statut_controles", {})
        ready_audit = sum(1 for v in saved_ctrls.values() if v == "Ready for Audit")
        approved = sum(1 for v in saved_ctrls.values() if v == "Approved by Auditor")
        pct_soc2 = int(((ready_audit + approved) / total_ctrls) * 100) if total_ctrls > 0 else 0
    else:
        total_ctrls, pct_soc2 = 0, 0

    if df_readiness_base is not None:
        total_tasks = len(df_readiness_base.dropna(subset=[df_readiness_base.columns[3]]))
        saved_tasks = db.get("statut_readiness", {})
        done_tasks = sum(1 for v in saved_tasks.values() if v == "Done")
        pct_readiness = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    else:
        total_tasks, pct_readiness = 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric(label="Avancement SOC2", value=f"{pct_soc2}%", delta=f"{total_ctrls} contrôles")
    col2.metric(label="Chantiers Techniques (Readiness)", value=f"{pct_readiness}%", delta=f"{total_tasks} jalons")
    col3.metric(label="Risques & Tiers Enregistrés", value=len(db["risques"]), delta=f"{len(db['vendors'])} fournisseurs")
    
    st.markdown("---")
    st.subheader("Feuille de route de la certification")
    st.write("**Statut de la préparation technique (Readiness)**")
    st.progress(pct_readiness / 100)
    st.write("**Niveau de maturité d'audit (SOC2 Control List)**")
    st.progress(pct_soc2 / 100)

# ----------------------------------------------------
# 2. CONTRÔLES SOC2
# ----------------------------------------------------
elif choice == "📋 Contrôles SOC2 (Audit)" and client_actif:
    st.header(f"📋 Évaluation des 54 Contrôles SOC2 — {client_actif}")
    st.caption("Qualifiez chaque point de contrôle et identifiez les 'Gaps' restants à corriger avant le passage de l'auditeur externe.")
    
    if df_controls_base is not None:
        df = df_controls_base.dropna(subset=[df_controls_base.columns[1]]).copy()
        
        search = st.text_input("🔍 Filtrer les critères / preuves (ex: chiffrement, logs...)")
        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        for _, row in df.iterrows():
            ctrl_id = str(row.iloc[0])
            ctrl_desc = str(row.iloc[1])
            evidence = str(row.iloc[2]) if pd.notna(row.iloc[2]) else "Aucune preuve spécifiée"
            
            current_status = db["statut_controles"].get(ctrl_id, str(row.iloc[4]) if pd.notna(row.iloc[4]) else "Gap")
            
            with st.expander(f"🔹 {ctrl_id} — {ctrl_desc[:100]}..."):
                st.markdown(f"**Description du contrôle :** {ctrl_desc}")
                st.markdown(f"**Éléments de preuve requis :** `{evidence}`")
                
                options_status = ["Gap", "Ready for Audit", "Approved by Auditor"]
                idx_default = options_status.index(current_status) if current_status in options_status else 0
                
                new_status = st.selectbox(f"Statut du contrôle {ctrl_id}", options_status, index=idx_default, key=f"ctrl_{client_actif}_{ctrl_id}")
                
                if new_status != current_status:
                    db["statut_controles"][ctrl_id] = new_status
                    save_client_file(client_actif, db)
                    st.toast(f"Sauvegardé pour {client_actif}", icon="💾")
    else:
        st.error("Fichier modèle 'Control List.csv' introuvable.")

# ----------------------------------------------------
# 3. SUIVI DE PRÉPARATION (READINESS)
# ----------------------------------------------------
elif choice == "🎯 Préparation (Readiness)" and client_actif:
    st.header(f"🎯 Plan d'action opérationnel (30 Tâches) — {client_actif}")
    
    if df_readiness_base is not None:
        df_tasks = df_readiness_base.dropna(subset=[df_readiness_base.columns[3]]).copy()
        
        for _, row in df_tasks.iterrows():
            t_id = str(row['Task #'])
            t_desc = str(row['Task Description'])
            section = str(row['Section'])
            priority = str(row['Priority'])
            
            current_task_status = db["statut_readiness"].get(t_id, str(row['Status']) if pd.notna(row['Status']) else "To Do")
            
            with st.container():
                col_status, col_desc = st.columns([2, 8])
                task_opts = ["To Do", "In Progress", "Done"]
                t_idx = task_opts.index(current_task_status) if current_task_status in task_opts else 0
                
                new_t_status = col_status.selectbox(f"Tâche {t_id}", task_opts, index=t_idx, key=f"tsk_{client_actif}_{t_id}")
                
                prio_indicator = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
                col_desc.markdown(f"**[{section}]** {t_desc} | Priorité : {prio_indicator} {priority}")
                
                if new_t_status != current_task_status:
                    db["statut_readiness"][t_id] = new_t_status
                    save_client_file(client_actif, db)
                    st.toast("Tâche mise à jour", icon="✅")
                st.divider()

# ----------------------------------------------------
# 4. RISQUES & FOURNISSEURS
# ----------------------------------------------------
elif choice == "🎲 Gestion des Risques & Tiers" and client_actif:
    st.header(f"🎲 Analyse de Risques & Cartographie des Tiers — {client_actif}")
    
    tab1, tab2 = st.tabs(["🎲 Analyse des Risques", "🏢 Évaluation Fournisseurs"])
    
    with tab1:
        st.subheader("Analyse des Menaces pour ce client")
        with st.form("risk_consultant_form"):
            desc = st.text_input("Risque identifié")
            vraisemblance = st.slider("Vraisemblance (1-5)", 1, 5, 2)
            impact = st.slider("Impact (1-5)", 1, 5, 2)
            if st.form_submit_button("Ajouter le risque"):
                if desc:
                    db["risques"].append({
                        "Description": desc, "Vraisemblance": vraisemblance, 
                        "Impact": impact, "Score": vraisemblance * impact
                    })
                    save_client_file(client_actif, db)
                    st.rerun()
        if db["risques"]:
            st.dataframe(pd.DataFrame(db["risques"]), use_container_width=True)

    with tab2:
        st.subheader("Cartographie et criticité des sous-traitants")
        with st.form("vendor_consultant_form"):
            v_name = st.text_input("Nom du tiers")
            crit = st.selectbox("Criticité", ["Haute", "Moyenne", "Faible"])
            if st.form_submit_button("Ajouter le sous-traitant"):
                if v_name:
                    db["vendors"].append({"Nom": v_name, "Criticité": crit})
                    save_client_file(client_actif, db)
                    st.rerun()
        if db["vendors"]:
            st.dataframe(pd.DataFrame(db["vendors"]), use_container_width=True)

# ----------------------------------------------------
# 5. POLITIQUES DOCUMENTAIRES
# ----------------------------------------------------
elif choice == "📜 Politiques & ISO27001" and client_actif:
    st.header(f"📜 Chantier Documentaire — {client_actif}")
    st.write("Suivez l'état d'avancement de la rédaction des politiques de sécurité obligatoires.")
    
    for policy, status in db["policies"].items():
        with st.container():
            col_p_name, col_p_stat = st.columns([6, 3])
            col_p_name.markdown(f"📄 **{policy}**")
            
            opts_p = ["À rédiger", "En cours de revue", "Approuvée & Publiée"]
            idx_p = opts_p.index(status) if status in opts_p else 0
            
            new_p_status = col_p_stat.selectbox("Statut du document", opts_p, index=idx_p, key=f"pol_{client_actif}_{policy}")
            
            if new_p_status != status:
                db["policies"][policy] = new_p_status
                save_client_file(client_actif, db)
                st.toast("Document mis à jour", icon="📝")
            st.divider()
