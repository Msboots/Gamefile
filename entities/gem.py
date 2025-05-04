import pygame
import random
import math
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
            FIELD_DRAW_OFFSET_X + FIELD_INNER_PADDING + x * CELL_SIZE + 2,
            FIELD_DRAW_OFFSET_Y + FIELD_INNER_PADDING + y * CELL_SIZE + 2,
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
        self.pulse_time = 0  # Таймер для пульсации
        self.shake_time = 0  # Таймер дрожания
        self.is_shaking = False
        self.shake_direction = 1

    def draw(self, screen, offset_x=0, offset_y=0):
        # Анимация дрожания
        shake_offset = 0
        if self.is_shaking:
            shake_offset = int(4 * math.sin(self.shake_time * 30) * self.shake_direction)
        # Анимация пульсации для выделенного гема
        if self.is_selected:
            scale = 1.17 + 0.08 * math.sin(self.pulse_time)
        elif (self.is_moving or self.is_returning) and self.scale != 1.0:
            scale = self.scale
        else:
            scale = 1.0

        draw_x = self.rect.x + offset_x + shake_offset
        draw_y = self.rect.y + offset_y

        if scale != 1.0:
            scaled_size = (int((CELL_SIZE - 4) * scale), int((CELL_SIZE - 4) * scale))
            scaled_image = pygame.transform.scale(self.image, scaled_size)
            offset_x_img = (CELL_SIZE - 4 - scaled_size[0]) // 2
            offset_y_img = (CELL_SIZE - 4 - scaled_size[1]) // 2
            screen.blit(scaled_image, (draw_x + offset_x_img, draw_y + offset_y_img))
        else:
            screen.blit(self.image, (draw_x, draw_y))
        
        # Убрана рамка выделения

    def update(self, dt):
        # Обновляем таймер пульсации
        if self.is_selected:
            self.pulse_time += dt * 6  # Скорость пульсации
        else:
            self.pulse_time = 0
        # Обновляем дрожание
        if self.is_shaking:
            self.shake_time += dt
            if self.shake_time > 0.25:
                self.is_shaking = False
                self.shake_time = 0
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
            self.rect.x = FIELD_DRAW_OFFSET_X + FIELD_INNER_PADDING + (start_x + (end_x - start_x) * progress) * CELL_SIZE + 2
            self.rect.y = FIELD_DRAW_OFFSET_Y + FIELD_INNER_PADDING + (start_y + (end_y - start_y) * progress) * CELL_SIZE + 2
            
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
                    self.rect.x = FIELD_DRAW_OFFSET_X + FIELD_INNER_PADDING + self.x * CELL_SIZE + 2
                    self.rect.y = FIELD_DRAW_OFFSET_Y + FIELD_INNER_PADDING + self.y * CELL_SIZE + 2
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

    def start_shake(self):
        self.is_shaking = True
        self.shake_time = 0
        self.shake_direction = random.choice([-1, 1]) 