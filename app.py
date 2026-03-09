import streamlit as st
from supabase import create_client
from fpdf import FPDF

# TES params Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def clean_ascii(text):
    """FORCE ASCII pur - ZÉRO erreur Helvetica"""
    if not text: return "NC"
    # Garde SEULEMENT lettres, chiffres, espaces, points, tirets
    ascii_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz 0123456789.,-():"
    return ''.join([c for c in str(text) if c in ascii_chars])[:80] or "NC"

class SimplePDF(FPDF):
    pass  # Pas d'header fancy

def generate_pro_pdf(prod_name, brand, ref, specs):
    pdf = SimplePDF()
    pdf.add_page()
    
    # Couleur simple
    pdf.set_fill_color(0, 100, 200)
    pdf.rect(10, 10, 190, 30, 'F')
    
    # TITRE (ASCII garanti)
    pdf.set_xy(20, 20)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(170, 10, clean_ascii(prod_name), 0, 1, 'C')
    
    pdf.set_xy(20, 35)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(170, 8, f"{clean_ascii(brand)} - {ref}", 0, 1, 'C')
    
    # CARACTÉRISTIQUES
    pdf.set_xy(15, 55)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 100, 200)
    pdf.cell(0, 10, "SPECIFICATIONS PRINCIPALES", 0, 1)
    
    pdf.set_font("Helvetica", "", 11)
    y_pos = 70
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"][:3]:
            gname = clean_ascii(group.get("GroupName", "Specs"))
            if gname != "NC":
                pdf.set_xy(15, y_pos)
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 6, gname, 0, 1)
                y_pos += 8
                
                for feat in group.get("Features", [])[:6]:
                    n = clean_ascii(feat.get("Feature", {}).get("Name", {}).get("Value", ""))
                    v = clean_ascii(feat.get("PresentationValue", ""))
                    if n != "NC" and v != "NC":
                        pdf.set_xy(20, y_pos)
                        pdf.set_font("Helvetica", "", 10)
                        line = f"{n}: {v}"
                        pdf.cell(175, 5, line, 0, 1)
                        y_pos += 6
                        if y_pos > 250: break
    
    # TABLEAU SIMPLE
    pdf.set_xy(15, max(y_pos, 140))
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 100, 200)
    pdf.cell(0, 8, "TABLEAU TECHNIQUE", 0, 1)
    
    # Lignes tableau
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(80, 6, "Parametre", 1)
    pdf.cell(95, 6, "Valeur", 1, 1)
    
    pdf.set_font("Helvetica", "", 9)
    specs_list = []
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            for feat in group.get("Features", [])[:12]:
                n = clean_ascii(feat.get("Feature", {}).get("Name", {}).get("Value", ""))
                v = clean_ascii(feat.get("PresentationValue", ""))
                if n != "NC" and v != "NC":
                    specs_list.append((n, v))
                    if len(specs_list) >= 15: break
    
    for n, v in specs_list:
        pdf.cell(80, 5, n, 1)
        pdf.cell(95, 5, v, 1, 1)
    
    # FOOTER
    pdf.set_xy(15, 280)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Generate par WIKIDATA IT - {brand} {ref} - Electroplanet Maroc", 0, 1, 'C')
    
    return bytes(pdf.output(dest="S"))

# TON INTERFACE EXACTE
st.set_page_config(page_title="WIKIDATA IT", layout="wide")
st.markdown("<h1 style='text-align: center;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    query = st.text_input("Reference Constructeur (PN)", placeholder="Ex: UA85U8000FUXMV")
with col2:
    st.write("##")
    btn_search = st.button("🔍 Lancer la recherche", use_container_width=True)

if btn_search:
    if query:
        try:
            q_upper = query.strip().upper()
            res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", q_upper).execute()
            
            if res.data:
                prod = res.data[0]
                specs = prod['specs_json']
                
                st.success(f"✅ Produit trouve : {prod['nom_produit']}")
                
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Marque", prod['marque'])
                with cols[1]:
                    st.metric("Reference", prod['ref_constructeur'])
                
                if "FeaturesGroups" in specs:
                    with st.expander("Voir tous les details techniques", expanded=True):
                        for group in specs["FeaturesGroups"]:
                            st.markdown(f"**{group.get('GroupName', 'Specs')}**")
                            data_tab = []
                            for feat in group.get("Features", []):
                                n = feat.get("Feature", {}).get("Name", {}).get("Value")
                                v = feat.get("PresentationValue")
                                if n and v: 
                                    data_tab.append({"Caracteristique": n, "Valeur": v})
                            st.table(data_tab)

                # PDF SANS ERREUR
                pdf_bytes = generate_pro_pdf(prod['nom_produit'], prod['marque'], prod['ref_constructeur'], specs)
                st.download_button("📥 Telecharger la Fiche PDF Complete", pdf_bytes, f"WIKIDATA_{q_upper}.pdf", "application/pdf")
                
            else:
                supabase.table("besoin_client").insert({"reference_cherchee": q_upper}).execute()
                st.error("❌ Reference inconnue. Le besoin a ete enregistre.")
                
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
            st.info("Secrets.toml OK ?")
    else:
        st.warning("Veuillez entrer un PN.")
