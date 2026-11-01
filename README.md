# umde-hackathon
# UMDE

**Turning CMS regulatory documents into traceable validation rules for Medicare Advantage data.**

UMDE is an early-stage healthcare data validation platform designed to catch CMS submission errors before data is submitted.

The core idea is simple: many CMS validation requirements are published in PDFs and spreadsheets. Health plans and implementation teams must interpret those documents and repeatedly translate the same regulatory logic into software.

UMDE explores a different workflow:

**CMS source document → structured rule → human review → executable validator → data validation**

> **Status:** Early prototype, built for the [World's Largest Hackathon presented by Bolt](https://devpost.com/software/umde-smarter-cms-rule-validation) (mid-2025). The rule pipeline and validation engine run end to end; the LLM extraction layer is not yet reliable. See [Known issues](#known-issues).

---

## Origin

UMDE began as an exploration of a problem I encountered while working on U.S. Medicare Advantage data-submission systems: regulatory validation requirements are repeatedly interpreted and reimplemented from human-readable CMS documentation.

This repository is the first working prototype of a system intended to turn that process into a traceable regulatory-rule lifecycle.

---

## Why UMDE

Medicare Advantage data submission depends on large sets of technical and regulatory validation rules distributed across CMS documentation.

Today, implementing those rules typically requires teams to:

1. read regulatory documents,
2. identify applicable requirements,
3. interpret them,
4. translate them into software,
5. test the implementation, and
6. repeat the process when CMS guidance changes.

That creates duplicated work and makes traceability between a validation rule and its regulatory source difficult.

Rather than every organization independently interpreting and implementing the same CMS validation requirements, UMDE aims to make those requirements reusable, testable, and traceable.

---

## What the prototype does

The current prototype supports two connected workflows.

### 1. Regulatory rule extraction

UMDE can ingest CMS PDF and Excel source material and process candidate validation rules.

Extraction runs a sequence of LLMs (Zephyr-7B, DeepSeek, a local model via Ollama, and FLAN-T5), keeping the first result that clears its confidence threshold, with a deterministic keyword-based fallback.

The pipeline can:

- parse PDF and XLSX regulatory sources;
- identify candidate rule chunks;
- extract structured rule metadata;
- classify rules into validation layers;
- preserve the originating document and source page;
- record extraction provenance and confidence;
- identify rules requiring manual review;
- generate versioned rule artifacts; and
- generate executable Python validators for simpler rules.

More complex rules remain human-implemented rather than being automatically converted into executable logic.

### 2. Member-data validation

Approved rules can be loaded dynamically by the validation engine and executed against member-data files.

The current API supports:

- CSV
- compressed CSV (`.csv.gz`)
- JSON

Validation output can include:

- rule ID;
- row-level validation errors;
- severity;
- validation layer;
- source-document reference;
- rule tags; and
- execution timing for debugging and benchmarking.

A validation result identifies the affected record and the specific rule that failed, rather than returning only a generic file-level error.

---

## Prototype workflow

```text
CMS PDF / XLSX
       |
       v
Document Parser
       |
       v
Candidate Rule Extraction
       |
       v
Structured Rule + Source Provenance
       |
       v
Rule Classification
   L1 / L2 / L3 / L4
       |
       v
Human Review
       |
       +----------------------+
       |                      |
       v                      v
L1/L2 Code Generation    L3/L4 Manual Stub
       |                      |
       +----------+-----------+
                  |
                  v
             Rule Registry
                  |
                  v
          Validation Engine
                  |
                  v
       CSV / JSON Member Data
                  |
                  v
       Validation Results
```

---

## Human-in-the-loop by design

UMDE does not assume that every regulatory statement should be translated automatically into executable code.

Rules are classified into layers based on implementation complexity, and a reviewer confirms each rule before it is used.

Simple validation rules can be candidates for automated code generation.

More complex rules are routed toward manual implementation and review.

Every extracted rule is intended to retain provenance back to the regulatory source so a reviewer can understand **where the rule came from**, not merely what an AI model produced.

---

## Architecture

The current prototype consists of:

### Backend

- Python
- FastAPI
- Pydantic
- pandas
- pdfplumber
- openpyxl
- JSON Schema
- AWS S3 integration

### AI / extraction

- Zephyr-7B and DeepSeek (Hugging Face Inference API)
- Local LLM via Ollama
- FLAN-T5 (fine-tuning planned)
- Keyword-based fallback extractor

### Frontend

- Angular
- TypeScript
- RxJS
- SCSS

### Runtime / deployment

- Docker
- Render
- local filesystem or Amazon S3 for generated rule metadata

---

## Rule architecture

Rules implement a common `ValidationRule` abstraction and are discovered dynamically by the rule registry.

Each rule can carry metadata such as:

```text
rule_id
name
layer
severity
field
tags
source/document link
```

The validator groups rules by validation layer and executes applicable rules against each record.

This allows new rules to be introduced without hard-coding every validation rule into the core validation engine.

---

## Rule provenance

A major design goal of UMDE is traceability.

Extracted rules can preserve information including:

- CMS rule identifier;
- originating document;
- source page;
- original regulatory text;
- extraction method/model;
- extraction chain;
- confidence;
- classification rationale; and
- whether manual review is required.

The intent is that an executable validation rule should never become disconnected from the regulatory requirement that produced it.

---

## Workflow state

Rule-extraction runs move through explicit workflow states:

```text
Started
   ↓
Extracting
   ↓
Reviewing
   ↓
Generating
   ↓
Publishing
   ↓
Completed
```

Failed runs retain an error state, and workflow history can be persisted for later inspection.

The API also supports server-sent events (SSE) for real-time workflow progress.

---

## Current prototype boundaries

UMDE is under active development.

The repository demonstrates the architecture and core validation/extraction concepts, but it should **not** currently be treated as a production CMS submission or compliance system.

In particular:

- portions of the human-review workflow still use prototype/mock behavior;
- when source PDFs or model access are unavailable, extraction runs return sample rules with simulated progress, for demonstration only;
- complex regulatory rules still require manual implementation;
- production security, identity, persistence, audit, and deployment controls are not complete;
- the system has not been validated or certified by CMS; and
- the prototype should not be used with production PHI.

These constraints are intentional while the core regulatory-rule lifecycle is being developed and tested.

### Known issues

- **LLM extraction does not yet take effect.** Model wrappers return confidence as text ("high", "medium") while the orchestrator expects a number, so AI results are rejected and the keyword fallback is used. Fix: numeric confidence end to end.
- **Most rules are scaffolds.** 19 CMS rules are generated; the majority are stubs that do not yet flag errors, and field mappings are incomplete.
- **Rule exceptions are not yet treated as failures.** A rule that errors is skipped instead of failing the record.
- **Startup dependencies.** Some model libraries are listed only in the dev requirements file.

---

## Repository structure

```text
umde-hackathon/
├── backend/        # FastAPI APIs, parsers, rule engine and extraction workflow
├── frontend/       # Angular prototype UI
├── Dockerfile      # Backend container
├── render.yaml     # Render deployment configuration
├── requirements.txt
├── pytest.ini
└── architecture documents
```

---

## API

The FastAPI application exposes endpoints for areas including:

```text
/upload
/validate
/rules
/api/rules
/ping
/docs
```

When running locally, FastAPI's generated OpenAPI documentation is available through `/docs`.

---

## License

MIT License.
