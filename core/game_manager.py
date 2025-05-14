import pygame
import os
import json
import random
import math
from config import *
from entities.gem import Gem
from ui.shop import Shop
from ui.main_menu import MainMenu
from entities.npc import NPCManager
from ui.location_panel import LocationPanel, COSMIC_ZONES

class GameManager:
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
            self.coins = 0
            self.ether_crystals = 0  # Новая валюта за победу над боссами
            self.moves_left = 50
            print(f"Количество ходов: {self.moves_left}")
            self.shop = Shop(self)
            self.main_menu = MainMenu()
            self.game_started = False
            self.damage_popups = []  # Очередь popup-уронов: [{'value': int, 'is_crit': bool, 'start_time': int, 'color': (r,g,b)}]
            self.last_swap_target = None

            # Инициализация инвентаря
            self.inventory = []  # Список предметов в инвентаре
            self.inventory_slots = 6  # Количество слотов в инвентаре
            self.inventory_page = 0   # Текущая страница инвентаря
            self.items_per_page = 6   # Количество предметов на странице
            self.active_bonuses = []  # Активные бонусы с оставшейся длительностью
            
            # Загружаем кнопку для инвентаря
            button_path = os.path.join("images", "button_invert.png")
            if os.path.exists(button_path):
                self.inventory_button = pygame.image.load(button_path).convert_alpha()
                self.inventory_button = pygame.transform.scale(self.inventory_button, (36, 36))
            else:
                print(f"Предупреждение: Изображение кнопки не найдено: {button_path}")
                self.inventory_button = None

            self.field_rect = None
            self.hud_y = GRID_OFFSET_Y + BORDER + 10
            self.hud_height = GRID_SIZE * CELL_SIZE + 30

            # Хранилище для отслеживания побежденных боссов
            self.defeated_bosses = set()  # Сохраняем ID побежденных боссов

            bg_path = os.path.join("images", "bg1-1.jpg")
            if not os.path.exists(bg_path):
                raise FileNotFoundError(f"Фоновое изображение не найдено: {bg_path}")
            self.background = pygame.image.load(bg_path).convert()
            self.background = pygame.transform.smoothscale(self.background, (WINDOW_WIDTH, WINDOW_HEIGHT))

            self.field_bg = pygame.image.load(os.path.join("images", "backgraund.png")).convert_alpha()

            npc_sprite_path = os.path.join("images", "npc_g", "NPC-1-1.png")
            if not os.path.exists(npc_sprite_path):
                raise FileNotFoundError(f"Спрайт персонажа не найден: {npc_sprite_path}")
            self.npc_image = pygame.image.load(npc_sprite_path).convert_alpha()
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

            # Инициализируем gem_progress до создания гемов
            self._show_map = False
            self.gem_progress = {}
            for gem_type in GEM_TYPES:
                self.gem_progress[gem_type] = {
                    'level': 1,
                    'xp': 0,
                    'damage': 10,
                    'crit_chance': 0.05,
                    'crit_multiplier': 1.5,
                    'evolution': 0,  # Уровень эволюции гема (0 - нет, 1, 2, и т.д.)
                    'evolved_bonus': None  # Тип бонуса от эволюции
                }

            print("Инициализация игрового поля...")
            self.initialize_grid()

            print("Загрузка NPC из файла...")
            with open(NPCS_FILE, "r") as f:
                npc_list = json.load(f)
            self.npc_manager = NPCManager(npc_list, GRID_SIZE, CELL_SIZE, BORDER)

            print("Загрузка сохранения...")
            self.load_save()
            print("Игра успешно инициализирована")

            self.location_list = [
                {'name': 'Тундра', 'level': '1-1', 'status': None},
                {'name': 'Тундра', 'level': '1-2', 'status': None},
                {'name': 'Тундра', 'level': '1-3', 'status': None},
                {'name': 'Тундра', 'level': '1-4', 'status': 'quest'},
                {'name': 'Тундра', 'level': '1-5', 'status': None},
            ]
            self.location_index = 0  # старт с 1-1
            self.global_level = 1  # глобальный уровень (1 = 1-1)
            self.location_panel = LocationPanel(self.get_level_info, self.global_level)

            self.animating_gems = []  # Список гемов в процессе анимации
            self.falling_gems = []    # Список падающих гемов
            self.animation_complete = True  # Флаг завершения всех анимаций
            self.pending_matches = []  # Очередь комбинаций для обработки
            self.is_processing_matches = False  # Флаг обработки комбинаций
            self.waiting_for_animations = False  # Флаг ожидания завершения анимаций
        except Exception as e:
            print(f"Ошибка при инициализации игры: {e}")
            self.running = False
            pygame.quit()
            raise

    def initialize_grid(self):
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                available_types = GEM_TYPES.copy()
                if x >= 2:
                    if (self.grid[y][x-1] and self.grid[y][x-2] and 
                        self.grid[y][x-1].type == self.grid[y][x-2].type):
                        if self.grid[y][x-1].type in available_types:
                            available_types.remove(self.grid[y][x-1].type)
                if y >= 2:
                    if (self.grid[y-1][x] and self.grid[y-2][x] and 
                        self.grid[y-1][x].type == self.grid[y-2][x].type):
                        if self.grid[y-1][x].type in available_types:
                            available_types.remove(self.grid[y-1][x].type)
                if not available_types:
                    available_types = GEM_TYPES.copy()
                gem_type = random.choice(available_types)
                gem = Gem(x, y, gem_type)
                # --- Синхронизация с глобальным прогрессом ---
                prog = self.gem_progress[gem_type]
                gem.level = prog['level']
                gem.damage = prog['damage']
                gem.crit_chance = prog['crit_chance']
                gem.crit_multiplier = prog['crit_multiplier']
                self.grid[y][x] = gem

    def start(self):
        pass 

    def save_game(self):
        save_data = {
            'enemy_health': self.npc_manager.enemy_health,
            'coins': self.coins,
            'ether_crystals': self.ether_crystals,
            'moves_left': self.moves_left,
            'grid': [[{'type': gem.type, 'level': gem.level} if gem else None 
                     for gem in row] for row in self.grid],
            'npc_total_level': getattr(self.npc_manager, 'total_level', 1),
            'npc_cycle_count': getattr(self.npc_manager, 'cycle_count', 0),
            'gem_progress': self.gem_progress,
            'npc_current_image': self.npc_manager.current_npc['image'],
            'defeated_bosses': list(self.defeated_bosses),  # Сохраняем список побежденных боссов
            'inventory': self.inventory,  # Сохраняем инвентарь
            'active_bonuses': self.active_bonuses  # Сохраняем активные бонусы
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(save_data, f)

    def load_save(self):
        try:
            with open(SAVE_FILE, 'r') as f:
                save_data = json.load(f)
                if save_data['enemy_health'] > 0:
                    self.npc_manager.enemy_health = save_data['enemy_health']
                self.coins = save_data['coins']
                self.ether_crystals = save_data.get('ether_crystals', 0)  # Совместимость со старыми сохранениями
                self.moves_left = save_data['moves_left']
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if save_data['grid'][y][x]:
                            gem_data = save_data['grid'][y][x]
                            self.grid[y][x] = Gem(x, y, gem_data['type'])
                            self.grid[y][x].level = gem_data['level']
                self.gem_progress = save_data.get('gem_progress', {gem_type: {'level': 1, 'xp': 0, 'damage': 10, 'crit_chance': 0.05, 'crit_multiplier': 1.5, 'evolution': 0, 'evolved_bonus': None} for gem_type in GEM_TYPES})
                self.npc_manager.total_level = save_data.get('npc_total_level', 1)
                self.npc_manager.cycle_count = save_data.get('npc_cycle_count', 0)
                
                # Загружаем побежденных боссов
                self.defeated_bosses = set(save_data.get('defeated_bosses', []))
                
                # Загружаем инвентарь
                self.inventory = save_data.get('inventory', [])
                self.active_bonuses = save_data.get('active_bonuses', [])
                
                npc_image = save_data.get('npc_current_image')
                if npc_image:
                    for npc in self.npc_manager.npc_list:
                        if npc['image'] == npc_image:
                            self.npc_manager.current_npc = npc.copy()
                            total_level = self.npc_manager.total_level
                            stage = (total_level - 1) // 10 + 1
                            local_level = (total_level - 1) % 10 + 1
                            is_boss = (local_level == 10)
                            self.npc_manager.current_npc['max_health'] = self.npc_manager.get_scaled_health(stage, is_boss, self.npc_manager.cycle_count)
                            break
                    else:
                        self.npc_manager.current_npc = self.npc_manager._get_npc()
                else:
                    self.npc_manager.current_npc = self.npc_manager._get_npc()
                self.npc_manager.ENEMY_MAX_HEALTH = self.npc_manager.current_npc['max_health']
                self.npc_manager.npc_image = self.npc_manager._load_npc_image(self.npc_manager.current_npc['image'])
        except FileNotFoundError:
            print("Сохранение не найдено, начинаем новую игру")
        except Exception as e:
            print(f"Ошибка при загрузке сохранения: {e}")
            print("Начинаем новую игру")

    def start_new_game(self):
        # Сбрасываем все прогрессии гемов на начальный уровень
        for gem_type in GEM_TYPES:
            self.gem_progress[gem_type] = {
                'level': 1,
                'xp': 0,
                'damage': 10,
                'crit_chance': 0.05,
                'crit_multiplier': 1.5,
                'evolution': 0,
                'evolved_bonus': None
            }
        
        # Сбрасываем уровень на начальный
        self.global_level = 1
        self.location_panel.set_level(1)
        
        # Сбрасываем побежденных боссов
        self.defeated_bosses = set()
        
        # Сбрасываем NPC на первого врага
        total_level = 1
        self.npc_manager.total_level = total_level
        self.npc_manager.cycle_count = 0
        self.npc_manager.current_npc = self.npc_manager._get_npc()
        base_hp = 100
        hp = int(base_hp * (1.15 ** (self.global_level-1)))
        self.npc_manager.ENEMY_MAX_HEALTH = hp
        self.npc_manager.enemy_health = hp
        self.npc_manager.npc_image = self.npc_manager._load_npc_image(self.npc_manager.current_npc['image'])
        
        # Сбрасываем игровые ресурсы
        self.coins = 0
        self.ether_crystals = 0
        self.moves_left = 50
        self.player_hp = 100  # Устанавливаем начальное здоровье игрока
        
        # Очищаем и добавляем начальные предметы в инвентарь
        self.inventory = []
        self.active_bonuses = []
        
        # Добавляем стартовые предметы
        self.add_to_inventory({'type': 'health_potion', 'count': 2})
        self.add_to_inventory({'type': 'damage_potion', 'count': 1})
        
        # Инициализируем поле заново
        self.initialize_grid()
        
        # Показываем игру
        self.main_menu.visible = False
        self.game_started = True

    def bounce(self, t):
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - 2 * (1 - t) * (1 - t)

    def run(self):
        print("Запуск игрового цикла...")
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            # Обновляем все анимации
            self.update_animations(dt)
            
            # Обновляем активные бонусы
            if hasattr(self, 'active_bonuses'):
                self.update_active_bonuses()

            # Проверка финальных совпадений после завершения хода
            if hasattr(self, '_final_check_timer') and not self.is_processing_matches and self.animation_complete:
                current_time = pygame.time.get_ticks()
                # Ждем 500 мс после завершения всех анимаций
                if current_time - self._final_check_timer > 500:
                    # Финальная проверка совпадений
                    final_matches = self.check_matches()
                    if final_matches:
                        # Если найдены новые совпадения - обрабатываем их
                        self.process_matches(final_matches, is_player_move=False)
                    # Удаляем таймер, чтобы не повторять проверку
                    delattr(self, '_final_check_timer')

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Получен сигнал выхода")
                    self.save_game()
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Проверяем, можно ли делать ход
                    if self.animation_complete:
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.shop.visible:
                            self.shop.close()
                        elif getattr(self, '_show_gems_info', False):
                            self._show_gems_info = False
                        elif getattr(self, '_show_map', False):
                            self._show_map = False
                        elif self.game_started and not self.main_menu.visible:
                            self.save_game()
                            self.main_menu.visible = True
                        elif self.game_started and self.main_menu.visible:
                            self.main_menu.visible = False
                        continue
                    if getattr(self, '_show_map', False):
                        continue
                    if event.key == pygame.K_m:
                        self._show_map = not self._show_map
                        continue
            # Обновляем состояние гемов только если игра начата
            if self.game_started:
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if self.grid[y][x]:
                            self.grid[y][x].update(dt)
            self.draw()
        print("Завершение работы...")
        self.save_game()
        pygame.quit()

    def draw(self):
        # Отображаем фоновое изображение
        self.screen.blit(self.background, (0, 0))
        # Если игра не начата, показываем только меню
        if not self.game_started:
            self.main_menu.draw(self.screen)
            pygame.display.flip()
            return

        # --- Якорь игрового поля ---
        field_anchor_x = GRID_OFFSET_X
        field_anchor_y = GRID_OFFSET_Y
        field_size = GRID_SIZE * CELL_SIZE
        field_rect = pygame.Rect(
            field_anchor_x,
            field_anchor_y,
            field_size + 2 * BORDER,
            field_size + 2 * BORDER
        )
        self.field_rect = field_rect
        shadow_rect = field_rect.move(8, 8)
        pygame.draw.rect(self.screen, COLORS['SHADOW'], shadow_rect, border_radius=18)
        bg_img = pygame.transform.smoothscale(self.field_bg, (field_rect.width, field_rect.height))
        self.screen.blit(bg_img, field_rect.topleft)
        overlay = pygame.Surface((field_rect.width, field_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (40, 40, 60, 120), overlay.get_rect(), border_radius=22)
        self.screen.blit(overlay, field_rect.topleft)
        grid_left = field_anchor_x + BORDER
        grid_top = field_anchor_y + BORDER
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x]:
                    shadow = pygame.Surface((CELL_SIZE-4, CELL_SIZE-4), pygame.SRCALPHA)
                    shadow.fill((0,0,0,80))
                    sx = grid_left + x * CELL_SIZE + 2
                    sy = grid_top + y * CELL_SIZE + 8
                    self.screen.blit(shadow, (sx, sy))
                    self.grid[y][x].draw(self.screen)
        grid_size_px = GRID_SIZE * CELL_SIZE
        grid_color = (255,255,255,30)
        grid_surface = pygame.Surface((grid_size_px, grid_size_px), pygame.SRCALPHA)
        for i in range(GRID_SIZE+1):
            pygame.draw.line(grid_surface, grid_color, (i*CELL_SIZE, 0), (i*CELL_SIZE, grid_size_px), 1)
            pygame.draw.line(grid_surface, grid_color, (0, i*CELL_SIZE), (grid_size_px, i*CELL_SIZE), 1)
        self.screen.blit(grid_surface, (grid_left, grid_top))
        # --- Компактная верхняя панель ---
        top_panel_h = 30
        top_panel_rect = pygame.Rect(self.field_rect.left, self.field_rect.top - top_panel_h - 5, self.field_rect.width, top_panel_h)
        border_radius_top = 12
        pygame.draw.rect(self.screen, (0,0,0,80), top_panel_rect.move(0, 3), border_radius=border_radius_top)
        top_panel_surface = pygame.Surface((top_panel_rect.width, top_panel_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(top_panel_surface, (40, 40, 60, 210), top_panel_surface.get_rect(), border_radius=border_radius_top)
        grad = pygame.Surface((top_panel_rect.width, 15), pygame.SRCALPHA)
        for i in range(15):
            alpha = max(0, 100 - i*6)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,top_panel_rect.width,1))
        grad_mask = pygame.Surface((top_panel_rect.width, 15), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=border_radius_top)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        top_panel_surface.blit(grad, (0,0))
        self.screen.blit(top_panel_surface, top_panel_rect.topleft)
        
        # --- Значок ходов ---
        moves_icon = pygame.Surface((18,18), pygame.SRCALPHA)
        pygame.draw.circle(moves_icon, (180,180,255), (9,9), 9)
        pygame.draw.circle(moves_icon, (255,255,255,80), (9,9), 9, 2)
        self.screen.blit(moves_icon, (top_panel_rect.left+8, top_panel_rect.top+6))
        font = pygame.font.Font(None, 24)
        moves_text = font.render(f"{self.moves_left}", True, COLORS['WHITE'])
        self.screen.blit(moves_text, (top_panel_rect.left+30, top_panel_rect.top+4))
        
        # --- Значок монет ---
        coin_icon = pygame.Surface((18,18), pygame.SRCALPHA)
        pygame.draw.circle(coin_icon, COLORS['GOLD'], (9,9), 9)
        pygame.draw.circle(coin_icon, (255,255,255,80), (9,9), 9, 2)
        self.screen.blit(coin_icon, (top_panel_rect.left+70, top_panel_rect.top+6))
        coins_text = font.render(f"{self.coins}", True, COLORS['GOLD'])
        self.screen.blit(coins_text, (top_panel_rect.left+92, top_panel_rect.top+4))
        
        # --- Значок эфирных кристаллов ---
        crystal_icon = pygame.Surface((18,18), pygame.SRCALPHA)
        pygame.draw.circle(crystal_icon, (120, 200, 255), (9,9), 9)  # Голубой цвет для кристаллов
        pygame.draw.circle(crystal_icon, (255,255,255,80), (9,9), 9, 2)
        self.screen.blit(crystal_icon, (top_panel_rect.left+140, top_panel_rect.top+6))
        crystal_text = font.render(f"{self.ether_crystals}", True, (120, 200, 255))
        self.screen.blit(crystal_text, (top_panel_rect.left+162, top_panel_rect.top+4))
        
        # --- Уровень ---
        total_level = getattr(self.npc_manager, 'total_level', 1)
        stage = (total_level - 1) // 10 + 1
        local_level = (total_level - 1) % 10 + 1
        level_text = f"{stage}-{local_level}"
        is_boss = (local_level == 10)
        level_font = pygame.font.Font(None, 28)
        level_color = COLORS['GOLD'] if is_boss else COLORS['WHITE']
        level_label = level_font.render(level_text, True, level_color)
        level_x = top_panel_rect.right - level_label.get_width() - 170
        level_y = top_panel_rect.top + 4
        self.screen.blit(level_label, (level_x, level_y))
        if is_boss:
            boss_font = pygame.font.Font(None, 20)
            boss_text = boss_font.render("БОСС", True, COLORS['RED'])
            self.screen.blit(boss_text, (level_x + level_label.get_width()//2 - boss_text.get_width()//2, level_y + level_label.get_height() + 2))
            
        # --- Полоска HP врага ---
        enemy_hp_bar_w, enemy_hp_bar_h = 220, 22
        # Фиксированная позиция полоски HP под NPC: центрируем относительно области NPC
        npc_area_x = field_rect.right + 70
        npc_area_y = self.hud_y + 20
        npc_area_w = 220  # ширина области NPC (фиксированная)
        npc_area_h = self.hud_height - 40

        # --- Панель локаций над врагом (была перемещена на место полоски HP) ---
        loc_panel_w = 250
        enemy_hp_bar_x = npc_area_x + (npc_area_w - enemy_hp_bar_w) // 2
        panel_x = npc_area_x + (npc_area_w - loc_panel_w) // 2
        panel_y = npc_area_y + npc_area_h + 16
        self.location_panel.draw(self.screen, panel_x, panel_y)

        # Определяем позицию полоски HP врага (перемещена на верхнюю панель)
        right_gap = (WINDOW_WIDTH - top_panel_rect.right)
        enemy_hp_bar_x = top_panel_rect.right + (right_gap - enemy_hp_bar_w) // 2
        enemy_hp_bar_y = top_panel_rect.top + 10 # Добавлен отступ 10px

        small_font = pygame.font.Font(None, 26)
        # --- Новый стиль полоски HP ---
        BAR_BG = (25, 30, 50, 230)
        BAR_BORDER = (180,180,200,40)
        BAR_RADIUS = 16
        # Тень
        shadow_rect = pygame.Rect(enemy_hp_bar_x-4, enemy_hp_bar_y-4, enemy_hp_bar_w+8, enemy_hp_bar_h+8)
        pygame.draw.rect(self.screen, (15,20,35,120), shadow_rect, border_radius=BAR_RADIUS)
        # Фон полоски
        bar_surf = pygame.Surface((enemy_hp_bar_w, enemy_hp_bar_h), pygame.SRCALPHA)
        pygame.draw.rect(bar_surf, BAR_BG, bar_surf.get_rect(), border_radius=BAR_RADIUS)
        # Градиент
        grad = pygame.Surface((enemy_hp_bar_w, enemy_hp_bar_h), pygame.SRCALPHA)
        for i in range(enemy_hp_bar_h//2):
            alpha = max(0, 40 - i*3)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,enemy_hp_bar_w,1))
        grad_mask = pygame.Surface((enemy_hp_bar_w, enemy_hp_bar_h), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=BAR_RADIUS)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        bar_surf.blit(grad, (0,0))
        # Прозрачная рамка
        pygame.draw.rect(bar_surf, BAR_BORDER, bar_surf.get_rect(), 2, border_radius=BAR_RADIUS)
        self.screen.blit(bar_surf, (enemy_hp_bar_x, enemy_hp_bar_y))
        # Заполнение полоски
        hp_perc = self.npc_manager.enemy_health / self.npc_manager.ENEMY_MAX_HEALTH
        prev_perc = getattr(self, '_prev_hp_perc', hp_perc)
        anim_perc = prev_perc + (hp_perc - prev_perc) * 0.2
        self._prev_hp_perc = anim_perc
        fill_w = int(enemy_hp_bar_w * anim_perc)
        fill_surf = pygame.Surface((enemy_hp_bar_w, enemy_hp_bar_h), pygame.SRCALPHA)

        # Создаем градиент от голубого к красному для полосы здоровья
        if fill_w > 0:
            # Создаем градиент от голубого к красному (с более темными оттенками)
            colors = [(40, 120, 200), (70, 80, 180), (100, 60, 180), (160, 40, 120), (200, 30, 30)]
            segment_width = enemy_hp_bar_w / (len(colors) - 1)
            
            for i in range(len(colors) - 1):
                start_color = colors[i]
                end_color = colors[i + 1]
                start_x = int(i * segment_width)
                end_x = int((i + 1) * segment_width)
                segment_length = end_x - start_x
                
                for j in range(min(segment_length, max(0, fill_w - start_x))):
                    if start_x + j >= fill_w:
                        break
                        
                    # Интерполяция цвета
                    t = j / segment_length
                    r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
                    g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
                    b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
                    
                    pygame.draw.line(fill_surf, (r, g, b), (start_x + j, 0), (start_x + j, enemy_hp_bar_h), 1)

            # Добавляем мягкое свечение по всей полосе (уменьшенное)
            pygame.draw.rect(fill_surf, (255, 255, 255, 30), (0, 0, fill_w, 3))
            
            # Добавляем белые точки/звезды для космического эффекта (меньше и реже)
            for _ in range(fill_w // 30):
                star_x = random.randint(0, fill_w - 1)
                star_y = random.randint(0, enemy_hp_bar_h - 1)
                star_size = random.randint(1, 1)
                star_alpha = random.randint(100, 180)
                pygame.draw.circle(fill_surf, (255, 255, 255, star_alpha), (star_x, star_y), star_size)
            
            # Создаем маску для скругления углов заполнения
            mask = pygame.Surface((enemy_hp_bar_w, enemy_hp_bar_h), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=BAR_RADIUS)
            fill_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        self.screen.blit(fill_surf, (enemy_hp_bar_x, enemy_hp_bar_y))
        # Мягкое свечение (уменьшенное)
        glow = pygame.Surface((enemy_hp_bar_w+10, enemy_hp_bar_h+10), pygame.SRCALPHA)
        glow_color = (60, 100, 180, 12)
        pygame.draw.rect(glow, glow_color, glow.get_rect(), border_radius=BAR_RADIUS+2)
        self.screen.blit(glow, (enemy_hp_bar_x-5, enemy_hp_bar_y-5), special_flags=pygame.BLEND_RGBA_ADD)
        # Текст HP с тенью
        hp_text = small_font.render(f"{int(self.npc_manager.enemy_health)}/{self.npc_manager.ENEMY_MAX_HEALTH}", True, (30,30,30))
        hp_text_shadow = small_font.render(f"{int(self.npc_manager.enemy_health)}/{self.npc_manager.ENEMY_MAX_HEALTH}", True, (255,255,255))
        text_x = enemy_hp_bar_x+enemy_hp_bar_w//2-hp_text.get_width()//2
        text_y = enemy_hp_bar_y+enemy_hp_bar_h//2-hp_text.get_height()//2
        self.screen.blit(hp_text_shadow, (text_x+1, text_y+1))
        self.screen.blit(hp_text, (text_x, text_y))
        
        # --- Панель инвентаря (с отступом таким же, как верхняя панель) ---
        inventory_h = 60
        inventory_rect = pygame.Rect(self.field_rect.left, self.field_rect.bottom + 5, self.field_rect.width, inventory_h)
        
        # Тень
        shadow_rect = inventory_rect.move(4, 4)
        pygame.draw.rect(self.screen, (0,0,0,80), shadow_rect, border_radius=16)
        
        # Фон панели
        inventory_surface = pygame.Surface((inventory_rect.width, inventory_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(inventory_surface, (40, 40, 60, 230), inventory_surface.get_rect(), border_radius=16)
        
        # Градиент
        grad = pygame.Surface((inventory_rect.width, inventory_rect.height//2), pygame.SRCALPHA)
        for i in range(inventory_rect.height//2):
            alpha = max(0, 80 - i*4)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,inventory_rect.width,1))
        grad_mask = pygame.Surface((inventory_rect.width, inventory_rect.height//2), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=16)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        inventory_surface.blit(grad, (0,0))
        
        # Рамка
        pygame.draw.rect(inventory_surface, (255,255,255,60), inventory_surface.get_rect(), 2, border_radius=16)
        
        self.screen.blit(inventory_surface, inventory_rect.topleft)
        
        # Кнопки перелистывания инвентаря вместо заголовка
        button_size = 43  # Размер кнопки (увеличен на 20%)
        
        # Кнопка влево
        left_button_x = inventory_rect.left + 15
        left_button_y = inventory_rect.top + (inventory_rect.height - button_size) // 2
        left_button_rect = pygame.Rect(left_button_x, left_button_y, button_size, button_size)
        
        # Кнопка вправо
        right_button_x = inventory_rect.right - button_size - 15
        right_button_y = left_button_y
        right_button_rect = pygame.Rect(right_button_x, right_button_y, button_size, button_size)
        
        # Сохраняем прямоугольники кнопок для обработки кликов
        self._inventory_left_button = left_button_rect
        self._inventory_right_button = right_button_rect
        
        # Вычисляем количество элементов в каждом направлении
        start_idx = self.inventory_page * self.items_per_page
        # Сколько элементов слева (на предыдущих страницах)
        items_left = start_idx
        # Сколько элементов справа (на следующих страницах)
        items_right = max(0, len(self.inventory) - (start_idx + self.items_per_page))
        
        # Отрисовка кнопок
        if self.inventory_button:
            # Кнопка влево (отражаем по горизонтали)
            left_button = pygame.transform.flip(self.inventory_button, True, False)
            left_button = pygame.transform.scale(left_button, (button_size, button_size))
            self.screen.blit(left_button, left_button_rect.topleft)
            
            # Кнопка вправо
            right_button = pygame.transform.scale(self.inventory_button, (button_size, button_size))
            self.screen.blit(right_button, right_button_rect.topleft)
        else:
            # Если изображение не найдено, рисуем простые стрелки
            pygame.draw.rect(self.screen, (60, 60, 90), left_button_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255,255,255,40), left_button_rect, 2, border_radius=8)
            
            pygame.draw.rect(self.screen, (60, 60, 90), right_button_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255,255,255,40), right_button_rect, 2, border_radius=8)
            
            # Рисуем стрелки
            arrow_font = pygame.font.Font(None, 30)
            left_arrow = arrow_font.render("←", True, COLORS['WHITE'])
            right_arrow = arrow_font.render("→", True, COLORS['WHITE'])
            
            self.screen.blit(left_arrow, (left_button_x + (button_size - left_arrow.get_width()) // 2, 
                                         left_button_y + (button_size - left_arrow.get_height()) // 2))
            self.screen.blit(right_arrow, (right_button_x + (button_size - right_arrow.get_width()) // 2, 
                                          right_button_y + (button_size - right_arrow.get_height()) // 2))
        
        # Добавляем текст с количеством элементов на кнопках
        count_font = pygame.font.Font(None, 20)
        
        # Отображаем текст только если есть элементы в соответствующем направлении
        if items_left > 0:
            left_count_text = count_font.render(f"{items_left}", True, COLORS['WHITE'])
            count_bg = pygame.Surface((left_count_text.get_width() + 10, 20), pygame.SRCALPHA)
            pygame.draw.rect(count_bg, (0, 0, 0, 150), count_bg.get_rect(), border_radius=10)
            count_bg.blit(left_count_text, ((count_bg.get_width() - left_count_text.get_width()) // 2, 
                                          (count_bg.get_height() - left_count_text.get_height()) // 2))
            
            # Размещаем текст в правом верхнем углу кнопки
            self.screen.blit(count_bg, (left_button_x + button_size - count_bg.get_width(), 
                                      left_button_y))
        
        if items_right > 0:
            right_count_text = count_font.render(f"{items_right}", True, COLORS['WHITE'])
            count_bg = pygame.Surface((right_count_text.get_width() + 10, 20), pygame.SRCALPHA)
            pygame.draw.rect(count_bg, (0, 0, 0, 150), count_bg.get_rect(), border_radius=10)
            count_bg.blit(right_count_text, ((count_bg.get_width() - right_count_text.get_width()) // 2, 
                                           (count_bg.get_height() - right_count_text.get_height()) // 2))
            
            # Размещаем текст в левом верхнем углу кнопки
            self.screen.blit(count_bg, (right_button_x, right_button_y))
        
        # Слоты инвентаря
        slot_size = 40
        slot_margin = 10
        start_x = inventory_rect.left + (inventory_rect.width - (slot_size+slot_margin)*self.items_per_page + slot_margin) // 2
        slot_y = inventory_rect.top + (inventory_rect.height - slot_size) // 2 + 5
        
        # Сохраняем прямоугольники слотов для обработки кликов
        self._inventory_slot_rects = []
        
        # Определяем начальный и конечный индекс предметов для текущей страницы
        start_idx = self.inventory_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.inventory))
        
        # Отрисовываем все слоты страницы
        for i in range(self.items_per_page):
            slot_x = start_x + i * (slot_size + slot_margin)
            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            
            # Тень слота
            pygame.draw.rect(self.screen, (0,0,0,80), slot_rect.move(2, 2), border_radius=8)
            
            # Фон слота
            pygame.draw.rect(self.screen, (60, 60, 90), slot_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255,255,255,40), slot_rect, 2, border_radius=8)
            
            # Если в слоте есть предмет для данной страницы, отрисовываем его
            item_idx = start_idx + i
            if item_idx < end_idx:
                item = self.inventory[item_idx]
                # Определяем цвет иконки в зависимости от типа предмета
                item_icon = pygame.Surface((slot_size-10, slot_size-10), pygame.SRCALPHA)
                if item['type'] == 'damage_potion':
                    item_color = (255, 100, 100)  # Красный для зелья урона
                elif item['type'] == 'crit_potion':
                    item_color = (255, 100, 255)  # Розовый для зелья крита
                elif item['type'] == 'health_potion':
                    item_color = (100, 255, 100)  # Зеленый для зелья здоровья
                else:
                    item_color = (200, 200, 200)  # Серый для прочих предметов
                
                pygame.draw.rect(item_icon, item_color, item_icon.get_rect(), border_radius=6)
                
                # Добавляем блик
                highlight = pygame.Surface((slot_size-10, (slot_size-10)//2), pygame.SRCALPHA)
                for j in range((slot_size-10)//2):
                    alpha = max(0, 120 - j*8)
                    pygame.draw.rect(highlight, (255,255,255,alpha), (0,j,slot_size-10,1))
                highlight_mask = pygame.Surface((slot_size-10, (slot_size-10)//2), pygame.SRCALPHA)
                pygame.draw.rect(highlight_mask, (255,255,255), highlight_mask.get_rect(), border_radius=6)
                highlight.blit(highlight_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
                item_icon.blit(highlight, (0,0))
                
                self.screen.blit(item_icon, (slot_x+5, slot_y+5))
                
                # Если у предмета есть количество, показываем его
                if 'count' in item and item['count'] > 1:
                    count_font = pygame.font.Font(None, 20)
                    count_text = count_font.render(f"{item['count']}", True, COLORS['WHITE'])
                    self.screen.blit(count_text, (slot_x + slot_size - count_text.get_width() - 3, 
                                                  slot_y + slot_size - count_text.get_height() - 3))
            
            # Сохраняем прямоугольник для обработки кликов вместе с индексом предмета
            self._inventory_slot_rects.append((slot_rect, start_idx + i))
        
        # Отображаем активные бонусы
        if self.active_bonuses:
            bonus_font = pygame.font.Font(None, 20)
            bonus_y = inventory_rect.top + 8
            bonus_x = inventory_rect.right - 20
            
            # Обновляем бонусы перед отрисовкой
            self.update_active_bonuses()
            
            for i, bonus in enumerate(self.active_bonuses):
                move_duration = 5000  # Примерно 5 секунд на ход
                current_time = pygame.time.get_ticks()
                elapsed_moves = (current_time - bonus['start_time']) / move_duration
                moves_left = max(0, bonus['duration'] - elapsed_moves)
                
                if bonus['type'] == 'damage_bonus':
                    bonus_text = f"+{int(bonus['value']*100)}% урон"
                    bonus_color = (255, 100, 100)
                elif bonus['type'] == 'crit_chance_bonus':
                    bonus_text = f"+{int(bonus['value']*100)}% крит"
                    bonus_color = (255, 100, 255)
                else:
                    bonus_text = f"Бонус: {bonus['type']}"
                    bonus_color = (200, 200, 200)
                
                # Добавляем время действия
                bonus_text += f" ({int(moves_left)} ходов)"
                
                # Создаем текст и определяем его ширину
                bonus_label = bonus_font.render(bonus_text, True, bonus_color)
                bonus_width = bonus_label.get_width() + 10
                
                # Рисуем фон с закругленными краями
                bonus_bg_rect = pygame.Rect(bonus_x - bonus_width, bonus_y + i*22, bonus_width, 20)
                pygame.draw.rect(self.screen, (50, 50, 70, 180), bonus_bg_rect, border_radius=10)
                pygame.draw.rect(self.screen, bonus_color, bonus_bg_rect, 1, border_radius=10)
                
                # Рисуем текст
                self.screen.blit(bonus_label, (bonus_x - bonus_width + 5, bonus_y + i*22 + 2))
          
        # --- Полоса здоровья игрока (под инвентарём с отступом 30px) ---
        # Временно скрыта
        """
        player_hp_max = 100
        player_hp = getattr(self, 'player_hp', player_hp_max)
        hp_bar_w, hp_bar_h = field_rect.width - 40, 28
        hp_bar_x = field_rect.left + 20
        hp_bar_y = inventory_rect.bottom + 30  # 30px отступ от инвентаря
        
        # Рисуем фон и обводку
        pygame.draw.rect(self.screen, (30,30,30), (hp_bar_x-2, hp_bar_y-2, hp_bar_w+4, hp_bar_h+4), border_radius=12)
        pygame.draw.rect(self.screen, (40, 50, 80, 210), (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h), border_radius=10)
        
        # Рассчитываем заполнение полосы
        hp_perc = player_hp / player_hp_max
        fill_w = int(hp_bar_w * hp_perc)
        
        # Создаем поверхность для заполнения
        fill_surf = pygame.Surface((hp_bar_w, hp_bar_h), pygame.SRCALPHA)
        
        # Создаем градиент от голубого к красному
        if fill_w > 0:
            colors = [(60, 170, 255), (100, 120, 255), (140, 80, 255), (220, 60, 160), (255, 40, 40)]
            segment_width = hp_bar_w / (len(colors) - 1)
            
            for i in range(len(colors) - 1):
                start_color = colors[i]
                end_color = colors[i + 1]
                start_x = int(i * segment_width)
                end_x = int((i + 1) * segment_width)
                segment_length = end_x - start_x
                
                for j in range(min(segment_length, max(0, fill_w - start_x))):
                    if start_x + j >= fill_w:
                        break
                        
                    # Интерполяция цвета
                    t = j / segment_length
                    r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
                    g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
                    b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
                    
                    pygame.draw.line(fill_surf, (r, g, b), (start_x + j, 0), (start_x + j, hp_bar_h), 1)
            
            # Добавляем мягкое свечение по верхнему краю
            pygame.draw.rect(fill_surf, (255, 255, 255, 60), (0, 0, fill_w, 5))
            
            # Добавляем белые точки/звезды для космического эффекта
            for _ in range(fill_w // 15):
                star_x = random.randint(0, fill_w - 1)
                star_y = random.randint(0, hp_bar_h - 1)
                star_size = random.randint(1, 2)
                star_alpha = random.randint(150, 255)
                pygame.draw.circle(fill_surf, (255, 255, 255, star_alpha), (star_x, star_y), star_size)
            
            # Создаем маску для скругления углов заполнения
            mask = pygame.Surface((hp_bar_w, hp_bar_h), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=10)
            fill_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        # Накладываем заполнение
        self.screen.blit(fill_surf, (hp_bar_x, hp_bar_y))
        
        # Добавляем свечение
        glow = pygame.Surface((hp_bar_w+20, hp_bar_h+20), pygame.SRCALPHA)
        glow_color = (100, 150, 255, 24)
        pygame.draw.rect(glow, glow_color, glow.get_rect(), border_radius=16)
        self.screen.blit(glow, (hp_bar_x-10, hp_bar_y-10), special_flags=pygame.BLEND_RGBA_ADD)
        
        # Рисуем обводку
        pygame.draw.rect(self.screen, (255,255,255,80), (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h), 2, border_radius=10)
        
        # Текст HP
        hp_text = font.render(f"HP игрока: {player_hp}/{player_hp_max}", True, COLORS['WHITE'])
        self.screen.blit(hp_text, (hp_bar_x+hp_bar_w//2-hp_text.get_width()//2, hp_bar_y+hp_bar_h//2-hp_text.get_height()//2))
        """
                
        # Обновляем позицию кнопок ниже полосы здоровья игрока
        btn_y = inventory_rect.bottom + 30  # Размещаем кнопки сразу под инвентарём
        btn_w, btn_h = 160, 48
        btn_gap = 18
        total_w = btn_w * 3 + btn_gap * 2
        start_x = field_rect.left + (field_rect.width - total_w) // 2
        shop_button = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        shop_surface = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        pygame.draw.rect(shop_surface, (60, 60, 90, 220), shop_surface.get_rect(), border_radius=16)
        grad = pygame.Surface((btn_w, btn_h//2), pygame.SRCALPHA)
        for i in range(btn_h//2):
            alpha = max(0, 80 - i*3)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,btn_w,1))
        grad_mask = pygame.Surface((btn_w, btn_h//2), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=16)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        shop_surface.blit(grad, (0,0))
        shop_font = pygame.font.Font(None, 36)
        shop_text = shop_font.render("Магазин", True, COLORS['WHITE'])
        shop_surface.blit(shop_text, (btn_w//2 - shop_text.get_width()//2, btn_h//2 - shop_text.get_height()//2))
        self.screen.blit(shop_surface, (start_x, btn_y))
        self._shop_button_rect = shop_button
        gems_x = start_x + btn_w + btn_gap
        gems_button = pygame.Rect(gems_x, btn_y, btn_w, btn_h)
        gems_surface = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        pygame.draw.rect(gems_surface, (60, 60, 90, 220), gems_surface.get_rect(), border_radius=16)
        grad = pygame.Surface((btn_w, btn_h//2), pygame.SRCALPHA)
        for i in range(btn_h//2):
            alpha = max(0, 80 - i*3)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,btn_w,1))
        grad_mask = pygame.Surface((btn_w, btn_h//2), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=16)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        gems_surface.blit(grad, (0,0))
        gems_font = pygame.font.Font(None, 36)
        gems_text = gems_font.render("Гемы", True, COLORS['WHITE'])
        gems_surface.blit(gems_text, (btn_w//2 - gems_text.get_width()//2, btn_h//2 - gems_text.get_height()//2))
        self.screen.blit(gems_surface, (gems_x, btn_y))
        self._gems_button_rect = gems_button
        map_x = gems_x + btn_w + btn_gap
        map_button = pygame.Rect(map_x, btn_y, btn_w, btn_h)
        map_surface = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        pygame.draw.rect(map_surface, (60, 60, 90, 220), map_surface.get_rect(), border_radius=16)
        grad = pygame.Surface((btn_w, btn_h//2), pygame.SRCALPHA)
        for i in range(btn_h//2):
            alpha = max(0, 80 - i*3)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,btn_w,1))
        grad_mask = pygame.Surface((btn_w, btn_h//2), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=16)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        map_surface.blit(grad, (0,0))
        map_font = pygame.font.Font(None, 36)
        map_text = map_font.render("Карта (M)", True, COLORS['WHITE'])
        map_surface.blit(map_text, (btn_w//2 - map_text.get_width()//2, btn_h//2 - map_text.get_height()//2))
        self.screen.blit(map_surface, (map_x, btn_y))
        self._map_button_rect = map_button
        shake = self.npc_manager.get_shake_offset()
        # Центрируем NPC по области
        npc_img = self.npc_manager.npc_image
        npc_x = npc_area_x + (npc_area_w - npc_img.get_width()) // 2 + shake
        npc_y = npc_area_y + (npc_area_h - npc_img.get_height()) // 2
        self.screen.blit(npc_img, (npc_x, npc_y))
        # Очередь popup-уронов
        now = pygame.time.get_ticks()
        new_popups = []
        for popup in self.damage_popups:
            elapsed = now - popup['start_time']
            if elapsed < 0:
                new_popups.append(popup)
                continue
            if elapsed > 1000:
                continue
            font = pygame.font.Font(None, 48)
            value = f"-{popup['value']}"
            color = popup['color']
            # Тень
            dmg_text_shadow = font.render(value, True, (0,0,0))
            dmg_text = font.render(value, True, color)
            # Пульсация для крита
            pulse = 1.0
            if popup['is_crit']:
                pulse = 1 + 0.18 * math.sin(elapsed * 0.018)
                dmg_text = pygame.transform.scale(dmg_text, (int(dmg_text.get_width()*pulse), int(dmg_text.get_height()*pulse)))
                dmg_text_shadow = pygame.transform.scale(dmg_text_shadow, (int(dmg_text_shadow.get_width()*pulse), int(dmg_text_shadow.get_height()*pulse)))
            # Позиция
            text_x = npc_area_x + npc_area_w // 2 - dmg_text.get_width() // 2
            base_y = npc_y + npc_img.get_height() // 2 + 20
            text_y = base_y - int(40 * (elapsed / 1000)) - 32 * self.damage_popups.index(popup)
            # Тень
            self.screen.blit(dmg_text_shadow, (text_x + 2, text_y + 2))
            # Основной текст
            self.screen.blit(dmg_text, (text_x, text_y))
            new_popups.append(popup)
        # Удаляем старые popup'ы
        self.damage_popups = [p for p in new_popups if now - p['start_time'] < 1000]
        if self.shop.visible:
            self.shop.draw(self.screen)
        if getattr(self, '_show_gems_info', False):
            self._show_gems_info_screen()
        if self.main_menu.visible:
            self.main_menu.draw(self.screen)
        pygame.display.flip() 

    def handle_click(self, pos):
        # --- Сначала проверяем клики по основным кнопкам ---
        if hasattr(self, '_shop_button_rect') and self._shop_button_rect.collidepoint(pos):
            self.shop.toggle_visibility()
            return
        if hasattr(self, '_gems_button_rect') and self._gems_button_rect.collidepoint(pos):
            self._show_gems_info = True
            return
        if hasattr(self, '_map_button_rect') and self._map_button_rect.collidepoint(pos):
            self._show_map = True
            return
            
        # --- Проверка кликов по кнопкам перелистывания инвентаря ---
        if hasattr(self, '_inventory_left_button') and self._inventory_left_button.collidepoint(pos):
            if self.inventory_page > 0:
                self.inventory_page -= 1
            return
            
        if hasattr(self, '_inventory_right_button') and self._inventory_right_button.collidepoint(pos):
            total_pages = (len(self.inventory) + self.items_per_page - 1) // self.items_per_page
            if self.inventory_page < total_pages - 1:
                self.inventory_page += 1
            return
            
        # --- Проверка кликов по слотам инвентаря ---
        if hasattr(self, '_inventory_slot_rects'):
            for slot_rect, item_idx in self._inventory_slot_rects:
                if slot_rect.collidepoint(pos) and item_idx < len(self.inventory):
                    # Активируем предмет в слоте
                    self.use_item(item_idx)
                    return
                    
        # --- Проверка клика по панели локаций ---
        action = self.location_panel.handle_click(pos)
        if action == 'left':
            self.location_panel.move_left()
            self.global_level = self.location_panel.current_global_level
            self._on_location_change()
            return
        elif action == 'right':
            self.location_panel.move_right()
            self.global_level = self.location_panel.current_global_level
            self._on_location_change()
            return
        elif isinstance(action, int):
            self.location_panel.set_level(action)
            self.global_level = self.location_panel.current_global_level
            self._on_location_change()
            return
        if getattr(self, '_show_gems_info', False):
            # Проверяем клик по кнопке закрытия
            if hasattr(self, '_gems_close_btn_rect') and self._gems_close_btn_rect.collidepoint(pos):
                self._show_gems_info = False
                return
                
            # Проверяем клики по кнопкам эволюции
            if hasattr(self, '_gem_evolution_buttons'):
                for gem_type, btn_rect, can_evolve in self._gem_evolution_buttons:
                    if btn_rect.collidepoint(pos) and can_evolve:
                        self.evolve_gem(gem_type)
                        # Обновляем информацию о гемах
                        return
            return
        if self.shop.visible:
            self.shop.handle_click(pos)
            return
        if self.main_menu.visible:
            action = self.main_menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': pos}))
            if action:
                self.handle_menu_action(action)
            return
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] and (self.grid[y][x].is_moving or self.grid[y][x].is_returning):
                    return
        if getattr(self, '_show_map', False):
            # Можно добавить обработку кликов по планетам
            # planet = self.solar_system_map.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': pos, 'button': 1}))
            # if planet:
            #     print(f"Выбрана планета: {planet.name}")
            return
        x = (pos[0] - FIELD_OFFSET_X) // CELL_SIZE
        y = (pos[1] - FIELD_OFFSET_Y) // CELL_SIZE
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            # Проверяем, что в ячейке есть гем и нет активных анимаций
            if not self.grid[y][x] or not self.animation_complete:
                return

            if self.selected_gem is None:
                self.selected_gem = (x, y)
                self.grid[y][x].is_selected = True
            else:
                if self.is_adjacent(self.selected_gem, (x, y)):
                    self.swap_gems(self.selected_gem, (x, y))
                    matches = self.check_matches()
                    if matches:
                        self.process_matches(matches)
                        for row in self.grid:
                            for gem in row:
                                if gem:
                                    gem.is_selected = False
                        self.selected_gem = None
                        
                        # Запускаем таймер для финальной проверки совпадений
                        self._final_check_timer = pygame.time.get_ticks()
                    else:
                        self.swap_gems(self.selected_gem, (x, y))
                        if self.grid[y][x]:
                            self.grid[y][x].start_shake()
                        if self.grid[self.selected_gem[1]][self.selected_gem[0]]:
                            self.grid[self.selected_gem[1]][self.selected_gem[0]].start_shake()
                        self.grid[self.selected_gem[1]][self.selected_gem[0]].is_selected = False
                        self.selected_gem = None
                else:
                    self.grid[self.selected_gem[1]][self.selected_gem[0]].is_selected = False
                    self.selected_gem = (x, y)
                    self.grid[y][x].is_selected = True 

    def is_adjacent(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

    def swap_gems(self, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        gem1 = self.grid[y1][x1]
        gem2 = self.grid[y2][x2]
        self.grid[y1][x1] = gem2
        self.grid[y2][x2] = gem1
        if gem1:
            gem1.x, gem1.y = x2, y2
            gem1.move_to(x2, y2)
        if gem2:
            gem2.x, gem2.y = x1, y1
            gem2.move_to(x1, y1)
        self.last_swap_target = (x2, y2)

    def check_matches(self):
        matches = []
        # Проверка горизонтальных комбинаций
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE - 2):
                if (self.grid[y][x] is not None and 
                    self.grid[y][x+1] is not None and 
                    self.grid[y][x+2] is not None and
                    self.grid[y][x].type == self.grid[y][x+1].type == self.grid[y][x+2].type):
                    matches.append([(x, y), (x+1, y), (x+2, y)])
                    
                    # Проверяем, можно ли продлить комбинацию вправо
                    if x + 3 < GRID_SIZE and self.grid[y][x+3] is not None and self.grid[y][x+3].type == self.grid[y][x].type:
                        matches[-1].append((x+3, y))
                        # Проверяем дальше
                        if x + 4 < GRID_SIZE and self.grid[y][x+4] is not None and self.grid[y][x+4].type == self.grid[y][x].type:
                            matches[-1].append((x+4, y))

        # Проверка вертикальных комбинаций
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE - 2):
                if (self.grid[y][x] is not None and 
                    self.grid[y+1][x] is not None and 
                    self.grid[y+2][x] is not None and
                    self.grid[y][x].type == self.grid[y+1][x].type == self.grid[y+2][x].type):
                    matches.append([(x, y), (x, y+1), (x, y+2)])
                    
                    # Проверяем, можно ли продлить комбинацию вниз
                    if y + 3 < GRID_SIZE and self.grid[y+3][x] is not None and self.grid[y+3][x].type == self.grid[y][x].type:
                        matches[-1].append((x, y+3))
                        # Проверяем дальше
                        if y + 4 < GRID_SIZE and self.grid[y+4][x] is not None and self.grid[y+4][x].type == self.grid[y][x].type:
                            matches[-1].append((x, y+4))
        
        return matches

    def process_matches(self, matches, is_player_move=True, accum_damage=0, is_root_call=True):
        if not matches:
            if is_root_call and accum_damage > 0:
                self.damage_popups.append({
                    'value': int(accum_damage),
                    'is_crit': getattr(self, '_was_critical', False),
                    'start_time': pygame.time.get_ticks(),
                    'color': getattr(self, '_damage_color', (255, 200, 0))
                })
            # Сбрасываем счетчик рекурсии, если это корневой вызов
            if is_root_call and hasattr(self, '_match_recursion_depth'):
                delattr(self, '_match_recursion_depth')
            return accum_damage

        # Защита от слишком глубокой рекурсии
        recursion_depth = getattr(self, '_match_recursion_depth', 0)
        if recursion_depth > 10:  # Ограничиваем максимальную глубину рекурсии
            print("Предотвращение зависания: слишком глубокая рекурсия при обработке совпадений")
            self.is_processing_matches = False
            self.animation_complete = True
            self.waiting_for_animations = False
            self.pending_matches = []
            if hasattr(self, '_match_recursion_depth'):
                delattr(self, '_match_recursion_depth')
            return accum_damage
        
        # Увеличиваем счетчик рекурсии
        self._match_recursion_depth = recursion_depth + 1

        # Если уже идет обработка комбинаций, добавляем новые в очередь
        if self.is_processing_matches and not is_root_call:
            self.pending_matches.extend(matches)
            # Уменьшаем счетчик рекурсии перед выходом
            self._match_recursion_depth = recursion_depth
            return accum_damage

        self.is_processing_matches = True
        self.waiting_for_animations = True
        self.animation_complete = False

        total_damage = 0
        critical_hits = 0
        combo_multiplier = 1.0
        active_gems = set()
        gem_type_counts = {}
        is_critical = False
        updated_gem_types = set()
        disappearing_gems = []
        
        # Обрабатываем специальные комбинации для эволюционировавших гемов
        special_match_effects = []  # Эффекты от специальных комбинаций
        
        for match in matches:
            # Проверка на длинную комбинацию (5+ гемов)
            if len(match) >= 5:
                main_gem = None
                gem_type = None
                
                # Находим один из гемов и запоминаем его тип
                for x, y in match:
                    if self.grid[y][x]:
                        main_gem = self.grid[y][x]
                        gem_type = main_gem.type
                        break
                
                if main_gem and gem_type:
                    prog = self.gem_progress[gem_type]
                    
                    # Если гем эволюционировал, активируем его особую способность
                    if prog['evolution'] > 0 and prog['evolved_bonus']:
                        bonus_type = prog['evolved_bonus']
                        # Сохраняем для дальнейшей обработки
                        special_match_effects.append({
                            'type': bonus_type,
                            'gem_type': gem_type,
                            'match': match,
                            'main_gem': main_gem
                        })
                        
                        # Добавляем визуальную индикацию срабатывания бонуса
                        self.damage_popups.append({
                            'value': f"Бонус: {bonus_type}",
                            'is_crit': True,
                            'start_time': pygame.time.get_ticks() + 100,
                            'color': (120, 255, 120)  # Зеленый цвет для бонусов
                        })

        # Собираем статистику по гемам
        for match in matches:
            for x, y in match:
                gem = self.grid[y][x]
                if gem:
                    gem_type_counts[gem.type] = gem_type_counts.get(gem.type, 0) + 1
                    active_gems.add((x, y))
                    prog = self.gem_progress[gem.type]
                    prog['xp'] += 1
                    xp_needed = int(100 * (1.2 ** (prog['level']-1)))
                    if prog['xp'] >= xp_needed:
                        prog['level'] += 1
                        prog['xp'] = 0
                        prog['damage'] = int(prog['damage'] * 1.15)
                        prog['crit_chance'] = min(0.5, prog['crit_chance'] + 0.01)
                        prog['crit_multiplier'] += 0.05
                        updated_gem_types.add(gem.type)

        # Синхронизируем все обновлённые типы гемов
        for gem_type in updated_gem_types:
            self.sync_gems_with_progress(gem_type)

        # Запускаем анимации исчезновения
        for match in matches:
            for x, y in match:
                gem = self.grid[y][x]
                if gem and not gem.is_disappearing:
                    gem.start_disappear()
                    self.animating_gems.append(gem)
                    disappearing_gems.append((x, y))

        # Обрабатываем специальные эффекты эволюционировавших гемов
        for effect in special_match_effects:
            bonus_type = effect['type']
            gem_type = effect['gem_type']
            
            # Применяем эффект в зависимости от типа бонуса
            # Примеры реализации для различных бонусов:
            
            if bonus_type == 'fire_explosion':
                # Бонус: взрыв наносит дополнительный урон
                additional_damage = self.gem_progress[gem_type]['damage'] * 3
                accum_damage += additional_damage
                
            elif bonus_type == 'ice_freeze':
                # Бонус: снижает защиту врага на несколько ходов
                # (Здесь можно добавить логику снижения защиты врага)
                pass
                
            elif bonus_type == 'poison_cloud':
                # Бонус: добавляет постепенный урон врагу
                # (Логика применения яда к врагу)
                pass
                
            elif bonus_type in ['lightning_chain', 'water_wave', 'rock_slam']:
                # Бонусы, дающие дополнительный множитель урона
                combo_multiplier += 0.5  # +50% к урону комбинации
                
            # Для более сложных бонусов можно добавить специальные эффекты

        # Сохраняем информацию для последующей обработки
        self._pending_info = {
            'disappearing_gems': disappearing_gems,
            'active_gems': active_gems,
            'is_player_move': is_player_move,
            'accum_damage': accum_damage,
            'is_root_call': is_root_call,
            'matches': matches,
            'combo_multiplier': combo_multiplier,  # Сохраняем множитель комбо
            'special_effects': special_match_effects  # Сохраняем эффекты
        }
        
        # Если это корневой вызов метода, начинаем отсчет времени анимации
        if is_root_call:
            self._animation_start_time = pygame.time.get_ticks()

        return accum_damage

    def fill_empty_cells(self):
        """Заполнение пустых клеток новыми гемами"""
        for x in range(GRID_SIZE):
            empty_cells = 0
            # Сначала сдвигаем существующие гемы вниз
            for y in range(GRID_SIZE - 1, -1, -1):
                if self.grid[y][x] is None:
                    empty_cells += 1
                elif empty_cells > 0:
                    self.grid[y + empty_cells][x] = self.grid[y][x]
                    self.grid[y][x] = None
                    gem = self.grid[y + empty_cells][x]
                    gem.y = y + empty_cells
                    gem.rect.x = FIELD_OFFSET_X + x * CELL_SIZE + 2
                    gem.rect.y = FIELD_OFFSET_Y + y * CELL_SIZE + 2
                    self.start_gem_fall(gem, y + empty_cells)

            # Затем создаем новые гемы сверху
            for y in range(empty_cells):
                new_gem = Gem(x, y)
                # Синхронизация с глобальным прогрессом
                prog = self.gem_progress[new_gem.type]
                new_gem.level = prog['level']
                new_gem.damage = prog['damage']
                new_gem.crit_chance = prog['crit_chance']
                new_gem.crit_multiplier = prog['crit_multiplier']
                
                self.grid[y][x] = new_gem
                # Устанавливаем начальную позицию над полем
                new_gem.rect.x = FIELD_OFFSET_X + x * CELL_SIZE + 2
                new_gem.rect.y = FIELD_OFFSET_Y - (empty_cells - y) * CELL_SIZE
                new_gem.y = y
                self.start_gem_fall(new_gem, y)

    def handle_menu_action(self, action):
        if action == 'new_game':
            self.start_new_game()
        elif action == 'continue':
            self.load_save()
            self.main_menu.visible = False
            self.game_started = True
        elif action == 'exit':
            self.running = False 

    def _on_location_change(self):
        # При смене уровня: сбрасываем врага, прогрессию HP и т.д.
        zone_name, lvl_in_zone, zone_idx = self.get_level_info(self.global_level)
        base_hp = 100
        hp = int(base_hp * (1.15 ** (self.global_level-1)))
        self.npc_manager.current_npc = self.npc_manager._get_npc()
        self.npc_manager.ENEMY_MAX_HEALTH = hp
        self.npc_manager.enemy_health = hp
        self.npc_manager.npc_image = self.npc_manager._load_npc_image(self.npc_manager.current_npc['image'])
        # Можно добавить смену фона/музыки/и т.д. 

    def get_level_info(self, global_level):
        # Возвращает (название зоны, номер уровня в зоне, индекс зоны)
        levels_per_zone = 10
        zone_idx = (global_level - 1) // levels_per_zone
        lvl_in_zone = (global_level - 1) % levels_per_zone + 1
        zone_name = COSMIC_ZONES[zone_idx % len(COSMIC_ZONES)]
        return zone_name, lvl_in_zone, zone_idx 

    def sync_gems_with_progress(self, gem_type=None):
        # Обновляет все гемы на поле по типу (или все, если тип не указан)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                gem = self.grid[y][x]
                if gem and (gem_type is None or gem.type == gem_type):
                    prog = self.gem_progress[gem.type]
                    gem.level = prog['level']
                    gem.damage = prog['damage']
                    gem.crit_chance = prog['crit_chance']
                    gem.crit_multiplier = prog['crit_multiplier'] 
                    
    def add_to_inventory(self, item):
        """Добавляет предмет в инвентарь"""
        # Проверяем, есть ли уже такой предмет (для складывания)
        for existing_item in self.inventory:
            if existing_item['type'] == item['type']:
                # Увеличиваем количество
                if 'count' in existing_item:
                    existing_item['count'] += item.get('count', 1)
                else:
                    existing_item['count'] = item.get('count', 1) + 1
                return True
                
        # Если предмет новый и есть свободное место
        if len(self.inventory) < self.inventory_slots:
            # Если количество не указано, задаем 1
            if 'count' not in item:
                item['count'] = 1
            self.inventory.append(item)
            return True
            
        # Если нет места в инвентаре
        return False
        
    def use_item(self, slot_index):
        """Использует предмет из указанного слота инвентаря"""
        if 0 <= slot_index < len(self.inventory):
            item = self.inventory[slot_index]
            
            # Применяем эффект предмета
            if item['type'] == 'damage_potion':
                # Временный бонус к урону
                self.active_bonuses.append({
                    'type': 'damage_bonus',
                    'value': 0.5,  # +50% к урону
                    'duration': 3,  # 3 хода
                    'start_time': pygame.time.get_ticks()
                })
                # Добавляем визуальное уведомление
                self.damage_popups.append({
                    'value': 'Бонус урона!',
                    'is_crit': True,
                    'start_time': pygame.time.get_ticks() + 100,
                    'color': (255, 100, 100)
                })
                
            elif item['type'] == 'crit_potion':
                # Временный бонус к шансу крита
                self.active_bonuses.append({
                    'type': 'crit_chance_bonus',
                    'value': 0.2,  # +20% к шансу крита
                    'duration': 3,  # 3 хода
                    'start_time': pygame.time.get_ticks()
                })
                # Добавляем визуальное уведомление
                self.damage_popups.append({
                    'value': 'Бонус крита!',
                    'is_crit': True,
                    'start_time': pygame.time.get_ticks() + 100,
                    'color': (255, 100, 255)
                })
                
            elif item['type'] == 'health_potion':
                # Восстановление здоровья
                player_hp_max = 100
                current_hp = getattr(self, 'player_hp', player_hp_max)
                heal_amount = int(player_hp_max * 0.3)  # Восстановление 30% здоровья
                new_hp = min(player_hp_max, current_hp + heal_amount)
                self.player_hp = new_hp
                
                # Добавляем визуальное уведомление
                self.damage_popups.append({
                    'value': f'+{heal_amount} HP',
                    'is_crit': False,
                    'start_time': pygame.time.get_ticks() + 100,
                    'color': (57, 255, 20)
                })
            
            # Уменьшаем количество предметов в стаке
            item['count'] -= 1
            
            # Если предметы закончились, удаляем из инвентаря
            if item['count'] <= 0:
                self.inventory.pop(slot_index)
                
            return True
                
        return False
                
    def update_active_bonuses(self):
        """Обновляет активные временные бонусы"""
        current_time = pygame.time.get_ticks()
        move_duration = 5000  # Примерно 5 секунд на ход
        
        # Фильтруем и обновляем бонусы
        updated_bonuses = []
        for bonus in self.active_bonuses:
            # Проверяем не истек ли срок действия
            elapsed_moves = (current_time - bonus['start_time']) / move_duration
            if elapsed_moves < bonus['duration']:
                updated_bonuses.append(bonus)
                
        self.active_bonuses = updated_bonuses

    def update_animations(self, dt):
        """Обновление всех анимаций"""
        if not self.is_processing_matches:
            self.animation_complete = True
            return
        
        # Добавляем защиту от бесконечной обработки
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_animation_start_time'):
            self._animation_start_time = current_time
        elif current_time - self._animation_start_time > 5000:  # 5 секунд макс
            print("Предотвращение зависания: принудительное завершение анимаций")
            self.animating_gems = []
            self.falling_gems = []
            self.is_processing_matches = False
            self.animation_complete = True
            self.waiting_for_animations = False
            self.pending_matches = []  # Очистка очереди комбинаций
            if hasattr(self, '_animation_start_time'):
                delattr(self, '_animation_start_time')
            if hasattr(self, '_pending_info'):
                delattr(self, '_pending_info')
            if hasattr(self, '_match_recursion_depth'):
                delattr(self, '_match_recursion_depth')
            return

        # Обновляем анимации исчезновения
        still_animating = []
        removed_any = False
        for gem in self.animating_gems:
            result = gem.update(dt)
            if result != 'remove':
                still_animating.append(gem)
            else:
                if self.grid[gem.y][gem.x] is gem:
                    self.grid[gem.y][gem.x] = None
                    removed_any = True
        self.animating_gems = still_animating

        # Если после исчезновения есть пустые клетки — заполняем их
        if removed_any:
            any_empty = any(self.grid[y][x] is None for y in range(GRID_SIZE) for x in range(GRID_SIZE))
            if any_empty:
                self.fill_empty_cells()

        # Обновляем анимации падения
        initial_falling_gems_count = len(self.falling_gems)
        still_falling = []
        for gem in self.falling_gems:
            if gem.update_falling(dt):
                still_falling.append(gem)
            else:
                if 0 <= gem.y < GRID_SIZE and 0 <= gem.x < GRID_SIZE:
                    self.grid[gem.y][gem.x] = gem
        
        # Определяем, закончили ли падать все гемы
        # True, когда изначально были падающие гемы и теперь их не осталось
        falling_complete = initial_falling_gems_count > 0 and len(still_falling) == 0
        self.falling_gems = still_falling

        # Если все гемы закончили падать, проверяем новые комбинации
        if falling_complete:
            # Проверяем, нет ли уже обрабатываемых комбинаций в очереди
            if not self.pending_matches:
                new_matches = self.check_matches()
                if new_matches:
                    self.pending_matches.extend(new_matches)

        # Проверяем состояние анимаций
        if self.waiting_for_animations:
            if not self.animating_gems and not self.falling_gems:
                self.waiting_for_animations = False
                # Проверяем, не слишком ли глубока рекурсия
                if getattr(self, '_match_recursion_depth', 0) <= 10:
                    self._process_pending_actions()
                # Сбрасываем таймер после обработки действий
                if hasattr(self, '_animation_start_time'):
                    delattr(self, '_animation_start_time')
        else:
            if not self.animating_gems and not self.falling_gems:
                # Последняя проверка на наличие новых комбинаций после всех анимаций
                if not self.pending_matches:
                    new_matches = self.check_matches()
                    if new_matches:
                        self.pending_matches.extend(new_matches)
                
                # Обработка отложенных комбинаций
                if self.pending_matches and getattr(self, '_match_recursion_depth', 0) <= 10:
                    matches = self.pending_matches
                    self.pending_matches = []
                    # Предотвращаем вложенный вызов обработки совпадений
                    self.process_matches(matches, is_player_move=False)
                else:
                    # Завершаем обработку, если нет новых комбинаций или достигнут лимит рекурсии
                    self.animation_complete = True
                    self.is_processing_matches = False
                    # Сбрасываем счетчик рекурсии
                    if hasattr(self, '_match_recursion_depth'):
                        delattr(self, '_match_recursion_depth')
                    # Сбрасываем таймер после завершения всех анимаций
                    if hasattr(self, '_animation_start_time'):
                        delattr(self, '_animation_start_time')

    def _process_pending_actions(self):
        """Обработка отложенных действий после завершения анимаций"""
        if not hasattr(self, '_pending_info'):
            return

        info = self._pending_info
        
        # Вычисляем урон от каждого гема в комбинациях
        total_damage = info['accum_damage']
        critical_hits = 0
        combo_multiplier = info.get('combo_multiplier', 1.0 + len(info['matches']) * 0.1)  # Бонус к урону за количество комбинаций
        
        # Применяем активные бонусы
        damage_bonus_multiplier = 1.0
        crit_chance_bonus = 0.0
        
        for bonus in self.active_bonuses:
            if bonus['type'] == 'damage_bonus':
                damage_bonus_multiplier += bonus['value']
            elif bonus['type'] == 'crit_chance_bonus':
                crit_chance_bonus += bonus['value']
        
        # Собираем урон от всех гемов в комбинациях
        for match in info['matches']:
            for x, y in match:
                if (x, y) in info['active_gems']:
                    gem = self.grid[y][x]
                    if gem:
                        # Рассчитываем урон от гема с учетом бонусов
                        base_damage = gem.damage * gem.level
                        # Проверяем крит с учетом бонуса к шансу крита
                        is_crit = random.random() < (gem.crit_chance + crit_chance_bonus)
                        if is_crit:
                            damage = base_damage * gem.crit_multiplier * combo_multiplier * damage_bonus_multiplier
                            critical_hits += 1
                        else:
                            damage = base_damage * combo_multiplier * damage_bonus_multiplier
                        total_damage += damage
                        
        # Округляем урон до целого
        total_damage = int(total_damage)
        
        # Определяем цвет для урона и статус критического удара
        if critical_hits > 0:
            # Критический урон - красный или фиолетовый
            if total_damage > 50:
                damage_color = (255, 50, 50)  # Яркий красный для большого крита
            else:
                damage_color = (255, 100, 180)  # Розовый для обычного крита
            is_critical = True
        else:
            # Обычный урон - градация от желтого к красному в зависимости от величины
            if total_damage > 50:
                damage_color = (255, 120, 0)  # Оранжевый для большого урона
            else:
                damage_color = (255, 200, 0)  # Желтый для малого урона
            is_critical = False
            
        # Сохраняем информацию для показа урона
        self._was_critical = is_critical
        self._damage_color = damage_color
        
        # Если был нанесен урон - уменьшаем здоровье врага
        if total_damage > 0:
            # Наносим урон врагу
            self.npc_manager.enemy_health = max(0, self.npc_manager.enemy_health - total_damage)
            
            # Запускаем эффект дрожания NPC
            self.npc_manager.trigger_shake()
            
            # Добавляем popup с уроном
            if info['is_root_call']:
                self.damage_popups.append({
                    'value': total_damage,
                    'is_crit': is_critical,
                    'start_time': pygame.time.get_ticks(),
                    'color': damage_color
                })
            
            # Проверяем, не побежден ли враг
            if self.npc_manager.enemy_health <= 0:
                # Победа!
                self.npc_manager.enemy_health = 0
                
                # Проверяем, является ли текущий враг боссом
                total_level = self.npc_manager.total_level
                stage = (total_level - 1) // 10 + 1
                local_level = (total_level - 1) % 10 + 1
                is_boss = (local_level == 10)
                
                # Создаем уникальный ID для босса, чтобы отслеживать первое убийство
                if is_boss:
                    boss_id = f"boss_{stage}_{local_level}"
                    
                    # Если это первый раз, когда мы побеждаем этого босса
                    if boss_id not in self.defeated_bosses:
                        self.defeated_bosses.add(boss_id)
                        self.ether_crystals += 1  # Награда эфирным кристаллом
                        
                        # Добавляем сообщение о получении эфирного кристалла
                        self.damage_popups.append({
                            'value': '+1 ЭК',
                            'is_crit': True,
                            'start_time': pygame.time.get_ticks() + 300,  # Немного задержки после урона
                            'color': (120, 200, 255)  # Голубой цвет для кристаллов
                        })
                
                # Стандартная награда монетами
                self.coins += int(10 + (self.global_level * 5))
                
                # Шанс выпадения предметов
                drop_chance = 0.3  # 30% шанс выпадения предмета
                if random.random() < drop_chance:
                    # Определяем какой предмет выпадет
                    item_roll = random.random()
                    if item_roll < 0.4:  # 40% шанс зелья урона
                        item = {'type': 'damage_potion', 'count': 1}
                    elif item_roll < 0.7:  # 30% шанс зелья крита
                        item = {'type': 'crit_potion', 'count': 1}
                    else:  # 30% шанс зелья здоровья
                        item = {'type': 'health_potion', 'count': 1}
                    
                    # Добавляем предмет в инвентарь
                    if self.add_to_inventory(item):
                        # Показываем уведомление о полученном предмете
                        item_name = {
                            'damage_potion': 'Зелье урона',
                            'crit_potion': 'Зелье крита',
                            'health_potion': 'Зелье здоровья'
                        }.get(item['type'], item['type'])
                        
                        self.damage_popups.append({
                            'value': f"+{item_name}",
                            'is_crit': True,
                            'start_time': pygame.time.get_ticks() + 500,  # Показываем после сообщения о кристалле
                            'color': (200, 255, 120)  # Светло-зеленый для лута
                        })
                
                # Переходим к следующему врагу/уровню
                self.npc_manager.total_level += 1
                
                # Обновляем глобальный уровень и панель локаций
                self.global_level = self.npc_manager.total_level
                self.location_panel.set_level(self.global_level)
                
                # Получаем информацию о новом уровне
                zone_name, lvl_in_zone, zone_idx = self.get_level_info(self.global_level)
                
                # Обновляем здоровье нового врага
                base_hp = 100
                hp = int(base_hp * (1.15 ** (self.global_level-1)))
                self.npc_manager.current_npc = self.npc_manager._get_npc()
                self.npc_manager.ENEMY_MAX_HEALTH = hp
                self.npc_manager.enemy_health = hp
                self.npc_manager.npc_image = self.npc_manager._load_npc_image(self.npc_manager.current_npc['image'])
            
        # Уменьшаем количество ходов, если это был ход игрока
        if info['is_player_move']:
            self.moves_left = max(0, self.moves_left - 1)
            
        # Проверяем новые совпадения после завершения анимаций
        # Защита от бесконечного цикла обработки
        recursion_depth = getattr(self, '_match_recursion_depth', 0)
        new_matches = self.check_matches()
        
        if new_matches and info['is_player_move'] and recursion_depth <= 10:
            # Запускаем обработку с увеличенным счетчиком рекурсии
            self.process_matches(new_matches, is_player_move=False, accum_damage=total_damage, is_root_call=info['is_root_call'])
        else:
            # Если больше нет совпадений или достигнут лимит рекурсии
            self.is_processing_matches = False
            self.animation_complete = True
            # Сбрасываем счетчик рекурсии
            if hasattr(self, '_match_recursion_depth'):
                delattr(self, '_match_recursion_depth')

        # Очищаем информацию о текущей обработке
        delattr(self, '_pending_info')

    def start_gem_fall(self, gem, target_y):
        """Запуск анимации падения гема"""
        if not gem:
            return
        gem.start_falling(target_y)
        self.falling_gems.append(gem)
        self.animation_complete = False
        # Обновляем позицию гема в сетке
        self.grid[target_y][gem.x] = gem 

    def evolve_gem(self, gem_type):
        """Эволюция гема, если есть достаточно эфирных кристаллов"""
        if gem_type not in self.gem_progress:
            return False

        gem_prog = self.gem_progress[gem_type]
        current_evolution = gem_prog['evolution']
        
        # Стоимость эволюции: 1 кристалл для первой, 2 для второй и т.д.
        evolution_cost = current_evolution + 1
        
        if self.ether_crystals < evolution_cost:
            return False  # Недостаточно кристаллов
            
        # Виды бонусов эволюции для разных типов гемов
        evolution_bonuses = {
            'red': ['fire_explosion', 'burning', 'meteor_strike'],
            'blue': ['ice_freeze', 'water_wave', 'blizzard'],
            'green': ['poison_cloud', 'healing', 'growth'],
            'yellow': ['lightning_chain', 'stun', 'thunder_storm'],
            'purple': ['dark_void', 'life_drain', 'shadow_clone'],
            'orange': ['rock_slam', 'tremor', 'mountain_rise']
        }
        
        # Если у гема нет бонуса для следующей эволюции, выходим
        if gem_type not in evolution_bonuses or current_evolution >= len(evolution_bonuses[gem_type]):
            return False
            
        # Выполняем эволюцию
        self.ether_crystals -= evolution_cost
        gem_prog['evolution'] += 1
        gem_prog['evolved_bonus'] = evolution_bonuses[gem_type][current_evolution]
        
        # Увеличиваем характеристики гема
        gem_prog['damage'] = int(gem_prog['damage'] * 1.25)  # +25% к урону
        gem_prog['crit_chance'] = min(0.7, gem_prog['crit_chance'] + 0.05)  # +5% к шансу крита
        gem_prog['crit_multiplier'] += 0.2  # +0.2 к множителю крита
        
        # Синхронизируем все гемы этого типа на поле
        self.sync_gems_with_progress(gem_type)
        
        return True
        
    def _show_gems_info_screen(self):
        """Отображает экран информации о гемах с возможностью эволюции"""
        info_w = 800
        info_h = 600
        info_x = (WINDOW_WIDTH - info_w) // 2
        info_y = max(20, (WINDOW_HEIGHT - info_h) // 2 - 50)
        info_surface = pygame.Surface((info_w, info_h), pygame.SRCALPHA)
        pygame.draw.rect(info_surface, (40, 40, 60, 230), info_surface.get_rect(), border_radius=28)
        grad = pygame.Surface((info_w, info_h//3), pygame.SRCALPHA)
        for i in range(info_h//3):
            alpha = max(0, 90 - i//2)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,info_w,1))
        grad_mask = pygame.Surface((info_w, info_h//3), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=28)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        info_surface.blit(grad, (0,0))
        font = pygame.font.Font(None, 48)
        title = font.render("Гемы и прокачка", True, COLORS['WHITE'])
        info_surface.blit(title, (info_w//2 - title.get_width()//2, 30))
        
        # Отображаем кристаллы для эволюции
        crystal_font = pygame.font.Font(None, 32)
        crystal_text = crystal_font.render(f"Эфирные кристаллы: {self.ether_crystals}", True, (120, 200, 255))
        info_surface.blit(crystal_text, (info_w//2 - crystal_text.get_width()//2, 80))
        
        # Отображаем карточки гемов
        card_w, card_h = 340, 170
        card_gap_x, card_gap_y = 10, 10
        cols = 2
        rows = 3
        start_x = (info_w - (card_w * cols + card_gap_x * (cols - 1))) // 2
        start_y = 120
        
        self._gem_evolution_buttons = []  # Сохраняем кнопки для обработки кликов
        
        for idx, gem_type in enumerate(GEM_TYPES):
            col = idx % cols
            row = idx // cols
            card_x = start_x + col * (card_w + card_gap_x)
            card_y = start_y + row * (card_h + card_gap_y)
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
            pygame.draw.rect(info_surface, (60, 60, 90, 210), card_rect, border_radius=16)
            pygame.draw.rect(info_surface, COLORS['WHITE'], card_rect, 2, border_radius=16)
            
            try:
                gem_img = pygame.image.load(GEM_IMAGES[gem_type]).convert_alpha()
                gem_img = pygame.transform.smoothscale(gem_img, (48, 48))
            except Exception:
                gem_img = pygame.Surface((48,48), pygame.SRCALPHA)
                gem_img.fill(COLORS['GRAY'])
            
            info_surface.blit(gem_img, (card_x + 14, card_y + 14))
            
            prog = self.gem_progress[gem_type]
            gem_level = prog['level']
            gem_xp = prog['xp']
            gem_xp_next = int(100 * (1.2 ** (gem_level-1)))
            
            name_font = pygame.font.Font(None, 30)
            name_text = name_font.render(gem_type.capitalize(), True, COLORS['WHITE'])
            info_surface.blit(name_text, (card_x + 74, card_y + 18))
            
            lvl_font = pygame.font.Font(None, 26)
            lvl_text = lvl_font.render(f"Ур. {gem_level}", True, COLORS['CYAN'])
            info_surface.blit(lvl_text, (card_x + card_w - lvl_text.get_width() - 16, card_y + 18))
            
            stat_font = pygame.font.Font(None, 24)
            dmg_text = stat_font.render(f"Урон: {prog['damage']}", True, COLORS['GOLD'])
            crit_text = stat_font.render(f"Крит: {int(prog['crit_chance']*100)}%", True, COLORS['PINK'])
            info_surface.blit(dmg_text, (card_x + 74, card_y + 48))
            info_surface.blit(crit_text, (card_x + card_w - crit_text.get_width() - 16, card_y + 48))
            
            xp_text = stat_font.render(f"Опыт: {gem_xp}/{gem_xp_next}", True, COLORS['WHITE'])
            info_surface.blit(xp_text, (card_x + 74, card_y + 76))
            
            # Информация об эволюции
            evolution_text = stat_font.render(f"Эволюция: {prog['evolution']}", True, COLORS['YELLOW'])
            info_surface.blit(evolution_text, (card_x + card_w - evolution_text.get_width() - 16, card_y + 76))
            
            if prog['evolved_bonus']:
                bonus_text = stat_font.render(f"Бонус: {prog['evolved_bonus']}", True, COLORS['GREEN'])
                info_surface.blit(bonus_text, (card_x + 74, card_y + 104))
            
            # Полоска опыта
            bar_w, bar_h = card_w - 90, 14
            bar_x = card_x + 74
            bar_y = card_y + card_h - 58
            pygame.draw.rect(info_surface, COLORS['LIGHT_GRAY'], (bar_x, bar_y, bar_w, bar_h), border_radius=7)
            fill_w = int(bar_w * min(gem_xp / gem_xp_next, 1.0))
            pygame.draw.rect(info_surface, COLORS['CYAN'], (bar_x, bar_y, fill_w, bar_h), border_radius=7)
            pygame.draw.rect(info_surface, COLORS['WHITE'], (bar_x, bar_y, bar_w, bar_h), 2, border_radius=7)
            
            # Кнопка эволюции, если доступна
            evolution_cost = prog['evolution'] + 1
            can_evolve = self.ether_crystals >= evolution_cost
            evolve_btn_w, evolve_btn_h = 170, 32
            evolve_btn_x = card_x + (card_w - evolve_btn_w) // 2
            evolve_btn_y = card_y + card_h - 40
            evolve_btn_rect = pygame.Rect(evolve_btn_x, evolve_btn_y, evolve_btn_w, evolve_btn_h)
            btn_color = (100, 180, 100, 220) if can_evolve else (100, 100, 100, 180)
            pygame.draw.rect(info_surface, btn_color, evolve_btn_rect, border_radius=12)
            pygame.draw.rect(info_surface, COLORS['WHITE'], evolve_btn_rect, 2, border_radius=12)
            
            evolve_cost_text = f"Эволюция: {evolution_cost} ЭК"
            evolve_font = pygame.font.Font(None, 22)
            evolve_text = evolve_font.render(evolve_cost_text, True, COLORS['WHITE'])
            info_surface.blit(evolve_text, (evolve_btn_x + evolve_btn_w//2 - evolve_text.get_width()//2, evolve_btn_y + evolve_btn_h//2 - evolve_text.get_height()//2))
            
            # Сохраняем кнопку для обработки кликов
            global_btn_rect = pygame.Rect(info_x + evolve_btn_x, info_y + evolve_btn_y, evolve_btn_w, evolve_btn_h)
            self._gem_evolution_buttons.append((gem_type, global_btn_rect, can_evolve))
        
        # Кнопка закрытия
        close_btn_width = 100
        close_btn_height = 40
        close_btn_x = info_w - close_btn_width - 20
        close_btn_y = 15
        close_btn_rect = pygame.Rect(close_btn_x, close_btn_y, close_btn_width, close_btn_height)
        pygame.draw.rect(info_surface, (120,40,40,220), close_btn_rect, border_radius=14)
        pygame.draw.rect(info_surface, COLORS['WHITE'], close_btn_rect, 2, border_radius=14)
        close_font = pygame.font.Font(None, 32)
        close_text = close_font.render("Закрыть", True, COLORS['WHITE'])
        info_surface.blit(close_text, (close_btn_x + close_btn_width//2 - close_text.get_width()//2, close_btn_y + close_btn_height//2 - close_text.get_height()//2))
        
        self.screen.blit(info_surface, (info_x, info_y))
        self._gems_close_btn_rect = pygame.Rect(info_x + close_btn_x, info_y + close_btn_y, close_btn_width, close_btn_height)