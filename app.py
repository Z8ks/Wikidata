import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Configuration de la page WIKIDATA IT
st.set_page_config(page_title="WIKIDATA IT", page_icon="🌐", layout="centered")

# 2. Connexion à ta base de données Supabase
# Assure-toi que SUPABASE_KEY est configurée dans les "Secrets" de Streamlit
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 3. Fonction de génération du PDF (Version Pro avec Logo)
def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    
    # Marges de sécurité
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    w_utile = pdf.w - 2 * pdf.l_margin
    
    # --- LOGO STYLISÉ WIKIDATA ---
    pdf.set_fill_color(30, 136, 229) # Bleu Royal
    pdf.rect(0, 0, 210, 35, 'F') # Bandeau de tête
    
    pdf.set_xy(15, 12)
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(255, 255, 255) # Blanc
    pdf.cell(0, 10, "WIKIDATA IT", ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "LA BASE DE CONNAISSANCES HARDWARE DU MAROC", ln=True)
    pdf.ln(15) # Espace après le bandeau
    
    # --- INFOS PRODUIT ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(w_utile, 10, f"FICHE TECHNIQUE : {prod_name}")
    
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(w_utile, 8, f"MARQUE : {brand} | PN : {ref}", ln=True)
    pdf.ln(5)
    
    # --- CARACTÉRISTIQUES (Filtrage des données Icecat) ---
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"][:10]:
            g_name = group.get('GroupName', 'Info').encode('latin-1', 'replace').decode('latin-1')
            
            # Titre de catégorie
            pdf.set_font("Arial", "B", 11)
            pdf.set_fill_color(230, 240, 255)
            pdf.set_text_color(30, 136, 229)
            pdf.cell(w_utile, 8, f" {g_name.upper()} ", ln=True, fill=True)
            
            # Liste des caractéristiques
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(0, 0, 0)
            for feat in group.get("Features", []):
                name = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                val = feat.get("PresentationValue", "")
                
                if name and val:
                    # On nettoie le texte pour éviter les erreurs de caractères spéciaux
                    txt = f"{name}: {val}".encode('latin-1', 'replace').decode('latin-1')
                    # multi_cell gère les retours à la ligne automatiques
                    pdf.multi_cell(w_utile, 6, txt, border='B') 
            pdf.ln(4)
            
    # Pied de page
    pdf.set_y(-20)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Document généré par WIKIDATA IT - wikidata-it.streamlit.app", align='C')
            
    return pdf.output(dest='S')

# 4. Interface Utilisateur Streamlit
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Consultation technique hardware pour les professionnels</p>", unsafe_allow_html=True)

query = st.text_input("", placeholder="Rechercher une référence constructeur (ex: C11CJ67408)...")

if query:
    query_clean = query.strip()
    with st.spinner('Recherche dans la base...'):
        # On interroge Supabase
        res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query_clean).execute()
    
    if res.data:
        prod = res.data[0]
        specs = prod['specs_json']
        
        st.success(f"**{prod['nom_produit']}**")
        
        # Bouton de téléchargement PDF
        try:
            pdf_bytes = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], specs)
            st.download_button(
                label="📥 Télécharger la Fiche PDF WIKIDATA",
                data=pdf_bytes,
                file_name=f"WIKIDATA_{prod['ref_constructeur']}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Note : Le PDF n'a pas pu être généré pour cette fiche : {e}")
        
        st.divider()
        
        # Affichage des catégories techniques sur le site
        if "FeaturesGroups" in specs:
            for group in specs["FeaturesGroups"]:
                with st.expander(f"🔹 {group.get('GroupName', 'Détails')}"):
                    for feature in group.get("Features", []):
                        n = feature.get("Feature", {}).get("Name", {}).get("Value")
                        v = feature.get("PresentationValue")
                        if n and v: 
                            st.write(f"**{n} :** {v}")
    else:
        st.error("Cette référence n'est pas encore répertoriée. WIKIDATA s'enrichit chaque jour !")
