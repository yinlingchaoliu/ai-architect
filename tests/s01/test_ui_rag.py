import importlib.util
from io import BytesIO
from pathlib import Path
import sqlite3
import sys

from docx import Document as WordDocument
from PyPDF2 import PdfWriter
from PyPDF2.generic import DictionaryObject, NameObject, DecodedStreamObject
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.language_models.fake_chat_models import FakeListChatModel
import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SmallEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text):
        return [1.0, 0.0] if "alpha" in text else [0.0, 1.0]


def test_pdf_word_text_retrieval_and_legacy_chain(monkeypatch):
    module = load("pdf_search_s01", "webui-chatbot/src/pages/pdf_search.py")
    text = BytesIO(b"alpha source document")
    text.name, text.type = "sample.txt", "text/plain"
    word = WordDocument()
    word.add_paragraph("beta word paragraph")
    uploaded = BytesIO()
    word.save(uploaded)
    uploaded.seek(0)
    uploaded.name = "sample.docx"
    uploaded.type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    pdf = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    page = writer.pages[0]
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"):
        DictionaryObject({NameObject("/F1"): font})})
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 72 720 Td (alpha PDF source) Tj ET")
    page[NameObject("/Contents")] = content
    writer.write(pdf)
    pdf.seek(0)
    pdf.name, pdf.type = "sample.pdf", "application/pdf"
    documents = module.get_pdf_text([text, uploaded, pdf])
    assert any("alpha" in d.page_content for d in documents)
    assert any("beta" in d.page_content for d in documents)
    assert any("alpha PDF source" in d.page_content and d.metadata["source"] == "sample.pdf on page 0" for d in documents)
    chunks = module.get_text_chunks(documents)
    monkeypatch.setattr(module, "OpenAIEmbeddings", SmallEmbeddings)
    store = module.get_vectorstore(chunks)
    monkeypatch.setattr(module, "ChatOpenAI", lambda **kwargs: FakeListChatModel(responses=["retrieved answer"]))
    chain = module.get_conversation_chain(store)
    result = chain.invoke({"question": "alpha", "chat_history": []})
    assert result["answer"] == "retrieved answer"
    assert any(d.metadata["source"] == "sample.txt" for d in result["source_documents"])


def test_web_search_new_imports_and_content(monkeypatch):
    import langchain_openai
    monkeypatch.setattr(langchain_openai, "ChatOpenAI", lambda **kwargs: FakeListChatModel(responses=["web answer"]))
    sys.path.insert(0, str(ROOT / "webui-chatbot/src"))
    module = load("web_search_s01", "webui-chatbot/src/pages/web_search.py")
    assert module.CharacterTextSplitter(chunk_size=30, chunk_overlap=0).split_text("sample") == ["sample"]
    assert module.chat.invoke("sample").text == "web answer"


def test_csv_sql_chain_reads_and_database_rejects_write(monkeypatch, tmp_path):
    module = load("csv_llm_s01", "csv-search/llm.py")
    (tmp_path / "offers.csv").write_text("offer\nalpha\nbeta\n")
    monkeypatch.setattr(module, "ChatOpenAI", lambda **kwargs: FakeListLLM(responses=[
        "SELECT offer FROM offers WHERE offer = 'alpha';", "alpha"]))
    monkeypatch.setattr(module, "OpenAIEmbeddings", lambda **kwargs: SmallEmbeddings())
    client = module.RetrievalLLM(str(tmp_path), ["offers"], str(tmp_path / "offers.sqlite"), "offline")
    assert "alpha" in client.retrieve_offers("Find alpha")
    with pytest.raises(Exception, match="(?i)(readonly|read-only|read only)"):
        client.db.run("DELETE FROM offers")
    assert client.get_embeddings(["alpha", "beta"]).shape == (2, 2)
    client.db._engine.dispose()


def test_public_request_sdk_and_root_entrypoint_import():
    import lib_request
    assert callable(lib_request.OpenAIAssistantClient)
    root = load("root_main_s01", "main.py")
    assert callable(root.search_openai)


def test_request_sdk_uses_configured_model_without_logging_credentials(monkeypatch, caplog):
    import httpx
    import json
    from pydantic import SecretStr
    from lib_llm import LLMRuntime, ModelProfile, ProviderConfig, RuntimeSettings
    from lib_request import OpenAIAssistantClient
    seen = []

    def respond(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"id": "sdk-test", "object": "chat.completion",
            "created": 1, "model": "deepseek-flash", "choices": [{"index": 0,
                "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}]})

    provider = ProviderConfig(base_url="https://api.deepseek.com", kind="deepseek",
                              api_key=SecretStr("s01-offline-test-key"))
    runtime = LLMRuntime(RuntimeSettings(profiles=(ModelProfile(provider=provider, model="deepseek-flash"),)),
                         transport=httpx.MockTransport(respond))
    try:
        client = OpenAIAssistantClient(runtime=runtime)
        client.enableDebug(True)
        assert json.loads(client.request("sample"))["choices"][0]["message"]["content"] == "ok"
        assert seen[0]["model"] == "deepseek-flash"
        assert "s01-offline-test-key" not in caplog.text
    finally:
        runtime.sync_client().close()
