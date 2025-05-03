import pygame
import random
from config import *

class Gem:
    def __init__(self, x, y, gem_type):
        self.x = x
        self.y = y
        self.gem_type = gem_type
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.image.fill(COLORS[gem_type])
        self.rect = self.image.get_rect()
        self.rect.x = GRID_OFFSET_X + x * CELL_SIZE
        self.rect.y = GRID_OFFSET_Y + y * CELL_SIZE
        self.is_selected = False
        self.is_moving = False
        self.move_start_time = 0
        self.original_x = x
        self.original_y = y
        self.is_exploding = False
        self.explosion_timer = 0
        self.explosion_duration = EXPLOSION_DURATION
        self.explosion_scale = 1.0
        self.explosion_alpha = 1.0
        self.experience = 0
        self.level = 1
        self.damage = BASE_DAMAGE
        self.crit_chance = CRIT_CHANCE
        self.crit_multiplier = CRIT_MULTIPLIER
        
        # Загружаем изображение гема
        image_path = GEM_IMAGES[self.gem_type]
        try:
            self.original_image = pygame.image.load(image_path)
        except pygame.error:
            print(f"Ошибка загрузки изображения: {image_path}")
            # Создаем пустое изображение как заглушку
            self.original_image = pygame.Surface((CELL_SIZE - 4, CELL_SIZE - 4))
            self.original_image.fill(COLORS['GRAY'])
        
        # Масштабируем изображение до стандартного размера
        self.image = pygame.transform.scale(self.original_image, (CELL_SIZE - 4, CELL_SIZE - 4))
        
        self.is_returning = False
        self.return_start_time = 0
        self.scale = 1.0

    def draw(self, screen):
        if self.is_exploding:
            # Создаем копию изображения для анимации
            scaled_image = pygame.transform.scale(
                self.image,
                (int(CELL_SIZE * self.explosion_scale),
                 int(CELL_SIZE * self.explosion_scale))
            )
            # Устанавливаем прозрачность
            scaled_image.set_alpha(int(255 * self.explosion_alpha))
            # Получаем прямоугольник для центрирования
            rect = scaled_image.get_rect(center=(
                GRID_OFFSET_X + self.x * CELL_SIZE + CELL_SIZE // 2,
                GRID_OFFSET_Y + self.y * CELL_SIZE + CELL_SIZE // 2
            ))
            screen.blit(scaled_image, rect)
        else:
            # Обычная отрисовка гема
            if self.is_moving:
                # Используем позицию из rect для анимации движения
                screen.blit(self.image, self.rect)
            else:
                # Используем стандартную позицию
                screen.blit(self.image, (
                    GRID_OFFSET_X + self.x * CELL_SIZE,
                    GRID_OFFSET_Y + self.y * CELL_SIZE
                ))
                
            if self.is_selected:
                # Отрисовка выделения
                pygame.draw.rect(screen, (255, 255, 255), (
                    GRID_OFFSET_X + self.x * CELL_SIZE,
                    GRID_OFFSET_Y + self.y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                ), 2)

    def update(self, dt):
        if self.is_exploding:
            self.explosion_timer += dt
            if self.explosion_timer >= self.explosion_duration:
                self.is_exploding = False
            else:
                # Обновляем масштаб и прозрачность
                progress = self.explosion_timer / self.explosion_duration
                self.explosion_scale = 1.0 + progress * 0.5  # Увеличиваем до 1.5x
                self.explosion_alpha = 1.0 - progress  # Плавно уменьшаем прозрачность
                
        if self.is_moving:
            elapsed = pygame.time.get_ticks() - self.move_start_time
            if elapsed >= SWAP_DURATION:
                self.is_moving = False
            else:
                # Вычисляем прогресс анимации
                progress = elapsed / SWAP_DURATION
                # Применяем плавное замедление
                progress = self.ease_in_out(progress)
                # Вычисляем текущую позицию
                current_x = self.original_x + (self.x - self.original_x) * progress
                current_y = self.original_y + (self.y - self.original_y) * progress
                # Обновляем позицию для отрисовки
                self.rect.x = GRID_OFFSET_X + current_x * CELL_SIZE
                self.rect.y = GRID_OFFSET_Y + current_y * CELL_SIZE

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
        self.move_start_time = pygame.time.get_ticks()
        self.original_x = self.x
        self.original_y = self.y
        self.x = target_x
        self.y = target_y

    def return_to_original(self):
        self.is_returning = True
        self.return_start_time = pygame.time.get_ticks()

    def add_experience(self):
        self.experience += 1
        if self.experience >= self.level * 2:
            self.level_up()

    def get_xp_for_next_level(self):
        # Формула для расчета необходимого опыта
        return 100 * (1.5 ** (self.level - 1))

    def level_up(self):
        self.level += 1
        self.experience = 0
        self.damage += BASE_DAMAGE * 0.1
        self.crit_chance += CRIT_CHANCE * 0.05

    def calculate_damage(self):
        return self.damage, self.crit_chance

    def upgrade(self, stat):
        if stat == 'damage':
            self.damage += 5
        elif stat == 'crit_chance':
            self.crit_chance += 0.05
        elif stat == 'crit_multiplier':
            self.crit_multiplier += 0.5
        self.level += 1

    def explode(self):
        self.is_exploding = True
        self.explosion_timer = 0
        self.explosion_scale = 1.0
        self.explosion_alpha = 1.0 