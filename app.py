import streamlit as st
from supabase import create_client

# 1. Connexion (On utilise tes clés Supabase)
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"] # On utilise les secrets pour la sécurité
supabase = create_client(URL, KEY)

# 2. Interface
st.set_page_config(page_title="Specs IT Maroc", page_icon="🇲🇦")
st.title("🔍 Moteur de recherche IT")

query = st.text_input("Saisissez une référence (ex: C11CJ67408)")

if query:
    # Recherche exacte dans ta table
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    
    if res.data:
        prod = res.data[0]
        st.header(f"{prod['marque']} - {prod['nom_produit']}")
        
        # Affichage propre des données JSON
        with st.expander("Voir les caractéristiques complètes"):
            st.write(prod['specs_json'])
    else:
        st.error("Référence inconnue. Essayez une autre référence de votre catalogue.")
