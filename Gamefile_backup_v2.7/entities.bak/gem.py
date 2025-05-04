import pygame
import random
from config import *

class Gem:
    def __init__(self, x, y, gem_type=None):
        self.x = x
        self.y = y
        self.type = gem_type if gem_type else random.choice(GEM_TYPES)
        self.level = 1
        self.experience = 0
        self.damage = BASE_DAMAGE
        self.crit_chance = CRIT_CHANCE
        self.crit_multiplier = CRIT_MULTIPLIER
        
        # Загружаем изображение гема
        image_path = GEM_IMAGES[self.type]
        try:
            self.original_image = pygame.image.load(image_path)
        except pygame.error:
            print(f"Ошибка загрузки изображения: {image_path}")
            # Создаем пустое изображение как заглушку
            self.original_image = pygame.Surface((CELL_SIZE - 4, CELL_SIZE - 4))
            self.original_image.fill(COLORS['GRAY'])
        
        # Масштабируем изображение до стандартного размера
        self.image = pygame.transform.scale(self.original_image, (CELL_SIZE - 4, CELL_SIZE - 4))
        
        self.rect = pygame.Rect(
            GRID_OFFSET_X + x * CELL_SIZE + 2,
            GRID_OFFSET_Y + y * CELL_SIZE + 2,
            CELL_SIZE - 4,
            CELL_SIZE - 4
        )
        self.is_selected = False
        self.is_moving = False
        self.is_returning = False
        self.target_x = x
        self.target_y = y
        self.original_x = x
        self.original_y = y
        self.move_start_time = 0
        self.return_start_time = 0
        self.scale = 1.0

    def draw(self, screen):
        # Если гем в процессе анимации, применяем масштабирование
        if (self.is_moving or self.is_returning) and self.scale != 1.0:
            scaled_size = (int((CELL_SIZE - 4) * self.scale), int((CELL_SIZE - 4) * self.scale))
            scaled_image = pygame.transform.scale(self.image, scaled_size)
            
            # Центрируем масштабированное изображение
            offset_x = (CELL_SIZE - 4 - scaled_size[0]) // 2
            offset_y = (CELL_SIZE - 4 - scaled_size[1]) // 2
            
        # Рисуем гем
            screen.blit(scaled_image, (self.rect.x + offset_x, self.rect.y + offset_y))
        else:
            # Рисуем гем без масштабирования
            screen.blit(self.image, self.rect)
        
        # Если гем выбран, рисуем рамку
        if self.is_selected:
            pygame.draw.rect(screen, COLORS['WHITE'], self.rect, 2)

    def update(self, dt):
        if self.is_moving or self.is_returning:
            if self.is_moving:
                progress = min(1.0, (pygame.time.get_ticks() - self.move_start_time) / MOVE_DURATION)
                start_x = self.original_x
                start_y = self.original_y
                end_x = self.target_x
                end_y = self.target_y
            else:  # is_returning
                progress = min(1.0, (pygame.time.get_ticks() - self.return_start_time) / RETURN_DURATION)
                start_x = self.target_x
                start_y = self.target_y
                end_x = self.original_x
                end_y = self.original_y

            # Применяем функцию плавности
            progress = self.ease_in_out(progress)
            
            # Обновляем позицию
            self.rect.x = GRID_OFFSET_X + (start_x + (end_x - start_x) * progress) * CELL_SIZE + 2
            self.rect.y = GRID_OFFSET_Y + (start_y + (end_y - start_y) * progress) * CELL_SIZE + 2
            
            # Обновляем масштаб для эффекта анимации
            self.scale = 1.0 + 0.1 * (1 - abs(progress - 0.5) * 2)

            # Если анимация завершена
            if progress >= 1.0:
                if self.is_moving:
                    self.is_moving = False
                    self.original_x = self.target_x
                    self.original_y = self.target_y
                else:  # is_returning
                    self.is_returning = False
                    self.x = self.original_x
                    self.y = self.original_y
                    self.rect.x = GRID_OFFSET_X + self.x * CELL_SIZE + 2
                    self.rect.y = GRID_OFFSET_Y + self.y * CELL_SIZE + 2
                self.scale = 1.0  # Сбрасываем масштаб

    def ease_in_out(self, t):
        # Функция плавности для более естественного движения
        return t * t * (3 - 2 * t)

    def bounce(self, t):
        # Функция эффекта отскока
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - 2 * (1 - t) * (1 - t)

    def move_to(self, target_x, target_y):
        self.is_moving = True
        self.target_x = target_x
        self.target_y = target_y
        self.original_x = self.x
        self.original_y = self.y
        self.move_start_time = pygame.time.get_ticks()
        self.x = target_x
        self.y = target_y

    def return_to_original(self):
        self.is_returning = True
        self.return_start_time = pygame.time.get_ticks()

    def add_experience(self):
        # Добавляем опыт за использование гема
        base_xp = GEM_EXPERIENCE['BASE_XP']
        level_multiplier = GEM_EXPERIENCE['LEVEL_MULTIPLIER']
        xp_gain = base_xp * (level_multiplier ** (self.level - 1))
        self.experience += xp_gain
        
        # Проверяем, достаточно ли опыта для повышения уровня
        xp_needed = self.get_xp_for_next_level()
        if self.experience >= xp_needed and self.level < GEM_EXPERIENCE['MAX_LEVEL']:
            self.level_up()

    def get_xp_for_next_level(self):
        # Формула для расчета необходимого опыта
        return 100 * (1.5 ** (self.level - 1))

    def level_up(self):
        if self.level < GEM_EXPERIENCE['MAX_LEVEL']:
            self.level += 1
            self.damage *= GEM_EXPERIENCE['DAMAGE_MULTIPLIER']
            self.crit_chance += 0.02
            self.crit_multiplier += 0.1
            # Сбрасываем избыточный опыт
            self.experience = 0

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

    def move_to_position(self, pos_x, pos_y):
        self.is_moving = True
        self.target_x = pos_x
        self.target_y = pos_y
        self.original_x = self.x
        self.original_y = self.y
        self.move_start_time = pygame.time.get_ticks()
        # Не меняем self.x/self.y, чтобы не сбивать сетку 