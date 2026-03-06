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
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "WIKIDATA IT - Document généré via wikidata-it.streamlit.app", align='C')

def generate_pdf(prod_name, brand, ref, specs):
    # Utilisation de 'Helvetica' (plus robuste pour les caractères spéciaux)
    pdf = BrochurePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Couleurs Premium
    C_BLUE = (0, 51, 153)
    C_LIGHT_BLUE = (230, 240, 255)
    
    # --- 1. ENTÊTE : LOGO DYNAMIQUE ---
    try:
        brand_domain = f"{brand.lower().replace(' ', '')}.com"
        logo_url = f"https://logo.clearbit.com/{brand_domain}"
        pdf.image(logo_url, x=10, y=10, w=22)
    except:
        pdf.set_font("Helvetica", "B", 14)
        pdf.text(10, 18, brand.upper())

    # --- 2. TITRE ET RÉFÉRENCE ---
    pdf.set_xy(10, 32)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*C_BLUE)
    pdf.multi_cell(0, 10, prod_name.upper())
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"PN : {ref} | {brand.upper()}", ln=True)
    pdf.ln(4)

    # --- 3. BARRE DE RÉSUMÉ VISUEL (LES "LOGOS" POINTS FORTS) ---
    pdf.set_fill_color(*C_LIGHT_BLUE)
    pdf.rect(10, pdf.get_y(), 190, 12, 'F')
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_BLUE)
    
    # Détection automatique des fonctions
    has_wifi = "OUI" if "wifi" in str(specs).lower() else "NON"
    has_duplex = "OUI" if "recto" in str(specs).lower() else "NON"
    
    pdf.cell(47, 6, f"[ WIFI : {has_wifi} ]", align='C')
    pdf.cell(47, 6, f"[ FORMAT : A4 ]", align='C')
    pdf.cell(47, 6, f"[ USB : OUI ]", align='C')
    pdf.cell(47, 6, f"[ RECTO-VERSO : {has_duplex} ]", align='C')
    pdf.ln(15)

    # --- 4. MISE EN PAGE 2 COLONNES ---
    y_start_body = pdf.get_y()
    
    # Colonne GAUCHE : Photo Produit
    try:
        img_url = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img_url:
            pdf.image(img_url, x=10, y=y_start_body, w=65)
    except:
        pass

    # Colonne DROITE : Spécifications
    pdf.set_xy(80, y_start_body)
    w_col = 120
    
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            # On ignore les titres "vides"
            if g_name in ["GÉNÉRAL", "SPECS", "INFO", "CARACTÉRISTIQUES"]: continue
            
            # Titre de catégorie stylisé
            pdf.set_x(80)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C_BLUE)
            pdf.cell(w_col, 6, g_name, ln=True)
            pdf.set_draw_color(*C_BLUE)
            pdf.line(80, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(1)
            
            # Liste compacte
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(40, 40, 40)
            
            for feat in group.get("Features", []):
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v:
                    # Encodage sécurisé pour éviter l'erreur FPDFUnicodeEncodingException
                    safe_txt = f"- {n}: {v}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(82)
                    pdf.multi_cell(w_col - 5, 3.5, safe_txt)
            pdf.ln(3)
            
            # Sécurité pour ne pas dépasser la page
            if pdf.get_y() > 270: break

    return bytes(pdf.output())

# --- INTERFACE ---
st.title("🌐 WIKIDATA IT")
query = st.text_input("Saisissez une référence (PN)", placeholder="C11CJ67408")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    if res.data:
        prod = res.data[0]
        try:
            pdf_bytes = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], prod['specs_json'])
            st.download_button(
                label="📄 Télécharger la Fiche Commerciale (1 Page)",
                data=pdf_bytes,
                file_name=f"WIKIDATA_{query}.pdf",
                mime="application/pdf"
            )
            st.success("Fiche optimisée prête !")
        except Exception as e:
            st.error(f"Erreur de génération : {e}")
