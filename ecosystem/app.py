"""Complete native Linux desktop GUI application orchestrating UI, rendering, and simulation."""
import os
import sys
import pygame
from typing import Optional, Tuple
from ecosystem.entities.organism import Organism
from ecosystem.core.simulation import Simulation
from ecosystem.core.save_load import SaveManager
from ecosystem.ui.camera import Camera
from ecosystem.ui.renderer import Renderer
from ecosystem.ui.widgets import Button, SparklineChart
from ecosystem.ui.theme import (
    COLOR_BG_DARK, COLOR_PANEL_BG, COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_ACCENT_CYAN, COLOR_ACCENT_GOLD, COLOR_ACCENT_CORAL, COLOR_ACCENT_GREEN,
    COLOR_HERBIVORE, COLOR_CARNIVORE, COLOR_OMNIVORE, COLOR_PLANT
)

class EcosystemApp:
    """The Native Desktop Application for Project Ecosystem."""

    def __init__(self, width: int = 1200, height: int = 800):
        pygame.init()
        pygame.font.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Project Ecosystem - Artificial Life Simulation")

        self.clock = pygame.time.Clock()
        self.is_running = True

        # Fonts
        self.font_large = pygame.font.SysFont("DejaVu Sans", 18, bold=True)
        self.font_main = pygame.font.SysFont("DejaVu Sans", 13)
        self.font_small = pygame.font.SysFont("DejaVu Sans", 11)

        # Simulation
        self.sim = Simulation(width=100, height=70, seed=42)
        self.sim.populate_initial_ecosystem(num_herbivores=45, num_omnivores=16, num_carnivores=8)

        # Camera & Renderer
        self.camera = Camera(self.width, self.height, tile_size=16)
        self.camera.center_on(self.sim.world.width / 2.0, self.sim.world.height / 2.0)
        self.renderer = Renderer(self.screen, self.camera)

        # UI State
        self.speed_levels = [0.5, 1.0, 2.0, 5.0, 10.0]
        self.speed_idx = 1
        self.active_tab = "stats"  # "stats", "species", "journal", "godmode"
        self.status_msg = "World running smoothly"
        self.status_timer = 0

        # Build UI Controls
        self._init_buttons()
        self.chart = SparklineChart(pygame.Rect(20, self.height - 180, 420, 160), self.font_small, "Ecological Census Trends")

    def _init_buttons(self) -> None:
        self.top_buttons = []

        # Play / Pause
        self.btn_pause = Button(
            pygame.Rect(15, 12, 80, 30),
            "Pause",
            self.font_main,
            callback=self.toggle_pause
        )
        self.top_buttons.append(self.btn_pause)

        # Speed Toggle
        self.btn_speed = Button(
            pygame.Rect(102, 12, 75, 30),
            f"{self.speed_levels[self.speed_idx]}x",
            self.font_main,
            callback=self.cycle_speed
        )
        self.top_buttons.append(self.btn_speed)

        # Save & Load
        self.top_buttons.append(
            Button(pygame.Rect(185, 12, 70, 30), "Save", self.font_main, callback=self.save_world)
        )
        self.top_buttons.append(
            Button(pygame.Rect(262, 12, 70, 30), "Load", self.font_main, callback=self.load_world)
        )
        self.top_buttons.append(
            Button(pygame.Rect(339, 12, 95, 30), "New World", self.font_main, callback=self.generate_new_world)
        )

        # Tab navigation buttons on right panel
        tab_y = 12
        tab_w = 78
        self.tab_buttons = [
            Button(pygame.Rect(self.width - 340, tab_y, tab_w, 28), "Stats", self.font_small, callback=lambda: self.set_tab("stats")),
            Button(pygame.Rect(self.width - 258, tab_y, tab_w, 28), "Species", self.font_small, callback=lambda: self.set_tab("species")),
            Button(pygame.Rect(self.width - 176, tab_y, tab_w, 28), "Journal", self.font_small, callback=lambda: self.set_tab("journal")),
            Button(pygame.Rect(self.width - 94, tab_y, tab_w, 28), "GodMode", self.font_small, callback=lambda: self.set_tab("godmode")),
        ]

    def set_tab(self, tab: str) -> None:
        self.active_tab = tab

    def toggle_pause(self) -> None:
        self.sim.is_paused = not self.sim.is_paused
        self.btn_pause.text = "Resume" if self.sim.is_paused else "Pause"

    def cycle_speed(self) -> None:
        self.speed_idx = (self.speed_idx + 1) % len(self.speed_levels)
        spd = self.speed_levels[self.speed_idx]
        self.sim.simulation_speed = spd
        self.btn_speed.text = f"{spd}x"

    def save_world(self) -> None:
        path = SaveManager.save_simulation(self.sim, "world_save.eco")
        self.set_status("World saved successfully!")

    def load_world(self) -> None:
        saves = SaveManager.list_saves()
        if saves:
            self.sim = SaveManager.load_simulation(saves[0])
            self.camera.center_on(self.sim.world.width / 2.0, self.sim.world.height / 2.0)
            self.set_status("World loaded successfully!")
        else:
            self.set_status("No save file found.")

    def generate_new_world(self) -> None:
        new_seed = self.sim.rng.randint(1, 999999)
        self.sim = Simulation(width=100, height=70, seed=new_seed)
        self.sim.populate_initial_ecosystem(num_herbivores=45, num_omnivores=16, num_carnivores=8)
        self.camera.center_on(self.sim.world.width / 2.0, self.sim.world.height / 2.0)
        self.set_status("Generated fresh pristine world.")

    def set_status(self, msg: str) -> None:
        self.status_msg = msg
        self.status_timer = 180

    def run(self) -> None:
        """Main application game loop."""
        while self.is_running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                return

            if event.type == pygame.VIDEORESIZE:
                self.width = max(800, event.w)
                self.height = max(600, event.h)
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.camera.screen_width = self.width
                self.camera.screen_height = self.height
                self._init_buttons()
                self.chart.rect = pygame.Rect(20, self.height - 180, 420, 160)

            # Check UI button clicks
            ui_clicked = False
            for btn in self.top_buttons + self.tab_buttons:
                if btn.handle_event(event):
                    ui_clicked = True
                    break

            if ui_clicked:
                continue

            # Check right panel click interception
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                if event.pos[0] >= self.width - 350:
                    self._handle_right_panel_event(event)
                    continue

            # Camera zoom/drag
            if self.camera.handle_event(event):
                continue

            # Organism Selection Click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                wx, wy = self.camera.screen_to_world(*event.pos)
                selected = self.sim.select_organism_at(wx, wy)
                if selected:
                    self.set_status(f"Selected organism #{selected.id}")

    def _handle_right_panel_event(self, event: pygame.event.Event) -> None:
        """Handle clicks on God Mode action buttons, etc."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.active_tab == "godmode":
            panel_x = self.width - 340
            y_start = getattr(self, "godmode_buttons_y", 90)
            actions = [
                ("Trigger Rainstorm", lambda: self.sim.trigger_environmental_event("storm")),
                ("Trigger Drought", lambda: self.sim.add_disaster("drought")),
                ("Trigger Super-Bloom", lambda: self.sim.add_disaster("bloom")),
                ("Spawn Plague", lambda: self.sim.add_disaster("plague")),
                ("Spawn Carnivores", lambda: self.sim.populate_initial_ecosystem(0, 0, 5)),
            ]
            for i, (name, fn) in enumerate(actions):
                r = pygame.Rect(panel_x + 10, y_start + i * 44, 300, 34)
                if r.collidepoint(event.pos):
                    fn()
                    self.set_status(f"Disaster action executed: {name}")

    def update(self) -> None:
        if self.status_timer > 0:
            self.status_timer -= 1

        # Smooth camera tracking of selected organism (if user is not manually panning)
        if not self.camera.is_dragging:
            sel_org = self.sim.get_selected_organism()
            if sel_org is not None and self.camera.tracking_target_id == sel_org.id:
                self.camera.update_tracking(sel_org.x, sel_org.y)

        # Simulation stepping based on speed
        if not self.sim.is_paused:
            ticks_to_run = int(self.sim.simulation_speed)
            fraction = self.sim.simulation_speed - ticks_to_run
            # Probabilistic fractional step for 0.5x
            if fraction > 0 and self.sim.rng.random() < fraction:
                ticks_to_run += 1

            for _ in range(max(1 if self.sim.simulation_speed >= 1.0 else 0, ticks_to_run)):
                self.sim.step()

    def render(self) -> None:
        self.screen.fill(COLOR_BG_DARK)

        # 1. Render World & Organisms Viewport
        self.renderer.render_world(self.sim.world)
        self.renderer.render_organisms(self.sim.organisms, self.sim.selected_organism_id)
        self.renderer.render_environment_overlays(self.sim.weather)

        # 2. Render Top HUD Bar
        self._render_top_bar()

        # 3. Render Bottom Left Statistics Chart
        self._render_charts()

        # 4. Render Right Inspector / Sidebar Panel
        self._render_right_panel()

        # 5. Status Toast
        if self.status_timer > 0:
            toast_surf = self.font_small.render(self.status_msg, True, COLOR_ACCENT_GOLD)
            pygame.draw.rect(self.screen, (20, 25, 35, 230), (self.width // 2 - 120, self.height - 35, 240, 24), border_radius=4)
            pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, (self.width // 2 - 120, self.height - 35, 240, 24), width=1, border_radius=4)
            self.screen.blit(toast_surf, (self.width // 2 - 110, self.height - 31))

        pygame.display.flip()

    def _render_top_bar(self) -> None:
        # Background bar
        bar_surf = pygame.Surface((self.width, 54), pygame.SRCALPHA)
        bar_surf.fill(COLOR_PANEL_BG)
        self.screen.blit(bar_surf, (0, 0))
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (0, 54), (self.width, 54), 1)

        # Draw Buttons
        for btn in self.top_buttons:
            btn.draw(self.screen)

        # Clock & Environmental Status info
        w_state = self.sim.weather.current_state
        time_text = f"Day {self.sim.weather.day}  |  Tick {self.sim.tick_count}  |  Weather: {w_state.condition.name.upper()}  |  Light: {int(self.sim.weather.daylight_intensity * 100)}%"
        time_surf = self.font_main.render(time_text, True, COLOR_TEXT_PRIMARY)
        self.screen.blit(time_surf, (450, 18))

    def _render_charts(self) -> None:
        # Supply latest telemetry to sparkline
        history = self.sim.stats.history
        if len(history) >= 2:
            herb_data = [s.herbivore_count for s in history]
            omni_data = [s.omnivore_count for s in history]
            carn_data = [s.carnivore_count for s in history]

            self.chart.draw(self.screen, {
                "Carn": (carn_data, COLOR_CARNIVORE),
                "Omni": (omni_data, COLOR_OMNIVORE),
                "Herb": (herb_data, COLOR_HERBIVORE),
            })

    def _render_right_panel(self) -> None:
        panel_w = 340
        panel_x = self.width - panel_w
        panel_surf = pygame.Surface((panel_w, self.height - 54), pygame.SRCALPHA)
        panel_surf.fill(COLOR_PANEL_BG)
        self.screen.blit(panel_surf, (panel_x, 54))
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (panel_x, 54), (panel_x, self.height), 1)

        # Draw Tab Buttons
        for btn in self.tab_buttons:
            btn.is_active = (btn.text.lower() == self.active_tab)
            btn.draw(self.screen)

        content_y = 65

        # If organism selected, display organism inspector card at top of panel
        sel_org = self.sim.get_selected_organism()
        if sel_org is not None:
            content_y = self._render_organism_inspector(panel_x + 10, content_y, sel_org) + 10

        # Render Active Tab Content
        if self.active_tab == "stats":
            self._render_tab_stats(panel_x + 10, content_y)
        elif self.active_tab == "species":
            self._render_tab_species(panel_x + 10, content_y)
        elif self.active_tab == "journal":
            self._render_tab_journal(panel_x + 10, content_y)
        elif self.active_tab == "godmode":
            self._render_tab_godmode(panel_x + 10, content_y)

    def _render_organism_inspector(self, x: int, y: int, org: Organism) -> int:
        card_h = 220
        pygame.draw.rect(self.screen, (22, 28, 38), (x, y, 320, card_h), border_radius=6)
        pygame.draw.rect(self.screen, COLOR_ACCENT_CYAN, (x, y, 320, card_h), width=1, border_radius=6)

        title = f"Creature #{org.id} [{org.genome.lineage_tag}]"
        self.screen.blit(self.font_large.render(title, True, COLOR_ACCENT_CYAN), (x + 10, y + 8))

        # Color swatch
        pygame.draw.circle(self.screen, org.genome.color, (x + 300, y + 18), 8)

        sp = self.sim.species_manager.species_catalog.get(org.species_id)
        sp_name = sp.name if sp else "Unknown"
        self.screen.blit(self.font_small.render(f"Species: {sp_name}", True, COLOR_TEXT_SECONDARY), (x + 10, y + 32))

        # Status bars: Health, Energy, Water
        def draw_bar(label: str, cur: float, max_v: float, by: int, col: Tuple[int, int, int]):
            self.screen.blit(self.font_small.render(label, True, COLOR_TEXT_MUTED), (x + 10, by))
            pygame.draw.rect(self.screen, (40, 45, 55), (x + 70, by + 2, 235, 10), border_radius=3)
            fill_w = max(0, min(235, int(235 * (cur / max_v))))
            pygame.draw.rect(self.screen, col, (x + 70, by + 2, fill_w, 10), border_radius=3)

        draw_bar("Health", org.health, org.max_health, y + 54, COLOR_ACCENT_CORAL)
        draw_bar("Energy", org.energy, org.max_energy, y + 72, COLOR_ACCENT_GOLD)
        draw_bar("Hydration", org.water, org.max_water, y + 90, COLOR_ACCENT_CYAN)

        # Traits & Stats
        stats = [
            f"Action: {org.current_action.name}  |  Age: {org.age_ticks} / {org.lifespan_ticks}",
            f"Diet: {org.genome.diet:.2f} ({'Herb' if org.is_herbivore else ('Carn' if org.is_carnivore else 'Omni')})  |  Gen: {org.generation}",
            f"Size: {org.genome.size:.2f}  |  Speed: {org.genome.speed:.2f}  |  Sight: {org.genome.sense_radius:.1f}",
            f"Offspring: {org.offspring_count}  |  Kills: {org.kills}  |  Food: {int(org.food_eaten)}",
            f"Parents: P1={org.parent_id_a or 'None'}, P2={org.parent_id_b or 'None'}",
        ]
        for i, s in enumerate(stats):
            self.screen.blit(self.font_small.render(s, True, COLOR_TEXT_SECONDARY), (x + 10, y + 110 + i * 20))

        return y + card_h + 12

    def _render_tab_stats(self, x: int, y: int) -> None:
        self.screen.blit(self.font_large.render("Ecosystem Overview", True, COLOR_ACCENT_CYAN), (x, y))
        y += 28

        herbs = sum(1 for o in self.sim.organisms if o.is_herbivore)
        omnis = sum(1 for o in self.sim.organisms if o.is_omnivore)
        carns = sum(1 for o in self.sim.organisms if o.is_carnivore)
        veg_sum = int(self.sim.world.vegetation.sum())
        active_sp = sum(1 for s in self.sim.species_manager.species_catalog.values() if not s.extinct)

        lines = [
            f"Living Population: {len(self.sim.organisms)}",
            f"  • Herbivores: {herbs}",
            f"  • Omnivores: {omnis}",
            f"  • Carnivores: {carns}",
            f"Total Vegetation Biomass: {veg_sum:,} units",
            f"Active Species: {active_sp}",
            f"Extinct Species: {len(self.sim.species_manager.species_catalog) - active_sp}",
            f"Total Historical Births: {self.sim.stats.total_births}",
            f"Total Historical Deaths: {self.sim.stats.total_deaths}",
        ]
        for line in lines:
            self.screen.blit(self.font_main.render(line, True, COLOR_TEXT_PRIMARY), (x, y))
            y += 22

    def _render_tab_species(self, x: int, y: int) -> None:
        self.screen.blit(self.font_large.render("Species Catalog & Lineages", True, COLOR_ACCENT_CYAN), (x, y))
        y += 28

        for sp in list(self.sim.species_manager.species_catalog.values())[-7:]:
            status = "Extinct" if sp.extinct else f"Pop: {sp.population}"
            status_col = COLOR_ACCENT_CORAL if sp.extinct else COLOR_ACCENT_GREEN
            card_rect = pygame.Rect(x, y, 320, 48)
            pygame.draw.rect(self.screen, (22, 28, 38), card_rect, border_radius=4)
            pygame.draw.rect(self.screen, sp.color, (x + 4, y + 4, 8, 40), border_radius=2)

            self.screen.blit(self.font_main.render(sp.name, True, COLOR_TEXT_PRIMARY), (x + 20, y + 4))
            self.screen.blit(self.font_small.render(sp.description, True, COLOR_TEXT_MUTED), (x + 20, y + 26))
            self.screen.blit(self.font_small.render(status, True, status_col), (x + 245, y + 6))
            y += 54

    def _render_tab_journal(self, x: int, y: int) -> None:
        self.screen.blit(self.font_large.render("Observation Journal", True, COLOR_ACCENT_CYAN), (x, y))
        y += 28

        for ev in reversed(self.sim.event_log[-9:]):
            header = f"[Day {ev['day']} / {ev['category']}]"
            self.screen.blit(self.font_small.render(header, True, COLOR_ACCENT_GOLD), (x, y))
            self.screen.blit(self.font_small.render(ev["text"], True, COLOR_TEXT_PRIMARY), (x, y + 14))
            y += 36

    def _render_tab_godmode(self, x: int, y: int) -> None:
        self.screen.blit(self.font_large.render("World Interventions", True, COLOR_ACCENT_CYAN), (x, y))
        y += 28
        self.screen.blit(self.font_small.render("Trigger ecological shocks and mutations:", True, COLOR_TEXT_SECONDARY), (x, y))
        y += 24
        self.godmode_buttons_y = y

        actions = [
            "Trigger Rainstorm",
            "Trigger Drought",
            "Trigger Super-Bloom",
            "Spawn Plague",
            "Spawn Carnivores",
        ]
        for btn_name in actions:
            r = pygame.Rect(x, y, 320, 34)
            pygame.draw.rect(self.screen, (38, 48, 64), r, border_radius=5)
            pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, r, width=1, border_radius=5)
            self.screen.blit(self.font_main.render(btn_name, True, COLOR_TEXT_PRIMARY), (x + 12, y + 8))
            y += 44
