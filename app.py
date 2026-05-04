"""Italian Streamlit RAG demo backed by OCI Generative AI Agents Runtime."""

import hashlib
import os
import re

from dotenv import load_dotenv
import oci
import streamlit as st

# Load local configuration for development; production can provide real env vars.
load_dotenv()

APP_TITLE = "OCI Generative AI Agents RAG Demo - Italiano"
APP_DESCRIPTION = (
    "Demo Streamlit in italiano per interrogare una knowledge base normativa "
    "con OCI Generative AI Agents e RAG."
)

SERVICE_ENDPOINT = os.getenv("OCI_SERVICE_ENDPOINT", "")
AGENT_ENDPOINT_ID = os.getenv("OCI_AGENT_ENDPOINT_ID", "")
PASSWORD_HASH = os.getenv("PASSWORD_HASH", "")
OS_URL = os.getenv("OS_URL", r"https://objectstorage\.eu-frankfurt-1\.oraclecloud\.com")
OS_URL_PREAUTH = os.getenv("OS_URL_PREAUTH", "")

EMPTY_RESPONSE_TEXT = "Nessun testo di risposta restituito dall'agente."
MAX_RAG_MATCHES_DISPLAYED = 3
MAX_SOURCE_EXCERPT_LENGTH = 220
OUT_OF_SCOPE_RESPONSE_MARKERS = (
    "non rientra nel mio ambito",
    "non è pertinente alle norme e ai regolamenti ambientali",
    "la sua richiesta non è pertinente",
)

