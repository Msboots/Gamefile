import pygame

COSMIC_ZONES = [
    'Тундра', 'Пустыня', 'Джунгли', 'Ледяная комета', 'Астероид',
    'Галактика', 'Новая Земля', 'Космостанция', 'Пульсар', 'Квазар',
    'Туманность', 'Сверхновая', 'Чёрная дыра', 'Экзопланета', 'Магелланово облако'
]

class LocationPanel:
    def __init__(self, get_level_info, current_global_level=1):
        self.get_level_info = get_level_info  # функция (индекс) -> (zone_name, level_in_zone, zone_idx)
        self.current_global_level = current_global_level
        self.font = pygame.font.Font(None, 16)
        self.big_font = pygame.font.Font(None, 20)
        self._last_draw_rects = None

    def draw(self, screen, x, y):
        panel_w, panel_h = 250, 37
        arrow_w = 20
        gap = 8
        card_w, card_h = 32, 32
        visible = 5
        PANEL_BG = (40, 50, 80, 210)
        PANEL_BORDER = (255,255,255,60)
        ARROW_BG = (70, 90, 130)
        ARROW_FG = (180, 210, 255)
        CARD_BG = (120, 170, 255)
        CARD_BG_ACTIVE = (200, 230, 255)
        CARD_BORDER = (255,255,255)
        CARD_BORDER_ACTIVE = (120,200,255)
        TEXT_COLOR = (255,255,255)
        QUEST_CIRCLE = (255,255,120)
        QUEST_TEXT = (200,180,0)
        panel_rect = pygame.Rect(x, y, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, PANEL_BG, panel_surf.get_rect(), border_radius=16)
        grad = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        for i in range(panel_h//2):
            alpha = max(0, 60 - i*3)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,panel_w,1))
        grad_mask = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=16)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        panel_surf.blit(grad, (0,0))
        pygame.draw.rect(panel_surf, PANEL_BORDER, panel_surf.get_rect(), 2, border_radius=16)
        screen.blit(panel_surf, panel_rect.topleft)
        left_btn_rect = pygame.Rect(panel_rect.left+2, panel_rect.centery-arrow_w//2, arrow_w, arrow_w)
        right_btn_rect = pygame.Rect(panel_rect.right-arrow_w-2, panel_rect.centery-arrow_w//2, arrow_w, arrow_w)
        pygame.draw.circle(screen, ARROW_BG, left_btn_rect.center, arrow_w//2)
        pygame.draw.polygon(screen, ARROW_FG, [
            (left_btn_rect.left+7, left_btn_rect.centery),
            (left_btn_rect.right-5, left_btn_rect.top+5),
            (left_btn_rect.right-5, left_btn_rect.bottom-5)
        ])
        pygame.draw.circle(screen, ARROW_BG, right_btn_rect.center, arrow_w//2)
        pygame.draw.polygon(screen, ARROW_FG, [
            (right_btn_rect.right-7, right_btn_rect.centery),
            (right_btn_rect.left+5, right_btn_rect.top+5),
            (right_btn_rect.left+5, right_btn_rect.bottom-5)
        ])
        max_cards_width = panel_w - 2*arrow_w - 16
        total_cards_width = visible*card_w + (visible-1)*gap
        if total_cards_width > max_cards_width:
            gap = max(2, (max_cards_width - visible*card_w)//(visible-1))
        start_x = panel_rect.left + arrow_w + 8
        card_rects = []
        # Показываем 5 уровней вокруг текущего
        center = self.current_global_level
        first = max(1, center-2)
        last = center+2
        for i, lvl in enumerate(range(first, last+1)):
            zone_name, lvl_in_zone, zone_idx = self.get_level_info(lvl)
            x_card = start_x + i*(card_w+gap)
            card_rect = pygame.Rect(x_card, panel_rect.top+2, card_w, card_h)
            card_rects.append((lvl, card_rect))
            is_active = (lvl == self.current_global_level)
            color = CARD_BG_ACTIVE if is_active else CARD_BG
            border = CARD_BORDER_ACTIVE if is_active else CARD_BORDER
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, color, card_surf.get_rect(), border_radius=10)
            grad = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            for j in range(card_h//2):
                alpha = max(0, 60 - j*3)
                pygame.draw.rect(grad, (255,255,255,alpha), (0,j,card_w,1))
            grad_mask = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=10)
            grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
            card_surf.blit(grad, (0,0))
            pygame.draw.rect(card_surf, border, card_surf.get_rect(), 2, border_radius=10)
            screen.blit(card_surf, card_rect.topleft)
            num_text = self.font.render(f"{zone_idx+1}-{lvl_in_zone}", True, TEXT_COLOR)
            screen.blit(num_text, (card_rect.centerx-num_text.get_width()//2, card_rect.bottom-13))
            if is_active:
                pygame.draw.polygon(screen, (180,220,255), [
                    (card_rect.centerx-5, card_rect.top-8),
                    (card_rect.centerx+5, card_rect.top-8),
                    (card_rect.centerx, card_rect.top-1)
                ])
        zone_name, lvl_in_zone, zone_idx = self.get_level_info(self.current_global_level)
        text = self.big_font.render(f"{COSMIC_ZONES[zone_idx%len(COSMIC_ZONES)]} ур. {zone_idx+1}-{lvl_in_zone}", True, TEXT_COLOR)
        screen.blit(text, (panel_rect.centerx - text.get_width()//2, panel_rect.bottom + 4))
        self._last_draw_rects = {
            'panel': panel_rect,
            'left': left_btn_rect,
            'right': right_btn_rect,
            'cards': card_rects
        }

    def handle_click(self, pos):
        if not self._last_draw_rects:
            return None
        if self._last_draw_rects['left'].collidepoint(pos):
            return 'left'
        if self._last_draw_rects['right'].collidepoint(pos):
            return 'right'
        for lvl, rect in self._last_draw_rects['cards']:
            if rect.collidepoint(pos):
                return lvl
        return None

    def move_left(self):
        if self.current_global_level > 1:
            self.current_global_level -= 1

    def move_right(self):
        self.current_global_level += 1

    def set_level(self, lvl):
        if lvl >= 1:
            self.current_global_level = lvl 