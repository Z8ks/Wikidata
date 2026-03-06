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
        st.balloons()
        
        st.success(f"**Produit trouvé :** {prod['nom_produit']}")
        
        col1, col2 = st.columns(2)
        col1.metric("Marque", prod['marque'])
        col2.metric("Référence PN", prod['ref_constructeur'])
        
        with st.expander("📄 Voir la fiche technique complète", expanded=True):
            st.json(prod['specs_json'])
    else:
        st.error("Cette référence n'est pas encore répertoriée. WIKIDATA s'enrichit chaque jour !")
        # ... (gardez le début du code identique)

if res.data:
    prod = res.data[0]
    specs = prod['specs_json'] # On récupère le dictionnaire complet

    st.success(f"**Produit trouvé :** {prod['nom_produit']}")
    
    # Création d'onglets pour une navigation fluide
    tab1, tab2 = st.tabs(["📋 Fiche Résumée", "💻 Données Brutes"])

    with tab1:
        # Extraction intelligente des caractéristiques principales
        # Note : Les clés dépendent de la structure d'Icecat
        info = specs.get("GeneralInfo", {})
        
        st.subheader("Caractéristiques Principales")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write(f"**Modèle :** {info.get('ProductName', 'N/A')}")
            st.write(f"**Marque :** {prod['marque']}")
        
        with col_b:
            st.write(f"**Référence :** {prod['ref_constructeur']}")
            st.write(f"**Catégorie :** {info.get('Category', {}).get('Name', {}).get('Value', 'Hardware')}")

        # Affichage des spécifications sous forme de tableau
        if "FeaturesGroups" in specs:
            st.subheader("Détails Techniques")
            for group in specs["FeaturesGroups"]:
                with st.expander(group.get("GroupName", "Spécifications")):
                    for feature in group.get("Features", []):
                        name = feature.get("Feature", {}).get("Name", {}).get("Value")
                        value = feature.get("PresentationValue")
                        st.write(f"**{name} :** {value}")

    with tab2:
        st.json(specs)
