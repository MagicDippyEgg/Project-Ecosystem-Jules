"""Organism implementation: autonomous biological agents with needs, sensory awareness, and behavior."""
import math
import random
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from ecosystem.entities.genome import Genome
from ecosystem.world.grid import WorldGrid
from ecosystem.world.weather import WeatherSystem

class OrganismAction(Enum):
    WANDER = "wander"
    FORAGE = "forage"
    HUNT = "hunt"
    DRINK = "drink"
    FLEE = "flee"
    MATE = "mate"
    REST = "rest"
    SHELTER = "shelter"

class Organism:
    """Individual creature with metabolism, needs, sensory awareness and behavior."""

    def __init__(
        self,
        organism_id: int,
        species_id: int,
        genome: Genome,
        x: float,
        y: float,
        birth_tick: int = 0,
        parent_id_a: Optional[int] = None,
        parent_id_b: Optional[int] = None,
    ):
        self.id = organism_id
        self.species_id = species_id
        self.genome = genome
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.heading = random.uniform(0, 2 * math.pi)

        # Lineage and history
        self.birth_tick = birth_tick
        self.parent_id_a = parent_id_a
        self.parent_id_b = parent_id_b
        self.offspring_count = 0
        self.generation = 0

        # Physical capacity (scaled by size)
        self.max_health = 80.0 * self.genome.size
        self.health = self.max_health
        self.max_energy = 100.0 * self.genome.size
        self.energy = self.max_energy * 0.75
        self.max_water = 80.0 * self.genome.size
        self.water = self.max_water * 0.75

        # Life cycle states
        self.age_ticks = 0
        self.lifespan_ticks = int((4000 + random.randint(0, 1500)) * (0.8 + 0.4 * self.genome.size))
        self.is_alive = True
        self.cause_of_death: Optional[str] = None

        # Reproduction state
        self.is_pregnant = False
        self.pregnancy_timer = 0
        self.mate_cooldown = 200
        self.partner_genome: Optional[Genome] = None

        # Autonomous AI state
        self.current_action = OrganismAction.WANDER
        self.target_x: Optional[float] = None
        self.target_y: Optional[float] = None
        self.target_entity_id: Optional[int] = None

        # Stats for inspector
        self.kills = 0
        self.food_eaten = 0.0
        self.water_drunk = 0.0

    @property
    def is_mature(self) -> bool:
        """Creatures must reach maturity (first 10% of lifespan) before reproducing."""
        return self.age_ticks >= int(self.lifespan_ticks * 0.10)

    @property
    def is_carnivore(self) -> bool:
        return self.genome.diet >= 0.65

    @property
    def is_herbivore(self) -> bool:
        return self.genome.diet <= 0.35

    @property
    def is_omnivore(self) -> bool:
        return 0.35 < self.genome.diet < 0.65

    def step(
        self,
        world: WorldGrid,
        weather: WeatherSystem,
        nearby_organisms: List["Organism"],
        rng: random.Random,
    ) -> Optional[List["Organism"]]:
        """Execute one simulation tick of life, decision-making, and metabolism."""
        if not self.is_alive:
            return None

        self.age_ticks += 1
        newborns: Optional[List["Organism"]] = None

        # 1. Ageing and Lifespan
        if self.age_ticks >= self.lifespan_ticks:
            self.die(world, "Old Age")
            return None

        # 2. Reproduction cooldown & Gestation
        if self.mate_cooldown > 0:
            self.mate_cooldown -= 1

        if self.is_pregnant:
            self.pregnancy_timer -= 1
            if self.pregnancy_timer <= 0:
                newborns = self._give_birth(world, rng)
                self.is_pregnant = False

        # 3. Decision making (Autonomous utility AI)
        self._decide_action(world, weather, nearby_organisms, rng)

        # 4. Action execution & Movement
        self._execute_action(world, weather, nearby_organisms, rng)

        # 5. Metabolism and Vital Degradation
        self._metabolic_burn(world, weather)

        # 6. Death checks
        if self.health <= 0.0:
            if not self.cause_of_death:
                self.die(world, "Exhaustion / Health depletion")
            return None
        if self.energy <= 0.0:
            self.die(world, "Starvation")
            return None
        if self.water <= 0.0:
            self.die(world, "Dehydration")
            return None

        return newborns

    def _decide_action(
        self,
        world: WorldGrid,
        weather: WeatherSystem,
        nearby_organisms: List["Organism"],
        rng: random.Random,
    ) -> None:
        """Utility AI evaluating survival drives to select optimal action."""
        # Environmental visibility factor
        effective_sight = self.genome.sense_radius * weather.current_state.visibility_factor
        if weather.is_night:
            effective_sight *= 0.6

        # Need urgencies [0.0 to 1.0]
        thirst_urgency = 1.0 - (self.water / self.max_water)
        hunger_urgency = 1.0 - (self.energy / self.max_energy)
        health_urgency = 1.0 - (self.health / self.max_health)

        # Scan for threats (predators nearby)
        nearest_threat: Optional["Organism"] = None
        min_threat_dist = 999.0
        potential_prey: List["Organism"] = []
        potential_mates: List["Organism"] = []

        for other in nearby_organisms:
            if other.id == self.id or not other.is_alive:
                continue
            dx = other.x - self.x
            dy = other.y - self.y
            dist = math.hypot(dx, dy)
            if dist > effective_sight:
                continue

            # Threat check: other is carnivore/omnivore, bigger than me, or aggressive
            if (other.is_carnivore or other.is_omnivore) and (other.genome.size > self.genome.size * 0.9):
                if dist < min_threat_dist:
                    min_threat_dist = dist
                    nearest_threat = other

            # Prey check: I am carnivore/omnivore, other is smaller and not my own species
            if (self.is_carnivore or self.is_omnivore) and other.species_id != self.species_id:
                if self.genome.size >= other.genome.size * 0.75:
                    potential_prey.append(other)

            # Mate check: same species, mature, not pregnant, not on cooldown, sufficient energy
            if (other.species_id == self.species_id and other.is_mature and
                not other.is_pregnant and other.mate_cooldown == 0 and
                other.energy > other.max_energy * other.genome.reproduction_threshold):
                potential_mates.append(other)

        # 1. Threat response: Flee!
        flee_threshold = 4.0 + (1.0 - self.genome.bravery) * 8.0
        if nearest_threat is not None and min_threat_dist < flee_threshold:
            self.current_action = OrganismAction.FLEE
            # Run in opposite direction
            escape_dx = self.x - nearest_threat.x
            escape_dy = self.y - nearest_threat.y
            norm = math.hypot(escape_dx, escape_dy) + 1e-4
            self.target_x = self.x + (escape_dx / norm) * 10.0
            self.target_y = self.y + (escape_dy / norm) * 10.0
            return

        # 2. Thirst response
        if thirst_urgency > 0.45 or (thirst_urgency > 0.25 and world.is_water(int(self.x), int(self.y))):
            water_loc = world.find_nearest_water(self.x, self.y, search_radius=int(effective_sight))
            if water_loc is not None:
                self.current_action = OrganismAction.DRINK
                self.target_x, self.target_y = water_loc
                return

        # 3. Hunger response
        if hunger_urgency > 0.4:
            # Herbivore / Omnivore: check plants
            if not self.is_carnivore:
                # Check current tile plant level
                if world.vegetation[int(self.y), int(self.x)] > 10.0:
                    self.current_action = OrganismAction.FORAGE
                    self.target_x, self.target_y = self.x, self.y
                    return
                # Seek tile with highest vegetation nearby
                best_veg = 0.0
                best_pos = None
                sr = int(effective_sight)
                for dy in range(-sr, sr + 1, 2):
                    for dx in range(-sr, sr + 1, 2):
                        tx, ty = int(self.x + dx), int(self.y + dy)
                        if 0 <= tx < world.width and 0 <= ty < world.height:
                            if world.vegetation[ty, tx] > best_veg:
                                best_veg = world.vegetation[ty, tx]
                                best_pos = (tx, ty)
                if best_pos and best_veg > 5.0:
                    self.current_action = OrganismAction.FORAGE
                    self.target_x, self.target_y = best_pos
                    return

            # Carnivore / Omnivore: check prey or carrion
            if not self.is_herbivore:
                # Check if carrion nearby
                if world.carrion[int(self.y), int(self.x)] > 5.0:
                    self.current_action = OrganismAction.FORAGE
                    self.target_x, self.target_y = self.x, self.y
                    return
                # Hunt prey
                if potential_prey:
                    closest_prey = min(potential_prey, key=lambda p: math.hypot(p.x - self.x, p.y - self.y))
                    self.current_action = OrganismAction.HUNT
                    self.target_x, self.target_y = closest_prey.x, closest_prey.y
                    self.target_entity_id = closest_prey.id
                    return

        # 4. Mate seeking
        if (self.is_mature and not self.is_pregnant and self.mate_cooldown == 0 and
            self.energy > self.max_energy * self.genome.reproduction_threshold and potential_mates):
            closest_mate = min(potential_mates, key=lambda m: math.hypot(m.x - self.x, m.y - self.y))
            self.current_action = OrganismAction.MATE
            self.target_x, self.target_y = closest_mate.x, closest_mate.y
            self.target_entity_id = closest_mate.id
            return

        # 5. Low health / energy resting
        if health_urgency > 0.5 or (self.energy < self.max_energy * 0.3 and weather.is_night):
            self.current_action = OrganismAction.REST
            return

        # 6. Default: wander or socialize
        self.current_action = OrganismAction.WANDER

    def _execute_action(
        self,
        world: WorldGrid,
        weather: WeatherSystem,
        nearby_organisms: List["Organism"],
        rng: random.Random,
    ) -> None:
        """Carry out target movement and interaction."""
        move_speed = self.genome.speed

        if self.current_action == OrganismAction.REST:
            # Recover small health while resting
            self.health = min(self.max_health, self.health + 0.1)
            return

        elif self.current_action == OrganismAction.DRINK:
            if world.is_water(int(self.x), int(self.y)) or math.hypot(self.x - (self.target_x or self.x), self.y - (self.target_y or self.y)) < 1.5:
                # Drink water!
                quenched = min(self.max_water - self.water, 25.0)
                self.water += quenched
                self.water_drunk += quenched
                self.current_action = OrganismAction.WANDER
                return
            else:
                self._move_towards(self.target_x, self.target_y, move_speed, world, weather, rng)

        elif self.current_action == OrganismAction.FORAGE:
            # Consume plant or carrion at current location
            ix, iy = int(self.x), int(self.y)
            eaten = 0.0
            if not self.is_carnivore:
                eaten += world.consume_vegetation(ix, iy, amount=12.0)
            if not self.is_herbivore:
                eaten += world.consume_carrion(ix, iy, amount=18.0)

            if eaten > 0:
                self.energy = min(self.max_energy, self.energy + eaten * 2.2)
                self.food_eaten += eaten
                self.current_action = OrganismAction.WANDER
            else:
                if self.target_x is not None:
                    self._move_towards(self.target_x, self.target_y, move_speed, world, weather, rng)
                else:
                    self._wander(move_speed, world, weather, rng)

        elif self.current_action == OrganismAction.HUNT:
            move_speed *= 1.25  # Sprint when hunting
            # Find targeted prey
            prey = next((o for o in nearby_organisms if o.id == self.target_entity_id and o.is_alive), None)
            if prey:
                dist = math.hypot(prey.x - self.x, prey.y - self.y)
                if dist < 1.4:
                    # Attack!
                    damage = (20.0 * self.genome.size * (1.0 + self.genome.aggression)) * (1.0 - prey.genome.armor)
                    prey.health -= damage
                    if prey.health <= 0:
                        prey.die(world, f"Killed by {self.genome.lineage_tag}")
                        meat = 35.0 * prey.genome.size
                        self.energy = min(self.max_energy, self.energy + meat * 2.0)
                        self.food_eaten += meat
                        self.kills += 1
                        self.current_action = OrganismAction.WANDER
                else:
                    self._move_towards(prey.x, prey.y, move_speed, world, weather, rng)
            else:
                self.current_action = OrganismAction.WANDER

        elif self.current_action == OrganismAction.FLEE:
            move_speed *= 1.35  # Adrenaline burst
            self._move_towards(self.target_x, self.target_y, move_speed, world, weather, rng)

        elif self.current_action == OrganismAction.MATE:
            mate = next((o for o in nearby_organisms if o.id == self.target_entity_id and o.is_alive), None)
            if mate:
                dist = math.hypot(mate.x - self.x, mate.y - self.y)
                if dist < 1.6:
                    # Conception
                    self.is_pregnant = True
                    self.pregnancy_timer = self.genome.gestation_time
                    self.partner_genome = mate.genome
                    self.mate_cooldown = 400
                    mate.mate_cooldown = 300
                    # Mating energy expenditure
                    self.energy *= 0.65
                    mate.energy *= 0.70
                    self.current_action = OrganismAction.WANDER
                else:
                    self._move_towards(mate.x, mate.y, move_speed, world, weather, rng)
            else:
                self.current_action = OrganismAction.WANDER

        else:  # WANDER
            self._wander(move_speed * 0.7, world, weather, rng)

    def _move_towards(
        self,
        tx: Optional[float],
        ty: Optional[float],
        speed: float,
        world: WorldGrid,
        weather: WeatherSystem,
        rng: random.Random,
    ) -> None:
        if tx is None or ty is None:
            self._wander(speed, world, weather, rng)
            return

        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.2:
            return

        self.heading = math.atan2(dy, dx)
        step = min(dist, speed * 0.4)
        new_x = self.x + math.cos(self.heading) * step
        new_y = self.y + math.sin(self.heading) * step

        # Boundary and terrain navigation
        if 0 <= new_x < world.width and 0 <= new_y < world.height:
            if world.is_walkable(new_x, new_y):
                self.x = new_x
                self.y = new_y
            else:
                # Steer around water/mountains
                self.heading += rng.uniform(-1.2, 1.2)
        else:
            self.heading += math.pi

    def _wander(self, speed: float, world: WorldGrid, weather: WeatherSystem, rng: random.Random) -> None:
        """Natural smooth Brownian random walk."""
        self.heading += rng.uniform(-0.4, 0.4)
        step = speed * 0.35
        new_x = self.x + math.cos(self.heading) * step
        new_y = self.y + math.sin(self.heading) * step

        if 0 <= new_x < world.width and 0 <= new_y < world.height and world.is_walkable(new_x, new_y):
            self.x = new_x
            self.y = new_y
        else:
            # Turn around on obstacle or boundary
            self.heading += rng.uniform(2.0, 3.5)

    def _metabolic_burn(self, world: WorldGrid, weather: WeatherSystem) -> None:
        """Burn energy and water based on size, speed, terrain, and temperature."""
        terrain_cost = world.get_movement_cost(self.x, self.y)
        stamina_factor = weather.current_state.stamina_drain_factor

        # Basal metabolic rate: Kleiber's law approximation (mass^0.75)
        bmr = 0.08 * (self.genome.size ** 0.75) * self.genome.metabolism

        # Movement energy consumption
        action_factor = 1.0
        if self.current_action in (OrganismAction.HUNT, OrganismAction.FLEE):
            action_factor = 1.8
        elif self.current_action == OrganismAction.REST:
            action_factor = 0.35

        energy_loss = bmr * action_factor * terrain_cost * stamina_factor
        self.energy -= energy_loss

        # Water evaporation / dehydration
        temp = world.get_temperature_at(self.x, self.y, weather)
        temp_diff = abs(temp - self.genome.optimal_temperature)
        water_loss = 0.06 * (self.genome.size ** 0.5) * (1.0 + max(0.0, temp - 25.0) * 0.05)
        self.water -= water_loss

        # Thermal stress damage if outside tolerance window
        if temp_diff > self.genome.temperature_tolerance:
            stress = (temp_diff - self.genome.temperature_tolerance) * 0.05
            self.health -= stress

    def _give_birth(self, world: WorldGrid, rng: random.Random) -> List["Organism"]:
        """Produce mutated/recombined progeny."""
        children = []
        count = self.genome.litter_size
        for _ in range(count):
            if self.partner_genome is not None:
                child_genome = Genome.crossover(self.genome, self.partner_genome, rng)
            else:
                child_genome = self.genome.mutate(rng)

            # Spawn slightly offset
            ox = max(1.0, min(world.width - 2.0, self.x + rng.uniform(-1.5, 1.5)))
            oy = max(1.0, min(world.height - 2.0, self.y + rng.uniform(-1.5, 1.5)))

            child = Organism(
                organism_id=0,  # Will be assigned by simulation
                species_id=self.species_id,
                genome=child_genome,
                x=ox,
                y=oy,
                birth_tick=self.birth_tick + self.age_ticks,
                parent_id_a=self.id,
                parent_id_b=None,
            )
            child.generation = self.generation + 1
            children.append(child)
            self.offspring_count += 1

        return children

    def die(self, world: WorldGrid, cause: str) -> None:
        """Handle death and return biomass to the earth."""
        if not self.is_alive:
            return
        self.is_alive = False
        self.cause_of_death = cause
        # Deposit meat / nutrients proportional to size
        world.add_carrion(int(self.x), int(self.y), amount=25.0 * self.genome.size)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "species_id": self.species_id,
            "genome": self.genome.to_dict(),
            "x": self.x,
            "y": self.y,
            "heading": self.heading,
            "birth_tick": self.birth_tick,
            "parent_id_a": self.parent_id_a,
            "parent_id_b": self.parent_id_b,
            "offspring_count": self.offspring_count,
            "generation": self.generation,
            "health": self.health,
            "energy": self.energy,
            "water": self.water,
            "age_ticks": self.age_ticks,
            "lifespan_ticks": self.lifespan_ticks,
            "is_alive": self.is_alive,
            "cause_of_death": self.cause_of_death,
            "is_pregnant": self.is_pregnant,
            "pregnancy_timer": self.pregnancy_timer,
            "mate_cooldown": self.mate_cooldown,
            "action": self.current_action.value,
            "kills": self.kills,
            "food_eaten": self.food_eaten,
            "water_drunk": self.water_drunk,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Organism":
        genome = Genome.from_dict(data["genome"])
        org = cls(
            organism_id=data["id"],
            species_id=data["species_id"],
            genome=genome,
            x=data["x"],
            y=data["y"],
            birth_tick=data.get("birth_tick", 0),
            parent_id_a=data.get("parent_id_a"),
            parent_id_b=data.get("parent_id_b"),
        )
        org.heading = data.get("heading", 0.0)
        org.offspring_count = data.get("offspring_count", 0)
        org.generation = data.get("generation", 0)
        org.health = data.get("health", org.max_health)
        org.energy = data.get("energy", org.max_energy)
        org.water = data.get("water", org.max_water)
        org.age_ticks = data.get("age_ticks", 0)
        org.lifespan_ticks = data.get("lifespan_ticks", 4000)
        org.is_alive = data.get("is_alive", True)
        org.cause_of_death = data.get("cause_of_death")
        org.is_pregnant = data.get("is_pregnant", False)
        org.pregnancy_timer = data.get("pregnancy_timer", 0)
        org.mate_cooldown = data.get("mate_cooldown", 0)
        org.current_action = OrganismAction(data.get("action", "wander"))
        org.kills = data.get("kills", 0)
        org.food_eaten = data.get("food_eaten", 0.0)
        org.water_drunk = data.get("water_drunk", 0.0)
        return org
