# OCI Generative AI Agents RAG Demo - Italiano

Demo Streamlit in italiano che mostra come usare **OCI Generative AI Agents** con un flusso **RAG** per rispondere a domande su normativa ambientale, gestione dei rifiuti e tracciabilita RENTRI.

Il progetto non e un prodotto finito: e una base didattica e dimostrativa per collegare una UI Python leggera a un Agent endpoint OCI, leggere la risposta dell'agente e mostrare i riferimenti documentali restituiti dalla knowledge base.

## Cosa Dimostra

- Integrazione con **OCI Generative AI Agents Runtime** tramite SDK Python OCI.
- Chat Streamlit in italiano con domande predefinite su rifiuti, EER, FIR, HP, EPR e RENTRI.
- Recupero e normalizzazione di risposte generate dall'agente, inclusi payload di tool e output RAG.
- Visualizzazione compatta delle fonti RAG: documenti, pagine, estratti e link.
- Riscrittura opzionale dei link Object Storage verso URL preautenticati.
- Protezione opzionale con password hash SHA256 per demo condivise.
- Test locali senza chiamate reali a OCI, basati su fake client e oggetti leggeri.

## Architettura

```text
Browser
  |
  v
Streamlit app.py
  |
  v
OCI Generative AI Agents Runtime
  |
  v
Agent + knowledge base RAG su documenti normativi
```

La cartella `kb/` contiene PDF normativi usati come materiale documentale della demo. L'app non indicizza direttamente i file locali a runtime: interroga l'Agent endpoint OCI gia configurato con la propria knowledge base.

## Struttura Repository

```text
oci-generative-ai-agents-rag-demo-it/
├── app.py                 # UI Streamlit, chiamate OCI e formattazione RAG
├── kb/                    # Documenti normativi usati per la knowledge base
├── tests/                 # Test pytest degli helper applicativi
├── .env.example           # Template delle variabili locali
├── requirements.txt       # Dipendenze runtime
├── requirements-dev.txt   # Dipendenze test/sviluppo
├── LICENSE
└── README.md
```

## Prerequisiti

- Python 3.12.
- Account Oracle Cloud Infrastructure.
- OCI Generative AI Agent creato, configurato e pubblicato.
- Agent endpoint ID disponibile.
- Knowledge base RAG collegata all'agente.
- File OCI config valido in `~/.oci/config`.

## Installazione

```bash
git clone https://github.com/enricopesce/oci-generative-ai-agents-rag-demo-it.git
cd oci-generative-ai-agents-rag-demo-it
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Su Windows:

```powershell
.venv\Scripts\activate
```

## Configurazione

Copia il template:

```bash
cp .env.example .env
```

Compila almeno:

```env
OCI_AGENT_ENDPOINT_ID=ocid1.genaiagentendpoint.oc1.eu-frankfurt-1...
OCI_SERVICE_ENDPOINT=https://agent-runtime.generativeai.eu-frankfurt-1.oci.oraclecloud.com
```

Variabili disponibili:

| Variabile | Obbligatoria | Descrizione |
| --- | --- | --- |
| `OCI_AGENT_ENDPOINT_ID` | Si | OCID dell'endpoint OCI Generative AI Agent. |
| `OCI_SERVICE_ENDPOINT` | Si | Endpoint OCI Agents Runtime della region scelta. |
| `PASSWORD_HASH` | No | Hash SHA256 della password di accesso alla demo. Se vuoto, il login e disattivato. |
| `OS_URL` | No | Pattern regex dell'URL Object Storage da sostituire nei link delle citazioni. |
| `OS_URL_PREAUTH` | No | URL sostitutivo, ad esempio un pre-authenticated request URL. Se vuoto, i link originali restano invariati. |

Per generare un hash password:

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

## Avvio

```bash
streamlit run app.py
```

Apri:

```text
http://localhost:8501
```

Porta alternativa:

```bash
streamlit run app.py --server.port=8080
```

## Test

```bash
python -m pytest -q
```

I test non chiamano OCI. Verificano helper, parsing delle risposte Agent Runtime, deduplica citazioni, formattazione fonti RAG, password opzionale e comportamento base dell'app.

## Note sulla Demo RAG

Questa demo assume che il lavoro RAG principale sia configurato lato OCI:

- documenti caricati o indicizzati nella knowledge base dell'agente;
- tool RAG collegato all'agent;
- endpoint agente pubblicato;
- permessi OCI corretti per l'utente/API key usata localmente.

`app.py` si occupa della parte applicativa: invia la domanda, legge la risposta, cerca testo e citazioni nei possibili payload dell'SDK e mostra all'utente i match documentali piu utili.

## Sicurezza

- Non committare `.env`, chiavi private OCI o URL preautenticati sensibili.
- Usa policy OCI con privilegi minimi.
- Imposta `PASSWORD_HASH` se la demo e esposta fuori dal tuo ambiente locale.
- Verifica i diritti di redistribuzione dei PDF in `kb/` prima di pubblicare o riusare il repository in altri contesti.

## Limiti Noti

- L'app non crea ne configura l'agente OCI: devi prepararlo prima in OCI.
- La qualita delle risposte dipende da knowledge base, prompt, modello e configurazione dell'Agent.
- La password opzionale e adatta a una demo leggera, non sostituisce un sistema di autenticazione enterprise.
- Le risposte su temi normativi vanno verificate sulle fonti ufficiali.

## Licenza

Distribuito con licenza MIT. Vedi `LICENSE`.
