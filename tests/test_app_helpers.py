from types import SimpleNamespace

import app


DEMO_QUESTIONS = [
    "Un produttore iniziale affida rifiuti pericolosi a un trasportatore autorizzato ma non riceve la quarta copia del FIR entro i termini previsti. Quali obblighi, tempistiche e responsabilità si applicano secondo il D.Lgs. 152/2006 e la disciplina RENTRI?",
    "Un impianto riceve un rifiuto con codice EER a specchio e documentazione analitica incompleta. Come deve essere gestita la classificazione del rifiuto, quali criteri HP vanno verificati e quali responsabilità ricadono su produttore, trasportatore e destinatario?",
    "Un'azienda soggetta a RENTRI produce sia rifiuti pericolosi sia non pericolosi da attività diverse, con depositi temporanei in più unità locali. Come devono essere gestiti registro cronologico, FIR, deposito temporaneo e tracciabilità per evitare violazioni?",
]


def obj(**kwargs):
    return SimpleNamespace(**kwargs)


def citation(doc_id, title, url=None, pages=None, source_text=None):
    source_location = obj(url=url) if url is not None else None
    return obj(
        doc_id=doc_id,
        title=title,
        source_location=source_location,
        page_numbers=pages,
        source_text=source_text,
    )


def test_get_field_reads_dict_object_and_default_values():
    assert app.get_field({"name": "dict-value"}, "name") == "dict-value"
    assert app.get_field(obj(name="object-value"), "name") == "object-value"
    assert app.get_field({}, "missing", "fallback") == "fallback"
    assert app.get_field(None, "missing", "fallback") == "fallback"


def test_as_list_normalizes_none_lists_tuples_and_scalars():
    existing = ["already", "list"]

    assert app.as_list(None) == []
    assert app.as_list(existing) is existing
    assert app.as_list(("tuple", "values")) == ["tuple", "values"]
    assert app.as_list("scalar") == ["scalar"]


def test_is_password_valid_requires_matching_configured_hash():
    expected_hash = app.hash_password("password-corretta")

    assert app.is_password_valid("password-corretta", expected_hash) is True
    assert app.is_password_valid("password-sbagliata", expected_hash) is False
    assert app.is_password_valid("password-corretta", "") is False


def test_iter_response_contents_yields_message_tool_content_payload_and_tool_object():
    message_content = obj(text="Messaggio")
    tool_content = obj(text="Contenuto tool")
    tool_payload = {"answer": "Payload tool"}
    tool_output = obj(content=tool_content, output=tool_payload)
    tool_result_payload = {"response": "Payload tool result"}
    tool_result = obj(content=None, output=tool_result_payload)
    chat_result = obj(
        message=obj(content=message_content),
        tool_outputs=[tool_output],
        tool_results={"rag": tool_result},
    )

    assert list(app.iter_response_contents(chat_result)) == [
        message_content,
        tool_content,
        tool_payload,
        tool_output,
        tool_result_payload,
        tool_result,
    ]


def test_preset_questions_include_three_difficult_rag_demo_prompts():
    for question in DEMO_QUESTIONS:
        assert question in app.PRESET_QUESTIONS

    assert len(app.PRESET_QUESTIONS) >= 8


def test_public_app_name_identifies_italian_oci_agents_rag_demo():
    public_text = f"{app.APP_TITLE} {app.APP_DESCRIPTION}"

    assert "OCI Generative AI Agents" in public_text
    assert "RAG" in public_text
    assert "italiano" in public_text.casefold()


def test_extract_response_text_reads_primary_message_content():
    chat_result = obj(message=obj(content=obj(text="Risposta principale")))

    assert app.extract_response_text(chat_result) == "Risposta principale"


def test_extract_response_text_reads_nested_tool_output_text():
    chat_result = obj(
        message=obj(content=obj(text=None)),
        tool_outputs=[
            obj(content=obj(text="Risposta dal tool RAG")),
        ],
    )

    assert app.extract_response_text(chat_result) == "Risposta dal tool RAG"


