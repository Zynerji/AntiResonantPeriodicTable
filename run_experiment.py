"""Run the Anti-Resonant Periodic Table experiment on IBM Marrakesh.

Tests 6 configurations:
    A. Hydrogen (Cu1·Br2·Ag2·Au4) — nested shell composite
    B. Helium (Cu2·Br3·Ag2·Au4) — double core
    C. Doped Hydrogen (Cu1·Br2·Ag1·Ct1·Au3·Ch1) — with dopant + vacancy
    D. Pure Bronze (control) — all qubits bronze
    E. Pure Golden (control) — all qubits golden
    F. Uniform (baseline) — all qubits 1/N

Each configuration: 30 SPSA iterations, 20 qubits, coupled pendulum Hamiltonian.
Total: 6 configs x 60 jobs = ~360 jobs, ~15 min QPU.
"""

import json
import logging
import math
import sys
import time
from pathlib import Path

import numpy as np
from qiskit import transpile
from qiskit.quantum_info import SparsePauliOp
from qiskit_ibm_runtime import EstimatorV2, QiskitRuntimeService

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "QuantumGoldenPendulum"))
from quantum_golden_pendulum.anti_resonant_weights import anti_resonant_weights, weights_to_angles
from quantum_golden_pendulum.calibration import pull_calibration, select_qubit_subset
from quantum_golden_pendulum.hamiltonian import build_pendulum_hamiltonian
from quantum_golden_pendulum.optimizer import SPSAOptimizer

from arpt.elements import ELEMENTS, metallic_mean
from arpt.shell_builder import build_shell_ansatz, compound_weights, describe_compound

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

PHI = (1 + math.sqrt(5)) / 2
N_QUBITS = 20
N_VAR_LAYERS = 2
MAX_ITER = 30
SHOTS = 4000


def run_config(backend, transpiled, H_padded, n_params, name):
    """Run SPSA optimization for a single configuration."""
    spsa = SPSAOptimizer(n_params=n_params, lam=0.5, A=3)
    energies = []
    best_energy = float("inf")
    best_step = 0
    total_jobs = 0

    for k in range(1, MAX_ITER + 1):
        ck = spsa.c / k ** spsa.gamma
        ak = spsa.a / (k + spsa.A) ** spsa.alpha
        delta = np.random.choice([-1, 1], size=n_params).astype(float)

        # Batch both SPSA evaluations into a single EstimatorV2 call (2 PUBs)
        # This halves network round-trips vs 2 separate submissions
        p_plus = spsa.params + ck * delta
        p_minus = spsa.params - ck * delta
        est = EstimatorV2(mode=backend)
        job = est.run([
            (transpiled, H_padded, p_plus),
            (transpiled, H_padded, p_minus),
        ])
        result = job.result()
        total_jobs += 1  # 1 batched job instead of 2

        e_plus = float(result[0].data.evs)
        e_minus = float(result[1].data.evs)

        g_hat = (e_plus - e_minus) / (2.0 * ck * delta)
        spsa.params -= ak * g_hat
        spsa.params = np.clip(spsa.params, -2 * np.pi, 2 * np.pi)

        e_mid = (e_plus + e_minus) / 2.0
        energies.append(e_mid)
        if e_mid < best_energy:
            best_energy = e_mid
            best_step = k

        if k % 10 == 0 or k == MAX_ITER:
            print(f"    [{k:>3d}/{MAX_ITER}] E={e_mid:+.4f} (best={best_energy:+.4f})")

    return {
        "energies": [float(e) for e in energies],
        "best_energy": float(best_energy),
        "best_step": best_step,
        "total_jobs": total_jobs,
    }


