-- ============================================================
-- PhytoAMP — Esquema Relacional PostgreSQL
-- Banco de dados orientado a ensaio (assay-level) para AMPs
-- contra fitopatógenos de relevância agrícola
-- Dissertação de Mestrado — SENAI CIMATEC
-- ============================================================
-- Versão: v0.1
-- Autor:  PhytoAMP Team
-- Data:   2025
-- ============================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- similaridade de texto
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- índices em JSONB

-- ────────────────────────────────────────────────────────────
-- TABELA 0 — Dataset Version
-- Controle de versão do dataset
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dataset_version (
    version_id      SERIAL PRIMARY KEY,
    version_tag     VARCHAR(32) UNIQUE NOT NULL,  -- e.g. 'v0', 'v1.0'
    frozen_at       TIMESTAMP WITH TIME ZONE DEFAULT now(),
    description     TEXT,
    record_count    INTEGER,
    trainable_count INTEGER,
    notes           TEXT
);

-- ────────────────────────────────────────────────────────────
-- TABELA 1 — reference
-- Referências bibliográficas / fontes de dados
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reference (
    reference_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doi             VARCHAR(256) UNIQUE,
    pubmed_id       VARCHAR(32),
    source_db       VARCHAR(64),   -- DBAASP, DRAMP, dbAMP, APD6, CAMPR4, LAMP2, PubMed, etc.
    title           TEXT,
    authors         TEXT,
    journal         VARCHAR(256),
    year            SMALLINT,
    language        VARCHAR(16) DEFAULT 'en',
    record_type     VARCHAR(32) CHECK (record_type IN (
                        'article', 'thesis', 'patent', 'database_entry', 'supplement', 'tool_doc'
                    )),
    url             TEXT,
    low_confidence  BOOLEAN DEFAULT FALSE,  -- artigos em língua não-inglesa traduzidos
    notes           TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX idx_reference_doi   ON reference(doi);
CREATE INDEX idx_reference_year  ON reference(year);

-- ────────────────────────────────────────────────────────────
-- TABELA 2 — peptide
-- Identidade molecular do peptídeo
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS peptide (
    peptide_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    internal_code       VARCHAR(64) UNIQUE NOT NULL,     -- código estável interno PhytoAMP-XXXXX
    name_primary        VARCHAR(256),
    synonyms            TEXT[],                          -- array de nomes alternativos
    sequence_fasta      TEXT NOT NULL,                   -- sequência em formato FASTA (apenas aa canônicos ou X)
    sequence_status     VARCHAR(32) NOT NULL CHECK (sequence_status IN (
                            'exact', 'partial', 'inferred', 'synthetic'
                        )),
    length_aa           SMALLINT GENERATED ALWAYS AS (length(sequence_fasta)) STORED,
    -- Regime químico (Dissertação: Regimes A/B/C/D)
    chemical_regime     CHAR(1) NOT NULL CHECK (chemical_regime IN ('A','B','C','D')),
    is_canonical        BOOLEAN NOT NULL DEFAULT TRUE,   -- apenas 20 aa padrão
    is_linear           BOOLEAN NOT NULL DEFAULT TRUE,   -- linear vs cíclico
    has_d_aminoacids    BOOLEAN DEFAULT FALSE,
    is_amidated         BOOLEAN DEFAULT FALSE,
    is_acetylated       BOOLEAN DEFAULT FALSE,
    has_disulfide       BOOLEAN DEFAULT FALSE,
    is_lipopeptide      BOOLEAN DEFAULT FALSE,
    is_nrp              BOOLEAN DEFAULT FALSE,           -- Non-Ribosomal Peptide
    is_ripp             BOOLEAN DEFAULT FALSE,           -- Ribosomally synthesized and Post-translationally modified Peptide
    -- Classe AMP (separado da classe química)
    amp_class           VARCHAR(128),    -- defensin, thionin, LTP, cyclotide, bacteriocin, etc.
    -- Classe química
    chemical_class      VARCHAR(128),    -- peptaibol, lipopeptide, NRP, synthetic, etc.
    biological_origin   TEXT,            -- espécie/gênero doador
    chebi_ids           TEXT[],          -- modificações via ChEBI
    go_terms            TEXT[],          -- GO do gene precursor
    smiles              TEXT,            -- SMILES quando houver (peptaibóis, NRPs)
    dataset_version_tag VARCHAR(32) REFERENCES dataset_version(version_tag),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX idx_peptide_regime    ON peptide(chemical_regime);
CREATE INDEX idx_peptide_canonical ON peptide(is_canonical);
CREATE INDEX idx_peptide_length    ON peptide(length_aa);
CREATE INDEX idx_peptide_seq_trgm  ON peptide USING gin(sequence_fasta gin_trgm_ops);

-- ────────────────────────────────────────────────────────────
-- TABELA 3 — peptide_chemistry
-- Descritores físico-químicos calculados
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS peptide_chemistry (
    chem_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    peptide_id      UUID NOT NULL REFERENCES peptide(peptide_id) ON DELETE CASCADE,
    net_charge      NUMERIC(6,2),         -- carga líquida calculada a pH 7
    pi              NUMERIC(6,2),         -- ponto isoelétrico
    hydrophobicity  NUMERIC(6,4),         -- índice de Kyte-Doolittle
    hydrophobic_moment NUMERIC(6,4),
    aromaticity     NUMERIC(6,4),
    aliphaticity    NUMERIC(6,4),
    instability_idx NUMERIC(6,2),
    gravy           NUMERIC(6,4),
    fraction_cationic  NUMERIC(5,4),
    fraction_hydrophobic NUMERIC(5,4),
    cys_count       SMALLINT,
    gly_count       SMALLINT,
    pro_count       SMALLINT,
    mw_daltons      NUMERIC(10,2),        -- massa molecular
    tool_version    VARCHAR(64),          -- modlAMP / iFeatureOmega
    computed_at     TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ────────────────────────────────────────────────────────────
-- TABELA 4 — target_pathogen
-- Organismo-alvo (fitopatógeno)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS target_pathogen (
    tax_id          INTEGER PRIMARY KEY,  -- NCBI Taxonomy ID
    species         VARCHAR(256) NOT NULL,
    genus           VARCHAR(128),
    family          VARCHAR(128),
    pathogen_type   VARCHAR(32) NOT NULL CHECK (pathogen_type IN (
                        'bacteria', 'true_fungi', 'oomycete', 'nematode', 'virus', 'other'
                    )),
    is_oomycete     BOOLEAN GENERATED ALWAYS AS (pathogen_type = 'oomycete') STORED,
    common_diseases TEXT[],               -- doenças associadas
    host_range      TEXT[],               -- hospedeiros vegetais principais
    notes           TEXT
);

-- ────────────────────────────────────────────────────────────
-- TABELA 5 — host_plant
-- Planta hospedeira / sistema de ensaio
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS host_plant (
    host_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tax_id          INTEGER,              -- NCBI Taxonomy
    species         VARCHAR(256),
    cultivar        VARCHAR(128),
    tissue_organ    VARCHAR(128),         -- folha, raiz, fruto, semente...
    growth_stage    VARCHAR(128),
    postharvest     BOOLEAN DEFAULT FALSE,
    notes           TEXT
);

-- ────────────────────────────────────────────────────────────
-- TABELA 6 — assay_condition
-- Condições experimentais do ensaio
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS assay_condition (
    condition_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    medium          VARCHAR(256),         -- RPMI, MH, PDA, etc.
    temperature_c   NUMERIC(5,1),
    ph              NUMERIC(4,2),
    inoculum_size   VARCHAR(128),         -- e.g. "5x10^5 CFU/mL"
    incubation_h    NUMERIC(6,1),         -- horas de incubação
    method          VARCHAR(128) CHECK (method IN (
                        'broth_microdilution', 'agar_diffusion', 'agar_dilution',
                        'detached_leaf', 'spray', 'infiltration', 'dip', 'drench',
                        'greenhouse', 'field', 'flow_cytometry', 'other'
                    )),
    protocol_standard VARCHAR(64) CHECK (protocol_standard IN (
                        'CLSI_M07', 'CLSI_M38', 'EUCAST', 'custom', 'not_reported'
                    )),
    n_replicates    SMALLINT,
    positive_control VARCHAR(256),
    negative_control VARCHAR(256),
    notes           TEXT
);

-- ────────────────────────────────────────────────────────────
-- TABELA 7 — activity_assay (TABELA CENTRAL — TREINÁVEL)
-- Registro de atividade biológica — unidade de treino
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activity_assay (
    assay_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    peptide_id          UUID NOT NULL REFERENCES peptide(peptide_id),
    tax_id              INTEGER NOT NULL REFERENCES target_pathogen(tax_id),
    reference_id        UUID NOT NULL REFERENCES reference(reference_id),
    condition_id        UUID REFERENCES assay_condition(condition_id),
    host_id             UUID REFERENCES host_plant(host_id),
    -- Localização no artigo
    figure_table_ref    VARCHAR(128),     -- e.g. "Table 2", "Figure 3A", "Suppl. S1"
    -- Tipo de experimento
    experiment_type     VARCHAR(64) CHECK (experiment_type IN (
                            'in_silico', 'in_vitro', 'ex_vivo', 'in_planta',
                            'greenhouse', 'field', 'product_formulation'
                        )),
    -- Endpoint principal
    endpoint_type       VARCHAR(32) NOT NULL CHECK (endpoint_type IN (
                            'MIC', 'MBC', 'MFC', 'IC50', 'EC50',
                            'pct_growth_inhibition', 'pct_spore_germination',
                            'halo_mm', 'lesion_reduction_pct', 'pathogen_load',
                            'plant_survival_pct', 'biofilm_inhibition_pct',
                            'membrane_permeabilization', 'ros_induction', 'other'
                        )),
    endpoint_value_raw  NUMERIC(12,4),    -- valor bruto exatamente como reportado
    endpoint_operator   CHAR(2) CHECK (endpoint_operator IN ('=', '>', '<', '>=', '<=')),
    endpoint_unit       VARCHAR(32),      -- µM, µg/mL, mg/L, mm, %, etc.
    endpoint_log2       NUMERIC(8,4),     -- log2(MIC) calculado quando aplicável
    concentration_range TEXT,             -- faixa testada (ex: "1–128 µg/mL")
    -- Controle de censura (MIC censurado)
    is_censored         BOOLEAN DEFAULT FALSE,
    censoring_direction VARCHAR(8) CHECK (censoring_direction IN ('left', 'right', 'none')),
    -- Elegibilidade para treino
    train_eligible      BOOLEAN NOT NULL DEFAULT FALSE,
    train_level         SMALLINT CHECK (train_level IN (1, 2, 3)),
    exclusion_reason    TEXT,             -- quando train_eligible = FALSE
    -- Zona cinzenta de atividade
    activity_zone       VARCHAR(16) CHECK (activity_zone IN ('active', 'grey', 'inactive', 'not_classified')),
    activity_threshold_used NUMERIC(10,4),
    -- Metadados de completude
    completeness_score  SMALLINT CHECK (completeness_score BETWEEN 0 AND 100),
    curator_notes       TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX idx_assay_peptide     ON activity_assay(peptide_id);
CREATE INDEX idx_assay_taxid       ON activity_assay(tax_id);
CREATE INDEX idx_assay_train       ON activity_assay(train_eligible, train_level);
CREATE INDEX idx_assay_endpoint    ON activity_assay(endpoint_type);
CREATE INDEX idx_assay_experiment  ON activity_assay(experiment_type);

-- ────────────────────────────────────────────────────────────
-- TABELA 8 — evidence_layer
-- Modelo ortogonal de evidência agrícola
-- Dissertação: 5 dimensões independentes (não colapsadas em escore único)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence_layer (
    evidence_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assay_id            UUID NOT NULL REFERENCES activity_assay(assay_id) ON DELETE CASCADE,
    -- Dimensão 1: Tipo de Evidência
    evidence_type       VARCHAR(64) CHECK (evidence_type IN (
                            'in_silico', 'in_vitro_microbiological',
                            'ex_vivo_detached_plant', 'in_planta',
                            'greenhouse', 'field', 'product_formulation'
                        )),
    -- Dimensão 2: Rigor Experimental
    experimental_rigor  VARCHAR(32) CHECK (experimental_rigor IN (
                            'exploratory', 'partially_standardized',
                            'standardized', 'well_controlled'
                        )),
    -- Dimensão 3: Relevância Agrícola
    agricultural_relevance VARCHAR(16) CHECK (agricultural_relevance IN (
                            'indirect', 'moderate', 'direct'
                        )),
    -- Dimensão 4: Identidade do Agente
    agent_identity      VARCHAR(32) CHECK (agent_identity IN (
                            'exact_sequence', 'partial_sequence',
                            'mixture', 'fraction', 'formulation'
                        )),
    -- Dimensão 5: Contexto de Aplicação
    application_context VARCHAR(64) CHECK (application_context IN (
                            'isolated_peptide', 'formulated_peptide',
                            'plant_expressed_peptide', 'consortium', 'recombinant_system'
                        )),
    -- Campos MIAPPE-inspirados para contexto em planta
    plant_species       VARCHAR(256),
    plant_cultivar      VARCHAR(128),
    plant_tissue        VARCHAR(128),
    plant_growth_stage  VARCHAR(128),
    environment_type    VARCHAR(32) CHECK (environment_type IN (
                            'in_vitro', 'greenhouse', 'field', 'postharvest', 'not_applicable'
                        )),
    treatment_description TEXT,
    observed_variable   TEXT,
    notes               TEXT
);

-- ────────────────────────────────────────────────────────────
-- TABELA 9 — toxicity_record
-- Avaliação de toxicidade (hemólise, citotox, fitotox)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS toxicity_record (
    toxicity_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    peptide_id          UUID NOT NULL REFERENCES peptide(peptide_id),
    reference_id        UUID REFERENCES reference(reference_id),
    toxicity_type       VARCHAR(32) CHECK (toxicity_type IN (
                            'hemolysis', 'cytotoxicity', 'phytotoxicity',
                            'mammalian_toxicity', 'aquatic_toxicity'
                        )),
    cell_or_system      VARCHAR(128),   -- e.g. "human erythrocytes", "Vero cells", "tomato leaf"
    endpoint_value      NUMERIC(12,4),
    endpoint_unit       VARCHAR(32),
    hc50_um             NUMERIC(10,4),  -- concentração 50% hemólise
    lc50_um             NUMERIC(10,4),
    selectivity_index   NUMERIC(10,4),  -- SI = HC50/MIC
    phytotoxic_status   VARCHAR(16) CHECK (phytotoxic_status IN (
                            'not_phytotoxic', 'mildly_phytotoxic',
                            'phytotoxic', 'not_tested', 'not_reported'
                        )),
    notes               TEXT
);

-- ────────────────────────────────────────────────────────────
-- TABELA 10 — stability_record
-- Estabilidade do peptídeo em diferentes condições
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stability_record (
    stability_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    peptide_id          UUID NOT NULL REFERENCES peptide(peptide_id),
    reference_id        UUID REFERENCES reference(reference_id),
    stability_type      VARCHAR(64) CHECK (stability_type IN (
                            'protease_stability', 'thermal_stability', 'salt_stability',
                            'ph_stability', 'apoplast_stability', 'environmental_stability',
                            'storage_stability'
                        )),
    condition_detail    TEXT,            -- ex: "37°C, 1h, trypsin 10 µg/mL"
    result_qualitative  VARCHAR(32) CHECK (result_qualitative IN (
                            'stable', 'partially_stable', 'unstable', 'not_tested', 'not_reported'
                        )),
    result_quantitative NUMERIC(10,4),
    result_unit         VARCHAR(32),
    half_life_h         NUMERIC(10,2),
    notes               TEXT
);

-- ────────────────────────────────────────────────────────────
-- TABELA 11 — mechanism_annotation
-- Modo de ação (campo controlado)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mechanism_annotation (
    mechanism_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    peptide_id          UUID NOT NULL REFERENCES peptide(peptide_id),
    reference_id        UUID REFERENCES reference(reference_id),
    membrane_disruption         BOOLEAN DEFAULT FALSE,
    pore_formation              BOOLEAN DEFAULT FALSE,
    cell_wall_interaction       BOOLEAN DEFAULT FALSE,
    dna_rna_binding             BOOLEAN DEFAULT FALSE,
    protein_synthesis_inhibition BOOLEAN DEFAULT FALSE,
    cell_wall_biosynthesis_inhib BOOLEAN DEFAULT FALSE,
    biofilm_effect              BOOLEAN DEFAULT FALSE,
    ros_induction               BOOLEAN DEFAULT FALSE,
    plant_defense_modulation    BOOLEAN DEFAULT FALSE,
    mechanism_mixed             BOOLEAN DEFAULT FALSE,
    mechanism_unclear           BOOLEAN DEFAULT FALSE,
    mechanism_notes             TEXT,
    confidence                  VARCHAR(16) CHECK (confidence IN (
                                    'high', 'moderate', 'low', 'inferred', 'not_stated'
                                ))
);

-- ────────────────────────────────────────────────────────────
-- TABELA 12 — feature_set / feature_value
-- Descritores e embeddings calculados (separados para flexibilidade)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feature_set (
    feature_set_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(128) UNIQUE NOT NULL,   -- e.g. "physicochemical_v1", "esm2_8M_v1"
    feature_type    VARCHAR(32) CHECK (feature_type IN (
                        'physicochemical', 'sequence_composition',
                        'structural', 'embedding_plm', 'embedding_amp', 'fingerprint'
                    )),
    tool_name       VARCHAR(128),
    tool_version    VARCHAR(64),
    n_dimensions    INTEGER,
    description     TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feature_value (
    fv_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    peptide_id      UUID NOT NULL REFERENCES peptide(peptide_id),
    feature_set_id  UUID NOT NULL REFERENCES feature_set(feature_set_id),
    feature_name    VARCHAR(128),        -- nome do descriptor individual
    value_scalar    NUMERIC(16,8),       -- para descritores únicos
    value_vector    JSONB,               -- para embeddings (vector armazenado como array JSON)
    computed_at     TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE (peptide_id, feature_set_id, feature_name)
);
CREATE INDEX idx_feature_value_peptide ON feature_value(peptide_id);
CREATE INDEX idx_feature_value_set     ON feature_value(feature_set_id);

-- ────────────────────────────────────────────────────────────
-- TABELA 13 — genomic_source / genomic_candidate
-- Pipeline genômico — braços bacteriano e fúngico
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS genomic_source (
    source_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tax_id          INTEGER NOT NULL,
    organism_name   VARCHAR(256) NOT NULL,
    strain          VARCHAR(128),
    assembly_accession VARCHAR(64),      -- NCBI Assembly accession
    genome_arm      VARCHAR(16) CHECK (genome_arm IN ('bacterial', 'fungal')),
    annotation_tool VARCHAR(64),         -- Bakta, PGAP, BRAKER3
    annotation_version VARCHAR(32),
    antismash_version  VARCHAR(16),
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS genomic_candidate (
    candidate_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id           UUID NOT NULL REFERENCES genomic_source(source_id),
    locus_tag           VARCHAR(128),
    predicted_sequence  TEXT,
    prediction_tool     VARCHAR(64),     -- Macrel, ampir, AMPcombi
    prediction_score    NUMERIC(6,4),
    bgc_id              VARCHAR(128),    -- ID do BGC (antiSMASH)
    bgc_type            VARCHAR(64),     -- NRPS, PKS, RiPP, ...
    has_signal_peptide  BOOLEAN,
    signalp_score       NUMERIC(6,4),
    is_secreted         BOOLEAN,
    apoplast_score      NUMERIC(6,4),
    has_transmembrane   BOOLEAN,
    n_tm_helices        SMALLINT,
    candidate_regime    CHAR(1) CHECK (candidate_regime IN ('A','B','C','D')),
    model_score         NUMERIC(6,4),    -- score do modelo PhytoAMP
    novelty_score       NUMERIC(6,4),    -- distância de candidatos conhecidos
    -- Flags de viabilidade translacional
    flag_length_ok      BOOLEAN,
    flag_canonical      BOOLEAN,
    flag_synthesizable  BOOLEAN,
    flag_low_phytotox   BOOLEAN,
    flag_low_hemolysis  BOOLEAN,
    flag_stable         BOOLEAN,
    pareto_rank         INTEGER,         -- rank na frente de Pareto
    priority_tier       SMALLINT CHECK (priority_tier IN (1, 2, 3)),
    curator_notes       TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX idx_gcand_source     ON genomic_candidate(source_id);
CREATE INDEX idx_gcand_pareto     ON genomic_candidate(pareto_rank);
CREATE INDEX idx_gcand_model_score ON genomic_candidate(model_score DESC);

-- ────────────────────────────────────────────────────────────
-- TABELA 14 — model_run / model_prediction
-- Rastreabilidade de execuções e predições
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_run (
    model_run_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name      VARCHAR(128) NOT NULL,  -- e.g. "RF_physicochemical_v1", "ESM2_classifier_v1"
    model_type      VARCHAR(64) CHECK (model_type IN (
                        'RandomForest', 'XGBoost', 'LogisticRegression',
                        'ESM2_classifier', 'ProtT5_classifier', 'AMP_BERT_finetuned',
                        'ranking', 'regression'
                    )),
    task            VARCHAR(32) CHECK (task IN (
                        'binary_classification', 'ranking', 'regression', 'ensemble'
                    )),
    feature_set_id  UUID REFERENCES feature_set(feature_set_id),
    split_type      VARCHAR(32) CHECK (split_type IN (
                        'random', 'peptide_id', 'homology_aware_80',
                        'homology_aware_60', 'homology_aware_40', 'holdout_source'
                    )),
    -- Métricas de desempenho
    auroc           NUMERIC(6,4),
    auprc           NUMERIC(6,4),
    f1              NUMERIC(6,4),
    mcc             NUMERIC(6,4),
    balanced_acc    NUMERIC(6,4),
    precision_at_10 NUMERIC(6,4),
    precision_at_20 NUMERIC(6,4),
    ndcg            NUMERIC(6,4),
    rmse_log2mic    NUMERIC(8,4),
    mae_log2mic     NUMERIC(8,4),
    pct_within_1dilution NUMERIC(6,4),
    -- Reprodutibilidade
    git_commit      VARCHAR(64),
    docker_image    VARCHAR(256),
    random_seed     INTEGER,
    hyperparams     JSONB,
    mlflow_run_id   VARCHAR(128),
    started_at      TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at    TIMESTAMP WITH TIME ZONE,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS model_prediction (
    prediction_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_run_id    UUID NOT NULL REFERENCES model_run(model_run_id),
    peptide_id      UUID REFERENCES peptide(peptide_id),
    candidate_id    UUID REFERENCES genomic_candidate(candidate_id),
    predicted_class SMALLINT CHECK (predicted_class IN (0, 1)),
    predicted_prob  NUMERIC(6,4),
    predicted_rank  INTEGER,
    predicted_mic_log2 NUMERIC(8,4),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CHECK (peptide_id IS NOT NULL OR candidate_id IS NOT NULL)
);
CREATE INDEX idx_pred_model    ON model_prediction(model_run_id);
CREATE INDEX idx_pred_peptide  ON model_prediction(peptide_id);
CREATE INDEX idx_pred_cand     ON model_prediction(candidate_id);

-- ────────────────────────────────────────────────────────────
-- TABELA 15 — curation_event
-- Audit trail de curadoria
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS curation_event (
    event_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type     VARCHAR(32) CHECK (entity_type IN (
                        'peptide', 'activity_assay', 'evidence_layer',
                        'toxicity_record', 'genomic_candidate'
                    )),
    entity_id       UUID NOT NULL,
    event_type      VARCHAR(32) CHECK (event_type IN (
                        'created', 'updated', 'excluded', 'level_change',
                        'merged', 'flagged', 'approved', 'version_frozen'
                    )),
    old_value       JSONB,
    new_value       JSONB,
    curator_name    VARCHAR(128),
    reason          TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX idx_curation_entity ON curation_event(entity_type, entity_id);
CREATE INDEX idx_curation_time   ON curation_event(created_at);

-- ────────────────────────────────────────────────────────────
-- VIEWS ÚTEIS
-- ────────────────────────────────────────────────────────────

-- View: registros treináveis de nível 1 com contexto completo
CREATE OR REPLACE VIEW vw_trainable_records AS
SELECT
    a.assay_id,
    p.peptide_id,
    p.internal_code,
    p.sequence_fasta,
    p.length_aa,
    p.chemical_regime,
    p.is_canonical,
    t.tax_id,
    t.species AS pathogen_species,
    t.pathogen_type,
    a.endpoint_type,
    a.endpoint_value_raw,
    a.endpoint_operator,
    a.endpoint_unit,
    a.endpoint_log2,
    a.is_censored,
    a.activity_zone,
    a.experiment_type,
    r.doi,
    r.source_db
FROM activity_assay a
JOIN peptide p           ON p.peptide_id  = a.peptide_id
JOIN target_pathogen t   ON t.tax_id      = a.tax_id
JOIN reference r         ON r.reference_id = a.reference_id
WHERE a.train_eligible = TRUE AND a.train_level = 1;

-- View: contagem honesta do dataset (Dissertação: Mês 1 / Etapa Piloto)
CREATE OR REPLACE VIEW vw_dataset_stats AS
SELECT
    COUNT(DISTINCT p.peptide_id)                                    AS total_peptides,
    COUNT(DISTINCT a.assay_id)                                      AS total_assays,
    COUNT(DISTINCT CASE WHEN a.train_eligible THEN a.assay_id END)  AS trainable_assays,
    COUNT(DISTINCT CASE WHEN a.train_level=1 THEN a.assay_id END)   AS level1_assays,
    COUNT(DISTINCT CASE WHEN a.train_level=2 THEN a.assay_id END)   AS level2_assays,
    COUNT(DISTINCT CASE WHEN p.chemical_regime='A' THEN p.peptide_id END) AS regime_a,
    COUNT(DISTINCT CASE WHEN p.chemical_regime='B' THEN p.peptide_id END) AS regime_b,
    COUNT(DISTINCT CASE WHEN p.chemical_regime='C' THEN p.peptide_id END) AS regime_c,
    COUNT(DISTINCT CASE WHEN p.chemical_regime='D' THEN p.peptide_id END) AS regime_d,
    COUNT(DISTINCT t.tax_id)                                        AS unique_pathogens,
    COUNT(DISTINCT r.reference_id)                                  AS unique_references
FROM peptide p
LEFT JOIN activity_assay a ON a.peptide_id = p.peptide_id
LEFT JOIN target_pathogen t ON t.tax_id = a.tax_id
LEFT JOIN reference r ON r.reference_id = a.reference_id;

-- View: candidatos genômicos priorizados (Frente de Pareto)
CREATE OR REPLACE VIEW vw_priority_candidates AS
SELECT
    gc.candidate_id,
    gs.organism_name,
    gs.genome_arm,
    gc.locus_tag,
    gc.predicted_sequence,
    gc.model_score,
    gc.pareto_rank,
    gc.priority_tier,
    gc.flag_length_ok,
    gc.flag_canonical,
    gc.flag_synthesizable,
    gc.flag_low_phytotox,
    gc.flag_low_hemolysis,
    gc.flag_stable,
    gc.bgc_type
FROM genomic_candidate gc
JOIN genomic_source gs ON gs.source_id = gc.source_id
WHERE gc.pareto_rank IS NOT NULL
ORDER BY gc.pareto_rank ASC, gc.model_score DESC;

-- ────────────────────────────────────────────────────────────
-- SEEDS: dados de referência iniciais
-- ────────────────────────────────────────────────────────────

-- Fitopatógenos prioritários (Dissertação — Eixo 1)
INSERT INTO target_pathogen (tax_id, species, genus, pathogen_type, common_diseases) VALUES
(5507,  'Fusarium oxysporum',                'Fusarium',      'true_fungi',  ARRAY['Fusariose', 'Murcha de Fusarium']),
(34350, 'Xanthomonas oryzae',                'Xanthomonas',   'bacteria',    ARRAY['Queima bacteriana do arroz']),
(339497,'Xanthomonas campestris',            'Xanthomonas',   'bacteria',    ARRAY['Cancro bacteriano do citros']),
(283,   'Pseudomonas syringae',              'Pseudomonas',   'bacteria',    ARRAY['Mancha bacteriana']),
(551   ,'Erwinia amylovora',                 'Erwinia',       'bacteria',    ARRAY['Fogo bacteriano']),
(70609, 'Pectobacterium carotovorum',        'Pectobacterium','bacteria',    ARRAY['Podridão mole']),
(29938, 'Colletotrichum gloeosporioides',    'Colletotrichum','true_fungi',  ARRAY['Antracnose']),
(33183, 'Botrytis cinerea',                  'Botrytis',      'true_fungi',  ARRAY['Mofo cinzento']),
(48850, 'Alternaria alternata',              'Alternaria',    'true_fungi',  ARRAY['Mancha de Alternaria']),
(318829,'Magnaporthe oryzae',                'Magnaporthe',   'true_fungi',  ARRAY['Brusone do arroz']),
(4792,  'Phytophthora infestans',            'Phytophthora',  'oomycete',    ARRAY['Requeima da batata']),
(4785,  'Pythium ultimum',                   'Pythium',       'oomycete',    ARRAY['Damping-off']),
(5535,  'Trichoderma asperellum',            'Trichoderma',   'true_fungi',  ARRAY['Agente de biocontrole']),
(1386,  'Bacillus subtilis',                 'Bacillus',      'bacteria',    ARRAY['Agente de biocontrole']),
(1902,  'Streptomyces coelicolor',           'Streptomyces',  'bacteria',    ARRAY['Produtor de metabolitos'])
ON CONFLICT (tax_id) DO NOTHING;

-- Feature sets pré-definidos
INSERT INTO feature_set (name, feature_type, tool_name, tool_version, n_dimensions, description) VALUES
('physicochemical_modlamp_v1',  'physicochemical',  'modlAMP',        '4.3.0', 12,   'Descritores físico-químicos clássicos'),
('sequence_composition_v1',     'sequence_composition', 'iFeatureOmega', '1.0', 400, 'Composição de aa + dipeptídeos + k-mers'),
('embeddings_esm2_8M_v1',       'embedding_plm',    'ESM-2',          '8M',   320,  'Embeddings ESM-2 (mean pool)'),
('embeddings_prot5_xl_v1',      'embedding_plm',    'ProtT5',         'xl',   1024, 'Embeddings ProtT5 (mean pool)'),
('map4_fingerprint_v1',         'fingerprint',      'MAP4',           '1.0',  1024, 'MAP4 fingerprint para não canônicos')
ON CONFLICT (name) DO NOTHING;

-- ────────────────────────────────────────────────────────────
-- INDICES ADICIONAIS para performance
-- ────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_assay_taxid_eligible
    ON activity_assay(tax_id, train_eligible);

CREATE INDEX IF NOT EXISTS idx_peptide_regime_canonical
    ON peptide(chemical_regime, is_canonical);

CREATE INDEX IF NOT EXISTS idx_model_pred_rank
    ON model_prediction(predicted_rank ASC NULLS LAST);

-- ════════════════════════════════════════════════════════════
-- FIM DO SCHEMA PhytoAMP v0.1
-- ════════════════════════════════════════════════════════════
