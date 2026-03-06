import streamlit as st
from supabase import create_client

# Configuration WIKIDATA
st.set_page_config(page_title="WIKIDATA IT", page_icon="🌐", layout="centered")

# Design du Header
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>La base de connaissances hardware du Maroc</p>", unsafe_allow_html=True)
st.divider()

# Initialisation Supabase (Utilise ton Project ID de l'image d6a4e4)
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# Interface de recherche
query = st.text_input("", placeholder="Rechercher une référence (ex: C11CJ67408)...")

if query:
    query_clean = query.strip()
    with st.spinner(f'Recherche de {query_clean}...'):
        res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query_clean).execute()
    
    if res.data:
        prod = res.data[0]
        specs = prod['specs_json']
        
        # Message de succès avec le nom commercial
        st.success(f"**Modèle trouvé :** {prod['nom_produit']}")
        
        # --- NOUVEL AFFICHAGE ÉPURÉ (WIKIDATA STYLE) ---
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.subheader("📋 Fiche Technique Professionnelle")
        
        # On organise par catégories (Expanders)
        if "FeaturesGroups" in specs:
            for group in specs["FeaturesGroups"]:
                group_name = group.get("GroupName", "Information")
                
                # Création d'un volet déroulant par catégorie (ex: Impression, Scan, Connectivité)
                with st.expander(f"🔹 {group_name}", expanded=(group_name == "GeneralInfo")):
                    for feature in group.get("Features", []):
                        name = feature.get("Feature", {}).get("Name", {}).get("Value")
                        value = feature.get("PresentationValue")
                        if name and value:
                            # Affichage propre Nom : Valeur
                            st.write(f"**{name} :** {value}")
        else:
            st.info("Les détails techniques de ce produit sont simplifiés.")
            
    else:
        st.error("Cette référence n'est pas encore dans la base WIKIDATA.")
