# Stage: Candidate Profile Viewer & Diff (UI Foundation)

## Context

This is the **first hands-on exercise** of the Hellio HR system and the **first concrete capability** of the platform.

HR professionals and interviewers routinely review candidate CVs in inconsistent formats (PDF, Word, email attachments).  
Comparing versions, understanding what changed, and forming a clear picture of a candidate is time-consuming and error-prone.

This stage establishes the **primary user interface** for Hellio HR and sets foundational expectations that all later stages will build on.

### Core Principles
- **Clarity over cleverness**
- **Traceability over automation**
- **Humans in control**

No intelligent automation is introduced at this stage.

---

## Goal

Design and implement a **clean, demo-able web UI** for reviewing and comparing candidate profiles that:

- Presents candidate data in a **uniform, normalized structure**
- Preserves access to **original CV documents**
- Is architected to be **extended later** by intelligent backends and agents

---

## Learning Objectives

By the end of this stage, participants should be able to:

- Design a clean UI for reviewing technical candidate profiles
- Separate normalized candidate data from original source documents
- Build a frontend that anticipates future backend and agent-driven features

This stage also builds familiarity with **agent-assisted development workflows**, including:
- Defining work rules and constraints
- Using sub-agents for scoped tasks
- Preparing the system for future MCP and agent integrations

---

## In Scope

### UI Capabilities
- Candidate profile viewer (structured view)
- Side-by-side comparison of **two candidates**
- Reference links to original CV documents

### Data Handling
- Semi-manual normalization of candidate CVs into JSON
- Semi-manual normalization of job descriptions into JSON
- Hardcoded JSON data (no persistence layer)

---

## Out of Scope

The following are **explicitly excluded** from this stage:

- Automatic CV parsing or extraction
- Databases or persistent storage
- Authentication or authorization
- Any LLM- or agent-powered functionality
- Backend APIs

> This stage is about **using agents to build**, not building AI-powered systems themselves.

---

## Inputs

Provided to participants:

- Mock candidate profiles in PDF / Word format  
  - 2–3 candidates are expected to be semi-manually normalized into JSON
- Job description documents  
  - Expected to be semi-manually normalized into JSON

---

## Expected Outputs

At the end of this stage, the system must be **fully demo-able** and include:

### Candidate Screen
- List of all **Active** candidates
- Search and filter by name and/or position
- Candidate profile displayed in a uniform structure
- Side-by-side comparison of two candidates
- Ability to add or remove positions from a candidate
- Links or previews for original CV documents

### Positions Screen
- List of all **Open** positions
- Display of position descriptions
- List of current candidates associated with each position

---

## Functional Requirements

- Candidate profiles must be displayed using a **consistent schema**
- Original CV documents must remain **accessible and unchanged**
- Comparison views must clearly show similarities and differences
- UI interactions must be deterministic and predictable

---

## Non-Functional Requirements

- UI prioritizes **readability over information density**
- Codebase should be easy to extend to support:
  - Additional profile fields
  - Backend APIs
  - Future agent-generated content
  - A future “contextual chat” on candidate and position screens

---

## Architectural Constraints & Hints

- Treat the **candidate profile as a pure data model**, independent of UI
- Normalize:
  - experience
  - skills
  - education  
  as lists with **stable identifiers**
- Maintain clear sorting rules to enable easy comparison
- Favor explicit structure over inferred meaning

---

## Done When

This stage is considered complete when:

- The UI can be demoed end-to-end without manual explanation
- Candidate data is consistently structured
- Original documents are traceable from the UI
- Two candidates can be compared side by side
- The codebase clearly anticipates future backend and agent extensions
