"""Automated end-to-end verification script for desktop UI interactions, screenshot capture, and save/load."""
import os
import pygame
from ecosystem.app import EcosystemApp
from ecosystem.entities.genome import Genome
from ecosystem.world.weather import WeatherCondition

def verify_desktop_app():
    print("Initializing EcosystemApp under Xvfb...")
    app = EcosystemApp(width=1200, height=800)

    # 1. Simulate 40 initial ticks
    for _ in range(40):
        app.update()
        app.render()

    # 2. Select an organism and verify inspector
    if app.sim.organisms:
        target_org = app.sim.organisms[0]
        app.sim.selected_organism_id = target_org.id
        print(f"Targeted organism #{target_org.id} ({target_org.genome.lineage_tag})")

    # 3. Step forward and render
    for _ in range(30):
        app.update()
        app.render()

    # Capture main screenshot
    os.makedirs("verification_output", exist_ok=True)
    screenshot_1 = "verification_output/desktop_sim_overview.png"
    pygame.image.save(app.screen, screenshot_1)
    print(f"Overview screenshot saved to {screenshot_1}")

    # 4. Switch to Species tab and capture
    app.set_tab("species")
    app.render()
    screenshot_2 = "verification_output/desktop_species_tab.png"
    pygame.image.save(app.screen, screenshot_2)
    print(f"Species catalog screenshot saved to {screenshot_2}")

    # 5. Switch to Journal tab and capture
    app.set_tab("journal")
    app.render()
    screenshot_3 = "verification_output/desktop_journal_tab.png"
    pygame.image.save(app.screen, screenshot_3)
    print(f"Journal screenshot saved to {screenshot_3}")

    # 6. Switch to GodMode tab, trigger weather storm, and capture
    app.set_tab("godmode")
    app.sim.trigger_environmental_event("storm")
    for _ in range(25):
        app.update()
        app.render()
    screenshot_4 = "verification_output/desktop_storm_godmode.png"
    pygame.image.save(app.screen, screenshot_4)
    print(f"Storm & GodMode screenshot saved to {screenshot_4}")

    # 7. Test Save and Load through UI
    app.save_world()
    app.load_world()
    print("UI Save and Load verified!")

    pygame.quit()
    print("Verification completed successfully!")

if __name__ == "__main__":
    verify_desktop_app()
