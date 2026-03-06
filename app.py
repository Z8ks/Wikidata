import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Configuration de la page
st.set_page_config(page_title="WIKIDATA IT", page_icon="🌐", layout="centered")

# 2. Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 3. Fonction de génération PDF "Ultra-Condensée"
def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    # Marges optimales
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    w_utile = pdf.w - 20

    # --- ENTÊTE : LOGO & TITRE ---
    try:
        # Logo de la marque via Clearbit
        brand_domain = f"{brand.lower().replace(' ', '')}.com"
        logo_url = f"https://logo.clearbit.com/{brand_domain}"
        pdf.image(logo_url, x=10, y=10, w=20)
    except:
        pdf.set_font("Arial", "B", 12)
        pdf.set_xy(10, 10)
        pdf.cell(40, 10, brand.upper())

    pdf.set_xy(10, 10)
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(30, 136, 229)
    pdf.cell(0, 10, "WIKIDATA IT", ln=True, align='R') [cite: 34]
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "LA BASE DE CONNAISSANCES HARDWARE DU MAROC", ln=True, align='R') [cite: 35]
    
    pdf.ln(10)

    # --- BLOC PRODUIT AVEC PHOTO ---
    y_start = pdf.get_y()
    
    # Texte du produit (60% de la largeur)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(w_utile * 0.6, 8, f"{prod_name}") [cite: 36]
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(w_utile * 0.6, 6, f"PN : {ref}", ln=True) [cite: 61]
    pdf.cell(w_utile * 0.6, 6, f"MARQUE : {brand.upper()}", ln=True) [cite: 37]

    # Image produit à droite (40% de la largeur)
    try:
        img_url = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img_url:
            pdf.image(img_url, x=140, y=y_start, w=45)
    except:
        pass

    pdf.set_y(y_start + 30)
    pdf.set_draw_color(30, 136, 229)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # --- SPÉCIFICATIONS TECHNIQUES (Format Compact) ---
    if "FeaturesGroups" in specs:
        # On ne garde que les groupes qui ne s'appellent pas "Général" pour éviter les doublons
        groups = [g for g in specs["FeaturesGroups"] if g.get('GroupName', '').upper() != "GÉNÉRAL"] [cite: 38, 49, 56, 58]
        
        for group in groups:
            g_name = group.get('GroupName', 'Specs')
            
            # Titre de section compact
            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(240, 245, 255)
            pdf.set_text_color(30, 136, 229)
            pdf.cell(w_utile, 6, f" {g_name.upper()}", ln=True, fill=True)
            
            pdf.set_font("Arial", "", 8)
            pdf.set_text_color(0, 0, 0)
            
            # Affichage des caractéristiques
            for feat in group.get("Features", []):
                name = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                val = feat.get("PresentationValue", "")
                
                if name and val:
                    # Nettoyage texte pour éviter les erreurs d'encodage
                    txt = f"{name}: {val}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(w_utile, 4, f" > {txt}") [cite: 39-48, 50-55, 60, 62-79]
            pdf.ln(2)

    # Pied de page
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 7)
    pdf.set_text_color(170, 170, 170)
    pdf.cell(0, 10, "Document généré par WIKIDATA IT - wikidata-it.streamlit.app", align='C') [cite: 113]

    return bytes(pdf.output())

# 4. Interface Streamlit
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)

query = st.text_input("", placeholder="Entrez une référence (PN)...")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    
    if res.data:
        prod = res.data[0]
        specs = prod['specs_json']
        
        st.success(f"**Modèle :** {prod['nom_produit']}")
        
        try:
            pdf_data = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], specs)
            st.download_button(
                label="📥 Télécharger la Fiche Technique",
                data=pdf_data,
                file_name=f"Fiche_{prod['ref_constructeur']}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erreur PDF : {e}")

        st.divider()
        
        # Affichage Web (Accordéons)
        if "FeaturesGroups" in specs:
            for group in specs["FeaturesGroups"]:
                with st.expander(f"🔹 {group.get('GroupName', 'Détails')}"):
                    for feat in group.get("Features", []):
                        n = feat.get("Feature", {}).get("Name", {}).get("Value")
                        v = feat.get("PresentationValue")
                        if n and v: st.write(f"**{n} :** {v}")
    else:
        st.error("Référence inconnue.")
