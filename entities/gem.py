import pygame
import random
from config import *

class Gem:
    def __init__(self, x, y, gem_type=None):
        self.x = x
        self.y = y
        self.type = gem_type if gem_type else random.choice(GEM_TYPES)
        self.level = 1
        self.damage = BASE_DAMAGE
        self.crit_chance = CRIT_CHANCE
        self.crit_multiplier = CRIT_MULTIPLIER
        
        # Загружаем изображение гема
        self.image = pygame.image.load(GEM_IMAGES[self.type])
        self.image = pygame.transform.scale(self.image, (CELL_SIZE, CELL_SIZE))
        
        # Создаем поверхность для отображения уровня
        self.level_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        
        self.rect = pygame.Rect(
            GRID_OFFSET_X + x * CELL_SIZE,
            GRID_OFFSET_Y + y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        self.is_selected = False
        self.is_moving = False
        self.target_pos = None
        self.animation_progress = 0

    def draw(self, screen):
        # Рисуем гем
        if self.is_selected:
            # Создаем копию изображения с повышенной яркостью
            bright_image = self.image.copy()
            bright_image.fill((50, 50, 50, 0), special_flags=pygame.BLEND_RGBA_ADD)
            screen.blit(bright_image, self.rect)
        else:
            screen.blit(self.image, self.rect)
        
        # Рисуем уровень гема
        self.level_surface.fill((0, 0, 0, 0))  # Очищаем поверхность
        font = pygame.font.Font(None, 24)
        level_text = font.render(str(self.level), True, COLORS['WHITE'])
        
        # Создаем полупрозрачный черный фон для текста
        text_rect = level_text.get_rect(center=(CELL_SIZE//2, CELL_SIZE//2))
        pygame.draw.rect(self.level_surface, (0, 0, 0, 128), 
                        text_rect.inflate(10, 10))
        
        # Рисуем текст
        self.level_surface.blit(level_text, text_rect)
        screen.blit(self.level_surface, self.rect)

    def update(self, dt):
        if self.is_moving and self.target_pos:
            self.animation_progress += dt / SWAP_DURATION
            if self.animation_progress >= 1:
                self.animation_progress = 0
                self.is_moving = False
                self.x, self.y = self.target_pos
                self.target_pos = None
            else:
                # Интерполяция позиции
                start_x = GRID_OFFSET_X + self.x * CELL_SIZE
                start_y = GRID_OFFSET_Y + self.y * CELL_SIZE
                target_x = GRID_OFFSET_X + self.target_pos[0] * CELL_SIZE
                target_y = GRID_OFFSET_Y + self.target_pos[1] * CELL_SIZE
                
                self.rect.x = start_x + (target_x - start_x) * self.animation_progress
                self.rect.y = start_y + (target_y - start_y) * self.animation_progress

    def move_to(self, target_x, target_y):
        self.is_moving = True
        self.target_pos = (target_x, target_y)

    def calculate_damage(self):
        damage = self.damage * self.level
        if random.random() < self.crit_chance:
            damage *= self.crit_multiplier
            return damage, True
        return damage, False

    def upgrade(self, stat):
        if stat == 'damage':
            self.damage += 5
        elif stat == 'crit_chance':
            self.crit_chance += 0.05
        elif stat == 'crit_multiplier':
            self.crit_multiplier += 0.5
        self.level += 1 