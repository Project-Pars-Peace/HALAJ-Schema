-- =============================================================================
-- HALAJ-SCHEMA v1.0 - PostgreSQL Database Schema
-- =============================================================================
-- 
-- Optimized OMOP Schema for NLP-Based Medical Text Extraction
-- Supports: Radiology, Pathology, Laboratory, Endoscopy, Operative, Discharge, Clinical Notes
-- 
-- Requirements:
--   - PostgreSQL 14+
--   - pgvector extension (for ICD embedding similarity search)
-- 
-- Version: 1.0
-- Date: December 2025
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search

-- =============================================================================
-- ENUMERATIONS
-- =============================================================================

-- Gender classification
CREATE TYPE gender_enum AS ENUM (
    'MALE', 
    'FEMALE', 
    'OTHER', 
    'UNKNOWN'
);

-- Data source type
CREATE TYPE source_type_enum AS ENUM (
    'HOSPITAL',
    'CLINIC',
    'LABORATORY',
    'IMAGING_CENTER',
    'PATHOLOGY_LAB',
    'SURGICAL_CENTER',
    'OTHER'
);

-- Document source language
CREATE TYPE source_language_enum AS ENUM (
    'fa',      -- Persian/Farsi
    'en',      -- English
    'mixed'    -- Both languages present
);

-- Clinical document type
CREATE TYPE document_type_enum AS ENUM (
    'RADIOLOGY',      -- Imaging reports: CT, MRI, US, X-ray, PET
    'PATHOLOGY',      -- Surgical pathology, cytology, biopsy
    'LABORATORY',     -- Lab test results
    'ENDOSCOPY',      -- Endoscopic procedures
    'OPERATIVE',      -- Surgical/operative reports
    'DISCHARGE',      -- Discharge summaries
    'CLINICAL_NOTE',  -- Progress notes, H&P, consultations
    'OTHER'
);

-- Modality codes
CREATE TYPE modality_code_enum AS ENUM (
    -- Imaging
    'CT', 'MRI', 'US', 'XRAY', 'FLUORO', 'MAMMO',
    'PET', 'PET_CT', 'PET_MRI', 'SPECT', 'NM', 'DEXA', 'ANGIO',
    -- Endoscopy
    'ENDO', 'EGD', 'COLON', 'ERCP', 'EUS', 'BRONCH', 'CYSTO',
    -- Pathology/Lab
    'PATH', 'CYTO', 'LAB', 'MICRO', 'MOLECULAR',
    -- Clinical
    'SURGERY', 'CLINICAL', 'DISCHARGE', 'OTHER'
);

-- Body regions
CREATE TYPE body_region_enum AS ENUM (
    'HEAD', 'NECK', 'CHEST', 'BREAST', 'ABDOMEN', 'PELVIS', 'ABDOMEN_PELVIS',
    'SPINE', 'CERVICAL_SPINE', 'THORACIC_SPINE', 'LUMBAR_SPINE',
    'UPPER_EXTREMITY', 'LOWER_EXTREMITY', 'MUSCULOSKELETAL',
    'VASCULAR', 'CARDIAC', 'WHOLE_BODY',
    'UPPER_GI', 'LOWER_GI', 'HEPATOBILIARY', 'GENITOURINARY',
    'OTHER'
);

-- Temporality of disease mentions
CREATE TYPE temporality_enum AS ENUM (
    'CURRENT',        -- Active now
    'HISTORICAL',     -- Past diagnosis
    'SUSPECTED',      -- Under investigation
    'RULED_OUT',      -- Explicitly excluded
    'FAMILY_HISTORY', -- In family member
    'CHRONIC',        -- Long-term ongoing
    'ACUTE',          -- Sudden onset
    'RECURRENT',      -- Returned after resolution
    'POST_TREATMENT', -- After treatment
    'INCIDENTAL',     -- Unexpected finding
    'UNKNOWN'
);

-- Abnormality severity
CREATE TYPE severity_enum AS ENUM (
    'MINIMAL',      -- Incidental, no clinical significance
    'MILD',         -- Minor, may need monitoring
    'MODERATE',     -- Notable, requires attention
    'SIGNIFICANT',  -- Clinically important
    'SEVERE'        -- Critical, urgent
);

