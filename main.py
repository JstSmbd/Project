import random

import pygame

from PIL import Image
from random import choices, choice, randint, uniform

STRUCTURES_RANGE = [20, 50]  # from: _ to: _
EXTENDED_RANGE = [-5, 5]  # from: _ to: _
ENEMIES_MULTI_RANGE = [0.1, 0.3]  # from: _ to: _
start = {(0, 0): 1, (1, 0): 1, (2, 0): 1, (1, 1): 1, (0, 1): 1, (0, 2): 1, (-1, 1): 1, (-1, 0): 1,
         (-2, 0): 1, (-1, -1): 1, (0, -1): 1, (0, -2): 1, (1, -1): 1}


class Character:
    def __init__(self, hp, pos, damage):
        self.hp = hp
        self.pos = pos
        self.damage = damage


class Player(Character):
    def __init__(self, max_hp, pos, damage):
        super().__init__(max_hp, pos, damage)
        self.max_hp = max_hp
        self.hp = max_hp
        self.floor = 1
        self.kills = 0

    def pressed_key(self, event):
        if event[pygame.K_w] or event[pygame.K_s] or event[pygame.K_a] or event[pygame.K_d]:
            self.move(event)
        elif event[pygame.K_UP] or event[pygame.K_DOWN] or event[pygame.K_LEFT] or event[
            pygame.K_RIGHT]:
            self.attack(event)
        if self.hp <= 0:
            global state, focused, drag_offset, size
            state = "end window"
            focused = False
            drag_offset = [self.pos[0] * size, self.pos[1] * size]
        elif event[pygame.K_e] and self.pos == exit_ladder:
            make_new_level()
            self.floor += 1

    def move(self, event):
        for args in [[[0, -1], pygame.K_w], [[0, 1], pygame.K_s],
                     [[-1, 0], pygame.K_a], [[1, 0], pygame.K_d]]:
            if check_condition([1, 1, 0, 1], pos=(self.pos[0] + args[0][0],
                                                  self.pos[1] + args[0][1]),
                               event=event, key=args[1]):
                self.pos = (self.pos[0] + args[0][0], self.pos[1] + args[0][1])
                [en.make_step() for en in enemies]
                global can_go_next
                can_go_next = False
                break

    def attack(self, event):
        for args in [[[0, -1], pygame.K_UP], [[0, 1], pygame.K_DOWN],
                     [[-1, 0], pygame.K_LEFT], [[1, 0], pygame.K_RIGHT]]:
            if check_condition([1, 0, 0, 1], pos=(self.pos[0] + args[0][0],
                                                  self.pos[1] + args[0][1]),
                               event=event, key=args[1]):
                for en in enemies:
                    if en.pos == (self.pos[0] + args[0][0], self.pos[1] + args[0][1]):
                        en.hp -= self.damage
                for en in [en for en in enemies if en.hp <= 0]:
                    enemies.remove(en)
                    self.kills += 1
                [en.make_step() for en in enemies]
                global can_go_next
                can_go_next = False
                break


class BasicEnemy(Character):
    def __init__(self, hp, damage, pos, found_radius, view, moves_per_step):
        super().__init__(hp, pos, damage)
        self.moves_per_step = moves_per_step
        self.cells_of_view = sphere_of_cells(view)
        self.found_radius = found_radius

    def make_step(self):
        if abs(self.pos[0] - player.pos[0]) + abs(self.pos[1] - player.pos[1]) <= self.found_radius:
            lb = {}
            for cell in self.cells_of_view:
                if (self.pos[0] + cell[0], self.pos[1] + cell[1]) in card:
                    lb[(self.pos[0] + cell[0], self.pos[1] + cell[1])] = 0
            result = self.find_path(lb, self.pos, player.pos)
            if result and (path := [cell for cell in result if cell != player.pos]):  # <-- path
                self.pos = path[:self.moves_per_step][-1]
            elif result is None:  # если нельзя пройти до игрока
                self.make_random_step()
            if result and len(path) < self.moves_per_step:  # если остались ходы
                player.hp -= self.damage
        else:
            self.make_random_step()

    def make_random_step(self):
        for _ in range(self.moves_per_step):
            variants = []
            for args in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
                if check_condition([1, 1], pos=(self.pos[0] + args[0], self.pos[1] + args[1])):
                    variants.append((self.pos[0] + args[0], self.pos[1] + args[1]))
            self.pos = choice(variants)

    def find_path(self, lab, start, end):
        copy_lab = lab.copy()
        self.find_lab_tuples([start], copy_lab)
        now = end
        path = []
        while now != start:
            path.append(now)
            now = copy_lab.get(now, None)
            if not now:
                path = None
                break
        if path:
            path.reverse()
        return path

    def find_lab_tuples(self, nexts, lb):
        new_nexts = []
        for now in nexts:
            for args in [[-1, 0], [1, 0], [0, -1], [0, 1]]:
                if check_condition([1, 1, 1], pos=(now[0] + args[0], now[1] + args[1]), flat=lb):
                    lb[now[0] + args[0], now[1] + args[1]] = now
                    new_nexts.append((now[0] + args[0], now[1] + args[1]))
        if new_nexts:
            self.find_lab_tuples(new_nexts, lb)


