# HALAJ-SCHEMA v1.0 - Diagrams

## Entity Relationship Diagram (Full)

```mermaid
erDiagram
    PERSON ||--o{ CLINICAL_DOCUMENT : "has"
    PERSON ||--o{ DISEASE_EXTRACTION : "has"
    DATA_SOURCE ||--o{ CLINICAL_DOCUMENT : "provides"
    CLINICAL_DOCUMENT ||--o{ DISEASE_EXTRACTION : "contains"
    CLINICAL_DOCUMENT ||--o{ PROCESSING_LOG : "tracked_by"
    DISEASE_EXTRACTION }o--|| ICD_MAPPING : "mapped_to"
    DISEASE_EXTRACTION }o--o| DISEASE_SCHEMA : "uses"
    DISEASE_EXTRACTION }o--o| PROCESSING_LOG : "created_by"
    SCHEMA_GENERATION_QUEUE }o--|| DISEASE_SCHEMA : "generates"

    PERSON {
        bigint person_id PK
        varchar person_source_id UK
        int birth_year
        enum gender
        timestamp created_at
    }

    DATA_SOURCE {
        int source_id PK
        varchar source_code UK
        varchar source_name
        enum source_type
        varchar city
        varchar province
        varchar country
        boolean is_active
    }

    CLINICAL_DOCUMENT {
        bigint document_id PK
        bigint person_id FK
        int source_id FK
        varchar document_source_id
        date document_date
        enum document_type
        enum source_language
        jsonb modalities
        jsonb abnormalities
        text document_text
        enum processing_status
    }

    DISEASE_EXTRACTION {
        bigint extraction_id PK
        bigint document_id FK
        bigint person_id FK
        int modality_index
        varchar disease_name_original
        varchar disease_name_english
        int icd_mapping_id FK
        varchar icd_code
        enum temporality
        date onset_date
        decimal confidence
        int schema_id FK
        jsonb metadata
    }

    DISEASE_SCHEMA {
        int schema_id PK
        varchar disease_name
        varchar icd_code
        int schema_version
        jsonb field_definitions
        text pydantic_class_code
        int sample_count
        boolean is_active
    }

    ICD_MAPPING {
        int mapping_id PK
        varchar disease_name_normalized UK
        varchar disease_name_display
        varchar icd_code
        enum match_status
        decimal match_confidence
        jsonb candidates_json
    }

    PROCESSING_LOG {
        bigint log_id PK
        bigint document_id FK
        enum pipeline_stage
        enum status
        int duration_ms
        varchar llm_model
        int token_count_input
        int token_count_output
    }

    SCHEMA_GENERATION_QUEUE {
        int queue_id PK
        varchar disease_name UK
        varchar icd_code
        bigint[] sample_document_ids
        int sample_count
        enum status
    }

    ICD_EMBEDDING {
        int embedding_id PK
        varchar icd_code UK
        varchar icd_description
        vector embedding
        varchar embedding_model
    }
```

---

## Document Type Flow

