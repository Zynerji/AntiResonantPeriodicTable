"""Anti-resonant elements and their properties.

Each element is a metallic mean with measured or predicted quantum properties
from IBM Marrakesh experiments.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

PHI = (1 + math.sqrt(5)) / 2


@dataclass
class Element:
    """An anti-resonant element (one metallic mean family)."""
    symbol: str
    name: str
    n: int  # metallic mean index
    beta: float  # metallic mean value
    measured_energy: Optional[float]  # from IBM Marrakesh (None = predicted)
    predicted_energy: float  # from E(n) = -0.705n - 4.416
    jerkiness: Optional[float]
    sharpe: Optional[float]
    rti: Optional[float]  # resonant trapping index
    particle_analog: str
    role: str


# Scaling law from Quantum Golden Pendulum experiment
def energy_from_n(n: float) -> float:
    """E(n) = -0.705*n - 4.416"""
    return -0.705 * n - 4.416


def metallic_mean(n: int) -> float:
    """(n + sqrt(n^2 + 4)) / 2"""
    return (n + math.sqrt(n * n + 4)) / 2


# ── The Periodic Table ────────────────────────────────────────────────────

ELEMENTS: Dict[str, Element] = {
    "Au": Element(
        symbol="Au", name="Golden", n=1,
        beta=PHI,
        measured_energy=-5.121, predicted_energy=energy_from_n(1),
        jerkiness=0.120, sharpe=-0.419, rti=0.0,
        particle_analog="Electron",
        role="Stability shell — smoothest trajectory, lowest tail risk",
    ),
    "Ag": Element(
        symbol="Ag", name="Silver", n=2,
        beta=metallic_mean(2),
        measured_energy=None, predicted_energy=energy_from_n(2),
        jerkiness=None, sharpe=None, rti=None,
        particle_analog="Gluon",
        role="Mediator — bridges core and shell",
    ),
    "Br": Element(
        symbol="Br", name="Bronze", n=3,
        beta=metallic_mean(3),
        measured_energy=-6.532, predicted_energy=energy_from_n(3),
        jerkiness=0.302, sharpe=-0.375, rti=0.0,
        particle_analog="Down quark",
        role="Primary depth driver — strongest late-stage momentum",
    ),
    "Cu": Element(
        symbol="Cu", name="Copper", n=4,
        beta=metallic_mean(4),
        measured_energy=None, predicted_energy=energy_from_n(4),
        jerkiness=None, sharpe=None, rti=None,
        particle_analog="Up quark",
        role="Ultra-deep seed — extreme irrationality",
    ),
    "Ni": Element(
        symbol="Ni", name="Nickel", n=5,
        beta=metallic_mean(5),
        measured_energy=None, predicted_energy=energy_from_n(5),
        jerkiness=None, sharpe=None, rti=None,
        particle_analog="Charm quark",
        role="Heavy depth element — diminishing returns regime",
    ),
    "Ct": Element(
        symbol="Ct", name="Cocktail", n=-1,  # transcendental, no metallic n
        beta=0.4 * PHI + 0.3 * math.e + 0.3 * math.pi,
        measured_energy=-5.509, predicted_energy=None,
        jerkiness=0.262, sharpe=-0.070, rti=0.071,
        particle_analog="Photon",
        role="Transcendental dopant — catalyzes inter-shell entanglement",
    ),
    "Ch": Element(
        symbol="Ch", name="Chaotic", n=-2,  # ergodic, no metallic n
        beta=None,  # not a single base
        measured_energy=-5.042, predicted_energy=None,
        jerkiness=0.157, sharpe=-0.140, rti=0.108,
        particle_analog="Gluon sea",
        role="Entropy vacancy — prevents crystallization",
    ),
}


# ── Compound Definitions ─────────────────────────────────────────────────

@dataclass
class Compound:
    """A compound anti-resonant structure (nested shells)."""
    name: str
    formula: str
    shells: List[Dict]  # [{element: str, n_qubits: int, shell_index: int}, ...]
    particle_analog: str
    predicted_energy: Optional[float]


COMPOUNDS: Dict[str, Compound] = {
    "hydrogen": Compound(
        name="Hydrogen",
        formula="Cu1·Br2·Ag2·Au4",
        shells=[
            {"element": "Cu", "n_qubits": 4, "shell_index": 0},
            {"element": "Br", "n_qubits": 6, "shell_index": 1},
            {"element": "Ag", "n_qubits": 6, "shell_index": 2},
            {"element": "Au", "n_qubits": 4, "shell_index": 3},
        ],
        particle_analog="Hydrogen atom",
        predicted_energy=-7.0,
    ),
    "helium": Compound(
        name="Helium",
        formula="Cu2·Br3·Ag2·Au4",
        shells=[
            {"element": "Cu", "n_qubits": 8, "shell_index": 0},
            {"element": "Br", "n_qubits": 4, "shell_index": 1},
            {"element": "Ag", "n_qubits": 4, "shell_index": 2},
            {"element": "Au", "n_qubits": 4, "shell_index": 3},
        ],
        particle_analog="Helium atom",
        predicted_energy=-7.5,
    ),
    "doped_hydrogen": Compound(
        name="Doped Hydrogen",
        formula="Cu1·Br2·Ag1·Ct1·Au3·Ch1",
        shells=[
            {"element": "Cu", "n_qubits": 4, "shell_index": 0},
            {"element": "Br", "n_qubits": 6, "shell_index": 1},
            {"element": "Ag", "n_qubits": 4, "shell_index": 2},
            {"element": "Ct", "n_qubits": 1, "shell_index": 2},  # dopant
            {"element": "Au", "n_qubits": 4, "shell_index": 3},
            {"element": "Ch", "n_qubits": 1, "shell_index": 3},  # vacancy
        ],
        particle_analog="Doped hydrogen",
        predicted_energy=-7.2,
    ),
}
