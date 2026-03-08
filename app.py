import streamlit as st
from supabase import create_client
from fpdf import FPDF

# Configuration Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def get_category(specs_txt):
    """Détecte la catégorie avec un système de score strict"""
    scores = {
        "IMPRESSION": specs_txt.count("ppm") + specs_txt.count("ink") + specs_txt.count("impression"),
        "AFFICHAGE": specs_txt.count("hz") + specs_txt.count("pouces") + specs_txt.count("display") + specs_txt.count("dalle"),
        "INFORMATIQUE": specs_txt.count("processor") + specs_txt.count("ram") + specs_txt.count("ssd") + specs_txt.count("coeurs")
    }
    # Retourne la catégorie avec le score le plus élevé
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "HARDWARE"

def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    all_txt = str(specs).lower()
    cat = get_category(all_txt)
    
    # Couleurs par catégorie
    colors = {"IMPRESSION": (0, 51, 153), "AFFICHAGE": (20, 90, 50), "INFORMATIQUE": (44, 62, 80), "HARDWARE": (100, 100, 100)}
    active_color = colors.get(cat)

    # 1. Logo & Header
    try:
        pdf.image(f"https://logo.clearbit.com/{brand.lower().replace(' ', '')}.com", x=10, y=10, w=25)
    except:
        pdf.set_font("Helvetica", "B", 16); pdf.text(10, 20, brand.upper())

    pdf.set_xy(10, 32)
    pdf.set_font("Helvetica", "B", 18); pdf.set_text_color(*active_color)
    pdf.cell(0, 10, prod_name.upper(), ln=True)
    pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f"PN: {ref}  |  CATEGORIE: {cat}", ln=True)

    # 2. Bandeau de Performance (Labels Dynamiques réels)
    pdf.ln(5)
    pdf.set_fill_color(*active_color)
    pdf.rect(10, pdf.get_y(), 190, 16, 'F')
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(255, 255, 255)
    
    # On définit les vrais labels ici
    labels = {
        "IMPRESSION": ["VITESSE NOIR", "VITESSE COULEUR", "CONNECTIVITE", "RESOLUTION"],
        "AFFICHAGE": ["DIAGONALE", "RESOLUTION", "FREQUENCE", "TECHNOLOGIE"],
        "INFORMATIQUE": ["PROCESSEUR", "RAM", "STOCKAGE", "ECRAN"]
    }.get(cat, ["MARQUE", "REF", "TYPE", "USAGE"])
    
    for l in labels: pdf.cell(47.5, 5, l, align='C')
    pdf.ln(10)

    # 3. Image et Spécifications (2 colonnes)
    y_body = pdf.get_y()
    try:
        img = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img: pdf.image(img, x=10, y=y_body, w=55)
    except: pass

    pdf.set_xy(70, y_body)
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            if g_name in ["GENERAL", "INFO", "SPECS"]: continue
            
            pdf.set_x(70)
            pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(245, 245, 245)
            pdf.set_text_color(*active_color)
            pdf.cell(130, 6, f"  {g_name}", ln=True, fill=True)
            
            pdf.set_font("Helvetica", "", 7.5); pdf.set_text_color(50, 50, 50)
            for feat in group.get("Features", []):
                n, v = feat.get("Feature", {}).get("Name", {}).get("Value"), feat.get("PresentationValue")
                if n and v:
                    line = f"- {n}: {v}".replace('°', ' deg').replace('²', '2').encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(72); pdf.multi_cell(125, 3.2, line)
            pdf.ln(2)
            if pdf.get_y() > 275: break

    return bytes(pdf.output())

# --- Interface Streamlit ---
st.markdown("<h1 style='text-align: center;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)
query = st.text_input("Référence (PN)")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    if res.data:
        prod = res.data[0]
        pdf_bytes = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], prod['specs_json'])
        st.download_button("📥 TELECHARGER LA BROCHURE EXPERT", pdf_bytes, f"WIKIDATA_{query}.pdf")
