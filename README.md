# Anti-Resonant Periodic Table

**Nested metallic mean shells as subatomic structure for quantum optimization on IBM Marrakesh.**

## Core Idea

Bronze goes deepest (-6.53). Golden is smoothest (jerk=0.12). Neither is optimal alone. **Nest them**: bronze core for depth, golden shell for stability. Like protons (strong force) surrounded by electrons (orbital stability).

Each metallic mean is an "element." Compounds are nested shell structures. The periodic table organizes them by depth vs stability with Aufbau filling rules.

## The Periodic Table

| Element | Symbol | n | Beta | Role | Particle Analog |
|---------|--------|---|------|------|-----------------|
| Golden | Au | 1 | 1.618 | Stability shell | Electron |
| Silver | Ag | 2 | 2.414 | Mediator | Gluon |
| Bronze | Br | 3 | 3.303 | Depth driver | Down quark |
| Copper | Cu | 4 | 4.236 | Ultra-deep seed | Up quark |
| Nickel | Ni | 5 | 5.193 | Heavy depth | Charm quark |
| Cocktail | Ct | - | 2.493 | Dopant | Photon |
| Chaotic | Ch | - | ergodic | Vacancy | Gluon sea |

## Compounds Tested

| Compound | Formula | Structure | Predicted E |
|----------|---------|-----------|-------------|
| Hydrogen | Cu1-Br2-Ag2-Au4 | Core + 3 shells | < -7.0 |
| Helium | Cu2-Br3-Ag2-Au4 | Double core | < -7.5 |
| Doped H | Cu1-Br2-Ag1-Ct1-Au3-Ch1 | With dopant + vacancy | < -7.2 |

## Scaling Law

```
E(n) = -0.705 * n - 4.416
```

Linear in metallic mean index — no ionization limit.

## Run

```bash
python run_experiment.py
```

## Theory

See [paper/theory.md](paper/theory.md) for full derivation.

## Author

Christian Knopp (cknopp@gmail.com)

All ideas, concepts, and novelties by the author. Code and documentation by Claude Code Opus 4.6.
