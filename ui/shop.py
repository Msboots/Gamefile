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
        
        # Отображаем текущее количество монет
        coins_font = pygame.font.Font(None, 28)
        coins_text = coins_font.render(f"Монеты: {self.game.coins}", True, COLORS['GOLD'])
        screen.blit(coins_text, (self.rect.centerx - coins_text.get_width() // 2, self.rect.top + 60))
        
        # Рисуем кнопки и информацию о бонусах
        for bonus_id, button_rect in self.buttons:
            # Переводим координаты кнопки в глобальные координаты экрана
            global_button_rect = button_rect.move(self.rect.topleft)
            
            bonus = self.bonuses[bonus_id]
            
            # Определяем цвет кнопки: серый если нет денег, светлый если есть
            can_afford = self.game.coins >= bonus['cost']
            button_color = COLORS['GRAY'] if not can_afford else COLORS['LIGHT_GRAY']
            if self.selected_bonus == bonus_id:
                button_color = (100, 130, 180)  # Выделение выбранного бонуса
                
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
            
            # Определяем тип предмета на основе ID бонуса
            if bonus_id == 'damage_potion':
                item_type = 'damage_potion'
            elif bonus_id == 'crit_cake':
                item_type = 'crit_potion'
            else:
                item_type = bonus_id  # Используем ID бонуса как тип предмета
            
            # Создаем предмет и добавляем в инвентарь
            item = {'type': item_type, 'count': 1}
            if self.game.add_to_inventory(item):
                print(f"Куплен предмет: {bonus['name']}")
            else:
                # Если не удалось добавить в инвентарь (нет места), возвращаем деньги
                self.game.coins += bonus['cost']
                print("Инвентарь полон!")
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