```mermaid
graph TB
    subgraph Input["📥 Clinical Documents"]
        RAD["🔬 Radiology<br/>CT, MRI, US, X-ray"]
        PATH["🔬 Pathology<br/>Biopsy, Resection"]
        LAB["🧪 Laboratory<br/>Blood, Urine"]
        ENDO["🔭 Endoscopy<br/>EGD, Colonoscopy"]
        SURG["🔪 Operative<br/>Surgery Reports"]
        DISCH["🏥 Discharge<br/>Summaries"]
        CLIN["📝 Clinical Note<br/>H&P, Progress"]
    end

    subgraph Processing["⚙️ LLM Extraction"]
        LLM["🤖 DocumentExtractionResult"]
    end

    subgraph TypeDetails["📋 Type-Specific Details"]
        RD["RadiologyDetails<br/>contrast, phases, technique"]
        PD["PathologyDetails<br/>specimen, stains, IHC, grade"]
        LD["LaboratoryDetails<br/>panel, sample, tests"]
        ED["EndoscopyDetails<br/>sedation, prep, interventions"]
        OD["OperativeDetails<br/>approach, time, blood loss"]
        DD["DischargeDetails<br/>LOS, disposition, meds"]
        CD["ClinicalNoteDetails<br/>type, specialty, CC"]
    end

    RAD --> LLM
    PATH --> LLM
    LAB --> LLM
    ENDO --> LLM
    SURG --> LLM
    DISCH --> LLM
    CLIN --> LLM

    LLM --> RD
    LLM --> PD
    LLM --> LD
    LLM --> ED
    LLM --> OD
    LLM --> DD
    LLM --> CD

    style RAD fill:#e3f2fd
    style PATH fill:#fce4ec
    style LAB fill:#fff3e0
    style ENDO fill:#e8f5e9
    style SURG fill:#f3e5f5
    style DISCH fill:#e0f7fa
    style CLIN fill:#fff8e1
    style LLM fill:#c8e6c9
```

---

## Layer Architecture

```mermaid
graph TB
    subgraph L1["🔵 Identity Layer"]
        P["👤 PERSON<br/>person_id, person_source_id"]
        DS["🏛️ DATA_SOURCE<br/>source_id, source_code"]
    end

    subgraph L2["🟠 Document Layer"]
        CD["📋 CLINICAL_DOCUMENT<br/>document_id, document_type<br/>modalities[], abnormalities[]"]
    end

    subgraph L3["🟢 Extraction Layer"]
        DE["🦠 DISEASE_EXTRACTION<br/>extraction_id, modality_index<br/>disease_name, metadata"]
        DSC["📐 DISEASE_SCHEMA<br/>schema_id, field_definitions"]
    end

    subgraph L4["🔴 Infrastructure Layer"]
        IM["🏷️ ICD_MAPPING<br/>mapping_id, icd_code"]
        PL["📊 PROCESSING_LOG<br/>log_id, stage, status"]
        SQ["📝 SCHEMA_QUEUE<br/>queue_id, sample_count"]
        IE["🧮 ICD_EMBEDDING<br/>embedding_id, vector"]
    end

    P --> CD
    DS --> CD
    CD --> DE
    DE --> IM
    DE --> DSC
    DE --> PL
    CD --> PL
    SQ -.-> DSC
    IM -.-> IE

    style L1 fill:#e3f2fd
    style L2 fill:#fff3e0
    style L3 fill:#e8f5e9
    style L4 fill:#fce4ec
```

---

## Modality Details by Document Type

```mermaid
graph LR
    subgraph Modality["📋 ExtractedModality"]
        BASE["index, code, name<br/>body_region"]
    end

    subgraph Details["Type-Specific Details"]
        RAD["🔬 radiology_details<br/>• contrast_iv<br/>• contrast_phases<br/>• technique<br/>• mri_sequences<br/>• slice_thickness"]
        
        PATH["🔬 pathology_details<br/>• specimen_type<br/>• collection_procedure<br/>• stains_performed<br/>• ihc_markers/results<br/>• tumor_grade<br/>• margins"]
        
        ENDO["🔭 endoscopy_details<br/>• procedure_type<br/>• sedation_type<br/>• bowel_prep_quality<br/>• biopsy_performed<br/>• interventions<br/>• polyps_found"]
        
        LAB["🧪 laboratory_details<br/>• panel_type<br/>• sample_type<br/>• fasting_status<br/>• culture_organism<br/>• sensitivities"]
        
        SURG["🔪 operative_details<br/>• procedure_name<br/>• surgical_approach<br/>• anesthesia_type<br/>• operative_time<br/>• blood_loss<br/>• specimens"]
    end

    BASE --> RAD
    BASE --> PATH
    BASE --> ENDO
    BASE --> LAB
    BASE --> SURG

    style BASE fill:#f5f5f5
    style RAD fill:#e3f2fd
    style PATH fill:#fce4ec
    style ENDO fill:#e8f5e9
    style LAB fill:#fff3e0
    style SURG fill:#f3e5f5
```

