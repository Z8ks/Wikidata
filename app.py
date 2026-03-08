import streamlit as st
from supabase import create_client
from fpdf import FPDF

# Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    all_txt = str(specs).lower()
    
    # --- 1. MOTEUR DE DÉTECTION DE CATÉGORIE ---
    if "processor" in all_txt or "ram" in all_txt:
        cat, color = "INFORMATIQUE", (44, 62, 80) # Bleu Nuit
        labels = ["PROCESSEUR", "MÉMOIRE RAM", "STOCKAGE", "ÉCRAN"]
        values = ["Core / Ryzen", "8GB / 16GB", "SSD NVMe", "Full HD / IPS"]
    elif "refresh rate" in all_txt or "pouces" in all_txt or "display" in all_txt:
        cat, color = "AFFICHAGE", (0, 102, 102) # Vert Canard
        labels = ["DIAGONALE", "RÉSOLUTION", "FRÉQUENCE", "DALLE"]
        values = ["24 / 27 / 55''", "4K / QHD", "144Hz / 60Hz", "OLED / IPS / VA"]
    elif "ppm" in all_txt or "impression" in all_txt:
        cat, color = "IMPRESSION", (0, 51, 153) # Bleu Epson
        labels = ["VITESSE NOIR", "VITESSE COULEUR", "RECTO-VERSO", "TYPE"]
        values = ["33 PPM", "15 PPM", "OUI", "ECOTANK / LASER"]
    elif "lumens" in all_txt or "projection" in all_txt:
        cat, color = "PROJECTION", (204, 0, 0) # Rouge
        labels = ["LUMINOSITÉ", "RÉSOLUTION", "IMAGE", "DURÉE LAMPE"]
        values = ["3000 LUMENS", "WXGA", "3LCD / DLP", "12 000 H"]
    else:
        cat, color = "ACCESSOIRE", (80, 80, 80) # Gris
        labels = ["MARQUE", "PN", "TYPE", "USAGE"]
        values = [brand.upper(), ref, "HARDWARE", "PROFESSIONNEL"]

    # --- 2. RENDU GRAPHIQUE ---
    # Logo Officiel
    try:
        pdf.image(f"https://logo.clearbit.com/{brand.lower().replace(' ', '')}.com", x=10, y=10, w=22)
    except:
        pdf.set_font("Helvetica", "B", 14); pdf.text(10, 18, brand.upper())

    # Titre et Header
    pdf.set_xy(40, 10)
    pdf.set_font("Helvetica", "B", 18); pdf.set_text_color(*color)
    pdf.cell(0, 10, prod_name.upper(), ln=True, align='R')
    pdf.set_font("Helvetica", "", 9); pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, f"PN: {ref} | Catégorie: {cat}", ln=True, align='R')

    # Bandeau Performance Dynamique
    pdf.ln(8)
    pdf.set_fill_color(*color)
    pdf.rect(10, pdf.get_y(), 190, 16, 'F')
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(255, 255, 255)
    for l in labels: pdf.cell(47.5, 5, l, align='C')
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    for v in values: pdf.cell(47.5, 6, v, align='C')
    
    pdf.ln(12)
    y_top = pdf.get_y()

    # Image Produit
    try:
        img = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img: pdf.image(img, x=10, y=y_top, w=55)
    except: pass

    # Bloc Expertise (Consommables / Garantie)
    pdf.set_xy(10, y_top + 50)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, pdf.get_y(), 55, 22, 'F')
    pdf.set_xy(12, pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*color)
    pdf.cell(0, 5, "INFOS COMPLÉMENTAIRES", ln=True)
    pdf.set_font("Helvetica", "", 8); pdf.set_text_color(0, 0, 0)
    pdf.set_x(12); pdf.multi_cell(50, 4, f"Produit {brand.upper()} garanti d'origine constructeur.")

    # Spécifications détaillées (Format 1 Page)
    pdf.set_xy(70, y_top)
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            if g_name in ["GÉNÉRAL", "INFO", "SPECS"]: continue
            
            pdf.set_x(70)
            pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(252, 252, 252)
            pdf.set_text_color(*color)
            pdf.cell(130, 6, f"  {g_name}", ln=True, fill=True)
            
            pdf.set_font("Helvetica", "", 7.5); pdf.set_text_color(60, 60, 60)
            for feat in group.get("Features", []):
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v:
                    # Correction Unicode pour éviter le plantage sur les symboles °, ², etc.
                    txt = f"> {n}: {v}".replace('°', ' deg').replace('²', '2').encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(72); pdf.multi_cell(125, 3.2, txt)
            pdf.ln(2)
            if pdf.get_y() > 275: break

    return bytes(pdf.output())
