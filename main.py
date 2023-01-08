import pygame

from random import choices, choice, randint, uniform, shuffle
from math import ceil

STRUCTURES_RANGE = [50, 100]  # from: _ to: _
EXTENDED_RANGE = [1, 5]  # from: _ to: _
ENEMIES_MULTI_RANGE = [0.1, 0.3]  # from: _ to: _
FOCUSE_RANGE = [5, 30]  # from: _ to: _
start = {(0, 0): 1, (1, 0): 1, (2, 0): 1, (1, 1): 1, (0, 1): 1, (0, 2): 1, (-1, 1): 1, (-1, 0): 1,
         (-2, 0): 1, (-1, -1): 1, (0, -1): 1, (0, -2): 1, (1, -1): 1}
FPS = 60


def load_image(name, colorkey=None):
    image = pygame.image.load(f"data/{name}")
    if colorkey is not None:
        image.set_colorkey(image.get_at((0, 0)))
    return image


class Weapon:
    def __init__(self, place, damage, im_name):
        self.place = place
        self.damage = damage
        self.image = load_image("weapons/" + im_name)


class Item(pygame.sprite.Sprite):
    def __init__(self, index, im_name, pos, group):
        super().__init__(group)
        self.image = pygame.image.load(f"data/items/{im_name}")
        self.index = index
        self.rect = self.image.get_rect().move(pos)

    def update(self, pos):
        if self.rect.collidepoint(pos):
            return self.index


