import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

class BrochurePDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "WIKIDATA IT - Document généré automatiquement via wikidata-it.streamlit.app", align='C')

def generate_pdf(prod_name, brand, ref, specs):
    pdf = BrochurePDF()
    pdf.add_page()
    
    # Couleurs
    C_BLUE = (0, 75, 145) # Bleu Epson
    C_GREY = (240, 240, 240)
    
    # --- 1. ENTÊTE AVEC LOGO ---
    try:
        brand_domain = f"{brand.lower().replace(' ', '')}.com"
        logo_url = f"https://logo.clearbit.com/{brand_domain}"
        pdf.image(logo_url, x=10, y=10, w=25)
    except:
        pdf.set_font("Arial", "B", 15)
        pdf.text(10, 20, brand.upper())

    pdf.set_xy(10, 30)
    pdf.set_font("Arial", "B", 22)
    pdf.set_text_color(*C_BLUE)
    pdf.cell(0, 10, prod_name.upper(), ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Référence produit (PN) : {ref}", ln=True)

    # --- 2. BARRE D'ICÔNES (RÉSUMÉ TECHNIQUE) ---
    pdf.ln(5)
    pdf.set_fill_color(*C_GREY)
    pdf.rect(10, pdf.get_y(), 190, 15, 'F')
    
    pdf.set_xy(15, pdf.get_y() + 4)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*C_BLUE)
    
    # Détection des technos clés pour les "logos" textuels
    wifi = "OUI" if "wifi" in str(specs).lower() else "NON"
    recto = "OUI" if "recto" in str(specs).lower() else "NON"
    
    pdf.cell(45, 7, f"WIFI : {wifi}", align='C')
    pdf.cell(45, 7, f"FORMAT : A4", align='C')
    pdf.cell(45, 7, f"USB : OUI", align='C')
    pdf.cell(45, 7, f"RECTO-VERSO : {recto}", align='C')
    pdf.ln(15)

    # --- 3. CORPS EN DEUX COLONNES ---
    y_start_cols = pdf.get_y()
    
    # --- COLONNE GAUCHE : IMAGE ET DESCRIPTION ---
    try:
        img_url = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img_url:
            pdf.image(img_url, x=10, y=y_start_cols, w=65)
    except:
        pass

    # --- COLONNE DROITE : SPÉCIFICATIONS TECHNIQUES ---
    pdf.set_xy(80, y_start_cols)
    w_col = 120

    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            if g_name in ["GÉNÉRAL", "SPECS", "CARACTÉRISTIQUES"]: continue
            
            # Titre de section compact
            pdf.set_x(80)
            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(*C_BLUE)
            pdf.cell(w_col, 7, g_name, ln=True)
            pdf.line(80, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(1)
            
            # Liste des caractéristiques (Police 8 pour gain de place)
            pdf.set_font("Arial", "", 8)
            pdf.set_text_color(0, 0, 0)
            
            for feat in group.get("Features", []):
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v:
                    txt = f"{n}: {v}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(82)
                    pdf.multi_cell(w_col - 5, 4, f"• {txt}")
            
            pdf.ln(3)
            # Vérifier si on dépasse la page
            if pdf.get_y() > 260: break 

    return bytes(pdf.output())

# --- INTERFACE STREAMLIT ---
st.title("🌐 WIKIDATA IT")
query = st.text_input("Référence (ex: C11CJ67408)")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    if res.data:
        prod = res.data[0]
        pdf_data = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], prod['specs_json'])
        st.download_button("📥 Télécharger la Brochure Officielle", pdf_data, f"Brochure_{query}.pdf", "application/pdf")
        st.success("Brochure générée sur 1 page.")
