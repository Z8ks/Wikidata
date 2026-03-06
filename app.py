import streamlit as st
from supabase import create_client
from fpdf import FPDF

# 1. Configuration de la page
st.set_page_config(page_title="WIKIDATA IT", page_icon="🌐", layout="centered")

# 2. Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 3. Fonction de génération PDF corrigée (Design Pro & Texte fluide)
def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    
    # Marges
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    w_utile = pdf.w - 2 * pdf.l_margin
    
    # --- BANDEAU BLEU (LOGO TEXTUEL) ---
    pdf.set_fill_color(30, 136, 229) 
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_xy(15, 15)
    pdf.set_font("Arial", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "WIKIDATA IT", ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "LA BASE DE CONNAISSANCES HARDWARE DU MAROC", ln=True)
    
    # --- ESPACEMENT ---
    pdf.set_xy(15, 50)
    
    # --- TITRE DU PRODUIT ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    # multi_cell permet au nom de s'étaler sans être coupé
    pdf.multi_cell(w_utile, 10, f"FICHE TECHNIQUE : {prod_name}")
    
    # --- INFOS MARQUE & REF ---
    pdf.ln(2)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(w_utile/2, 10, f"MARQUE : {brand.upper()}")
    pdf.cell(w_utile/2, 10, f"RÉF : {ref}", ln=True, align='R')
    
    # Ligne de séparation
    pdf.set_draw_color(200, 200, 200)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(10)

    # --- SPÉCIFICATIONS TECHNIQUES ---
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            g_name = group.get('GroupName', 'Général')
            
            # En-tête de section (Fond gris clair, texte bleu)
            pdf.set_font("Arial", "B", 12)
            pdf.set_fill_color(245, 245, 245)
            pdf.set_text_color(30, 136, 229)
            pdf.cell(w_utile, 9, f"  {g_name.upper()}", ln=True, fill=True)
            pdf.ln(2)
            
            # Liste des caractéristiques
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(0, 0, 0)
            
            for feat in group.get("Features", []):
                name = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                val = feat.get("PresentationValue", "")
                
                if name and val:
                    # Encodage sécurisé pour éviter les erreurs de caractères spéciaux
                    line_text = f"{name} : {val}".encode('latin-1', 'replace').decode('latin-1')
                    # On utilise multi_cell avec un petit retrait pour la lisibilité
                    pdf.set_x(20)
                    pdf.multi_cell(w_utile - 5, 7, f"- {line_text}")
            
            pdf.ln(5) # Espace entre les blocs

    # Pied de page
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Document généré par WIKIDATA IT - wikidata-it.streamlit.app", align='C')

    # Sortie propre en Bytes pour Streamlit
    return bytes(pdf.output())

# 4. Interface Streamlit
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)

query = st.text_input("", placeholder="Saisissez une référence (ex: C11CJ67408)...")

if query:
    query_clean = query.strip()
    with st.spinner('Récupération de la fiche...'):
        res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", query_clean).execute()
    
    if res.data:
        prod = res.data[0]
        specs = prod['specs_json']
        
        st.success(f"**Modèle :** {prod['nom_produit']}")
        
        # Bouton PDF
        try:
            pdf_data = generate_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], specs)
            st.download_button(
                label="📥 Télécharger la Fiche PDF WIKIDATA",
                data=pdf_data,
                file_name=f"WIKIDATA_{prod['ref_constructeur']}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erreur PDF : {e}")
            
        st.divider()
        
        # Affichage propre sur le Web
        if "FeaturesGroups" in specs:
            for group in specs["FeaturesGroups"]:
                with st.expander(f"🔹 {group.get('GroupName', 'Spécifications')}"):
                    for feat in group.get("Features", []):
                        n = feat.get("Feature", {}).get("Name", {}).get("Value")
                        v = feat.get("PresentationValue")
                        if n and v: st.write(f"**{n} :** {v}")
    else:
        st.error("Produit non trouvé dans la base.")
