"""
sequence_features.py

Funções básicas para extrair descritores de sequência de peptídeos.

Este módulo não depende de BioPython. Ele calcula descritores simples:
- comprimento
- validação de aminoácidos canônicos
- composição de aminoácidos
- frações por grupos químicos
- carga líquida aproximada
- contagem de resíduos importantes
"""

from __future__ import annotations

from collections import Counter
from typing import Dict


CANONICAL_AA = set("ACDEFGHIKLMNPQRSTVWY")

AA_ORDER = list("ACDEFGHIKLMNPQRSTVWY")

POSITIVE_AA = set("KRH")
NEGATIVE_AA = set("DE")

BASIC_AA = set("KRH")
ACIDIC_AA = set("DE")

POLAR_UNCHARGED_AA = set("STNQCY")
NONPOLAR_AA = set("AVILMFWPG")

HYDROPHOBIC_AA = set("AILMFWVY")
AROMATIC_AA = set("FWY")
SULFUR_AA = set("CM")
SMALL_AA = set("AGSTP")
SPECIAL_AA = set("CGP")


def clean_sequence(sequence: str) -> str:
    """
    Padroniza uma sequência de aminoácidos.

    Remove espaços, hífens e quebras de linha.
    Converte para maiúsculas.

    Exemplo:
    ' kwk-lfkk ' -> 'KWKLFKK'
    """
    if sequence is None:
        return ""

    sequence = str(sequence)
    sequence = sequence.strip().upper()
    sequence = sequence.replace(" ", "")
    sequence = sequence.replace("-", "")
    sequence = sequence.replace("\n", "")
    sequence = sequence.replace("\r", "")
    sequence = sequence.replace("\t", "")

    return sequence


def is_canonical_sequence(sequence: str) -> bool:
    """
    Verifica se a sequência contém apenas os 20 aminoácidos canônicos.
    """
    sequence = clean_sequence(sequence)

    if len(sequence) == 0:
        return False

    return set(sequence).issubset(CANONICAL_AA)


def sequence_length(sequence: str) -> int:
    """
    Retorna o comprimento da sequência.
    """
    return len(clean_sequence(sequence))


def count_residues(sequence: str) -> Dict[str, int]:
    """
    Conta cada aminoácido canônico na sequência.

    Retorna colunas como:
    count_A, count_C, count_D...
    """
    sequence = clean_sequence(sequence)
    counts = Counter(sequence)

    return {f"count_{aa}": counts.get(aa, 0) for aa in AA_ORDER}


def amino_acid_composition(sequence: str) -> Dict[str, float]:
    """
    Calcula a composição relativa de cada aminoácido.

    Retorna colunas como:
    comp_A, comp_C, comp_D...

    Exemplo:
    se A aparece 2 vezes em uma sequência de tamanho 10,
    comp_A = 0.2
    """
    sequence = clean_sequence(sequence)
    length = len(sequence)

    if length == 0:
        return {f"comp_{aa}": 0.0 for aa in AA_ORDER}

    counts = Counter(sequence)

    return {f"comp_{aa}": counts.get(aa, 0) / length for aa in AA_ORDER}


def fraction_of_group(sequence: str, group: set[str]) -> float:
    """
    Calcula a fração de resíduos pertencentes a um grupo.
    """
    sequence = clean_sequence(sequence)
    length = len(sequence)

    if length == 0:
        return 0.0

    return sum(aa in group for aa in sequence) / length


def approximate_net_charge(sequence: str) -> int:
    """
    Calcula uma carga líquida aproximada em pH fisiológico.

    Regra simples:
    K, R, H = +1
    D, E = -1

    Observação:
    É uma aproximação. A carga real depende de pH e pKa.
    Para carga estimada por pH, use physicochemical_descriptors.py.
    """
    sequence = clean_sequence(sequence)

    positive = sum(aa in POSITIVE_AA for aa in sequence)
    negative = sum(aa in NEGATIVE_AA for aa in sequence)

    return positive - negative


def has_invalid_characters(sequence: str) -> bool:
    """
    Retorna True se a sequência tiver caracteres fora dos 20 aminoácidos canônicos.
    """
    sequence = clean_sequence(sequence)

    if len(sequence) == 0:
        return True

    return not set(sequence).issubset(CANONICAL_AA)


def invalid_characters(sequence: str) -> str:
    """
    Retorna caracteres inválidos encontrados na sequência.
    """
    sequence = clean_sequence(sequence)
    invalid = sorted(set(sequence) - CANONICAL_AA)

    return "".join(invalid)


def compute_basic_sequence_features(sequence: str) -> Dict[str, float | int | bool | str]:
    """
    Calcula descritores básicos de sequência.

    Entrada:
    - sequence: sequência de aminoácidos

    Saída:
    - dicionário com features numéricas e flags
    """
    sequence = clean_sequence(sequence)
    length = len(sequence)

    features: Dict[str, float | int | bool | str] = {
        "sequence_clean": sequence,
        "length_aa_computed": length,
        "is_canonical_computed": is_canonical_sequence(sequence),
        "has_invalid_characters": has_invalid_characters(sequence),
        "invalid_characters": invalid_characters(sequence),
        "net_charge_approx": approximate_net_charge(sequence),
        "frac_positive": fraction_of_group(sequence, POSITIVE_AA),
        "frac_negative": fraction_of_group(sequence, NEGATIVE_AA),
        "frac_basic": fraction_of_group(sequence, BASIC_AA),
        "frac_acidic": fraction_of_group(sequence, ACIDIC_AA),
        "frac_polar_uncharged": fraction_of_group(sequence, POLAR_UNCHARGED_AA),
        "frac_nonpolar": fraction_of_group(sequence, NONPOLAR_AA),
        "frac_hydrophobic": fraction_of_group(sequence, HYDROPHOBIC_AA),
        "frac_aromatic": fraction_of_group(sequence, AROMATIC_AA),
        "frac_sulfur": fraction_of_group(sequence, SULFUR_AA),
        "frac_small": fraction_of_group(sequence, SMALL_AA),
        "frac_special_CGP": fraction_of_group(sequence, SPECIAL_AA),
        "count_cys": sequence.count("C"),
        "count_gly": sequence.count("G"),
        "count_pro": sequence.count("P"),
        "count_lys": sequence.count("K"),
        "count_arg": sequence.count("R"),
        "count_his": sequence.count("H"),
        "count_asp": sequence.count("D"),
        "count_glu": sequence.count("E"),
    }

    features.update(count_residues(sequence))
    features.update(amino_acid_composition(sequence))

    return features
