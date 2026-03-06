import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Configuration WIKIDATA IT
st.set_page_config(page_title="WIKIDATA IT", page_icon="🌐", layout="centered")

# 2. Connexion Supabase
# Assure-toi que SUPABASE_KEY est bien dans tes Secrets Streamlit
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 3. Fonction de génération du PDF
def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    
    # En-tête du document
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(30, 136, 229) 
    pdf.cell(0, 10, "WIKIDATA IT - FICHE TECHNIQUE", ln=True, align='C')
    
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "La base de connaissances hardware du Maroc", ln=True, align='C')
    pdf.ln(10)
    
    # Infos de base
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Produit : {prod_name}", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Marque : {brand}", ln=True)
    pdf.cell(0, 8, f"Reference PN : {ref}", ln=True)
    pdf.ln(5)
    
    # Détails techniques
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"][:8]:
            pdf.set_font("Arial", "B", 11)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 8, f" {group.get('GroupName', 'Info')} ", ln=True, fill=True)
            
            pdf.set_font("Arial", "", 9)
            for feat in group.get("Features", [])[:12]:
                name = feat.get("Feature", {}).get("Name", {}).get("Value")
                val = feat.get("PresentationValue")
                if name and val:
                    pdf.multi_cell(0, 6, f"{name}: {val}")
            pdf.ln(2)
            
    return pdf.output(dest='S')

# 4. Interface Utilisateur
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Recherche technique instantanée</p>", unsafe_allow_html=True)

query = st.text_input("", placeholder="Saisissez une référence constructeur...")

if query:
    query_clean = query.strip()
    with st.spinner('Extraction depuis WIKIDATA...'):
        res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query_clean).execute()
    
    if res.data:
        prod = res.data[0]
        specs = prod['specs_json']
        
        st.success(f"**{prod['nom_produit']}**")
        
        # Génération et bouton PDF
        try:
            pdf_bytes = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], specs)
            st.download_button(
                label="📥 Télécharger la Fiche PDF Officielle",
                data=pdf_bytes,
                file_name=f"WIKIDATA_{prod['ref_constructeur']}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erreur lors de la création du PDF : {e}")
        
        st.divider()
        
        # Affichage des catégories techniques
        if "FeaturesGroups" in specs:
            for group in specs["FeaturesGroups"]:
                with st.expander(f"🔹 {group.get('GroupName', 'Détails')}"):
                    for feature in group.get("Features", []):
                        n = feature.get("Feature", {}).get("Name", {}).get("Value")
                        v = feature.get("PresentationValue")
                        if n and v: 
                            st.write(f"**{n} :** {v}")
    else:
        st.error("Cette référence n'est pas encore répertoriée dans la base.")