def test_extract_response_text_reads_generic_tool_output_payload():
    chat_result = obj(
        message=obj(content=obj(text=None)),
        tool_outputs=[
            obj(output={"text": "Risposta dal tool generico"}),
        ],
    )

    assert app.extract_response_text(chat_result) == "Risposta dal tool generico"


def test_extract_response_text_reads_alternate_text_field_names_and_strips():
    for field_name in ("answer", "output", "response"):
        chat_result = obj(message=obj(content={field_name: f"  {field_name} test  "}))

        assert app.extract_response_text(chat_result) == f"{field_name} test"


def test_extract_response_text_ignores_non_string_fields():
    chat_result = obj(
        message=obj(content={"text": ["not", "text"]}),
        tool_outputs=[obj(output={"answer": {"not": "text"}})],
    )

    assert app.extract_response_text(chat_result) == app.EMPTY_RESPONSE_TEXT


def test_extract_response_text_returns_fallback_when_empty():
    chat_result = obj(message=obj(content=obj(text="")))

    assert app.extract_response_text(chat_result) == app.EMPTY_RESPONSE_TEXT


def test_extract_citations_collects_direct_and_paragraph_citations_once():
    direct = citation("doc-1", "Diretto", "https://example.com/direct.pdf", [1])
    duplicate = citation("doc-1", "Diretto", "https://example.com/direct.pdf", [1])
    paragraph = citation("doc-2", "Paragrafo", "https://example.com/paragraph.pdf", [2, 3])
    chat_result = obj(
        message=obj(
            content=obj(
                citations=[direct],
                paragraph_citations=[obj(citations=[duplicate, paragraph])],
            )
        )
    )

    citations = app.extract_citations(chat_result)

    assert citations == [direct, paragraph]


def test_extract_citations_collects_tool_output_citations():
    tool_citation = citation("doc-tool", "Tool", "https://example.com/tool.pdf", [4])
    chat_result = obj(
        message=obj(content=obj(citations=[])),
        tool_outputs=[obj(content=obj(citations=[tool_citation]))],
    )

    assert app.extract_citations(chat_result) == [tool_citation]


def test_extract_citations_collects_generic_tool_output_payload_citations():
    tool_citation = citation("doc-generic", "Generic", "https://example.com/generic.pdf", [5])
    chat_result = obj(
        message=obj(content=obj(citations=[])),
        tool_outputs=[obj(output={"citations": [tool_citation]})],
    )

    assert app.extract_citations(chat_result) == [tool_citation]


def test_extract_citations_collects_tool_results_dict_and_tool_object_citations():
    tool_result_citation = citation("doc-result", "Result", "https://example.com/result.pdf", [6])
    direct_tool_citation = citation("doc-direct", "Direct", "https://example.com/direct.pdf", [7])
    chat_result = obj(
        message=obj(content=obj(citations=[])),
        tool_results={"rag": obj(content=obj(citations=[tool_result_citation]))},
        tool_outputs=[obj(citations=[direct_tool_citation])],
    )

    assert app.extract_citations(chat_result) == [direct_tool_citation, tool_result_citation]


def test_extract_citations_keeps_distinct_page_sets_for_same_document():
    first_page = citation("doc-1", "Documento", "https://example.com/doc.pdf", [1])
    second_page = citation("doc-1", "Documento", "https://example.com/doc.pdf", [2])
    chat_result = obj(message=obj(content=obj(citations=[first_page, second_page])))

    assert app.extract_citations(chat_result) == [first_page, second_page]


def test_citation_identity_handles_missing_source_location_and_pages():
    item = citation("doc-1", "Documento")

    assert app.citation_identity(item) == ("doc-1", "Documento", (), "")


def test_rewrite_source_url_uses_original_when_replacement_missing(monkeypatch):
    monkeypatch.setattr(app, "OS_URL", r"https://objectstorage\.eu-frankfurt-1\.oraclecloud\.com")
    monkeypatch.setattr(app, "OS_URL_PREAUTH", "")

    url = "https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/source.pdf"

    assert app.rewrite_source_url(url) == url


