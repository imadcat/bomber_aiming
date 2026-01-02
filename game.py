import pygame
import math
import random
import sys

# Physics Constants
M_BULLET = 0.045  # kg
CD = 0.295
A = 0.000071  # m^2
RHO = 1.225  # kg/m^3
V_BOMBER = 100.0 # m/s (Bomber moving right/forward)

# Game Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GREY = (100, 100, 100)
YELLOW = (255, 255, 0)

class Bullet:
    def __init__(self, x, y, angle, speed):
        # x, y are screen positions (relative to bomber)
        self.x = x
        self.y = y

        # Initial velocity relative to bomber
        vx_rel = speed * math.cos(angle)
        vy_rel = speed * math.sin(angle)

        # Initial velocity relative to ground (Air is stationary relative to ground)
        # Bomber is moving +X direction
        self.vx_ground = vx_rel + V_BOMBER
        self.vy_ground = vy_rel

        self.active = True
        self.trail = [] # Store past positions for visualization

    def update(self, dt):
        # Store position for trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 20: # Limit trail length
            self.trail.pop(0)

        # Calculate ground velocity magnitude
        v_ground = math.sqrt(self.vx_ground**2 + self.vy_ground**2)

        # Drag force acts opposite to ground velocity
        # Fd = 0.5 * rho * v^2 * Cd * A
        drag_force = 0.5 * RHO * (v_ground**2) * CD * A

        # Deceleration components relative to ground
        decel = drag_force / M_BULLET

        if v_ground > 0:
            ax = -(self.vx_ground / v_ground) * decel
            ay = -(self.vy_ground / v_ground) * decel

            # Update ground velocity
            self.vx_ground += ax * dt
            self.vy_ground += ay * dt

        # Update screen position (relative to bomber)
        # Change in relative position = (V_ground - V_bomber) * dt
        vx_rel = self.vx_ground - V_BOMBER
        vy_rel = self.vy_ground # vy_ground - 0

        self.x += vx_rel * dt
        self.y += vy_rel * dt

        # Deactivate if out of bounds
        if (self.x < -100 or self.x > WIDTH + 100 or
            self.y < -100 or self.y > HEIGHT + 100):
            self.active = False

    def draw(self, screen):
        # Draw Trail
        if len(self.trail) > 1:
            pygame.draw.lines(screen, (255, 100, 100), False, self.trail, 2)
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), 3)

class Enemy:
    def __init__(self, speed_mult=1.0):
        self.x = WIDTH + 50
        self.y = random.randint(50, HEIGHT - 50)
        self.vx = -random.randint(200, 400) * speed_mult
        self.radius = 15
        self.active = True

    def update(self, dt):
        self.x += self.vx * dt
        if self.x < 0:
            self.active = False
            return "hit_base"
        return None

    def draw(self, screen):
        pygame.draw.polygon(screen, GREEN, [
            (self.x, self.y),
            (self.x + 20, self.y - 10),
            (self.x + 20, self.y + 10)
        ])

class Game:
    def __init__(self, test_mode=False):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Bomber Defense - Moving Platform Physics")
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

        self.stars = []
        for _ in range(50):
            self.stars.append([random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)])

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

                # Verification print during test
                if self.test_mode and self.frames % 10 == 0:
                    if self.bullets:
                        b = self.bullets[0]
                        vx_rel = b.vx_ground - V_BOMBER
                        print(f"Frame {self.frames}: Bullet Vx_rel={vx_rel:.2f}, X={b.x:.2f}")

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
        speed = 890 # m/s
        bullet = Bullet(self.turret_x, self.turret_y, self.turret_angle, speed)
        self.bullets.append(bullet)

    def get_predicted_path(self, angle):
        # Simulate bullet physics for 1.5 seconds into the future
        points = []
        dt = 0.05 # Larger dt for faster prediction
        t_max = 1.5

        x = self.turret_x
        y = self.turret_y
        speed = 890

        vx_rel = speed * math.cos(angle)
        vy_rel = speed * math.sin(angle)
        vx_ground = vx_rel + V_BOMBER
        vy_ground = vy_rel

        t = 0
        while t < t_max:
            points.append((x, y))

            v_ground = math.sqrt(vx_ground**2 + vy_ground**2)
            drag_force = 0.5 * RHO * (v_ground**2) * CD * A
            decel = drag_force / M_BULLET

            if v_ground > 0:
                ax = -(vx_ground / v_ground) * decel
                ay = -(vy_ground / v_ground) * decel
                vx_ground += ax * dt
                vy_ground += ay * dt

            vx_rel = vx_ground - V_BOMBER
            vy_rel = vy_ground

            x += vx_rel * dt
            y += vy_rel * dt

            t += dt

            # Stop if out of bounds (optimization)
            if x < 0 or x > WIDTH or y < 0 or y > HEIGHT:
                points.append((x, y))
                break

        return points

    def update(self, dt):
        mx, my = pygame.mouse.get_pos()
        dx = mx - self.turret_x
        dy = my - self.turret_y
        self.turret_angle = math.atan2(dy, dx)

        for star in self.stars:
            star[0] -= V_BOMBER * 5 * dt * star[2] * 0.1
            if star[0] < 0:
                star[0] = WIDTH
                star[1] = random.randint(0, HEIGHT)

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.enemies.append(Enemy(speed_mult=1.0 + self.score * 0.02))
            self.spawn_timer = max(0.3, 1.2 - self.score * 0.05)

        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if b.active]

        for e in self.enemies:
            result = e.update(dt)
            if result == "hit_base":
                self.game_over = True
        self.enemies = [e for e in self.enemies if e.active]

        for e in self.enemies:
            e_rect = pygame.Rect(e.x, e.y - 10, 20, 20)
            for b in self.bullets:
                if b.active:
                    if e_rect.collidepoint(b.x, b.y):
                        e.active = False
                        b.active = False
                        self.score += 1
                        break

    def draw(self):
        self.screen.fill(BLACK)

        for star in self.stars:
            pygame.draw.circle(self.screen, GREY, (int(star[0]), int(star[1])), star[2])

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
            # Draw Aim Assist Trajectory
            predicted_path = self.get_predicted_path(self.turret_angle)
            if len(predicted_path) > 1:
                pygame.draw.lines(self.screen, YELLOW, False, predicted_path, 1)

            # Draw Turret Base
            pygame.draw.circle(self.screen, BLUE, (self.turret_x, self.turret_y), 25)
            # Turret Barrel
            end_x = self.turret_x + 50 * math.cos(self.turret_angle)
            end_y = self.turret_y + 50 * math.sin(self.turret_angle)
            pygame.draw.line(self.screen, BLUE, (self.turret_x, self.turret_y), (end_x, end_y), 8)

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
    if test_mode:
        game.shoot()
    game.run()
