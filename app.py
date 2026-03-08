import streamlit as st
from supabase import create_client
from fpdf import FPDF
import re

# --- CONNEXION SUPABASE ---
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def clean_text(text):
    """Nettoie les caractères spéciaux pour éviter le crash FPDF"""
    if not text: return ""
    replacements = {
        '°': ' deg', '²': '2', '³': '3', '×': 'x', 
        '™': '', '®': '', '©': '', '…': '...'
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    all_txt = str(specs).lower()
    
    # --- DÉTECTION DE CATÉGORIE ---
    if any(k in all_txt for k in ["processor", "ram", "ssd", "laptop"]):
        cat, color = "INFORMATIQUE", (44, 62, 80) # Bleu Nuit
        labels = ["PROCESSEUR", "RAM", "STOCKAGE", "ECRAN"]
    elif any(k in all_txt for k in ["hz", "pouces", "display", "monitor", "téléviseur"]):
        cat, color = "AFFICHAGE", (20, 90, 50) # Vert Sombre
        labels = ["DIAGONALE", "RESOLUTION", "FREQUENCE", "DALLE"]
    elif any(k in all_txt for k in ["ppm", "impression", "ink"]):
        cat, color = "IMPRESSION", (0, 51, 153) # Bleu Royal
        labels = ["VITESSE NOIR", "VITESSE COULEUR", "RECTO-VERSO", "ENCRE"]
    elif any(k in all_txt for k in ["lumens", "projection"]):
        cat, color = "PROJECTION", (150, 0, 0) # Rouge Brique
        labels = ["LUMINOSITE", "RESOLUTION", "IMAGE", "LAMPE"]
    else:
        cat, color = "ACCESSOIRE", (100, 100, 100) # Gris
        labels = ["MARQUE", "PN", "TYPE", "USAGE"]

    # --- DESIGN ---
    # Logo Officiel via Clearbit
    try:
        brand_clean = brand.lower().strip().replace(' ', '')
        pdf.image(f"https://logo.clearbit.com/{brand_clean}.com", x=10, y=10, w=22)
    except:
        pdf.set_font("Helvetica", "B", 14); pdf.text(10, 18, brand.upper())

    # Titre Droite
    pdf.set_xy(40, 10)
    pdf.set_font("Helvetica", "B", 18); pdf.set_text_color(*color)
    pdf.cell(0, 10, clean_text(prod_name.upper()), ln=True, align='R')
    pdf.set_font("Helvetica", "", 9); pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, f"PN: {ref} | {cat}", ln=True, align='R')

    # Bandeau Performance
    pdf.ln(8)
    pdf.set_fill_color(*color)
    pdf.rect(10, pdf.get_y(), 190, 15, 'F')
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(255, 255, 255)
    for l in labels: pdf.cell(47.5, 5, l, align='C')
    
    pdf.ln(12)
    y_start = pdf.get_y()

    # Image Produit
    try:
        img = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img: pdf.image(img, x=10, y=y_start, w=55)
    except: pass

    # Détails Techniques (2 colonnes simulées)
    pdf.set_xy(70, y_start)
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            if g_name in ["GENERAL", "INFO", "SPECS", "GENERALE"]: continue
            
            pdf.set_x(70)
            pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(248, 248, 248)
            pdf.set_text_color(*color)
            pdf.cell(130, 6, f"  {clean_text(g_name)}", ln=True, fill=True)
            
            pdf.set_font("Helvetica", "", 7.5); pdf.set_text_color(60, 60, 60)
            for feat in group.get("Features", []):
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v:
                    line = clean_text(f"> {n}: {v}")
                    pdf.set_x(72); pdf.multi_cell(125, 3.5, line)
            pdf.ln(2)
            if pdf.get_y() > 275: break

    return bytes(pdf.output())

# --- INTERFACE STREAMLIT ---
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)
query = st.text_input("", placeholder="Entrez une référence (PN)...")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    if res.data:
        prod = res.data[0]
        st.info(f"Produit détecté : {prod['nom_produit']}")
        try:
            pdf_bytes = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], prod['specs_json'])
            st.download_button(label="📥 Télécharger la Brochure Officielle", data=pdf_bytes, file_name=f"WIKIDATA_{query}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Erreur technique : {e}")
    else:
        st.warning("Référence non trouvée.")