def test_rewrite_source_url_returns_none_for_empty_urls():
    assert app.rewrite_source_url(None) is None
    assert app.rewrite_source_url("") is None


def test_document_match_key_uses_document_title_and_source_url():
    item = citation("doc-1", "Documento", "https://example.com/doc.pdf", [1])

    assert app.document_match_key(item) == (
        "doc-1",
        "Documento",
        "https://example.com/doc.pdf",
    )


def test_format_source_excerpt_normalizes_whitespace_and_respects_boundary():
    assert app.format_source_excerpt("  prima\n\nseconda\tterza  ") == "prima seconda terza"

    exact_length = "x" * app.MAX_SOURCE_EXCERPT_LENGTH
    assert app.format_source_excerpt(exact_length) == exact_length


def test_summarize_document_matches_merges_pages_and_keeps_first_excerpt(monkeypatch):
    monkeypatch.setattr(app, "OS_URL", r"https://objectstorage\.eu-frankfurt-1\.oraclecloud\.com")
    monkeypatch.setattr(app, "OS_URL_PREAUTH", "https://download.example.com")
    first = citation(
        "doc-1",
        "Documento",
        "https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/doc.pdf",
        [3, 1],
        "Primo estratto",
    )
    second = citation(
        "doc-1",
        "Documento",
        "https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/doc.pdf",
        [2, 3],
        "Secondo estratto",
    )

    matches = app.summarize_document_matches([first, second])

    assert matches == [
        {
            "title": "Documento",
            "url": "https://download.example.com/n/doc.pdf",
            "pages": [3, 1, 2],
            "excerpt": "Primo estratto",
        }
    ]


def test_format_citations_returns_none_without_citations():
    assert app.format_citations([]) is None


def test_format_response_citations_suppresses_out_of_scope_answer_citations():
    response_text = (
        "Mi dispiace, ma la sua richiesta non rientra nel mio ambito di competenza, "
        "che è limitato alla legislazione italiana in materia di gestione dei rifiuti "
        "e protezione dell'ambiente."
    )

    formatted = app.format_response_citations(
        response_text,
        [citation("doc-1", "D.Lgs. 152/2006", None, [479], "carbone da vapore")],
    )

    assert formatted is None


def test_format_citations_handles_missing_optional_fields(monkeypatch):
    monkeypatch.setattr(app, "OS_URL", r"https://objectstorage\.eu-frankfurt-1\.oraclecloud\.com")
    monkeypatch.setattr(app, "OS_URL_PREAUTH", "https://download.example.com")
    source = citation(
        "doc-1",
        "Documento",
        "https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/source.pdf",
        None,
    )
    missing_url = citation("doc-2", "Senza URL", None, None)

    formatted = app.format_citations([source, missing_url])

    assert "**[1] Documento**" in formatted
    assert "https://download.example.com/n/source.pdf" in formatted
    assert "**[2] Senza URL**" in formatted


def test_format_citations_highlights_rag_document_matches(monkeypatch):
    monkeypatch.setattr(app, "OS_URL", r"https://objectstorage\.eu-frankfurt-1\.oraclecloud\.com")
    monkeypatch.setattr(app, "OS_URL_PREAUTH", "https://download.example.com")
    first_page = citation(
        "doc-1",
        "D.Lgs. 152/2006",
        "https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/dlgs152.pdf",
        [12],
        "Il produttore conserva una copia del formulario.",
    )
    second_page = citation(
        "doc-1",
        "D.Lgs. 152/2006",
        "https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/dlgs152.pdf",
        [18],
    )
    manual = citation("doc-2", "Manuale RENTRI", None, [4])

    formatted = app.format_citations([first_page, second_page, manual])

    assert "**📚 Match RAG con i documenti**" in formatted
    assert "2 documenti usati nella risposta." in formatted
    assert "**[1] D.Lgs. 152/2006**" in formatted
    assert "Pagine: 12, 18" in formatted
    assert "Estratto rilevante: Il produttore conserva una copia del formulario." in formatted
    assert "[Apri fonte](https://download.example.com/n/dlgs152.pdf)" in formatted
    assert "**[2] Manuale RENTRI**" in formatted
    assert "Sources" not in formatted


