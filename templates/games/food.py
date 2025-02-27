
import pygame
import random
import math
from pygame import gfxdraw

# Initialize Pygame
pygame.init()

# Define colors
BACKGROUND_COLOR = (15, 25, 35)  # Darker background
SNAKE_PRIMARY = (46, 204, 113)  # Main green
SNAKE_SECONDARY = (39, 174, 96)  # Darker green
SNAKE_HIGHLIGHT = (82, 226, 140)  # Lighter green for highlights
FOOD_COLOR = (231, 76, 60)  # Bright red
FOOD_GLOW = (192, 57, 43)  # Darker red for glow
GRID_COLOR = (30, 45, 60)  # Subtle grid
TEXT_COLOR = (236, 240, 241)  # Almost white

# Set grid size and screen dimensions
GRID_SIZE = 28  # Slightly larger grid
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN_ROWS = SCREEN_HEIGHT // GRID_SIZE
SCREEN_COLS = SCREEN_WIDTH // GRID_SIZE

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Realistic Snake Game")

# Set up the clock
clock = pygame.time.Clock()
FPS = 15

# Directions
UP = {'x': 0, 'y': -1}
DOWN = {'x': 0, 'y': 1}
LEFT = {'x': -1, 'y': 0}
RIGHT = {'x': 1, 'y': 0}

def create_gradient_circle(radius, color1, color2):
    surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(radius):
        alpha = int(255 * (1 - i/radius))
        current_color = (
            int(color1[0] + (color2[0] - color1[0]) * i/radius),
            int(color1[1] + (color2[1] - color1[1]) * i/radius),
            int(color1[2] + (color2[2] - color1[2]) * i/radius),
            alpha
        )
        pygame.draw.circle(surface, current_color, (radius, radius), radius - i)
    return surface

