import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Funzione per estrarre l'elenco dei vocabolari Schema.org
def fetch_schema_vocabulary():
    schema_url = "https://schema.org/version/latest/schema.jsonld"
    try:
        response = requests.get(schema_url, timeout=20)
        response.raise_for_status()
        data = response.json()
        types = data.get("@graph", [])
        vocabularies = [item["@id"].replace("schema:", "") for item in types if item.get("@type") == "rdfs:Class"]
        return vocabularies
    except requests.exceptions.RequestException as e:
        st.error(f"Errore durante il recupero del vocabolario: {e}")
        return []

# Funzione per estrarre le proprietà del vocabolario Schema.org
def fetch_schema_properties(vocabulary_type):
    schema_url = f"https://schema.org/{vocabulary_type}"
    try:
        response = requests.get(schema_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
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
        st.error(f"Errore durante il recupero delle proprietà: {e}")
        return None

# Funzione per analizzare i dati JSON-LD esistenti
def analyze_existing_json_ld(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text
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

# Funzione per unire JSON-LD esistenti con un nuovo vocabolario
def merge_json_ld(existing_data, new_json_ld):
    if not existing_data:
        return [new_json_ld]  # Nessun dato esistente, restituisci solo il nuovo
    return existing_data + [new_json_ld]  # Aggiungi il nuovo JSON-LD agli esistenti

# Streamlit app
st.title("JSON-LD Manager with Schema.org Support")

# Input per l'URL
url = st.text_input("Inserisci l'URL della pagina da analizzare:")

# Analisi dei dati JSON-LD esistenti
if url and st.button("Analizza JSON-LD"):
    existing_data = analyze_existing_json_ld(url)
    if existing_data:
        st.subheader("Dati JSON-LD trovati:")
        for i, data in enumerate(existing_data, start=1):
            st.json(data)
    else:
        st.warning("Nessun dato JSON-LD trovato nella pagina.")

# Aggiunta di nuovo vocabolario Schema.org
st.subheader("Aggiungi un nuovo vocabolario Schema.org")

vocabularies = fetch_schema_vocabulary()
if vocabularies:
    vocabulary_type = st.selectbox("Seleziona il tipo di vocabolario Schema.org:", vocabularies)

    if vocabulary_type and st.button("Recupera proprietà"):
        properties = fetch_schema_properties(vocabulary_type)
        if properties:
            st.success(f"Proprietà del vocabolario '{vocabulary_type}' recuperate con successo!")
            populated_data = {}
            for property_name, description in properties.items():
                value = st.text_input(f"{property_name} ({description}):", key=property_name)
                if value.strip():
                    populated_data[property_name] = value

            if st.button("Genera e Unisci JSON-LD"):
                new_json_ld = {
                    "@context": "https://schema.org",
                    "@type": vocabulary_type,
                    **populated_data,
                }
                st.subheader("Nuovo JSON-LD Generato:")
                st.json(new_json_ld)

                # Unisci al JSON-LD esistente
                if url and existing_data:
                    merged_data = merge_json_ld(existing_data, new_json_ld)
                    st.subheader("JSON-LD Unito:")
                    st.json(merged_data)

                    # Salva su file
                    file_name = "merged_json_ld.json"
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write(json.dumps(merged_data, indent=2, ensure_ascii=False))
                    st.success(f"Il file JSON-LD unito è stato salvato come '{file_name}'.")
