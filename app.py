import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

class WikidataBrochure(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "WIKIDATA IT - La base de données hardware n°1 au Maroc", align='C')

def generate_pdf(prod_name, brand, ref, specs):
    pdf = WikidataBrochure()
    pdf.add_page()
    
    # Couleurs de la charte
    C_BLUE = (0, 51, 153)
    C_GREY_TEXT = (80, 80, 80)
    C_LINE = (220, 220, 220)

    # --- 1. LOGO OFFICIEL DE LA MARQUE ---
    # Utilisation de l'API Clearbit pour récupérer le vrai logo (ex: logo Epson)
    brand_domain = f"{brand.lower().strip().replace(' ', '')}.com"
    logo_url = f"https://logo.clearbit.com/{brand_domain}"
    
    try:
        pdf.image(logo_url, x=10, y=10, w=25)
    except:
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_xy(10, 10)
        pdf.cell(0, 10, brand.upper())

    # --- 2. TITRE & RÉFÉRENCE ---
    pdf.set_xy(40, 10)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*C_BLUE)
    pdf.cell(0, 10, prod_name.upper(), ln=True, align='R')
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Référence Constructeur : {ref}", ln=True, align='R')

    # --- 3. SIGNALÉTIQUE TECHNIQUE (ICÔNES STYLISÉES) ---
    pdf.ln(10)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, pdf.get_y(), 190, 20, 'F')
    
    # Extraction des Specs Clés (PPM, Recto-Verso, etc.)
    all_specs = str(specs).lower()
    ppm = "33 PPM" if "33" in all_specs else "Standard"
    wifi = "Wi-Fi Direct" if "wifi" in all_specs else "USB"
    format_p = "A4 / Photo"
    
    pdf.set_y(pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_BLUE)
    
    # Colonnes de signalétique
    cols = [("VITESSE NOIR", ppm), ("CONNECTIVITÉ", wifi), ("FORMAT", format_p), ("RÉSOLUTION", "5760x1440")]
    for title, val in cols:
        curr_x = pdf.get_x()
        pdf.cell(47.5, 5, title, align='C', ln=0)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 0, 0)
    for title, val in cols:
        pdf.cell(47.5, 7, val, align='C', ln=0)
    
    pdf.ln(15)

    # --- 4. PHOTO & DÉTAILS ---
    y_body = pdf.get_y()
    
    # Image du matériel
    try:
        img_url = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img_url:
            pdf.image(img_url, x=10, y=y_body, w=65)
    except:
        pass

    # Bloc "CONSOMMABLES" (Crucial pour la vente)
    pdf.set_xy(10, y_body + 60)
    pdf.set_fill_color(255, 240, 230) # Orange clair
    pdf.rect(10, pdf.get_y(), 65, 25, 'F')
    pdf.set_xy(13, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(255, 102, 0)
    pdf.cell(0, 5, "CONSOMMABLES", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(13)
    ink = "Série 103 EcoTank" if "103" in all_specs else "Vérifier compatibilité"
    pdf.multi_cell(60, 5, f"Encre recommandée :\n{ink}")

    # --- 5. SPÉCIFICATIONS TECHNIQUES DÉTAILLÉES ---
    pdf.set_xy(80, y_body)
    w_col = 120
    
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            if g_name in ["GÉNÉRAL", "SPECS", "INFO"]: continue
            
            # Sous-titre de section
            pdf.set_x(80)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*C_BLUE)
            pdf.cell(w_col, 8, g_name, ln=True)
            pdf.line(80, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
            
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*C_GREY_TEXT)
            
            for feat in group.get("Features", []):
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v:
                    # Sécurisation des caractères pour éviter le plantage
                    line = f"- {n} : {v}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(82)
                    pdf.multi_cell(w_col - 5, 4, line)
            pdf.ln(4)
            if pdf.get_y() > 270: break

    return bytes(pdf.output())

# --- INTERFACE STREAMLIT ---
st.title("🌐 WIKIDATA IT")
query = st.text_input("Saisissez une référence (PN)", placeholder="C11CJ67408")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    if res.data:
        prod = res.data[0]
        pdf_bytes = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], prod['specs_json'])
        st.download_button(
            label="📥 TÉLÉCHARGER LA FICHE COMMERCIALE",
            data=pdf_bytes,
            file_name=f"Brochure_{query}.pdf",
            mime="application/pdf"
        )
