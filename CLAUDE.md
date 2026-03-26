# Anti-Resonant Periodic Table — Session Checkpoint

## NEXT SESSION: Pick up here

### What's done
- **Theory document COMPLETE** (paper/theory.md) — nested shell model, Aufbau rules, particle analogy, Rydberg formula
- **Whitepaper COMPLETE** (paper/anti_resonant_periodic_table.tex) — LaTeX RevTeX4-2, results table needs filling
- **IBM Marrakesh experiment COMPLETE** (March 26, 2026) — 180 batched QPU jobs, 6 configurations
- GitHub: https://github.com/Zynerji/AntiResonantPeriodicTable

### Results (from IBM Marrakesh)
```
B. Helium (Cu8·Br4·Ag4·Au4):    -3.494  *** BEATS BRONZE ***
D. Pure Bronze:                   -3.314  (control)
F. Uniform:                       -2.515  (baseline)
E. Pure Golden:                   -2.367  (control)
A. Hydrogen (Cu4·Br6·Ag6·Au4):   -2.039  (underperformed)
C. Doped H:                       -2.006  (underperformed)
```

### What went wrong with Hydrogen
The shell weight scaling `1/(s+1)` is too aggressive. Core qubits get weight ~0.37, shell qubits get ~0.0005. The Hamiltonian coupling terms `alpha_i * alpha_j` between core and shell become negligible (~10^-4), effectively decoupling the shells. Helium works because its 8 copper core qubits dominate — it's essentially pure copper with golden decoration.

### CRITICAL FIX NEEDED
In `arpt/shell_builder.py`, the `compound_weights()` function uses:
```python
shell_scale = 1.0 / (shell["shell_index"] + 1)
```
This must be changed to one of:
- `shell_scale = 1.0 / math.sqrt(shell["shell_index"] + 1)` (gentler falloff)
- `shell_scale = 1.0` (equal shell importance, let metallic mean handle anti-resonance)
- `shell_scale = n_shell / n_total` (proportional to qubit count)

Then re-run the experiment. With correct normalization, Hydrogen should beat bronze because the golden shell will actually COUPLE to the bronze core through the Hamiltonian.

### What needs doing (in priority order)

1. **Fix shell weight normalization** — Change the one line above, re-run 6 configs (~180 jobs, ~15 min QPU). This is the highest-priority fix.

2. **Fill in the whitepaper results table** — `paper/anti_resonant_periodic_table.tex` has TBD entries. Fill from `results/periodic_table_marrakesh.json` (or from the re-run if normalization is fixed first).

3. **Add the 40 novelties analysis** — Run `compute_metrics.py` and `compute_novelties_21_40.py` (from QuantumGoldenPendulum) on the periodic table data to derive RSM, DUAR, spectral entropy, etc. for compounds.

4. **Test shell ordering** — Run a control where shells are assigned randomly (not Aufbau order) to prove that ordering matters. If random = Aufbau, the theory is weaker.

### Architecture
```
arpt/
  elements.py      — 7 elements (Au, Ag, Br, Cu, Ni, Ct, Ch) with properties
  shell_builder.py — compound_weights() + build_shell_ansatz() [NEEDS FIX]
run_experiment.py  — Full 6-config experiment with batched SPSA
paper/
  theory.md        — Full theory document (markdown)
  anti_resonant_periodic_table.tex — LaTeX whitepaper
results/
  periodic_table_marrakesh.json — Raw results from IBM run
```

### Dependencies
- Imports from `../QuantumGoldenPendulum/quantum_golden_pendulum/` (anti_resonant_weights, hamiltonian, calibration, optimizer)
- sys.path.insert resolves this at runtime

### IBM allocation
- CHECK DASHBOARD — approximately 74 min remaining as of March 26, 2026
- Each full run = 180 batched jobs, ~15 min QPU, ~250 min wall time
- QPU billing = full job wall time (not just gate execution)

### The bigger picture
This project extends QuantumGoldenPendulum (which proved anti-resonant encoding works on hardware) into a structural theory (nested shells, periodic table, compounds). The key open question: **does shell nesting provide emergent benefit beyond the sum of individual elements?** Helium (+5.4% vs bronze) says yes, but only barely and possibly due to more copper qubits rather than shell interaction. The normalization fix will answer this definitively.
