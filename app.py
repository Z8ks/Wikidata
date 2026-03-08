import streamlit as st
from supabase import create_client
from fpdf import FPDF

# Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def clean_txt(text):
    if not text: return ""
    replacements = {'°': ' deg', '²': '2', '×': 'x', '™': '', '®': ''}
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pro_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    cat_id = specs.get("GeneralInfo", {}).get("Category", {}).get("ID", 0)
    
    # Configuration par ID
    if cat_id in [303, 712]: # IMPRESSION
        cfg = {"n": "IMPRESSION", "c": (0, 51, 153), "l": ["VITESSE", "WIFI", "RESOLUTION", "TYPE"]}
    elif cat_id in [160, 202, 1584]: # ECRANS / TV
        cfg = {"n": "AFFICHAGE", "c": (20, 90, 50), "l": ["TAILLE", "RESOLUTION", "HERTZ", "DALLE"]}
    elif cat_id in [151, 189]: # PC
        cfg = {"n": "INFORMATIQUE", "c": (44, 62, 80), "l": ["CPU", "RAM", "STOCKAGE", "ECRAN"]}
    else:
        cfg = {"n": "HARDWARE", "c": (80, 80, 80), "l": ["MARQUE", "PN", "TYPE", "USAGE"]}

    # Rendu PDF simplifié pour la démo
    pdf.set_font("Helvetica", "B", 16); pdf.set_text_color(*cfg["c"])
    pdf.cell(0, 10, clean_txt(prod_name.upper()), ln=True)
    pdf.set_font("Helvetica", "", 10); pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"PN: {ref} | {cfg['n']}", ln=True)
    
    return bytes(pdf.output())

# --- INTERFACE ---
st.set_page_config(page_title="WIKIDATA IT", layout="wide")
st.markdown("<h1 style='text-align: center;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    query = st.text_input("Référence Constructeur (PN)", placeholder="Ex: UA85U8000FUXMV")
with col2:
    st.write("##")
    btn_search = st.button("🔍 Lancer la recherche", use_container_width=True)

if btn_search:
    if query:
        q_upper = query.strip().upper()
        res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", q_upper).execute()
        
        if res.data:
            prod = res.data[0]
            specs = prod['specs_json']
            
            st.success(f"✅ Produit trouvé : {prod['nom_produit']}")
            
            # --- SECTION APERÇU RAPIDE ---
            st.subheader("🔍 Aperçu des caractéristiques")
            cols = st.columns(3)
            with cols[0]:
                st.metric("Marque", prod['marque'])
            with cols[1]:
                st.metric("Référence", prod['ref_constructeur'])
            
            # Affichage des specs en tableau Streamlit
            if "FeaturesGroups" in specs:
                with st.expander("Voir tous les détails techniques", expanded=True):
                    for group in specs["FeaturesGroups"]:
                        st.markdown(f"**{group.get('GroupName', 'Specs')}**")
                        data_tab = []
                        for feat in group.get("Features", []):
                            n = feat.get("Feature", {}).get("Name", {}).get("Value")
                            v = feat.get("PresentationValue")
                            if n and v: data_tab.append({"Caractéristique": n, "Valeur": v})
                        st.table(data_tab)

            # Bouton PDF
            pdf_bytes = generate_pro_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], specs)
            st.download_button("📥 Télécharger la Fiche PDF Complète", pdf_bytes, f"WIKIDATA_{q_upper}.pdf", "application/pdf")
            
        else:
            # Log du besoin client
            supabase.table("besoin_client").insert({"reference_cherchee": q_upper}).execute()
            st.error("❌ Référence inconnue. Le besoin a été enregistré pour indexation.")
    else:
        st.warning("Veuillez entrer un PN.")
