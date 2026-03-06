def generate_pdf(prod_name, brand, ref, specs):
    pdf = FPDF()
    pdf.add_page()
    
    # Marges de sécurité
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    w_utile = pdf.w - 2 * pdf.l_margin
    
    # --- LOGO STYLISÉ WIKIDATA ---
    pdf.set_fill_color(30, 136, 229) # Bleu Royal
    pdf.rect(0, 0, 210, 35, 'F') # Bandeau de tête
    
    pdf.set_xy(15, 12)
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(255, 255, 255) # Blanc
    pdf.cell(0, 10, "WIKIDATA IT", ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "LA BASE DE CONNAISSANCES HARDWARE DU MAROC", ln=True)
    pdf.ln(15) # Espace après le bandeau
    
    # --- INFOS PRODUIT ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(w_utile, 10, f"FICHE TECHNIQUE : {prod_name}")
    
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(w_utile, 8, f"MARQUE : {brand} | PN : {ref}", ln=True)
    pdf.ln(5)
    
    # --- CARACTÉRISTIQUES ---
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"][:12]:
            g_name = group.get('GroupName', 'Info').encode('latin-1', 'replace').decode('latin-1')
            
            # Titre de catégorie
            pdf.set_font("Arial", "B", 11)
            pdf.set_fill_color(230, 240, 255)
            pdf.set_text_color(30, 136, 229)
            pdf.cell(w_utile, 8, f" {g_name.upper()} ", ln=True, fill=True)
            
            # Liste des caractéristiques
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(0, 0, 0)
            for feat in group.get("Features", []):
                name = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                val = feat.get("PresentationValue", "")
                
                if name and val:
                    txt = f"{name}: {val}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(w_utile, 6, txt, border='B') # Bordure basse pour l'aspect tableau
            pdf.ln(4)
            
    # Pied de page
    pdf.set_y(-20)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Document généré automatiquement par WIKIDATA IT - wikidata-it.streamlit.app", align='C')
            
    return pdf.output(dest='S')
