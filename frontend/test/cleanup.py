import sys
import uuid
import os
import logging
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

try:
    from app.models import Document, Candidate, CandidateProfile, CandidatePosition
    from app.config import settings
    logger.info("Successfully imported backend modules")
except ImportError as e:
    logger.error(f"Failed to import backend modules: {e}")
    sys.exit(1)

def cleanup(document_id_str, candidate_id_str=None):
    logger.info(f"Starting cleanup for doc_id: {document_id_str}, candidate_id: {candidate_id_str}")
    engine = create_engine(settings.database_url)
    
    with Session(engine) as session:
        try:
            # If doc_id is provided, try to find the associated candidate_id if not provided
            doc_id = None
            cand_id = None

            if document_id_str and document_id_str.strip():
                doc_id = uuid.UUID(document_id_str)
            
            if candidate_id_str and candidate_id_str.strip():
                cand_id = uuid.UUID(candidate_id_str)

            if doc_id and not cand_id:
                doc = session.get(Document, doc_id)
                if doc and doc.candidate_id:
                    cand_id = doc.candidate_id
                    logger.info(f"Found associated candidate_id: {cand_id} from document: {doc_id}")

            if doc_id:
                storage_path = Path(settings.cv_storage_path)
                file_path = storage_path / str(doc_id)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted file: {file_path}")

                session.execute(delete(Document).where(Document.id == doc_id))
                logger.info(f"Deleted document from DB: {doc_id}")

            if cand_id:
                session.execute(delete(CandidateProfile).where(CandidateProfile.candidate_id == cand_id))
                session.execute(delete(CandidatePosition).where(CandidatePosition.candidate_id == cand_id))
                session.execute(delete(Candidate).where(Candidate.id == cand_id))
                logger.info(f"Deleted candidate from DB: {cand_id}")
            
            session.commit()
            logger.info("Cleanup committed successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Error during cleanup: {e}")
            raise

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python3 cleanup.py <doc_id> [candidate_id]")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    cand_id = sys.argv[2] if len(sys.argv) > 2 else None
    cleanup(doc_id, cand_id)