---

## Pipeline Flow

```mermaid
flowchart TD
    subgraph Stage1["📥 Stage 1: Document Ingestion"]
        A[/"📄 Receive Document"/] --> B["Determine document_type"]
        B --> C["👤 Create/Lookup PERSON"]
        C --> D["📋 Create CLINICAL_DOCUMENT"]
        D --> E["📊 Create PROCESSING_LOG"]
        E --> F["🤖 LLM Extraction<br/>DocumentExtractionResult"]
        F --> G["💾 Store modalities[]<br/>with type-specific details"]
        G --> H["💾 Store abnormalities[]"]
        H --> I["🦠 Create DISEASE_EXTRACTION<br/>for each disease"]
    end

    subgraph Stage2["🏷️ Stage 2: ICD Mapping"]
        I --> J["🔤 Normalize disease_name"]
        J --> K{"🔍 ICD_MAPPING<br/>cache lookup"}
        K -->|"✅ Found"| L["♻️ Use existing mapping"]
        K -->|"❌ Not Found"| M["🧮 Vector search<br/>ICD_EMBEDDING"]
        M --> N["🤖 LLM selects<br/>best match"]
        N --> O["💾 Create ICD_MAPPING"]
        O --> L
        L --> P["🔄 Update extraction"]
    end

    subgraph Stage3["📐 Stage 3: Metadata"]
        P --> Q{"📐 Schema<br/>exists?"}
        Q -->|"✅ Yes"| R["🤖 Extract metadata"]
        Q -->|"❌ No"| S["📝 Add to queue"]
        S --> T["⏭️ Skip metadata"]
        R --> U["💾 Update metadata"]
        T --> U
    end

    subgraph Stage4["🔄 Stage 4: Schema Gen"]
        V["⏰ Background"] --> W{"samples >= N?"}
        W -->|"✅ Yes"| X["📄 Fetch samples"]
        X --> Y["🎯 Cluster"]
        Y --> Z["🤖 Generate schema"]
        Z --> AA["💾 Create SCHEMA"]
    end

    U -.-> V

    style F fill:#c8e6c9
    style N fill:#c8e6c9
    style R fill:#c8e6c9
    style Z fill:#c8e6c9
```

---

## Modality Index Linkage

```mermaid
graph TB
    subgraph Document["📋 CLINICAL_DOCUMENT"]
        MOD["modalities JSONB Array"]
        MOD0["[0] CT Abdomen<br/>radiology_details: {...}"]
        MOD1["[1] CT Chest<br/>radiology_details: {...}"]
        MOD2["[2] Liver Biopsy<br/>pathology_details: {...}"]
        MOD --> MOD0
        MOD --> MOD1
        MOD --> MOD2
    end

    subgraph Extractions["🦠 DISEASE_EXTRACTIONs"]
        EXT1["Pancreatic Cancer<br/>modality_index: 0"]
        EXT2["Liver Metastasis<br/>modality_index: 0"]
        EXT3["Pulmonary Nodule<br/>modality_index: 1"]
        EXT4["Hepatocellular Carcinoma<br/>modality_index: 2"]
    end

    subgraph Abnormalities["⚠️ abnormalities[]"]
        ABN1["surgical_clips<br/>modality_index: 0"]
        ABN2["pleural_effusion<br/>modality_index: 1"]
    end

    MOD0 -.->|"index=0"| EXT1
    MOD0 -.->|"index=0"| EXT2
    MOD0 -.->|"index=0"| ABN1
    MOD1 -.->|"index=1"| EXT3
    MOD1 -.->|"index=1"| ABN2
    MOD2 -.->|"index=2"| EXT4

    style MOD0 fill:#bbdefb
    style MOD1 fill:#c8e6c9
    style MOD2 fill:#fff9c4
    style EXT1 fill:#bbdefb
    style EXT2 fill:#bbdefb
    style EXT3 fill:#c8e6c9
    style EXT4 fill:#fff9c4
    style ABN1 fill:#bbdefb
    style ABN2 fill:#c8e6c9
```

