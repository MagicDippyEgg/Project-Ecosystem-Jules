# Project Ecosystem: Native Artificial Life Simulation

Project Ecosystem is a self-sustaining artificial life simulation running as a native Linux desktop application. Organisms live, make autonomous survival decisions, reproduce with genetic inheritance and mutations, compete for natural resources, and evolve over generations in a procedurally generated world.

---

## Key Features

### 1. Procedural World & Environment
- **Multi-Octave Terrain**: Elevation and moisture fields generating diverse biomes (Deep Ocean, Shallow Water, Beach, Plains, Forest, Rainforest, Savanna, Desert, Tundra, Mountain).
- **Dynamic Resource Dynamics**: Continuous plant/vegetation growth governed by biome fertility, sunlight, and moisture; decomposing carrion deposits from deceased creatures.
- **Day/Night Cycle & Seasons**: Cosine daylight illumination affecting vision and plant photosynthesis; seasonal annual temperature curves.
- **Dynamic Weather System**: Clear, Cloudy, Rain, Storms, Droughts, Heatwaves, and Cold Snaps affecting visibility, animal stamina drain, and moisture.

### 2. Autonomous Organisms & True Genetics
- **Continuous Genome Traits**:
  - Size, speed, sensory radius, basal metabolism, natural armor defense.
  - Diet inclination (Herbivore, Omnivore, Apex Carnivore).
  - Thermal preference & temperature tolerance window.
  - Behavioral genes: Aggression, bravery, sociability, mating thresholds.
- **Mendelian Crossover & Mutation**: Sexual recombination between mates, point mutations, and speciation distance metrics.
- **Autonomous Utility-Based AI**:
  - Real-time evaluation of hunger, thirst, thermal stress, predator proximity, and mating availability.
  - Foraging, drinking from water sources, cooperative flocking, predatory stalking, sprint evasions, and resting.
  - True life cycle: birth, maturation, ageing, energy exhaustion, starvation, dehydration, predation, and death.

### 3. Evolutionary Speciation & Lineages
- Dynamic taxonomic classification clustering genomes into distinct species with scientific nomenclature.
- Lineage generational tags (`HB-0 -> HB-1 -> ...`) and genealogical parent tracking.
- Extinction tracking and living biodiversity metrics.

### 4. Native Linux Desktop User Interface
- **Interactive Viewport**: Smooth camera panning (WASD / middle mouse drag) and zooming (scroll wheel / +/-).
- **Entity Inspector**: Click on any organism to lock the camera and inspect live vitals (Health, Energy, Hydration), current goal, genetic alleles, family lineage, and lifetime records.
- **Real-Time Ecological Charts**: Sparkline multi-series graphs tracking herbivore, omnivore, and carnivore populations over time.
- **Species Catalog & Observation Journal**: Live census records, newly branched species milestones, and ecological events.
- **World Generation & Interventions ("God Mode")**:
  - Generate fresh procedural worlds with custom seeds.
  - Trigger meteorological disasters (Droughts, Storms, Plagues) or ecological boons (Super-Blooms).
- **Save & Load Persistence**: Compressed `.eco` archives persisting complete world state, entity genomes, and timeline history.

---

## Installation & Running

### Requirements
- Linux OS (Ubuntu 20.04+, Debian, Fedora, Arch, etc.)
- Python 3.10+
- Dependencies: `pygame`, `numpy`, `pytest`

### Quick Start
To launch the application:
```bash
./bin/ecosystem
```
or directly via Python:
```bash
python3 main.py
```

### Controls & Keyboard Shortcuts
- **W / A / S / D** or **Arrow Keys**: Pan camera viewport
- **Mouse Drag (Middle Click / Ctrl + Left Click)**: Pan camera smoothly
- **Mouse Scroll Wheel** or **+ / -**: Zoom in and out
- **Left Click**: Select organism to inspect and track with camera
- **Top Toolbar Buttons**:
  - `Pause / Resume`: Toggle simulation stepping
  - `Speed Toggle (0.5x, 1x, 2x, 5x, 10x)`: Adjust simulation velocity
  - `Save`: Save current state to `saves/`
  - `Load`: Restore previous simulation state
  - `New World`: Procedurally regenerate a pristine world
- **Right Sidebar Tabs**:
  - `Stats`: Real-time ecosystem census breakdown
  - `Species`: Evolutionary taxonomy catalog and status
  - `Journal`: Chronological record of major events and speciation
  - `GodMode`: Ecological interventions and disaster triggers

---

## Running the Automated Test Suite

Project Ecosystem includes unit and integration tests covering world generation, genetics, organism metabolism, predator-prey dynamics, and simulation longevity:

```bash
pytest -v tests/
```