def main():
    print("=" * 70)
    print("ANTI-RESONANT PERIODIC TABLE — IBM MARRAKESH EXPERIMENT")
    print("Testing nested shell compounds vs pure elements")
    print("=" * 70)

    service = QiskitRuntimeService(instance="open-instance")
    backend = service.backend("ibm_marrakesh")
    print(f"Backend: {backend.name}, status={backend.status().status_msg}")

    cal = pull_calibration(backend)
    qubits, edges = select_qubit_subset(cal, N_QUBITS)
    qubit_map = {q: i for i, q in enumerate(qubits)}
    local_edges = [
        (qubit_map[i], qubit_map[j])
        for (i, j) in edges
        if i in qubit_map and j in qubit_map
    ]
    print(f"Selected {N_QUBITS} qubits: {qubits} ({len(local_edges)} edges)")

    # ── Define configurations ─────────────────────────────────────────
    configs = [
        # Compounds (nested shells)
        ("A_hydrogen", "hydrogen"),
        ("B_helium", "helium"),
        ("C_doped_hydrogen", "doped_hydrogen"),
        # Pure elements (controls)
        ("D_pure_bronze", None),
        ("E_pure_golden", None),
        ("F_uniform", None),
    ]

    all_results = {}
    t_start = time.monotonic()
    total_jobs = 0

    for config_name, compound_name in configs:
        print(f"\n{'=' * 60}")
        print(f"CONFIG: {config_name}")

        if compound_name:
            # Nested shell compound
            print(describe_compound(compound_name))
            w = compound_weights(compound_name, N_QUBITS)
        elif "bronze" in config_name:
            w = anti_resonant_weights(N_QUBITS, base=metallic_mean(3))
        elif "golden" in config_name:
            w = anti_resonant_weights(N_QUBITS, base=PHI)
        else:
            w = np.ones(N_QUBITS) / N_QUBITS

        print(f"Weights (first 8): {w[:8].round(4)}")
        print(f"{'=' * 60}")

        ansatz, params = build_shell_ansatz(N_QUBITS, w, local_edges, N_VAR_LAYERS)
        H = build_pendulum_hamiltonian(N_QUBITS, w, local_edges)

        transpiled = transpile(ansatz, backend=backend, optimization_level=2)
        depth = transpiled.depth()
        print(f"Transpiled: depth={depth}, gates={transpiled.size()}")

        if depth > 150:
            print("SKIP: depth > 150")
            continue

        # Pad observable
        cq = transpiled.num_qubits
        oq = H.num_qubits
        if oq < cq:
            pad = "I" * (cq - oq)
            H_padded = SparsePauliOp.from_list(
                [(pad + str(p), c) for p, c in zip(H.paulis, H.coeffs)]
            ).simplify()
        else:
            H_padded = H

        n_p = len(transpiled.parameters)
        result = run_config(backend, transpiled, H_padded, n_p, config_name)
        total_jobs += result["total_jobs"]

        all_results[config_name] = {
            "compound": compound_name,
            **result,
            "is_compound": compound_name is not None,
        }
        print(f"  RESULT: best_E={result['best_energy']:+.4f} at step {result['best_step']}")

    # ── Summary ───────────────────────────────────────────────────────
    dt = time.monotonic() - t_start
    print(f"\n{'=' * 70}")
    print("ANTI-RESONANT PERIODIC TABLE — RESULTS")
    print(f"{'=' * 70}")
    print(f"{'Config':<25s} {'Best E':>10s} {'Step':>5s} {'vs Bronze':>10s} {'Type':>12s}")
    print("-" * 65)

    bronze_e = all_results.get("D_pure_bronze", {}).get("best_energy", -6.532)
    for name in ["A_hydrogen", "B_helium", "C_doped_hydrogen",
                  "D_pure_bronze", "E_pure_golden", "F_uniform"]:
        if name in all_results:
            r = all_results[name]
            vs_bronze = ((r["best_energy"] - bronze_e) / abs(bronze_e)) * 100
            typ = "COMPOUND" if r["is_compound"] else "CONTROL"
            marker = " ***" if r["best_energy"] < bronze_e else ""
            print(
                f"{name:<25s} {r['best_energy']:>+10.4f} {r['best_step']:>5d} "
                f"{vs_bronze:>+9.1f}% {typ:>12s}{marker}"
            )

    print(f"\nTotal: {dt:.0f}s wall, {total_jobs} QPU jobs")

    # Verdict
    hydrogen_e = all_results.get("A_hydrogen", {}).get("best_energy", 0)
    if hydrogen_e < bronze_e:
        print(f"\n*** THEORY CONFIRMED: Hydrogen ({hydrogen_e:.3f}) beats Bronze ({bronze_e:.3f}) ***")
    else:
        print(f"\n    Theory not confirmed: Hydrogen ({hydrogen_e:.3f}) vs Bronze ({bronze_e:.3f})")

    out = Path("results/periodic_table_marrakesh.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Results saved to {out}")


if __name__ == "__main__":
    main()
