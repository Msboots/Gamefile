import pygame
from config import *

class Shop:
    def __init__(self, game):
        self.game = game
        self.visible = False
        self.bonuses = BONUSES
        self.selected_bonus = None
        self.damage_bonus = False
        self.damage_timer = 0
        self.crit_bonus = False
        self.crit_timer = 0
        
        # Создаем поверхность для магазина
        self.surface = pygame.Surface((300, 400))
        self.surface.fill(COLORS['DARK_GRAY'])
        self.rect = self.surface.get_rect()
        self.rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        
        # Создаем кнопки для бонусов
        self.buttons = []
        button_width = 200
        button_height = 100
        button_spacing = 20
        
        # Вычисляем общую высоту всех кнопок
        total_height = len(self.bonuses) * (button_height + button_spacing) - button_spacing
        
        # Начальная позиция для первой кнопки (центрируем по вертикали)
        start_y = (self.rect.height - total_height) // 2
        
        for i, (bonus_id, bonus) in enumerate(self.bonuses.items()):
            # Вычисляем позицию кнопки относительно центра магазина
            button_x = (self.rect.width - button_width) // 2
            button_y = start_y + i * (button_height + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            self.buttons.append((bonus_id, button_rect))

    def draw(self, screen):
        if not self.visible:
            return
            
        # Рисуем фон магазина
        screen.blit(self.surface, self.rect)
        
        # Рисуем заголовок
        font = pygame.font.Font(None, 36)
        title = font.render("Магазин", True, COLORS['WHITE'])
        screen.blit(title, (self.rect.centerx - title.get_width() // 2, self.rect.top + 20))
        
        # Рисуем кнопки и информацию о бонусах
        for bonus_id, button_rect in self.buttons:
            # Переводим координаты кнопки в глобальные координаты экрана
            global_button_rect = button_rect.move(self.rect.topleft)
            
            bonus = self.bonuses[bonus_id]
            
            # Рисуем кнопку
            button_color = COLORS['GRAY'] if self.selected_bonus == bonus_id else COLORS['LIGHT_GRAY']
            pygame.draw.rect(screen, button_color, global_button_rect)
            pygame.draw.rect(screen, COLORS['WHITE'], global_button_rect, 2)
            
            # Рисуем название и описание
            name_font = pygame.font.Font(None, 24)
            desc_font = pygame.font.Font(None, 18)
            
            name_text = name_font.render(bonus['name'], True, COLORS['WHITE'])
            desc_text = desc_font.render(bonus['description'], True, COLORS['WHITE'])
            cost_text = desc_font.render(f"Цена: {bonus['cost']} монет", True, COLORS['GOLD'])
            
            # Центрируем текст
            name_x = global_button_rect.centerx - name_text.get_width() // 2
            desc_x = global_button_rect.centerx - desc_text.get_width() // 2
            cost_x = global_button_rect.centerx - cost_text.get_width() // 2
            
            screen.blit(name_text, (name_x, global_button_rect.y + 10))
            screen.blit(desc_text, (desc_x, global_button_rect.y + 40))
            screen.blit(cost_text, (cost_x, global_button_rect.y + 70))
            
            # Показываем активный бонус
            if bonus_id == 'damage_potion' and self.damage_bonus:
                active_text = desc_font.render(f"Активен: {self.damage_timer} ходов", True, COLORS['GREEN'])
                active_x = global_button_rect.centerx - active_text.get_width() // 2
                screen.blit(active_text, (active_x, global_button_rect.y + 80))
            elif bonus_id == 'crit_cake' and self.crit_bonus:
                active_text = desc_font.render(f"Активен: {self.crit_timer} ходов", True, COLORS['GREEN'])
                active_x = global_button_rect.centerx - active_text.get_width() // 2
                screen.blit(active_text, (active_x, global_button_rect.y + 80))

    def handle_click(self, pos):
        if not self.visible:
            return
            
        # Проверяем, кликнули ли вне магазина
        if not self.rect.collidepoint(pos):
            self.visible = False
            return
            
        # Проверяем клик по кнопкам
        for bonus_id, button_rect in self.buttons:
            # Переводим координаты кнопки в глобальные координаты экрана
            global_button_rect = button_rect.move(self.rect.topleft)
            if global_button_rect.collidepoint(pos):
                self.selected_bonus = bonus_id
                self.buy_bonus(bonus_id)
                return

    def buy_bonus(self, bonus_id):
        bonus = self.bonuses[bonus_id]
        
        # Проверяем, достаточно ли монет
        if self.game.coins >= bonus['cost']:
            self.game.coins -= bonus['cost']
            
            if bonus_id == 'damage_potion':
                self.damage_bonus = True
                self.damage_timer = bonus['duration']
            elif bonus_id == 'crit_cake':
                self.crit_bonus = True
                self.crit_timer = bonus['duration']
                
            print(f"Куплен бонус: {bonus['name']}")
        else:
            print("Недостаточно монет!")

    def update(self):
        # Обновляем таймеры бонусов
        if self.damage_bonus:
            self.damage_timer -= 1
            if self.damage_timer <= 0:
                self.damage_bonus = False
                
        if self.crit_bonus:
            self.crit_timer -= 1
            if self.crit_timer <= 0:
                self.crit_bonus = False

    def toggle_visibility(self):
        self.visible = not self.visible
        if self.visible:
            print("Магазин открыт")
        else:
            print("Магазин закрыт") 