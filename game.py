import pygame
import math
import random
import sys

# Physics Constants (from original project)
# Although solve_ivp is too slow for real-time game loop, we can use Euler integration with these constants
# to maintain the "simulation" aspect.
M_BULLET = 0.045  # kg
CD = 0.295
A = 0.000071  # m^2
RHO = 1.225  # kg/m^3

# Game Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

class Bullet:
    def __init__(self, x, y, angle, speed):
        self.x = x
        self.y = y
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.active = True

    def update(self, dt):
        # Calculate velocity magnitude
        v = math.sqrt(self.vx**2 + self.vy**2)

        # Drag force: Fd = 0.5 * rho * v^2 * Cd * A
        drag_force = 0.5 * RHO * (v**2) * CD * A

        # Deceleration: a = Fd / m
        decel = drag_force / M_BULLET

        # Update velocity components
        if v > 0:
            self.vx -= (self.vx / v) * decel * dt
            self.vy -= (self.vy / v) * decel * dt

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Deactivate if out of bounds or too slow
        if (self.x < 0 or self.x > WIDTH or
            self.y < 0 or self.y > HEIGHT or v < 10):
            self.active = False

    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), 3)

class Enemy:
    def __init__(self, speed_mult=1.0):
        self.x = WIDTH
        self.y = random.randint(50, HEIGHT - 50)
        self.vx = -random.randint(100, 300) * speed_mult
        self.radius = 15
        self.active = True

    def update(self, dt):
        self.x += self.vx * dt
        if self.x < 0:
            self.active = False
            return "hit_base"
        return None

    def draw(self, screen):
        # Draw a simple fighter shape
        pygame.draw.polygon(screen, GREEN, [
            (self.x, self.y),
            (self.x + 20, self.y - 10),
            (self.x + 20, self.y + 10)
        ])

class Game:
    def __init__(self, test_mode=False):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Bomber Defense")
        self.clock = pygame.time.Clock()
        self.running = True
        self.test_mode = test_mode
        self.frames = 0

        self.bullets = []
        self.enemies = []
        self.score = 0
        self.game_over = False

        # Turret position
        self.turret_x = 50
        self.turret_y = HEIGHT // 2
        self.turret_angle = 0

        self.spawn_timer = 0
        self.spawn_rate = 1.0 # seconds

    def reset(self):
        self.bullets = []
        self.enemies = []
        self.score = 0
        self.game_over = False
        self.turret_y = HEIGHT // 2

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # seconds
            self.handle_events()

            if not self.game_over:
                self.update(dt)

            self.draw()

            if self.test_mode:
                self.frames += 1
                if self.frames > 60:
                    self.running = False

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                if event.button == 1: # Left click
                    self.shoot()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.reset()

    def shoot(self):
        # Bullet initial speed
        speed = 890 # m/s from original code
        bullet = Bullet(self.turret_x, self.turret_y, self.turret_angle, speed)
        self.bullets.append(bullet)

    def update(self, dt):
        # Update Turret Angle
        mx, my = pygame.mouse.get_pos()
        dx = mx - self.turret_x
        dy = my - self.turret_y
        self.turret_angle = math.atan2(dy, dx)

        # Spawn Enemies
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.enemies.append(Enemy(speed_mult=1.0 + self.score * 0.01))
            self.spawn_timer = max(0.2, 1.0 - self.score * 0.05)

        # Update Bullets
        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if b.active]

        # Update Enemies
        for e in self.enemies:
            result = e.update(dt)
            if result == "hit_base":
                self.game_over = True
        self.enemies = [e for e in self.enemies if e.active]

        # Collision Detection
        for e in self.enemies:
            e_rect = pygame.Rect(e.x, e.y - 10, 20, 20)
            for b in self.bullets:
                if b.active:
                    # Simple point collision
                    if e_rect.collidepoint(b.x, b.y):
                        e.active = False
                        b.active = False
                        self.score += 1
                        break

    def draw(self):
        self.screen.fill(BLACK)

        if self.game_over:
            font = pygame.font.SysFont(None, 64)
            text = font.render("GAME OVER", True, RED)
            self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))

            font_small = pygame.font.SysFont(None, 32)
            score_text = font_small.render(f"Final Score: {self.score}", True, WHITE)
            self.screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 + 20))

            restart_text = font_small.render("Press 'R' to Restart", True, WHITE)
            self.screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 60))

        else:
            # Draw Turret
            pygame.draw.circle(self.screen, BLUE, (self.turret_x, self.turret_y), 20)
            # Turret Barrel
            end_x = self.turret_x + 40 * math.cos(self.turret_angle)
            end_y = self.turret_y + 40 * math.sin(self.turret_angle)
            pygame.draw.line(self.screen, BLUE, (self.turret_x, self.turret_y), (end_x, end_y), 5)

            # Draw Bullets
            for b in self.bullets:
                b.draw(self.screen)

            # Draw Enemies
            for e in self.enemies:
                e.draw(self.screen)

            # Draw Score
            font = pygame.font.SysFont(None, 36)
            score_text = font.render(f"Score: {self.score}", True, WHITE)
            self.screen.blit(score_text, (10, 10))

        pygame.display.flip()

if __name__ == "__main__":
    test_mode = "--test" in sys.argv
    game = Game(test_mode=test_mode)
    game.run()
