"""Species taxonomy, cataloging, and evolutionary lineage management."""
import math
from typing import List, Dict, Optional, Tuple
from ecosystem.entities.genome import Genome

class Species:
    """Represents an evolving taxonomic species cluster."""

    def __init__(self, species_id: int, name: str, archetype_genome: Genome, color: Tuple[int, int, int]):
        self.species_id = species_id
        self.name = name
        self.archetype_genome = archetype_genome
        self.color = color
        self.population = 0
        self.total_ever_born = 0
        self.generation_appeared = 0
        self.extinct = False
        self.ancestor_species_id: Optional[int] = None
        self.description = self._generate_description()

    def _generate_description(self) -> str:
        g = self.archetype_genome
        diet_str = "Herbivore" if g.diet < 0.33 else ("Omnivore" if g.diet < 0.66 else "Apex Carnivore")
        temp_str = "Cold-adapted" if g.optimal_temperature < 10 else ("Temperate" if g.optimal_temperature < 25 else "Warm-adapted")
        size_str = "Minute" if g.size < 0.8 else ("Medium" if g.size < 1.4 else "Bulky / Gigantic")
        return f"{size_str} {temp_str} {diet_str}"

    def matches(self, genome: Genome, threshold: float = 0.55) -> bool:
        """Determines if a genome belongs to this species cluster."""
        return self.archetype_genome.genetic_distance(genome) <= threshold

class SpeciesManager:
    """Maintains species classification, dynamic speciation, and evolutionary trees."""

    def __init__(self):
        self.species_catalog: Dict[int, Species] = {}
        self.next_species_id = 1
        self._name_prefixes = [
            "Aero", "Bio", "Chloro", "Dendro", "Eco", "Ferro", "Geo", "Hydro",
            "Ignis", "Litho", "Morpho", "Necro", "Oro", "Proto", "Silvi", "Therma", "Velo", "Xeno"
        ]
        self._name_suffixes = [
            "saurus", "pod", "vora", "nyx", "therium", "pteryx", "phage", "morph",
            "lophus", "raptor", "ceps", "don", "gaster", "rhinus", "pus"
        ]

    def _generate_species_name(self, genome: Genome) -> str:
        p_idx = int(genome.size * 5 + genome.optimal_temperature) % len(self._name_prefixes)
        s_idx = int(genome.speed * 4 + genome.diet * 7) % len(self._name_suffixes)
        return f"{self._name_prefixes[p_idx]}{self._name_suffixes[s_idx]}"

    def classify_or_speciate(self, genome: Genome, current_tick: int, ancestor_species_id: Optional[int] = None) -> Species:
        """Finds closest matching species or forms a new branch if genetically divergent."""
        best_species = None
        min_dist = 999.0

        for sp in self.species_catalog.values():
            if sp.extinct:
                continue
            dist = sp.archetype_genome.genetic_distance(genome)
            if dist < min_dist:
                min_dist = dist
                best_species = sp

        # Speciation threshold (e.g. 0.58 distance)
        if best_species is not None and min_dist <= 0.58:
            return best_species

        # Create a new species!
        sp_id = self.next_species_id
        self.next_species_id += 1
        name = f"{self._generate_species_name(genome)} #{sp_id}"
        new_sp = Species(
            species_id=sp_id,
            name=name,
            archetype_genome=genome,
            color=genome.color,
        )
        new_sp.generation_appeared = current_tick // 600
        new_sp.ancestor_species_id = ancestor_species_id
        self.species_catalog[sp_id] = new_sp
        return new_sp

    def update_extinctions(self) -> None:
        """Mark species with 0 active population as extinct."""
        for sp in self.species_catalog.values():
            if sp.population <= 0 and sp.total_ever_born > 0:
                sp.extinct = True

    def to_dict(self) -> Dict:
        return {
            "next_id": self.next_species_id,
            "species": [
                {
                    "id": sp.species_id,
                    "name": sp.name,
                    "archetype": sp.archetype_genome.to_dict(),
                    "color": list(sp.color),
                    "population": sp.population,
                    "total_ever_born": sp.total_ever_born,
                    "generation_appeared": sp.generation_appeared,
                    "extinct": sp.extinct,
                    "ancestor_species_id": sp.ancestor_species_id,
                    "description": sp.description,
                }
                for sp in self.species_catalog.values()
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SpeciesManager":
        sm = cls()
        sm.next_species_id = data.get("next_id", 1)
        for d in data.get("species", []):
            sp = Species(
                species_id=d["id"],
                name=d["name"],
                archetype_genome=Genome.from_dict(d["archetype"]),
                color=tuple(d["color"]),
            )
            sp.population = d["population"]
            sp.total_ever_born = d["total_ever_born"]
            sp.generation_appeared = d["generation_appeared"]
            sp.extinct = d["extinct"]
            sp.ancestor_species_id = d["ancestor_species_id"]
            sp.description = d.get("description", sp.description)
            sm.species_catalog[sp.species_id] = sp
        return sm