class FastEnemy(BasicEnemy):
    def __init__(self, hp, damage, pos, found_radius, view, moves_per_step):
        super().__init__(hp, damage, pos, found_radius, view, moves_per_step)


def check_condition(variants, pos=None, flat=None, event=None, key=None):
    if flat is None:
        flat = card
    flag = True
    if len(variants) >= 1 and variants[0]:
        flag = flag and pos in flat
    if len(variants) >= 2 and variants[1]:
        flag = flag and all([pos != en.pos for en in enemies])
    if len(variants) >= 3 and variants[2]:
        flag = flag and type(flat[pos]) != tuple
    if len(variants) >= 4 and variants[3]:
        flag = flag and event[key]
    return flag


def load_new_place(filename):
    new = []
    im = Image.open(filename)
    pixels = im.load()
    x, y = im.size
    firsts = [0, 0]
    find_first = pixels[0, 0] != (0, 0, 0, 255)
    for i in range(x):
        for j in range(y):
            if pixels[i, j] == (0, 0, 0, 255) or pixels[i, j] == (0, 0, 0):
                if find_first:
                    find_first = False
                    firsts = [i, j]
                new.append([i - firsts[0], j - firsts[1]])
    return new


def rotate(place, to):
    if to == 0:
        return place
    elif to == 1:
        return [[coord[1], coord[0]] for coord in place]
    elif to == 2:
        return [[-coord[0], -coord[1]] for coord in place]
    elif to == 3:
        return [[-coord[1], -coord[0]] for coord in place]


