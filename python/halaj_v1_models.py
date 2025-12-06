"""
HALAJ-SCHEMA v1.0 - Pydantic Models for LLM-Based Medical Text Extraction

This module defines all data models for extracting structured information from
Persian/English clinical documents including radiology reports, pathology reports,
laboratory results, endoscopy reports, operative notes, discharge summaries, and
clinical notes.

All model field descriptions are written to be directly usable as LLM prompts.

Usage:
    from halaj_v1_models import DocumentExtractionResult
    
    # Use as structured output schema for LLM
    result = llm.extract(document_text, output_schema=DocumentExtractionResult)

Version: 1.0
Date: December 2025
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMERATIONS
# =============================================================================

class Gender(str, Enum):
    """Patient gender classification."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class SourceType(str, Enum):
    """Type of healthcare facility providing the document."""
    HOSPITAL = "HOSPITAL"
    CLINIC = "CLINIC"
    LABORATORY = "LABORATORY"
    IMAGING_CENTER = "IMAGING_CENTER"
    PATHOLOGY_LAB = "PATHOLOGY_LAB"
    SURGICAL_CENTER = "SURGICAL_CENTER"
    OTHER = "OTHER"


class SourceLanguage(str, Enum):
    """Primary language of the source document."""
    FA = "fa"  # Persian/Farsi
    EN = "en"  # English
    MIXED = "mixed"  # Both languages present


class DocumentType(str, Enum):
    """
    Classification of clinical document type.
    Determines which type-specific metadata fields are applicable.
    """
    RADIOLOGY = "RADIOLOGY"
    """Imaging reports: CT, MRI, ultrasound, X-ray, PET, nuclear medicine, mammography."""
    
    PATHOLOGY = "PATHOLOGY"
    """Surgical pathology, cytology, biopsy reports, autopsy reports."""
    
    LABORATORY = "LABORATORY"
    """Laboratory test results: blood work, urinalysis, microbiology, molecular tests."""
    
    ENDOSCOPY = "ENDOSCOPY"
    """Endoscopic procedures: EGD, colonoscopy, ERCP, EUS, bronchoscopy, cystoscopy."""
    
    OPERATIVE = "OPERATIVE"
    """Surgical and operative reports describing procedures performed."""
    
    DISCHARGE = "DISCHARGE"
    """Hospital discharge summaries with admission/discharge details."""
    
    CLINICAL_NOTE = "CLINICAL_NOTE"
    """Progress notes, H&P, consultations, follow-up notes."""
    
    OTHER = "OTHER"
    """Documents that don't fit other categories."""


class ModalityCode(str, Enum):
    """
    Standard modality codes for imaging and procedures.
    Use the most specific code that applies.
    """
    # Imaging modalities
    CT = "CT"
    """Computed Tomography scan."""
    
    MRI = "MRI"
    """Magnetic Resonance Imaging."""
    
    US = "US"
    """Ultrasound / Sonography."""
    
    XRAY = "XRAY"
    """Plain radiograph / X-ray."""
    
    FLUORO = "FLUORO"
    """Fluoroscopy."""
    
    MAMMO = "MAMMO"
    """Mammography."""
    
    PET = "PET"
    """Positron Emission Tomography (standalone)."""
    
    PET_CT = "PET_CT"
    """Combined PET/CT scan."""
    
    PET_MRI = "PET_MRI"
    """Combined PET/MRI scan."""
    
    SPECT = "SPECT"
    """Single Photon Emission Computed Tomography."""
    
    NM = "NM"
    """Nuclear Medicine scan (bone scan, thyroid scan, etc.)."""
    
    DEXA = "DEXA"
    """Dual-energy X-ray absorptiometry (bone density)."""
    
    ANGIO = "ANGIO"
    """Angiography."""
    
    # Procedure modalities
    ENDO = "ENDO"
    """Endoscopy (when specific type not determinable)."""
    
    EGD = "EGD"
    """Esophagogastroduodenoscopy."""
    
    COLON = "COLON"
    """Colonoscopy."""
    
    ERCP = "ERCP"
    """Endoscopic Retrograde Cholangiopancreatography."""
    
    EUS = "EUS"
    """Endoscopic Ultrasound."""
    
    BRONCH = "BRONCH"
    """Bronchoscopy."""
    
    CYSTO = "CYSTO"
    """Cystoscopy."""
    
    # Pathology/Lab modalities
    PATH = "PATH"
    """Surgical pathology."""
    
    CYTO = "CYTO"
    """Cytology (Pap smear, FNA cytology, fluid cytology)."""
    
    LAB = "LAB"
    """Laboratory tests."""
    
    MICRO = "MICRO"
    """Microbiology cultures and sensitivity."""
    
    MOLECULAR = "MOLECULAR"
    """Molecular/genetic testing."""
    
    # Clinical modalities
    SURGERY = "SURGERY"
    """Surgical procedure."""
    
    CLINICAL = "CLINICAL"
    """Clinical examination/note."""
    
    DISCHARGE = "DISCHARGE"
    """Discharge summary."""
    
    OTHER = "OTHER"
    """Other modality not listed."""


