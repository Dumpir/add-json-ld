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
            logging.error(f"Nessuna tabella di proprietà trovata per {vocabulary_type}.")
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
        logging.error(f"Errore durante il recupero del vocabolario: {e}")
        return None

# Funzione per popolare un vocabolario Schema.org
def populate_vocabulary(vocabulary):
    populated_data = {}
    for property_name, description in vocabulary.items():
        user_input = input(f"Aggiungi il valore per '{property_name}' ({description}): ")
        if user_input.strip():  # Skippa i campi non popolati
            populated_data[property_name] = user_input
    return populated_data

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
                logging.error(f"Errore durante il parsing del JSON-LD: {e}")

        return json_ld_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante il recupero della pagina: {e}")
        return []

# Funzione principale
def main():
    # Chiedi l'URL della pagina da analizzare
    url = input("Inserisci l'URL della pagina da analizzare: ")

    # Analizza i dati JSON-LD esistenti
    existing_data = analyze_existing_json_ld(url)
    if not existing_data:
        print("Nessun dato JSON-LD trovato nella pagina.")
        existing_data = []

    print("\nDati JSON-LD esistenti:")
    for i, data in enumerate(existing_data, start=1):
        print(f"\nMarkup #{i}:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

    # Chiedi se l'utente vuole aggiungere un nuovo vocabolario
    add_vocabulary = input("\nVuoi aggiungere un nuovo vocabolario Schema.org? (sì/no): ")

    if add_vocabulary.strip().lower() in ['sì', 'si', 'yes', 'y']:
        # Chiedi il tipo di vocabolario da aggiungere
        vocabulary_type = input("\nInserisci il tipo di vocabolario Schema.org da aggiungere (es. 'Product', 'Event', 'Organization'): ")

        # Recupera il vocabolario Schema.org
        vocabulary = fetch_schema_vocabulary(vocabulary_type)
        if not vocabulary:
            print(f"Impossibile recuperare il vocabolario per '{vocabulary_type}'.")
            integrated_data = existing_data  # Continua con i dati esistenti
        else:
            # Popola il vocabolario
            print(f"\nPopolazione del vocabolario '{vocabulary_type}':")
            populated_data = populate_vocabulary(vocabulary)

            # Crea il nuovo JSON-LD
            new_json_ld = {
                "@context": "https://schema.org",
                "@type": vocabulary_type,
                **populated_data
            }

            # Integra il nuovo JSON-LD nei dati esistenti
            integrated_data = existing_data + [new_json_ld] if populated_data else existing_data
    else:
        # Non aggiungere nuovo vocabolario
        integrated_data = existing_data

    # Salva il JSON-LD in un file
    file_name = "json_ld_only.json"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(json.dumps(integrated_data, indent=2, ensure_ascii=False))

    print(f"\nIl file JSON-LD aggiornato è stato salvato come '{file_name}'.")

if __name__ == "__main__":
    main()
