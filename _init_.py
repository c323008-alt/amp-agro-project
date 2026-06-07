"""
Subpacote de extração de features.

Aqui ficam funções para transformar sequências peptídicas
em descritores numéricos usados pelos modelos.
"""

from src.features.sequence_features import (
    clean_sequence,
    is_canonical_sequence,
    compute_basic_sequence_features,
)

from src.features.physicochemical_descriptors import (
    compute_physicochemical_descriptors,
)
