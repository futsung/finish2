import pygame
import os
from board import Board
from utils import ImageManager, HealthBar, StatusBar
from typing import Optional, Dict, Tuple, List

class GameManager:
    def __init__(self) -> None:
        """
        初始化遊戲的相關參數與模組。
        """
        self.screen_width: int = 720
        self.screen_height: int = 800
        self.rows: int = 5
        self.cols: int = 6
        self.tile_size: int = 100
        self.fps: int = 60

        # 初始化 Pygame
        pygame.init()
        pygame.mixer.init()

        # 建立畫布
        self.screen: pygame.Surface = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("行人地獄")
        self.clock: pygame.time.Clock = pygame.time.Clock()

        # 加載圖片與音效
        self.image_paths: Dict[str, str] = self._get_image_paths()
        self.images: Dict[str, pygame.Surface] = ImageManager.load_images(
            self.image_paths, self.tile_size, self.screen_width, self.screen_height
        )
        self.match_sound: Optional[pygame.mixer.Sound] = self._load_sound("music/caraccident.mp3")
        self._initialize_music("music/bgm.mp3")

        # 遊戲核心模組
        self.board: Board = Board(self.rows, self.cols, self.tile_size)
        self.level: int = 1
        self.traffic_tickets: int = 0
        self.combo: int = 0

        # 敵人參數
        self.enemies: List[str] = ["man", "old_woman", "kid_and_dog"]
        self.enemy_health: List[int] = [150, 250, 500]
        self.enemy_sizes: List[Tuple[int, int]] = [(150, 200), (250, 220), (150, 200)]
        self.current_enemy_index: int = 0
        self.max_health: int = self.enemy_health[self.current_enemy_index]
        self.health: int = self.max_health
        self.enemy_x: int = -self.enemy_sizes[self.current_enemy_index][0]  # 起始位置
        self.enemy_y: int = 31  # 與原始設定一致
        self.enemy_speed: float = 1.0  # 第一關初始速度較快

        # 控制參數
        self.running: bool = True
        self.dragging: bool = False
        self.start_pos: Optional[Tuple[int, int]] = None

    def _get_image_paths(self) -> Dict[str, str]:
        """
        設置圖片資源路徑。
        """
        base_dir: str = os.path.dirname(__file__)
        return {
            "car": os.path.join(base_dir, "Image", "car.png"),
            "scooter": os.path.join(base_dir, "Image", "scooter.png"),
            "bus": os.path.join(base_dir, "Image", "bus.png"),
            "train": os.path.join(base_dir, "Image", "train.png"),
            "bike": os.path.join(base_dir, "Image", "bike.jpg"),
            "background": os.path.join(base_dir, "Image", "background.jpg"),
            "man": os.path.join(base_dir, "Image", "man.png"),
            "old_woman": os.path.join(base_dir, "Image", "old_woman.png"),
            "kid_and_dog": os.path.join(base_dir, "Image", "kid_and_dog.png"),
            "victory": os.path.join(base_dir, "Image", "victory.jpg"),
            "start_background": os.path.join(base_dir, "Image", "alivinghell.jpg"),
            "lose": os.path.join(base_dir, "Image", "lose.jpg")
        }

    def _initialize_music(self, music_path: str) -> None:
        """
        初始化背景音樂。
        """
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        else:
            print(f"Error: Music file not found at {music_path}")

    def _load_sound(self, sound_path: str) -> Optional[pygame.mixer.Sound]:
        """
        加載音效檔案。
        """
        if os.path.exists(sound_path):
            return pygame.mixer.Sound(sound_path)
        else:
            print(f"Error: Sound file not found at {sound_path}")
            exit()

    def show_start_screen(self) -> None:
        """
        顯示起始畫面。
        """
        start_background: pygame.Surface = pygame.image.load(self.image_paths["start_background"])
        start_background = pygame.transform.scale(start_background, (self.screen_width, self.screen_height))
        UIManager.show_start_screen(self.screen, start_background)

    def show_summary(self, failed: bool = False) -> None:
        """
        顯示結算畫面。
        """
        UIManager.show_summary(self.screen, self.traffic_tickets, self.images, failed)

    def main_loop(self) -> None:
        """
        遊戲主循環。
        """
        self.show_start_screen()

        while self.running:
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.images["background"], (0, 0))  # 背景圖

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.start_pos = pygame.mouse.get_pos()
                    self.dragging = True
                    self.board.handle_drag(self.start_pos)

                if event.type == pygame.MOUSEMOTION and self.dragging:
                    self.board.continue_drag(pygame.mouse.get_pos())

                if event.type == pygame.MOUSEBUTTONUP:
                    self.dragging = False
                    self.board.end_drag()
                    matches = self.board.check_matches()
                    if matches:
                        self.match_sound.play()
                        self.combo += 1
                        damage: int = len(matches) * 10
                        self.health -= damage
                        self.traffic_tickets += damage
                        if self.health <= 0:
                            self.level += 1
                            if self.level > len(self.enemies):
                                self.show_summary()
                                self.running = False
                            else:
                                self.current_enemy_index = self.level - 1
                                self.health = self.enemy_health[self.current_enemy_index]
                                self.max_health = self.health
                                if self.level == 2:
                                    self.enemy_speed -= 0.3  # 第二關速度
                                elif self.level == 3:
                                    self.enemy_speed += 0.1  # 第三關速度
                                else:
                                    self.enemy_speed += 0.5  # 提升速度
                                self.enemy_x = -self.enemy_sizes[self.current_enemy_index][0]  # 重置敵人位置
                        self.board.apply_gravity()

            # 更新敵人位置
            self.enemy_x += self.enemy_speed
            if self.enemy_x > self.screen_width:  # 敵人走出畫布右邊
                gameover_background: pygame.Surface = pygame.image.load(self.image_paths["lose"])
                gameover_background = pygame.transform.scale(gameover_background, (self.screen_width, self.screen_height))
                self.screen.blit(gameover_background, (0, 0))
                pygame.display.flip()
                waiting: bool = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                            self.__init__()  # 重置遊戲
                            self.main_loop()
                            return
                        elif event.type == pygame.QUIT:
                            waiting = False
                            self.running = False

            # 繪製敵人
            enemy_image: pygame.Surface = pygame.transform.scale(
                self.images[self.enemies[self.current_enemy_index]],
                self.enemy_sizes[self.current_enemy_index]
            )
            self.screen.blit(enemy_image, (self.enemy_x, self.enemy_y))
            HealthBar.draw(
                self.screen, self.health, self.max_health, self.enemy_x, self.enemy_y - 20,
                self.enemy_sizes[self.current_enemy_index][0], 10
            )

            # 繪製遊戲盤面與狀態欄
            self.board.draw(self.screen, self.images)
            StatusBar.draw(self.screen, self.traffic_tickets, self.combo, self.level)

            # 更新畫面
            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()


