import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Configuration de la page WIKIDATA IT
st.set_page_config(page_title="WIKIDATA IT", page_icon="🌐", layout="centered")

# 2. Connexion à ta base de données Supabase
# Assure-toi que SUPABASE_KEY est configurée dans les "Secrets" de Streamlit
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 3. Fonction de génération du PDF (Version Pro avec Logo)
def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    
    # Marges et largeur utile
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    w_utile = pdf.w - 2 * pdf.l_margin
    
    # --- BANDEAU ENTÊTE ---
    pdf.set_fill_color(30, 136, 229) 
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_xy(15, 15)
    pdf.set_font("Arial", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "WIKIDATA IT", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "LA BASE DE CONNAISSANCES HARDWARE DU MAROC", ln=True)
    
    pdf.ln(20) # Espace après le bandeau
    
    # --- INFOS PRODUIT (CORRIGÉ) ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    # multi_cell empêche le nom de se couper
    pdf.multi_cell(w_utile, 10, f"FICHE TECHNIQUE : {prod_name}")
    
    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(100, 100, 100)
    # On sépare Marque et PN pour plus de clarté
    pdf.cell(w_utile/2, 10, f"MARQUE : {brand}")
    pdf.cell(w_utile/2, 10, f"RÉF : {ref}", ln=True, align='R')
    
    pdf.ln(5)
    pdf.set_draw_color(30, 136, 229)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y()) # Ligne de séparation bleue
    pdf.ln(5)

    # --- TABLEAU DES SPÉCIFICATIONS ---
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', 'Caractéristiques')
            
            # Titre de la section
            pdf.set_font("Arial", "B", 12)
            pdf.set_fill_color(240, 245, 255)
            pdf.set_text_color(30, 136, 229)
            pdf.cell(w_utile, 9, f" {g_name.upper()}", ln=True, fill=True)
            pdf.ln(2)
            
            # Liste des caractéristiques (Format "Nom : Valeur")
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(0, 0, 0)
            
            for feat in group.get("Features", []):
                name = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                val = feat.get("PresentationValue", "")
                
                if name and val:
                    # On utilise multi_cell pour chaque ligne pour éviter "Technolog..."
                    text = f"- {name} : {val}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(w_utile, 7, text)
            
            pdf.ln(5) # Espace entre les groupes

    return bytes(pdf.output())
