import pygame
import os

# Получаем абсолютный путь к директории проекта
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Пути к изображениям
IMAGE_DIR = os.path.join(PROJECT_DIR, 'images')
GEM_IMAGES = {
    'red': os.path.join(IMAGE_DIR, 'gems', 'red.png'),
    'blue': os.path.join(IMAGE_DIR, 'gems', 'blue.png'),
    'green': os.path.join(IMAGE_DIR, 'gems', 'green.png'),
    'yellow': os.path.join(IMAGE_DIR, 'gems', 'yellow.png'),
    'purple': os.path.join(IMAGE_DIR, 'gems', 'purple.png'),
    'cyan': os.path.join(IMAGE_DIR, 'gems', 'cyan.png')
}

# Типы гемов
GEM_TYPES = list(GEM_IMAGES.keys())

# Размеры окна
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Размеры сетки
GRID_SIZE = 8
CELL_SIZE = 50
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50

# Цвета
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'GRAY': (128, 128, 128),
    'DARK_GRAY': (64, 64, 64),
    'LIGHT_GRAY': (192, 192, 192),
    'GOLD': (255, 215, 0),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'YELLOW': (255, 215, 0),
    'BLUE': (0, 120, 255),
    'PURPLE': (155, 89, 182),
    'CYAN': (0, 255, 255),
    'ORANGE': (255, 140, 0),
    'PINK': (255, 105, 180),
    'SHADOW': (30, 30, 30),
    'UI_SHADOW': (0, 0, 0, 100),
    'UI_BG': (40, 40, 60),
    'UI_ACCENT': (255, 255, 255, 40),
}

# Базовый урон
BASE_DAMAGE = 10

# Шанс критического удара
CRIT_CHANCE = 0.1

# Множитель критического удара
CRIT_MULTIPLIER = 2.0

# Настройки персонажа
ENEMY_MAX_HEALTH = 1000
ENEMY_HEALTH_BAR_WIDTH = 200
ENEMY_HEALTH_BAR_HEIGHT = 20
ENEMY_HEALTH_BAR_X = WINDOW_WIDTH - ENEMY_HEALTH_BAR_WIDTH - 50
ENEMY_HEALTH_BAR_Y = 50

# Настройки анимации
ANIMATION_SPEED = 0.3  # секунды
SWAP_DURATION = 200
EXPLOSION_DURATION = 0.5

# Константы для анимаций
MOVE_DURATION = 200  # Длительность анимации движения в миллисекундах
RETURN_DURATION = 200  # Длительность анимации возврата в миллисекундах

# Настройки магазина
BONUSES = {
    'damage_potion': {
        'name': 'Зелье силы',
        'description': 'Увеличивает урон на 50% на 3 хода',
        'cost': 50,
        'duration': 3
    },
    'crit_cake': {
        'name': 'Пирог удачи',
        'description': 'Увеличивает шанс крита на 20% на 3 хода',
        'cost': 75,
        'duration': 3
    }
}

# Система опыта гемов
GEM_EXPERIENCE = {
    'BASE_XP': 10,
    'LEVEL_MULTIPLIER': 1.5,
    'DAMAGE_MULTIPLIER': 1.2,
    'MAX_LEVEL': 10
}

# Настройки сохранения
SAVE_FILE = 'save.json' 