import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Configuration de la page
st.set_page_config(page_title="WIKIDATA IT", page_icon="🌐", layout="centered")

# 2. Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 3. Fonction de génération PDF corrigée (Design Pro & Texte fluide)
def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)
    
    # Marges étroites pour gagner de la place
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    w_utile = pdf.w - 20

    # --- ENTÊTE : LOGO MARQUE & TITRE ---
    # On récupère le logo via Clearbit (ex: epson.com)
    brand_domain = f"{brand.lower().replace(' ', '')}.com"
    logo_url = f"https://logo.clearbit.com/{brand_domain}"
    
    try:
        pdf.image(logo_url, x=10, y=10, w=25)
    except:
        pdf.set_font("Arial", "B", 12)
        pdf.text(10, 15, brand.upper())

    pdf.set_xy(40, 10)
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(30, 136, 229)
    pdf.cell(0, 10, "WIKIDATA IT - FICHE PRODUIT", ln=True, align='R')
    pdf.ln(10)

    # --- BLOC PRODUIT AVEC PHOTO ---
    y_start = pdf.get_y()
    
    # Colonne Gauche : Texte
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(w_utile * 0.65, 8, f"{prod_name}") # [cite: 36]
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(w_utile * 0.65, 6, f"RÉFÉRENCE CONSTRUCTEUR (PN) : {ref}", ln=True) # [cite: 61]
    
    # Colonne Droite : Image Produit (Icecat)
    try:
        # Tentative d'extraction de l'image dans le JSON
        img_url = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img_url:
            pdf.image(img_url, x=w_utile * 0.7, y=y_start, w=45)
    except:
        pass

    pdf.set_xy(10, y_start + 25)
    pdf.set_draw_color(30, 136, 229)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # --- SPÉCIFICATIONS TECHNIQUES (FORMAT COMPACT) ---
    if "FeaturesGroups" in specs: # [cite: 4, 38]
        # On filtre pour ne pas répéter "GÉNÉRAL"
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', 'Specs')
            if g_name.upper() == "GÉNÉRAL": continue # On saute les titres inutiles [cite: 38, 49, 56]
            
            # Titre de section compact
            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_text_color(30, 136, 229)
            pdf.cell(w_utile, 6, f" {g_name.upper()}", ln=True, fill=True)
            
            pdf.set_font("Arial", "", 8)
            pdf.set_text_color(0, 0, 0)
            
            # Affichage deux colonnes simulé pour gagner de la place
            for feat in group.get("Features", []):
                name = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                val = feat.get("PresentationValue", "")
                
                if name and val:
                    txt = f"{name}: {val}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(w_utile, 4, f"  > {txt}") # [cite: 39-48]
            pdf.ln(2)

    # Pied de page discret
    pdf.set_y(-12)
    pdf.set_font("Arial", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Document généré par WIKIDATA IT - wikidata-it.streamlit.app", align='C') # [cite: 113]

    return bytes(pdf.output())
