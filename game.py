import pygame
import random
import json
import os
from config import *
from entities.gem import Gem
from ui.shop import Shop

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gem Battle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_gem = None
        self.enemy_health = ENEMY_HEALTH
        self.moves_left = MOVES_LEFT
        self.coins = STARTING_COINS
        self.shop = Shop(self)
        self.initialize_grid()
        self.running = True
        print(f"Здоровье врага инициализировано: {self.enemy_health}")
        print(f"Количество ходов: {self.moves_left}")
        print(f"Начальное количество монет: {self.coins}")
        
        print("Проверка директории с изображениями...")
        if not os.path.exists(IMAGE_DIR):
            raise FileNotFoundError(f"Директория с изображениями не найдена: {IMAGE_DIR}")
        print(f"Директория с изображениями найдена: {IMAGE_DIR}")
        
        print("Проверка файлов изображений...")
        for gem_type, image_path in GEM_IMAGES.items():
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Изображение не найдено: {image_path}")
            print(f"Изображение найдено: {image_path}")
        
        print("Загрузка сохранения...")
        self.load_save()
        print(f"Здоровье врага после загрузки: {self.enemy_health}")
        print("Игра успешно инициализирована")

    def initialize_grid(self):
        # Создаем случайные гемы
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Выбираем случайный тип гема
                gem_type = random.choice(GEM_TYPES)
                # Создаем гем
                self.grid[y][x] = Gem(x, y, gem_type)
                
        # Проверяем и удаляем начальные совпадения
        matches = self.check_matches()
        while matches:
            for match in matches:
                for x, y in match:
                    self.grid[y][x] = None
            self.fill_empty_cells()
            matches = self.check_matches()

    def draw(self):
        # Очистка экрана
        self.screen.fill((0, 0, 0))
        
        # Отрисовка сетки
        self.draw_grid()
        
        # Отрисовка UI
        self.draw_ui()
        
        # Обновление экрана
        pygame.display.flip()

    def handle_click(self, pos):
        # Проверяем клик по кнопке магазина
        shop_button_rect = pygame.Rect(
            GRID_OFFSET_X,
            GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 20,
            100,
            40
        )
        if shop_button_rect.collidepoint(pos):
            self.shop.toggle_visibility()
            return
            
        # Проверяем клик по магазину
        if self.shop.is_visible:
            self.shop.handle_click(pos)
            return
            
        # Проверяем клик по игровому полю
        if (GRID_OFFSET_X <= pos[0] <= GRID_OFFSET_X + GRID_SIZE * CELL_SIZE and
            GRID_OFFSET_Y <= pos[1] <= GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE):
            # Вычисляем координаты ячейки
            x = (pos[0] - GRID_OFFSET_X) // CELL_SIZE
            y = (pos[1] - GRID_OFFSET_Y) // CELL_SIZE
            
            # Проверяем, что координаты в пределах сетки
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                # Если гем уже выбран
                if self.selected_gem:
                    # Проверяем, что выбранный гем и кликнутый гем соседние
                    if self.are_adjacent(self.selected_gem, self.grid[y][x]):
                        # Меняем гемы местами
                        self.swap_gems(self.selected_gem, self.grid[y][x])
                        
                        # Проверяем совпадения
                        matches = self.check_matches()
                        if matches:
                            # Обрабатываем совпадения
                            self.process_matches(matches)
                            # Уменьшаем количество ходов
                            self.moves_left -= 1
                        else:
                            # Если совпадений нет, возвращаем гемы на место
                            self.swap_gems(self.grid[y][x], self.selected_gem)
                            
                        # Снимаем выделение
                        self.selected_gem.is_selected = False
                        self.selected_gem = None
                    else:
                        # Если гемы не соседние, снимаем выделение
                        self.selected_gem.is_selected = False
                        self.selected_gem = None
                else:
                    # Выбираем гем
                    self.selected_gem = self.grid[y][x]
                    if self.selected_gem:
                        self.selected_gem.is_selected = True

    def are_adjacent(self, gem1, gem2):
        return abs(gem1.x - gem2.x) + abs(gem1.y - gem2.y) == 1

    def swap_gems(self, gem1, gem2):
        # Получаем координаты гемов
        x1, y1 = gem1.x, gem1.y
        x2, y2 = gem2.x, gem2.y
        
        # Меняем гемы местами в сетке
        self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
        
        # Обновляем позиции гемов
        gem1.x, gem1.y = x2, y2
        gem2.x, gem2.y = x1, y1
        
        # Запускаем анимацию обмена
        gem1.move_to(x2, y2)
        gem2.move_to(x1, y1)
        
        # Ждем завершения анимации
        pygame.time.wait(SWAP_DURATION)

    def check_matches(self):
        matches = []
        
        # Проверяем горизонтальные совпадения
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE - 2):
                if (self.grid[y][x] and self.grid[y][x + 1] and self.grid[y][x + 2] and
                    self.grid[y][x].gem_type == self.grid[y][x + 1].gem_type == self.grid[y][x + 2].gem_type):
                    match = [(x, y), (x + 1, y), (x + 2, y)]
                    # Проверяем, есть ли продолжение совпадения
                    for i in range(x + 3, GRID_SIZE):
                        if self.grid[y][i] and self.grid[y][i].gem_type == self.grid[y][x].gem_type:
                            match.append((i, y))
                        else:
                            break
                    matches.append(match)
                    
        # Проверяем вертикальные совпадения
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE - 2):
                if (self.grid[y][x] and self.grid[y + 1][x] and self.grid[y + 2][x] and
                    self.grid[y][x].gem_type == self.grid[y + 1][x].gem_type == self.grid[y + 2][x].gem_type):
                    match = [(x, y), (x, y + 1), (x, y + 2)]
                    # Проверяем, есть ли продолжение совпадения
                    for i in range(y + 3, GRID_SIZE):
                        if self.grid[i][x] and self.grid[i][x].gem_type == self.grid[y][x].gem_type:
                            match.append((x, i))
                        else:
                            break
                    matches.append(match)
                    
        return matches

    def process_matches(self, matches):
        if not matches:  # Защита от пустого списка
            return
            
        total_damage = 0
        critical_hits = 0
        gems_to_explode = set()
        
        # Сначала отмечаем все гемы для взрыва
        for match in matches:
            for x, y in match:
                if self.grid[y][x]:
                    gems_to_explode.add((x, y))
        
        # Запускаем анимацию взрыва для всех отмеченных гемов
        for x, y in gems_to_explode:
            self.grid[y][x].explode()
        
        # Ждем завершения анимации
        pygame.time.wait(int(EXPLOSION_DURATION * 1000))
        
        # После завершения анимации обрабатываем урон и удаляем гемы
        for x, y in gems_to_explode:
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
        
        # Проверяем новые комбинации после заполнения
        new_matches = self.check_matches()
        if new_matches:
            print("Найдены новые комбинации после заполнения!")
            self.process_matches(new_matches)

    def fill_empty_cells(self):
        # Сначала перемещаем существующие гемы вниз
        for x in range(GRID_SIZE):
            empty_cells = []
            for y in range(GRID_SIZE - 1, -1, -1):
                if self.grid[y][x] is None:
                    empty_cells.append(y)
                elif empty_cells:
                    # Находим самую нижнюю пустую ячейку
                    target_y = empty_cells.pop(0)
                    # Перемещаем гем вниз
                    self.grid[target_y][x] = self.grid[y][x]
                    self.grid[target_y][x].y = target_y
                    self.grid[y][x] = None
                    # Запускаем анимацию падения
                    self.grid[target_y][x].move_to(x, target_y)
                    
        # Затем заполняем оставшиеся пустые ячейки новыми гемами
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if self.grid[y][x] is None:
                    # Создаем новый гем выше игрового поля
                    gem = Gem(x, -1, random.choice(GEM_TYPES))
                    self.grid[y][x] = gem
                    # Запускаем анимацию падения
                    gem.move_to(x, y)

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
        running = True
        while running:
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                    
            # Отрисовка
            self.draw()
            
            # Ограничение FPS
            self.clock.tick(60)
            
            # Проверка условий окончания игры
            if self.moves_left <= 0:
                print("Закончились ходы")
                running = False
            elif self.enemy_health <= 0:
                print("Враг побежден")
                running = False
                
        pygame.quit()

    def draw_grid(self):
        # Отрисовка сетки
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Отрисовка фона ячейки
                cell_rect = pygame.Rect(
                    GRID_OFFSET_X + x * CELL_SIZE,
                    GRID_OFFSET_Y + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                pygame.draw.rect(self.screen, (50, 50, 50), cell_rect)
                pygame.draw.rect(self.screen, (30, 30, 30), cell_rect, 1)
                
                # Отрисовка гема
                if self.grid[y][x]:
                    self.grid[y][x].draw(self.screen)
                    
        # Обновляем анимации всех гемов
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x]:
                    self.grid[y][x].update(self.clock.get_time() / 1000.0)

    def draw_ui(self):
        # Отрисовка здоровья врага
        health_text = self.font.render(f"Здоровье врага: {self.enemy_health}", True, (255, 255, 255))
        self.screen.blit(health_text, (10, 10))
        
        # Отрисовка количества ходов
        moves_text = self.font.render(f"Ходов осталось: {self.moves_left}", True, (255, 255, 255))
        self.screen.blit(moves_text, (10, 40))
        
        # Отрисовка количества золота
        coins_text = self.font.render(f"Золото: {self.coins}", True, (255, 255, 255))
        self.screen.blit(coins_text, (10, 70))
        
        # Отрисовка кнопки магазина
        shop_button = pygame.Rect(
            GRID_OFFSET_X,
            GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 20,
            100,
            40
        )
        pygame.draw.rect(self.screen, (100, 100, 100), shop_button)
        shop_text = self.font.render("Магазин", True, (255, 255, 255))
        self.screen.blit(shop_text, (
            shop_button.x + (shop_button.width - shop_text.get_width()) // 2,
            shop_button.y + (shop_button.height - shop_text.get_height()) // 2
        ))
        
        # Отрисовка магазина, если он открыт
        if self.shop.is_visible:
            self.shop.draw(self.screen)

if __name__ == "__main__":
    print("Запуск игры...")
    game = Game()
    game.run()
    print("Игра завершена") 