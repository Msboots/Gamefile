import pygame
from config import *

class Shop:
    def __init__(self, game):
        self.game = game
        self.is_visible = False
        self.damage_bonus = False
        self.damage_timer = 0
        self.crit_bonus = False
        self.crit_timer = 0
        self.surface = pygame.Surface((300, 400))
        self.surface.fill((50, 50, 50))
        self.buttons = []
        
        # Создаем кнопки для бонусов
        y_offset = 100
        for bonus_id, bonus_data in BONUSES.items():
            button = pygame.Rect(50, y_offset, 200, 100)
            self.buttons.append((button, bonus_id))
            y_offset += 120
        
    def draw(self, screen):
        if not self.is_visible:
            return
            
        # Отрисовка фона магазина
        screen.blit(self.surface, (SCREEN_WIDTH - 350, 50))
        
        # Отрисовка заголовка
        title = pygame.font.Font(None, 36).render("Магазин", True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH - 350 + (300 - title.get_width()) // 2, 20))
        
        # Отрисовка кнопок
        for button, bonus_id in self.buttons:
            bonus_data = BONUSES[bonus_id]
            
            # Отрисовка фона кнопки
            pygame.draw.rect(screen, (100, 100, 100), button)
            
            # Отрисовка текста
            name = pygame.font.Font(None, 24).render(bonus_data['name'], True, (255, 255, 255))
            description = pygame.font.Font(None, 18).render(bonus_data['description'], True, (200, 200, 200))
            cost = pygame.font.Font(None, 24).render(f"Цена: {bonus_data['cost']}", True, (255, 255, 0))
            
            screen.blit(name, (button.x + (button.width - name.get_width()) // 2, button.y + 10))
            screen.blit(description, (button.x + (button.width - description.get_width()) // 2, button.y + 40))
            screen.blit(cost, (button.x + (button.width - cost.get_width()) // 2, button.y + 70))
            
            # Отрисовка статуса бонуса
            if bonus_id == 'damage_potion' and self.damage_bonus:
                status = pygame.font.Font(None, 18).render(f"Активен: {self.damage_timer} ходов", True, (0, 255, 0))
                screen.blit(status, (button.x + (button.width - status.get_width()) // 2, button.y + 90))
            elif bonus_id == 'crit_cake' and self.crit_bonus:
                status = pygame.font.Font(None, 18).render(f"Активен: {self.crit_timer} ходов", True, (0, 255, 0))
                screen.blit(status, (button.x + (button.width - status.get_width()) // 2, button.y + 90))
                
    def handle_click(self, pos):
        if not self.is_visible:
            return
            
        # Проверяем клик по кнопкам
        for button, bonus_id in self.buttons:
            if button.collidepoint(pos):
                self.buy_bonus(bonus_id)
                
    def buy_bonus(self, bonus_id):
        bonus_data = BONUSES[bonus_id]
        
        # Проверяем, достаточно ли монет
        if self.game.coins < bonus_data['cost']:
            return
            
        # Применяем бонус
        if bonus_id == 'damage_potion':
            self.damage_bonus = True
            self.damage_timer = bonus_data['duration']
        elif bonus_id == 'crit_cake':
            self.crit_bonus = True
            self.crit_timer = bonus_data['duration']
            
        # Списываем монеты
        self.game.coins -= bonus_data['cost']
        
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
        self.is_visible = not self.is_visible
        if self.is_visible:
            print("Магазин открыт")
        else:
            print("Магазин закрыт") 