---

## Temporality Classification

```mermaid
graph LR
    subgraph Time["⏱️ Temporality Values"]
        CURRENT["🟢 CURRENT<br/>Active now"]
        HISTORICAL["🔵 HISTORICAL<br/>Past diagnosis"]
        SUSPECTED["🟡 SUSPECTED<br/>Under investigation"]
        RULED_OUT["⚪ RULED_OUT<br/>Excluded"]
        FAMILY["👨‍👩‍👧 FAMILY_HISTORY<br/>In family"]
        CHRONIC["🔄 CHRONIC<br/>Long-term"]
        ACUTE["⚡ ACUTE<br/>Sudden onset"]
        RECURRENT["🔁 RECURRENT<br/>Returned"]
        POST_TX["💊 POST_TREATMENT<br/>After therapy"]
        INCIDENTAL["🔍 INCIDENTAL<br/>Unexpected"]
        UNKNOWN["❓ UNKNOWN<br/>Cannot determine"]
    end

    style CURRENT fill:#c8e6c9
    style HISTORICAL fill:#bbdefb
    style SUSPECTED fill:#fff9c4
    style RULED_OUT fill:#f5f5f5
    style FAMILY fill:#e1bee7
    style CHRONIC fill:#b3e5fc
    style ACUTE fill:#ffcdd2
    style RECURRENT fill:#ffe0b2
    style POST_TX fill:#d1c4e9
    style INCIDENTAL fill:#b2dfdb
    style UNKNOWN fill:#e0e0e0
```

---

## ICD Mapping Workflow

```mermaid
sequenceDiagram
    participant App as 🖥️ Application
    participant Cache as 🗄️ ICD_MAPPING
    participant Vec as 🧮 ICD_EMBEDDING
    participant LLM as 🤖 LLM
    participant DB as 💾 Database

    App->>App: normalize_disease_name()
    App->>Cache: SELECT WHERE normalized = ?
    
    alt Cache Hit
        Cache-->>App: mapping_id, icd_code
        App->>DB: UPDATE disease_extraction
    else Cache Miss
        Cache-->>App: Not found
        App->>Vec: find_similar_icd_codes(embedding, 5)
        Vec-->>App: Top 5 candidates[]
        App->>LLM: Select best from candidates
        LLM-->>App: Selected + reasoning
        App->>Cache: INSERT new mapping
        Cache-->>App: New mapping_id
        App->>DB: UPDATE disease_extraction
    end
```

---

## Data Flow

```mermaid
flowchart LR
    subgraph Input["📥 Input Sources"]
        RAD["🔬 Radiology"]
        PATH["🧬 Pathology"]
        LAB["🧪 Laboratory"]
        ENDO["🔭 Endoscopy"]
        SURG["🔪 Surgery"]
        DISCH["🏥 Discharge"]
        CLIN["📝 Clinical"]
    end

    subgraph Processing["⚙️ Processing"]
        TYPE["Document<br/>Type Detection"]
        LLM["🤖 LLM<br/>Extraction"]
        ICD["🏷️ ICD<br/>Matching"]
        SCHEMA["📐 Schema<br/>Application"]
    end

    subgraph Storage["💾 PostgreSQL"]
        DB[("🗄️ Database<br/>+ pgvector")]
    end

    subgraph Output["📤 Output"]
        API["🔌 API"]
        DASH["📊 Analytics"]
        EXPORT["📁 Export"]
    end

    RAD --> TYPE
    PATH --> TYPE
    LAB --> TYPE
    ENDO --> TYPE
    SURG --> TYPE
    DISCH --> TYPE
    CLIN --> TYPE
    
    TYPE --> LLM
    LLM --> DB
    DB --> ICD
    ICD --> DB
    DB --> SCHEMA
    SCHEMA --> DB
    
    DB --> API
    DB --> DASH
    DB --> EXPORT

    style TYPE fill:#e3f2fd
    style LLM fill:#c8e6c9
    style ICD fill:#fff9c4
    style SCHEMA fill:#f3e5f5
    style DB fill:#ffccbc
```

