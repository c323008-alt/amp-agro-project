"""
physicochemical_descriptors.py

Descritores físico-químicos para peptídeos canônicos.

Usa BioPython/ProtParam para calcular:
- peso molecular
- ponto isoelétrico teórico
- GRAVY
- aromaticidade
- índice de instabilidade
- carga em pH 7
- frações de hélice/turn/sheet

Também calcula alguns descritores próprios:
- índice alifático aproximado
- razão carga/comprimento
- razão hidrofobicidade/carga
"""

from __future__ import annotations

from typing import Dict

import math

from Bio.SeqUtils.ProtParam import ProteinAnalysis

from src.features.sequence_features import (
    clean_sequence,
    is_canonical_sequence,
    fraction_of_group,
)


ALIPHATIC_AA = set("AVIL")
HYDROPHOBIC_AA = set("AILMFWVY")
POSITIVE_AA = set("KRH")
NEGATIVE_AA = set("DE")


def safe_float(value) -> float:
    """
    Converte valores para float.
    Se falhar, retorna NaN.
    """
    try:
        return float(value)
    except Exception:
        return math.nan


def aliphatic_index_approx(sequence: str) -> float:
    """
    Calcula um índice alifático aproximado.

    Fórmula simplificada inspirada no índice alifático clássico:
    Ala% + 2.9 * Val% + 3.9 * (Ile% + Leu%)

    Observação:
    O resultado é uma aproximação útil para comparação interna.
    """
    sequence = clean_sequence(sequence)
    length = len(sequence)

    if length == 0:
        return math.nan

    ala = sequence.count("A") / length * 100
    val = sequence.count("V") / length * 100
    ile = sequence.count("I") / length * 100
    leu = sequence.count("L") / length * 100

    return ala + 2.9 * val + 3.9 * (ile + leu)


def charge_density(sequence: str) -> float:
    """
    Carga aproximada dividida pelo comprimento.
    """
    sequence = clean_sequence(sequence)
    length = len(sequence)

    if length == 0:
        return math.nan

    positive = sum(aa in POSITIVE_AA for aa in sequence)
    negative = sum(aa in NEGATIVE_AA for aa in sequence)

    return (positive - negative) / length


def hydrophobic_charge_ratio(sequence: str) -> float:
    """
    Razão entre fração hidrofóbica e carga positiva aproximada.

    Útil para flag exploratória de peptídeos muito hidrofóbicos
    ou muito catiônicos.

    Se não houver resíduos positivos, retorna NaN.
    """
    sequence = clean_sequence(sequence)

    positive = sum(aa in POSITIVE_AA for aa in sequence)

    if positive == 0:
        return math.nan

    hydrophobic_fraction = fraction_of_group(sequence, HYDROPHOBIC_AA)

    return hydrophobic_fraction / positive


def compute_protparam_descriptors(sequence: str) -> Dict[str, float | bool]:
    """
    Calcula descritores físico-químicos usando BioPython ProtParam.

    Retorna NaN para descritores que não puderem ser calculados.

    Importante:
    Este método deve ser usado principalmente para sequências canônicas.
    """
    sequence = clean_sequence(sequence)

    result: Dict[str, float | bool] = {
        "protparam_ok": False,
        "molecular_weight": math.nan,
        "aromaticity": math.nan,
        "instability_index": math.nan,
        "gravy": math.nan,
        "isoelectric_point": math.nan,
        "charge_at_pH_7": math.nan,
        "secondary_structure_helix": math.nan,
        "secondary_structure_turn": math.nan,
        "secondary_structure_sheet": math.nan,
    }

    if not is_canonical_sequence(sequence):
        return result

    try:
        analysis = ProteinAnalysis(sequence)

        helix, turn, sheet = analysis.secondary_structure_fraction()

        result.update(
            {
                "protparam_ok": True,
                "molecular_weight": safe_float(analysis.molecular_weight()),
                "aromaticity": safe_float(analysis.aromaticity()),
                "instability_index": safe_float(analysis.instability_index()),
                "gravy": safe_float(analysis.gravy()),
                "isoelectric_point": safe_float(analysis.isoelectric_point()),
                "charge_at_pH_7": safe_float(analysis.charge_at_pH(7.0)),
                "secondary_structure_helix": safe_float(helix),
                "secondary_structure_turn": safe_float(turn),
                "secondary_structure_sheet": safe_float(sheet),
            }
        )

    except Exception:
        # Em pipeline científico, é melhor retornar NaN do que quebrar tudo
        # por causa de uma sequência problemática.
        return result

    return result


def compute_physicochemical_descriptors(sequence: str) -> Dict[str, float | bool]:
    """
    Calcula descritores físico-químicos combinando:
    - BioPython ProtParam
    - descritores próprios simples
    """
    sequence = clean_sequence(sequence)

    descriptors = compute_protparam_descriptors(sequence)

    descriptors.update(
        {
            "aliphatic_index_approx": aliphatic_index_approx(sequence),
            "charge_density_approx": charge_density(sequence),
            "hydrophobic_charge_ratio": hydrophobic_charge_ratio(sequence),
        }
    )

    return descriptors
