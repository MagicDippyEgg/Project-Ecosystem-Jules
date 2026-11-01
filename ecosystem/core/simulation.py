"""Main simulation loop orchestrating the world, organisms, weather, and life cycles."""
import random
import math
from typing import List, Dict, Optional, Tuple, Any
from ecosystem.world.grid import WorldGrid
from ecosystem.world.weather import WeatherSystem, WeatherCondition
from ecosystem.entities.genome import Genome
from ecosystem.entities.organism import Organism, OrganismAction
from ecosystem.entities.species import SpeciesManager
from ecosystem.core.stats import StatsTracker, EcosystemSnapshot

class SpatialHash:
    """Fast 2D spatial partitioning grid for O(1) proximity queries."""

    def __init__(self, cell_size: float = 8.0):
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], List[Organism]] = {}

    def clear(self) -> None:
        self.cells.clear()

    def insert(self, org: Organism) -> None:
        cx = int(org.x // self.cell_size)
        cy = int(org.y // self.cell_size)
        key = (cx, cy)
        if key not in self.cells:
            self.cells[key] = []
        self.cells[key].append(org)

    def query_radius(self, x: float, y: float, radius: float) -> List[Organism]:
        """Returns all organisms within radius."""
        cx = int(x // self.cell_size)
        cy = int(y // self.cell_size)
        cell_r = int(math.ceil(radius / self.cell_size))
        results: List[Organism] = []

        for dy in range(-cell_r, cell_r + 1):
            for dx in range(-cell_r, cell_r + 1):
                key = (cx + dx, cy + dy)
                if key in self.cells:
                    results.extend(self.cells[key])
        return results

class Simulation:
    """The complete self-sustaining artificial ecosystem simulation backend."""

    def __init__(self, width: int = 100, height: int = 70, seed: Optional[int] = None):
        self.seed = seed if seed is not None else random.randint(1, 999999)
        self.rng = random.Random(self.seed)

        self.world = WorldGrid(width=width, height=height, seed=self.seed)
        self.weather = WeatherSystem(seed=self.seed)
        self.species_manager = SpeciesManager()
        self.stats = StatsTracker(record_interval=20, max_history_len=300)

        self.organisms: List[Organism] = []
        self.next_organism_id = 1
        self.spatial_hash = SpatialHash(cell_size=10.0)

        # Simulation control
        self.tick_count = 0
        self.is_paused = False
        self.simulation_speed = 1.0  # Multiplier: 0.5x, 1x, 2x, 5x, 10x
        self.selected_organism_id: Optional[int] = None

        # Journal / Log of historical events
        self.event_log: List[Dict[str, Any]] = []

    def populate_initial_ecosystem(
        self,
        num_herbivores: int = 40,
        num_omnivores: int = 15,
        num_carnivores: int = 8,
    ) -> None:
        """Seed the world with ancestral archetypes that will evolve and branch."""
        # Archetype 1: Herbivore (small, swift, plant-eating)
        herb_proto = Genome(
            size=0.8,
            speed=1.3,
            sense_radius=11.0,
            metabolism=0.85,
            diet=0.08,
            optimal_temperature=20.0,
            lineage_tag="HB-0",
        )

        # Archetype 2: Omnivore (moderate size, adaptive opportunist)
        omni_proto = Genome(
            size=1.2,
            speed=1.0,
            sense_radius=12.0,
            metabolism=1.0,
            diet=0.50,
            optimal_temperature=22.0,
            lineage_tag="OM-0",
        )

        # Archetype 3: Carnivore (large, formidable, predatory)
        carn_proto = Genome(
            size=1.6,
            speed=1.25,
            sense_radius=14.0,
            metabolism=1.25,
            diet=0.92,
            aggression=0.75,
            bravery=0.85,
            optimal_temperature=21.0,
            lineage_tag="CR-0",
        )

        self.spawn_creatures(herb_proto, num_herbivores)
        self.spawn_creatures(omni_proto, num_omnivores)
        self.spawn_creatures(carn_proto, num_carnivores)

        self.log_event("Genesis", f"Ecosystem established with {len(self.organisms)} founding organisms.")

    def spawn_creatures(self, genome: Genome, count: int) -> None:
        """Spawn `count` creatures with a specific genome onto valid walkable tiles."""
        species = self.species_manager.classify_or_speciate(genome, self.tick_count)

        for _ in range(count):
            # Find random walkable location
            for _attempt in range(50):
                rx = self.rng.uniform(2.0, self.world.width - 2.0)
                ry = self.rng.uniform(2.0, self.world.height - 2.0)
                if self.world.is_walkable(rx, ry):
                    break

            org = Organism(
                organism_id=self.next_organism_id,
                species_id=species.species_id,
                genome=genome.mutate(self.rng),
                x=rx,
                y=ry,
                birth_tick=self.tick_count,
            )
            self.next_organism_id += 1
            species.population += 1
            species.total_ever_born += 1
            self.organisms.append(org)

    def trigger_environmental_event(self, condition_name: str) -> None:
        """God-mode or natural event trigger (drought, storm, heatwave, etc.)."""
        try:
            cond = WeatherCondition(condition_name.lower())
            self.weather.transition_weather(force_condition=cond)
            self.log_event("Weather Shift", f"Environmental climate shifted to {cond.name.upper()}!")
        except ValueError:
            pass

    def add_disaster(self, disaster_type: str) -> None:
        """Trigger an ecological catastrophe or boon."""
        if disaster_type == "drought":
            self.weather.transition_weather(WeatherCondition.DROUGHT)
            self.world.vegetation *= 0.3
            self.log_event("Disaster", "Severe drought struck! 70% of vegetation withered.")
        elif disaster_type == "plague":
            killed = 0
            for org in self.organisms:
                if self.rng.random() < 0.4:
                    org.die(self.world, "Plague Outbreak")
                    killed += 1
            self.log_event("Disaster", f"Plague outbreak wiped out {killed} organisms.")
        elif disaster_type == "bloom":
            self.world.vegetation = self.world.max_vegetation.copy()
            self.log_event("Boon", "Super-bloom! All biomes reached maximum lush vegetation.")

    def step(self) -> None:
        """Advance the simulation state by one tick."""
        self.tick_count += 1

        # 1. Update weather and world resources
        self.weather.step()
        self.world.update_resources(self.weather)

        # 2. Build spatial hash for rapid neighborhood queries
        self.spatial_hash.clear()
        for org in self.organisms:
            if org.is_alive:
                self.spatial_hash.insert(org)

        # 3. Simulate all organisms
        new_borns: List[Organism] = []
        dead_count = 0

        for org in self.organisms:
            if not org.is_alive:
                continue

            query_radius = org.genome.sense_radius * self.weather.current_state.visibility_factor
            nearby = self.spatial_hash.query_radius(org.x, org.y, radius=max(8.0, query_radius))
            progeny = org.step(self.world, self.weather, nearby, self.rng)

            if progeny:
                for child in progeny:
                    child.id = self.next_organism_id
                    self.next_organism_id += 1
                    # Classify species or determine speciation drift
                    sp = self.species_manager.classify_or_speciate(child.genome, self.tick_count, ancestor_species_id=org.species_id)
                    child.species_id = sp.species_id
                    sp.population += 1
                    sp.total_ever_born += 1
                    if sp.species_id not in [s.species_id for s in self.species_manager.species_catalog.values() if s.population > 1]:
                        self.log_event("Speciation", f"New species branched: {sp.name} ({sp.description})")
                    new_borns.append(child)
                    self.stats.total_births += 1

        # 4. Integrate newborns & clean up corpses
        self.organisms.extend(new_borns)

        survivors = []
        for org in self.organisms:
            if org.is_alive:
                survivors.append(org)
            else:
                dead_count += 1
                sp = self.species_manager.species_catalog.get(org.species_id)
                if sp:
                    sp.population -= 1
                self.stats.total_deaths += 1

        self.organisms = survivors
        self.species_manager.update_extinctions()

        # 5. Record ecological telemetry snapshot
        if self.stats.should_record(self.tick_count):
            self._record_telemetry()

    def _record_telemetry(self) -> None:
        """Capture ecosystem census data."""
        herbs = sum(1 for o in self.organisms if o.is_herbivore)
        omnis = sum(1 for o in self.organisms if o.is_omnivore)
        carns = sum(1 for o in self.organisms if o.is_carnivore)
        biomass = sum(o.genome.size * 50.0 for o in self.organisms)
        total_veg = float(self.world.vegetation.sum())
        active_sps = sum(1 for s in self.species_manager.species_catalog.values() if not s.extinct)
        extinct_sps = sum(1 for s in self.species_manager.species_catalog.values() if s.extinct)

        avg_spd = (sum(o.genome.speed for o in self.organisms) / len(self.organisms)) if self.organisms else 0.0
        avg_sz = (sum(o.genome.size for o in self.organisms) / len(self.organisms)) if self.organisms else 0.0

        snapshot = EcosystemSnapshot(
            tick=self.tick_count,
            total_population=len(self.organisms),
            herbivore_count=herbs,
            omnivore_count=omnis,
            carnivore_count=carns,
            total_biomass=biomass,
            total_vegetation=total_veg,
            extinct_species_count=extinct_sps,
            active_species_count=active_sps,
            average_speed=avg_spd,
            average_size=avg_sz,
        )
        self.stats.record_snapshot(snapshot)

    def log_event(self, category: str, text: str) -> None:
        """Store historical milestone event in observation journal."""
        self.event_log.append({
            "tick": self.tick_count,
            "day": self.weather.day,
            "category": category,
            "text": text,
        })
        if len(self.event_log) > 200:
            self.event_log.pop(0)

    def get_selected_organism(self) -> Optional[Organism]:
        if self.selected_organism_id is None:
            return None
        return next((o for o in self.organisms if o.id == self.selected_organism_id and o.is_alive), None)

    def select_organism_at(self, world_x: float, world_y: float) -> Optional[Organism]:
        """Finds closest organism to clicked world coordinate."""
        closest = None
        min_dist = 2.5  # Click tolerance
        for org in self.organisms:
            dist = math.hypot(org.x - world_x, org.y - world_y)
            if dist < min_dist:
                min_dist = dist
                closest = org
        if closest:
            self.selected_organism_id = closest.id
        else:
            self.selected_organism_id = None
        return closest
