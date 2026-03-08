import streamlit as st
from supabase import create_client
from fpdf import FPDF

# Configuration
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def generate_pro_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. DÉTECTION PAR ID DE CATÉGORIE (MÉTHODE PROFESSIONNELLE)
    # On récupère l'ID directement dans le JSON d'Icecat
    cat_id = specs.get("GeneralInfo", {}).get("Category", {}).get("ID", 0)
    
    # Configuration des templates par métier
    if cat_id in [303, 712]: # IMPRIMANTES
        cfg = {"name": "IMPRESSION", "color": (0, 51, 153), 
               "labels": ["VITESSE NOIR", "VITESSE COULEUR", "CONNECTIVITÉ", "TYPE D'ENCRE"],
               "values": ["33 PPM", "15 PPM", "Wi-Fi / USB", "EcoTank / Laser"]}
    elif cat_id in [567]: # PROJECTEURS
        cfg = {"name": "PROJECTION", "color": (204, 0, 0), 
               "labels": ["LUMINOSITÉ", "RÉSOLUTION", "IMAGE", "SOURCE LUMINEUSE"],
               "values": ["3000 ANSI", "WXGA / HD", "3LCD / DLP", "Lampe / Laser"]}
    elif cat_id in [151, 189, 897]: # LAPTOPS / TABLETTES / PC
        cfg = {"name": "INFORMATIQUE", "color": (44, 62, 80), 
               "labels": ["PROCESSEUR", "RAM", "STOCKAGE", "ÉCRAN"],
               "values": ["Core i5/i7", "8GB/16GB", "SSD NVMe", "Full HD IPS"]}
    else: # PAR DÉFAUT (TV, ACCESSOIRES, ETC.)
        cfg = {"name": "HARDWARE", "color": (80, 80, 80), 
               "labels": ["MARQUE", "PN", "USAGE", "GARANTIE"],
               "values": [brand.upper(), ref, "Professionnel", "12 Mois"]}

    # --- RENDU GRAPHIQUE (MAX 1 PAGE) ---
    # Logo Officiel
    try:
        pdf.image(f"https://logo.clearbit.com/{brand.lower()}.com", x=10, y=10, w=22)
    except:
        pdf.set_font("Helvetica", "B", 14); pdf.text(10, 18, brand.upper())

    # Header
    pdf.set_xy(40, 10)
    pdf.set_font("Helvetica", "B", 18); pdf.set_text_color(*cfg["color"])
    pdf.cell(0, 10, prod_name.upper()[:40], ln=True, align='R')
    pdf.set_font("Helvetica", "", 9); pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f"PN: {ref}  |  CATÉGORIE: {cfg['name']}", ln=True, align='R')

    # Bandeau Performance Dynamique
    pdf.ln(8)
    pdf.set_fill_color(*cfg["color"])
    pdf.rect(10, pdf.get_y(), 190, 16, 'F')
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(255, 255, 255)
    for l in cfg["labels"]: pdf.cell(47.5, 5, l, align='C')
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    for v in cfg["values"]: pdf.cell(47.5, 6, v, align='C')

    pdf.ln(12)
    y_body = pdf.get_y()

    # Image Produit
    try:
        img = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img: pdf.image(img, x=10, y=y_body, w=55)
    except: pass

    # Détails Techniques (Police compacte pour tenir sur 1 page)
    pdf.set_xy(70, y_body)
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            if g_name in ["GÉNÉRAL", "INFO", "SPECS"]: continue
            
            pdf.set_x(70)
            pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(248, 248, 248)
            pdf.set_text_color(*cfg["color"])
            pdf.cell(130, 6, f"  {g_name}", ln=True, fill=True)
            
            pdf.set_font("Helvetica", "", 7.5); pdf.set_text_color(60, 60, 60)
            for feat in group.get("Features", []):
                n, v = feat.get("Feature", {}).get("Name", {}).get("Value"), feat.get("PresentationValue")
                if n and v:
                    # Nettoyage Unicode critique pour les projecteurs (° et ²)
                    line = f"> {n}: {v}".replace('°', ' deg').replace('²', '2').encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(72); pdf.multi_cell(125, 3.2, line)
            pdf.ln(2)
            if pdf.get_y() > 275: break # Sécurité 1 page

    return bytes(pdf.output())

# Interface Streamlit
st.title("🌐 WIKIDATA IT")
query = st.text_input("Référence (PN)")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    if res.data:
        prod = res.data[0]
        pdf_bytes = generate_pro_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], prod['specs_json'])
        st.download_button("📥 TÉLÉCHARGER LA FICHE COMMERCIALE", pdf_bytes, f"WIKIDATA_{query}.pdf")
