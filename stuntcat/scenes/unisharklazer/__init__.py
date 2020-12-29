"""
Cat 3 Module.

"""

import math
import random
from typing import Optional

import pygame
from pygame.sprite import DirtySprite, LayeredDirty

from stuntcat.resources import gfx, sfx, music, distance
from stuntcat.scenes.scene import Scene
from stuntcat.scenes.unisharklazer.flying_objects import Fish, NotFish
from stuntcat.scenes.unisharklazer.elephant import Elephant


class LayeredDirtyAppend(LayeredDirty):
    """Like a group, except it has append and extend methods like a list."""

    def append(self, sprite):
        """
        Append an item to the sprite group.

        :param sprite: the sprite.
        """
        self.add(sprite)

    def extend(self, sprite_list):
        """
        Extend the sprite group with a list of items.

        :param sprite_list: the list.
        """
        for sprite in sprite_list:
            self.add(sprite)


class Lazer(DirtySprite):
    """
    lazer sprite class.
    """

    def __init__(self, container, shark_size):
        DirtySprite.__init__(self, container)
        self.rect = pygame.Rect([150, shark_size[1] - 155, shark_size[0], 10])
        # self.rect.x = -1000
        self.image = pygame.transform.scale(
            gfx("shark_laser.png", convert_alpha=True), self.rect.size
        )


