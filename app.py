import streamlit as st
from supabase import create_client
from fpdf import FPDF

# Configuration WIKIDATA IT
st.set_page_config(page_title="WIKIDATA IT", page_icon="🌐")

# Initialisation Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- FONCTION GÉNÉRATION PDF ---
def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, f"FICHE TECHNIQUE : {prod_name}", ln=True, align='C')
    pdf.set_font("Arial", "I", 12)
    pdf.cell(200, 10, f"Propulsé par WIKIDATA IT - Maroc", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Marque : {brand}", ln=True)
    pdf.cell(0, 10, f"Référence : {ref}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 10)
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"][:5]: # On limite aux 5 premiers groupes pour le PDF
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 10, f"--- {group.get('GroupName', 'Info')} ---", ln=True)
            pdf.set_font("Arial", "", 10)
            for feat in group.get("Features", [])[:10]:
                name = feat.get("Feature", {}).get("Name", {}).get("Value")
                val = feat.get("PresentationValue")
                if name and val:
                    pdf.multi_cell(0, 7, f"{name}: {val}")
    return pdf.output(dest='S')

# --- INTERFACE ---
st.markdown("<h1 style='text-align: center;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)
query = st.text_input("", placeholder="Rechercher une référence (ex: C11CJ67408)...")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    
    if res.data:
        prod = res.data[0]
        specs = prod['specs_json']
        
        st.success(f"**Modèle :** {prod['nom_produit']}")
        
        # Bouton PDF
        pdf_data = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], specs)
        st.download_button(
            label="📥 Télécharger la Fiche PDF",
            data=pdf_data,
            file_name=f"WIKIDATA_{prod['ref_constructeur']}.pdf",
            mime="application/pdf"
        )

        # Affichage catégories (Expanders)
        if "FeaturesGroups" in specs:
            for group in specs["FeaturesGroups"]:
                with st.expander(f"🔹 {group.get('GroupName', 'Détails')}"):
                    for feature in group.get("Features", []):
                        n = feature.get("Feature", {}).get("Name", {}).get("Value")
                        v = feature.get("PresentationValue")
                        if n and v: st.write(f"**{n} :** {v}")
    else:
        st.error("Référence non trouvée.")