def sphere_of_cells(diametr):
    cells_of_diametr = []
    for i in range(-(diametr // 2), diametr // 2 + 1):
        for j in range(-(diametr // 2 - abs(i)), diametr // 2 - abs(i) + 1):
            cells_of_diametr.append((j, i))
    return cells_of_diametr


def make_new_level():
    global card, exit_ladder, enemies, focused, chest, width_loading, height_loading

    structures = randint(STRUCTURES_RANGE[0], STRUCTURES_RANGE[1])
    extended = uniform(EXTENDED_RANGE[0], EXTENDED_RANGE[1])
    card = start.copy()
    for i in range(structures):
        draw_loading_bar(i / structures)
        global percent
        percent = i / structures * 100, 2
        cells = []
        for cell in card:
            if (cell[0] + 1, cell[1]) not in card:
                cells.append((cell[0] + 1, cell[1]))
            if (cell[0] - 1, cell[1]) not in card:
                cells.append((cell[0] - 1, cell[1]))
            if (cell[0], cell[1] + 1) not in card:
                cells.append((cell[0], cell[1] + 1))
            if (cell[0], cell[1] - 1) not in card:
                cells.append((cell[0], cell[1] - 1))

        first = \
            choices(cells, weights=[pow((abs(cell[0]) + abs(cell[1])), extended) for cell in cells])[
                0]
        for coord in rotate(choice(places), randint(0, 3)):
            card[first[0] + coord[0], first[1] + coord[1]] = 1

    max_cell = (0, 0)
    for key in card:
        if abs(key[0]) + abs(key[1]) > abs(max_cell[0]) + abs(max_cell[1]):
            max_cell = key
    exit_ladder = choice([(max_cell[0] + cell[0], max_cell[1] + cell[1])
                          for cell in sphere_of_cells(20)
                          if (max_cell[0] + cell[0], max_cell[1] + cell[1]) in card])

    enemies = []
    flat = card.copy()
    flat2 = flat.copy()
    [flat.pop(cell) for cell in sphere_of_cells(20) if cell in flat]
    numb_enemies = len(flat) if \
        len(flat) < (numb_enemies :=
                     int(structures * uniform(ENEMIES_MULTI_RANGE[0],
                                              ENEMIES_MULTI_RANGE[1]))) else numb_enemies
    for i in range(numb_enemies):
        cell = choice(list(flat))
        enemies.append(choices([BasicEnemy(30, 1, cell, 5, 10, 1), FastEnemy(20, 1, cell, 7, 15, 3)],
                               weights=[10, player.floor])[0])
        flat.pop(cell)

    flat2.pop((0, 0))
    flat2.pop(exit_ladder)
    chest = choices(list(flat2), weights=[pow(abs(cell[0] - exit_ladder[0]) +
                                              abs(cell[1] - exit_ladder[1]) + abs(cell[0]) +
                                              abs(cell[1]), 1.5) for cell in flat2])[0]

    focused = True
    player.pos = (0, 0)


def draw_main_game():
    global first, size, drag_offset, drag, focused, can_go_next, time_for_next, card
    screen.fill('black')
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            end()
        elif event.type == pygame.MOUSEWHEEL and (size != 1 or event.y != -1) and \
                (size != 100 or event.y != 1):
            size += event.y
            drag_offset = [round(drag_offset[0] * (size / (size - event.y))),
                           round(drag_offset[1] * (size / (size - event.y)))]
        elif event.type == pygame.MOUSEBUTTONDOWN:
            drag = True
        elif event.type == pygame.MOUSEBUTTONUP:
            drag = False
        elif event.type == pygame.MOUSEMOTION and drag:
            drag_offset = [drag_offset[i] - event.rel[i] for i in range(2)]
            focused = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                focused = not focused
                drag_offset = [player.pos[0] * size, player.pos[1] * size]
        elif event.type == MYEVENTTYPE:
            if not can_go_next:
                time_for_next += timer_speed
            if time_for_next >= time_rest:
                can_go_next = True
                time_for_next = 0
        if pygame.key.get_pressed() and can_go_next:
            player.pressed_key(pygame.key.get_pressed())

    offset = [player.pos[0] * size, player.pos[1] * size] if focused else drag_offset
    for cell in card:  # поле
        pygame.draw.rect(screen,
                         (200, 200, 200), (width // 2 + cell[0] * size - offset[0] - size // 2,
                                           height // 2 + cell[1] * size - offset[1] - size // 2,
                                           size, size), 1)
        pygame.draw.rect(screen,
                         (150, 150, 150),
                         (width // 2 + cell[0] * size + 1 - offset[0] - size // 2,
                          height // 2 + cell[1] * size + 1 - offset[1] - size // 2,
                          size - 2, size - 2))

    pygame.draw.rect(screen,
                     (128, 64, 48),
                     (width // 2 + exit_ladder[0] * size + 1 - offset[0] - size // 2,
                      height // 2 + exit_ladder[1] * size + 1 - offset[1] - size // 2,
                      size - 2, size - 2))
    pygame.draw.rect(screen, (255, 0, 255),
                     (width // 2 + chest[0] * size + 1 - offset[0] - size // 2,
                      height // 2 + chest[1] * size + 1 - offset[1] - size // 2,
                      size - 2, size - 2))

    for en in enemies:
        pygame.draw.circle(
            screen,
            {"BasicEnemy": (0, 0, 255), "FastEnemy": (255, 255, 0)}[en.__class__.__name__],
            (width // 2 + size // 2 - offset[0] + en.pos[0] * size - size // 2,
             height // 2 + size // 2 - offset[1] + en.pos[1] * size - size // 2),
            size // 2)

    if focused:
        pygame.draw.circle(screen, (255, 0, 0), (width // 2, height // 2),
                           size // 2)  # игрок
    else:
        pygame.draw.circle(screen, (255, 0, 0),
                           (width // 2 - drag_offset[0] + player.pos[0] * size,
                            height // 2 - drag_offset[1] + player.pos[1] * size),
                           size // 2)  # игрок
    pygame.draw.arc(screen, (255, 255, 0), (50, height - 100, 50, 50), 90 / 57.2958,
                    360 / 57.2958 * (time_for_next / time_rest) +
                    90 / 57.2958, 25)
    pygame.draw.arc(screen, (255, 150, 0), (50, height - 100, 50, 50), 90 / 57.2958,
                    360 / 57.2958 * (time_for_next / time_rest) +
                    90 / 57.2958, 5)  # время до следующего хода

    hp_bar_height = 200
    hp_bar_line_width = 2
    pygame.draw.rect(screen, (100, 100, 100), (10, 10, 30, hp_bar_height))
    for i in range(player.max_hp):
        pygame.draw.rect(
            screen, (255, 0, 0) if i < player.hp else (10, 10, 10),
            (12, 12 + i * ((hp_bar_height - hp_bar_line_width * (player.max_hp + 1)) /
                           player.max_hp + hp_bar_line_width), 26,
             (hp_bar_height - hp_bar_line_width * (player.max_hp + 1)) / player.max_hp))
    pygame.display.flip()


def draw_loading_bar(percent, width_lb=500, height_lb=50, text_under_lb=50):
    screen.fill("black")
    pygame.draw.rect(screen, (255, 255, 255), (
        (width - width_lb) // 2, (height - height_lb) // 2, width_lb, height_lb), 1)
    pygame.draw.rect(screen, (255, 255, 255), (
        (width - width_lb) // 2, (height - height_lb) // 2, percent * width_lb,
        height_lb))
    text = pygame.font.Font(None, 50).render(f"{round(percent * 100, 1)}%", True, (255, 255, 255))
    screen.blit(text, ((width - text.get_width()) // 2, (height - height_lb) // 2 +
                       height_lb + text_under_lb))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            end()
    pygame.display.flip()


def draw_start_window(start_window_borders=[100, 450, 900, 550]):
    global state
    screen.fill("black")
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            end()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                and start_window_borders[0] <= event.pos[0] <= start_window_borders[2] \
                and start_window_borders[1] <= event.pos[1] <= start_window_borders[3]:
            state = "main"
            make_new_level()
    pygame.draw.rect(screen, (0, 255, 0), (start_window_borders[0], start_window_borders[1],
                                           start_window_borders[2] - start_window_borders[0],
                                           start_window_borders[3] - start_window_borders[1]), 1)
    text = pygame.font.Font(None, 100).render("START", True, (0, 255, 0))
    screen.blit(text, ((width - text.get_width()) // 2, (height - text.get_height()) // 2))
    pygame.display.flip()


def draw_end_window(end_window_borders=[780, 20, 200, 400],
                    exit_button_sizes=[200, 50], text_under_end_window=20):
    global size, drag_offset, drag, focused
    screen.fill("black")
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            end()
        elif event.type == pygame.MOUSEWHEEL and (size != 1 or event.y != -1) and \
                (size != 100 or event.y != 1):
            size += event.y
            drag_offset = [round(drag_offset[0] * (size / (size - event.y))),
                           round(drag_offset[1] * (size / (size - event.y)))]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if end_window_borders[0] + end_window_borders[2] // 2 - exit_button_sizes[0] // 2 <= \
                    event.pos[0] <= end_window_borders[0] + end_window_borders[2] // 2 - \
                    exit_button_sizes[0] // 2 + exit_button_sizes[0] and end_window_borders[1] + \
                    end_window_borders[3] + text_under_end_window <= event.pos[1] <= \
                    end_window_borders[1] + end_window_borders[3] + \
                    text_under_end_window + exit_button_sizes[1]:
                end()
            drag = True
        elif event.type == pygame.MOUSEBUTTONUP:
            drag = False
        elif event.type == pygame.MOUSEMOTION and drag:
            drag_offset = [drag_offset[i] - event.rel[i] for i in range(2)]
            focused = False

    offset = [player.pos[0] * size, player.pos[1] * size] if focused else drag_offset
    for cell in card:  # поле
        pygame.draw.rect(screen,
                         (200, 200, 200), (width // 2 + cell[0] * size - offset[0] - size // 2,
                                           height // 2 + cell[1] * size - offset[1] - size // 2,
                                           size, size), 1)
        pygame.draw.rect(screen,
                         (150, 150, 150),
                         (width // 2 + cell[0] * size + 1 - offset[0] - size // 2,
                          height // 2 + cell[1] * size + 1 - offset[1] - size // 2,
                          size - 2, size - 2))

    pygame.draw.rect(screen,
                     (128, 64, 48),
                     (width // 2 + exit_ladder[0] * size + 1 - offset[0] - size // 2,
                      height // 2 + exit_ladder[1] * size + 1 - offset[1] - size // 2,
                      size - 2, size - 2))
    pygame.draw.rect(screen, (255, 0, 255),
                     (width // 2 + chest[0] * size + 1 - offset[0] - size // 2,
                      height // 2 + chest[1] * size + 1 - offset[1] - size // 2,
                      size - 2, size - 2))

    for en in enemies:
        pygame.draw.circle(
            screen,
            {"BasicEnemy": (0, 0, 255), "FastEnemy": (255, 255, 0)}[en.__class__.__name__],
            (width // 2 + size // 2 - offset[0] + en.pos[0] * size - size // 2,
             height // 2 + size // 2 - offset[1] + en.pos[1] * size - size // 2),
            size // 2)
    pygame.draw.rect(screen, (255, 255, 255), (end_window_borders[0], end_window_borders[1],
                                               end_window_borders[2], end_window_borders[3]), 1)
    pygame.draw.rect(screen, (0, 0, 0), (end_window_borders[0] + 1, end_window_borders[1] + 1,
                                         end_window_borders[2] - 2, end_window_borders[3] - 2))
    text = pygame.font.Font(None, 30).render(f"floor - {player.floor}", True, (255, 255, 255))
    screen.blit(text, (end_window_borders[0] + 10, end_window_borders[1] + 10))
    text = pygame.font.Font(None, 30).render(f"kills - {player.kills}", True, (255, 255, 255))
    screen.blit(text, (end_window_borders[0] + 10, end_window_borders[1] + 30))

    pygame.draw.rect(screen, (255, 255, 255), (end_window_borders[0] +
                                               end_window_borders[2] // 2 -
                                               exit_button_sizes[0] // 2,
                                               end_window_borders[1] +
                                               end_window_borders[3] + text_under_end_window,
                                               exit_button_sizes[0], exit_button_sizes[1]), 1)
    pygame.draw.rect(screen, (0, 0, 0), (end_window_borders[0] +
                                         end_window_borders[2] // 2 -
                                         exit_button_sizes[0] // 2 + 1,
                                         end_window_borders[1] +
                                         end_window_borders[3] + text_under_end_window + 1,
                                         exit_button_sizes[0] - 2, exit_button_sizes[1] - 2))
    text = pygame.font.Font(None, 50).render("EXIT", True, (255, 255, 255))
    screen.blit(text, (end_window_borders[0] +
                       end_window_borders[2] // 2 -
                       exit_button_sizes[0] // 2 + (exit_button_sizes[0] - text.get_width()) // 2,
                       end_window_borders[1] +
                       end_window_borders[3] + text_under_end_window + (
                                   exit_button_sizes[1] - text.get_height()) // 2,
                       exit_button_sizes[0], exit_button_sizes[1]))
    pygame.display.flip()


def end():
    pygame.quit()
    exit()


pygame.init()
MYEVENTTYPE = pygame.USEREVENT + 1
timer_speed = 10
pygame.time.set_timer(MYEVENTTYPE, timer_speed)
drag = False
first = True
focused = True
can_go_next = True
time_rest = 100  # промежуток между ходами в миллисекундах
time_for_next = 0
drag_offset = [0, 0]
size = 20
sized = width, height = 1000, 1000
screen = pygame.display.set_mode(sized)
player = Player(10, (0, 0), 10)
places = [load_new_place(f"paint{i}.png") for i in range(1, 6)]  # структуры можно также хранить в
# БД или csv/текстовом файле


if __name__ == '__main__':
    state = "start window"
    while True:
        if state == "main":
            draw_main_game()
        elif state == "start window":
            draw_start_window()
        elif state == "end window":
            draw_end_window()

