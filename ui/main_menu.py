import pygame
from config import *

class MainMenu:
    def __init__(self):
        self.visible = True
        self.buttons = []
        self.selected_button = None
        
        # Настройки кнопок
        button_width = 300
        button_height = 80
        button_spacing = 30
        
        # Вычисляем позиции для центрирования кнопок
        start_y = (WINDOW_HEIGHT - (3 * button_height + 2 * button_spacing)) // 2
        
        # Создаем кнопки
        self.buttons = [
            {
                'rect': pygame.Rect((WINDOW_WIDTH - button_width) // 2, 
                                  start_y + i * (button_height + button_spacing),
                                  button_width, button_height),
                'text': text,
                'action': action
            }
            for i, (text, action) in enumerate([
                ('Новая игра', 'new_game'),
                ('Продолжить', 'continue'),
                ('Выход', 'exit')
            ])
        ]
        
        # Загружаем шрифт
        self.font = pygame.font.Font(None, 48)
        
    def draw(self, screen):
        if not self.visible:
            return
            
        # Затемняем фон
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        screen.blit(overlay, (0, 0))
        
        # Рисуем кнопки
        for button in self.buttons:
            # Рисуем фон кнопки
            color = COLORS['BUTTON_HOVER'] if button == self.selected_button else COLORS['BUTTON']
            pygame.draw.rect(screen, color, button['rect'], border_radius=15)
            
            # Рисуем рамку кнопки
            pygame.draw.rect(screen, COLORS['WHITE'], button['rect'], 3, border_radius=15)
            
            # Добавляем градиент и блик
            gradient_rect = button['rect'].copy()
            gradient_surface = pygame.Surface((gradient_rect.width, gradient_rect.height), pygame.SRCALPHA)
            for i in range(gradient_rect.height // 2):
                alpha = 100 - (i * 2)
                if alpha > 0:
                    pygame.draw.rect(gradient_surface, (255, 255, 255, alpha),
                                   (0, i, gradient_rect.width, 1))
            screen.blit(gradient_surface, gradient_rect)
            
            # Рисуем текст
            text_surface = self.font.render(button['text'], True, COLORS['WHITE'])
            text_rect = text_surface.get_rect(center=button['rect'].center)
            screen.blit(text_surface, text_rect)
            
    def handle_event(self, event):
        if not self.visible:
            return None
            
        if event.type == pygame.MOUSEMOTION:
            # Проверяем наведение на кнопки
            self.selected_button = None
            for button in self.buttons:
                if button['rect'].collidepoint(event.pos):
                    self.selected_button = button
                    break
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Проверяем клик по кнопкам
            for button in self.buttons:
                if button['rect'].collidepoint(event.pos):
                    return button['action']
        
        return None 