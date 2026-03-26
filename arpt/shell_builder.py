"""Build nested shell ansatz circuits for compound anti-resonant structures.

Each shell gets its own metallic mean encoding in Layer 0, then all qubits
share the same variational layers. The hardware coupling map determines
which qubits are physically adjacent.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector

from .elements import COMPOUNDS, ELEMENTS, Compound


def compound_weights(compound_name: str, n_qubits: int = 20) -> np.ndarray:
    """Generate the nested shell weight vector for a compound.

    Each qubit gets a weight determined by its shell's metallic mean.
    Within a shell, weights follow the standard anti-resonant power law.

    Args:
        compound_name: Key in COMPOUNDS dict.
        n_qubits: Total qubit count (must match compound definition).

    Returns:
        Weight vector of shape (n_qubits,), summing to 1.0.
    """
    compound = COMPOUNDS[compound_name]

    weights = np.zeros(n_qubits)
    qubit_idx = 0

    for shell in compound.shells:
        elem = ELEMENTS[shell["element"]]
        n_shell = shell["n_qubits"]

        if elem.beta is not None:
            # Standard metallic mean weights within this shell
            shell_weights = np.array([elem.beta ** k for k in range(n_shell)])
        else:
            # Chaotic element: use logistic map
            x = 1.0 / ((1 + math.sqrt(5)) / 2)  # seed = 1/phi
            for _ in range(1000):  # burn-in
                x = 4.0 * x * (1.0 - x)
            shell_weights = []
            for _ in range(n_shell):
                x = 4.0 * x * (1.0 - x)
                shell_weights.append(max(x, 0.01))
            shell_weights = np.array(shell_weights)

        # Normalize within shell
        shell_weights = shell_weights / shell_weights.sum()

        # Scale by shell importance (inner shells get more weight)
        shell_scale = 1.0 / (shell["shell_index"] + 1)
        weights[qubit_idx:qubit_idx + n_shell] = shell_weights * shell_scale

        qubit_idx += n_shell

    # Global normalization
    weights = weights / weights.sum()
    return weights


def build_shell_ansatz(
    n_qubits: int,
    weights: np.ndarray,
    coupling_edges: List[Tuple[int, int]],
    n_var_layers: int = 2,
) -> Tuple[QuantumCircuit, ParameterVector]:
    """Build the nested shell ansatz circuit.

    Identical structure to the QuantumGoldenPendulum ansatz, but the
    fixed Layer 0 angles come from the compound's nested shell weights
    instead of a single metallic mean.

    Args:
        n_qubits: Total qubit count.
        weights: Nested shell weight vector from compound_weights().
        coupling_edges: Hardware edges (local indices).
        n_var_layers: Trainable variational layers.

    Returns:
        (circuit, parameters) tuple.
    """
    fixed_angles = 2.0 * np.pi * weights

    n_params = 2 * n_qubits * n_var_layers
    params = ParameterVector("s", n_params)

    qc = QuantumCircuit(n_qubits, name="NestedShellAnsatz")

    # Layer 0: nested shell anti-resonant encoding
    qc.barrier(label="shell_encoding")
    for k in range(n_qubits):
        qc.ry(float(fixed_angles[k]), k)

    # Variational layers (same as QuantumGoldenPendulum)
    edges_even = [(i, j) for idx, (i, j) in enumerate(coupling_edges) if idx % 2 == 0]
    edges_odd = [(i, j) for idx, (i, j) in enumerate(coupling_edges) if idx % 2 == 1]

    param_idx = 0
    for layer in range(n_var_layers):
        qc.barrier(label=f"var_{layer}")
        for k in range(n_qubits):
            qc.ry(params[param_idx], k)
            param_idx += 1
            qc.rz(params[param_idx], k)
            param_idx += 1

        edge_set = edges_even if layer % 2 == 0 else edges_odd
        for (i, j) in edge_set:
            if i < n_qubits and j < n_qubits:
                qc.cx(i, j)

    return qc, params


def describe_compound(compound_name: str) -> str:
    """Pretty-print a compound's shell structure."""
    compound = COMPOUNDS[compound_name]
    lines = [
        f"Compound: {compound.name} ({compound.formula})",
        f"Analog: {compound.particle_analog}",
        f"Predicted energy: {compound.predicted_energy}",
        f"Shells:",
    ]
    qubit_idx = 0
    for shell in compound.shells:
        elem = ELEMENTS[shell["element"]]
        n = shell["n_qubits"]
        lines.append(
            f"  Shell {shell['shell_index']}: "
            f"qubits {qubit_idx}-{qubit_idx + n - 1} "
            f"= {elem.name} ({elem.symbol}, n={elem.n}, "
            f"beta={f'{elem.beta:.3f}' if elem.beta else 'chaotic'}) "
            f"[{elem.role}]"
        )
        qubit_idx += n
    return "\n".join(lines)