class Shark(DirtySprite):  # pylint:disable=too-many-instance-attributes
    """
    Shark sprite class.
    """

    def __init__(self, container, scene, width, height):
        DirtySprite.__init__(self, container)
        self.debug = False
        self.container = container
        self.scene = scene
        self.width, self.height = width, height

        self.state = 0  #
        self.states = {
            0: "offscreen",
            1: "about_to_appear",
            2: "poise",
            3: "aiming",
            4: "fire laser",
            5: "leaving",
        }
        self.last_state = 0
        self.just_happened = None
        self.lazered = False  # was the cat hit?
        self.lazer = None  # type: Optional[Lazer]
        self.laser_height = height - 150  # where should the laser be on the screen?

        # TODO: to make it easier to test the shark
        #        self.time_between_appearances = 1000 #ms
        # self.time_between_appearances = 5000 #ms

        # self.time_of_about_to_appear = 1000#ms
        # self.time_of_poise = 1000 #ms
        # self.time_of_aiming = 500 #ms
        # self.time_of_laser = 200 #ms
        # self.time_of_leaving = 1000 #ms

        self.timings = {
            "time_between_appearances": 5000,
            "time_of_about_to_appear": 1000,
            "time_of_poise": 1000,
            "time_of_aiming": 500,
            "time_of_laser": 200,
            "time_of_leaving": 1000,
        }
        self.last_animation = 0  # ms

        self.applaud = True

        sfx("default_shark.ogg")
        sfx("shark_appear.ogg")
        sfx("shark_gone.ogg")
        sfx("shark_lazer.ogg")
        sfx("applause.ogg")
        sfx("cat_shot.ogg")
        sfx("boo.ogg")

        self.image = gfx("shark.png", convert_alpha=True)
        # gfx('foot_part.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = -1000
        self.rect.y = self.height - self.image.get_height()

    def update(self, *args, **kwargs):

        if self.debug and self.just_happened:
            print(self.just_happened)

        if self.just_happened == "offscreen":
            sfx("shark_gone.ogg", stop=1)

            self.rect.x = -1000
            self.dirty = True

        elif self.just_happened == "about_to_appear":
            music(stop=True)
            self.applaud = True
            sfx("shark_appear.ogg", play=1)

        elif self.just_happened == "poise":
            sfx("shark_attacks.ogg", play=1)

            self.rect.x = -30
            self.dirty = True

        elif self.just_happened == "fire laser":
            self.fire_laserbeam(self.debug)

        elif self.just_happened == "leaving":
            sfx("shark_appear.ogg", fadeout=3500)
            sfx("shark_attacks.ogg", stop=1)
            sfx("shark_gone.ogg", play=1)
            self.dirty = True
            if self.lazered:
                sfx("boo.ogg", play=True)
                self.scene.reset_on_death()
                self.lazered = False
                self.scene.annoy_crowd()
            elif self.applaud:
                sfx("applause.ogg", play=1)
            if self.lazer:
                self.lazer.kill()
                self.lazer = None

    def fire_laserbeam(self, debug):
        """
        Fires the shark's head mounted laser cannon.

        :param debug:
        """
        if debug:
            print(self.just_happened)
        self.lazer = Lazer(self.container, (self.width, self.height))

        sfx("shark_lazer.ogg", play=1)

        if (
            self.scene.player_data.cat_location[1]
            > self.scene.player_data.cat_wire_height - 3
        ):
            sfx("cat_shot.ogg", play=1)

            self.lazered = True
        else:
            self.lazered = False

    def _update_last_animation(self, total_time, timing):
        """"""
        if total_time > self.last_animation + self.timings[timing]:
            self.state += 1
            self.last_animation = total_time

    def animate(self, total_time):
        """
        Animate method.

        :param total_time:
        """
        # print('update', self.states[self.state], self.states[self.last_state])
        state = self.states[self.state]
        start_state = self.state

        if state == "offscreen":
            self.just_happened = state if self.state != self.last_state else None
            self._update_last_animation(total_time, "time_between_appearances")

        elif state == "about_to_appear":
            self.just_happened = state if self.state != self.last_state else None
            self._update_last_animation(total_time, "time_of_about_to_appear")

        elif state == "poise":
            self.just_happened = state if self.state != self.last_state else None

            # smoothly animate upwards
            self.rect.y = (self.height - self.image.get_height()) + 0.2 * (
                self.last_animation + self.timings["time_of_poise"] - total_time
            )
            self.dirty = True

            self._update_last_animation(total_time, "time_of_poise")

        elif state == "aiming":
            self.just_happened = state if self.state != self.last_state else None
            self._update_last_animation(total_time, "time_of_aiming")

        elif state == "fire laser":
            self.just_happened = state if self.state != self.last_state else None
            self._update_last_animation(total_time, "time_of_laser")

        elif state == "leaving":
            self.just_happened = state if self.state != self.last_state else None

            # smoothly animate downwards
            self.rect.y = (self.height - self.image.get_height()) + 0.2 * (
                total_time - self.last_animation
            )
            self.dirty = True

            if total_time > self.last_animation + self.timings["time_of_leaving"]:
                self.state += 1
                if self.state == max(self.states.keys()) + 1:
                    self.state = 0
                self.last_animation = total_time

        self.last_state = start_state

    def set_state(self, new_state):
        """set the state number from the name """
        self.state = list(self.states.values()).index(new_state)

    def get_state(self):
        """get state name"""
        return self.states[self.state]

    def collide(self, scene, width, height, cat_location):
        """ TODO: this doesn't work. It means the laser never fires."""
        # if self.state == 2:
        #     if cat_location[1] > height - 130:
        #         print('shark collide')
        #         scene.reset_on_death()


class AnimatedCat(DirtySprite):
    """Handle animations for the cat."""

    def __init__(self):
        DirtySprite.__init__(self)

        self.last_location = [0, 0]
        self.last_direction = True  # right is true
        self.last_rotation = -1
        self.last_frame = None

        self.frame = 1
        self.frame_rate = 750  # time passed in ms before frame changes
        self.frame_time = 0
        self.frame_direction = True  # True = increasing, False = decreasing

        self.num_frames = 4

    def changed(self, location, direction, rotation, frame):
        """Has the cat state changed? Store the last state."""
        changed = (
            self.last_rotation != rotation
            or self.last_location != location
            or self.last_frame != self.frame
        )

        self.last_location = location
        self.last_direction = direction
        self.last_rotation = rotation
        self.last_frame = frame

        return changed

    def animate(self, time_delta):
        """Animate the sprite."""
        self.frame_time += time_delta
        if self.frame_time >= self.frame_rate:
            if self.frame_direction:
                self.frame += 1
            else:
                self.frame -= 1
            self.frame_time = 0
            if self.frame == self.num_frames or self.frame == 1:
                self.frame_direction = not self.frame_direction


