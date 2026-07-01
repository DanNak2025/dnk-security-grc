import streamlit as st
import pandas as pd
import json
import os

# Configuration de la page avec un style épuré
st.set_page_config(page_title="ClearGRC Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- STYLE CSS POUR REPRODUIRE L'INTERFACE CLEARGRC ---
st.markdown("""
<style>
    /* Fond de page et polices */
    .reportview-container, .main { background-color: #fafbfc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    
    /* En-tête de l'application */
    .header-container { background-color: #ffffff; padding: 20px; border-bottom: 1px solid #e1e4e8; margin-bottom: 25px; }
    .header-title { font-size: 24px; font-weight: 600; color: #1e293b; }
    
    /* Cartes d'indicateurs (Metrics) */
    .metric-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .metric-label { font-size: 13px; font-weight: 500; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #0f172a; }
</style>
""", unsafe_with_stdio=True)

# --- HEADER CLEARGRC ---
st.markdown('<div class="header-container"><div class="header-title">🛡️ ClearGRC — Plateforme de Gouvernance & Conformité</div></div>', unsafe_with_stdio=True)

# --- INITIALISATION DE LA BASE DE DONNÉES EN MÉMOIRE ---
if "clients_db" not in st.session_state:
    st.session_state.clients_db = {}

# --- BARRE LATÉRALE (DISCRÈTE, UNIQUEMENT POUR CHOISIR LE CLIENT ET LES MATRICES) ---
with st.sidebar:
    st.header("⚙️ Paramètres Consultant")
    new_client = st.text_input("Créer un compte client :", placeholder="Nom de l'entreprise...")
    if st.button("➕ Initialiser", use_container_width=True):
        if new_client and new_client not in st.session_state.clients_db:
            st.session_state.clients_db[new_client] = {
                "statut_controles": {}, "statut_readiness": {}, "risques": [], "vendors": [],
                "policies": {
                    "Politique de Sécurité (PSSI)": "À rédiger",
                    "Contrôle d'Accès": "À rédiger",
                    "Gestion des Incidents": "À rédiger",
                    "Sécurité des Tiers": "À rédiger"
                }
            }
    
    liste_clients = list(st.session_state.clients_db.keys())
    client_actif = st.selectbox("🎯 Client en cours d'audit :", liste_clients if liste_clients else ["Exemple_Client"])
    
    # Si le client de démo est actif, on l'initialise en mémoire pour éviter les bugs
    if client_actif not in st.session_state.clients_db:
        st.session_state.clients_db[client_actif] = {"statut_controles": {}, "statut_readiness": {}, "risques": [], "vendors": [], "policies": {}}
    
    db = st.session_state.clients_db[client_actif]
    
    st.markdown("---")
    st.markdown("**📁 Chargement des Matrices Excel (CSV)**")
    uploaded_controls = st.file_uploader("Contrôles SOC2 / ISO", type=["csv"])
    uploaded_readiness = st.file_uploader("Plan de route Readiness", type=["csv"])

# Lecture des fichiers
def read_csv(file):
    if file is not None:
        try: return pd.read_csv(file, sep=None, engine='python')
        except Exception: return None
    return None

df_controls = read_csv(uploaded_controls)
df_readiness = read_csv(uploaded_readiness)

# --- NAVIGATION SUPÉRIEURE PAR ONGLETS (STYLE DU SITE CLEARGRC) ---
tab_dash, tab_risk, tab_vendor, tab_policies, tab_certs = st.tabs([
    "📊 Dashboard", 
    "🎲 Risk Assessment", 
    "🏢 Vendor Assessment", 
    "📜 Policies", 
    "📜 Certifications (ISO27001/SOC2)"
])

# ----------------------------------------------------
# ONGLET 1 : DASHBOARD
# ----------------------------------------------------
with tab_dash:
    st.subheader(f"Vue d'ensemble de la posture — {client_actif}")
    
    # Calculs rapides pour les métriques
    total_ctrls = len(df_controls) if df_controls is not None else 54
    ready_count = sum(1 for v in db["statut_controles"].values() if v in ["Ready for Audit", "Approved"])
    score_compliance = int((ready_count / total_ctrls) * 100) if total_ctrls > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Conformité Globale</div><div class="metric-value">{score_compliance}%</div></div>', unsafe_with_stdio=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Risques Critiques</div><div class="metric-value">{len(db["risques"])}</div></div>', unsafe_with_stdio=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Tiers Évalués</div><div class="metric-value">{len(db["vendors"])}</div></div>', unsafe_with_stdio=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Politiques Validées</div><div class="metric-value">{sum(1 for v in db["policies"].values() if v == "Approuvée")}/{len(db["policies"])}</div></div>', unsafe_with_stdio=True)

    st.markdown("### 📈 Jalons de Remédiation")
    if df_readiness is not None:
        st.dataframe(df_readiness, use_container_width=True)
    else:
        st.info("ℹ️ Chargez votre fichier 'Readiness.csv' dans le menu de gauche pour afficher les jalons techniques ici.")

