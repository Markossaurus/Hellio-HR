from app.models import Document, DocumentText, DocumentExtraction, DocumentSummary

def test_document_models_importable():
    assert Document is not None
    assert DocumentText is not None
    assert DocumentExtraction is not None
    assert DocumentSummary is not None
