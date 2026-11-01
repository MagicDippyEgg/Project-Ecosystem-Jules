"""Save and load persistence system for simulation worlds."""
import json
import gzip
import os
from typing import Dict, Any, Optional
from ecosystem.core.simulation import Simulation
from ecosystem.world.grid import WorldGrid
from ecosystem.world.weather import WeatherSystem
from ecosystem.entities.species import SpeciesManager
from ecosystem.entities.organism import Organism
from ecosystem.core.stats import StatsTracker

SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "saves")

class SaveManager:
    """Handles compressed state serialization to persist worlds between application launches."""

    @staticmethod
    def ensure_saves_dir() -> str:
        os.makedirs(SAVES_DIR, exist_ok=True)
        return SAVES_DIR

    @staticmethod
    def save_simulation(sim: Simulation, filename: str) -> str:
        """Saves entire simulation state to a gzipped JSON archive."""
        SaveManager.ensure_saves_dir()
        if not filename.endswith(".eco"):
            filename += ".eco"
        filepath = os.path.join(SAVES_DIR, filename)

        data = {
            "version": "1.0",
            "seed": sim.seed,
            "tick_count": sim.tick_count,
            "next_organism_id": sim.next_organism_id,
            "world": sim.world.to_dict(),
            "weather": sim.weather.to_dict(),
            "species_manager": sim.species_manager.to_dict(),
            "organisms": [o.to_dict() for o in sim.organisms],
            "stats": sim.stats.to_dict(),
            "event_log": sim.event_log,
        }

        json_bytes = json.dumps(data).encode("utf-8")
        with gzip.open(filepath, "wb") as f:
            f.write(json_bytes)

        return filepath

    @staticmethod
    def load_simulation(filepath: str) -> Simulation:
        """Restores a simulation state from an .eco save file."""
        if not os.path.isabs(filepath):
            filepath = os.path.join(SAVES_DIR, filepath)
        if not filepath.endswith(".eco"):
            filepath += ".eco"

        with gzip.open(filepath, "rb") as f:
            data = json.loads(f.read().decode("utf-8"))

        world = WorldGrid.from_dict(data["world"])
        weather = WeatherSystem.from_dict(data["weather"], seed=data["seed"])
        species_manager = SpeciesManager.from_dict(data["species_manager"])
        stats = StatsTracker.from_dict(data["stats"])

        sim = Simulation(width=world.width, height=world.height, seed=data["seed"])
        sim.world = world
        sim.weather = weather
        sim.species_manager = species_manager
        sim.stats = stats
        sim.tick_count = data["tick_count"]
        sim.next_organism_id = data["next_organism_id"]
        sim.event_log = data.get("event_log", [])

        sim.organisms = [Organism.from_dict(d) for d in data["organisms"]]

        return sim

    @staticmethod
    def list_saves() -> list[str]:
        SaveManager.ensure_saves_dir()
        return [f for f in os.listdir(SAVES_DIR) if f.endswith(".eco")]
