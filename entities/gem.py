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
        
        # Новые атрибуты для системы прокачки
        self.kills = 0  # Количество убийств
        self.combo_count = 0  # Счетчик комбо
        self.max_combo = 0  # Максимальное достигнутое комбо
        self.special_abilities = []  # Список специальных способностей
        self.evolution_stage = 1  # Стадия эволюции гема
        self.evolution_requirements = {
            2: {'level': 5, 'kills': 10},
            3: {'level': 10, 'kills': 25},
            4: {'level': 15, 'kills': 50},
            5: {'level': 20, 'kills': 100}
        }
        
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
            FIELD_OFFSET_X + x * CELL_SIZE + 2,
            FIELD_OFFSET_Y + y * CELL_SIZE + 2,
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
        self.is_disappearing = False
        self.disappear_start_time = 0
        self.disappear_duration = 700  # мс (сокращенное время анимации)
        self.disappear_velocity = [0, 0]  # [vx, vy]
        self.disappear_rotation = 0
        self.disappear_rotation_speed = random.uniform(-720, 720)  # градусы в секунду
        self.disappear_scale = 1.0
        self.disappear_gravity = 1500  # пикселей в секунду²
        self.disappear_initial_velocity = -1500  # увеличенная начальная скорость вверх
        self.disappear_initial_x = 0  # Начальная X позиция
        self.disappear_initial_y = 0  # Начальная Y позиция
        self.is_falling = False
        self.fall_speed = 0
        self.max_fall_speed = 1500  # Увеличенная максимальная скорость падения
        self.fall_acceleration = 3000  # Увеличенное ускорение падения

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
        
        if self.is_disappearing:
            # Сохраняем оригинальный размер
            original_size = (CELL_SIZE - 4, CELL_SIZE - 4)
            
            # Создаем поверхность для вращающегося гема
            rotated_size = int(max(original_size) * self.disappear_scale * 1.5)
            rotated_surf = pygame.Surface((rotated_size, rotated_size), pygame.SRCALPHA)
            
            # Центрируем гем на поверхности
            center_x = rotated_size // 2
            center_y = rotated_size // 2
            
            # Масштабируем и рисуем гем
            scaled_size = (int(original_size[0] * self.disappear_scale), 
                         int(original_size[1] * self.disappear_scale))
            scaled_image = pygame.transform.scale(self.image, scaled_size)
            
            # Рисуем гем по центру
            rotated_surf.blit(scaled_image, 
                            (center_x - scaled_size[0]//2, 
                             center_y - scaled_size[1]//2))
            
            # Вращаем поверхность
            rotated_image = pygame.transform.rotate(rotated_surf, self.disappear_rotation)
            
            # Рисуем с учетом прозрачности
            alpha = int(255 * (1 - self.disappear_progress))
            rotated_image.set_alpha(alpha)
            
            # Рисуем на экране
            screen.blit(rotated_image, 
                       (self.rect.x - rotated_image.get_width()//2 + original_size[0]//2,
                        self.rect.y - rotated_image.get_height()//2 + original_size[1]//2))

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
            self.rect.x = FIELD_OFFSET_X + (start_x + (end_x - start_x) * progress) * CELL_SIZE + 2
            self.rect.y = FIELD_OFFSET_Y + (start_y + (end_y - start_y) * progress) * CELL_SIZE + 2
            
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
                    self.rect.x = FIELD_OFFSET_X + self.x * CELL_SIZE + 2
                    self.rect.y = FIELD_OFFSET_Y + self.y * CELL_SIZE + 2
                self.scale = 1.0  # Сбрасываем масштаб

        if self.is_disappearing:
            now = pygame.time.get_ticks()
            elapsed = now - self.disappear_start_time
            self.disappear_progress = min(1.0, elapsed / self.disappear_duration)
            
            # Обновляем вращение
            self.disappear_rotation += self.disappear_rotation_speed * dt
            
            # Обновляем размер
            self.disappear_scale = 1.0 - 0.5 * self.disappear_progress  # Увеличиваем уменьшение размера
            
            # Обновляем позицию
            self.rect.x += self.disappear_velocity[0] * dt
            self.rect.y += self.disappear_velocity[1] * dt
            
            # Применяем гравитацию
            self.disappear_velocity[1] += self.disappear_gravity * dt
            
            # Проверяем, не ушел ли гем слишком далеко от поля
            if (abs(self.rect.x - self.disappear_initial_x) > WINDOW_WIDTH or 
                self.rect.y > WINDOW_HEIGHT + 100):
                return 'remove'
            
            if elapsed >= self.disappear_duration:
                return 'remove'  # Сигнал для удаления гема

        # Если гем падает, обновляем его позицию
        if self.is_falling:
            self.update_falling(dt)

        return None

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

    def add_experience(self, is_kill=False, combo_multiplier=1):
        # Базовый опыт за использование
        base_xp = GEM_EXPERIENCE['BASE_XP']
        
        # Множители опыта
        level_multiplier = GEM_EXPERIENCE['LEVEL_MULTIPLIER']
        kill_multiplier = 2.0 if is_kill else 1.0
        combo_bonus = min(combo_multiplier * 0.5, 2.0)  # Максимум +200% за комбо
        
        # Итоговый опыт
        xp_gain = base_xp * (level_multiplier ** (self.level - 1)) * kill_multiplier * (1 + combo_bonus)
        self.experience += xp_gain
        
        # Обновляем счетчики
        if is_kill:
            self.kills += 1
            self.combo_count += 1
            self.max_combo = max(self.max_combo, self.combo_count)
        
        # Проверяем эволюцию
        self.check_evolution()
        
        # Проверяем повышение уровня
        xp_needed = self.get_xp_for_next_level()
        if self.experience >= xp_needed and self.level < GEM_EXPERIENCE['MAX_LEVEL']:
            self.level_up()

    def check_evolution(self):
        next_stage = self.evolution_stage + 1
        if next_stage in self.evolution_requirements:
            reqs = self.evolution_requirements[next_stage]
            if (self.level >= reqs['level'] and 
                self.kills >= reqs['kills']):
                self.evolve()

    def evolve(self):
        self.evolution_stage += 1
        # Улучшаем характеристики
        self.damage *= 1.5
        self.crit_chance += 0.05
        self.crit_multiplier += 0.2
        
        # Добавляем специальную способность в зависимости от типа гема
        ability = self.get_special_ability()
        if ability:
            self.special_abilities.append(ability)
        
        # Визуальный эффект эволюции
        self.start_evolution_animation()

    def get_special_ability(self):
        abilities = {
            'red': {
                'name': 'Огненный взрыв',
                'effect': 'Наносит дополнительный урон всем врагам'
            },
            'blue': {
                'name': 'Ледяная тюрьма',
                'effect': 'Увеличивает шанс крита на 50%'
            },
            'green': {
                'name': 'Ядовитый туман',
                'effect': 'Наносит урон в течение 3 ходов'
            },
            'yellow': {
                'name': 'Молния',
                'effect': 'Шанс мгновенно убить врага'
            },
            'purple': {
                'name': 'Темная магия',
                'effect': 'Увеличивает урон всех гемов'
            },
            'cyan': {
                'name': 'Водный щит',
                'effect': 'Снижает получаемый урон'
            }
        }
        return abilities.get(self.type)

    def start_evolution_animation(self):
        # Здесь можно добавить анимацию эволюции
        self.pulse_time = pygame.time.get_ticks()
        self.scale = 1.5

    def calculate_damage(self):
        base_damage = self.damage * self.level
        
        # Бонусы от эволюции
        evolution_multiplier = 1 + (self.evolution_stage - 1) * 0.2
        
        # Бонусы от комбо
        combo_multiplier = 1 + min(self.combo_count * 0.1, 1.0)
        
        # Итоговый урон
        damage = base_damage * evolution_multiplier * combo_multiplier
        
        # Проверяем крит
        if random.random() < self.crit_chance:
            damage *= self.crit_multiplier
            return damage, True
        return damage, False

    def reset_combo(self):
        self.combo_count = 0

    def get_xp_for_next_level(self):
        # Усложняем формулу получения опыта
        base_xp = 100
        level_multiplier = 1.5
        evolution_bonus = 1 + (self.evolution_stage - 1) * 0.2
        return base_xp * (level_multiplier ** (self.level - 1)) * evolution_bonus

    def level_up(self):
        if self.level < GEM_EXPERIENCE['MAX_LEVEL']:
            self.level += 1
            self.damage *= GEM_EXPERIENCE['DAMAGE_MULTIPLIER']
            self.crit_chance += 0.02
            self.crit_multiplier += 0.1
            
            # Сбрасываем избыточный опыт
            self.experience = 0
            
            # Проверяем эволюцию после повышения уровня
            self.check_evolution()

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

    def start_disappear(self):
        self.is_disappearing = True
        self.disappear_start_time = pygame.time.get_ticks()
        self.disappear_progress = 0
        self.disappear_scale = 1.0
        self.disappear_rotation = 0
        
        # Сохраняем начальную позицию
        self.disappear_initial_x = self.rect.x
        self.disappear_initial_y = self.rect.y
        
        # Задаем начальную скорость
        angle = random.uniform(-math.pi/3, math.pi/3)  # Увеличиваем угол разлета
        speed = random.uniform(400, 600)  # Случайная начальная скорость
        self.disappear_velocity = [
            math.sin(angle) * speed,  # Горизонтальная составляющая
            self.disappear_initial_velocity  # Вертикальная составляющая (вверх)
        ]

    def start_falling(self, target_y):
        """Запуск анимации падения"""
        self.is_falling = True
        self.target_y = target_y
        self.fall_speed = 0
        # Сохраняем текущую позицию как начальную
        self.start_y = self.rect.y
        # Вычисляем целевую позицию
        self.target_pixel_y = GRID_OFFSET_Y + target_y * CELL_SIZE + 2

    def update_falling(self, dt):
        """Обновление анимации падения"""
        if not self.is_falling:
            return False

        # Увеличиваем скорость падения
        self.fall_speed = min(self.max_fall_speed, self.fall_speed + self.fall_acceleration * dt)
        
        # Вычисляем новую позицию
        target_pixel_y = GRID_OFFSET_Y + self.target_y * CELL_SIZE
        current_pixel_y = self.rect.y
        
        # Если гем достиг цели
        if current_pixel_y >= target_pixel_y:
            self.rect.y = target_pixel_y
            self.is_falling = False
            # Обновляем координаты в сетке
            self.y = self.target_y
            self.rect.x = FIELD_OFFSET_X + self.x * CELL_SIZE + 2
            self.rect.y = FIELD_OFFSET_Y + self.y * CELL_SIZE + 2
            return False
        
        # Ускоряем падение если гем далеко от цели
        distance_to_target = target_pixel_y - current_pixel_y
        if distance_to_target > CELL_SIZE * 2:
            # Дополнительное ускорение для гемов, которые падают издалека
            self.fall_speed = min(self.max_fall_speed * 1.5, self.fall_speed * 1.1)
        
        # Двигаем гем вниз
        self.rect.y += self.fall_speed * dt
        return True 