class UIManager:
    @staticmethod
    def show_start_screen(screen: pygame.Surface, background_image: pygame.Surface) -> None:
        font_button: pygame.font.Font = pygame.font.Font(None, 48)
        button_text: pygame.Surface = font_button.render("START", True, (0, 0, 0))
        button_rect: pygame.Rect = pygame.Rect(260, 400, 200, 80)

        screen.blit(background_image, (0, 0))
        pygame.draw.rect(screen, (255, 255, 255), button_rect)
        screen.blit(
            button_text,
            (button_rect.centerx - button_text.get_width() // 2, button_rect.centery - button_text.get_height() // 2)
        )
        pygame.display.flip()

        waiting: bool = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
                    waiting = False

    @staticmethod
    def show_summary(screen: pygame.Surface, traffic_tickets: int, images: Dict[str, pygame.Surface], failed: bool = False) -> None:
        screen.fill((0, 0, 0))
        if failed:
            font: pygame.font.Font = pygame.font.Font(None, 72)
            text: pygame.Surface = font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, screen.get_height() // 2 - text.get_height() // 2))
        else:
            screen.blit(images["victory"], (0, 0))
            font: pygame.font.Font = pygame.font.Font(None, 72)
            text_number: pygame.Surface = font.render(f"{traffic_tickets}", True, (255, 255, 255))
            number_rect: pygame.Rect = text_number.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
            screen.blit(text_number, number_rect)
        pygame.display.flip()
        pygame.time.wait(5000)


if __name__ == "__main__":
    game: GameManager = GameManager()
    game.main_loop()