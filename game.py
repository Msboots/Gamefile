import pygame
import random
import json
from config import *
from entities.gem import Gem
from ui.shop import Shop

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Match-3 RPG")
        self.clock = pygame.time.Clock()
        self.running = True
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_gem = None
        self.enemy_health = ENEMY_MAX_HEALTH
        self.coins = 0
        self.moves_left = 30
        self.shop = Shop(self)
        self.initialize_grid()
        self.load_save()

    def initialize_grid(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = Gem(x, y)

    def draw(self):
        self.screen.fill(COLORS['WHITE'])
        
        # Рисуем сетку
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x]:
                    self.grid[y][x].draw(self.screen)

        # Рисуем полосу здоровья врага
        health_bar_x = GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 50
        health_bar_y = GRID_OFFSET_Y
        pygame.draw.rect(self.screen, COLORS['RED'], 
                        (health_bar_x, health_bar_y, 
                         ENEMY_HEALTH_BAR_WIDTH, ENEMY_HEALTH_BAR_HEIGHT))
        current_health_width = (self.enemy_health / ENEMY_MAX_HEALTH) * ENEMY_HEALTH_BAR_WIDTH
        pygame.draw.rect(self.screen, COLORS['GREEN'], 
                        (health_bar_x, health_bar_y, 
                         current_health_width, ENEMY_HEALTH_BAR_HEIGHT))

        # Рисуем статистику
        font = pygame.font.Font(None, 36)
        stats_y = health_bar_y + ENEMY_HEALTH_BAR_HEIGHT + 20
        moves_text = font.render(f"Ходы: {self.moves_left}", True, COLORS['BLACK'])
        coins_text = font.render(f"Монеты: {self.coins}", True, COLORS['BLACK'])
        self.screen.blit(moves_text, (health_bar_x, stats_y))
        self.screen.blit(coins_text, (health_bar_x, stats_y + 40))

        # Рисуем кнопку магазина
        shop_button = pygame.Rect(health_bar_x, stats_y + 80, 150, 40)
        pygame.draw.rect(self.screen, COLORS['WHITE'], shop_button)
        pygame.draw.rect(self.screen, COLORS['BLACK'], shop_button, 2)
        shop_text = font.render("Магазин", True, COLORS['BLACK'])
        self.screen.blit(shop_text, (shop_button.centerx - shop_text.get_width() // 2,
                                   shop_button.centery - shop_text.get_height() // 2))

        # Рисуем магазин
        self.shop.draw(self.screen)

        pygame.display.flip()

    def handle_click(self, pos):
        # Проверяем клик по кнопке магазина
        shop_button = pygame.Rect(
            GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 50,
            GRID_OFFSET_Y + ENEMY_HEALTH_BAR_HEIGHT + 100,
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
                    self.swap_gems(self.selected_gem, (x, y))
                    if not self.check_matches():
                        self.swap_gems(self.selected_gem, (x, y))
                    else:
                        self.moves_left -= 1
                self.grid[self.selected_gem[1]][self.selected_gem[0]].is_selected = False
                self.selected_gem = None

    def is_adjacent(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

    def swap_gems(self, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
        self.grid[y1][x1].move_to(x1, y1)
        self.grid[y2][x2].move_to(x2, y2)

    def check_matches(self):
        matches = []
        # Проверяем горизонтальные совпадения
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE - 2):
                if (self.grid[y][x] and self.grid[y][x+1] and self.grid[y][x+2] and
                    self.grid[y][x].type == self.grid[y][x+1].type == self.grid[y][x+2].type):
                    matches.append([(x, y), (x+1, y), (x+2, y)])

        # Проверяем вертикальные совпадения
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE - 2):
                if (self.grid[y][x] and self.grid[y+1][x] and self.grid[y+2][x] and
                    self.grid[y][x].type == self.grid[y+1][x].type == self.grid[y+2][x].type):
                    matches.append([(x, y), (x, y+1), (x, y+2)])

        if matches:
            self.process_matches(matches)
            return True
        return False

    def process_matches(self, matches):
        total_damage = 0
        critical_hits = 0
        
        for match in matches:
            for x, y in match:
                if self.grid[y][x]:
                    damage, is_crit = self.grid[y][x].calculate_damage()
                    total_damage += damage
                    if is_crit:
                        critical_hits += 1
                    self.grid[y][x] = None

        self.enemy_health = max(0, self.enemy_health - total_damage)
        self.coins += critical_hits * 10
        self.fill_empty_cells()

    def fill_empty_cells(self):
        for x in range(GRID_SIZE):
            empty_cells = 0
            for y in range(GRID_SIZE - 1, -1, -1):
                if self.grid[y][x] is None:
                    empty_cells += 1
                elif empty_cells > 0:
                    self.grid[y + empty_cells][x] = self.grid[y][x]
                    self.grid[y][x] = None
                    self.grid[y + empty_cells][x].move_to(x, y + empty_cells)

            for y in range(empty_cells):
                self.grid[y][x] = Gem(x, y)
                self.grid[y][x].move_to(x, y)

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
            pass

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.grid[y][x]:
                        self.grid[y][x].update(dt)

            self.draw()

            if self.enemy_health <= 0 or self.moves_left <= 0:
                self.save_game()
                self.running = False

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run() 