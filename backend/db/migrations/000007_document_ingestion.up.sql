CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,
    content_type VARCHAR(20) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    candidate_id UUID REFERENCES candidates(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_documents_content_hash ON documents(content_hash);
CREATE INDEX idx_documents_candidate_id ON documents(candidate_id);

CREATE TABLE document_texts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    extracted_text TEXT NOT NULL,
    parser_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    heuristic_json JSONB NOT NULL,
    llm_raw_output TEXT NOT NULL,
    extracted_json_validated JSONB,
    extraction_schema_version VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_details JSONB,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    token_estimate_in INTEGER,
    token_estimate_out INTEGER,
    cost_estimate_usd NUMERIC(10, 6),
    elapsed_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE document_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    token_estimate_in INTEGER,
    token_estimate_out INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);
