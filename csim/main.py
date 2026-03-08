"""main.py — entry point. Run with: python main.py"""

import sys
import pygame
from csim.sim import Simulation
from csim.render import Renderer
from csim.config import WINDOW_WIDTH, WINDOW_HEIGHT, TARGET_FPS, TRAIL_INTERVALS, TRAIL_INTERVAL_DEFAULT


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Solar System — edit sim.py to implement orbital mechanics")
    clock = pygame.time.Clock()

    sim      = Simulation()
    renderer = Renderer(screen)

    paused = False

    trail_idx = TRAIL_INTERVAL_DEFAULT

    while True:
        dt_real = clock.tick(TARGET_FPS) / 1000.0   # real seconds elapsed this frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_LEFTBRACKET:
                    trail_idx = max(0, trail_idx - 1)
                if event.key == pygame.K_RIGHTBRACKET:
                    trail_idx = min(len(TRAIL_INTERVALS) - 1, trail_idx + 1)
                if event.key == pygame.K_c:
                    renderer.cycle_coord_mode()
                elif event.key == pygame.K_r:
                    renderer.record_toggle()

        renderer.trail_interval = TRAIL_INTERVALS[trail_idx]

        keys = pygame.key.get_pressed()
        renderer.handle_input(keys, dt_real)

        if not paused:
            sim.step(dt_real * renderer.sim_speed)

        screen.fill((5, 5, 15))
        renderer.render(sim, paused)
        pygame.display.flip()


if __name__ == "__main__":
    main()