def create_snake_textures():
    head_size = GRID_SIZE
    body_size = GRID_SIZE - 4
    
    # Create head texture with gradient
    head_surface = pygame.Surface((head_size, head_size), pygame.SRCALPHA)
    
    # Main head shape with gradient
    for i in range(head_size//2):
        alpha = 255 - int(155 * (i/(head_size/2)))
        color = (
            SNAKE_PRIMARY[0] + int((SNAKE_HIGHLIGHT[0] - SNAKE_PRIMARY[0]) * i/(head_size/2)),
            SNAKE_PRIMARY[1] + int((SNAKE_HIGHLIGHT[1] - SNAKE_PRIMARY[1]) * i/(head_size/2)),
            SNAKE_PRIMARY[2] + int((SNAKE_HIGHLIGHT[2] - SNAKE_PRIMARY[2]) * i/(head_size/2)),
            alpha
        )
        pygame.draw.circle(head_surface, color, (head_size//2, head_size//2), head_size//2 - i)
    
    # Create eyes
    eye_size = head_size // 6
    # Left eye
    pygame.draw.circle(head_surface, (255, 255, 255), (head_size//2 + eye_size, head_size//2 - eye_size), eye_size)
    pygame.draw.circle(head_surface, (0, 0, 0), (head_size//2 + eye_size + 1, head_size//2 - eye_size), eye_size//2)
    # Right eye
    pygame.draw.circle(head_surface, (255, 255, 255), (head_size//2 + eye_size, head_size//2 + eye_size), eye_size)
    pygame.draw.circle(head_surface, (0, 0, 0), (head_size//2 + eye_size + 1, head_size//2 + eye_size), eye_size//2)
    
    # Add snake pattern to head
    pattern_size = head_size // 8
    for x in range(3):
        for y in range(3):
            offset_x = x * pattern_size * 2
            offset_y = y * pattern_size * 2
            pygame.draw.circle(head_surface, SNAKE_SECONDARY, 
                             (offset_x + pattern_size, offset_y + pattern_size), 
                             pattern_size // 2)

    # Create body texture with scales
    body_surface = pygame.Surface((body_size, body_size), pygame.SRCALPHA)
    
    # Main body gradient
    for i in range(body_size//2):
        alpha = 255 - int(155 * (i/(body_size/2)))
        color = (
            SNAKE_PRIMARY[0] + int((SNAKE_HIGHLIGHT[0] - SNAKE_PRIMARY[0]) * i/(body_size/2)),
            SNAKE_PRIMARY[1] + int((SNAKE_HIGHLIGHT[1] - SNAKE_PRIMARY[1]) * i/(body_size/2)),
            SNAKE_PRIMARY[2] + int((SNAKE_HIGHLIGHT[2] - SNAKE_PRIMARY[2]) * i/(body_size/2)),
            alpha
        )
        pygame.draw.circle(body_surface, color, (body_size//2, body_size//2), body_size//2 - i)
    
    # Add scale pattern
    scale_size = body_size // 4
    for i in range(4):
        angle = i * (math.pi / 2)
        x = body_size//2 + int(math.cos(angle) * scale_size)
        y = body_size//2 + int(math.sin(angle) * scale_size)
        pygame.draw.circle(body_surface, SNAKE_SECONDARY, (x, y), scale_size//2)
    
    return head_surface, body_surface

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def emit(self, x, y, color, count=15):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            size = random.uniform(2, 4)
            self.particles.append({
                'x': x,
                'y': y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'color': color,
                'size': size,
                'life': 1.0
            })
    
    def update(self):
        for particle in self.particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['dx'] *= 0.98
            particle['dy'] *= 0.98
            particle['life'] -= 0.02
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, surface):
        for particle in self.particles:
            alpha = int(255 * particle['life'])
            color = (*particle['color'], alpha)
            pos = (int(particle['x']), int(particle['y']))
            size = int(particle['size'] * particle['life'])
            pygame.draw.circle(surface, color, pos, size)

class GameState:
    def __init__(self):
        self.reset()
        self.particles = ParticleSystem()
        self.head_texture, self.body_texture = create_snake_textures()
        self.high_score = 0
        self.glow_angle = 0
        
    def reset(self):
        self.snake = [{'x': SCREEN_COLS // 2, 'y': SCREEN_ROWS // 2}]
        self.snake_direction = RIGHT
        self.food = self.spawn_food()
        self.score = 0
        self.game_over_state = False
    
    def spawn_food(self):
        while True:
            food = {'x': random.randint(0, SCREEN_COLS - 1), 
                   'y': random.randint(0, SCREEN_ROWS - 1)}
            if food not in self.snake:
                return food
    
    def update(self):
        if self.game_over_state:
            return
        
        self.glow_angle += 0.1
        
        head = {'x': self.snake[0]['x'] + self.snake_direction['x'],
                'y': self.snake[0]['y'] + self.snake_direction['y']}
        
        if (head['x'] < 0 or head['x'] >= SCREEN_COLS or
            head['y'] < 0 or head['y'] >= SCREEN_ROWS or
            head in self.snake):
            self.game_over_state = True
            if self.score > self.high_score:
                self.high_score = self.score
            return
        
        self.snake.insert(0, head)
        
        if head['x'] == self.food['x'] and head['y'] == self.food['y']:
            self.score += 1
            self.food = self.spawn_food()
            food_pixel_pos = (self.food['x'] * GRID_SIZE + GRID_SIZE // 2,
                            self.food['y'] * GRID_SIZE + GRID_SIZE // 2)
            self.particles.emit(*food_pixel_pos, FOOD_COLOR)
        else:
            self.snake.pop()
        
        self.particles.update()
    
    def draw(self, surface):
        # Draw background with subtle gradient
        surface.fill(BACKGROUND_COLOR)
        
        # Draw subtle grid
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(surface, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))
        
        # Draw snake with smooth connections
        for i, segment in enumerate(self.snake):
            x = segment['x'] * GRID_SIZE
            y = segment['y'] * GRID_SIZE
            
            if i == 0:
                angle = 0
                if self.snake_direction == UP: angle = 90
                elif self.snake_direction == DOWN: angle = -90
                elif self.snake_direction == LEFT: angle = 180
                
                rotated_head = pygame.transform.rotate(self.head_texture, angle)
                surface.blit(rotated_head, (x - 2, y - 2))
            else:
                # Draw body segments with connecting curves
                surface.blit(self.body_texture, (x, y))
        
        # Draw food with animated glow
        food_x = self.food['x'] * GRID_SIZE + GRID_SIZE // 2
        food_y = self.food['y'] * GRID_SIZE + GRID_SIZE // 2
        
        # Animated glow effect
        glow_size = GRID_SIZE // 2 + 4 + math.sin(self.glow_angle) * 2
        glow_surface = create_gradient_circle(int(glow_size), FOOD_COLOR, (0, 0, 0, 0))
        surface.blit(glow_surface, 
                    (food_x - glow_size, food_y - glow_size))
        
        # Main food
        pygame.draw.circle(surface, FOOD_COLOR, (food_x, food_y), GRID_SIZE // 3)
        pygame.draw.circle(surface, (255, 255, 255), 
                         (food_x - 2, food_y - 2), GRID_SIZE // 8)  # Highlight
        
        # Draw particles
        self.particles.draw(surface)
        
        # Draw scores with shadow effect
        font = pygame.font.Font(None, 48)
        
        def draw_text_with_shadow(text, pos):
            shadow = font.render(text, True, (0, 0, 0))
            main = font.render(text, True, TEXT_COLOR)
            surface.blit(shadow, (pos[0] + 2, pos[1] + 2))
            surface.blit(main, pos)
        
        draw_text_with_shadow(f"Score: {self.score}", (10, 10))
        draw_text_with_shadow(f"High Score: {self.high_score}", (10, 50))
        
        if self.game_over_state:
            game_over_font = pygame.font.Font(None, 72)
            game_over_text = game_over_font.render("Game Over!", True, TEXT_COLOR)
            restart_text = font.render("Press R to Restart or Q to Quit", True, TEXT_COLOR)
            
            # Draw text with glow effect
            glow_surface = pygame.Surface(game_over_text.get_size(), pygame.SRCALPHA)
            glow_surface.fill((255, 255, 255, 50))
            surface.blit(glow_surface, 
                        (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2 + 2,
                         SCREEN_HEIGHT // 2 - game_over_text.get_height() + 2))
            
            surface.blit(game_over_text, 
                        (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                         SCREEN_HEIGHT // 2 - game_over_text.get_height()))
            surface.blit(restart_text,
                        (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                         SCREEN_HEIGHT // 2 + restart_text.get_height()))

def main():
    game = GameState()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            if event.type == pygame.KEYDOWN:
                if game.game_over_state:
                    if event.key == pygame.K_r:
                        game.reset()
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        return
                else:
                    if event.key == pygame.K_LEFT and game.snake_direction != RIGHT:
                        game.snake_direction = LEFT
                    elif event.key == pygame.K_RIGHT and game.snake_direction != LEFT:
                        game.snake_direction = RIGHT
                    elif event.key == pygame.K_UP and game.snake_direction != DOWN:
                        game.snake_direction = UP
                    elif event.key == pygame.K_DOWN and game.snake_direction != UP:
                        game.snake_direction = DOWN
        
        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()