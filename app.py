import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Configuration de la page
st.set_page_config(page_title="WIKIDATA IT", page_icon="🌐", layout="centered")

# 2. Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

class FicheTechnique(FPDF):
    def header(self):
        # Cette partie est gérée dans generate_pdf pour être dynamique
        pass

def generate_pdf(prod_name, brand, ref, specs):
    pdf = FicheTechnique()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Couleurs Epson-style
    c_bleu = (0, 51, 153)
    c_gris_fond = (245, 245, 245)
    
    # --- LOGO OFFICIEL ---
    try:
        brand_domain = f"{brand.lower().replace(' ', '')}.com"
        logo_url = f"https://logo.clearbit.com/{brand_domain}"
        pdf.image(logo_url, x=10, y=10, w=25)
    except:
        pdf.set_font("Arial", "B", 16)
        pdf.text(10, 20, brand.upper())

    # --- TITRE PRINCIPAL ---
    pdf.set_xy(10, 30)
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(*c_bleu)
    pdf.cell(0, 15, prod_name.upper(), ln=True)
    
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Réf: {ref} | {brand.upper()}", ln=True)
    pdf.ln(10)

    # --- COLONNE GAUCHE (Points Forts / Image) ---
    y_corps = pdf.get_y()
    
    # Image Produit
    try:
        img_url = specs.get("GeneralInfo", {}).get("Image", {}).get("HighPic")
        if img_url:
            pdf.image(img_url, x=10, y=y_corps, w=60)
    except:
        pdf.rect(10, y_corps, 60, 45) # Cadre vide si pas d'image
    
    # --- COLONNE DROITE (Détails Techniques) ---
    pdf.set_xy(75, y_corps)
    w_col_droite = 125

    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', '').upper()
            # On ignore les noms de groupes génériques peu esthétiques
            if g_name in ["GÉNÉRAL", "SPECS", "INFO"]: continue
            
            # Titre de catégorie
            pdf.set_x(75)
            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(*c_bleu)
            pdf.cell(w_col_droite, 8, g_name, ln=True)
            
            # Ligne de séparation fine
            pdf.set_draw_color(*c_bleu)
            pdf.line(75, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
            
            # Caractéristiques
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(50, 50, 50)
            
            for feat in group.get("Features", []):
                name = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                val = feat.get("PresentationValue", "")
                if name and val:
                    txt = f"{name}: {val}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_x(77)
                    pdf.multi_cell(w_col_droite - 2, 5, f"- {txt}")
            pdf.ln(4)

    # Pied de page
    pdf.set_y(-15)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(180, 180, 180)
    pdf.cell(0, 10, "WIKIDATA IT - LA BASE DE CONNAISSANCES HARDWARE DU MAROC", align='C')

    return bytes(pdf.output())

# 4. Interface Streamlit
st.markdown("<h1 style='text-align: center; color: #003399;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)

query = st.text_input("", placeholder="Rechercher une référence (ex: C11CJ67408)...")

if query:
    res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query.strip()).execute()
    
    if res.data:
        prod = res.data[0]
        specs = prod['specs_json']
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"{prod['nom_produit']}")
        with col2:
            try:
                pdf_data = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], specs)
                st.download_button(
                    label="📄 Télécharger la Brochure",
                    data=pdf_data,
                    file_name=f"Brochure_{prod['ref_constructeur']}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erreur : {e}")

        st.divider()
        
        # Affichage Web interactif
        if "FeaturesGroups" in specs:
            for group in specs["FeaturesGroups"]:
                with st.expander(f"🔍 {group.get('GroupName', 'Caractéristiques')}"):
                    for feat in group.get("Features", []):
                        n = feat.get("Feature", {}).get("Name", {}).get("Value")
                        v = feat.get("PresentationValue")
                        if n and v: st.write(f"**{n} :** {v}")
    else:
        st.error("Produit introuvable.")
