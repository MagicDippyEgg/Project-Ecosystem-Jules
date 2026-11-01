"""Reusable UI widgets: buttons, cards, stat graphs, and popup modals."""
import pygame
from typing import Tuple, List, Callable, Optional, Dict
from ecosystem.ui.theme import (
    COLOR_PANEL_BG, COLOR_PANEL_SOLID, COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER, COLOR_BUTTON_ACTIVE, COLOR_BUTTON_BORDER,
    COLOR_ACCENT_CYAN, COLOR_HERBIVORE, COLOR_CARNIVORE, COLOR_OMNIVORE, COLOR_PLANT
)

class Button:
    """Interactive clickable UI button with hover states and callback."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        callback: Optional[Callable[[], None]] = None,
        is_toggle: bool = False,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.is_toggle = is_toggle
        self.is_active = False
        self.is_hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.is_toggle:
                    self.is_active = not self.is_active
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        bg_col = COLOR_BUTTON_ACTIVE if self.is_active else (
            COLOR_BUTTON_HOVER if self.is_hovered else COLOR_BUTTON_NORMAL
        )
        pygame.draw.rect(surface, bg_col, self.rect, border_radius=5)
        border_col = COLOR_ACCENT_CYAN if (self.is_hovered or self.is_active) else COLOR_BUTTON_BORDER
        pygame.draw.rect(surface, border_col, self.rect, width=1, border_radius=5)

        text_surf = self.font.render(self.text, True, COLOR_TEXT_PRIMARY if (self.is_hovered or self.is_active) else COLOR_TEXT_SECONDARY)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class SparklineChart:
    """Real-time multi-series line chart for ecological statistics."""

    def __init__(self, rect: pygame.Rect, font: pygame.font.Font, title: str = "Population Trends"):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.title = title

    def draw(
        self,
        surface: pygame.Surface,
        series_dict: Dict[str, Tuple[List[float], Tuple[int, int, int]]],
    ) -> None:
        # Chart background panel
        panel_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel_surf.fill((20, 25, 34, 220))
        surface.blit(panel_surf, self.rect.topleft)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, width=1, border_radius=6)

        # Title
        title_surf = self.font.render(self.title, True, COLOR_ACCENT_CYAN)
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 6))

        # Chart area bounds
        plot_x = self.rect.x + 12
        plot_y = self.rect.y + 28
        plot_w = self.rect.width - 24
        plot_h = self.rect.height - 38

        # Draw grid line
        pygame.draw.line(surface, (45, 55, 72), (plot_x, plot_y + plot_h), (plot_x + plot_w, plot_y + plot_h), 1)

        # Find global max for scaling
        all_vals = []
        for vals, _ in series_dict.values():
            all_vals.extend(vals)
        max_val = max(all_vals) if all_vals and max(all_vals) > 0 else 1.0

        # Draw series lines
        for name, (vals, color) in series_dict.items():
            if len(vals) < 2:
                continue

            points = []
            n = len(vals)
            step_x = plot_w / max(1, n - 1)
            for i, val in enumerate(vals):
                px = plot_x + i * step_x
                norm_y = min(1.0, max(0.0, val / max_val))
                py = plot_y + plot_h - (norm_y * (plot_h - 4))
                points.append((int(px), int(py)))

            if len(points) >= 2:
                pygame.draw.lines(surface, color, False, points, 2)

        # Legend
        leg_x = self.rect.x + self.rect.width - 10
        for name, (_, color) in reversed(series_dict.items()):
            leg_surf = self.font.render(name, True, color)
            leg_x -= (leg_surf.get_width() + 12)
            surface.blit(leg_surf, (leg_x, self.rect.y + 6))
