import pygame
import random
import math
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
ROAD_COLOR = (40, 40, 40)
SKY_COLOR = (135, 206, 235)

# Game settings
ROAD_WIDTH = 500
MOTORCYCLE_SIZE = (80, 50)
COIN_SIZE = 30
SPEED_INCREASE = 0.05
GRAVITY = 0.8
JUMP_STRENGTH = -15

class ObstacleType(Enum):
    BARRIER = 1
    RAMP = 2
    SPIKE = 3
    GAP = 4

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.life = 1.0

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.2  # Gravity effect
        self.life -= 0.02
        return self.life > 0

    def draw(self, screen):
        alpha = int(255 * self.life)
        color = (*self.color, alpha)
        pos = (int(self.x), int(self.y))
        pygame.draw.circle(screen, color, pos, self.size)

class MotorcycleGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Extreme Motorcycle Racing")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.particles = []
        
        # Load background elements
        self.mountains = self.create_mountain_silhouette()
        
        # Game state
        self.reset_game()
        
        # Load and scale images
        self.motorcycle_img = self.create_motorcycle_image()
        self.coin_img = self.create_coin_image()
        
    def create_mountain_silhouette(self):
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 2), pygame.SRCALPHA)
        points = [(0, SCREEN_HEIGHT // 2)]
        
        for x in range(0, SCREEN_WIDTH + 50, 50):
            height = random.randint(50, 150)
            points.append((x, SCREEN_HEIGHT // 2 - height))
            
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        pygame.draw.polygon(surface, (100, 100, 100), points)
        return surface

    def create_motorcycle_image(self):
        surface = pygame.Surface(MOTORCYCLE_SIZE, pygame.SRCALPHA)
        
        # Wheel radius and position
        wheel_radius = 15
        rear_wheel_pos = (wheel_radius + 5, MOTORCYCLE_SIZE[1] - wheel_radius)
        front_wheel_pos = (MOTORCYCLE_SIZE[0] - wheel_radius - 5, MOTORCYCLE_SIZE[1] - wheel_radius)
        
        # Draw wheels with spokes
        for wheel_pos in [rear_wheel_pos, front_wheel_pos]:
            # Outer rim
            pygame.draw.circle(surface, BLACK, wheel_pos, wheel_radius)
            pygame.draw.circle(surface, (50, 50, 50), wheel_pos, wheel_radius - 2)
            # Spokes
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                start = (wheel_pos[0] + math.cos(rad) * 5,
                        wheel_pos[1] + math.sin(rad) * 5)
                end = (wheel_pos[0] + math.cos(rad) * (wheel_radius - 2),
                      wheel_pos[1] + math.sin(rad) * (wheel_radius - 2))
                pygame.draw.line(surface, BLACK, start, end, 2)
        
        # Draw suspension
        pygame.draw.line(surface, (100, 100, 100),
                        (front_wheel_pos[0], front_wheel_pos[1] - wheel_radius),
                        (front_wheel_pos[0] - 15, front_wheel_pos[1] - wheel_radius * 2),
                        3)
        
        # Draw body
        body_points = [
            (rear_wheel_pos[0] + 10, rear_wheel_pos[1] - wheel_radius * 2),
            (front_wheel_pos[0] - 5, front_wheel_pos[1] - wheel_radius * 2),
            (front_wheel_pos[0] - wheel_radius, rear_wheel_pos[1] - wheel_radius * 3),
            (rear_wheel_pos[0] + wheel_radius, rear_wheel_pos[1] - wheel_radius * 2.5)
        ]
        pygame.draw.polygon(surface, RED, body_points)
        
        # Draw rider
        rider_head_pos = (front_wheel_pos[0] - wheel_radius * 2, rear_wheel_pos[1] - wheel_radius * 3.5)
        pygame.draw.circle(surface, BLACK, rider_head_pos, 10)  # Head
        pygame.draw.ellipse(surface, (0, 0, 150),  # Body
                          (rider_head_pos[0] - 8, rider_head_pos[1],
                           20, 25))
        
        return surface
        
    def create_coin_image(self):
        surface = pygame.Surface((COIN_SIZE, COIN_SIZE), pygame.SRCALPHA)
        
        # Outer ring
        pygame.draw.circle(surface, YELLOW, (COIN_SIZE // 2, COIN_SIZE // 2), COIN_SIZE // 2)
        pygame.draw.circle(surface, (200, 200, 0), (COIN_SIZE // 2, COIN_SIZE // 2), COIN_SIZE // 2 - 2)
        
        # Inner detail
        pygame.draw.circle(surface, YELLOW, (COIN_SIZE // 2, COIN_SIZE // 2), COIN_SIZE // 4)
        
        # Shine effect
        pygame.draw.ellipse(surface, (255, 255, 200),
                          (COIN_SIZE // 4, COIN_SIZE // 4,
                           COIN_SIZE // 6, COIN_SIZE // 6))
        
        return surface

    def create_obstacle(self, x, type):
        if type == ObstacleType.BARRIER:
            return {
                'type': type,
                'x': x,
                'y': SCREEN_HEIGHT - 100,
                'width': 60,
                'height': 40
            }
        elif type == ObstacleType.RAMP:
            return {
                'type': type,
                'x': x,
                'y': SCREEN_HEIGHT - 100,
                'width': 100,
                'height': 50
            }
        elif type == ObstacleType.SPIKE:
            return {
                'type': type,
                'x': x,
                'y': SCREEN_HEIGHT - 80,
                'width': 30,
                'height': 30
            }
        elif type == ObstacleType.GAP:
            return {
                'type': type,
                'x': x,
                'y': SCREEN_HEIGHT - 60,
                'width': 120,
                'height': 60
            }

    def reset_game(self):
        self.motorcycle_pos = [SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150]
        self.motorcycle_velocity = 0
        self.distance = 0
        self.score = 0
        self.game_speed = 5
        self.coins = []
        self.obstacles = []
        self.is_jumping = False
        self.game_over = False
        self.boosting = False
        self.boost_fuel = 100
        self.particles = []
        
        # Generate initial coins and obstacles
        self.generate_coins()
        self.generate_obstacles()
        
    def generate_coins(self):
        if len(self.coins) < 5:
            x = SCREEN_WIDTH if not self.coins else self.coins[-1][0] + random.randint(200, 400)
            y = random.randint(SCREEN_HEIGHT - 250, SCREEN_HEIGHT - 150)
            self.coins.append([x, y])
            
    def generate_obstacles(self):
        if len(self.obstacles) < 3:
            x = SCREEN_WIDTH if not self.obstacles else self.obstacles[-1]['x'] + random.randint(400, 800)
            obstacle_type = random.choice(list(ObstacleType))
            self.obstacles.append(self.create_obstacle(x, obstacle_type))
            
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Jump control
        if keys[pygame.K_SPACE] and not self.is_jumping:
            self.motorcycle_velocity = JUMP_STRENGTH
            self.is_jumping = True
            
        # Boost control
        self.boosting = keys[pygame.K_RIGHT] and self.boost_fuel > 0
        if self.boosting:
            self.boost_fuel = max(0, self.boost_fuel - 1)
            self.add_boost_particles()
            
    def add_boost_particles(self):
        x = self.motorcycle_pos[0]
        y = self.motorcycle_pos[1] + MOTORCYCLE_SIZE[1] // 2
        for _ in range(2):
            self.particles.append(Particle(x, y, (255, 100, 0)))
            
    def update(self):
        if self.game_over:
            return
            
        # Update particles
        self.particles = [p for p in self.particles if p.update()]
            
        # Update motorcycle position
        self.motorcycle_velocity += GRAVITY
        self.motorcycle_pos[1] += self.motorcycle_velocity
        
        # Ground collision
        if self.motorcycle_pos[1] > SCREEN_HEIGHT - 150:
            self.motorcycle_pos[1] = SCREEN_HEIGHT - 150
            self.motorcycle_velocity = 0
            self.is_jumping = False
            
        # Update distance and speed
        base_speed = self.game_speed + (SPEED_INCREASE * (self.distance / 100))
        current_speed = base_speed * (2 if self.boosting else 1)
        self.distance += current_speed
        
        # Regenerate boost fuel when not boosting
        if not self.boosting and self.boost_fuel < 100:
            self.boost_fuel += 0.5
            
        # Update coins
        for coin in self.coins[:]:
            coin[0] -= current_speed
            if coin[0] < -COIN_SIZE:
                self.coins.remove(coin)
            elif (abs(coin[0] - self.motorcycle_pos[0]) < MOTORCYCLE_SIZE[0] * 0.7 and
                  abs(coin[1] - self.motorcycle_pos[1]) < MOTORCYCLE_SIZE[1] * 0.7):
                self.coins.remove(coin)
                self.score += 10
                for _ in range(10):
                    self.particles.append(Particle(coin[0], coin[1], YELLOW))
                
        # Update obstacles
        for obstacle in self.obstacles[:]:
            obstacle['x'] -= current_speed
            if obstacle['x'] < -obstacle['width']:
                self.obstacles.remove(obstacle)
            else:
                # Collision detection based on obstacle type
                if self.check_obstacle_collision(obstacle):
                    self.game_over = True
                    for _ in range(20):
                        self.particles.append(Particle(
                            self.motorcycle_pos[0] + MOTORCYCLE_SIZE[0] // 2,
                            self.motorcycle_pos[1] + MOTORCYCLE_SIZE[1] // 2,
                            RED
                        ))
                
        # Generate new coins and obstacles
        self.generate_coins()
        self.generate_obstacles()
        
    def check_obstacle_collision(self, obstacle):
        moto_rect = pygame.Rect(
            self.motorcycle_pos[0] + 10,
            self.motorcycle_pos[1] + 10,
            MOTORCYCLE_SIZE[0] - 20,
            MOTORCYCLE_SIZE[1] - 20
        )
        
        if obstacle['type'] == ObstacleType.GAP:
            if (self.motorcycle_pos[0] > obstacle['x'] and 
                self.motorcycle_pos[0] < obstacle['x'] + obstacle['width'] and
                self.motorcycle_pos[1] > SCREEN_HEIGHT - 200):
                return True
        else:
            obstacle_rect = pygame.Rect(
                obstacle['x'],
                obstacle['y'],
                obstacle['width'],
                obstacle['height']
            )
            return moto_rect.colliderect(obstacle_rect)
        
        return False

    def draw_obstacle(self, obstacle):
        if obstacle['type'] == ObstacleType.BARRIER:
            pygame.draw.rect(self.screen, RED,
                           (obstacle['x'], obstacle['y'],
                            obstacle['width'], obstacle['height']))
            # Add stripe pattern
            for y in range(0, obstacle['height'], 10):
                pygame.draw.rect(self.screen, WHITE,
                               (obstacle['x'], obstacle['y'] + y,
                                obstacle['width'], 5))
                
        elif obstacle['type'] == ObstacleType.RAMP:
            points = [
                (obstacle['x'], obstacle['y'] + obstacle['height']),
                (obstacle['x'] + obstacle['width'], obstacle['y'] + obstacle['height']),
                (obstacle['x'] + obstacle['width'] // 2, obstacle['y'])
            ]
            pygame.draw.polygon(self.screen, (139, 69, 19), points)
            
        elif obstacle['type'] == ObstacleType.SPIKE:
            points = [
                (obstacle['x'], obstacle['y'] + obstacle['height']),
                (obstacle['x'] + obstacle['width'], obstacle['y'] + obstacle['height']),
                (obstacle['x'] + obstacle['width'] // 2, obstacle['y'])
            ]
            pygame.draw.polygon(self.screen, (169, 169, 169), points)
            
        elif obstacle['type'] == ObstacleType.GAP:
            # Draw gap edges
            pygame.draw.rect(self.screen, ROAD_COLOR,
                           (obstacle['x'] - 20, obstacle['y'],
                            20, obstacle['height']))
            pygame.draw.rect(self.screen, ROAD_COLOR,
                           (obstacle['x'] + obstacle['width'], obstacle['y'],
                            20, obstacle['height']))

    def draw(self):
        # Draw sky
        self.screen.fill(SKY_COLOR)
        
        # Draw mountains (parallax scrolling)
        mountain_offset = -(self.distance * 0.2) % SCREEN_WIDTH
        self.screen.blit(self.mountains, (mountain_offset, SCREEN_HEIGHT // 2))
        self.screen.blit(self.mountains, (mountain_offset + SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        
        # Draw road
        pygame.draw.rect(self.screen, ROAD_COLOR,
                        (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
        
        # Draw coins
        for coin in self.coins:
            self.screen.blit(self.coin_img, (coin[0], coin[1]))
        
        # Draw obstacles
        for obstacle in self.obstacles:
            self.draw_obstacle(obstacle)
        
        # Draw motorcycle
        self.screen.blit(self.motorcycle_img, self.motorcycle_pos)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw score and boost fuel
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        boost_text = self.font.render(f"Boost: {int(self.boost_fuel)}", True, WHITE)
        self.screen.blit(boost_text, (10, 50))
        
        if self.game_over:
            game_over_text = self.font.render("Game Over! Press R to Restart", True, WHITE)
            self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2))
        
        pygame.display.flip()

# Main game loop
def main():
    game = MotorcycleGame()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.game_over:
                    game.reset_game()

        game.handle_input()
        game.update()
        game.draw()
        game.clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()