class BodyRegion(str, Enum):
    """
    Anatomical body region. Select the primary region examined or affected.
    For procedures spanning multiple regions, use the most clinically relevant one.
    """
    HEAD = "HEAD"
    """Brain, skull, face, orbits, sinuses."""
    
    NECK = "NECK"
    """Cervical spine, thyroid, lymph nodes, soft tissues of neck."""
    
    CHEST = "CHEST"
    """Thorax, lungs, mediastinum, heart, thoracic spine."""
    
    BREAST = "BREAST"
    """Breast tissue, axilla for breast imaging."""
    
    ABDOMEN = "ABDOMEN"
    """Liver, spleen, pancreas, kidneys, GI tract, abdominal vessels."""
    
    PELVIS = "PELVIS"
    """Bladder, reproductive organs, rectum, pelvic bones."""
    
    ABDOMEN_PELVIS = "ABDOMEN_PELVIS"
    """Combined abdominal and pelvic examination."""
    
    SPINE = "SPINE"
    """Vertebral column (when not specific to cervical/thoracic/lumbar)."""
    
    CERVICAL_SPINE = "CERVICAL_SPINE"
    """Cervical vertebrae C1-C7."""
    
    THORACIC_SPINE = "THORACIC_SPINE"
    """Thoracic vertebrae T1-T12."""
    
    LUMBAR_SPINE = "LUMBAR_SPINE"
    """Lumbar vertebrae L1-L5, including lumbosacral."""
    
    UPPER_EXTREMITY = "UPPER_EXTREMITY"
    """Shoulder, arm, elbow, forearm, wrist, hand."""
    
    LOWER_EXTREMITY = "LOWER_EXTREMITY"
    """Hip, thigh, knee, leg, ankle, foot."""
    
    MUSCULOSKELETAL = "MUSCULOSKELETAL"
    """Bones and joints (general)."""
    
    VASCULAR = "VASCULAR"
    """Blood vessels, angiography studies."""
    
    CARDIAC = "CARDIAC"
    """Heart-specific imaging."""
    
    WHOLE_BODY = "WHOLE_BODY"
    """Full body scan (PET, bone scan)."""
    
    UPPER_GI = "UPPER_GI"
    """Esophagus, stomach, duodenum (for endoscopy)."""
    
    LOWER_GI = "LOWER_GI"
    """Colon, rectum (for endoscopy)."""
    
    HEPATOBILIARY = "HEPATOBILIARY"
    """Liver, gallbladder, bile ducts, pancreas (for ERCP/EUS)."""
    
    GENITOURINARY = "GENITOURINARY"
    """Kidneys, ureters, bladder, reproductive organs."""
    
    OTHER = "OTHER"
    """Body region not listed above."""


class Temporality(str, Enum):
    """
    Temporal status of a disease or condition relative to the current document.
    This indicates WHEN the disease is/was present, not its severity.
    """
    CURRENT = "CURRENT"
    """Disease is currently active/present at the time of this report.
    Example: 'Patient has a 3cm pancreatic mass' or 'Active pneumonia'."""
    
    HISTORICAL = "HISTORICAL"
    """Disease occurred in the past; may or may not be resolved.
    Example: 'History of breast cancer, status post mastectomy'."""
    
    SUSPECTED = "SUSPECTED"
    """Disease is being considered but not confirmed; under investigation.
    Example: 'Rule out malignancy' or 'Findings suspicious for metastasis'."""
    
    RULED_OUT = "RULED_OUT"
    """Disease has been explicitly excluded or negated.
    Example: 'No evidence of recurrence' or 'Metastasis ruled out'."""
    
    FAMILY_HISTORY = "FAMILY_HISTORY"
    """Disease present in a family member, not the patient.
    Example: 'Father with history of colon cancer'."""
    
    CHRONIC = "CHRONIC"
    """Long-standing condition that persists over time.
    Example: 'Chronic kidney disease stage 3' or 'Chronic hepatitis B'."""
    
    ACUTE = "ACUTE"
    """Recent or sudden onset condition.
    Example: 'Acute pancreatitis' or 'Acute appendicitis'."""
    
    RECURRENT = "RECURRENT"
    """Disease has returned after a period of resolution.
    Example: 'Recurrent ovarian cancer' or 'Recurrence of lymphoma'."""
    
    POST_TREATMENT = "POST_TREATMENT"
    """Status after treatment; monitoring for response or recurrence.
    Example: 'Post-chemotherapy changes' or 'Post-radiation fibrosis'."""
    
    INCIDENTAL = "INCIDENTAL"
    """Finding discovered unexpectedly, unrelated to primary indication.
    Example: 'Incidental thyroid nodule' or 'Incidentally noted renal cyst'."""
    
    UNKNOWN = "UNKNOWN"
    """Temporal status cannot be determined from the text."""


class Severity(str, Enum):
    """
    Severity classification for abnormalities and findings.
    Used to prioritize clinical attention.
    """
    MINIMAL = "MINIMAL"
    """Incidental finding with no clinical significance.
    Examples: Simple cyst, old granuloma, surgical clips."""
    
    MILD = "MILD"
    """Minor finding that may warrant monitoring but no immediate action.
    Examples: Small benign-appearing nodule, mild fatty liver."""
    
    MODERATE = "MODERATE"
    """Notable finding requiring attention or follow-up.
    Examples: Indeterminate nodule, moderate stenosis."""
    
    SIGNIFICANT = "SIGNIFICANT"
    """Clinically important finding requiring intervention or close follow-up.
    Examples: Suspicious mass, significant obstruction."""
    
    SEVERE = "SEVERE"
    """Critical finding requiring urgent attention.
    Examples: Active hemorrhage, impending perforation, critical stenosis."""


class ProcessingStatus(str, Enum):
    """Status of document processing through the pipeline."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class ICDMatchStatus(str, Enum):
    """Status of ICD code matching."""
    MATCHED = "MATCHED"
    """Successfully matched to ICD code with high confidence."""
    
    PARTIAL_MATCH = "PARTIAL_MATCH"
    """Matched but may need review (moderate confidence)."""
    
    NOT_MATCHED = "NOT_MATCHED"
    """Could not find appropriate ICD code."""
    
    PENDING_REVIEW = "PENDING_REVIEW"
    """Requires manual review."""


class PipelineStage(str, Enum):
    """Pipeline processing stages."""
    DOCUMENT_INGESTION = "DOCUMENT_INGESTION"
    DISEASE_EXTRACTION = "DISEASE_EXTRACTION"
    ICD_MATCHING = "ICD_MATCHING"
    METADATA_EXTRACTION = "METADATA_EXTRACTION"
    SCHEMA_GENERATION = "SCHEMA_GENERATION"
    QUALITY_CHECK = "QUALITY_CHECK"


class PipelineStatus(str, Enum):
    """Status of a pipeline stage execution."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    RETRYING = "RETRYING"