class Character(pygame.sprite.Sprite):
    def __init__(self, hp, pos, damage):
        super().__init__()
        im = load_image(f"{self.__class__.__name__.lower()}.png")
        self.image_orig = cut_sheet(im, im.get_width() // 30, im.get_height() // 30)[0]
        self.hp = hp
        self.max_hp = hp
        self.pos = pos
        self.average_pos = [0, 0]
        self.animated_row = []
        self.damage = damage
        self.cells_per_move = 1 if self.__class__.__name__ == "Player" else self.moves_per_step
        im_walk = load_image(f"{self.__class__.__name__.lower()}_walk.png")
        im_attack = load_image(f"{self.__class__.__name__.lower()}_attack.png")
        self.animations = [
            cut_sheet(im_walk, im_walk.get_width() // 30, im_walk.get_height() // 30)[0],
            cut_sheet(im_attack, im_attack.get_width() // 30, im_attack.get_height() // 30)[0]]
        self.frame = 0
        self.stayed_frame = 0

    def update(self, offset=None):
        if self.animated_row:
            self.stayed_frame = 0
            if self.animated_row[0] == "attack":
                if len(self.animated_row) > 1 or round(
                        len(self.animations[1]) * (self.frame / (FPS * time_rest * 0.001))) >= \
                        len(self.animations[1]):
                    self.frame = 0
                    self.animated_row = self.animated_row[1:]
                else:
                    self.image = pygame. \
                        transform.scale(self.animations[1][round(len(self.animations[1]) *
                                                                 (self.frame /
                                                                  (FPS * time_rest * 0.001)))],
                                        (size, size))
            else:
                self.image = pygame.transform.scale(self.animations[0]
                                                    [round((len(self.animations[0]) - 1) *
                                                           max([abs(el) for el in
                                                                self.average_pos]))], (size, size))
                next_pos = [self.animated_row[0][0] - self.pos[0],
                            self.animated_row[0][1] - self.pos[1]]
                self.average_pos = [self.average_pos[0] + next_pos[0] / (
                        FPS / (self.cells_per_move / (time_rest * 0.001))),
                                    self.average_pos[1] + next_pos[1] / (
                                            FPS / (self.cells_per_move / (time_rest * 0.001)))]
                # FPS / (self.cells_per_move / (time_rest * 0.001)) - сколько кадров нужно потратить,
                # чтобы пройти 1 клетку
                if not (-1 < self.average_pos[0] < 1 and -1 < self.average_pos[1] < 1
                        and self.average_pos != [0, 0]):
                    self.pos = tuple(self.animated_row[0])
                    self.animated_row = self.animated_row[1:]
                    self.average_pos = [0, 0]
                    self.frame = -1
            self.frame += 1
        else:
            self.frame = 0
            self.image = pygame.transform.scale(self.image_orig[round(self.stayed_frame //
                                                                      (FPS / 2.5) %
                                                                      len(self.image_orig))],
                                                (size, size))
            self.stayed_frame += 1
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = (
            width // 2 - size // 2 - offset[0] + (self.pos[0] + self.average_pos[0]) * size,
            height // 2 - size // 2 - offset[1] + (self.pos[1] + self.average_pos[1]) * size)


class Player(Character):
    def __init__(self, max_hp, pos, damage):
        super().__init__(max_hp, pos, damage)
        self.floor = 1
        self.moves_per_step = 1
        self.moves_last = self.moves_per_step
        self.kills = 0
        self.items = []
        self.weapon_now = Weapon([[0, -1]], 5, "sword.png")

    def pressed_key(self, event):
        if event[pygame.K_w] or event[pygame.K_s] or event[pygame.K_a] or event[pygame.K_d]:
            self.move(event)
        elif event[pygame.K_UP] or event[pygame.K_DOWN] or event[pygame.K_LEFT] \
                or event[pygame.K_RIGHT]:
            self.attack(event)
        if self.hp <= 0:
            global state, focused, drag_offset
            state = "end window"
            focused = False
            drag_offset = [self.pos[0] * size, self.pos[1] * size]

    def move(self, event):
        list0 = [[[0, -1], pygame.K_w], [[0, 1], pygame.K_s],
                 [[-1, 0], pygame.K_a], [[1, 0], pygame.K_d]]
        shuffle(list0)
        for args in list0:
            if check_condition([1, 1, 0, 1], pos=(self.pos[0] + args[0][0],
                                                  self.pos[1] + args[0][1]),
                               event=event, key=args[1]) and self.average_pos == [0, 0]:
                self.animated_row.append([self.pos[0] + args[0][0], self.pos[1] + args[0][1]])
                sound = choice(sounds["player walk"])
                sound.set_volume(volume)
                sound.play()
                self.moves_last -= 1
                global can_go_next
                can_go_next = False
                break
        if self.moves_last <= 0:
            self.moves_last = self.moves_per_step
            enemies.update(your_move=True)

    def attack(self, event):
        list0 = [[self.weapon_now.place, pygame.K_UP],
                 [rotate(self.weapon_now.place, 2), pygame.K_DOWN],
                 [rotate(self.weapon_now.place, 1), pygame.K_LEFT],
                 [rotate(self.weapon_now.place, 3), pygame.K_RIGHT]]
        shuffle(list0)
        for args in list0:
            if event[args[1]]:
                for arg in args[0]:
                    AnimatedAttack((width // 2 + (self.pos[0] + arg[0]) * size,
                                    height // 2 + (self.pos[1] + arg[1]) * size))
                attacks_group.update(offset=get_offset())
                sound = choice(sounds["player attack"])
                sound.set_volume(volume)
                sound.play()
                self.animated_row.append("attack")
                global can_go_next
                can_go_next = False
                self.moves_last = self.moves_per_step
                break
        else:
            return
        enemies.update(your_move=True)


class BasicEnemy(Character):
    def __init__(self, hp, damage, pos, view, moves_per_step):
        self.moves_per_step = moves_per_step
        super().__init__(hp, pos, damage)
        self.cells_of_view = sphere_of_cells(view)
        self.found_radius = view // 2
        self.show_hp = False

    def update(self, offset=None, size_changed=None, your_move=None, check_attack=None, rect=None):
        if self.show_hp:
            pygame.draw.rect(screen, "black", (self.rect.x, self.rect.y, self.rect.width, 1))
            pygame.draw.rect(screen, "red", (self.rect.x, self.rect.y,
                                             round(self.hp / self.max_hp * self.rect.width), 1))
        if your_move:
            self.make_step()
        elif check_attack:
            if self.rect.colliderect(rect):
                self.hp -= player.damage + player.weapon_now.damage
                sound = choice(sounds["hit enemy"])
                sound.set_volume(volume)
                sound.play()
                self.show_hp = True
                if self.hp <= 0:
                    self.kill()
                    return
        else:
            super().update(offset)

    def make_step(self):
        if abs(self.pos[0] - player.pos[0]) + abs(self.pos[1] - player.pos[1]) <= self.found_radius:
            lb = {}
            for cell in self.cells_of_view:
                if (self.pos[0] + cell[0], self.pos[1] + cell[1]) in card:
                    lb[(self.pos[0] + cell[0], self.pos[1] + cell[1])] = 0
            sorted_row = [el for el in player.animated_row if el != "attack"]
            need_pos = tuple(sorted_row[0]) if sorted_row else player.pos
            result = self.find_path(lb, self.pos, need_pos)
            if result and (path := [cell for cell in result if cell != need_pos]):  # <-- path
                self.animated_row.extend(path[:self.moves_per_step])
            elif result is None:  # если нельзя пройти до игрока
                self.make_random_step()
            if result and len(path) < self.moves_per_step:  # если остались ходы
                self.attack_player(need_pos)
        else:
            self.make_random_step()

    def attack_player(self, need_pos):
        player.hp -= self.damage
        self.animated_row.append("attack")
        AnimatedAttack((width // 2 + need_pos[0] * size, height // 2 + need_pos[1] * size))
        sound = choice(sounds["hit player"])
        sound.set_volume(volume)
        sound.play()

    def make_random_step(self):
        pos_now = self.pos
        for _ in range(self.moves_per_step):
            variants = []
            for args in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
                if check_condition([1, 1], pos=(pos_now[0] + args[0], pos_now[1] + args[1])):
                    variants.append((pos_now[0] + args[0], pos_now[1] + args[1]))
            if variants:
                pos_now = choice(variants)
                self.animated_row.append(pos_now)

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
                if check_condition([1, 1, 1, 0, 1], pos=(now[0] + args[0], now[1] + args[1]),
                                   flat=lb):
                    lb[now[0] + args[0], now[1] + args[1]] = now
                    new_nexts.append((now[0] + args[0], now[1] + args[1]))
        if new_nexts:
            self.find_lab_tuples(new_nexts, lb)


class Enemy(BasicEnemy):
    def __init__(self, hp, damage, pos, view, moves_per_step):
        super().__init__(hp, damage, pos, view, moves_per_step)


class FastEnemy(BasicEnemy):
    def __init__(self, hp, damage, pos, view, moves_per_step):
        super().__init__(hp, damage, pos, view, moves_per_step)


class CubeEnemy(BasicEnemy):
    def __init__(self, *args):
        super().__init__(*args)

    def attack_player(self, need_pos):
        self.animated_row.append("attack")


class StrongEnemy(BasicEnemy):
    def __init__(self, *args):
        super().__init__(*args)


class AnimatedAttack(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__(attacks_group)
        self.frames, self.width, self.height = \
            cut_sheet(load_image("attack.png"), 5, 1)
        self.cur_frame = 0
        self.x, self.y = pos
        self.image = pygame.transform.scale(self.frames[self.cur_frame], (size, size))
        self.rect = self.image.get_rect()
        self.delitel = 5
        self.checked = False

    def update(self, offset=None):
        if not self.checked:
            enemies.update(check_attack=True,
                           rect=(self.x - offset[0] - self.image.get_width() // 2,
                                 self.y - offset[1] - self.image.get_height() // 2, size, size))
            self.checked = True
        elif self.cur_frame < len(self.frames) * self.delitel:
            self.rect.x = self.x - offset[0] - self.image.get_width() // 2
            self.rect.y = self.y - offset[1] - self.image.get_height() // 2
            self.image = pygame.transform.scale(self.frames[self.cur_frame // self.delitel],
                                                (size, size))
            self.cur_frame += 1
        else:
            self.kill()


items = [[0, "item1.png"], [1, "item2.png"], [2, "item3.png"]]
weapons = [Weapon([[0, -1], [0, -2]], 10, "sword1.png")]


def cut_sheet(sheet, columns, rows):
    rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                       sheet.get_height() // rows)
    frames = []
    for j in range(rows):
        for i in range(columns):
            frame_location = (rect.w * i, rect.h * j)
            frames.append(sheet.subsurface(pygame.Rect(
                frame_location, rect.size)))
    return frames, rect.w, rect.h


def get_offset():
    global size, focused, drag_offset
    return [(player.pos[0] + player.average_pos[0]) * size,
            (player.pos[1] + player.average_pos[1]) * size] if focused else drag_offset


def check_condition(variants, pos=None, flat=None, event=None, key=None):
    if flat is None:
        flat = card
    flag = True
    if len(variants) >= 1 and variants[0]:
        flag = flag and pos in flat
    if len(variants) >= 2 and variants[1]:
        flag = flag and all([pos !=
                             (en.animated_row[0] if en.animated_row else en.pos) for en in enemies])
    if len(variants) >= 3 and variants[2]:
        flag = flag and type(flat[pos]) != tuple
    if len(variants) >= 4 and variants[3]:
        flag = flag and event[key]
    if len(variants) >= 5 and variants[4]:
        flag = flag and pos != player.animated_row[0]
    return flag


def load_new_place(filename):
    new = []
    f = open("data/" + filename, "r", encoding="utf-8")
    firsts = []
    for i, row in enumerate(f.read().split("\n")):
        for j, symb in enumerate(row):
            if symb == "*":
                if not firsts:
                    firsts = [j, i]
                new.append([j - firsts[0], i - firsts[1]])
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
    global card, exit_ladder, enemies, focused, chest, field_rect, \
        drag_offset, chest_looted, usually_lvl, floor_weapons
    usually_lvl = player.floor <= 1 or randint(0, round(5 * (2 - hardness))) != 0
    structures = int(randint(STRUCTURES_RANGE[0], STRUCTURES_RANGE[1]) * hardness)
    extended = uniform(EXTENDED_RANGE[0], EXTENDED_RANGE[1]) if usually_lvl else -10
    card = start.copy()
    for i in range(structures):
        draw_loading_bar(i / structures)
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

        first = choices(cells,
                        weights=[pow((abs(cell[0]) + abs(cell[1])), extended) for cell in cells])[0]
        for coord in rotate(choice(places), randint(0, 3)):
            card[first[0] + coord[0], first[1] + coord[1]] = 1

    max_cell = (0, 0)
    for key in card:
        if abs(key[0]) + abs(key[1]) > abs(max_cell[0]) + abs(max_cell[1]):
            max_cell = key
    exit_ladder = choice([(max_cell[0] + cell[0], max_cell[1] + cell[1])
                          for cell in sphere_of_cells(20)
                          if (max_cell[0] + cell[0], max_cell[1] + cell[1]) in card])

    enemies = pygame.sprite.Group()
    flat = card.copy()
    flat2 = flat.copy()
    [flat.pop(cell) for cell in sphere_of_cells(20) if cell in flat]
    numb_enemies = int(structures * uniform(ENEMIES_MULTI_RANGE[0], ENEMIES_MULTI_RANGE[1]))
    for i in range(numb_enemies):
        cell = choice(list(flat))
        if player.floor < 4:
            enemies.add(choices([Enemy(round((30 + (player.floor - 1) * 2) * hardness), 1, cell,
                                       round(10 * hardness), 1),
                                 FastEnemy(round((20 + (player.floor - 1) * 1.5) * hardness),
                                           1, cell, round(15 * hardness),
                                           round(3 * hardness))],
                                weights=[6, player.floor])[0])
        else:
            enemies.add(choices([CubeEnemy(round((70 + (player.floor - 1) * 5) * hardness), 1, cell,
                                           round(10 * hardness), 1),
                                 StrongEnemy(10, round((3 + (player.floor - 1) * 0.2) * hardness),
                                             cell, round(15 * hardness), 3)],
                                weights=[4, player.floor])[0])
        flat.pop(cell)

    flat2.pop((0, 0))
    flat2.pop(exit_ladder)
    chest = choices(list(flat2), weights=[pow(abs(cell[0] - exit_ladder[0]) +
                                              abs(cell[1] - exit_ladder[1]) + abs(cell[0]) +
                                              abs(cell[1]), 3 * hardness) for cell in flat2])[0]

    focused = True
    chest_looted = False
    player.pos = (0, 0)
    field_rect = [sorted(card.keys(), key=lambda x: x[0])[0][0],
                  sorted(card.keys(), key=lambda x: x[1])[0][1],
                  sorted(card.keys(), key=lambda x: x[0], reverse=True)[0][0] + 1,
                  sorted(card.keys(), key=lambda x: x[1], reverse=True)[0][1] + 1]
    drag_offset = [0, 0]

    flat2.pop(chest)
    floor_weapons = []
    if randint(0, round(0.5 + hardness * 2)) == 0:
        for _ in range(randint(1, round(2.5 - hardness))):
            floor_weapons.append([choice(list(flat2.keys())), choice(weapons)])

    enemies.update(offset=get_offset())
    attacks_group.empty()
    make_surface_field()


def make_surface_field():
    global floor_field, floor_field_sized, usually_lvl
    """ниже создается surface, где отображены все клетки сразу, которые не будут меняться"""
    list_of_tiles = []
    if player.floor < 4:
        stage = "first"
    else:
        stage = "second"
    try:
        i = 0
        while True:
            i += 1
            floor = load_image(f"floors/{stage}/floor{i}.png")
            floor = pygame.transform.scale(floor, (FOCUSE_RANGE[1], FOCUSE_RANGE[1]))
            list_of_tiles.append(floor)
    except FileNotFoundError:
        pass
    floor_field = pygame.Surface(
        ((field_rect[2] - field_rect[0]) * FOCUSE_RANGE[1], (field_rect[3] -
                                                             field_rect[1]) * FOCUSE_RANGE[1]))
    for cell in card.keys():
        tile = choices(list_of_tiles, weights={"first": [1, 0.05, 0.05, 0.005],
                                               "second": [1, 0.05, 0.05, 0.005]}[stage])[0]
        tile = pygame.transform.rotate(tile, randint(0, 3) * 90)
        floor_field.blit(tile, ((cell[0] - field_rect[0]) * FOCUSE_RANGE[1],
                                (cell[1] - field_rect[1]) * FOCUSE_RANGE[1]))
        if cell == exit_ladder and usually_lvl:
            tile = load_image("exit_ladder.png")
            tile = pygame.transform.scale(tile, (FOCUSE_RANGE[1], FOCUSE_RANGE[1]))
        else:
            continue
        floor_field.blit(tile, ((cell[0] - field_rect[0]) * FOCUSE_RANGE[1],
                                (cell[1] - field_rect[1]) * FOCUSE_RANGE[1]))
    pygame.image.save(floor_field, "picture.png")

    floor_field_sized = pygame.transform.scale(floor_field,
                                               ((field_rect[2] - field_rect[0]) * size,
                                                (field_rect[3] - field_rect[1]) * size))


def end():
    pygame.quit()
    exit()


def draw_main_game():
    global drag_offset, drag, focused, can_go_next, time_for_next, floor_field_sized, size, \
        state, chest_looted, usually_lvl, floor_weapons

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            end()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            sf = pygame.Surface((width, height))
            sf.set_alpha(150)
            sf.fill("black")
            sc = screen.copy()
            sc.blit(sf, (0, 0))
            draw_menu(sc)
        elif event.type == pygame.MOUSEWHEEL:
            last_size = size
            if size + ceil(event.y * (size / 10)) > FOCUSE_RANGE[1]:
                size = FOCUSE_RANGE[1]
            elif size + ceil(event.y * (size / 10)) < FOCUSE_RANGE[0]:
                size = FOCUSE_RANGE[0]
            else:
                size += ceil(event.y * (size / 10))
            drag_offset = [round(drag_offset[0] * (size / last_size)),
                           round(drag_offset[1] * (size / last_size))]
            floor_field_sized = pygame.transform.scale(floor_field,
                                                       ((field_rect[2] - field_rect[0]) * size,
                                                        (field_rect[3] - field_rect[1]) * size))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            drag = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            drag = False
        elif event.type == pygame.MOUSEMOTION and drag:
            drag_offset = [drag_offset[i] - event.rel[i] for i in range(2)]
            focused = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                focused = not focused
                drag_offset = [player.pos[0] * size, player.pos[1] * size]
            elif event.key == pygame.K_e:
                if player.pos == exit_ladder and (usually_lvl or len(enemies) == 0):
                    player.floor += 1
                    make_new_level()
                elif player.pos == chest and not chest_looted:
                    state = "choice item"
                elif result := [weapon for weapon in floor_weapons if weapon[0] == (
                        tuple(player.animated_row[0]) if player.animated_row else player.pos)]:
                    floor_weapons.remove(result[0])
                    floor_weapons.append([result[0][0], player.weapon_now])
                    player.weapon_now = result[0][1]
        elif event.type == MYEVENTTYPE:
            if not can_go_next:
                time_for_next += timer_speed
            if time_for_next >= time_rest:
                can_go_next = True
                time_for_next = 0
        if pygame.key.get_pressed() and can_go_next and all(
                [len(enemy.animated_row) == 0 for enemy in enemies]):
            player.pressed_key(pygame.key.get_pressed())

    screen.fill('black')

    offset = get_offset()
    draw_field(offset)
    draw_player(offset)
    attacks_group.update(offset)
    attacks_group.draw(screen)

    pygame.draw.arc(screen, (255, 255, 0), (50, height - 100, 50, 50), 90 / 57.2958,
                    360 / 57.2958 * (time_for_next / time_rest) +
                    90 / 57.2958, 25)
    pygame.draw.arc(screen, (255, 150, 0), (50, height - 100, 50, 50), 90 / 57.2958,
                    360 / 57.2958 * (time_for_next / time_rest) +
                    90 / 57.2958, 5)  # время до следующего хода

    text = pygame.font.Font(None, 50).render(str(player.moves_last), True, (255, 255, 255))
    screen.blit(text, (
        50 + 25 - text.get_width() // 2, height - 100 + 25 - text.get_height() // 2))

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
    clock.tick(FPS)


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
        if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            end()
    pygame.display.flip()


def draw_start_window(start_window_sizes=[800, 100],
                      exit_button_sizes=[200, 50], hardness_under=100):
    global state, player, drag, can_go_next, time_for_next, drag_offset, size, player_group, \
        hardness, timer

    drag_hd = False

    start_window_borders = [(width - start_window_sizes[0]) // 2,
                            (height - start_window_sizes[1]) // 2]
    start_window_borders.extend([start_window_borders[0] + start_window_sizes[0],
                                 start_window_borders[1] + start_window_sizes[1]])
    while True:
        screen.fill("black")
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or \
                    (event.type == pygame.MOUSEBUTTONDOWN and pygame.Rect(
                        width - 50 - exit_button_sizes[0],
                        height - 50 - exit_button_sizes[1],
                        exit_button_sizes[0], exit_button_sizes[1]).collidepoint(event.pos)):
                end()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and pygame.Rect(*start_window_borders[:2], *start_window_sizes). \
                    collidepoint(event.pos):
                state = "main"
                drag = False
                can_go_next = True
                time_for_next = 0
                drag_offset = [0, 0]
                size = FOCUSE_RANGE[1]
                player_group = pygame.sprite.Group()
                player = Player(10, (0, 0), 5)
                player_group.add(player)
                make_new_level()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and \
                    pygame.Rect(start_window_borders[0],
                                start_window_borders[3] + hardness_under - 10,
                                start_window_sizes[0], 22).collidepoint(event.pos):
                drag_hd = True
                hardness = (event.pos[0] - start_window_borders[0]) / start_window_sizes[0] + 0.5
            elif event.type == pygame.MOUSEBUTTONUP:
                drag_hd = False
            elif event.type == pygame.MOUSEMOTION and drag_hd:
                hardness = \
                    (event.pos[0] - start_window_borders[0]) / start_window_sizes[0] + 0.5
                if hardness > 1.5:
                    hardness = 1.5
                elif hardness < 0.5:
                    hardness = 0.5

        pygame.draw.rect(screen, "green", (start_window_borders[0], start_window_borders[1],
                                           start_window_sizes[0], start_window_sizes[1]), 1)
        text = pygame.font.Font(None, 100).render("START", True, "green")
        screen.blit(text, ((width - text.get_width()) // 2, (height - text.get_height()) // 2))

        pygame.draw.rect(screen, "white", (start_window_borders[0], start_window_borders[3] +
                                           hardness_under, start_window_sizes[0], 2))
        pygame.draw.rect(screen, "white", (start_window_borders[0] + (hardness - 0.5) *
                                           start_window_sizes[0] - 2, start_window_borders[3] +
                                           hardness_under - 10, 4, 22))

        pygame.draw.rect(screen, "white", (start_window_borders[0], start_window_borders[3] +
                                           hardness_under - 2, 2, 6))
        text = pygame.font.Font(None, 50).render("0.5", True, "white")
        screen.blit(text, (start_window_borders[0] - text.get_width() // 2, start_window_borders[3] +
                           hardness_under + text.get_height() // 2))

        pygame.draw.rect(screen, "white", (start_window_borders[0] + start_window_sizes[0] // 2,
                                           start_window_borders[3] + hardness_under - 2, 2, 6))
        text = pygame.font.Font(None, 50).render("1.0", True, "white")
        screen.blit(text, (start_window_borders[0] + start_window_sizes[0] // 2 -
                           text.get_width() // 2, start_window_borders[3] +
                           hardness_under + text.get_height() // 2))

        pygame.draw.rect(screen, "white", (start_window_borders[2],
                                           start_window_borders[3] + hardness_under - 2, 2, 6))
        text = pygame.font.Font(None, 50).render("1.5", True, "white")
        screen.blit(text, (start_window_borders[2] - text.get_width() // 2, start_window_borders[3] +
                           hardness_under + text.get_height() // 2))

        text = pygame.font.Font(None, 70).render(str(round(hardness, 2)), True, "white")
        screen.blit(text, (start_window_borders[0] + (start_window_sizes[0] - text.get_width()) // 2,
                           start_window_borders[3] + hardness_under - text.get_height() // 2 -
                           hardness_under // 2))

        pygame.draw.rect(screen, (255, 255, 255), (width - 50 - exit_button_sizes[0],
                                                   height - 50 - exit_button_sizes[1],
                                                   exit_button_sizes[0], exit_button_sizes[1]), 1)
        pygame.draw.rect(screen, (0, 0, 0), (width - 50 - exit_button_sizes[0] + 1,
                                             height - 50 - exit_button_sizes[1] + 1,
                                             exit_button_sizes[0] - 2, exit_button_sizes[1] - 2))
        text = pygame.font.Font(None, 50).render("EXIT", True, (255, 255, 255))
        screen.blit(text, (width - 50 - (exit_button_sizes[0] + text.get_width()) // 2,
                           height - 50 - (exit_button_sizes[1] + text.get_height()) // 2))

        pygame.display.flip()


def draw_end_window(end_window_sizes=[200, 400], exit_button_sizes=[200, 50],
                    text_under_end_window=20):
    global size, drag_offset, drag, focused, state, floor_field_sized, chest_looted, usually_lvl
    end_window_borders = [width - end_window_sizes[0] - 20, 20, end_window_sizes[0],
                          end_window_sizes[1]]
    screen.fill("black")
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            end()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            attacks_group.empty()
            state = "start window"
        elif event.type == pygame.MOUSEWHEEL:
            last_size = size
            if size + ceil(event.y * (size / 10)) > FOCUSE_RANGE[1]:
                size = FOCUSE_RANGE[1]
            elif size + ceil(event.y * (size / 10)) < FOCUSE_RANGE[0]:
                size = FOCUSE_RANGE[0]
            else:
                size += ceil(event.y * (size / 10))
            drag_offset = [round(drag_offset[0] * (size / last_size)),
                           round(drag_offset[1] * (size / last_size))]
            floor_field_sized = pygame.transform.scale(floor_field,
                                                       ((field_rect[2] - field_rect[0]) * size,
                                                        (field_rect[3] - field_rect[1]) * size))
            enemies.update(offset=get_offset())
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(end_window_borders[0] + (end_window_borders[2] - exit_button_sizes[0]),
                           end_window_borders[1] + end_window_borders[3] + text_under_end_window,
                           exit_button_sizes[0], exit_button_sizes[1]).collidepoint(event.pos):
                attacks_group.empty()
                state = "start window"
            drag = True
        elif event.type == pygame.MOUSEBUTTONUP:
            drag = False
        elif event.type == pygame.MOUSEMOTION and drag:
            drag_offset = [drag_offset[i] - event.rel[i] for i in range(2)]
            focused = False

    draw_field(get_offset())

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
    clock.tick(FPS)


def draw_choice_item(item_size=200, menu_sizes=[[200, 500], [2, 50], [200, 50]]):
    global player, size, focused, drag_offset, state, chest_looted, menu_mode
    offset = get_offset()
    copy_items = items.copy()
    items_for_choice = []
    for _ in range(3):
        items_for_choice.append(
            choices(copy_items, weights=[len(player.items) - player.items.count(item) + 1
                                         for item in copy_items])[0])
        copy_items.remove(items_for_choice[-1])
    items_group = pygame.sprite.Group()
    for i, coord in enumerate([[width // 4 - item_size // 2, height // 4 - item_size // 2],
                               [width // 4 * 2 - item_size // 2, height // 4 * 3 - item_size // 2],
                               [width // 4 * 3 - item_size // 2, height // 4 - item_size // 2]]):
        Item(items_for_choice[i][0], items_for_choice[i][1], coord, items_group)
    while state == "choice item":
        screen.fill("black")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                end()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if result := [item.update(event.pos) for item in items_group
                              if item.update(event.pos) is not None]:
                    use_item(result[0])
                    chest_looted = True
                    state = "main"
                    return
        draw_field(offset)
        draw_chest(offset)
        draw_player(offset)
        items_group.draw(screen)
        pygame.display.flip()


def use_item(index):
    player.items.append(index)
    if index == 0:
        player.max_hp += 1
        player.hp = player.max_hp
    elif index == 1:
        player.damage += 5
    elif index == 2:
        player.moves_per_step += 1


def draw_field(offset):
    screen.blit(floor_field_sized,
                (width // 2 - offset[0] - size // 2 + field_rect[0] * size,
                 height // 2 - offset[1] - size // 2 + field_rect[1] * size))  # поле
    draw_floor_weapons(offset)
    if not chest_looted:
        draw_chest(offset)
    if usually_lvl or len(enemies) == 0:
        draw_exit_ladder(offset)
    enemies.update(offset)
    enemies.draw(screen)


def draw_player(offset):
    player_group.update(offset)
    player_group.draw(screen)


def draw_chest(offset):
    global chest_looted
    if not chest_looted:
        copy_chest = pygame.transform.scale(chest_im, (size, size))
        screen.blit(copy_chest, (width // 2 + chest[0] * size - size // 2 - offset[0],
                                 height // 2 + chest[1] * size - size // 2 - offset[1]))


def draw_exit_ladder(offset):
    copy_exit_ladder = pygame.transform.scale(exit_ladder_im, (size, size))
    screen.blit(copy_exit_ladder, (width // 2 + exit_ladder[0] * size - size // 2 - offset[0],
                                   height // 2 + exit_ladder[1] * size - size // 2 - offset[1]))


def draw_floor_weapons(offset):
    global floor_weapons
    for weapon in floor_weapons:
        image = pygame.transform.scale(weapon[1].image, (size, size))
        screen.blit(image, (width // 2 - image.get_width() // 2 - offset[0] + weapon[0][0] * size,
                            height // 2 - image.get_height() // 2 - offset[1] + weapon[0][1] * size))


def draw_menu(sc, menu_sizes=[[200, 500], [2, 50], [200, 50]]):
    global volume, state
    drag_hd = False
    while True:
        screen.fill("black")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                end()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pygame.Rect(width - 25 - (menu_sizes[0][0] + menu_sizes[1][0]) // 2,
                               20 + menu_sizes[1][1], 12,
                               menu_sizes[0][1] - menu_sizes[1][1] * 2).collidepoint(event.pos):
                    drag_hd = True
                    volume = 1 - (event.pos[1] - 20 - menu_sizes[1][1]) / (
                            menu_sizes[0][1] - menu_sizes[1][1] * 2)
                elif pygame.Rect(width - 20 - menu_sizes[2][0],
                                 40 + menu_sizes[0][1],
                                 menu_sizes[2][0],
                                 menu_sizes[2][1]).collidepoint(event.pos):
                    state = "start window"
                    return
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                drag_hd = False
            elif event.type == pygame.MOUSEMOTION and drag_hd:
                volume = 1 - (event.pos[1] - 20 - menu_sizes[1][1]) / (
                        menu_sizes[0][1] - menu_sizes[1][1] * 2)
                if volume > 1:
                    volume = 1
                elif volume < 0:
                    volume = 0
        screen.blit(sc, (0, 0))
        pygame.draw.rect(screen, "white", (width - menu_sizes[0][0] - 20, 20,
                                           menu_sizes[0][0], menu_sizes[0][1]), 1)
        pygame.draw.rect(screen, "black", (width - menu_sizes[0][0] - 19, 21,
                                           menu_sizes[0][0] - 2, menu_sizes[0][1] - 2))
        pygame.draw.rect(screen, "white", (width - 20 -
                                           (menu_sizes[0][0] + menu_sizes[1][0]) // 2,
                                           20 + menu_sizes[1][1], menu_sizes[1][0],
                                           menu_sizes[0][1] - menu_sizes[1][1] * 2))
        text = pygame.font.Font(None, 30).render(f"{round(volume * 100)}%", True,
                                                 (255, 255, 255))
        screen.blit(text, (width - (menu_sizes[0][0] + text.get_width()) // 2 - 20,
                           20 + menu_sizes[0][1] - (menu_sizes[1][1] + text.get_height()) // 2))
        pygame.draw.rect(screen, "white", (width - 25 -
                                           (menu_sizes[0][0] + menu_sizes[1][0]) // 2,
                                           20 + menu_sizes[1][1] + (1 - volume) *
                                           (menu_sizes[0][1] - menu_sizes[1][1] * 2), 12, 2))

        pygame.draw.rect(screen, "white", (width - 20 - menu_sizes[2][0],
                                           40 + menu_sizes[0][1],
                                           menu_sizes[2][0], menu_sizes[2][1]), 1)
        pygame.draw.rect(screen, "black", (width - 19 - menu_sizes[2][0],
                                           41 + menu_sizes[0][1],
                                           menu_sizes[2][0] - 2, menu_sizes[2][1] - 2))
        text = pygame.font.Font(None, 50).render(f"EXIT", True,
                                                 (255, 255, 255))
        screen.blit(text, (width - 20 - (menu_sizes[2][0] + text.get_width()) // 2,
                           40 + menu_sizes[0][1] + (menu_sizes[2][1] - text.get_height()) // 2))

        pygame.display.flip()


def find_sounds(name):
    sounds = []
    try:
        i = 0
        while True:
            i += 1
            sounds.append(pygame.mixer.Sound(f"data/sounds/{name}{i}.wav"))
    except FileNotFoundError:
        return sounds


pygame.init()
width, height = (1000, 1000) if input() == "" else (
    pygame.display.Info().current_w, pygame.display.Info().current_h)
screen = pygame.display.set_mode((width, height))

sounds = {"player attack": find_sounds("player attack"), "hit player": find_sounds("hit player"),
          "hit enemy": find_sounds("hit enemy"), "player walk": find_sounds("player walk")}

hardness = 1.0
MYEVENTTYPE = pygame.USEREVENT + 1
timer_speed = 10
volume = 0.1
time_rest = 100  # промежуток между ходами в миллисекундах
clock = pygame.time.Clock()
pygame.time.set_timer(MYEVENTTYPE, timer_speed)
attacks_group = pygame.sprite.Group()
places = [load_new_place(f"places/place{i}.txt") for i in range(1, 6)]
chest_im = load_image("chest.png")
exit_ladder_im = load_image("exit_ladder.png")

if __name__ == '__main__':
    state = "start window"
    while True:
        if state == "main":
            draw_main_game()
        elif state == "start window":
            draw_start_window()
        elif state == "end window":
            draw_end_window()
        elif state == "choice item":
            draw_choice_item()
