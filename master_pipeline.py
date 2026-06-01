#!/usr/bin/env python3
"""
PhytoAMP Master Pipeline Script
================================
Projeto: Recurso curado e orientado a contexto agrícola para AMPs contra fitopatógenos
Dissertação de Mestrado — SENAI CIMATEC

Este script orquestra TODAS as etapas do projeto em ordem de execução,
cobrindo todos os verbos no infinitivo presentes no documento de orientação.

Verbos mapeados como steps:
  - Definir, Desenhar, Montar, Medir, Diferenciar, Estruturar
  - Desenvolver, Criar, Realizar, Separar, Classificar
  - Validar, Congelar, Rodar, Testar, Decidir
  - Adotar, Priorizar, Registrar, Usar, Investigar
  - Incluir, Declarar, Verificar, Comparar, Expandir
  - Provar, Integrar, Organizar, Evitar, Distinguir
  - Fazer, Escolher, Auditoria, Operacionalizar
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# ── Configuração de logging ──────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("PhytoAMP.Master")

# ── Raiz do projeto ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SRC = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))

# ─────────────────────────────────────────────────────────────────────────────
# FASE 0 — SETUP & INFRAESTRUTURA
# ─────────────────────────────────────────────────────────────────────────────

def step_definir_schema():
    """
    PASSO 1 — Definir o Schema e Vocabulário
    Verbo: DEFINIR
    Ref.: Fase 1, item 1 da dissertação
    """
    log.info("═══ PASSO 1: DEFINIR schema conceitual e vocabulário mínimo ═══")
    from src.curation.schema_builder import build_schema_definition
    schema = build_schema_definition()
    schema_path = PROJECT_ROOT / "configs" / "schema_definition.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    log.info(f"  ✔ Schema definido e salvo em: {schema_path}")
    return schema


def step_desenhar_banco():
    """
    PASSO 2 — Desenhar o banco de dados relacional (PostgreSQL)
    Verbo: DESENHAR
    Ref.: Apêndice G da dissertação
    """
    log.info("═══ PASSO 2: DESENHAR banco relacional PostgreSQL ═══")
    from src.database.setup import run_schema_sql
    result = run_schema_sql(
        sql_path=PROJECT_ROOT / "database" / "schema.sql"
    )
    log.info(f"  ✔ Banco desenhado: {result}")


def step_montar_busca_inicial():
    """
    PASSO 3 — Montar a Busca Inicial nas bases AMP
    Verbo: MONTAR
    Ref.: Frentes A, B, C da dissertação
    """
    log.info("═══ PASSO 3: MONTAR estratégia de busca bibliográfica ═══")
    from src.curation.search_strategy import SearchStrategy
    ss = SearchStrategy()
    queries = ss.build_queries()
    out_path = PROJECT_ROOT / "data" / "raw" / "search_queries.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2, ensure_ascii=False)
    log.info(f"  ✔ {len(queries)} queries montadas → {out_path}")
    return queries


def step_medir_dataset_inicial():
    """
    PASSO 4 — Medir o Dataset Inicial (Contagem Honesta)
    Verbo: MEDIR
    Ref.: Fase 1, item 2 — Mês 1
    """
    log.info("═══ PASSO 4: MEDIR dataset inicial — contagem honesta ═══")
    from src.curation.measurement import measure_dataset
    raw_dir = PROJECT_ROOT / "data" / "raw"
    stats = measure_dataset(raw_dir)
    stats_path = PROJECT_ROOT / "data" / "curated" / "dataset_measurement.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    log.info(f"  ✔ Contagem: {stats.get('total_records', '?')} registros brutos")
    log.info(f"  ✔ Treináveis estimados: {stats.get('trainable_estimate', '?')}")
    return stats


def step_diferenciar_registros():
    """
    PASSO 5 — Diferenciar Registros: Nível 1 (Treinável) vs Nível 2 (Contextual)
    Verbo: DIFERENCIAR
    Ref.: Fase 1, item 3 da dissertação
    """
    log.info("═══ PASSO 5: DIFERENCIAR registros — Nível 1 vs Nível 2 ═══")
    from src.curation.classifier import RecordClassifier
    clf = RecordClassifier()
    raw_path = PROJECT_ROOT / "data" / "raw"
    classified = clf.classify_all(raw_path)
    out_path = PROJECT_ROOT / "data" / "curated" / "classified_records.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(classified, f, indent=2, ensure_ascii=False)
    n1 = sum(1 for r in classified if r.get("level") == 1)
    n2 = sum(1 for r in classified if r.get("level") == 2)
    log.info(f"  ✔ Nível 1 (treinável): {n1} | Nível 2 (contextual): {n2}")
    return classified


def step_estruturar_extracao():
    """
    PASSO 6 — Estruturar a Extração em duas camadas (Rápida + Profunda)
    Verbo: ESTRUTURAR
    Ref.: Fase 1, item 4 da dissertação
    """
    log.info("═══ PASSO 6: ESTRUTURAR extração — camada rápida + profunda ═══")
    from src.curation.extraction import ExtractionPipeline
    pipeline = ExtractionPipeline(
        raw_dir=PROJECT_ROOT / "data" / "raw",
        curated_dir=PROJECT_ROOT / "data" / "curated",
    )
    pipeline.run_rapid_layer()
    pipeline.run_deep_layer()
    log.info("  ✔ Extração estruturada concluída")


def step_separar_regimes():
    """
    PASSO 7 — Separar em Regimes Químicos (A, B, C, D)
    Verbo: SEPARAR
    Ref.: Seção de Regimes da dissertação
    """
    log.info("═══ PASSO 7: SEPARAR peptídeos em regimes químicos A/B/C/D ═══")
    from src.features.regime_separator import RegimeSeparator
    sep = RegimeSeparator(
        input_path=PROJECT_ROOT / "data" / "curated" / "classified_records.json",
        output_dir=PROJECT_ROOT / "data" / "curated",
    )
    sep.separate()
    log.info("  ✔ Regimes A/B/C/D separados")


def step_realizar_curadoria_profunda():
    """
    PASSO 8 — Realizar a Curadoria Profunda com controle de qualidade
    Verbo: REALIZAR
    Ref.: Pipeline de curadoria profunda
    """
    log.info("═══ PASSO 8: REALIZAR curadoria profunda + controle de qualidade ═══")
    from src.curation.quality_control import QualityController
    qc = QualityController(
        curated_dir=PROJECT_ROOT / "data" / "curated",
        log_dir=LOG_DIR,
    )
    report = qc.run()
    qc_path = PROJECT_ROOT / "data" / "curated" / "qc_report.json"
    with open(qc_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log.info(f"  ✔ QC concluído — {report.get('issues_found', 0)} issues encontrados")


def step_registrar_evidencia_agricola():
    """
    PASSO 9 — Registrar o nível de evidência agrícola (modelo ortogonal)
    Verbo: REGISTRAR
    Ref.: Tabela de modelo ortogonal da dissertação
    """
    log.info("═══ PASSO 9: REGISTRAR nível de evidência agrícola — modelo ortogonal ═══")
    from src.curation.evidence_layer import EvidenceLayerAnnotator
    ela = EvidenceLayerAnnotator(
        input_path=PROJECT_ROOT / "data" / "curated" / "classified_records.json",
        output_path=PROJECT_ROOT / "data" / "curated" / "evidence_annotated.json",
    )
    ela.annotate()
    log.info("  ✔ Evidência agrícola registrada para todos os registros")


def step_organizar_endpoints():
    """
    PASSO 10 — Organizar e normalizar endpoints (MIC, IC50, log2, censura)
    Verbo: ORGANIZAR
    Ref.: Seção de endpoints e censura da dissertação
    """
    log.info("═══ PASSO 10: ORGANIZAR endpoints — normalização e censura ═══")
    from src.curation.endpoint_normalizer import EndpointNormalizer
    en = EndpointNormalizer(
        input_path=PROJECT_ROOT / "data" / "curated" / "evidence_annotated.json",
        output_path=PROJECT_ROOT / "data" / "curated" / "endpoints_normalized.json",
    )
    en.normalize()
    log.info("  ✔ Endpoints organizados com operadores de censura (=, >, <)")


def step_congelar_dataset_v0():
    """
    PASSO 11 — Congelar V0 do dataset
    Verbo: CONGELAR
    Ref.: Mês 3 da dissertação
    """
    log.info("═══ PASSO 11: CONGELAR V0 do dataset ═══")
    from src.curation.versioning import freeze_dataset_version
    v0_path = freeze_dataset_version(
        source_dir=PROJECT_ROOT / "data" / "curated",
        version="v0",
        output_dir=PROJECT_ROOT / "data" / "curated",
    )
    log.info(f"  ✔ Dataset V0 congelado em: {v0_path}")


# ─────────────────────────────────────────────────────────────────────────────
# FASE 2 — FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

def step_desenvolver_features():
    """
    PASSO 12 — Desenvolver features (descritores físico-químicos + embeddings)
    Verbo: DESENVOLVER
    Ref.: Seção de Feature Engineering da dissertação
    """
    log.info("═══ PASSO 12: DESENVOLVER features — descritores + embeddings ═══")
    from src.features.physicochemical import compute_physicochemical
    from src.features.sequence_descriptors import compute_sequence_descriptors
    from src.features.embeddings import generate_embeddings

    data_path = PROJECT_ROOT / "data" / "curated" / "endpoints_normalized.json"
    feat_dir = PROJECT_ROOT / "data" / "processed"

    compute_physicochemical(data_path, feat_dir / "features_physicochemical.json")
    compute_sequence_descriptors(data_path, feat_dir / "features_sequence.json")
    generate_embeddings(data_path, feat_dir / "embeddings_esm2.h5",
                        model_name="esm2_t6_8M_UR50D")
    log.info("  ✔ Features desenvolvidas: físico-químicos + sequência + embeddings ESM-2")


def step_usar_plm():
    """
    PASSO 13 — Usar Protein Language Models (ESM-2, ProtT5) para embeddings
    Verbo: USAR
    Ref.: Estratégias 1, 2, 3 de transfer learning da dissertação
    """
    log.info("═══ PASSO 13: USAR PLMs — ESM-2 e ProtT5 para embeddings ═══")
    from src.features.embeddings import generate_embeddings
    data_path = PROJECT_ROOT / "data" / "curated" / "endpoints_normalized.json"
    feat_dir = PROJECT_ROOT / "data" / "processed"
    generate_embeddings(data_path, feat_dir / "embeddings_prot5.h5",
                        model_name="prot_t5_xl_half_uniref50-enc")
    log.info("  ✔ Embeddings ProtT5 gerados")


# ─────────────────────────────────────────────────────────────────────────────
# FASE 3 — BENCHMARK
# ─────────────────────────────────────────────────────────────────────────────

def step_criar_splits():
    """
    PASSO 14 — Criar splits de validação (aleatório, peptide_id, homology-aware)
    Verbo: CRIAR
    Ref.: Benchmarks 1–4 do Apêndice C
    """
    log.info("═══ PASSO 14: CRIAR splits de validação — 4 benchmarks ═══")
    from src.benchmark.splits import SplitGenerator
    sg = SplitGenerator(
        data_path=PROJECT_ROOT / "data" / "curated" / "endpoints_normalized.json",
        output_dir=PROJECT_ROOT / "data" / "processed" / "splits",
        similarity_thresholds=[0.80, 0.60, 0.40],
    )
    sg.generate_random_split()           # Benchmark 1
    sg.generate_peptide_id_split()       # Benchmark 2
    sg.generate_homology_aware_split()   # Benchmark 3 (resultado principal)
    sg.generate_holdout_split()          # Benchmark 4
    log.info("  ✔ 4 splits criados com thresholds 80/60/40%")


def step_adotar_split_homology():
    """
    PASSO 15 — Adotar split homology-aware como resultado principal de avaliação
    Verbo: ADOTAR
    Ref.: Benchmark 3 — resultado principal
    """
    log.info("═══ PASSO 15: ADOTAR split homology-aware como resultado principal ═══")
    from src.benchmark.splits import SplitGenerator
    splits_dir = PROJECT_ROOT / "data" / "processed" / "splits"
    main_split_path = splits_dir / "split_homology_aware_60pct.json"
    symlink_path = splits_dir / "main_split.json"
    if symlink_path.exists():
        symlink_path.unlink()
    symlink_path.symlink_to(main_split_path.name)
    log.info(f"  ✔ Split principal adotado: {main_split_path.name}")


def step_priorizar_negativos():
    """
    PASSO 16 — Priorizar negativos reais (testados e reportados como inativos)
    Verbo: PRIORIZAR
    Ref.: Tratamento de Negativos da dissertação
    """
    log.info("═══ PASSO 16: PRIORIZAR negativos reais — inativos testados ═══")
    from src.benchmark.negatives import NegativeSelector
    ns = NegativeSelector(
        data_path=PROJECT_ROOT / "data" / "curated" / "endpoints_normalized.json",
        output_path=PROJECT_ROOT / "data" / "processed" / "negatives_real.json",
    )
    ns.select_real_negatives()
    log.info("  ✔ Negativos reais priorizados — sem sequências aleatórias")


def step_controlar_vazamentos():
    """
    PASSO 17 — Controlar vazamentos (deduplicação, quase duplicatas, homologia)
    Verbo: CONTROLAR
    Ref.: Seção de Benchmark — Vazamentos da dissertação
    """
    log.info("═══ PASSO 17: CONTROLAR vazamentos — deduplicação + homologia ═══")
    from src.benchmark.leakage_control import LeakageController
    lc = LeakageController(
        data_path=PROJECT_ROOT / "data" / "curated" / "endpoints_normalized.json",
        output_path=PROJECT_ROOT / "data" / "curated" / "deduplicated.json",
    )
    lc.deduplicate()
    lc.check_near_duplicates()
    lc.check_homology_leakage()
    log.info("  ✔ Vazamentos controlados: duplicatas e homologia verificadas")


# ─────────────────────────────────────────────────────────────────────────────
# FASE 4 — MODELAGEM
# ─────────────────────────────────────────────────────────────────────────────

def step_rodar_baseline():
    """
    PASSO 18 — Rodar baseline de features clássicas (RF/XGBoost)
    Verbo: RODAR
    Ref.: Mês 3 e linha comparativa da dissertação
    """
    log.info("═══ PASSO 18: RODAR baseline — descritores clássicos + RF/XGBoost ═══")
    from src.modeling.classification import ClassificationPipeline
    clf = ClassificationPipeline(
        features_path=PROJECT_ROOT / "data" / "processed" / "features_physicochemical.json",
        split_path=PROJECT_ROOT / "data" / "processed" / "splits" / "main_split.json",
        output_dir=PROJECT_ROOT / "data" / "models",
        models=["RandomForest", "XGBoost"],
    )
    results = clf.run()
    log.info(f"  ✔ Baseline: AUROC={results.get('auroc', '?'):.3f}")
    return results


def step_realizar_transfer_learning():
    """
    PASSO 19 — Realizar transfer learning com PLMs (ESM-2 + ProtT5)
    Verbo: REALIZAR
    Ref.: Fase 3, item 2 — Priorizar Transfer Learning
    """
    log.info("═══ PASSO 19: REALIZAR transfer learning — ESM-2/ProtT5 ═══")
    from src.modeling.transfer_learning import TransferLearningPipeline
    tl = TransferLearningPipeline(
        embeddings_dir=PROJECT_ROOT / "data" / "processed",
        split_path=PROJECT_ROOT / "data" / "processed" / "splits" / "main_split.json",
        output_dir=PROJECT_ROOT / "data" / "models",
    )
    results = tl.run_strategy_1()   # Embeddings congelados + classificador leve
    log.info(f"  ✔ Transfer learning: AUROC={results.get('auroc', '?'):.3f}")
    return results


def step_classificar_candidatos():
    """
    PASSO 20 — Classificar candidatos (ativo vs inativo) com análise de threshold
    Verbo: CLASSIFICAR
    Ref.: Tarefa 1 — classificação binária
    """
    log.info("═══ PASSO 20: CLASSIFICAR candidatos — binário com análise de threshold ═══")
    from src.modeling.classification import run_binary_classification
    results = run_binary_classification(
        data_dir=PROJECT_ROOT / "data" / "processed",
        model_dir=PROJECT_ROOT / "data" / "models",
        thresholds=[16, 32, 64],  # µg/mL — zona cinzenta
    )
    log.info(f"  ✔ Classificação com sensibilidade a 3 thresholds realizada")


def step_realizar_ranking():
    """
    PASSO 21 — Realizar ranking de candidatos por potencial relativo
    Verbo: REALIZAR (ranking)
    Ref.: Tarefa 2 — ranking da dissertação
    """
    log.info("═══ PASSO 21: REALIZAR ranking — candidatos por potencial agrícola ═══")
    from src.modeling.ranking import RankingPipeline
    rp = RankingPipeline(
        data_path=PROJECT_ROOT / "data" / "processed",
        model_dir=PROJECT_ROOT / "data" / "models",
        output_path=PROJECT_ROOT / "data" / "processed" / "candidates_ranked.json",
    )
    ranked = rp.rank()
    log.info(f"  ✔ {len(ranked)} candidatos ranqueados")
    return ranked


def step_investigar_xai():
    """
    PASSO 22 — Investigar importância de features via XAI (SHAP)
    Verbo: INVESTIGAR
    Ref.: Auditoria do Modelo — XAI da dissertação
    """
    log.info("═══ PASSO 22: INVESTIGAR XAI — SHAP para auditoria do modelo ═══")
    from src.modeling.xai import XAIAuditor
    auditor = XAIAuditor(
        model_dir=PROJECT_ROOT / "data" / "models",
        data_path=PROJECT_ROOT / "data" / "processed",
        output_dir=PROJECT_ROOT / "data" / "models" / "xai",
    )
    auditor.compute_shap()
    auditor.generate_report()
    log.info("  ✔ SHAP computado — relatório de auditoria gerado")


def step_verificar_artefatos():
    """
    PASSO 23 — Verificar se o modelo captura propriedades biológicas (não artefatos)
    Verbo: VERIFICAR
    Ref.: Auditoria XAI — 'verificar se o modelo está capturando propriedades esperadas'
    """
    log.info("═══ PASSO 23: VERIFICAR ausência de artefatos de protocolo ═══")
    from src.modeling.xai import XAIAuditor
    auditor = XAIAuditor(
        model_dir=PROJECT_ROOT / "data" / "models",
        data_path=PROJECT_ROOT / "data" / "processed",
        output_dir=PROJECT_ROOT / "data" / "models" / "xai",
    )
    auditor.check_artifacts()
    log.info("  ✔ Artefatos de protocolo verificados")


def step_comparar_modelos():
    """
    PASSO 24 — Comparar modelos: clássico vs transfer learning
    Verbo: COMPARAR
    Ref.: Linha comparativa da dissertação
    """
    log.info("═══ PASSO 24: COMPARAR modelos — baseline vs transfer learning ═══")
    from src.benchmark.evaluation import ModelComparator
    mc = ModelComparator(
        models_dir=PROJECT_ROOT / "data" / "models",
        output_path=PROJECT_ROOT / "data" / "models" / "comparison_report.json",
    )
    report = mc.compare_all()
    log.info(f"  ✔ Comparação concluída — melhor modelo: {report.get('best_model', '?')}")
    return report


def step_validar_dominio():
    """
    PASSO 25 — Validar e declarar domínio de aplicabilidade do modelo
    Verbo: VALIDAR + DECLARAR
    Ref.: 'Declaração de Domínio de Aplicabilidade'
    """
    log.info("═══ PASSO 25: VALIDAR + DECLARAR domínio de aplicabilidade ═══")
    from src.modeling.applicability import ApplicabilityDomain
    ad = ApplicabilityDomain(
        model_dir=PROJECT_ROOT / "data" / "models",
        output_path=PROJECT_ROOT / "data" / "models" / "applicability_domain.json",
    )
    ad.define()
    ad.export_model_card(PROJECT_ROOT / "docs" / "model_card.md")
    log.info("  ✔ Domínio de aplicabilidade declarado — model card gerado")


# ─────────────────────────────────────────────────────────────────────────────
# FASE 5 — PIPELINE GENÔMICO (MAMBA)
# ─────────────────────────────────────────────────────────────────────────────

def step_executar_anotacao_bacteriana():
    """
    PASSO 26 — Executar anotação procariótica (Bakta/PGAP)
    Verbo: EXECUTAR
    Ref.: Braço bacteriano — Bakta/PGAP
    """
    log.info("═══ PASSO 26: EXECUTAR anotação bacteriana — Bakta ═══")
    from src.genomic.bacterial_arm import BacterialGenomicArm
    ba = BacterialGenomicArm(
        genome_dir=PROJECT_ROOT / "data" / "raw" / "genomes",
        output_dir=PROJECT_ROOT / "data" / "processed" / "genomic" / "bacterial",
    )
    ba.run_bakta_annotation()
    log.info("  ✔ Anotação bacteriana executada")


def step_usar_antismash():
    """
    PASSO 27 — Usar antiSMASH 8 para identificar BGCs
    Verbo: USAR (antiSMASH)
    Ref.: Braço bacteriano — antiSMASH 8 + GECCO
    """
    log.info("═══ PASSO 27: USAR antiSMASH 8 — identificação de BGCs ═══")
    from src.genomic.bacterial_arm import BacterialGenomicArm
    ba = BacterialGenomicArm(
        genome_dir=PROJECT_ROOT / "data" / "raw" / "genomes",
        output_dir=PROJECT_ROOT / "data" / "processed" / "genomic" / "bacterial",
    )
    ba.run_antismash()
    ba.run_gecco()  # contraste baseado em ML
    log.info("  ✔ BGCs identificados com antiSMASH 8 + GECCO")


def step_varrer_smORFs():
    """
    PASSO 28 — Varrer small ORFs (smORFs) candidatos a AMP
    Verbo: VARRER
    Ref.: Varredura de candidatos AMP — Macrel + ampir
    """
    log.info("═══ PASSO 28: VARRER smORFs — Macrel + ampir ═══")
    from src.genomic.bacterial_arm import BacterialGenomicArm
    ba = BacterialGenomicArm(
        genome_dir=PROJECT_ROOT / "data" / "raw" / "genomes",
        output_dir=PROJECT_ROOT / "data" / "processed" / "genomic" / "bacterial",
    )
    ba.run_macrel()
    ba.run_ampir()
    ba.consolidate_with_ampcombi()
    log.info("  ✔ smORFs varridos e consolidados com AMPcombi")


def step_integrar_candidatos_genomicos():
    """
    PASSO 29 — Integrar candidatos genômicos no pipeline de priorização
    Verbo: INTEGRAR
    Ref.: Candidatos genômicos — priorização por eixos (Pareto)
    """
    log.info("═══ PASSO 29: INTEGRAR candidatos genômicos ao pipeline ═══")
    from src.genomic.prioritization import GenomicPrioritizer
    gp = GenomicPrioritizer(
        genomic_dir=PROJECT_ROOT / "data" / "processed" / "genomic",
        model_dir=PROJECT_ROOT / "data" / "models",
        output_path=PROJECT_ROOT / "data" / "processed" / "genomic_candidates_prioritized.json",
    )
    gp.score_candidates()
    gp.apply_pareto_front()
    gp.apply_translational_flags()
    log.info("  ✔ Candidatos genômicos integrados e priorizados via Pareto")


def step_incluir_flags_viabilidade():
    """
    PASSO 30 — Incluir flags de viabilidade translacional
    Verbo: INCLUIR
    Ref.: 'Manufacturability e Estabilidade' — Incluir flags
    """
    log.info("═══ PASSO 30: INCLUIR flags de viabilidade translacional ═══")
    from src.genomic.translational_flags import TranslationalFlagAnnotator
    tfa = TranslationalFlagAnnotator(
        candidates_path=PROJECT_ROOT / "data" / "processed" / "genomic_candidates_prioritized.json",
        output_path=PROJECT_ROOT / "data" / "processed" / "candidates_with_flags.json",
    )
    tfa.annotate_length()
    tfa.annotate_canonical_status()
    tfa.annotate_stability()
    tfa.annotate_phytotoxicity()
    tfa.annotate_hemolysis()
    log.info("  ✔ Flags de viabilidade incluídas: comprimento, estabilidade, toxicidade")


# ─────────────────────────────────────────────────────────────────────────────
# FASE 6 — REPRODUTIBILIDADE & OUTPUTS FINAIS
# ─────────────────────────────────────────────────────────────────────────────

def step_escolher_modelo_final():
    """
    PASSO 31 — Escolher o modelo final para publicação
    Verbo: ESCOLHER
    Ref.: Mês 3 — 'decidir se o braço principal de modelagem será...'
    """
    log.info("═══ PASSO 31: ESCOLHER modelo final para publicação ═══")
    from src.modeling.selection import ModelSelector
    ms = ModelSelector(
        comparison_path=PROJECT_ROOT / "data" / "models" / "comparison_report.json",
    )
    selected = ms.select()
    log.info(f"  ✔ Modelo escolhido: {selected}")


def step_expandir_para_braco_fungico():
    """
    PASSO 32 — Expandir para o braço fúngico (se houver fôlego)
    Verbo: EXPANDIR
    Ref.: Braço fúngico — opcional Fase 2
    """
    log.info("═══ PASSO 32: EXPANDIR — braço fúngico (BRAKER3/SignalP) ═══")
    from src.genomic.fungal_arm import FungalGenomicArm
    fa = FungalGenomicArm(
        genome_dir=PROJECT_ROOT / "data" / "raw" / "genomes" / "fungal",
        output_dir=PROJECT_ROOT / "data" / "processed" / "genomic" / "fungal",
    )
    fa.run_braker3()
    fa.run_signalp()
    fa.run_apoplastp()
    log.info("  ✔ Braço fúngico executado — secretoma anotado")


def step_provar_pipeline_integrado():
    """
    PASSO 33 — Provar que curadoria → benchmark → priorização funciona
    Verbo: PROVAR
    Ref.: Recomendação operacional — 'provar que a integração funciona'
    """
    log.info("═══ PASSO 33: PROVAR pipeline integrado curadoria→benchmark→priorização ═══")
    from src.benchmark.integration_test import IntegrationTester
    it = IntegrationTester(project_root=PROJECT_ROOT)
    result = it.run_end_to_end_test()
    log.info(f"  ✔ Pipeline integrado provado: {result}")


def step_operacionalizar_pareto():
    """
    PASSO 34 — Operacionalizar por frente de Pareto (multi-objetivo)
    Verbo: OPERACIONALIZAR
    Ref.: 'Operacionalizar por frente de Pareto'
    """
    log.info("═══ PASSO 34: OPERACIONALIZAR frente de Pareto ═══")
    from src.modeling.ranking import ParetoFrontOptimizer
    pfo = ParetoFrontOptimizer(
        candidates_path=PROJECT_ROOT / "data" / "processed" / "candidates_with_flags.json",
        output_path=PROJECT_ROOT / "data" / "processed" / "pareto_front.json",
        objectives=["model_score", "manufacturability", "stability", "low_toxicity"],
    )
    pfo.compute()
    log.info("  ✔ Frente de Pareto computada com 4 objetivos")


def step_gerar_outputs_h4i():
    """
    PASSO 35 — Gerar outputs para plataforma H4i do SENAI CIMATEC
    Verbo: GERAR
    Ref.: Requisito do projeto
    """
    log.info("═══ PASSO 35: GERAR outputs H4i — Dataset + AI Blocks + GRIPP ═══")
    from src.outputs.h4i_exporter import H4iExporter
    exp = H4iExporter(
        data_dir=PROJECT_ROOT / "data",
        output_dir=PROJECT_ROOT / "h4i",
    )
    exp.export_dataset_json()
    exp.export_ai_blocks()
    exp.export_gripp()
    log.info("  ✔ Outputs H4i gerados: dataset.json, ai_blocks.json, gripp.json")


def step_gerar_documentacao():
    """
    PASSO 36 — Gerar documentação completa do projeto
    Verbo: GERAR (documentação)
    """
    log.info("═══ PASSO 36: GERAR documentação — README, data_card, model_card ═══")
    from src.outputs.doc_generator import DocGenerator
    dg = DocGenerator(project_root=PROJECT_ROOT)
    dg.generate_readme()
    dg.generate_data_card()
    dg.generate_model_card()
    dg.generate_curation_log()
    log.info("  ✔ Documentação gerada")


# ─────────────────────────────────────────────────────────────────────────────
# ORQUESTRADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

PIPELINE_STEPS = [
    # FASE 0 — Setup
    ("F0.1", "definir_schema",           step_definir_schema),
    ("F0.2", "desenhar_banco",           step_desenhar_banco),
    ("F0.3", "montar_busca",             step_montar_busca_inicial),
    # FASE 1 — Curadoria
    ("F1.1", "medir_dataset",            step_medir_dataset_inicial),
    ("F1.2", "diferenciar_registros",    step_diferenciar_registros),
    ("F1.3", "estruturar_extracao",      step_estruturar_extracao),
    ("F1.4", "separar_regimes",          step_separar_regimes),
    ("F1.5", "realizar_curadoria",       step_realizar_curadoria_profunda),
    ("F1.6", "registrar_evidencia",      step_registrar_evidencia_agricola),
    ("F1.7", "organizar_endpoints",      step_organizar_endpoints),
    ("F1.8", "congelar_v0",              step_congelar_dataset_v0),
    # FASE 2 — Features
    ("F2.1", "desenvolver_features",     step_desenvolver_features),
    ("F2.2", "usar_plm",                 step_usar_plm),
    # FASE 3 — Benchmark
    ("F3.1", "criar_splits",             step_criar_splits),
    ("F3.2", "adotar_split_homology",    step_adotar_split_homology),
    ("F3.3", "priorizar_negativos",      step_priorizar_negativos),
    ("F3.4", "controlar_vazamentos",     step_controlar_vazamentos),
    # FASE 4 — Modelagem
    ("F4.1", "rodar_baseline",           step_rodar_baseline),
    ("F4.2", "realizar_transfer",        step_realizar_transfer_learning),
    ("F4.3", "classificar_candidatos",   step_classificar_candidatos),
    ("F4.4", "realizar_ranking",         step_realizar_ranking),
    ("F4.5", "investigar_xai",           step_investigar_xai),
    ("F4.6", "verificar_artefatos",      step_verificar_artefatos),
    ("F4.7", "comparar_modelos",         step_comparar_modelos),
    ("F4.8", "validar_declarar",         step_validar_dominio),
    # FASE 5 — Genômica
    ("F5.1", "executar_anotacao",        step_executar_anotacao_bacteriana),
    ("F5.2", "usar_antismash",           step_usar_antismash),
    ("F5.3", "varrer_smorfs",            step_varrer_smORFs),
    ("F5.4", "integrar_genomicos",       step_integrar_candidatos_genomicos),
    ("F5.5", "incluir_flags",            step_incluir_flags_viabilidade),
    # FASE 6 — Outputs
    ("F6.1", "escolher_modelo",          step_escolher_modelo_final),
    ("F6.2", "expandir_fungico",         step_expandir_para_braco_fungico),
    ("F6.3", "provar_pipeline",          step_provar_pipeline_integrado),
    ("F6.4", "operacionalizar_pareto",   step_operacionalizar_pareto),
    ("F6.5", "gerar_h4i",               step_gerar_outputs_h4i),
    ("F6.6", "gerar_documentacao",       step_gerar_documentacao),
]


def run_pipeline(start_from: str = None, only_step: str = None, dry_run: bool = False):
    """Executa o pipeline completo ou a partir de um step específico."""
    log.info("╔══════════════════════════════════════════════════════════════╗")
    log.info("║           PhytoAMP — Pipeline Master Script                 ║")
    log.info("║   SENAI CIMATEC / Dissertação de Mestrado                  ║")
    log.info("╚══════════════════════════════════════════════════════════════╝")
    log.info(f"  Início: {datetime.now().isoformat()}")
    log.info(f"  Dry-run: {dry_run}")

    started = start_from is None
    results = {}

    for step_id, step_name, step_fn in PIPELINE_STEPS:
        if only_step and step_name != only_step:
            continue
        if start_from and step_name == start_from:
            started = True
        if not started:
            continue

        log.info(f"\n{'─'*60}")
        log.info(f"  [{step_id}] {step_name}")
        if dry_run:
            log.info("  ⚠ DRY-RUN — pulando execução real")
            results[step_name] = "skipped (dry-run)"
            continue

        try:
            result = step_fn()
            results[step_name] = {"status": "ok", "result": str(result)[:200]}
        except Exception as exc:
            log.error(f"  ✗ ERRO em {step_name}: {exc}")
            results[step_name] = {"status": "error", "error": str(exc)}
            # Decide se continua ou para
            answer = input(f"\n  Continuar mesmo com erro em {step_name}? [s/N]: ")
            if answer.lower() != "s":
                break

    # Sumário
    run_log = {
        "pipeline_run": datetime.now().isoformat(),
        "steps": results,
        "total": len(results),
        "errors": sum(1 for v in results.values()
                      if isinstance(v, dict) and v.get("status") == "error"),
    }
    summary_path = LOG_DIR / "pipeline_summary.json"
    with open(summary_path, "w") as f:
        json.dump(run_log, f, indent=2)

    log.info(f"\n{'═'*60}")
    log.info(f"  Pipeline concluído — {run_log['total']} steps, {run_log['errors']} erros")
    log.info(f"  Sumário: {summary_path}")
    return run_log


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PhytoAMP Master Pipeline — Executa todos os steps do projeto"
    )
    parser.add_argument("--start-from", metavar="STEP", help="Iniciar a partir de um step")
    parser.add_argument("--only", metavar="STEP", help="Executar apenas um step")
    parser.add_argument("--dry-run", action="store_true", help="Listar steps sem executar")
    parser.add_argument("--list-steps", action="store_true", help="Listar todos os steps")
    args = parser.parse_args()

    if args.list_steps:
        print("\n  Steps disponíveis:\n")
        for sid, sname, sfn in PIPELINE_STEPS:
            doc = sfn.__doc__.strip().split("\n")[1].strip() if sfn.__doc__ else ""
            print(f"  [{sid:5s}] {sname:<30s}  {doc}")
        sys.exit(0)

    run_pipeline(
        start_from=args.start_from,
        only_step=args.only,
        dry_run=args.dry_run,
    )
