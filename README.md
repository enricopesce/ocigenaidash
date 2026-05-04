# GenAI Rifiuti

Applicazione Streamlit che espone un assistente AI specializzato in normativa ambientale italiana, gestione dei rifiuti e tracciabilità RENTRI. L'app usa OCI Generative AI Agents Runtime e mostra, quando disponibili, i riferimenti RAG ai documenti della knowledge base.

## Funzionalità

- Chat interattiva con un agente OCI Generative AI Agents.
- Domande predefinite per scenari su rifiuti, FIR, EER, HP, EPR e RENTRI.
- Visualizzazione compatta dei documenti RAG usati nella risposta, con pagine, estratti e link sorgente.
- Storico conversazione mantenuto nella sessione Streamlit.
- Protezione opzionale con password hash SHA256 per deployment condivisi.
- Riscrittura opzionale degli URL Object Storage verso URL preautenticati.
- Test automatici per estrazione testo, citazioni, formattazione fonti e integrazione base con l'SDK OCI.

## Struttura

```text
genairifiuti/
├── app.py                 # Applicazione Streamlit e helper OCI/RAG
├── kb/                    # PDF usati come knowledge base documentale
├── tests/                 # Test pytest degli helper applicativi
├── .env.example           # Template di configurazione locale
├── requirements.txt       # Dipendenze runtime
├── requirements-dev.txt   # Dipendenze di sviluppo e test
└── README.md
```

## Prerequisiti

- Python 3.12.
- Account Oracle Cloud Infrastructure.
- Agente OCI Generative AI Agents configurato e pubblicato.
- File OCI CLI/API config valido in `~/.oci/config`.

## Installazione

```bash
git clone <repo-url>
cd genairifiuti
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Su Windows, l'attivazione dell'ambiente virtuale è:

```powershell
.venv\Scripts\activate
```

## Configurazione

Copia il template e compila i valori reali:

```bash
cp .env.example .env
```

Variabili supportate:

| Variabile | Obbligatoria | Descrizione |
| --- | --- | --- |
| `OCI_AGENT_ENDPOINT_ID` | Sì | OCID dell'endpoint dell'agente OCI GenAI Agents. |
| `OCI_SERVICE_ENDPOINT` | Sì | Endpoint OCI Agents Runtime, ad esempio `https://agent-runtime.generativeai.eu-frankfurt-1.oci.oraclecloud.com`. |
| `PASSWORD_HASH` | No | Hash SHA256 della password di accesso. Se vuoto, il login Streamlit è disattivato. |
| `OS_URL` | No | Pattern regex dell'URL Object Storage da sostituire nei link delle citazioni. |
| `OS_URL_PREAUTH` | No | URL sostitutivo, tipicamente un pre-authenticated request URL. Se vuoto, i link originali restano invariati. |

Per generare `PASSWORD_HASH`:

```bash
python -c "import hashlib; print(hashlib.sha256('scegli-una-password'.encode()).hexdigest())"
```

Esempio minimale di `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..example
fingerprint=00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00
tenancy=ocid1.tenancy.oc1..example
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key.pem
```

Non committare `.env`, chiavi private o credenziali OCI. Il file `.gitignore` esclude già `.env`, `.venv`, cache Python e log locali.

## Avvio

```bash
streamlit run app.py
```

Poi apri `http://localhost:8501`.

Per usare una porta diversa:

```bash
streamlit run app.py --server.port=8080
```

## Test

```bash
python -m pytest -q
```

I test non chiamano OCI: usano fake client e oggetti leggeri per verificare la logica locale.

## Knowledge Base

La directory `kb/` contiene i PDF normativi usati come base documentale del progetto. Prima di pubblicare o ridistribuire il repository, verifica che ciascun documento possa essere condiviso secondo la relativa licenza o fonte pubblica.

## Note di Sicurezza

- Usa credenziali OCI con privilegi minimi.
- Ruota periodicamente le chiavi API.
- Non pubblicare pre-authenticated request URL se danno accesso a documenti non pubblici.
- Per ambienti condivisi o pubblici, aggiungi un livello di autenticazione davanti all'app Streamlit.

## Licenza

Distribuito con licenza MIT. Vedi `LICENSE`.
