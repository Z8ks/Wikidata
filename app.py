import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

class PremiumBrochure(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, "WIKIDATA IT - L'expertise Hardware au Maroc", align='C')

def generate_pdf(prod_name, brand, ref, specs):
    pdf = PremiumBrochure()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    # Palette de couleurs
    PRIMARY = (0, 51, 153)    # Bleu Royal
    ACCENT = (255, 102, 0)     # Orange Action
    LIGHT_BG = (245, 247, 250) # Gris bleu très clair
    
    # --- 1. ENTÊTE & LOGO ---
    try:
        brand_domain = f"{brand.lower().replace(' ', '')}.com"
        logo_url = f"https://logo.clearbit.com/{brand_domain}"
        pdf.image(logo_url, x=10, y=10, w=25)
    except:
        pdf.set_font("Helvetica", "B", 16)
        pdf.text(10, 20, brand.upper())

    pdf.set_xy(10, 32)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*PRIMARY)
    pdf.multi_cell(130, 10, prod_name.upper()) # Nom du produit
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.text(11, 55, f"PN: {ref}")
    
    # --- 2. BADGES VISUELS (ICÔNES STYLISÉES) ---
    # On crée des blocs de couleur pour chaque techno clé
    pdf.set_xy(10, 60)
    technos = [
        ("WIFI", PRIMARY if "wifi" in str(specs).lower() else (200, 200, 200)),
        ("A4 FORMAT", PRIMARY),
        ("ECO-TANK", ACCENT if "tank" in str(specs).lower() or "bouteille" in str(specs).lower() else PRIMARY),
        ("USB 2.0", PRIMARY)
    ]
    
    for label, color in technos:
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        curr_x = pdf.get_x()
        curr_y = pdf.get_y()
        pdf.rect(curr_x, curr_y, 35, 8, 'F')
        pdf.cell(35, 8, label, align='C')
        pdf.set_x(curr_x + 40)

    # --- 3. MISE EN PAGE 2 COLONNES ---
    y_body = 75
    
    # Colonne GAUCHE : Photo & Points Forts
    try:
        img_url = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img_url:
            pdf.image(img_url, x=10, y=y_body, w=60)
    except:
        pass
    
    # Colonne DROITE : Spécifications techniques
    pdf.set_xy(75, y_body)
    w_col = 125
    
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            if g_name in ["GÉNÉRAL", "SPECS", "INFO"]: continue
            
            # Titre de section coloré
            pdf.set_x(75)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(*LIGHT_BG)
            pdf.set_text_color(*PRIMARY)
            pdf.cell(w_col, 7, f"  {g_name}", ln=True, fill=True)
            pdf.ln(1)
            
            # Liste des caractéristiques
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(60, 60, 60)
            
            for feat in group.get("Features", []):
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v:
                    # Encodage sécurisé (remplace les caractères inconnus par ?)
                    safe_line = f"> {n}: {v}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(77)
                    pdf.multi_cell(w_col-5, 3.8, safe_line)
            pdf.ln(3)
            
            if pdf.get_y() > 275: break # Évite de créer une page 2 inutile

    return bytes(pdf.output())

# --- INTERFACE STREAMLIT ---
st.markdown("<h1 style='text-align: center; color: #003399;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)
query = st.text_input("Référence (PN)", placeholder="C11CJ67408")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    if res.data:
        prod = res.data[0]
        try:
            pdf_bytes = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], prod['specs_json'])
            st.download_button(
                label="📥 TÉLÉCHARGER LA BROCHURE PREMIUM (1 PAGE)",
                data=pdf_bytes,
                file_name=f"WIKIDATA_{query}.pdf",
                mime="application/pdf"
            )
            st.success(f"Brochure générée pour {prod['nom_produit']}")
        except Exception as e:
            st.error(f"Erreur : {e}")
