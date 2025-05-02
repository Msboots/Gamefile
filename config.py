import pygame
import os

# Пути к изображениям
IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')
GEM_IMAGES = {
    'BLUE': os.path.join(IMAGE_DIR, 'gems', 'blue.png'),      # вода
    'CYAN': os.path.join(IMAGE_DIR, 'gems', 'cyan.png'),      # череп
    'GREEN': os.path.join(IMAGE_DIR, 'gems', 'green.png'),    # природа
    'PURPLE': os.path.join(IMAGE_DIR, 'gems', 'purple.png'),  # луна
    'RED': os.path.join(IMAGE_DIR, 'gems', 'red.png'),        # огонь
    'YELLOW': os.path.join(IMAGE_DIR, 'gems', 'yellow.png'),  # солнце
}

# Размеры окна
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Размеры игрового поля
GRID_SIZE = 10
CELL_SIZE = 50
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50

# Цвета
COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'GRAY': (128, 128, 128),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0)
}

# Настройки гемов
GEM_TYPES = ['BLUE', 'CYAN', 'GREEN', 'PURPLE', 'RED', 'YELLOW']
GEM_LEVELS = 5
BASE_DAMAGE = 10
CRIT_CHANCE = 0.1
CRIT_MULTIPLIER = 2.0

# Настройки персонажа
ENEMY_MAX_HEALTH = 1000
ENEMY_HEALTH_BAR_WIDTH = 200
ENEMY_HEALTH_BAR_HEIGHT = 20

# Настройки анимации
ANIMATION_SPEED = 0.2
SWAP_DURATION = 0.3
EXPLOSION_DURATION = 0.5

# Настройки магазина
UPGRADE_COSTS = {
    'damage': [100, 200, 400, 800, 1600],
    'crit_chance': [150, 300, 600, 1200, 2400],
    'crit_multiplier': [200, 400, 800, 1600, 3200]
}

# Настройки сохранения
SAVE_FILE = 'save.json' 