class Cat(AnimatedCat):
    """Cat sprite class."""

    def __init__(self, cat_holder):
        AnimatedCat.__init__(self)
        self.cat_holder = cat_holder
        self.image = gfx("cat_unicycle1.png", convert_alpha=True)
        self.rect = self.image.get_rect()
        sfx("cat_jump.ogg")

        self.images = []
        self.flipped_images = []

        for i in range(self.num_frames):
            img = gfx("cat_unicycle%d.png" % (i + 1), convert_alpha=True)
            self.images.append(img)
            self.flipped_images.append(pygame.transform.flip(img, 1, 0))

    def get_image(self):
        """Return the image for the animated frame"""
        return (self.images, self.flipped_images)[
            self.cat_holder.player_data.cat_speed[0] < 0
        ][self.frame - 1]

    def update(self, *args, **kwargs):
        direction = self.cat_holder.player_data.cat_speed[0] > 0
        location = self.cat_holder.player_data.cat_head_location
        rotation = self.cat_holder.player_data.cat_angle

        if self.last_direction != direction:
            self.dirty = True
            self.image = self.get_image()

        if self.changed(location[:], direction, rotation, self.frame):
            self.image = pygame.transform.rotate(
                self.get_image(), -self.cat_holder.player_data.cat_angle * 180 / math.pi
            )
            size = self.image.get_rect().size
            self.dirty = True
            self.rect.x = int(location[0]) - size[0] * 0.5
            self.rect.y = int(location[1]) - size[1] * 0.5


SCORE_TEXT_CENTER = (472, 469)


class Score(DirtySprite):
    """Score class."""

    def __init__(self, score_holder):
        """
        score_holder has a 'score' attrib.
        """
        DirtySprite.__init__(self)
        self.score_holder = score_holder
        self.myfont = pygame.font.SysFont("monospace", 30, bold=True)
        self.image = self.myfont.render(
            str(self.score_holder.player_data.score), True, [0, 0, 0]
        )

        self._update_rect()
        self.last_score = self.score_holder.player_data.score

    def _update_rect(self):
        self.rect = self.image.get_rect()
        self.rect.center = SCORE_TEXT_CENTER

    def update(self, *args, **kwargs):
        if self.last_score != self.score_holder.player_data.score:
            self.dirty = True
            self.image = self.myfont.render(
                str(self.score_holder.player_data.score), True, [0, 0, 0]
            )
            self._update_rect()
        self.last_score = self.score_holder.player_data.score


class DeadZone(DirtySprite):
    """
    Dead Zone class.
    """

    def __init__(self, points):
        """
        score_holder has a 'score' attrib.
        """
        DirtySprite.__init__(self)
        zone_color = [255, 0, 0]

        # draw dead zones
        surf = pygame.display.get_surface()
        rect = pygame.draw.polygon(surf, zone_color, points)
        self.image = surf.subsurface(rect.clip(surf.get_rect())).copy()
        self.rect = self.image.get_rect()
        self.rect.x = rect.x
        self.rect.y = rect.y


