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


def test_preset_questions_include_three_difficult_rag_demo_prompts():
    for question in DEMO_QUESTIONS:
        assert question in app.PRESET_QUESTIONS

    assert len(app.PRESET_QUESTIONS) >= 8


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


def test_rewrite_source_url_uses_original_when_replacement_missing(monkeypatch):
    monkeypatch.setattr(app, "OS_URL", r"https://objectstorage\.eu-frankfurt-1\.oraclecloud\.com")
    monkeypatch.setattr(app, "OS_URL_PREAUTH", "")

    url = "https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/source.pdf"

    assert app.rewrite_source_url(url) == url


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
