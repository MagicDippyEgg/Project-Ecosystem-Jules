"""Camera controller providing smooth panning, zooming, and organism tracking."""
import pygame
from typing import Tuple, Optional

class Camera:
    """Manages 2D viewport offset, zoom scaling, and coordinate transformations."""

    def __init__(self, screen_width: int, screen_height: int, tile_size: int = 16):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size

        # World coordinates centered in view
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.zoom: float = 1.0
        self.min_zoom: float = 0.35
        self.max_zoom: float = 3.5

        # Pan state
        self.is_dragging: bool = False
        self.drag_start_screen: Tuple[int, int] = (0, 0)
        self.drag_start_offset: Tuple[float, float] = (0.0, 0.0)

        # Smooth tracking target
        self.tracking_target_id: Optional[int] = None

    def center_on(self, world_x: float, world_y: float) -> None:
        """Centers the camera view directly on a given world coordinate."""
        self.offset_x = (world_x * self.tile_size * self.zoom) - (self.screen_width / 2.0)
        self.offset_y = (world_y * self.tile_size * self.zoom) - (self.screen_height / 2.0)

    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        """Convert continuous world coordinates to screen pixel positions."""
        sx = int((wx * self.tile_size * self.zoom) - self.offset_x)
        sy = int((wy * self.tile_size * self.zoom) - self.offset_y)
        return (sx, sy)

    def screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        """Convert screen pixel coordinates to continuous world coordinates."""
        wx = (sx + self.offset_x) / (self.tile_size * self.zoom)
        wy = (sy + self.offset_y) / (self.tile_size * self.zoom)
        return (wx, wy)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse drag and mouse wheel zoom events. Returns True if consumed."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Button 3 = Right Click, Button 2 = Middle Click, Button 1 + Ctrl
            if event.button in (2, 3) or (event.button == 1 and pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.is_dragging = True
                self.drag_button = event.button
                self.drag_start_screen = event.pos
                self.drag_start_offset = (self.offset_x, self.offset_y)
                # Manual dragging breaks organism lock-on tracking
                self.tracking_target_id = None
                return True
            elif event.button == 4:  # Wheel up (Zoom in)
                self.adjust_zoom(1.15, event.pos)
                return True
            elif event.button == 5:  # Wheel down (Zoom out)
                self.adjust_zoom(1.0 / 1.15, event.pos)
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if hasattr(self, "drag_button") and event.button == self.drag_button and self.is_dragging:
                self.is_dragging = False
                return True
            elif event.button in (1, 2, 3) and self.is_dragging:
                self.is_dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                dx = event.pos[0] - self.drag_start_screen[0]
                dy = event.pos[1] - self.drag_start_screen[1]
                self.offset_x = self.drag_start_offset[0] - dx
                self.offset_y = self.drag_start_offset[1] - dy
                return True

        elif event.type == pygame.KEYDOWN:
            pan_speed = 30.0 / self.zoom
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.offset_x -= pan_speed
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.offset_x += pan_speed
                return True
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.offset_y -= pan_speed
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.offset_y += pan_speed
                return True
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                self.adjust_zoom(1.2, (self.screen_width // 2, self.screen_height // 2))
                return True
            elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                self.adjust_zoom(1.0 / 1.2, (self.screen_width // 2, self.screen_height // 2))
                return True

        return False

    def adjust_zoom(self, factor: float, focal_point_screen: Tuple[int, int]) -> None:
        """Zoom focused towards screen point."""
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * factor))
        if new_zoom == old_zoom:
            return

        fx, fy = focal_point_screen
        # World point before zoom
        wx = (fx + self.offset_x) / (self.tile_size * old_zoom)
        wy = (fy + self.offset_y) / (self.tile_size * old_zoom)

        self.zoom = new_zoom
        # Adjust offset to keep world point fixed under cursor
        self.offset_x = (wx * self.tile_size * self.zoom) - fx
        self.offset_y = (wy * self.tile_size * self.zoom) - fy

    def update_tracking(self, target_x: float, target_y: float) -> None:
        """Smoothly lerp camera towards tracked target."""
        target_off_x = (target_x * self.tile_size * self.zoom) - (self.screen_width / 2.0)
        target_off_y = (target_y * self.tile_size * self.zoom) - (self.screen_height / 2.0)
        # Smooth damping lerp
        self.offset_x += (target_off_x - self.offset_x) * 0.12
        self.offset_y += (target_off_y - self.offset_y) * 0.12
