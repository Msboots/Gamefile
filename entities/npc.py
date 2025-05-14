import pygame
import os
import random
from config import *

class NPCManager:
    def __init__(self, npc_list, grid_size, cell_size, border, hud_width=280):
        self.npc_list = npc_list
        self.current_npc_index = 0
        self.game_over = False
        self.npc_image = None
        self.enemy_health = 0
        self.ENEMY_MAX_HEALTH = 0
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.border = border
        self.hud_width = hud_width
        self.npc_hit_time = None
        self.cycle_count = 0  # Счетчик пройденных циклов
        self.health_multiplier = 1.0  # Множитель здоровья
        self.current_npc = self._get_npc()
        self.enemy_health = self.current_npc['max_health']
        self.ENEMY_MAX_HEALTH = self.current_npc['max_health']
        self.npc_image = self._load_npc_image(self.current_npc['image'])
        self.total_level = 1
        self.shake_offset = 0
        self.shake_time = 0

    def _get_npc(self):
        # Случайный выбор спрайта из папки
        npc_dir = os.path.join('images', 'npc_g')
        npc_files = [f for f in os.listdir(npc_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        chosen = random.choice(npc_files)
        return {
            'image': os.path.join(npc_dir, chosen),
            'max_health': 100  # или любая логика для HP
        }

    def _load_npc_image(self, image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Изображение NPC не найдено: {image_path}")
        img = pygame.image.load(image_path).convert_alpha()
        # Масштабируем спрайт под высоту игрового поля
        npc_height = self.grid_size * self.cell_size
        scale_factor = npc_height / img.get_height()
        npc_width = int(img.get_width() * scale_factor)
        return pygame.transform.smoothscale(img, (npc_width, npc_height))

    def next_npc(self, screen, field_rect, hud_y, hud_height):
        self.cycle_count += 1
        self.health_multiplier *= 1.2  # +20% к здоровью
        self.current_npc = self._get_npc()
        self.enemy_health = self.current_npc['max_health']
        self.ENEMY_MAX_HEALTH = self.current_npc['max_health']
        self.npc_image = self._load_npc_image(self.current_npc['image'])
        self.game_over = False

    def trigger_shake(self):
        self.npc_hit_time = pygame.time.get_ticks()

    def get_shake_offset(self):
        shake = 0
        if self.npc_hit_time:
            current_time = pygame.time.get_ticks()
            hit_duration = 200  # мс
            elapsed = current_time - self.npc_hit_time
            if elapsed < hit_duration:
                intensity = 1 - (elapsed / hit_duration)
                shake = int(8 * intensity) * (1 if (elapsed // 30) % 2 == 0 else -1)
            else:
                self.npc_hit_time = None
        return shake 