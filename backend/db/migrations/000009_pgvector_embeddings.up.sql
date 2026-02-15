CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE candidates ADD COLUMN embedding_text TEXT;
ALTER TABLE candidates ADD COLUMN embedding vector(768);

ALTER TABLE positions ADD COLUMN embedding_text TEXT;
ALTER TABLE positions ADD COLUMN embedding vector(768);
