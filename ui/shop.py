import pygame
from config import *

class Shop:
    def __init__(self, game):
        self.game = game
        self.visible = False
        self.selected_gem_type = None
        self.upgrade_buttons = []
        self.initialize_buttons()

    def initialize_buttons(self):
        button_width = 150
        button_height = 40
        start_x = GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 50
        start_y = GRID_OFFSET_Y + 200

        # Кнопки выбора типа гема
        for i, gem_type in enumerate(GEM_TYPES):
            self.upgrade_buttons.append({
                'rect': pygame.Rect(start_x, start_y + i * 60, button_width, button_height),
                'text': f"Улучшить {gem_type}",
                'gem_type': gem_type,
                'stat': None
            })

        # Кнопки улучшения характеристик
        stats = ['damage', 'crit_chance', 'crit_multiplier']
        for i, stat in enumerate(stats):
            self.upgrade_buttons.append({
                'rect': pygame.Rect(start_x, start_y + len(GEM_TYPES) * 60 + i * 50, 
                                  button_width, button_height),
                'text': f"Улучшить {stat}",
                'gem_type': None,
                'stat': stat
            })

    def draw(self, screen):
        if not self.visible:
            return

        # Рисуем фон магазина
        shop_rect = pygame.Rect(
            GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 30,
            GRID_OFFSET_Y,
            200,
            WINDOW_HEIGHT - 2 * GRID_OFFSET_Y
        )
        pygame.draw.rect(screen, COLORS['GRAY'], shop_rect)
        pygame.draw.rect(screen, COLORS['BLACK'], shop_rect, 2)

        # Рисуем заголовок
        font = pygame.font.Font(None, 36)
        title = font.render("Магазин", True, COLORS['BLACK'])
        screen.blit(title, (shop_rect.centerx - title.get_width() // 2, 
                          shop_rect.y + 10))

        # Рисуем кнопки
        font = pygame.font.Font(None, 24)
        for button in self.upgrade_buttons:
            pygame.draw.rect(screen, COLORS['WHITE'], button['rect'])
            pygame.draw.rect(screen, COLORS['BLACK'], button['rect'], 2)
            
            text = font.render(button['text'], True, COLORS['BLACK'])
            screen.blit(text, (button['rect'].centerx - text.get_width() // 2,
                             button['rect'].centery - text.get_height() // 2))

            # Показываем стоимость улучшения
            if button['gem_type']:
                cost = UPGRADE_COSTS['damage'][0]  # Базовая стоимость
                cost_text = font.render(f"Стоимость: {cost}", True, COLORS['BLACK'])
                screen.blit(cost_text, (button['rect'].x, button['rect'].bottom + 5))
            elif button['stat']:
                cost = UPGRADE_COSTS[button['stat']][0]
                cost_text = font.render(f"Стоимость: {cost}", True, COLORS['BLACK'])
                screen.blit(cost_text, (button['rect'].x, button['rect'].bottom + 5))

    def handle_click(self, pos):
        if not self.visible:
            return

        for button in self.upgrade_buttons:
            if button['rect'].collidepoint(pos):
                if button['gem_type']:
                    self.upgrade_gem_type(button['gem_type'])
                elif button['stat']:
                    self.upgrade_stat(button['stat'])

    def upgrade_gem_type(self, gem_type):
        cost = UPGRADE_COSTS['damage'][0]
        if self.game.coins >= cost:
            self.game.coins -= cost
            # Находим все гемы данного типа и улучшаем их
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.game.grid[y][x] and self.game.grid[y][x].type == gem_type:
                        self.game.grid[y][x].upgrade('damage')

    def upgrade_stat(self, stat):
        cost = UPGRADE_COSTS[stat][0]
        if self.game.coins >= cost:
            self.game.coins -= cost
            # Улучшаем все гемы выбранного типа
            if self.selected_gem_type:
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if (self.game.grid[y][x] and 
                            self.game.grid[y][x].type == self.selected_gem_type):
                            self.game.grid[y][x].upgrade(stat)

    def toggle_visibility(self):
        self.visible = not self.visible 