import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Funzione per estrarre le proprietà dal vocabolario Schema.org
def fetch_schema_vocabulary(vocabulary_type):
    schema_url = f"https://schema.org/{vocabulary_type}"
    try:
        response = requests.get(schema_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Trova la sezione delle proprietà del vocabolario
        properties_table = soup.find("table", class_="definition-table")
        if not properties_table:
            st.error(f"Nessuna tabella di proprietà trovata per {vocabulary_type}.")
            return None

        properties = {}
        rows = properties_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                property_name = cells[0].get_text(strip=True)
                description = cells[1].get_text(strip=True)
                properties[property_name] = description

        return properties
    except requests.exceptions.RequestException as e:
        st.error(f"Errore durante il recupero del vocabolario: {e}")
        return None

# Funzione per analizzare i dati JSON-LD esistenti
def analyze_existing_json_ld(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text

        # Estrazione dei dati JSON-LD
        soup = BeautifulSoup(html_content, "html.parser")
        scripts = soup.find_all("script", {"type": "application/ld+json"})

        json_ld_data = []
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    json_ld_data.extend(data)
                else:
                    json_ld_data.append(data)
            except json.JSONDecodeError as e:
                st.error(f"Errore durante il parsing del JSON-LD: {e}")

        return json_ld_data
    except requests.exceptions.RequestException as e:
        st.error(f"Errore durante il recupero della pagina: {e}")
        return []

# Streamlit app
st.title("Analizzatore e Generatore di JSON-LD Schema.org")

# Input per l'URL
url = st.text_input("Inserisci l'URL della pagina da analizzare:")

if url and st.button("Analizza JSON-LD"):
    existing_data = analyze_existing_json_ld(url)
    if existing_data:
        st.subheader("Dati JSON-LD trovati:")
        for i, data in enumerate(existing_data, start=1):
            st.json(data)
    else:
        st.warning("Nessun dato JSON-LD trovato nella pagina.")

# Aggiunta di nuovo vocabolario
st.subheader("Aggiungi un nuovo vocabolario Schema.org")
vocabulary_type = st.text_input("Inserisci il tipo di vocabolario (es. 'Product', 'Event', 'Organization'): ")

if vocabulary_type and st.button("Recupera vocabolario"):
    vocabulary = fetch_schema_vocabulary(vocabulary_type)
    if vocabulary:
        st.success(f"Vocabolario '{vocabulary_type}' recuperato con successo!")
        populated_data = {}
        for property_name, description in vocabulary.items():
            value = st.text_input(f"{property_name} ({description}):", key=property_name)
            if value.strip():
                populated_data[property_name] = value

        if st.button("Genera JSON-LD"):
            new_json_ld = {
                "@context": "https://schema.org",
                "@type": vocabulary_type,
                **populated_data,
            }
            st.subheader("Nuovo JSON-LD Generato:")
            
            # Mostra il JSON generato
            json_string = json.dumps(new_json_ld, indent=2, ensure_ascii=False)
            st.code(json_string, language="json", line_numbers=False)

            # Copia negli appunti
            st.success("JSON generato! Usa il pulsante copia sopra per trasferirlo negli appunti.")

            # Link al Validator Schema.org
            st.markdown(
                f"[Controlla il tuo JSON-LD su Schema.org Validator](https://validator.schema.org/)",
                unsafe_allow_html=True,
            )

            # Salva il JSON-LD in un file
            file_name = "json_ld_only.json"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(json_string)
            st.success(f"Il file JSON-LD aggiornato è stato salvato come '{file_name}'.")