class QueueStatus(str, Enum):
    """Status of schema generation queue items."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# =============================================================================
# TYPE-SPECIFIC METADATA MODELS
# =============================================================================

class RadiologyDetails(BaseModel):
    """
    Radiology-specific metadata for imaging studies.
    Extract these details when document_type is RADIOLOGY.
    """
    
    contrast_iv: Optional[bool] = Field(
        None,
        description="Whether intravenous contrast was administered. True if contrast was given, False if non-contrast study, None if not mentioned."
    )
    
    contrast_phases: Optional[list[str]] = Field(
        None,
        description="Contrast enhancement phases acquired. Common values: 'non-contrast', 'arterial', 'portal_venous', 'venous', 'delayed', 'equilibrium', 'hepatobiliary'. List all phases mentioned."
    )
    
    contrast_oral: Optional[bool] = Field(
        None,
        description="Whether oral contrast was administered (for CT abdomen/pelvis)."
    )
    
    contrast_agent: Optional[str] = Field(
        None,
        max_length=100,
        description="Name of contrast agent if specified (e.g., 'Omnipaque', 'Gadavist', 'Eovist')."
    )
    
    technique: Optional[str] = Field(
        None,
        max_length=200,
        description="Imaging technique description (e.g., 'multiphasic CT', 'diffusion-weighted MRI', 'Doppler ultrasound')."
    )
    
    slice_thickness_mm: Optional[float] = Field(
        None,
        ge=0,
        description="CT/MRI slice thickness in millimeters if specified."
    )
    
    field_strength_tesla: Optional[float] = Field(
        None,
        ge=0,
        description="MRI field strength in Tesla (e.g., 1.5, 3.0)."
    )
    
    mri_sequences: Optional[list[str]] = Field(
        None,
        description="MRI sequences performed. Common values: 'T1', 'T2', 'FLAIR', 'DWI', 'ADC', 'SWI', 'MRA', 'MRV', 'MRCP', 'post-contrast T1'."
    )
    
    radiopharmaceutical: Optional[str] = Field(
        None,
        max_length=100,
        description="Radiotracer used for nuclear medicine/PET (e.g., 'FDG', 'Tc-99m MDP', 'Ga-68 DOTATATE')."
    )
    
    comparison_study_date: Optional[str] = Field(
        None,
        max_length=50,
        description="Date of prior study used for comparison, if mentioned."
    )
    
    radiation_dose_mgy: Optional[float] = Field(
        None,
        ge=0,
        description="Radiation dose in mGy if documented (CT dose report)."
    )
    
    ultrasound_approach: Optional[str] = Field(
        None,
        max_length=100,
        description="Ultrasound approach if applicable: 'transabdominal', 'endovaginal', 'transrectal', 'transthoracic', 'transesophageal'."
    )


class PathologyDetails(BaseModel):
    """
    Pathology-specific metadata for surgical pathology and cytology reports.
    Extract these details when document_type is PATHOLOGY.
    """
    
    specimen_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Type of specimen. Common values: 'biopsy', 'core_biopsy', 'excision', 'resection', 'fine_needle_aspiration', 'cytology', 'autopsy'."
    )
    
    collection_procedure: Optional[str] = Field(
        None,
        max_length=200,
        description="How the specimen was obtained (e.g., 'CT-guided biopsy', 'EUS-FNA', 'surgical resection', 'Whipple procedure', 'colonoscopic polypectomy')."
    )
    
    tissue_source: Optional[str] = Field(
        None,
        max_length=200,
        description="Specific organ/tissue sampled (e.g., 'pancreatic head', 'liver segment 6', 'sigmoid colon polyp')."
    )
    
    laterality: Optional[str] = Field(
        None,
        max_length=20,
        description="Side if applicable: 'left', 'right', 'bilateral', 'midline'."
    )
    
    specimen_size_cm: Optional[str] = Field(
        None,
        max_length=50,
        description="Specimen dimensions (e.g., '3.5 x 2.1 x 1.8 cm')."
    )
    
    blocks_submitted: Optional[int] = Field(
        None,
        ge=0,
        description="Number of tissue blocks submitted for processing."
    )
    
    blocks_examined: Optional[int] = Field(
        None,
        ge=0,
        description="Number of tissue blocks examined microscopically."
    )
    
    stains_performed: Optional[list[str]] = Field(
        None,
        description="Histological stains used. Include routine (H&E) and special stains. IHC markers should be listed in ihc_markers field."
    )
    
    ihc_markers: Optional[list[str]] = Field(
        None,
        description="Immunohistochemistry markers tested (e.g., 'Ki-67', 'p53', 'CK7', 'CK20', 'CDX2', 'TTF-1', 'ER', 'PR', 'HER2')."
    )
    
    ihc_results: Optional[dict[str, str]] = Field(
        None,
        description="IHC results as marker:result pairs (e.g., {'Ki-67': '15%', 'p53': 'wild-type pattern', 'CK7': 'positive'})."
    )
    
    molecular_tests: Optional[list[str]] = Field(
        None,
        description="Molecular/genetic tests performed (e.g., 'KRAS', 'BRAF', 'MSI', 'PDL1', 'NGS panel')."
    )
    
    molecular_results: Optional[dict[str, str]] = Field(
        None,
        description="Molecular test results as test:result pairs (e.g., {'KRAS': 'G12D mutation', 'MSI': 'stable'})."
    )
    
    tumor_grade: Optional[str] = Field(
        None,
        max_length=100,
        description="Histologic grade if applicable (e.g., 'well-differentiated', 'moderately differentiated', 'poorly differentiated', 'Grade 2', 'Gleason 3+4=7')."
    )
    
    margins: Optional[str] = Field(
        None,
        max_length=100,
        description="Surgical margin status: 'negative', 'positive', 'close (<1mm)', or specific measurement."
    )
    
    lymph_nodes_examined: Optional[int] = Field(
        None,
        ge=0,
        description="Total number of lymph nodes examined."
    )
    
    lymph_nodes_positive: Optional[int] = Field(
        None,
        ge=0,
        description="Number of lymph nodes with metastatic disease."
    )
    
    lymphovascular_invasion: Optional[bool] = Field(
        None,
        description="Whether lymphovascular invasion is present."
    )
    
    perineural_invasion: Optional[bool] = Field(
        None,
        description="Whether perineural invasion is present."
    )


class EndoscopyDetails(BaseModel):
    """
    Endoscopy-specific metadata for GI, pulmonary, and urologic endoscopy.
    Extract these details when document_type is ENDOSCOPY.
    """
    
    procedure_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Specific endoscopic procedure: 'EGD', 'colonoscopy', 'sigmoidoscopy', 'ERCP', 'EUS', 'bronchoscopy', 'cystoscopy', 'enteroscopy', 'capsule_endoscopy'."
    )
    
    indication: Optional[str] = Field(
        None,
        max_length=300,
        description="Clinical indication for the procedure."
    )
    
    scope_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Type of endoscope used (e.g., 'standard gastroscope', 'pediatric colonoscope', 'linear EUS', 'radial EUS', 'therapeutic duodenoscope')."
    )
    
    sedation_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Type of sedation: 'none', 'topical', 'moderate_sedation', 'MAC', 'general_anesthesia'."
    )
    
    sedation_medications: Optional[list[str]] = Field(
        None,
        description="Sedation medications used (e.g., 'midazolam', 'fentanyl', 'propofol')."
    )
    
    extent_of_exam: Optional[str] = Field(
        None,
        max_length=200,
        description="How far the scope was advanced (e.g., 'to second portion of duodenum', 'to cecum', 'to terminal ileum')."
    )
    
    completion_status: Optional[str] = Field(
        None,
        max_length=50,
        description="Whether procedure was completed: 'complete', 'incomplete', 'aborted'. If incomplete, reason should be noted."
    )
    
    incomplete_reason: Optional[str] = Field(
        None,
        max_length=200,
        description="Reason for incomplete procedure if applicable (e.g., 'poor preparation', 'patient intolerance', 'obstruction')."
    )
    
    bowel_prep_quality: Optional[str] = Field(
        None,
        max_length=50,
        description="Bowel preparation quality for colonoscopy: 'excellent', 'good', 'fair', 'poor', 'inadequate', or Boston Bowel Prep Score."
    )
    
    boston_prep_score: Optional[int] = Field(
        None,
        ge=0,
        le=9,
        description="Boston Bowel Preparation Scale score (0-9) if documented."
    )
    
    withdrawal_time_minutes: Optional[int] = Field(
        None,
        ge=0,
        description="Colonoscopy withdrawal time in minutes."
    )
    
    biopsy_performed: Optional[bool] = Field(
        None,
        description="Whether biopsy was taken during the procedure."
    )
    
    biopsy_sites: Optional[list[str]] = Field(
        None,
        description="Anatomic locations where biopsies were taken."
    )
    
    therapeutic_interventions: Optional[list[str]] = Field(
        None,
        description="Therapeutic procedures performed: 'polypectomy', 'EMR', 'ESD', 'dilation', 'stent_placement', 'hemostasis', 'foreign_body_removal', 'sphincterotomy', 'stone_extraction'."
    )
    
    polyps_found: Optional[int] = Field(
        None,
        ge=0,
        description="Number of polyps found."
    )
    
    polyps_removed: Optional[int] = Field(
        None,
        ge=0,
        description="Number of polyps removed."
    )
    
    largest_polyp_size_mm: Optional[int] = Field(
        None,
        ge=0,
        description="Size of largest polyp in millimeters."
    )
    
    complications: Optional[list[str]] = Field(
        None,
        description="Any complications during procedure: 'bleeding', 'perforation', 'aspiration', 'adverse_sedation_event'."
    )


class LaboratoryDetails(BaseModel):
    """
    Laboratory-specific metadata for lab test results.
    Extract these details when document_type is LABORATORY.
    """
    
    panel_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Type of lab panel: 'CBC', 'BMP', 'CMP', 'LFT', 'lipid_panel', 'thyroid_panel', 'coagulation', 'tumor_markers', 'urinalysis', 'CSF_analysis', 'ABG'."
    )
    
    sample_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Type of sample: 'serum', 'plasma', 'whole_blood', 'urine', 'CSF', 'stool', 'sputum', 'wound_swab', 'tissue', 'bone_marrow'."
    )
    
    collection_time: Optional[str] = Field(
        None,
        max_length=50,
        description="Time of sample collection if relevant (e.g., 'fasting', '2-hour post-prandial', 'random', 'trough_level')."
    )
    
    fasting_status: Optional[bool] = Field(
        None,
        description="Whether patient was fasting for sample collection."
    )
    
    tests_performed: Optional[list[str]] = Field(
        None,
        description="List of specific tests performed."
    )
    
    critical_values: Optional[list[str]] = Field(
        None,
        description="Any critical/panic values flagged in results."
    )
    
    culture_organism: Optional[str] = Field(
        None,
        max_length=200,
        description="Organism identified in culture if applicable."
    )
    
    antibiotic_sensitivities: Optional[dict[str, str]] = Field(
        None,
        description="Antibiotic sensitivity results as antibiotic:sensitivity pairs (e.g., {'ampicillin': 'resistant', 'ciprofloxacin': 'sensitive'})."
    )


class OperativeDetails(BaseModel):
    """
    Operative/surgical report-specific metadata.
    Extract these details when document_type is OPERATIVE.
    """
    
    procedure_name: Optional[str] = Field(
        None,
        max_length=300,
        description="Name of surgical procedure performed (e.g., 'Laparoscopic cholecystectomy', 'Whipple procedure', 'Total hip arthroplasty')."
    )
    
    procedure_codes: Optional[list[str]] = Field(
        None,
        description="CPT or ICD-PCS procedure codes if documented."
    )
    
    primary_surgeon: Optional[str] = Field(
        None,
        max_length=100,
        description="Name of primary/attending surgeon."
    )
    
    surgical_approach: Optional[str] = Field(
        None,
        max_length=100,
        description="Surgical approach: 'open', 'laparoscopic', 'robotic', 'endoscopic', 'percutaneous', 'thoracoscopic', 'arthroscopic', 'hybrid'."
    )
    
    anesthesia_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Type of anesthesia: 'general', 'regional', 'spinal', 'epidural', 'local', 'MAC'."
    )
    
    patient_positioning: Optional[str] = Field(
        None,
        max_length=100,
        description="Patient position during surgery: 'supine', 'prone', 'lateral', 'lithotomy', 'trendelenburg'."
    )
    
    incision_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Type and location of incision (e.g., 'midline laparotomy', 'Pfannenstiel', 'right subcostal')."
    )
    
    operative_time_minutes: Optional[int] = Field(
        None,
        ge=0,
        description="Total operative time in minutes (skin-to-skin or cut-to-close)."
    )
    
    estimated_blood_loss_ml: Optional[int] = Field(
        None,
        ge=0,
        description="Estimated blood loss during surgery in milliliters."
    )
    
    transfusion_given: Optional[bool] = Field(
        None,
        description="Whether blood transfusion was given."
    )
    
    transfusion_units: Optional[int] = Field(
        None,
        ge=0,
        description="Number of blood product units transfused."
    )
    
    specimens_collected: Optional[list[str]] = Field(
        None,
        description="Specimens sent to pathology (e.g., 'gallbladder', 'appendix', 'lymph nodes')."
    )
    
    implants_used: Optional[list[str]] = Field(
        None,
        description="Implants or devices placed (e.g., 'mesh', 'prosthetic valve', 'joint prosthesis', 'stent')."
    )
    
    drains_placed: Optional[list[str]] = Field(
        None,
        description="Surgical drains placed (e.g., 'JP drain', 'chest tube', 'Foley catheter')."
    )
    
    intraoperative_findings: Optional[str] = Field(
        None,
        max_length=500,
        description="Key intraoperative findings described by surgeon."
    )
    
    complications: Optional[list[str]] = Field(
        None,
        description="Intraoperative complications if any."
    )
    
    closure_technique: Optional[str] = Field(
        None,
        max_length=200,
        description="Wound closure technique (e.g., 'running absorbable sutures', 'staples', 'subcuticular')."
    )


class DischargeDetails(BaseModel):
    """
    Discharge summary-specific metadata.
    Extract these details when document_type is DISCHARGE.
    """
    
    admission_date: Optional[date] = Field(
        None,
        description="Date of hospital admission."
    )
    
    discharge_date: Optional[date] = Field(
        None,
        description="Date of hospital discharge."
    )
    
    length_of_stay_days: Optional[int] = Field(
        None,
        ge=0,
        description="Total length of hospital stay in days."
    )
    
    admission_source: Optional[str] = Field(
        None,
        max_length=100,
        description="Where patient was admitted from: 'emergency_department', 'direct_admission', 'transfer', 'clinic', 'operating_room'."
    )
    
    admission_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Type of admission: 'emergency', 'urgent', 'elective', 'observation'."
    )
    
    admitting_diagnosis: Optional[str] = Field(
        None,
        max_length=300,
        description="Primary diagnosis at time of admission."
    )
    
    principal_diagnosis: Optional[str] = Field(
        None,
        max_length=300,
        description="Principal/primary diagnosis at discharge."
    )
    
    secondary_diagnoses: Optional[list[str]] = Field(
        None,
        description="Secondary diagnoses at discharge."
    )
    
    procedures_performed: Optional[list[str]] = Field(
        None,
        description="Major procedures performed during hospitalization."
    )
    
    discharge_disposition: Optional[str] = Field(
        None,
        max_length=100,
        description="Discharge destination: 'home', 'home_with_services', 'SNF', 'rehab', 'LTAC', 'hospice', 'AMA', 'expired', 'transfer'."
    )
    
    discharge_condition: Optional[str] = Field(
        None,
        max_length=50,
        description="Patient condition at discharge: 'stable', 'improved', 'unchanged', 'guarded', 'critical'."
    )
    
    follow_up_appointments: Optional[list[str]] = Field(
        None,
        description="Scheduled follow-up appointments with specialty and timeframe."
    )
    
    discharge_medications: Optional[list[str]] = Field(
        None,
        description="Medications prescribed at discharge."
    )
    
    new_medications: Optional[list[str]] = Field(
        None,
        description="New medications started during admission."
    )
    
    discontinued_medications: Optional[list[str]] = Field(
        None,
        description="Medications stopped during admission."
    )
    
    activity_restrictions: Optional[str] = Field(
        None,
        max_length=300,
        description="Activity restrictions at discharge."
    )
    
    diet_instructions: Optional[str] = Field(
        None,
        max_length=200,
        description="Dietary instructions at discharge."
    )
    
    wound_care_instructions: Optional[str] = Field(
        None,
        max_length=300,
        description="Wound care instructions if applicable."
    )
    
    warning_signs: Optional[list[str]] = Field(
        None,
        description="Red flag symptoms to watch for and return to care."
    )
    
    code_status: Optional[str] = Field(
        None,
        max_length=50,
        description="Code status at discharge: 'full_code', 'DNR', 'DNR_DNI', 'comfort_care'."
    )


class ClinicalNoteDetails(BaseModel):
    """
    Clinical note-specific metadata for progress notes, H&P, consultations.
    Extract these details when document_type is CLINICAL_NOTE.
    """
    
    note_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Type of clinical note: 'H&P', 'progress_note', 'consultation', 'follow_up', 'telephone_encounter', 'ED_note', 'pre_op', 'post_op'."
    )
    
    specialty: Optional[str] = Field(
        None,
        max_length=100,
        description="Medical specialty of the note author (e.g., 'oncology', 'cardiology', 'surgery', 'primary_care')."
    )
    
    encounter_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Type of encounter: 'inpatient', 'outpatient', 'emergency', 'observation', 'telehealth', 'home_visit'."
    )
    
    chief_complaint: Optional[str] = Field(
        None,
        max_length=300,
        description="Patient's chief complaint or reason for visit."
    )
    
    vital_signs: Optional[dict[str, str]] = Field(
        None,
        description="Vital signs as name:value pairs (e.g., {'BP': '120/80', 'HR': '72', 'Temp': '37.2', 'SpO2': '98%'})."
    )
    
    physical_exam_performed: Optional[bool] = Field(
        None,
        description="Whether physical examination was performed."
    )
    
    assessment_plan_documented: Optional[bool] = Field(
        None,
        description="Whether assessment and plan are documented."
    )
    
    number_of_problems: Optional[int] = Field(
        None,
        ge=0,
        description="Number of problems addressed in the note."
    )
    
    follow_up_interval: Optional[str] = Field(
        None,
        max_length=100,
        description="Recommended follow-up interval (e.g., '2 weeks', '1 month', 'PRN')."
    )


# =============================================================================
# MODALITY MODEL
# =============================================================================

class ExtractedModality(BaseModel):
    """
    A single modality or study found in the clinical document.
    
    Each document may contain multiple modalities (e.g., a radiology report covering
    both CT Chest and CT Abdomen, or a pathology report with multiple specimens).
    
    The 'index' field is used to link diseases and abnormalities to specific modalities
    within the document.
    """
    
    index: int = Field(
        ...,
        ge=0,
        description="Zero-based index for this modality within the document. Used by diseases and abnormalities to reference which modality they belong to. First modality is 0, second is 1, etc."
    )
    
    code: ModalityCode = Field(
        ...,
        description="Standardized modality code from the ModalityCode enum. Use the most specific code applicable."
    )
    
    name: str = Field(
        ...,
        max_length=300,
        description="Full modality/study name as stated in the document (e.g., 'CT Abdomen and Pelvis with IV Contrast', 'Colonoscopy with polypectomy', 'Core biopsy of liver mass')."
    )
    
    body_region: Optional[BodyRegion] = Field(
        None,
        description="Primary anatomical region examined. Select from BodyRegion enum. May be None for laboratory tests."
    )
    
    # Type-specific details - populate based on document_type
    radiology_details: Optional[RadiologyDetails] = Field(
        None,
        description="Radiology-specific metadata. Populate when modality code is an imaging modality (CT, MRI, US, XRAY, PET, etc.)."
    )
    
    pathology_details: Optional[PathologyDetails] = Field(
        None,
        description="Pathology-specific metadata. Populate when modality code is PATH or CYTO."
    )
    
    endoscopy_details: Optional[EndoscopyDetails] = Field(
        None,
        description="Endoscopy-specific metadata. Populate when modality code is ENDO, EGD, COLON, ERCP, EUS, BRONCH, or CYSTO."
    )
    
    laboratory_details: Optional[LaboratoryDetails] = Field(
        None,
        description="Laboratory-specific metadata. Populate when modality code is LAB, MICRO, or MOLECULAR."
    )
    
    operative_details: Optional[OperativeDetails] = Field(
        None,
        description="Operative-specific metadata. Populate when modality code is SURGERY."
    )


# =============================================================================
# DISEASE AND ABNORMALITY MODELS
# =============================================================================

class ExtractedDisease(BaseModel):
    """
    A single disease or diagnosis extracted from the document.
    
    This is the atomic unit of extraction - one row per disease mention.
    A document may contain multiple disease mentions.
    """
    
    disease_name_original: str = Field(
        ...,
        max_length=500,
        description="Disease name exactly as written in the source document, preserving original language (Persian or English) and exact wording. Do not translate or standardize."
    )
    
    disease_name_english: str = Field(
        ...,
        max_length=500,
        description="Standardized disease name in English. Use standard medical terminology. For example: 'آدنوکارسینوم پانکراس' becomes 'Pancreatic Adenocarcinoma'."
    )
    
    modality_index: int = Field(
        ...,
        ge=0,
        description="Index into the modalities array indicating which modality/study this disease was found in. Must match an existing modality's index value."
    )
    
    temporality: Temporality = Field(
        ...,
        description="Temporal status of the disease. CURRENT = active now, HISTORICAL = past, SUSPECTED = under investigation, RULED_OUT = excluded, etc. See Temporality enum for full list."
    )
    
    temporal_expression: Optional[str] = Field(
        None,
        max_length=200,
        description="Raw temporal phrase from the text if present (e.g., 'diagnosed 3 years ago', 'since 2020', 'new finding', 'post-chemotherapy'). Extract verbatim."
    )
    
    onset_date: Optional[date] = Field(
        None,
        description="Computed date of disease onset if determinable from temporal expression and document date. Format: YYYY-MM-DD. Leave None if cannot be reliably computed."
    )
    
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score for this extraction (0.0 to 1.0). High confidence (>0.9) for clearly stated diagnoses, lower for inferred or ambiguous findings."
    )
    
    extracted_text_snippet: Optional[str] = Field(
        None,
        max_length=500,
        description="Brief excerpt from source text where disease was mentioned. Useful for verification. Limit to relevant sentence(s)."
    )


class ExtractedAbnormality(BaseModel):
    """
    A non-disease abnormality or incidental finding.
    
    These are findings that are not diseases themselves but are clinically notable.
    Examples: surgical clips, anatomical variants, old granulomas, implanted devices.
    """
    
    name: str = Field(
        ...,
        max_length=200,
        description="Abnormality name in snake_case English (e.g., 'surgical_clips', 'gallstones', 'pacemaker', 'anatomical_variant', 'old_granuloma', 'simple_cyst')."
    )
    
    name_original: Optional[str] = Field(
        None,
        max_length=200,
        description="Original abnormality description as written in source document, preserving original language."
    )
    
    anatomy: Optional[str] = Field(
        None,
        max_length=200,
        description="Anatomical location of the abnormality in snake_case (e.g., 'gallbladder_fossa', 'right_lung_apex', 'left_kidney', 'anterior_chest_wall')."
    )
    
    severity: Severity = Field(
        ...,
        description="Clinical significance of the abnormality. MINIMAL = incidental/benign, MILD = may need monitoring, MODERATE = needs attention, SIGNIFICANT = requires action, SEVERE = urgent."
    )
    
    modality_index: int = Field(
        ...,
        ge=0,
        description="Index into the modalities array indicating which modality/study this abnormality was found in."
    )
    
    description: Optional[str] = Field(
        None,
        max_length=300,
        description="Additional descriptive details about the abnormality."
    )
    
    size_cm: Optional[str] = Field(
        None,
        max_length=50,
        description="Size of abnormality if measurable (e.g., '1.2 cm', '3 x 2 cm')."
    )
    
    recommendation: Optional[str] = Field(
        None,
        max_length=200,
        description="Any follow-up recommendation mentioned for this abnormality."
    )


# =============================================================================
# DOCUMENT-LEVEL EXTRACTION RESULT
# =============================================================================

class DocumentExtractionResult(BaseModel):
    """
    Complete extraction result for a clinical document.
    
    This is the primary output schema for LLM extraction. It captures:
    1. Document-level information (type, modalities)
    2. All diseases mentioned with their temporal status
    3. Non-disease abnormalities/incidental findings
    4. Patient age if mentioned
    
    Use this schema as the structured output format for LLM extraction calls.
    """
    
    document_type: DocumentType = Field(
        ...,
        description="Primary type of this clinical document. Determines which type-specific metadata fields are applicable. RADIOLOGY for imaging, PATHOLOGY for tissue analysis, LABORATORY for lab tests, ENDOSCOPY for endoscopic procedures, OPERATIVE for surgery reports, DISCHARGE for discharge summaries, CLINICAL_NOTE for progress notes and consultations."
    )
    
    modalities: list[ExtractedModality] = Field(
        ...,
        min_length=1,
        description="List of modalities/studies in this document. Most documents have one modality, but some may have multiple (e.g., CT Chest and CT Abdomen in same report, or multiple pathology specimens). Each modality has an index (starting at 0) used to link diseases and abnormalities."
    )
    
    diseases: list[ExtractedDisease] = Field(
        default_factory=list,
        description="List of diseases/diagnoses extracted from the document. May be empty if document contains only normal findings or incidental abnormalities. Each disease links to a modality via modality_index."
    )
    
    abnormalities: list[ExtractedAbnormality] = Field(
        default_factory=list,
        description="List of non-disease abnormalities and incidental findings. Examples: surgical clips, anatomical variants, benign cysts, implanted devices. May be empty. Each links to a modality via modality_index."
    )
    
    patient_age: Optional[int] = Field(
        None,
        ge=0,
        le=150,
        description="Patient's age in years at the time of this document, if mentioned in the text. Extract numeric age only (e.g., '65-year-old man' → 65)."
    )
    
    patient_sex: Optional[str] = Field(
        None,
        max_length=20,
        description="Patient's sex if mentioned: 'male', 'female', or as stated."
    )
    
    clinical_indication: Optional[str] = Field(
        None,
        max_length=500,
        description="Clinical indication or reason for the study/procedure if stated in the document."
    )
    
    impression_summary: Optional[str] = Field(
        None,
        max_length=1000,
        description="Brief summary of the overall impression or conclusion from the document in standardized English."
    )
    
    # Document-level type-specific details
    discharge_details: Optional[DischargeDetails] = Field(
        None,
        description="Discharge-specific metadata. Populate when document_type is DISCHARGE."
    )
    
    clinical_note_details: Optional[ClinicalNoteDetails] = Field(
        None,
        description="Clinical note-specific metadata. Populate when document_type is CLINICAL_NOTE."
    )

    @field_validator('diseases', 'abnormalities')
    @classmethod
    def validate_modality_indices(cls, items: list, info) -> list:
        """Validate that modality_index references exist."""
        # Note: In production, you'd validate against actual modalities
        return items


# =============================================================================
# DATABASE ENTITY MODELS
# =============================================================================

class PersonCreate(BaseModel):
    """Model for creating a new person record."""
    person_source_id: str = Field(..., max_length=100)
    birth_year: Optional[int] = Field(None, ge=1900, le=2100)
    gender: Optional[Gender] = None


class PersonRead(PersonCreate):
    """Model for reading a person record."""
    person_id: int
    created_at: datetime


class DataSourceCreate(BaseModel):
    """Model for creating a new data source record."""
    source_code: str = Field(..., max_length=50)
    source_name: str = Field(..., max_length=200)
    source_type: SourceType
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    country: str = Field(default="Iran", max_length=100)
    is_active: bool = True


class DataSourceRead(DataSourceCreate):
    """Model for reading a data source record."""
    source_id: int


class ClinicalDocumentCreate(BaseModel):
    """Model for creating a new clinical document record."""
    person_id: int
    source_id: int
    document_source_id: str = Field(..., max_length=100)
    document_source_url: Optional[str] = Field(None, max_length=500)
    document_date: date
    document_type: DocumentType
    source_language: SourceLanguage
    modalities: list[dict[str, Any]] = Field(default_factory=list)
    abnormalities: list[dict[str, Any]] = Field(default_factory=list)
    document_text: Optional[str] = None
    text_hash: Optional[str] = Field(None, max_length=64)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING


class ClinicalDocumentRead(ClinicalDocumentCreate):
    """Model for reading a clinical document record."""
    document_id: int
    created_at: datetime


class DiseaseExtractionCreate(BaseModel):
    """Model for creating a new disease extraction record."""
    document_id: int
    person_id: int
    modality_index: int = Field(..., ge=0)
    disease_name_original: str = Field(..., max_length=500)
    disease_name_english: str = Field(..., max_length=500)
    icd_mapping_id: Optional[int] = None
    icd_code: Optional[str] = Field(None, max_length=20)
    temporality: Temporality
    temporal_expression: Optional[str] = Field(None, max_length=200)
    onset_date: Optional[date] = None
    patient_age_at_document: Optional[int] = Field(None, ge=0, le=150)
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    schema_id: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None
    extracted_text_snippet: Optional[str] = Field(None, max_length=500)
    processing_log_id: Optional[int] = None


class DiseaseExtractionRead(DiseaseExtractionCreate):
    """Model for reading a disease extraction record."""
    extraction_id: int
    created_at: datetime


class DiseaseSchemaCreate(BaseModel):
    """Model for creating a new disease schema record."""
    disease_name: str = Field(..., max_length=500)
    icd_code: Optional[str] = Field(None, max_length=20)
    schema_version: int = Field(default=1, ge=1)
    field_definitions: list[dict[str, Any]]
    pydantic_class_code: Optional[str] = None
    sample_count: int = Field(default=0, ge=0)
    is_active: bool = True
    processing_log_id: Optional[int] = None


class DiseaseSchemaRead(DiseaseSchemaCreate):
    """Model for reading a disease schema record."""
    schema_id: int
    created_at: datetime
    updated_at: datetime


class ICDMappingCreate(BaseModel):
    """Model for creating a new ICD mapping record."""
    disease_name_normalized: str = Field(..., max_length=500)
    disease_name_display: str = Field(..., max_length=500)
    icd_code: Optional[str] = Field(None, max_length=20)
    icd_description: Optional[str] = Field(None, max_length=500)
    match_status: ICDMatchStatus
    match_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    candidates_json: Optional[list[dict[str, Any]]] = None
    selection_reasoning: Optional[str] = None
    created_by_model: Optional[str] = Field(None, max_length=100)


class ICDMappingRead(ICDMappingCreate):
    """Model for reading an ICD mapping record."""
    mapping_id: int
    created_at: datetime
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None


class ProcessingLogCreate(BaseModel):
    """Model for creating a new processing log record."""
    document_id: Optional[int] = None
    pipeline_stage: PipelineStage
    pipeline_version: str = Field(..., max_length=50)
    status: PipelineStatus = PipelineStatus.PENDING
    error_message: Optional[str] = None
    error_type: Optional[str] = Field(None, max_length=100)
    retry_count: int = Field(default=0, ge=0)
    llm_provider: Optional[str] = Field(None, max_length=50)
    llm_model: Optional[str] = Field(None, max_length=100)
    prompt_template_id: Optional[str] = Field(None, max_length=100)
    token_count_input: Optional[int] = Field(None, ge=0)
    token_count_output: Optional[int] = Field(None, ge=0)


class ProcessingLogRead(ProcessingLogCreate):
    """Model for reading a processing log record."""
    log_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class SchemaGenerationQueueCreate(BaseModel):
    """Model for creating a new schema generation queue record."""
    disease_name: str = Field(..., max_length=500)
    icd_code: Optional[str] = Field(None, max_length=20)
    sample_document_ids: list[int] = Field(default_factory=list)
    sample_count: int = Field(default=1, ge=1)
    status: QueueStatus = QueueStatus.PENDING


class SchemaGenerationQueueRead(SchemaGenerationQueueCreate):
    """Model for reading a schema generation queue record."""
    queue_id: int
    created_at: datetime
    processed_at: Optional[datetime] = None


class ICDEmbeddingCreate(BaseModel):
    """Model for creating a new ICD embedding record."""
    icd_code: str = Field(..., max_length=20)
    icd_description: str = Field(..., max_length=500)
    embedding: list[float]
    embedding_model: str = Field(..., max_length=100)


class ICDEmbeddingRead(ICDEmbeddingCreate):
    """Model for reading an ICD embedding record."""
    embedding_id: int


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_disease_name(name: str) -> str:
    """
    Normalize a disease name for ICD mapping lookup.
    
    Args:
        name: Raw disease name in English
        
    Returns:
        Normalized name (lowercase, trimmed, single spaces)
    """
    import re
    normalized = name.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def create_extraction_from_llm_result(
    result: DocumentExtractionResult,
    document_id: int,
    person_id: int,
    document_date: date
) -> list[DiseaseExtractionCreate]:
    """
    Convert LLM extraction result to database-ready extraction records.
    
    Args:
        result: DocumentExtractionResult from LLM
        document_id: ID of the clinical document
        person_id: ID of the patient
        document_date: Date of the document
        
    Returns:
        List of DiseaseExtractionCreate records ready for database insertion
    """
    extractions = []
    
    for disease in result.diseases:
        extraction = DiseaseExtractionCreate(
            document_id=document_id,
            person_id=person_id,
            modality_index=disease.modality_index,
            disease_name_original=disease.disease_name_original,
            disease_name_english=disease.disease_name_english,
            temporality=disease.temporality,
            temporal_expression=disease.temporal_expression,
            onset_date=disease.onset_date,
            patient_age_at_document=result.patient_age,
            confidence=Decimal(str(disease.confidence)) if disease.confidence else None,
            extracted_text_snippet=disease.extracted_text_snippet
        )
        extractions.append(extraction)
    
    return extractions


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example: Creating a DocumentExtractionResult for a CT scan
    example_result = DocumentExtractionResult(
        document_type=DocumentType.RADIOLOGY,
        modalities=[
            ExtractedModality(
                index=0,
                code=ModalityCode.CT,
                name="CT Abdomen and Pelvis with IV Contrast",
                body_region=BodyRegion.ABDOMEN_PELVIS,
                radiology_details=RadiologyDetails(
                    contrast_iv=True,
                    contrast_phases=["arterial", "portal_venous"],
                    technique="multiphasic CT"
                )
            )
        ],
        diseases=[
            ExtractedDisease(
                disease_name_original="توده در سر پانکراس",
                disease_name_english="Pancreatic Head Mass",
                modality_index=0,
                temporality=Temporality.CURRENT,
                confidence=0.95,
                extracted_text_snippet="There is a 3.2 cm mass in the pancreatic head."
            )
        ],
        abnormalities=[
            ExtractedAbnormality(
                name="surgical_clips",
                anatomy="gallbladder_fossa",
                severity=Severity.MINIMAL,
                modality_index=0,
                description="Cholecystectomy clips noted"
            )
        ],
        patient_age=67,
        patient_sex="male",
        clinical_indication="Elevated CA 19-9, evaluate for pancreatic pathology"
    )
    
    # Print JSON schema for LLM
    print("=== DocumentExtractionResult JSON Schema ===")
    print(DocumentExtractionResult.model_json_schema())
