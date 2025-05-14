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
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700

# Размеры сетки
GRID_SIZE = 8
CELL_SIZE = 50
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50

# Смещение игрового поля для отрисовки (учитывает верхнюю панель)
FIELD_DRAW_OFFSET_X = GRID_OFFSET_X - 15
FIELD_DRAW_OFFSET_Y = 30 + 60 + 10 + GRID_OFFSET_Y - 15  # top_panel_margin + top_panel_h + 10 + GRID_OFFSET_Y - 15

# Цвета
COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'PURPLE': (128, 0, 128),
    'ORANGE': (255, 165, 0),
    'DARK_GRAY': (64, 64, 64),
    'SHADOW': (0, 0, 0, 128),
    'BUTTON': (45, 45, 75),
    'BUTTON_HOVER': (65, 65, 95),
    'GRAY': (128, 128, 128),
    'LIGHT_GRAY': (192, 192, 192),
    'GOLD': (255, 215, 0),
    'CYAN': (0, 255, 255),
    'PINK': (255, 105, 180),
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
    },
    'health_potion': {
        'name': 'Зелье здоровья',
        'description': 'Восстанавливает 30% здоровья',
        'cost': 60,
        'duration': 0
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

FIELD_INNER_PADDING = 15

BORDER = 14
FIELD_OFFSET_X = GRID_OFFSET_X + BORDER
FIELD_OFFSET_Y = GRID_OFFSET_Y + BORDER

# Базовый урон
BASE_DAMAGE = 10

# Шанс критического удара
CRIT_CHANCE = 0.1

# Множитель критического удара
CRIT_MULTIPLIER = 2.0

COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'PURPLE': (128, 0, 128),
    'ORANGE': (255, 165, 0),
    'DARK_GRAY': (64, 64, 64),
    'SHADOW': (0, 0, 0, 128),
    'BUTTON': (45, 45, 75),
    'BUTTON_HOVER': (65, 65, 95),
    'GRAY': (128, 128, 128),
    'LIGHT_GRAY': (192, 192, 192),
    'GOLD': (255, 215, 0),
    'CYAN': (0, 255, 255),
    'PINK': (255, 105, 180),
    'UI_SHADOW': (0, 0, 0, 100),
    'UI_BG': (40, 40, 60),
    'UI_ACCENT': (255, 255, 255, 40),
}

# Путь к файлу с NPC
NPCS_FILE = "npcs.json" 