# ----------------------------------------------------
# ONGLET 2 : RISK ASSESSMENT
# ----------------------------------------------------
with tab_risk:
    st.subheader("🎲 Matrice d'Analyse des Risques")
    
    with st.form("risk_premium_form", clear_on_submit=True):
        col_r1, col_r2, col_r3 = st.columns([6, 3, 3])
        r_title = col_r1.text_input("Identification de la menace / vulnérabilité")
        vrais = col_r2.selectbox("Vraisemblance", [1, 2, 3, 4, 5])
        imp = col_r3.selectbox("Impact", [1, 2, 3, 4, 5])
        if st.form_submit_button("⚡ Ajouter au registre des risques"):
            if r_title:
                db["risques"].append({"Risque / Scénario": r_title, "Criticité": vrais * imp, "Statut": "À traiter"})
                st.rerun()

    if db["risques"]:
        st.dataframe(pd.DataFrame(db["risques"]), use_container_width=True)
    else:
        st.caption("Aucun risque enregistré pour le moment.")

# ----------------------------------------------------
# ONGLET 3 : VENDOR ASSESSMENT
# ----------------------------------------------------
with tab_vendor:
    st.subheader("🏢 Évaluation de la chaîne de sous-traitance (Third-Party Risk)")
    
    with st.form("vendor_premium_form", clear_on_submit=True):
        v_name = st.text_input("Nom du fournisseur tiers (ex: AWS, Google Cloud, Salesforce...)")
        v_crit = st.selectbox("Niveau de criticité pour l'entreprise", ["Critique", "Élevé", "Moyen", "Faible"])
        if st.form_submit_button("➕ Ajouter le fournisseur"):
            if v_name:
                db["vendors"].append({"Sous-traitant": v_name, "Criticité": v_crit, "Rapport SOC2/ISO": "En attente"})
                st.rerun()

    if db["vendors"]:
        st.dataframe(pd.DataFrame(db["vendors"]), use_container_width=True)

# ----------------------------------------------------
# ONGLET 4 : POLICIES
# ----------------------------------------------------
with tab_policies:
    st.subheader("📜 Documentation de Gouvernance & Politiques")
    
    for p, status in list(db["policies"].items()):
        c_p1, c_p2 = st.columns([7, 3])
        c_p1.markdown(f"📄 **{p}**")
        opts_p = ["À rédiger", "En cours de revue", "Approuvée"]
        new_status = c_select = c_p2.selectbox("Statut du document", opts_p, index=opts_p.index(status) if status in opts_p else 0, key=f"p_{p}")
        if new_status != status:
            db["policies"][p] = new_status
        st.divider()

# ----------------------------------------------------
# ONGLET 5 : CERTIFICATIONS (ISO27001/SOC2)
# ----------------------------------------------------
with tab_certs:
    st.subheader("📜 Suivi d'Audit Réglementaire")
    
    if df_controls is not None:
        search = st.text_input("🔍 Filtrer la liste des contrôles d'audit...")
        df_f = df_controls.copy()
        if search:
            df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
        for idx, row in df_f.iterrows():
            c_id = str(row.iloc[0])
            c_desc = str(row.iloc[1])
            
            current_st = db["statut_controles"].get(c_id, "Gap")
            
            with st.container():
                col_c1, col_c2 = st.columns([8, 2])
                col_c1.markdown(f"**{c_id}** — {c_desc}")
                
                opts_c = ["Gap", "Ready for Audit", "Approved"]
                new_c_st = col_c2.selectbox("Maturité", opts_c, index=opts_c.index(current_st), key=f"c_{c_id}")
                if new_c_st != current_st:
                    db["statut_controles"][c_id] = new_c_st
                st.divider()
    else:
        st.info("ℹ️ Pour charger vos 54 contrôles d'audit d'évaluation, déposez votre fichier 'Control List.csv' dans le menu latéral gauche.")