class PlayerData:
    """
    Data about the player that gets passed around a lot at the minute.
    """

    def __init__(self, width, height):
        self._score = 0

        self.angle_to_not_fish = 0.0

        self.cat_wire_height = height - 100

        self.cat_start_pos = [width / 2, height - 100]
        self.cat_location = self.cat_start_pos[:]

        self.cat_speed = [0, 0]
        self.cat_speed_max = 8
        self.cat_fall_speed_max = 16
        self.cat_roll_speed = 0.01
        self.cat_angle = 0
        self.cat_angular_vel = 0
        self.cat_head_location = [
            int(self.cat_location[0] + 100 * math.cos(self.cat_angle - math.pi / 2)),
            int(self.cat_location[1] + 100 * math.sin(self.cat_angle - math.pi / 2)),
        ]

    def increment_score(self):
        """
        Increase the score.
        """
        self._score += 1

    def reset(self):
        """
        Reset the player data.
        """
        self.cat_location = self.cat_start_pos[:]
        self.cat_speed = [0, 0]
        self.cat_angle = 0
        self.cat_angular_vel = 0
        self._score = 0

    @property
    def score(self):
        """
        Get the player's score.
        """
        return self._score


CAT_MAX_JUMPING_TIME = 600  # ms
CAT_JUMP_SPEED = 0.07

JOY_JUMP_BUTTONS = (0, 1)
JOY_LEFT_BUTTONS = (4,)
JOY_RIGHT_BUTTONS = (5,)
JOY_TILT_LEFT_AXIS = 2
JOY_TILT_RIGHT_AXIS = 5
JOY_SENSE = 0.5  # Joystick sensitivity for movement


