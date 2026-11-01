"""Renderer for simulation viewport: biomes, plants, weather lighting, and organism traits."""
import math
import pygame
import numpy as np
from typing import Tuple, Optional
from ecosystem.world.grid import WorldGrid
from ecosystem.world.biome import BIOME_REGISTRY, BiomeType
from ecosystem.world.weather import WeatherSystem, WeatherCondition
from ecosystem.entities.organism import Organism, OrganismAction
from ecosystem.ui.camera import Camera
from ecosystem.ui.theme import COLOR_ACCENT_CYAN, COLOR_ACCENT_GOLD, COLOR_ACCENT_CORAL

class Renderer:
    """Renders the world map, lighting conditions, weather effects, and organisms."""

    def __init__(self, surface: pygame.Surface, camera: Camera):
        self.surface = surface
        self.camera = camera
        self.biome_colors = [BIOME_REGISTRY[b].color for b in BiomeType]

        # Rain particle system
        self.rain_drops = [
            [float(np.random.randint(0, 1200)), float(np.random.randint(0, 800)), float(np.random.uniform(7, 14))]
            for _ in range(120)
        ]

    def render_world(self, world: WorldGrid) -> None:
        """Renders visible tiles of the procedural landscape."""
        # Calculate visible world bounding box in tile coordinates
        top_left_w = self.camera.screen_to_world(0, 0)
        bot_right_w = self.camera.screen_to_world(self.camera.screen_width, self.camera.screen_height)

        min_tx = max(0, int(top_left_w[0]))
        max_tx = min(world.width, int(bot_right_w[0]) + 2)
        min_ty = max(0, int(top_left_w[1]))
        max_ty = min(world.height, int(bot_right_w[1]) + 2)

        tile_px = max(1, int(self.camera.tile_size * self.camera.zoom))

        for ty in range(min_ty, max_ty):
            for tx in range(min_tx, max_tx):
                b_idx = world.biome_map[ty, tx]
                base_col = self.biome_colors[b_idx]

                # Blend vegetation lushness for land biomes
                veg_ratio = min(1.0, world.vegetation[ty, tx] / (world.max_vegetation[ty, tx] + 1e-4))
                if b_idx not in (0, 1):  # Non-water
                    # Blend base color slightly towards lush green
                    r = int(base_col[0] * (1.0 - 0.25 * veg_ratio) + 20 * veg_ratio)
                    g = int(base_col[1] * (1.0 - 0.25 * veg_ratio) + 160 * veg_ratio)
                    b = int(base_col[2] * (1.0 - 0.25 * veg_ratio) + 30 * veg_ratio)
                    col = (min(255, r), min(255, g), min(255, b))
                else:
                    col = base_col

                # Screen coordinates
                sx, sy = self.camera.world_to_screen(tx, ty)
                pygame.draw.rect(self.surface, col, (sx, sy, tile_px + 1, tile_px + 1))

                # Render carrion marker if present
                if world.carrion[ty, tx] > 5.0:
                    carrion_r = max(2, int(tile_px * 0.3))
                    pygame.draw.circle(self.surface, (180, 40, 40), (sx + tile_px // 2, sy + tile_px // 2), carrion_r)

    def render_organisms(self, organisms: list[Organism], selected_id: Optional[int]) -> None:
        """Renders organisms with distinct body scales, headings, and status reticles."""
        for org in organisms:
            if not org.is_alive:
                continue

            sx, sy = self.camera.world_to_screen(org.x, org.y)
            # Check viewport bounds
            if not (-30 <= sx <= self.camera.screen_width + 30 and -30 <= sy <= self.camera.screen_height + 30):
                continue

            radius = max(3, int(5 * org.genome.size * self.camera.zoom))
            color = org.genome.color

            # Draw body circle
            pygame.draw.circle(self.surface, color, (sx, sy), radius)
            # Draw outline
            outline_color = (255, 255, 255) if org.id == selected_id else (20, 20, 20)
            pygame.draw.circle(self.surface, outline_color, (sx, sy), radius, width=1 if org.id != selected_id else 2)

            # Draw heading pointer line
            hx = sx + int(math.cos(org.heading) * (radius + 3))
            hy = sy + int(math.sin(org.heading) * (radius + 3))
            pygame.draw.line(self.surface, outline_color, (sx, sy), (hx, hy), 2)

            # Draw small health / energy bar underneath if zoomed in
            if self.camera.zoom >= 1.0:
                bar_w = radius * 2
                bar_h = 3
                bx = sx - radius
                by = sy + radius + 2
                # Background
                pygame.draw.rect(self.surface, (40, 40, 40), (bx, by, bar_w, bar_h))
                # Health fill
                health_w = int(bar_w * (org.health / org.max_health))
                pygame.draw.rect(self.surface, (80, 220, 100), (bx, by, health_w, bar_h))

            # Selected reticle
            if org.id == selected_id:
                reticle_r = radius + 6
                pygame.draw.circle(self.surface, COLOR_ACCENT_CYAN, (sx, sy), reticle_r, width=2)
                # Sense radius circle (semi-transparent)
                sense_px = int(org.genome.sense_radius * self.camera.tile_size * self.camera.zoom)
                sense_surf = pygame.Surface((sense_px * 2, sense_px * 2), pygame.SRCALPHA)
                pygame.draw.circle(sense_surf, (0, 210, 210, 35), (sense_px, sense_px), sense_px, width=1)
                self.surface.blit(sense_surf, (sx - sense_px, sy - sense_px))

    def render_environment_overlays(self, weather: WeatherSystem) -> None:
        """Renders day/night ambient illumination and dynamic weather particle effects."""
        # 1. Day / Night ambient lighting
        light = weather.daylight_intensity  # [0.15, 1.0]
        if light < 0.95:
            night_alpha = int((1.0 - light) * 165)
            ambient_surf = pygame.Surface((self.camera.screen_width, self.camera.screen_height), pygame.SRCALPHA)
            # Blue-tinted dark overlay
            ambient_surf.fill((10, 15, 35, night_alpha))
            self.surface.blit(ambient_surf, (0, 0))

        # 2. Weather conditions
        cond = weather.current_state.condition
        if cond in (WeatherCondition.RAIN, WeatherCondition.STORM):
            # Animate rain particles
            storm_mult = 1.6 if cond == WeatherCondition.STORM else 1.0
            for drop in self.rain_drops:
                drop[0] += 2.0 * storm_mult
                drop[1] += drop[2] * storm_mult
                if drop[1] > self.camera.screen_height:
                    drop[1] = float(np.random.randint(-20, -5))
                    drop[0] = float(np.random.randint(0, self.camera.screen_width))
                x, y, spd = int(drop[0]), int(drop[1]), int(drop[2])
                pygame.draw.line(self.surface, (150, 190, 240, 160), (x, y), (x + 2, y + spd), 1)

        elif cond == WeatherCondition.HEATWAVE:
            heat_surf = pygame.Surface((self.camera.screen_width, self.camera.screen_height), pygame.SRCALPHA)
            heat_surf.fill((255, 140, 30, 25))
            self.surface.blit(heat_surf, (0, 0))

        elif cond == WeatherCondition.COLDSNAP:
            cold_surf = pygame.Surface((self.camera.screen_width, self.camera.screen_height), pygame.SRCALPHA)
            cold_surf.fill((180, 220, 255, 30))
            self.surface.blit(cold_surf, (0, 0))
