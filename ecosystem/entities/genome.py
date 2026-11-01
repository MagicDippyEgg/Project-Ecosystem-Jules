"""Genetic genome encoding individual organism traits and hereditary evolutionary mechanics."""
import random
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple

# Dietary inclinations
DIET_HERBIVORE = 0.0   # Feeds strictly on plants
DIET_OMNIVORE = 0.5    # Feeds on plants and meat/carrion
DIET_CARNIVORE = 1.0   # Feeds on other organisms and carrion

@dataclass
class Genome:
    """Contains alleles and physiological/behavioral traits of an organism."""
    # Physical traits
    size: float = 1.0                  # [0.5, 2.5] Larger: more max energy/health, slower, higher metabolism
    speed: float = 1.0                 # [0.4, 2.5] Movement velocity per tick
    sense_radius: float = 8.0          # [3.0, 24.0] Detection radius for food, water, mates, danger
    metabolism: float = 1.0            # [0.5, 2.0] Basal energy burn rate multiplier
    armor: float = 0.0                 # [0.0, 0.8] Defense percentage against physical attacks

    # Ecological & Dietary traits
    diet: float = 0.0                  # [0.0 = pure herbivore, 0.5 = omnivore, 1.0 = pure carnivore]
    optimal_temperature: float = 20.0  # [-5.0, 38.0] Optimal ambient Celsius temperature
    temperature_tolerance: float = 15.0# [5.0, 25.0] Tolerance range (+/-) before suffering thermal stress

    # Reproduction traits
    reproduction_threshold: float = 0.75 # [0.5, 0.95] Fraction of max energy required to attempt mating
    litter_size: int = 1               # [1, 4] Offspring produced per birth
    gestation_time: int = 80           # [40, 200] Ticks required to carry offspring
    mutation_rate: float = 0.12        # [0.02, 0.35] Probability/magnitude of mutation per gene

    # Behavioral traits
    aggression: float = 0.1            # [0.0, 1.0] Inclination to fight/hunt vs flee
    bravery: float = 0.3               # [0.0, 1.0] Tolerance to predator proximity before fleeing
    sociability: float = 0.5           # [0.0, 1.0] Affinity for grouping near conspecifics

    # Visual pigmentation (RGB tuple, derived from diet and thermal/speed genes)
    color: Tuple[int, int, int] = (80, 190, 80)

    # Genetic lineage identifier (generational branch tracking)
    lineage_tag: str = "P-0"

    def __post_init__(self):
        self._derive_color()

    def _derive_color(self) -> None:
        """Derive visual pigmentation dynamically from genetic makeup."""
        # Red component is influenced by carnivory (diet) and aggression
        r = int(math.tanh(self.diet * 1.5 + self.aggression * 0.8) * 200 + 40)
        # Green component is influenced by herbivory and optimal temp
        g = int(math.tanh((1.0 - self.diet) * 1.5 + max(0, self.optimal_temperature) / 40.0) * 180 + 40)
        # Blue component is influenced by speed, armor, or cold adaptation
        b = int(math.tanh((self.speed / 2.0) + (self.armor * 1.2) + max(0, 20.0 - self.optimal_temperature) / 25.0) * 180 + 35)

        self.color = (
            max(20, min(240, r)),
            max(20, min(240, g)),
            max(20, min(240, b))
        )

    def mutate(self, rng: random.Random) -> "Genome":
        """Produce an offspring genome with potential mutations."""
        mr = self.mutation_rate

        def perturb(val: float, low: float, high: float, scale: float = 0.1) -> float:
            if rng.random() < mr:
                delta = rng.gauss(0.0, (high - low) * scale)
                return max(low, min(high, val + delta))
            return val

        def perturb_int(val: int, low: int, high: int) -> int:
            if rng.random() < mr:
                val += rng.choice([-1, 1])
                return max(low, min(high, val))
            return val

        new_size = perturb(self.size, 0.4, 2.8, 0.08)
        new_speed = perturb(self.speed, 0.3, 2.5, 0.08)
        new_sense = perturb(self.sense_radius, 3.0, 26.0, 0.10)
        new_metabolism = perturb(self.metabolism, 0.5, 2.2, 0.08)
        new_armor = perturb(self.armor, 0.0, 0.8, 0.08)
        new_diet = perturb(self.diet, 0.0, 1.0, 0.10)
        new_opt_temp = perturb(self.optimal_temperature, -5.0, 40.0, 0.08)
        new_temp_tol = perturb(self.temperature_tolerance, 5.0, 25.0, 0.08)
        new_repro_thresh = perturb(self.reproduction_threshold, 0.5, 0.95, 0.05)
        new_litter = perturb_int(self.litter_size, 1, 4)
        new_gestation = perturb_int(self.gestation_time, 40, 220)
        new_mutation_rate = perturb(self.mutation_rate, 0.02, 0.35, 0.05)
        new_aggression = perturb(self.aggression, 0.0, 1.0, 0.10)
        new_bravery = perturb(self.bravery, 0.0, 1.0, 0.10)
        new_sociability = perturb(self.sociability, 0.0, 1.0, 0.10)

        # Generate mutated lineage tag
        tag_parts = self.lineage_tag.split("-")
        prefix = tag_parts[0]
        gen = int(tag_parts[1]) if len(tag_parts) > 1 and tag_parts[1].isdigit() else 0
        new_tag = f"{prefix}-{gen + 1}"

        g = Genome(
            size=new_size,
            speed=new_speed,
            sense_radius=new_sense,
            metabolism=new_metabolism,
            armor=new_armor,
            diet=new_diet,
            optimal_temperature=new_opt_temp,
            temperature_tolerance=new_temp_tol,
            reproduction_threshold=new_repro_thresh,
            litter_size=new_litter,
            gestation_time=new_gestation,
            mutation_rate=new_mutation_rate,
            aggression=new_aggression,
            bravery=new_bravery,
            sociability=new_sociability,
            lineage_tag=new_tag,
        )
        return g

    @classmethod
    def crossover(cls, parent_a: "Genome", parent_b: "Genome", rng: random.Random) -> "Genome":
        """Recombine traits from two parents with mendelian crossover."""
        def pick(a, b):
            return a if rng.random() < 0.5 else b

        child_proto = cls(
            size=pick(parent_a.size, parent_b.size),
            speed=pick(parent_a.speed, parent_b.speed),
            sense_radius=pick(parent_a.sense_radius, parent_b.sense_radius),
            metabolism=pick(parent_a.metabolism, parent_b.metabolism),
            armor=pick(parent_a.armor, parent_b.armor),
            diet=pick(parent_a.diet, parent_b.diet),
            optimal_temperature=pick(parent_a.optimal_temperature, parent_b.optimal_temperature),
            temperature_tolerance=pick(parent_a.temperature_tolerance, parent_b.temperature_tolerance),
            reproduction_threshold=pick(parent_a.reproduction_threshold, parent_b.reproduction_threshold),
            litter_size=pick(parent_a.litter_size, parent_b.litter_size),
            gestation_time=pick(parent_a.gestation_time, parent_b.gestation_time),
            mutation_rate=pick(parent_a.mutation_rate, parent_b.mutation_rate),
            aggression=pick(parent_a.aggression, parent_b.aggression),
            bravery=pick(parent_a.bravery, parent_b.bravery),
            sociability=pick(parent_a.sociability, parent_b.sociability),
            lineage_tag=parent_a.lineage_tag,
        )
        # Apply mutation on top of recombined genome
        return child_proto.mutate(rng)

    def genetic_distance(self, other: "Genome") -> float:
        """Computes Euclidean/normalized genetic distance to determine speciation."""
        diffs = [
            (self.size - other.size) / 2.0,
            (self.speed - other.speed) / 2.0,
            (self.sense_radius - other.sense_radius) / 20.0,
            (self.diet - other.diet),
            (self.aggression - other.aggression),
            (self.optimal_temperature - other.optimal_temperature) / 30.0,
            (self.armor - other.armor),
        ]
        return math.sqrt(sum(d * d for d in diffs))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "size": self.size,
            "speed": self.speed,
            "sense_radius": self.sense_radius,
            "metabolism": self.metabolism,
            "armor": self.armor,
            "diet": self.diet,
            "optimal_temperature": self.optimal_temperature,
            "temperature_tolerance": self.temperature_tolerance,
            "reproduction_threshold": self.reproduction_threshold,
            "litter_size": self.litter_size,
            "gestation_time": self.gestation_time,
            "mutation_rate": self.mutation_rate,
            "aggression": self.aggression,
            "bravery": self.bravery,
            "sociability": self.sociability,
            "color": list(self.color),
            "lineage_tag": self.lineage_tag,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Genome":
        color = tuple(data.get("color", (100, 100, 100)))
        g = cls(
            size=data["size"],
            speed=data["speed"],
            sense_radius=data["sense_radius"],
            metabolism=data["metabolism"],
            armor=data["armor"],
            diet=data["diet"],
            optimal_temperature=data["optimal_temperature"],
            temperature_tolerance=data["temperature_tolerance"],
            reproduction_threshold=data["reproduction_threshold"],
            litter_size=data["litter_size"],
            gestation_time=data["gestation_time"],
            mutation_rate=data["mutation_rate"],
            aggression=data["aggression"],
            bravery=data["bravery"],
            sociability=data["sociability"],
            color=color,
            lineage_tag=data.get("lineage_tag", "P-0"),
        )
        return g