class CatUniScene(Scene):  # pylint:disable=too-many-instance-attributes
    """Cat unicycle scene."""

    def __init__(self, *args, **kwargs):
        Scene.__init__(self, *args, **kwargs)

        (width, height) = (1920 // 2, 1080 // 2)
        self.width, self.height = width, height

        # Loading screen should always be a fallback active scene
        self.active = False
        self.first_render = True

        self.myfont = pygame.font.SysFont("monospace", 20)

        self.background = gfx("background.png", convert=True)
        # self.cat_unicycle = gfx('cat_unicycle.png').convert_alpha()
        # self.fish = gfx('fish.png').convert_alpha()
        # self.foot = gfx('foot.png').convert_alpha()
        # self.foot_part = gfx('foot_part.png').convert_alpha()
        # self.shark = gfx('shark.png').convert_alpha()

        sfx("cat_jump.ogg")
        sfx("eatfish.ogg")
        sfx("splash.ogg")
        sfx("cat_crash.ogg")

        self.meow_names = ["cat_meow01.ogg", "cat_meow02.ogg", "cat_meow03.ogg"]
        self.last_meow = None

        self.touching_ground = True
        self.jumping = False
        self.jumping_time = 0
        self.jump_key = None

        for meow_name in self.meow_names:
            sfx(meow_name)

        self.boing_names = ["boing1.ogg", "boing2.ogg", "boing3.ogg"]
        for boing_name in self.boing_names:
            sfx(boing_name)

        self.people_mad = False
        self.people_mad_duration = 3000  # ms
        self.people_mad_current_time = 0
        self.next_notfish = 0
        self.notfish_time = 0

        self.last_joy_right_tilt = 0
        self.last_joy_left_tilt = 0

        self.left_pressed = False
        self.right_pressed = False
        self.player_data = PlayerData(width, height)

        # timing
        self.dt_scaled = 0
        self.total_time = 0

        # elephant and shark classes
        self.elephant = Elephant(self)
        self.shark_active = False  # is the shark enabled yet
        self.elephant_active = False
        self.cat = Cat(self)
        self.score_text = Score(self)

        self.allsprites = None  # type: Optional[LayeredDirty]
        self.shark = None  # type: Optional[Shark]
        self.init_sprites()

        # lists of things to catch by [posx, posy, velx, vely]
        # self.fish = [[0, height / 2, 10, -5]]
        self.fish = LayeredDirtyAppend()
        self.fish.extend([Fish(self.allsprites, (0, height / 2), (10, -5))])

        self.not_fish = LayeredDirtyAppend()

        self.unicycle_sound = sfx("unicycle.ogg", play=True, loops=-1, fadein=500)

        self._reset_meow()

        # difficulty varibles
        self.number_of_not_fish = 0

    def _reset_meow(self):
        self.next_meow = random.uniform(5000, 10000)

    def _meow(self):
        # Play a meow sound, but not the same one twice in a row
        meow_names = self.meow_names[:]
        if self.last_meow in self.meow_names:
            meow_names.remove(self.last_meow)
        self.last_meow = random.choice(meow_names)
        sfx(self.last_meow, play=1)
        self._reset_meow()

    def init_sprites(self):
        """temp, this will go in the init."""
        sprite_list = [self.elephant, self.cat, self.score_text]
        self.allsprites = LayeredDirty(sprite_list, _time_threshold=1000 / 10.0)
        scene = self
        self.shark = Shark(self.allsprites, scene, self.width, self.height)
        self.allsprites.add(self.shark)
        self.allsprites.clear(self.screen, self.background)

    def reset_on_death(self):
        """Reset on death.

        What to do when you die, reset the level.
        """
        self.player_data.reset()
        self.total_time = 0

        self.elephant.last_animation = 0
        self.elephant.state = 0
        self.elephant.just_happened = None
        self.elephant.dirty = 1
        self.elephant_active = False
        self.elephant.animate(self.total_time)

        # make the shark leave
        self.shark_active = False
        self.shark.last_animation = 0
        self.shark.dirty = True

        if self.shark.get_state() in ("aiming", "fire laser"):
            self.shark.just_happened = None
            self.shark.set_state("leaving")
            self.shark.applaud = False
        else:
            self.shark.just_happened = None
            self.shark.set_state("offscreen")
            self.shark.animate(self.total_time)

        sfx("shark_appear.ogg", fadeout=1000)

        if self.shark.lazer:
            self.shark.lazer.kill()

    def increase_difficulty(self):
        """ Periodically increase the difficulty."""
        self.number_of_not_fish = 0
        if self.player_data.score > 3:
            self.number_of_not_fish = 1
        if self.player_data.score > 9:
            self.number_of_not_fish = 1
        if self.player_data.score > 15:
            self.number_of_not_fish = 2
        if self.player_data.score > 19:
            self.number_of_not_fish = 1
        if self.player_data.score > 25:
            self.number_of_not_fish = 2
        if self.player_data.score > 35:
            self.number_of_not_fish = 3
        if self.player_data.score >= 50:
            self.number_of_not_fish = int((self.player_data.score - 20) / 10)

        if self.player_data.score >= 10:
            self.shark_active = True

        # Elephant doesn't work yet, so let's not use it

    #        if self.player_data.score >= 20:
    #            self.elephant_active = True

    def annoy_crowd(self):
        """ Annoy the crowd."""
        self.people_mad = True
        self.people_mad_current_time = 0

    def render_sprites(self):
        """ Render the sprites."""
        rects = []
        self.allsprites.update(
            time_delta=self.dt_scaled, height=self.height, player_data=self.player_data
        )
        rects.extend(self.allsprites.draw(self.screen))
        return rects

    def render(self):
        rects = []
        if self.first_render:
            self.first_render = False
            rects.append(self.screen.get_rect())
        rects.extend(self.render_sprites())
        return rects

    def tick(self, time_delta):
        self.increase_difficulty()

        self.cat.animate(time_delta)

        self.total_time += (
            time_delta  # keep track of the total number of ms passed during the game
        )
        dt_scaled = time_delta / 17
        self.dt_scaled = dt_scaled
        width, height = self.width, self.height

        ##cat physics
        self.player_data.cat_angular_vel *= (
            0.9 ** dt_scaled
        )  # max(0.9/(max(0.1,dt_scaled)),0.999)

        # make the cat slide in the direction it's rotated
        self.player_data.cat_speed[0] += math.sin(self.player_data.cat_angle) * (
            dt_scaled * self.player_data.cat_roll_speed
        )

        # add gravity
        self.player_data.cat_speed[1] = min(
            self.player_data.cat_speed[1] + (1 * dt_scaled),
            self.player_data.cat_fall_speed_max,
        )

        self.unicycle_sound.set_volume(
            abs(self.player_data.cat_speed[0] / self.player_data.cat_speed_max)
        )

        self._move_cat()
        self._cat_out_of_bounds()

        # check for collision with the elephant stomp
        if self.elephant_active:
            self.elephant.animate(self.total_time)
            self.elephant.collide(width)
        if self.shark_active or self.shark.states[self.shark.state] == "leaving":
            self.shark.animate(self.total_time)
            self.shark.collide(self, width, height, self.player_data.cat_location)

        self._cat_jumping(time_delta)
        self._cats_meow(time_delta)
        self._angry_people(time_delta)
        self._collide_flying_objects()
        self._spawn_flying_objects()

    def _move_cat(self):
        """Move, accelerate, and tilt the cat."""

        # accelerate the cat left or right
        if self.right_pressed:
            self.player_data.cat_speed[0] = min(
                self.player_data.cat_speed[0] + 0.3 * self.dt_scaled,
                self.player_data.cat_speed_max,
            )
            self.player_data.cat_angle -= 0.003 * self.dt_scaled

        if self.left_pressed:
            self.player_data.cat_speed[0] = max(
                self.player_data.cat_speed[0] - 0.3 * self.dt_scaled,
                -self.player_data.cat_speed_max,
            )
            self.player_data.cat_angle += 0.003 * self.dt_scaled

        # make the cat fall
        angle_sign = 1 if self.player_data.cat_angle > 0 else -1
        self.player_data.cat_angular_vel += 0.0002 * angle_sign * self.dt_scaled
        self.player_data.cat_angle += self.player_data.cat_angular_vel * self.dt_scaled
        if (
            self.player_data.cat_angle > math.pi / 2
            or self.player_data.cat_angle < -math.pi / 2
        ) and self.player_data.cat_location[1] > self.height - 160:
            sfx("cat_crash.ogg", play=1)
            self.reset_on_death()

        # move cat
        self.player_data.cat_location[0] += (
            self.player_data.cat_speed[0] * self.dt_scaled
        )
        self.player_data.cat_location[1] += (
            self.player_data.cat_speed[1] * self.dt_scaled
        )
        if (
            self.player_data.cat_location[1] > self.player_data.cat_wire_height
            and self.player_data.cat_location[0] > 0.25 * self.width
        ):
            self.touching_ground = True
            self.player_data.cat_location[1] = self.player_data.cat_wire_height
            self.player_data.cat_speed[1] = 0
        else:
            self.touching_ground = False

    def _cat_out_of_bounds(self):
        """check for out of bounds"""

        # in the pool
        if self.player_data.cat_location[1] > self.height:
            sfx("splash.ogg", play=1)
            self._meow()
            self.reset_on_death()

        # to the right of screen.
        if self.player_data.cat_location[0] > self.width:
            self.player_data.cat_location[0] = self.width
            if self.player_data.cat_angle > 0:
                self.player_data.cat_angle *= 0.7

        self.player_data.cat_head_location = [
            int(
                self.player_data.cat_location[0]
                + 100 * math.cos(self.player_data.cat_angle - math.pi / 2)
            ),
            int(
                self.player_data.cat_location[1]
                + 100 * math.sin(self.player_data.cat_angle - math.pi / 2)
            ),
        ]

        if (
            self.player_data.cat_location[0] > 0.98 * self.width
            and self.player_data.cat_location[1] > self.player_data.cat_wire_height - 30
        ):
            # bump the cat back in
            self._meow()
            sfx(random.choice(self.boing_names), play=True)
            self.player_data.cat_angular_vel -= 0.01 * self.dt_scaled
            self.player_data.cat_speed[0] = -5
            self.player_data.cat_speed[1] = -20
            # self.reset_on_death()
        if (
            self.player_data.cat_location[0] < 0.25 * self.width
            and self.player_data.cat_location[1] > self.player_data.cat_wire_height - 30
        ):
            pass

    def _cat_jumping(self, time_delta):
        """jumping physics"""
        if self.jumping:
            self.player_data.cat_speed[1] -= (
                time_delta
                * ((CAT_MAX_JUMPING_TIME - self.jumping_time) / CAT_MAX_JUMPING_TIME)
                * CAT_JUMP_SPEED
            )
            self.jumping_time += time_delta
            if self.jumping_time >= CAT_MAX_JUMPING_TIME:
                self.jumping = False

    def _cats_meow(self, time_delta):
        """meow timing"""
        if self.next_meow <= 0:
            self._meow()
        self.next_meow -= time_delta

    def _angry_people(self, time_delta):
        """angry people (increased throwing of not-fish)"""

        if self.people_mad:
            self.people_mad_current_time += time_delta
            self.notfish_time += time_delta
            if self.notfish_time >= self.next_notfish:
                self.next_notfish = random.randint(100, 400)
                self.notfish_time = 0
                self._spawn_not_fish()
            if self.people_mad_current_time >= self.people_mad_duration:
                self.people_mad = False

    def _collide_flying_objects(self):
        """object physics"""
        height = self.height
        dt_scaled = self.dt_scaled

        # move fish and not fish
        for fish in reversed(self.fish.sprites()):
            fish.pos[0] += fish.velocity[0] * dt_scaled  # speed of the throw
            fish.velocity[1] += 0.2 * dt_scaled  # gravity
            fish.pos[1] += fish.velocity[1] * dt_scaled  # y velocity
            # check out of bounds
            if fish.pos[1] > height:
                self.fish.remove(fish)
                fish.kill()
        for fish in reversed(self.not_fish.sprites()):
            fish.pos[0] += fish.velocity[0] * dt_scaled  # speed of the throw
            fish.velocity[1] += 0.2 * dt_scaled  # gravity
            fish.pos[1] += fish.velocity[1] * dt_scaled  # y velocity
            # check out of bounds
            if fish.pos[1] > height:
                self.not_fish.remove(fish)
                fish.kill()

        # check collision with the cat
        for fish in reversed(self.fish.sprites()):
            if (
                distance(
                    [fish.rect[0], fish.rect[1]], self.player_data.cat_head_location
                )
                < 100
            ):
                self.player_data.increment_score()
                self.fish.remove(fish)
                sfx("eatfish.ogg", play=1)
                fish.kill()
        for fish in reversed(self.not_fish.sprites()):
            if (
                distance(
                    [fish.rect[0], fish.rect[1]], self.player_data.cat_head_location
                )
                < 50
            ):
                self.not_fish.remove(fish)
                fish.kill()
                self.player_data.angle_to_not_fish = (
                    math.atan2(
                        self.player_data.cat_head_location[1] - fish.rect[1],
                        self.player_data.cat_head_location[0] - fish.rect[0],
                    )
                    - math.pi / 2
                )
                side = 1 if self.player_data.angle_to_not_fish < 0 else -1
                self.player_data.cat_angular_vel += side * random.uniform(0.08, 0.15)
                sfx(random.choice(self.boing_names), play=True)

    def _spawn_flying_objects(self):
        """Throws random objects at the cat."""
        width, height = self.width, self.height

        # refresh lists
        while len(self.fish) < 1 and not self.people_mad:
            # choose a side of the screen
            if random.choice([0, 1]) == 0:
                self.fish.append(
                    Fish(
                        self.allsprites,
                        (0, height / 2),  # random.randint(0, height / 2),
                        (random.randint(3, 7), -random.randint(5, 12)),
                    )
                )
            else:
                self.fish.append(
                    Fish(
                        self.allsprites,
                        (width, height / 2),  # random.randint(0, height / 2),
                        (-random.randint(3, 7), -random.randint(5, 12)),
                    )
                )
        while len(self.not_fish) < self.number_of_not_fish:
            self._spawn_not_fish()

    def _spawn_not_fish(self):
        """Choose a side of the screen."""

        velocity_multiplier = 1
        x_pos = 0
        if random.randint(0, 1):
            velocity_multiplier *= -1
            x_pos = self.width
        self.not_fish.append(
            NotFish(
                self.allsprites,
                (x_pos, self.height / 2),
                (random.randint(3, 7) * velocity_multiplier, -random.randint(5, 12)),
            )
        )

    def _start_jump(self, key):
        self.jump_key = key
        if self.touching_ground and not self.jumping:
            self.jumping = True
            self.jumping_time = 0
            self.player_data.cat_speed[1] -= 12.5
            sfx("cat_jump.ogg", play=1)

    def _stop_jump(self):
        self.jumping = False
        sfx("cat_jump.ogg", fadeout=50)

    def _tilt_left(self):
        self.player_data.cat_angular_vel -= random.uniform(
            0.01 * math.pi, 0.03 * math.pi
        )

    def _tilt_right(self):
        self.player_data.cat_angular_vel += random.uniform(
            0.01 * math.pi, 0.03 * math.pi
        )

    def _event_keydown(self, event):
        if event.key == pygame.K_RIGHT:
            self.right_pressed = True
        elif event.key == pygame.K_LEFT:
            self.left_pressed = True
        elif event.key == pygame.K_a:
            self._tilt_left()
        elif event.key == pygame.K_d:
            self._tilt_right()
        elif event.key in (pygame.K_UP, pygame.K_SPACE):
            self._start_jump(event.key)

    def _event_keyup(self, event):
        if event.key == self.jump_key:
            self._stop_jump()
        elif event.key == pygame.K_RIGHT:
            self.right_pressed = False
        elif event.key == pygame.K_LEFT:
            self.left_pressed = False

    def _event_joybuttondown(self, event):
        if event.button in JOY_JUMP_BUTTONS:
            self._start_jump("JOY" + str(event.button))
        if event.button in JOY_LEFT_BUTTONS:
            self._tilt_left()
        if event.button in JOY_RIGHT_BUTTONS:
            self._tilt_right()

    def _event_joybuttonup(self, event):
        if "JOY" + str(event.button) == self.jump_key:
            self._stop_jump()

    def _event_joyaxismotion(self, event):
        if event.axis == 0:
            if event.value >= JOY_SENSE:
                self.right_pressed = True
                self.left_pressed = False
            elif event.value <= -JOY_SENSE:
                self.right_pressed = False
                self.left_pressed = True
            else:
                self.right_pressed = False
                self.left_pressed = False
        if event.axis == JOY_TILT_RIGHT_AXIS:
            # if self.last_joy_right_tilt < JOY_SENSE and event.value >= JOY_SENSE:
            if self.last_joy_right_tilt < JOY_SENSE < event.value:
                self._tilt_right()
            self.last_joy_right_tilt = event.value
        if event.axis == JOY_TILT_LEFT_AXIS:
            # if self.last_joy_left_tilt < JOY_SENSE and event.value >= JOY_SENSE:
            if self.last_joy_left_tilt < JOY_SENSE < event.value:
                self._tilt_left()
            self.last_joy_left_tilt = event.value

    def event(self, event):
        if event.type == pygame.KEYDOWN:
            self._event_keydown(event)
        elif event.type == pygame.KEYUP:
            self._event_keyup(event)
        elif event.type == pygame.JOYBUTTONDOWN:
            self._event_joybuttondown(event)
        elif event.type == pygame.JOYBUTTONUP:
            self._event_joybuttonup(event)
        elif event.type == pygame.JOYAXISMOTION:
            self._event_joyaxismotion(event)