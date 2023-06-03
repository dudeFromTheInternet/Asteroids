import random
import pygame
from pygame_widgets.button import Button
from pygame import Color, Vector2
from scripts.utils import get_random_position, print_text, load_sprite, \
    get_random_size, draw_buttons
from scripts.models import Asteroid, Spaceship, Ufo, Bullet
from enum import Enum


class GameState(Enum):
    MAIN_MENU = 0,
    GAME = 1,
    PAUSE = 2
    WIN_MENU = 3,
    LOSE_MENU = 4,
    QUIT = 5,
    ENTER_NAME = 6,
    LEADERBOARD = 7


class Asteroids:
    MIN_ASTEROID_DISTANCE = 250
    MIN_UFO_DISTANCE = 250
    FRAMERATE = 60

    def __init__(self):
        init_pygame()
        self.screen = pygame.display.set_mode((1500, 700))
        self.default_text_pos = Vector2(self.screen.get_width() // 2,
                                        self.screen.get_height() // 12 * 6)
        self.default_button_pos = Vector2(self.screen.get_width() // 2,
                                          self.screen.get_height() // 12 * 7)
        self.default_button_size = Vector2(300, 50)
        self.default_delay = Vector2(0, self.screen.get_height() // 12)
        self.default_input_field_size = Vector2(800, 60)
        self.default_input_field_rect_pos = (self.default_text_pos
                                             - self.default_delay // 2
                                             - self.default_input_field_size
                                             // 2,
                                             self.default_input_field_size)
        self.clock = pygame.time.Clock()
        self.current_frame = 0
        self.font = pygame.font.Font(None, 64)
        self.nickname = "Default"
        self.is_default_nickname = True
        self.leaderboard = {}
        self.level = 1
        self.ufo_quantity = 0

        self.game_state = GameState.MAIN_MENU
        self.asteroids = []
        self.bullets = []
        self.bullets_ufo = []
        self.ufo = []
        self.standard_spaceship_position = Vector2(
            self.screen.get_width() / 2,
            self.screen.get_height() / 2
        )
        self.spaceship = Spaceship(self.standard_spaceship_position,
                                   self.bullets.append)
        self._generate_enemies()
        self._fill_leaderboard("record_table.txt")

    def start_game(self):
        while self.game_state is not GameState.QUIT:
            match self.game_state:
                case GameState.MAIN_MENU:
                    self._show_main_menu()
                case GameState.ENTER_NAME:
                    self._show_input_field()
                case GameState.LEADERBOARD:
                    self._show_leaderboard()
                case GameState.GAME:
                    self._handle_input()
                    self._process_game_logic()
                    self._draw()
                case GameState.PAUSE:
                    self._pause_game()
                case GameState.WIN_MENU:
                    self._record_score("record_table.txt")
                    self._show_win_menu()
                case GameState.LOSE_MENU:
                    self._record_score("record_table.txt")
                    self._show_lose_menu()
        else:
            quit()

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_state = GameState.QUIT
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = GameState.PAUSE
                elif self.spaceship.is_alive and event.key == pygame.K_SPACE:
                    self.spaceship.shoot()

        is_key_pressed = pygame.key.get_pressed()

        if self.spaceship.is_alive:
            if is_key_pressed[pygame.K_RIGHT]:
                self.spaceship.rotate(clockwise=True)
            elif is_key_pressed[pygame.K_LEFT]:
                self.spaceship.rotate(clockwise=False)
            if is_key_pressed[pygame.K_UP]:
                self.spaceship.accelerate()
            else:
                self.spaceship.not_accelerate()

    def _process_game_logic(self):
        self._move_objects()
        self._process_bullets_logic()
        if self.ufo_quantity > 0:
            self._generate_ufo()
        self._process_ufo_logic()
        self._check_bullets_collision()
        self._check_ufo_collision()
        self._check_asteroids_collision()
        self._check_spaceship_collision()
        self._check_game_state()

    def _draw(self):
        self.screen.fill(Color("black"))
        pygame.display.set_caption("Asteroids")
        if self.spaceship.is_alive:
            heart_image = load_sprite("heart")
            heart_rect = heart_image.get_rect()
            for i in range(self.spaceship.lives):
                self.screen.blit(heart_image, (10 + i * heart_rect.width, 10))

            print_text(self.screen, f'Level {self.level}',
                       pygame.font.Font(None, 28),
                       Vector2(48, 50), (150, 150, 150))
            print_text(self.screen, f'Score: {self.spaceship.score}',
                       pygame.font.Font(None, 32),
                       Vector2(self.screen.get_size()[0] // 2, 20))
            print_text(self.screen, self.nickname, pygame.font.Font(None, 32),
                       Vector2(self.screen.get_size()[0] // 2, 50),
                       (150, 150, 150))

        for game_object in self._get_game_objects():
            game_object.draw(self.screen)

        pygame.display.flip()
        self.clock.tick(self.FRAMERATE)
        self.current_frame += 1

    def _generate_enemies(self):
        match self.level:
            case 1:
                self._generate_asteroids(1)
                self.ufo_quantity = 1
            case 2:
                self._generate_asteroids(4)
                self.ufo_quantity = 2
            case 3:
                self._generate_asteroids(6)
                self.ufo_quantity = 3

    def _generate_asteroids(self, asteroids_quantity):
        for _ in range(asteroids_quantity):
            while True:
                position = get_random_position(self.screen)
                if position.distance_to(self.spaceship.position) \
                        > self.MIN_ASTEROID_DISTANCE:
                    break

            self.asteroids.append(Asteroid(position, self.asteroids.append,
                                           get_random_size(0.8, 1.5)))

    def _get_game_objects(self):
        game_objects = [*self.asteroids, *self.bullets, *self.ufo,
                        *self.bullets_ufo]
        if self.spaceship.is_alive:
            game_objects.append(self.spaceship)

        return game_objects

    def _check_spaceship_collision(self):
        for asteroid in self.asteroids[:]:
            self._spaceship_wrecked_logic(asteroid, True)
        for bullet in self.bullets_ufo[:]:
            self._spaceship_wrecked_logic(bullet, False)
        for ufo in self.ufo[:]:
            self._spaceship_wrecked_logic(ufo, True)

    def _spaceship_wrecked_logic(self, collision_object, teleport):
        if self.spaceship.is_alive \
                and collision_object.collides_with(self.spaceship):
            if teleport:
                self.spaceship.position = self.standard_spaceship_position
            if type(collision_object) is Bullet:
                self.bullets_ufo.remove(collision_object)
            self.spaceship.lives -= 1
            self._check_death()

    def _process_bullets_logic(self):
        for bullet in self.bullets[:]:
            if not self.screen.get_rect().collidepoint(bullet.position):
                self.bullets.remove(bullet)

    def _check_bullets_collision(self):
        for bullet in self.bullets[:]:
            for bullet_ufo in self.bullets_ufo[:]:
                if bullet.collides_with(bullet_ufo):
                    self.bullets.remove(bullet)
                    self.bullets_ufo.remove(bullet_ufo)
                    break

    def _check_ufo_collision(self):
        for bullet in self.bullets[:]:
            for ufo in self.ufo[:]:
                if bullet.collides_with(ufo):
                    self.spaceship.score += 200
                    self.ufo.remove(ufo)
                    self.bullets.remove(bullet)
                    break

    def _check_asteroids_collision(self):
        for asteroid in self.asteroids[:]:
            for bullet in self.bullets[:]:
                if asteroid.collides_with(bullet):
                    self.asteroids.remove(asteroid)
                    self.bullets.remove(bullet)
                    asteroid.split(self.spaceship)
                    break

    def _generate_ufo(self):
        directions = {0: (0, 1),
                      1: (1, 0),
                      2: (-1, 0),
                      3: (0, -1)}
        (random_x, random_y) = [random.randrange(self.screen.get_width()),
                                random.randrange(self.screen.get_height())]
        ufo_spawn = {(0, 1): (random_x, 0),
                     (1, 0): (0, random_y),
                     (-1, 0): (self.screen.get_width() - 1, random_y),
                     (0, -1): (random_x, self.screen.get_height() - 1)}
        if (self.current_frame % (random.randrange(8, 12)
                                  * self.FRAMERATE)) == self.FRAMERATE * 3:
            direction = directions[random.randrange(4)]
            position = ufo_spawn[direction]
            self.ufo.append(Ufo(position, direction, self.bullets_ufo.append))
            self.ufo_quantity -= 1

    def _process_ufo_logic(self):
        if self.ufo:
            for ufo in self.ufo[:]:
                if ufo.current_frame % ufo.BULLET_FREQUENCY == 0:
                    ufo.shoot()
                if not self.screen.get_rect().collidepoint(ufo.position):
                    self.ufo.remove(ufo)

    def _move_objects(self):
        for game_object in self._get_game_objects():
            game_object.move(self.screen)

    def _check_death(self):
        if self.spaceship.lives == 0:
            self.spaceship.is_alive = False

    def __draw_label(self, text, color):
        print_text(self.screen, text, self.font,
                   self.default_text_pos, color=color)

    def _show_main_menu(self):
        pygame.display.set_caption("Menu")
        self.screen.fill(Color("black"))
        menu_buttons = [Button(self.screen,
                               *(self.default_button_pos
                                 - self.default_button_size // 2),
                               *self.default_button_size,
                               text='PLAY', fontSize=40,
                               inactiveColour=(255, 0, 0),
                               radius=20,
                               onClick=lambda:
                               self._change_game_state(GameState.ENTER_NAME)),
                        Button(self.screen,
                               *(self.default_button_pos
                                 + self.default_delay
                                 - self.default_button_size // 2),
                               *self.default_button_size,
                               text='LEADERBOARD', fontSize=40,
                               inactiveColour=(255, 0, 0),
                               radius=20,
                               onClick=lambda:
                               self._change_game_state(
                                   GameState.LEADERBOARD))]
        while self.game_state is GameState.MAIN_MENU:
            self.__draw_label("THE ASTEROIDS", "white")
            draw_buttons(menu_buttons)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_state = GameState.QUIT
                elif event.type == pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_TAB:
                            self.game_state = GameState.LEADERBOARD

    def _pause_game(self):
        pygame.display.set_caption("Paused")
        buttons = [Button(self.screen,
                          *(self.default_button_pos -
                            self.default_button_size // 2),
                          *self.default_button_size,
                          text='MAIN MENU', fontSize=40,
                          inactiveColour=(155, 155, 155),
                          radius=20,
                          onClick=lambda:
                          self._change_game_state(GameState.MAIN_MENU))]
        while self.game_state is GameState.PAUSE:
            self.__draw_label("PAUSED", "red")
            draw_buttons(buttons)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_state = GameState.QUIT
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.display.set_caption("Asteroids")
                        self.game_state = GameState.GAME
                        break

    def _show_input_field(self):
        pygame.display.set_caption("Enter your name")
        self.screen.fill(Color("black"))
        buttons = [Button(self.screen,
                          *(self.default_button_pos -
                            self.default_button_size // 2),
                          *self.default_button_size,
                          text='START', fontSize=40,
                          inactiveColour=(255, 0, 0),
                          radius=20,
                          onClick=lambda:
                          self._change_game_state(GameState.GAME)),
                   Button(self.screen,
                          *(self.default_button_pos
                            - self.default_button_size // 2
                            + self.default_delay),
                          *self.default_button_size,
                          text='TO MENU', fontSize=40,
                          inactiveColour=(255, 0, 0),
                          radius=20,
                          onClick=lambda:
                          restart_game(self, True))
                   ]
        while self.game_state is GameState.ENTER_NAME:
            draw_buttons(buttons)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_state = GameState.QUIT
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.nickname = self.nickname[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.game_state = GameState.GAME
                        return
                    elif len(self.nickname) <= 20:
                        if self.is_default_nickname:
                            self.nickname = ""
                            self.is_default_nickname = False
                        self.nickname += event.unicode
            print_text(self.screen, "Enter your name", self.font,
                       self.default_text_pos - self.default_delay * 1.8,
                       Color("white"))
            pygame.draw.rect(self.screen, (156, 156, 156),
                             self.default_input_field_rect_pos)
            print_text(self.screen, self.nickname, self.font,
                       self.default_text_pos - self.default_delay // 2,
                       Color("white"))

    def _show_leaderboard(self):
        pygame.display.set_caption("Leaderboard")
        self.screen.fill(Color("black"))
        menu_buttons = [Button(self.screen,
                               *(self.default_button_pos
                                 + self.default_delay * 4
                                 - self.default_button_size // 2),
                               *self.default_button_size,
                               text='TO MENU', fontSize=40,
                               inactiveColour=(255, 0, 0),
                               radius=20,
                               onClick=lambda:
                               self._change_game_state(GameState.MAIN_MENU))]
        print_text(self.screen, "Leaderboard", pygame.font.Font(None, 90),
                   (self.screen.get_size()[0] // 2, self.default_delay[1]),
                   Color("RED"))
        i = 1.5
        for player, score in self.leaderboard.items():
            i += 1
            if i < 10:
                print_text(self.screen, f"{player}: {score}", self.font,
                           Vector2(self.screen.get_size()[0] // 2,
                                   self.default_delay[1] * i),
                           Color("white"))

        pygame.display.flip()

        while self.game_state is GameState.LEADERBOARD:
            draw_buttons(menu_buttons)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_state = GameState.QUIT
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        self.game_state = GameState.MAIN_MENU
                        return

    def _show_win_menu(self):
        pygame.display.set_caption("WIN")
        self.screen.fill(Color("black"))
        win_buttons = [Button(self.screen,
                              *(self.default_button_pos -
                                self.default_button_size // 2),
                              *self.default_button_size,
                              text='RESTART', fontSize=40,
                              inactiveColour=(255, 0, 0),
                              radius=20,
                              onClick=lambda: restart_game(self, False)),
                       Button(self.screen,
                              *(self.default_button_pos
                                - self.default_button_size // 2
                                + self.default_delay),
                              *self.default_button_size,
                              text='TO MENU', fontSize=40,
                              inactiveColour=(255, 0, 0),
                              radius=20,
                              onClick=lambda:
                              restart_game(self, True))
                       ]
        while self.game_state is GameState.WIN_MENU:
            self.__draw_label("YOU WIN", "green")
            draw_buttons(win_buttons)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_state = GameState.QUIT
                    return

    def _show_lose_menu(self):
        pygame.display.set_caption("LOSE")
        self.screen.fill(Color("black"))
        lose_buttons = [Button(self.screen,
                               *(self.default_button_pos -
                                 self.default_button_size // 2),
                               *self.default_button_size,
                               text='RESTART', fontSize=40,
                               inactiveColour=(255, 0, 0),
                               radius=20,
                               onClick=lambda: restart_game(self, False)),
                        Button(self.screen,
                               *(self.default_button_pos
                                 - self.default_button_size // 2
                                 + self.default_delay),
                               *self.default_button_size,
                               text='TO MENU', fontSize=40,
                               inactiveColour=(255, 0, 0),
                               radius=20,
                               onClick=lambda:
                               restart_game(self, True))
                        ]
        while self.game_state is GameState.LOSE_MENU:
            self.__draw_label("YOU LOSE", "red")
            draw_buttons(lose_buttons)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_state = GameState.QUIT
                    return

    def _record_score(self, filename):
        if self.nickname not in self.leaderboard:
            self.leaderboard[self.nickname] = self.spaceship.score
        if self.spaceship.score > self.leaderboard[self.nickname]:
            self.leaderboard[self.nickname] = self.spaceship.score
        self.leaderboard = dict(sorted(self.leaderboard.items(),
                                       key=lambda item: item[1], reverse=True))
        with open(filename, "w") as record_table:
            for player, score in self.leaderboard.items():
                record_table.write(f"{player}: {score} \n")

    def _fill_leaderboard(self, filename):
        with open(filename, "r") as record_table:
            for string in record_table:
                if not string.strip():
                    return
                player = string.split(":")[0]
                score = int(string.split(":")[1][1:])
                self.leaderboard[player] = score

    def _check_game_state(self):
        if not self.spaceship.is_alive:
            self.game_state = GameState.LOSE_MENU
        elif not self.asteroids and not self.ufo and self.level == 4:
            self.game_state = GameState.WIN_MENU
        elif not self.asteroids and not self.ufo and self.level < 4:
            self.spaceship.position = self.standard_spaceship_position
            self.spaceship.direction = Vector2(0, -1)
            self.bullets.clear()
            self.bullets_ufo = []
            self.level += 1
            self._generate_enemies()

    def _change_game_state(self, game_state):
        match game_state:
            case GameState.MAIN_MENU:
                restart_game(self, True)
            case GameState.GAME:
                if len(self.nickname) > 0:
                    self.game_state = GameState.GAME
            case _:
                self.game_state = game_state


def init_pygame():
    pygame.init()
    pygame.display.set_caption("Asteroids")


def restart_game(asteroids, to_menu):
    nickname = asteroids.nickname
    asteroids.__init__()
    if not to_menu:
        asteroids.nickname = nickname
        asteroids.game_state = GameState.GAME
    else:
        asteroids.game_state = GameState.MAIN_MENU
