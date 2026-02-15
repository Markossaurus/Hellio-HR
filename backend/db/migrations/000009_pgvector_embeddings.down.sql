ALTER TABLE candidates DROP COLUMN IF EXISTS embedding;
ALTER TABLE candidates DROP COLUMN IF EXISTS embedding_text;

ALTER TABLE positions DROP COLUMN IF EXISTS embedding;
ALTER TABLE positions DROP COLUMN IF EXISTS embedding_text;
