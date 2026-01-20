# Domain Model

Core entities:
- Candidate
- CVVersion
- Position
- Skill
- Experience
- RecruiterAction

Key invariants:
- A Candidate may have multiple CVVersions
- CVVersions are immutable once ingested
- Search results must always reference a specific CVVersion