def test_format_citations_limits_rag_matches_to_three_documents():
    citations = [
        citation("doc-1", "Documento 1", None, [1]),
        citation("doc-2", "Documento 2", None, [2]),
        citation("doc-3", "Documento 3", None, [3]),
        citation("doc-4", "Documento 4", None, [4]),
    ]

    formatted = app.format_citations(citations)

    assert "**[1] Documento 1**" in formatted
    assert "**[2] Documento 2**" in formatted
    assert "**[3] Documento 3**" in formatted
    assert "Documento 4" not in formatted
    assert "Altri 1 documenti citati non mostrati." in formatted


def test_format_citations_truncates_long_source_text():
    long_text = " ".join(["testo"] * 80)
    formatted = app.format_citations([
        citation("doc-1", "Documento", None, [1], long_text),
    ])

    assert "Estratto rilevante:" in formatted
    assert "..." in formatted


def test_format_citations_uses_fallback_title_for_untitled_documents():
    formatted = app.format_citations([citation("doc-1", "", None, [1])])

    assert "**[1] Documento senza titolo**" in formatted


def test_generate_response_uses_agent_session_chat_and_extractors(monkeypatch):
    returned_citation = citation("doc-1", "Documento", "https://example.com/doc.pdf", [1])

    class FakeClient:
        def create_session(self, create_session_details, agent_endpoint_id):
            self.create_session_details = create_session_details
            self.create_session_agent_endpoint_id = agent_endpoint_id
            return obj(data=obj(id="session-1"))

        def chat(self, agent_endpoint_id, chat_details):
            self.chat_agent_endpoint_id = agent_endpoint_id
            self.chat_details = chat_details
            return obj(
                data=obj(
                    message=obj(
                        content=obj(
                            text="Risposta generata",
                            citations=[returned_citation],
                        )
                    )
                )
            )

    fake_client = FakeClient()
    monkeypatch.setattr(app, "AGENT_ENDPOINT_ID", "endpoint-1")
    monkeypatch.setattr(app, "get_oci_client", lambda: fake_client)

    response_text, citations = app.generate_response("Domanda utente")

    assert response_text == "Risposta generata"
    assert citations == [returned_citation]
    assert fake_client.create_session_agent_endpoint_id == "endpoint-1"
    assert fake_client.create_session_details.display_name == "USER_Session"
    assert fake_client.chat_agent_endpoint_id == "endpoint-1"
    assert fake_client.chat_details.user_message == "Domanda utente"
    assert fake_client.chat_details.session_id == "session-1"


def test_get_oci_client_initializes_once_and_reuses_session_state(monkeypatch):
    class FakeRuntimeClient:
        def __init__(self, config, service_endpoint):
            self.config = config
            self.service_endpoint = service_endpoint

    fake_st = obj(session_state=obj(oci_client=None))
    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app.oci.config, "from_file", lambda: {"profile": "test"})
    monkeypatch.setattr(
        app.oci.generative_ai_agent_runtime,
        "GenerativeAiAgentRuntimeClient",
        FakeRuntimeClient,
    )
    monkeypatch.setattr(app, "SERVICE_ENDPOINT", "https://agent.example.com")

    client = app.get_oci_client()

    assert client.config == {"profile": "test"}
    assert client.service_endpoint == "https://agent.example.com"
    assert fake_st.session_state.oci_client is client
    assert app.get_oci_client() is client


def test_main_reports_missing_agent_endpoint_without_rendering_chat(monkeypatch):
    errors = []
    fake_st = obj(error=errors.append)
    monkeypatch.setattr(app, "AGENT_ENDPOINT_ID", "")
    monkeypatch.setattr(app, "PASSWORD_HASH", "")
    monkeypatch.setattr(app, "st", fake_st)

    app.main()

    assert errors == ["OCI_AGENT_ENDPOINT_ID environment variable is required"]