st.set_page_config(page_title=APP_TITLE, layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False
if "oci_client" not in st.session_state:
    st.session_state.oci_client = None

PRESET_QUESTIONS = [
    "Come si applica il principio della responsabilità estesa del produttore (EPR) nei settori degli imballaggi e dei RAEE?",
    "Quali sono i limiti di concentrazione per definire pericoloso un rifiuto contenente metalli pesanti e come si applicano i criteri HP?",
    "Un'azienda produce scarti di lavorazione metallica contaminati da oli. Quale procedura deve seguire per la classificazione e quali codici EER potrebbero applicarsi?",
    "Quali sono gli obblighi del produttore di rifiuti pericolosi che supera le 10 tonnellate annue secondo il SISTRI e le modifiche successive?",
    "Un laboratorio chimico deve smaltire reagenti scaduti di varia natura. Quali procedure deve seguire per il confezionamento, l'etichettatura e l'affidamento a trasportatori autorizzati?",
    "Un produttore iniziale affida rifiuti pericolosi a un trasportatore autorizzato ma non riceve la quarta copia del FIR entro i termini previsti. Quali obblighi, tempistiche e responsabilità si applicano secondo il D.Lgs. 152/2006 e la disciplina RENTRI?",
    "Un impianto riceve un rifiuto con codice EER a specchio e documentazione analitica incompleta. Come deve essere gestita la classificazione del rifiuto, quali criteri HP vanno verificati e quali responsabilità ricadono su produttore, trasportatore e destinatario?",
    "Un'azienda soggetta a RENTRI produce sia rifiuti pericolosi sia non pericolosi da attività diverse, con depositi temporanei in più unità locali. Come devono essere gestiti registro cronologico, FIR, deposito temporaneo e tracciabilità per evitare violazioni?",
]


def get_field(value, field_name, default=None):
    """Read an OCI SDK model, dict, or lightweight test object field."""
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def as_list(value):
    """Normalize optional OCI SDK fields to a list for uniform processing."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def hash_password(password):
    """Return the SHA256 hex digest used by the optional Streamlit login."""
    return hashlib.sha256(password.encode()).hexdigest()


def is_password_valid(password, expected_hash):
    """Validate a plain-text password against a configured SHA256 hash."""
    return bool(expected_hash) and hash_password(password) == expected_hash


def check_password():
    """Require a password only when PASSWORD_HASH is configured."""
    if not PASSWORD_HASH:
        return True

    def password_entered():
        st.session_state.password_correct = is_password_valid(
            st.session_state["password"],
            PASSWORD_HASH,
        )
        if st.session_state.password_correct:
            del st.session_state["password"]
            st.session_state.password_error = False
        else:
            st.session_state.password_error = True

    if st.session_state.password_correct:
        if st.sidebar.button("Logout"):
            st.session_state.password_correct = False
            st.session_state.messages = []
            st.session_state.oci_client = None
            st.rerun()
        return True

    st.title("Accesso richiesto")
    st.text_input(
        "Password",
        type="password",
        on_change=password_entered,
        key="password",
    )
    if st.session_state.get("password_error"):
        st.error("Password errata. Riprova.")
    return False


def get_oci_client():
    """Initialize and cache the OCI Agents Runtime client in Streamlit state."""
    if st.session_state.oci_client is None:
        try:
            config = oci.config.from_file()
            st.session_state.oci_client = oci.generative_ai_agent_runtime.GenerativeAiAgentRuntimeClient(
                config, service_endpoint=SERVICE_ENDPOINT
            )
        except Exception as e:
            st.error(f"Failed to initialize OCI client: {e}")
            st.stop()
    return st.session_state.oci_client


def iter_response_contents(chat_result):
    """Yield message and tool output content objects from Agent Runtime responses."""
    message = get_field(chat_result, "message")
    content = get_field(message, "content")
    if content is not None:
        yield content

    for field_name in ("tool_outputs", "tool_results"):
        tool_values = get_field(chat_result, field_name)
        if isinstance(tool_values, dict):
            tool_iterable = tool_values.values()
        else:
            tool_iterable = as_list(tool_values)

        for tool_output in tool_iterable:
            tool_content = get_field(tool_output, "content")
            if tool_content is not None:
                yield tool_content

            output_payload = get_field(tool_output, "output")
            if output_payload is not None:
                yield output_payload

            yield tool_output


def extract_response_text(chat_result):
    """Return the first non-empty text payload exposed by the agent response."""
    for content in iter_response_contents(chat_result):
        for field_name in ("text", "answer", "output", "response"):
            text = get_field(content, field_name)
            if isinstance(text, str) and text.strip():
                return text.strip()
    return EMPTY_RESPONSE_TEXT


def generate_response(user_message):
    """Send a user message to the configured OCI GenAI Agent endpoint."""
    client = get_oci_client()

    session_response = client.create_session(
        create_session_details=oci.generative_ai_agent_runtime.models.CreateSessionDetails(
            display_name="USER_Session",
            description="User Session",
        ),
        agent_endpoint_id=AGENT_ENDPOINT_ID,
    )

    chat_response = client.chat(
        agent_endpoint_id=AGENT_ENDPOINT_ID,
        chat_details=oci.generative_ai_agent_runtime.models.ChatDetails(
            user_message=user_message,
            session_id=session_response.data.id,
        ),
    )

    response_text = extract_response_text(chat_response.data)
    citations = extract_citations(chat_response.data)

    return response_text, citations


def citation_identity(citation):
    """Build a stable key for de-duplicating raw citation objects."""
    source_location = get_field(citation, "source_location")
    return (
        get_field(citation, "doc_id", ""),
        get_field(citation, "title", ""),
        tuple(as_list(get_field(citation, "page_numbers"))),
        get_field(source_location, "url", ""),
    )


def extract_citations(chat_result):
    """Extract and de-duplicate citations from Agent Runtime content."""
    all_citations = []

    for content in iter_response_contents(chat_result):
        all_citations.extend(as_list(get_field(content, "citations")))

        for para_group in as_list(get_field(content, "paragraph_citations")):
            all_citations.extend(as_list(get_field(para_group, "citations")))

    unique_citations = []
    seen = set()
    for citation in all_citations:
        key = citation_identity(citation)
        if key not in seen:
            unique_citations.append(citation)
            seen.add(key)
    
    return unique_citations


def rewrite_source_url(original_url):
    """Replace OCI Object Storage URLs with optional pre-authenticated URLs."""
    if not original_url:
        return None
    if not OS_URL_PREAUTH:
        return original_url
    return re.sub(OS_URL, OS_URL_PREAUTH, original_url)


def document_match_key(citation):
    """Group citations that refer to the same source document."""
    source_location = get_field(citation, "source_location")
    return (
        get_field(citation, "doc_id", ""),
        get_field(citation, "title", ""),
        get_field(source_location, "url", ""),
    )


def format_source_excerpt(source_text):
    """Create a short, single-line source excerpt for the Streamlit expander."""
    if not source_text:
        return None

    excerpt = " ".join(str(source_text).split())
    if len(excerpt) <= MAX_SOURCE_EXCERPT_LENGTH:
        return excerpt
    return f"{excerpt[:MAX_SOURCE_EXCERPT_LENGTH].rstrip()}..."


def summarize_document_matches(citations):
    """Collapse page-level citations into one display item per source document."""
    matches = []
    match_index = {}

    for citation in citations:
        key = document_match_key(citation)
        if key not in match_index:
            source_location = get_field(citation, "source_location")
            match_index[key] = {
                "title": get_field(citation, "title") or "Documento senza titolo",
                "url": rewrite_source_url(get_field(source_location, "url")),
                "pages": [],
                "excerpt": None,
            }
            matches.append(match_index[key])

        for page in as_list(get_field(citation, "page_numbers")):
            if page not in match_index[key]["pages"]:
                match_index[key]["pages"].append(page)

        if match_index[key]["excerpt"] is None:
            match_index[key]["excerpt"] = format_source_excerpt(
                get_field(citation, "source_text")
            )

    return matches


def format_citations(citations):
    """Format citations as a compact RAG document match summary."""
    if not citations:
        return None

    matches = summarize_document_matches(citations)
    citation_text = "**📚 Match RAG con i documenti**\n\n"
    citation_text += f"{len(matches)} documenti usati nella risposta.\n\n"

    for i, match in enumerate(matches[:MAX_RAG_MATCHES_DISPLAYED], 1):
        citation_text += f"**[{i}] {match['title']}**\n"

        if match["pages"]:
            pages = ", ".join(map(str, sorted(match["pages"])))
            citation_text += f"   📄 Pagine: {pages}\n"

        if match["excerpt"]:
            citation_text += f"   Estratto rilevante: {match['excerpt']}\n"

        if match["url"]:
            citation_text += f"   🔗 [Apri fonte]({match['url']})\n"

        citation_text += "\n"

    hidden_count = len(matches) - MAX_RAG_MATCHES_DISPLAYED
    if hidden_count > 0:
        citation_text += f"_Altri {hidden_count} documenti citati non mostrati._\n"
    
    return citation_text


def is_out_of_scope_response(response_text):
    """Detect agent refusals so unrelated RAG matches are not shown as sources."""
    if not response_text:
        return False

    normalized_response = " ".join(str(response_text).casefold().split())
    return any(marker in normalized_response for marker in OUT_OF_SCOPE_RESPONSE_MARKERS)


def format_response_citations(response_text, citations):
    """Format citations only when they support an in-scope answer."""
    if is_out_of_scope_response(response_text):
        return None
    return format_citations(citations)


def main():
    """Render the Streamlit chat UI."""
    if not check_password():
        return

    if not AGENT_ENDPOINT_ID:
        st.error("OCI_AGENT_ENDPOINT_ID environment variable is required")
        return

    st.title(APP_TITLE)
    st.write(APP_DESCRIPTION)

    with st.sidebar:
        st.header("🎯 Domande Rapide")

        for i, question in enumerate(PRESET_QUESTIONS):
            if st.button(question[:60] + "...", key=f"preset_{i}", help=question):
                st.session_state.messages.append({"role": "user", "content": question})

                with st.spinner("Generando risposta..."):
                    try:
                        response_text, citations = generate_response(question)
                        formatted_citations = format_response_citations(
                            response_text, citations
                        )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": response_text,
                                "citations": formatted_citations,
                            }
                        )
                    except Exception as e:
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": f"Errore: {e}",
                                "citations": None,
                            }
                        )

                st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

            if message["role"] == "assistant" and message.get("citations"):
                with st.expander("📚 Match RAG con i documenti"):
                    st.markdown(message["citations"])

    if prompt := st.chat_input("Come posso aiutarti?"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Generando risposta..."):
                try:
                    response_text, citations = generate_response(prompt)
                    st.write(response_text)

                    formatted_citations = format_response_citations(
                        response_text, citations
                    )
                    if formatted_citations:
                        with st.expander("📚 Match RAG con i documenti"):
                            st.markdown(formatted_citations)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response_text,
                            "citations": formatted_citations,
                        }
                    )

                except Exception as e:
                    error_msg = f"Errore: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_msg,
                            "citations": None,
                        }
                    )


if __name__ == "__main__":
    main()
