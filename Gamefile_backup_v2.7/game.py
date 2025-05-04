import pygame
import random
import json
import os
from config import *
from entities.gem import Gem
from ui.shop import Shop

class Game:
    def __init__(self):
        try:
            print("Инициализация Pygame...")
            pygame.init()
            print("Создание окна...")
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            pygame.display.set_caption("Match-3 RPG")
            print("Окно создано успешно")
            
            self.clock = pygame.time.Clock()
            self.running = True
            self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
            self.selected_gem = None
            self.enemy_health = ENEMY_MAX_HEALTH
            print(f"Здоровье врага инициализировано: {self.enemy_health}")
            self.coins = 0
            self.moves_left = 50
            print(f"Количество ходов: {self.moves_left}")
            self.shop = Shop(self)
            self.damage_popup = None
            self.damage_popup_time = 0
            self.damage_popup_value = 0
            self.npc_hit_time = None  # Для анимации получения урона
            
            # Загружаем фоновое изображение всего окна
            bg_path = os.path.join("images", "bg1-1.jpg")
            if not os.path.exists(bg_path):
                raise FileNotFoundError(f"Фоновое изображение не найдено: {bg_path}")
            self.background = pygame.image.load(bg_path).convert()
            self.background = pygame.transform.smoothscale(self.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
            
            # Загружаем фон поля
            self.field_bg = pygame.image.load(os.path.join("images", "backgraund.png")).convert_alpha()
            
            # Загружаем спрайт персонажа
            npc_sprite_path = os.path.join("images", "npc_g", "NPC-1-1.png")
            if not os.path.exists(npc_sprite_path):
                raise FileNotFoundError(f"Спрайт персонажа не найден: {npc_sprite_path}")
            self.npc_image = pygame.image.load(npc_sprite_path).convert_alpha()
            # Масштабируем спрайт под высоту игрового поля
            npc_height = GRID_SIZE * CELL_SIZE
            scale_factor = npc_height / self.npc_image.get_height()
            npc_width = int(self.npc_image.get_width() * scale_factor)
            self.npc_image = pygame.transform.smoothscale(self.npc_image, (npc_width, npc_height))
            
            print("Проверка директории с изображениями...")
            if not os.path.exists(IMAGE_DIR):
                raise FileNotFoundError(f"Директория с изображениями не найдена: {IMAGE_DIR}")
            print(f"Директория с изображениями найдена: {IMAGE_DIR}")
            
            print("Проверка файлов изображений...")
            for gem_type, image_path in GEM_IMAGES.items():
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Изображение не найдено: {image_path}")
                print(f"Изображение найдено: {image_path}")
            
            print("Инициализация игрового поля...")
            self.initialize_grid()
            print("Загрузка сохранения...")
            self.load_save()
            print(f"Здоровье врага после загрузки: {self.enemy_health}")
            print("Игра успешно инициализирована")
        except Exception as e:
            print(f"Ошибка при инициализации игры: {e}")
            self.running = False
            pygame.quit()
            raise

    def initialize_grid(self):
        # Создаем пустое поле
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Заполняем поле гемами, избегая комбинаций
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Список доступных типов гемов
                available_types = GEM_TYPES.copy()
                
                # Проверяем два предыдущих гема по горизонтали
                if x >= 2:
                    if (self.grid[y][x-1] and self.grid[y][x-2] and 
                        self.grid[y][x-1].type == self.grid[y][x-2].type):
                        # Удаляем тип, который создаст комбинацию
                        if self.grid[y][x-1].type in available_types:
                            available_types.remove(self.grid[y][x-1].type)
                
                # Проверяем два предыдущих гема по вертикали
                if y >= 2:
                    if (self.grid[y-1][x] and self.grid[y-2][x] and 
                        self.grid[y-1][x].type == self.grid[y-2][x].type):
                        # Удаляем тип, который создаст комбинацию
                        if self.grid[y-1][x].type in available_types:
                            available_types.remove(self.grid[y-1][x].type)
                
                # Если нет доступных типов, используем случайный
                if not available_types:
                    available_types = GEM_TYPES.copy()
                
                # Создаем новый гем
                self.grid[y][x] = Gem(x, y, random.choice(available_types))

    def draw(self):
        # Отображаем фоновое изображение
        self.screen.blit(self.background, (0, 0))
        
        # --- Красивая рамка и фон поля ---
        field_rect = pygame.Rect(
            GRID_OFFSET_X - 15,
            GRID_OFFSET_Y - 15,
            GRID_SIZE * CELL_SIZE + 30,
            GRID_SIZE * CELL_SIZE + 30
        )
        # Тень от поля
        shadow_rect = field_rect.move(8, 8)
        pygame.draw.rect(self.screen, COLORS['SHADOW'], shadow_rect, border_radius=18)
        # Фон поля — изображение
        bg_img = pygame.transform.smoothscale(self.field_bg, (field_rect.width, field_rect.height))
        self.screen.blit(bg_img, field_rect.topleft)
        # Рамка
        pygame.draw.rect(self.screen, COLORS['WHITE'], field_rect, 4, border_radius=18)
        
        # --- Гемы с тенью ---
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x]:
                    # Тень под гемом
                    shadow = pygame.Surface((CELL_SIZE-4, CELL_SIZE-4), pygame.SRCALPHA)
                    shadow.fill((0,0,0,80))
                    sx = GRID_OFFSET_X + x * CELL_SIZE + 4
                    sy = GRID_OFFSET_Y + y * CELL_SIZE + 8
                    self.screen.blit(shadow, (sx, sy))
                    # Сам гем
                    self.grid[y][x].draw(self.screen)
        
        # Рисуем секторную полосу здоровья врага
        health_bar_x = GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 50
        health_bar_y = GRID_OFFSET_Y
        
        # Настройки секторной полосы здоровья
        num_sectors = 10  # Количество секторов
        sector_width = ENEMY_HEALTH_BAR_WIDTH // num_sectors - 2  # Ширина сектора с учетом отступа
        sector_height = ENEMY_HEALTH_BAR_HEIGHT
        sector_spacing = 2  # Минимальный отступ между секторами
        
        # Вычисляем количество активных секторов на основе здоровья
        health_percentage = self.enemy_health / ENEMY_MAX_HEALTH
        active_sectors = int(health_percentage * num_sectors)
        
        # Неоновый зеленый цвет
        neon_green = (57, 255, 20)
        glow_green = (57, 255, 20, 100)  # Полупрозрачный для свечения
        
        # Рисуем каждый сектор
        for i in range(num_sectors):
            x = health_bar_x + i * (sector_width + sector_spacing)
            
            # Создаем поверхность для свечения
            glow_surface = pygame.Surface((sector_width + 8, sector_height + 8), pygame.SRCALPHA)
            
            # Рисуем фоновый (темный) сектор
            sector_rect = pygame.Rect(x, health_bar_y, sector_width, sector_height)
            pygame.draw.rect(self.screen, COLORS['DARK_GRAY'], sector_rect, border_radius=2)
            
            if i < active_sectors:
                # Рисуем свечение для активного сектора
                glow_rect = pygame.Rect(4, 4, sector_width, sector_height)
                pygame.draw.rect(glow_surface, glow_green, glow_rect, border_radius=2)
                self.screen.blit(glow_surface, (x - 4, health_bar_y - 4))
                
                # Рисуем активный сектор
                pygame.draw.rect(self.screen, neon_green, sector_rect, border_radius=2)
                # Добавляем белую обводку для большей яркости
                pygame.draw.rect(self.screen, COLORS['WHITE'], sector_rect, 1, border_radius=2)
        
        # Рисуем кнопку магазина в нижнем левом углу
        font = pygame.font.Font(None, 36)
        shop_button = pygame.Rect(GRID_OFFSET_X, GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 20, 150, 40)
        pygame.draw.rect(self.screen, COLORS['BLACK'], shop_button)
        pygame.draw.rect(self.screen, COLORS['WHITE'], shop_button, 2)
        shop_text = font.render("Магазин", True, COLORS['WHITE'])
        self.screen.blit(shop_text, (shop_button.centerx - shop_text.get_width() // 2,
                                    shop_button.centery - shop_text.get_height() // 2))
        
        # --- Рисуем монеты и ходы справа от кнопки магазин ---
        coins_x = shop_button.right + 20
        coins_y = shop_button.centery - 18
        coins_text = font.render(f"{self.coins}", True, COLORS['YELLOW'])
        self.screen.blit(coins_text, (coins_x, coins_y))
        moves_x = coins_x + coins_text.get_width() + 30
        moves_text = font.render(f"Ходы: {self.moves_left}", True, COLORS['WHITE'])
        self.screen.blit(moves_text, (moves_x, coins_y))
        
        # Рисуем магазин
        self.shop.draw(self.screen)
        
        # Рисуем спрайт персонажа справа от игрового поля
        npc_x = GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 50
        npc_y = GRID_OFFSET_Y
        # --- Эффект урона: только встряска ---
        shake = 0
        
        if self.npc_hit_time:
            current_time = pygame.time.get_ticks()
            hit_duration = 200  # Длительность эффекта в мс
            elapsed = current_time - self.npc_hit_time
            
            if elapsed < hit_duration:
                # Встряска с затуханием
                intensity = 1 - (elapsed / hit_duration)
                shake = int(8 * intensity) * random.choice([-1, 1])
            else:
                self.npc_hit_time = None
        
        # Отрисовка персонажа только со встряской
        self.screen.blit(self.npc_image, (npc_x + shake, npc_y))
        
        # --- Рисуем popup урона ---
        if self.damage_popup:
            elapsed = pygame.time.get_ticks() - self.damage_popup
            if elapsed < self.damage_popup_time:
                font = pygame.font.Font(None, 48)
                dmg_text = font.render(f"-{self.damage_popup_value}", True, COLORS['RED'])
                text_x = npc_x + self.npc_image.get_width() // 2 - dmg_text.get_width() // 2
                text_y = npc_y - 40 - int(40 * (elapsed / self.damage_popup_time))
                self.screen.blit(dmg_text, (text_x, text_y))
            else:
                self.damage_popup = None
        
        pygame.display.flip()

    def handle_click(self, pos):
        # Проверяем, есть ли гемы в процессе анимации
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] and (self.grid[y][x].is_moving or self.grid[y][x].is_returning):
                    return
        
        # Проверяем клик по кнопке магазина
        shop_button = pygame.Rect(
            GRID_OFFSET_X,
            GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 20,
            150, 40
        )
        if shop_button.collidepoint(pos):
            self.shop.toggle_visibility()
            return
        
        # Если магазин открыт, обрабатываем клики в нем
        if self.shop.visible:
            self.shop.handle_click(pos)
            return
        
        # Обрабатываем клики по игровому полю
        x = (pos[0] - GRID_OFFSET_X) // CELL_SIZE
        y = (pos[1] - GRID_OFFSET_Y) // CELL_SIZE
        
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            if self.selected_gem is None:
                self.selected_gem = (x, y)
                self.grid[y][x].is_selected = True
            else:
                if self.is_adjacent(self.selected_gem, (x, y)):
                    # Меняем гемы местами
                    self.swap_gems(self.selected_gem, (x, y))
                    
                    # Проверяем совпадения
                    matches = self.check_matches()
                    if matches:
                        self.process_matches(matches)
                        self.moves_left -= 1
                    else:
                        # Если совпадений нет, возвращаем гемы в исходные позиции
                        self.swap_gems(self.selected_gem, (x, y))
                        self.grid[y][x].return_to_original()
                        self.grid[self.selected_gem[1]][self.selected_gem[0]].return_to_original()
                
                # Снимаем выделение
                self.grid[self.selected_gem[1]][self.selected_gem[0]].is_selected = False
                self.selected_gem = None

    def is_adjacent(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

    def swap_gems(self, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        
        # Временно сохраняем гемы
        gem1 = self.grid[y1][x1]
        gem2 = self.grid[y2][x2]
        
        # Обновляем позиции гемов в сетке
        self.grid[y1][x1] = gem2
        self.grid[y2][x2] = gem1
        
        # Обновляем координаты гемов
        if gem1:
            gem1.x, gem1.y = x2, y2
            gem1.move_to(x2, y2)
        if gem2:
            gem2.x, gem2.y = x1, y1
            gem2.move_to(x1, y1)

    def check_matches(self):
        matches = []
        # Проверяем горизонтальные совпадения
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE - 2):
                if (self.grid[y][x] is not None and 
                    self.grid[y][x+1] is not None and 
                    self.grid[y][x+2] is not None and
                    self.grid[y][x].type == self.grid[y][x+1].type == self.grid[y][x+2].type):
                    matches.append([(x, y), (x+1, y), (x+2, y)])

        # Проверяем вертикальные совпадения
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE - 2):
                if (self.grid[y][x] is not None and 
                    self.grid[y+1][x] is not None and 
                    self.grid[y+2][x] is not None and
                    self.grid[y][x].type == self.grid[y+1][x].type == self.grid[y+2][x].type):
                    matches.append([(x, y), (x, y+1), (x, y+2)])

        return matches

    def process_matches(self, matches):
        if not matches:  # Защита от пустого списка
            return
        
        # --- Анимация сложения ---
        for match in matches:
            # Находим центр комбинации
            center_x = sum([x for x, y in match]) / len(match)
            center_y = sum([y for x, y in match]) / len(match)
            for x, y in match:
                gem = self.grid[y][x]
                if gem:
                    gem.move_to_position(center_x, center_y)
        # Ждем завершения анимации
        animation_running = True
        while animation_running:
            animation_running = False
            for match in matches:
                for x, y in match:
                    gem = self.grid[y][x]
                    if gem and gem.is_moving:
                        animation_running = True
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.grid[y][x]:
                        self.grid[y][x].update(1/60)
            self.draw()
            self.clock.tick(60)
        # --- Конец анимации сложения ---
        
        total_damage = 0
        critical_hits = 0
        
        # Обрабатываем каждое совпадение
        for match in matches:
            for x, y in match:
                gem = self.grid[y][x]
                if gem:
                    # Получаем базовый урон и шанс крита
                    base_damage, crit_chance = gem.calculate_damage()
                    
                    # Учитываем бонусы из магазина
                    if self.shop.damage_bonus:
                        base_damage *= 1.5  # Увеличение урона на 50%
                        
                    if self.shop.crit_bonus:
                        crit_chance += 0.2  # Увеличение шанса крита на 20%
                        
                    # Проверяем крит
                    if random.random() < crit_chance:
                        damage = base_damage * gem.crit_multiplier
                        critical_hits += 1
                    else:
                        damage = base_damage
                        
                    total_damage += damage
                    gem.add_experience()
                    
                    # Удаляем гем
                    self.grid[y][x] = None
        
        # Наносим урон врагу
        self.enemy_health = max(0, self.enemy_health - total_damage)
        self.coins += critical_hits * 10
        
        # Заполняем пустые ячейки
        self.fill_empty_cells()
        
        # Обновляем таймеры бонусов
        self.shop.update()
        
        # Проверяем новые комбинации после заполнения/841
        new_matches = self.check_matches()
        if new_matches:
            print("Найдены новые комбинации после заполнения!")
            self.process_matches(new_matches)
        
        # --- Показываем popup урона ---
        if total_damage > 0:
            self.damage_popup = pygame.time.get_ticks()
            self.damage_popup_time = 1000  # мс
            self.damage_popup_value = int(total_damage)
            self.npc_hit_time = pygame.time.get_ticks()  # <-- для анимации урона

    def fill_empty_cells(self):
        for x in range(GRID_SIZE):
            empty_cells = 0
            for y in range(GRID_SIZE - 1, -1, -1):
                if self.grid[y][x] is None:
                    empty_cells += 1
                elif empty_cells > 0:
                    # Перемещаем гем вниз
                    self.grid[y + empty_cells][x] = self.grid[y][x]
                    self.grid[y][x] = None
                    self.grid[y + empty_cells][x].move_to(x, y + empty_cells)

            # Создаем новые гемы в пустых ячейках
            for y in range(empty_cells):
                new_gem = Gem(x, y)
                self.grid[y][x] = new_gem
                # Устанавливаем начальную позицию выше игрового поля
                new_gem.rect.y = GRID_OFFSET_Y - CELL_SIZE
                new_gem.move_to(x, y)

    def save_game(self):
        save_data = {
            'enemy_health': self.enemy_health,
            'coins': self.coins,
            'moves_left': self.moves_left,
            'grid': [[{'type': gem.type, 'level': gem.level} if gem else None 
                     for gem in row] for row in self.grid]
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(save_data, f)

    def load_save(self):
        try:
            with open(SAVE_FILE, 'r') as f:
                save_data = json.load(f)
                # Загружаем здоровье врага только если оно больше 0
                if save_data['enemy_health'] > 0:
                    self.enemy_health = save_data['enemy_health']
                self.coins = save_data['coins']
                self.moves_left = save_data['moves_left']
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if save_data['grid'][y][x]:
                            gem_data = save_data['grid'][y][x]
                            self.grid[y][x] = Gem(x, y, gem_data['type'])
                            self.grid[y][x].level = gem_data['level']
        except FileNotFoundError:
            print("Сохранение не найдено, начинаем новую игру")
        except Exception as e:
            print(f"Ошибка при загрузке сохранения: {e}")
            print("Начинаем новую игру")

    def run(self):
        print("Запуск игрового цикла...")
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Получен сигнал выхода")
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.grid[y][x]:
                        self.grid[y][x].update(dt)

            self.draw()

            # Проверяем условие окончания игры только если есть ходы
            if self.moves_left <= 0:
                print("Закончились ходы")
                self.save_game()
                self.running = False
            elif self.enemy_health <= 0:
                print("Враг побежден")
                self.save_game()
                self.running = False

        print("Завершение работы...")
        pygame.quit()

    def bounce(self, t):
        # Функция эффекта отскока
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - 2 * (1 - t) * (1 - t)

if __name__ == "__main__":
    print("Запуск игры...")
    game = Game()
    game.run()
    print("Игра завершена") 