---

## Severity Classification

```mermaid
graph TB
    subgraph Severity["⚠️ Abnormality Severity Levels"]
        MIN["🟢 MINIMAL<br/>No clinical significance<br/>surgical clips, simple cyst"]
        MILD["🔵 MILD<br/>May need monitoring<br/>small benign nodule"]
        MOD["🟡 MODERATE<br/>Requires attention<br/>indeterminate nodule"]
        SIG["🟠 SIGNIFICANT<br/>Requires intervention<br/>suspicious mass"]
        SEV["🔴 SEVERE<br/>Urgent attention<br/>active hemorrhage"]
    end

    MIN --> MILD --> MOD --> SIG --> SEV

    style MIN fill:#c8e6c9
    style MILD fill:#bbdefb
    style MOD fill:#fff9c4
    style SIG fill:#ffe0b2
    style SEV fill:#ffcdd2
```

---

## Processing Status Flow

```mermaid
stateDiagram-v2
    [*] --> PENDING: Document received
    PENDING --> PROCESSING: Start extraction
    PROCESSING --> COMPLETED: Success
    PROCESSING --> FAILED: Error
    FAILED --> PROCESSING: Retry
    PROCESSING --> REQUIRES_REVIEW: Low confidence
    REQUIRES_REVIEW --> COMPLETED: Manual review done
    COMPLETED --> [*]
```

---

## Pydantic Model Hierarchy

```mermaid
classDiagram
    class DocumentExtractionResult {
        +DocumentType document_type
        +List~ExtractedModality~ modalities
        +List~ExtractedDisease~ diseases
        +List~ExtractedAbnormality~ abnormalities
        +int patient_age
        +str clinical_indication
        +DischargeDetails discharge_details
        +ClinicalNoteDetails clinical_note_details
    }

    class ExtractedModality {
        +int index
        +ModalityCode code
        +str name
        +BodyRegion body_region
        +RadiologyDetails radiology_details
        +PathologyDetails pathology_details
        +EndoscopyDetails endoscopy_details
        +LaboratoryDetails laboratory_details
        +OperativeDetails operative_details
    }

    class ExtractedDisease {
        +str disease_name_original
        +str disease_name_english
        +int modality_index
        +Temporality temporality
        +str temporal_expression
        +date onset_date
        +float confidence
    }

    class ExtractedAbnormality {
        +str name
        +str anatomy
        +Severity severity
        +int modality_index
        +str size_cm
    }

    class RadiologyDetails {
        +bool contrast_iv
        +List~str~ contrast_phases
        +str technique
        +List~str~ mri_sequences
    }

    class PathologyDetails {
        +str specimen_type
        +str collection_procedure
        +List~str~ ihc_markers
        +Dict ihc_results
        +str tumor_grade
        +str margins
    }

    class EndoscopyDetails {
        +str procedure_type
        +str sedation_type
        +str bowel_prep_quality
        +int boston_prep_score
        +List~str~ therapeutic_interventions
    }

    class OperativeDetails {
        +str procedure_name
        +str surgical_approach
        +int operative_time_minutes
        +int estimated_blood_loss_ml
        +List~str~ specimens_collected
    }

    DocumentExtractionResult *-- ExtractedModality
    DocumentExtractionResult *-- ExtractedDisease
    DocumentExtractionResult *-- ExtractedAbnormality
    ExtractedModality *-- RadiologyDetails
    ExtractedModality *-- PathologyDetails
    ExtractedModality *-- EndoscopyDetails
    ExtractedModality *-- OperativeDetails
```