-- Document processing status
CREATE TYPE processing_status_enum AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED',
    'REQUIRES_REVIEW'
);

-- ICD match status
CREATE TYPE icd_match_status_enum AS ENUM (
    'MATCHED',
    'PARTIAL_MATCH',
    'NOT_MATCHED',
    'PENDING_REVIEW'
);

-- Pipeline stages
CREATE TYPE pipeline_stage_enum AS ENUM (
    'DOCUMENT_INGESTION',
    'DISEASE_EXTRACTION',
    'ICD_MATCHING',
    'METADATA_EXTRACTION',
    'SCHEMA_GENERATION',
    'QUALITY_CHECK'
);

-- Pipeline status
CREATE TYPE pipeline_status_enum AS ENUM (
    'PENDING',
    'RUNNING',
    'SUCCESS',
    'FAILED',
    'SKIPPED',
    'RETRYING'
);

-- Schema generation queue status
CREATE TYPE queue_status_enum AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED'
);


-- =============================================================================
-- IDENTITY LAYER
-- =============================================================================

-- PERSON: Core patient identity (simplified from OMOP)
CREATE TABLE person (
    person_id           BIGSERIAL PRIMARY KEY,
    person_source_id    VARCHAR(100) NOT NULL UNIQUE,  -- Original patient ID from source
    birth_year          INTEGER CHECK (birth_year BETWEEN 1900 AND 2100),
    gender              gender_enum,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE person IS 'Core patient identity table. Simplified from OMOP PERSON.';
COMMENT ON COLUMN person.person_source_id IS 'Original patient ID from the source system (hospital MRN, etc.)';


-- DATA_SOURCE: Reference table for hospitals/clinics
CREATE TABLE data_source (
    source_id       SERIAL PRIMARY KEY,
    source_code     VARCHAR(50) NOT NULL UNIQUE,   -- Short code (e.g., TUMS_IMAM)
    source_name     VARCHAR(200) NOT NULL,         -- Full institution name
    source_type     source_type_enum NOT NULL,
    city            VARCHAR(100),
    province        VARCHAR(100),
    country         VARCHAR(100) NOT NULL DEFAULT 'Iran',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE data_source IS 'Reference table for hospitals, clinics, and data providers.';


-- =============================================================================
-- DOCUMENT LAYER
-- =============================================================================

-- CLINICAL_DOCUMENT: Source documents with modalities and abnormalities
CREATE TABLE clinical_document (
    document_id         BIGSERIAL PRIMARY KEY,
    person_id           BIGINT NOT NULL REFERENCES person(person_id),
    source_id           INTEGER NOT NULL REFERENCES data_source(source_id),
    
    -- Source reference (minimal storage)
    document_source_id  VARCHAR(100) NOT NULL,     -- Original document ID in source system
    document_source_url VARCHAR(500),               -- URL/path to retrieve original
    
    -- Document metadata
    document_date       DATE NOT NULL,              -- Date of the clinical document
    document_type       document_type_enum NOT NULL, -- Type of document
    source_language     source_language_enum NOT NULL DEFAULT 'fa',
    
    -- Extracted structure (JSONB for flexibility)
    modalities          JSONB NOT NULL DEFAULT '[]'::JSONB,  -- Array of modalities with details
    abnormalities       JSONB DEFAULT '[]'::JSONB,           -- Array of non-disease findings
    
    -- Optional full text (can be cleared after processing)
    document_text       TEXT,
    text_hash           VARCHAR(64),                -- SHA-256 for deduplication
    
    -- Processing status
    processing_status   processing_status_enum NOT NULL DEFAULT 'PENDING',
    
    -- Timestamps
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT uk_document_source UNIQUE (source_id, document_source_id)
);

COMMENT ON TABLE clinical_document IS 'Source clinical documents with modalities and processing status.';
COMMENT ON COLUMN clinical_document.modalities IS 'JSONB array of modalities with type-specific metadata. Each has index, code, name, body_region, and type-specific details.';
COMMENT ON COLUMN clinical_document.abnormalities IS 'JSONB array of non-disease abnormalities/incidental findings.';
COMMENT ON COLUMN clinical_document.document_type IS 'Type of document: RADIOLOGY, PATHOLOGY, LABORATORY, ENDOSCOPY, OPERATIVE, DISCHARGE, CLINICAL_NOTE';

-- Modalities JSONB structure example:
-- [
--   {
--     "index": 0,
--     "code": "CT",
--     "name": "CT Abdomen and Pelvis with IV Contrast",
--     "body_region": "ABDOMEN_PELVIS",
--     "radiology_details": {
--       "contrast_iv": true,
--       "contrast_phases": ["arterial", "portal_venous"],
--       "technique": "multiphasic CT"
--     }
--   }
-- ]

-- Abnormalities JSONB structure example:
-- [
--   {
--     "name": "surgical_clips",
--     "anatomy": "gallbladder_fossa",
--     "severity": "MINIMAL",
--     "modality_index": 0
--   }
-- ]


-- =============================================================================
-- EXTRACTION LAYER
-- =============================================================================

-- DISEASE_EXTRACTION: Core atomic unit - one row per disease mention
CREATE TABLE disease_extraction (
    extraction_id           BIGSERIAL PRIMARY KEY,
    document_id             BIGINT NOT NULL REFERENCES clinical_document(document_id),
    person_id               BIGINT NOT NULL REFERENCES person(person_id),  -- Denormalized for fast queries
    
    -- Modality linkage
    modality_index          INTEGER NOT NULL CHECK (modality_index >= 0),
    
    -- Disease identification
    disease_name_original   VARCHAR(500) NOT NULL,   -- Original language (Persian/English)
    disease_name_english    VARCHAR(500) NOT NULL,   -- Standardized English name
    
    -- ICD mapping (with denormalized code for fast queries)
    icd_mapping_id          INTEGER REFERENCES icd_mapping(mapping_id),
    icd_code                VARCHAR(20),             -- Denormalized from icd_mapping
    
    -- Temporal information
    temporality             temporality_enum NOT NULL,
    temporal_expression     VARCHAR(200),            -- Raw temporal phrase from text
    onset_date              DATE,                    -- Computed onset date if determinable
    
    -- Patient context
    patient_age_at_document INTEGER CHECK (patient_age_at_document BETWEEN 0 AND 150),
    
    -- Extraction quality
    confidence              DECIMAL(4,3) CHECK (confidence BETWEEN 0 AND 1),
    extracted_text_snippet  VARCHAR(500),            -- Source text excerpt
    
    -- Dynamic schema for disease-specific metadata
    schema_id               INTEGER REFERENCES disease_schema(schema_id),
    metadata                JSONB,                   -- Disease-specific attributes
    
    -- Provenance
    processing_log_id       BIGINT REFERENCES processing_log(log_id),
    
    -- Timestamps
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE disease_extraction IS 'Core atomic unit: one row per disease mention in a document.';
COMMENT ON COLUMN disease_extraction.modality_index IS 'Index into document.modalities array (0-based).';
COMMENT ON COLUMN disease_extraction.icd_code IS 'Denormalized ICD code for fast queries. Source of truth is icd_mapping_id.';
COMMENT ON COLUMN disease_extraction.metadata IS 'Disease-specific attributes defined by disease_schema.';


-- DISEASE_SCHEMA: Dynamic Pydantic schemas per disease type
CREATE TABLE disease_schema (
    schema_id           SERIAL PRIMARY KEY,
    disease_name        VARCHAR(500) NOT NULL,       -- Canonical disease name
    icd_code            VARCHAR(20),                 -- Associated ICD code
    schema_version      INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
    
    -- Schema definition
    field_definitions   JSONB NOT NULL,              -- Array of field definitions
    pydantic_class_code TEXT,                        -- Generated Pydantic class as Python
    
    -- Metadata
    sample_count        INTEGER NOT NULL DEFAULT 0,  -- Reports used to generate
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Provenance
    processing_log_id   BIGINT REFERENCES processing_log(log_id),
    
    -- Timestamps
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Only one active version per disease
    CONSTRAINT uk_active_disease_schema UNIQUE (disease_name, is_active) 
        DEFERRABLE INITIALLY DEFERRED
);

COMMENT ON TABLE disease_schema IS 'Dynamic Pydantic schemas per disease type, generated from sample reports.';
COMMENT ON COLUMN disease_schema.field_definitions IS 'Array of {name, type, description, required, enum_values, unit} objects.';


-- =============================================================================
-- INFRASTRUCTURE LAYER
-- =============================================================================

-- ICD_MAPPING: Learned cache of disease name to ICD code mappings
CREATE TABLE icd_mapping (
    mapping_id              SERIAL PRIMARY KEY,
    
    -- Disease name (normalized for lookup)
    disease_name_normalized VARCHAR(500) NOT NULL UNIQUE,  -- Lowercase, cleaned
    disease_name_display    VARCHAR(500) NOT NULL,         -- Original casing
    
    -- ICD code
    icd_code                VARCHAR(20),
    icd_description         VARCHAR(500),
    
    -- Match quality
    match_status            icd_match_status_enum NOT NULL,
    match_confidence        DECIMAL(4,3) CHECK (match_confidence BETWEEN 0 AND 1),
    
    -- Selection details (for auditing)
    candidates_json         JSONB,                         -- Top 5 candidates from vector search
    selection_reasoning     TEXT,                          -- LLM explanation
    
    -- Provenance
    created_by_model        VARCHAR(100),                  -- LLM model that created mapping
    
    -- Manual verification
    verified_by             VARCHAR(100),
    verified_at             TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE icd_mapping IS 'Learned cache of disease name to ICD code mappings. Lookup before vector search.';
COMMENT ON COLUMN icd_mapping.disease_name_normalized IS 'Lowercase, trimmed disease name for consistent lookup.';
COMMENT ON COLUMN icd_mapping.candidates_json IS 'Top 5 candidates from ICD embedding vector search.';


-- PROCESSING_LOG: Pipeline execution tracking
CREATE TABLE processing_log (
    log_id              BIGSERIAL PRIMARY KEY,
    document_id         BIGINT REFERENCES clinical_document(document_id),
    
    -- Pipeline info
    pipeline_stage      pipeline_stage_enum NOT NULL,
    pipeline_version    VARCHAR(50) NOT NULL,
    status              pipeline_status_enum NOT NULL DEFAULT 'PENDING',
    
    -- Timing
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    duration_ms         INTEGER,
    
    -- Error handling
    error_message       TEXT,
    error_type          VARCHAR(100),
    retry_count         INTEGER NOT NULL DEFAULT 0,
    
    -- LLM details
    llm_provider        VARCHAR(50),                 -- OpenAI, Anthropic, Local, etc.
    llm_model           VARCHAR(100),                -- gpt-4o, claude-3-opus, etc.
    prompt_template_id  VARCHAR(100),
    token_count_input   INTEGER,
    token_count_output  INTEGER,
    
    -- Timestamps
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE processing_log IS 'Pipeline execution tracking with error handling and LLM metrics.';


-- SCHEMA_GENERATION_QUEUE: Queue for diseases awaiting schema generation
CREATE TABLE schema_generation_queue (
    queue_id            SERIAL PRIMARY KEY,
    disease_name        VARCHAR(500) NOT NULL UNIQUE,
    icd_code            VARCHAR(20),
    
    -- Sample collection
    sample_document_ids BIGINT[] NOT NULL DEFAULT '{}',
    sample_count        INTEGER NOT NULL DEFAULT 0,
    
    -- Status
    status              queue_status_enum NOT NULL DEFAULT 'PENDING',
    processed_at        TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE schema_generation_queue IS 'Queue for diseases awaiting schema generation. Triggers when sample_count reaches threshold.';


-- ICD_EMBEDDING: Vector embeddings for ICD similarity search
CREATE TABLE icd_embedding (
    embedding_id        SERIAL PRIMARY KEY,
    icd_code            VARCHAR(20) NOT NULL UNIQUE,
    icd_description     VARCHAR(500) NOT NULL,
    embedding           vector(1536) NOT NULL,       -- OpenAI text-embedding-3-small dimension
    embedding_model     VARCHAR(100) NOT NULL,
    
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE icd_embedding IS 'Vector embeddings for ICD codes, used for semantic similarity search.';


-- =============================================================================
-- INDEXES
-- =============================================================================

-- Person indexes
CREATE INDEX idx_person_source_id ON person(person_source_id);

-- Clinical document indexes
CREATE INDEX idx_document_person ON clinical_document(person_id);
CREATE INDEX idx_document_source ON clinical_document(source_id);
CREATE INDEX idx_document_date ON clinical_document(document_date);
CREATE INDEX idx_document_person_date ON clinical_document(person_id, document_date);
CREATE INDEX idx_document_type ON clinical_document(document_type);
CREATE INDEX idx_document_status ON clinical_document(processing_status);
CREATE INDEX idx_document_text_hash ON clinical_document(text_hash);

-- GIN indexes for JSONB
CREATE INDEX idx_document_modalities ON clinical_document USING GIN (modalities);
CREATE INDEX idx_document_abnormalities ON clinical_document USING GIN (abnormalities);

-- Disease extraction indexes
CREATE INDEX idx_extraction_document ON disease_extraction(document_id);
CREATE INDEX idx_extraction_person ON disease_extraction(person_id);
CREATE INDEX idx_extraction_disease_english ON disease_extraction(disease_name_english);
CREATE INDEX idx_extraction_icd_code ON disease_extraction(icd_code);
CREATE INDEX idx_extraction_temporality ON disease_extraction(temporality);
CREATE INDEX idx_extraction_person_disease ON disease_extraction(person_id, disease_name_english);

-- Text search indexes
CREATE INDEX idx_extraction_disease_trgm ON disease_extraction 
    USING GIN (disease_name_english gin_trgm_ops);

-- Disease schema indexes
CREATE INDEX idx_schema_disease ON disease_schema(disease_name);
CREATE INDEX idx_schema_active ON disease_schema(is_active) WHERE is_active = TRUE;

-- ICD mapping indexes
CREATE INDEX idx_icd_mapping_code ON icd_mapping(icd_code);
CREATE INDEX idx_icd_mapping_status ON icd_mapping(match_status);

-- Processing log indexes
CREATE INDEX idx_log_document ON processing_log(document_id);
CREATE INDEX idx_log_stage_status ON processing_log(pipeline_stage, status);
CREATE INDEX idx_log_created ON processing_log(created_at);

-- Schema generation queue indexes
CREATE INDEX idx_queue_status ON schema_generation_queue(status);

-- Vector similarity index (IVFFlat for faster search)
CREATE INDEX idx_icd_embedding_vector ON icd_embedding 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function: Normalize disease name for ICD lookup
CREATE OR REPLACE FUNCTION normalize_disease_name(name TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN LOWER(TRIM(REGEXP_REPLACE(name, '\s+', ' ', 'g')));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION normalize_disease_name IS 'Normalize disease name: lowercase, trim, collapse multiple spaces.';


-- Function: Add disease to schema generation queue (upsert)
CREATE OR REPLACE FUNCTION add_to_schema_queue(
    p_disease_name VARCHAR(500),
    p_icd_code VARCHAR(20),
    p_document_id BIGINT
) RETURNS INTEGER AS $$
DECLARE
    v_queue_id INTEGER;
BEGIN
    INSERT INTO schema_generation_queue (disease_name, icd_code, sample_document_ids, sample_count)
    VALUES (p_disease_name, p_icd_code, ARRAY[p_document_id], 1)
    ON CONFLICT (disease_name) 
    DO UPDATE SET 
        sample_document_ids = CASE 
            WHEN NOT (p_document_id = ANY(schema_generation_queue.sample_document_ids))
            THEN array_append(schema_generation_queue.sample_document_ids, p_document_id)
            ELSE schema_generation_queue.sample_document_ids
        END,
        sample_count = CASE 
            WHEN NOT (p_document_id = ANY(schema_generation_queue.sample_document_ids))
            THEN schema_generation_queue.sample_count + 1
            ELSE schema_generation_queue.sample_count
        END
    WHERE schema_generation_queue.status = 'PENDING'
    RETURNING queue_id INTO v_queue_id;
    
    RETURN v_queue_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION add_to_schema_queue IS 'Add a document to the schema generation queue for a disease. Upserts and increments sample count.';


-- Function: Sync ICD codes from mapping (after mapping update)
CREATE OR REPLACE FUNCTION sync_icd_codes_from_mapping(p_mapping_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE disease_extraction de
    SET icd_code = im.icd_code,
        updated_at = CURRENT_TIMESTAMP
    FROM icd_mapping im
    WHERE de.icd_mapping_id = im.mapping_id
      AND im.mapping_id = p_mapping_id
      AND de.icd_code IS DISTINCT FROM im.icd_code;
    
    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sync_icd_codes_from_mapping IS 'Sync denormalized ICD codes in disease_extraction after an ICD mapping is updated.';


-- Function: Find similar ICD codes using vector similarity
CREATE OR REPLACE FUNCTION find_similar_icd_codes(
    p_query_embedding vector(1536),
    p_limit INTEGER DEFAULT 5
) RETURNS TABLE (
    icd_code VARCHAR(20),
    icd_description VARCHAR(500),
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ie.icd_code,
        ie.icd_description,
        1 - (ie.embedding <=> p_query_embedding) AS similarity
    FROM icd_embedding ie
    ORDER BY ie.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_similar_icd_codes IS 'Find ICD codes similar to a query embedding using cosine similarity.';


-- Function: Update document processing status
CREATE OR REPLACE FUNCTION update_document_status(
    p_document_id BIGINT,
    p_status processing_status_enum
) RETURNS VOID AS $$
BEGIN
    UPDATE clinical_document
    SET processing_status = p_status,
        updated_at = CURRENT_TIMESTAMP
    WHERE document_id = p_document_id;
END;
$$ LANGUAGE plpgsql;


-- Function: Get modality at index
CREATE OR REPLACE FUNCTION get_modality_at_index(
    p_document_id BIGINT,
    p_modality_index INTEGER
) RETURNS JSONB AS $$
BEGIN
    RETURN (
        SELECT modalities->p_modality_index
        FROM clinical_document
        WHERE document_id = p_document_id
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_modality_at_index IS 'Get a specific modality from a document by its index.';


-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger: Update timestamps on modification
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_person_update
    BEFORE UPDATE ON person
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER tr_clinical_document_update
    BEFORE UPDATE ON clinical_document
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER tr_disease_extraction_update
    BEFORE UPDATE ON disease_extraction
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER tr_disease_schema_update
    BEFORE UPDATE ON disease_schema
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER tr_icd_mapping_update
    BEFORE UPDATE ON icd_mapping
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();


-- Trigger: Calculate processing duration
CREATE OR REPLACE FUNCTION calculate_processing_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_ms = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)) * 1000;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_processing_log_duration
    BEFORE INSERT OR UPDATE ON processing_log
    FOR EACH ROW EXECUTE FUNCTION calculate_processing_duration();


-- =============================================================================
-- VIEWS
-- =============================================================================

-- View: Full disease extraction with all context
CREATE OR REPLACE VIEW v_disease_extraction_full AS
SELECT 
    de.extraction_id,
    de.document_id,
    de.person_id,
    p.person_source_id,
    p.birth_year,
    p.gender,
    
    -- Document context
    cd.document_date,
    cd.document_type,
    cd.source_language,
    ds.source_code,
    ds.source_name,
    ds.city AS source_city,
    
    -- Modality context
    de.modality_index,
    cd.modalities->de.modality_index->>'code' AS modality_code,
    cd.modalities->de.modality_index->>'name' AS modality_name,
    cd.modalities->de.modality_index->>'body_region' AS body_region,
    cd.modalities->de.modality_index AS modality_details,
    
    -- Disease details
    de.disease_name_original,
    de.disease_name_english,
    de.icd_code,
    im.icd_description,
    de.temporality,
    de.temporal_expression,
    de.onset_date,
    de.patient_age_at_document,
    de.confidence,
    de.extracted_text_snippet,
    
    -- Metadata
    de.schema_id,
    de.metadata,
    
    de.created_at
    
FROM disease_extraction de
JOIN person p ON de.person_id = p.person_id
JOIN clinical_document cd ON de.document_id = cd.document_id
JOIN data_source ds ON cd.source_id = ds.source_id
LEFT JOIN icd_mapping im ON de.icd_mapping_id = im.mapping_id;

COMMENT ON VIEW v_disease_extraction_full IS 'Complete disease extraction view with patient, document, modality, and source context.';


-- View: Patient disease timeline
CREATE OR REPLACE VIEW v_patient_timeline AS
SELECT 
    p.person_id,
    p.person_source_id,
    de.disease_name_english,
    de.icd_code,
    de.temporality,
    cd.document_date,
    cd.document_type,
    cd.modalities->de.modality_index->>'code' AS modality_code,
    ds.source_code AS hospital,
    de.extraction_id
FROM person p
JOIN disease_extraction de ON p.person_id = de.person_id
JOIN clinical_document cd ON de.document_id = cd.document_id
JOIN data_source ds ON cd.source_id = ds.source_id
ORDER BY p.person_id, cd.document_date;

COMMENT ON VIEW v_patient_timeline IS 'Chronological disease timeline per patient.';


-- View: Document processing status summary
CREATE OR REPLACE VIEW v_processing_status AS
SELECT 
    cd.document_type,
    cd.processing_status,
    COUNT(*) AS document_count,
    MIN(cd.created_at) AS oldest_document,
    MAX(cd.created_at) AS newest_document
FROM clinical_document cd
GROUP BY cd.document_type, cd.processing_status
ORDER BY cd.document_type, cd.processing_status;

COMMENT ON VIEW v_processing_status IS 'Summary of document processing status by document type.';


-- View: ICD mapping statistics
CREATE OR REPLACE VIEW v_icd_mapping_stats AS
SELECT 
    match_status,
    COUNT(*) AS mapping_count,
    AVG(match_confidence) AS avg_confidence,
    COUNT(*) FILTER (WHERE verified_by IS NOT NULL) AS verified_count
FROM icd_mapping
GROUP BY match_status;

COMMENT ON VIEW v_icd_mapping_stats IS 'ICD mapping statistics by status.';


-- View: Schema generation queue with sample counts
CREATE OR REPLACE VIEW v_schema_queue_ready AS
SELECT 
    queue_id,
    disease_name,
    icd_code,
    sample_count,
    array_length(sample_document_ids, 1) AS unique_documents,
    status,
    created_at
FROM schema_generation_queue
WHERE status = 'PENDING'
ORDER BY sample_count DESC;

COMMENT ON VIEW v_schema_queue_ready IS 'Schema generation queue items, ordered by sample count.';


-- View: Pipeline performance metrics
CREATE OR REPLACE VIEW v_pipeline_metrics AS
SELECT 
    DATE(created_at) AS processing_date,
    pipeline_stage,
    status,
    COUNT(*) AS execution_count,
    AVG(duration_ms) AS avg_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_duration_ms,
    SUM(token_count_input) AS total_input_tokens,
    SUM(token_count_output) AS total_output_tokens
FROM processing_log
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at), pipeline_stage, status
ORDER BY processing_date DESC, pipeline_stage;

COMMENT ON VIEW v_pipeline_metrics IS 'Pipeline performance metrics aggregated by day and stage.';


-- View: Disease extraction by document type
CREATE OR REPLACE VIEW v_extractions_by_document_type AS
SELECT 
    cd.document_type,
    COUNT(DISTINCT cd.document_id) AS document_count,
    COUNT(de.extraction_id) AS disease_count,
    COUNT(DISTINCT de.disease_name_english) AS unique_diseases,
    ROUND(AVG(de.confidence)::NUMERIC, 3) AS avg_confidence
FROM clinical_document cd
LEFT JOIN disease_extraction de ON cd.document_id = de.document_id
GROUP BY cd.document_type
ORDER BY document_count DESC;

COMMENT ON VIEW v_extractions_by_document_type IS 'Extraction statistics grouped by document type.';


-- =============================================================================
-- SAMPLE DATA (Optional - for testing)
-- =============================================================================

-- Insert sample data sources
INSERT INTO data_source (source_code, source_name, source_type, city, province, country) VALUES
    ('TUMS_IMAM', 'Imam Khomeini Hospital Complex', 'HOSPITAL', 'Tehran', 'Tehran', 'Iran'),
    ('TUMS_SHARIATI', 'Shariati Hospital', 'HOSPITAL', 'Tehran', 'Tehran', 'Iran'),
    ('TUMS_SINA', 'Sina Hospital', 'HOSPITAL', 'Tehran', 'Tehran', 'Iran')
ON CONFLICT (source_code) DO NOTHING;


-- =============================================================================
-- GRANTS (Adjust roles as needed)
-- =============================================================================

-- Example: Create application role with appropriate permissions
-- CREATE ROLE halaj_app WITH LOGIN PASSWORD 'your_password';
-- GRANT USAGE ON SCHEMA public TO halaj_app;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO halaj_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO halaj_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO halaj_app;


-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
