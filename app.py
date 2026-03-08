import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def generate_universal_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    all_txt = str(specs).lower()
    cat_id = specs.get("GeneralInfo", {}).get("Category", {}).get("ID", 0)

    # --- LOGIQUE DE DÉTECTION ET CONFIGURATION ---
    # Ordinateurs (Laptops, Desktops, Tablettes)
    if cat_id in [151, 189, 897] or any(x in all_txt for x in ["processor", "ram", "ssd"]):
        cfg = {"name": "INFORMATIQUE", "color": (44, 62, 80), 
               "labels": ["PROCESSEUR", "MÉMOIRE RAM", "STOCKAGE", "SYSTÈME"],
               "values": ["Hautes Perf.", "DDR4 / DDR5", "SSD NVMe", "Windows / macOS"]}
    # Écrans (TV, Moniteurs)
    elif cat_id in [160, 202, 1584] or any(x in all_txt for x in ["hz", "display", "dalle"]):
        cfg = {"name": "AFFICHAGE", "color": (20, 90, 50), 
               "labels": ["DIAGONALE", "RÉSOLUTION", "FRÉQUENCE", "TECHNOLOGIE"],
               "values": ["Taille XL", "4K / UHD", "Fréquence Pro", "OLED / IPS / VA"]}
    # Impression
    elif cat_id in [303, 712] or "ppm" in all_txt:
        cfg = {"name": "IMPRESSION", "color": (0, 51, 153), 
               "labels": ["VITESSE NOIR", "VITESSE COULEUR", "CONNECTIVITÉ", "TYPE ENCRE"],
               "values": ["33 PPM", "15 PPM", "Wi-Fi / USB", "EcoTank / Laser"]}
    # Projection
    elif cat_id in [567] or "lumens" in all_txt:
        cfg = {"name": "PROJECTION", "color": (204, 0, 0), 
               "labels": ["LUMINOSITÉ", "RÉSOLUTION", "IMAGE", "SOURCE"],
               "values": ["3000 ANSI", "WXGA / HD", "3LCD / DLP", "Lampe / Laser"]}
    else:
        cfg = {"name": "HARDWARE", "color": (80, 80, 80), 
               "labels": ["MARQUE", "PN", "TYPE", "USAGE"],
               "values": [brand.upper(), ref, "Matériel IT", "Professionnel"]}

    # --- DESIGN DU PDF ---
    # Logo
    try:
        pdf.image(f"https://logo.clearbit.com/{brand.lower()}.com", x=10, y=10, w=22)
    except:
        pdf.set_font("Helvetica", "B", 14); pdf.text(10, 18, brand.upper())

    # Header
    pdf.set_xy(10, 32)
    pdf.set_font("Helvetica", "B", 18); pdf.set_text_color(*cfg["color"])
    pdf.cell(0, 10, prod_name.upper()[:45], ln=True)
    pdf.set_font("Helvetica", "", 9); pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, f"PN: {ref}  |  CATÉGORIE: {cfg['name']}", ln=True)

    # Bandeau Performance
    pdf.ln(5)
    pdf.set_fill_color(*cfg["color"])
    pdf.rect(10, pdf.get_y(), 190, 16, 'F')
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(255, 255, 255)
    for l in cfg["labels"]: pdf.cell(47.5, 5, l, align='C')
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    for v in cfg["values"]: pdf.cell(47.5, 6, v, align='C')
    
    pdf.ln(12)
    y_start = pdf.get_y()

    # Image (Gauche)
    try:
        img = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img: pdf.image(img, x=10, y=y_start, w=55)
    except: pass

    # Détails (Droite)
    pdf.set_xy(70, y_start)
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
                    txt = f"> {n}: {v}".replace('°', ' deg').replace('²', '2').encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(72); pdf.multi_cell(125, 3.2, txt)
            pdf.ln(2)
            if pdf.get_y() > 275: break

    return bytes(pdf.output())

# Interface Streamlit
st.markdown("<h1 style='text-align: center;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)
query = st.text_input("Référence Constructeur (PN)")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    if res.data:
        prod = res.data[0]
        pdf_bytes = generate_universal_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], prod['specs_json'])
        st.download_button("📥 TÉLÉCHARGER LA BROCHURE EXPERT", pdf_bytes, f"WIKIDATA_{query}.pdf")
    else:
        st.warning("Produit non trouvé. Vérifiez la référence ou lancez le scraper.")
