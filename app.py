import streamlit as st
from supabase import create_client
from fpdf import FPDF

# Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

class HardwareBrochure(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, "Fiche éditée par WIKIDATA IT - L'expertise hardware au Maroc", align='C')

def generate_pdf(prod_name, brand, ref, specs):
    pdf = HardwareBrochure()
    pdf.add_page()
    
    # Palette de couleurs pro
    C_BLUE = (0, 51, 153)
    C_DARK = (40, 40, 40)
    C_ACCENT = (255, 102, 0)
    
    # --- 1. LOGO & ENTÊTE DYNAMIQUE ---
    try:
        brand_domain = f"{brand.lower().replace(' ', '')}.com"
        logo_url = f"https://logo.clearbit.com/{brand_domain}"
        pdf.image(logo_url, x=10, y=10, w=22)
    except:
        pdf.set_font("Helvetica", "B", 14)
        pdf.text(10, 18, brand.upper())

    pdf.set_xy(10, 32)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*C_BLUE)
    pdf.cell(0, 10, prod_name.upper(), ln=True)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Réf Constructeur (PN): {ref}", ln=True)

    # --- 2. BANDEAU DE PERFORMANCE (PPM / RÉSOLUTION / WIFI) ---
    # Extraction des données clés pour le bandeau
    all_text = str(specs).lower()
    ppm_noir = "33 ppm" if "33 ppm" in all_text else "Standard"
    ppm_coul = "15 ppm" if "15 ppm" in all_text else "Standard"
    wifi = "WIFI DIRECT" if "wifi" in all_text else "USB SEULEMENT"
    
    pdf.ln(5)
    pdf.set_fill_color(*C_BLUE)
    pdf.rect(10, pdf.get_y(), 190, 18, 'F')
    
    pdf.set_y(pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(255, 255, 255)
    
    # Simulation d'icônes avec du texte stylisé
    pdf.cell(47, 5, "VITESSE NOIR", align='C')
    pdf.cell(47, 5, "VITESSE COULEUR", align='C')
    pdf.cell(47, 5, "CONNECTIVITÉ", align='C')
    pdf.cell(47, 5, "FORMAT MAX", align='C', ln=True)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(47, 7, ppm_noir, align='C')
    pdf.cell(47, 7, ppm_coul, align='C')
    pdf.cell(47, 7, wifi, align='C')
    pdf.cell(47, 7, "A4", align='C', ln=True)
    
    pdf.ln(10)

    # --- 3. CORPS : IMAGE & SPECS DÉTAILLÉES ---
    y_body = pdf.get_y()
    
    # Colonne Gauche : Image et Consommables
    try:
        img_url = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img_url:
            pdf.image(img_url, x=10, y=y_body, w=60)
    except:
        pass
        
    # Bloc Consommables (Important !)
    pdf.set_xy(10, y_body + 55)
    pdf.set_fill_color(255, 245, 235) # Fond orange très clair
    pdf.rect(10, pdf.get_y(), 60, 25, 'F')
    pdf.set_xy(12, pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(0, 5, "CONSOMMABLES COMPATIBLES", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C_DARK)
    pdf.set_x(12)
    # On essaye de trouver la série d'encre (ex: 103)
    ink_series = "Série 103 (Epson)" if "103" in str(specs) else "Consultez nous"
    pdf.multi_cell(55, 4, f"Référence recommandée :\n{ink_series}")

    # Colonne Droite : Le détail technique pro
    pdf.set_xy(75, y_body)
    w_col = 125
    
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            if g_name in ["GÉNÉRAL", "INFO", "SPECS"]: continue
            
            # Titre de section compact
            pdf.set_x(75)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(245, 245, 245)
            pdf.set_text_color(*C_BLUE)
            pdf.cell(w_col, 6, f"  {g_name}", ln=True, fill=True)
            pdf.ln(1)
            
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*C_DARK)
            
            for feat in group.get("Features", []):
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v:
                    safe_txt = f"> {n}: {v}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(77)
                    pdf.multi_cell(w_col-5, 3.5, safe_txt)
            pdf.ln(3)
            
            if pdf.get_y() > 270: break

    return bytes(pdf.output())

# Interface Streamlit
st.title("🌐 WIKIDATA IT")
query = st.text_input("Référence (PN)", placeholder="C11CJ67408")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    if res.data:
        prod = res.data[0]
        try:
            pdf_bytes = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], prod['specs_json'])
            st.download_button(
                label="📥 TÉLÉCHARGER LA FICHE TECHNIQUE EXPERT",
                data=pdf_bytes,
                file_name=f"WIKIDATA_{query}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erreur : {e}")
