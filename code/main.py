from settings import *
from player import Player
from sprites import * 
from groups import AllSprites 
from pytmx.util_pygame import load_pygame
from random import randint, choice

class Game(pygame.sprite.Sprite):
    def __init__(self):
        pygame.init()
        self.running = True
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Vampire survivor")
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(join("data", "Font", "Pixeltype.ttf"), 160)
        self.score_font = pygame.font.Font(join("data", "Font", "Pixeltype.ttf"), 70)
        self.start_again_font  = pygame.font.Font(join("data", "Font", "Pixeltype.ttf"), 100)
        self.main_score_font = pygame.font.Font(join("data", "Font", "Oxanium-Bold.ttf"), 85)
        self.score = 0
        self.health = 100

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        # gun timer
        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 150

        # enemy timer
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 500)
        self.spawn_positions = []
        
        # audio
        self.shoot_sound = pygame.mixer.Sound(join("audio", "shoot.wav"))
        self.shoot_sound.set_volume(0.4)
        self.impact_sound = pygame.mixer.Sound(join("audio", "impact.ogg"))
        self.impact_sound.set_volume(0.4)
        self.music = pygame.mixer.Sound(join("audio", "music.wav"))
        self.music.set_volume(0.4)
        # self.music.play(-1)

        # setup        
        self.game_active = False
        self.load_images()
        self.setup()

    def load_images(self):
        # gun images
        self.bullet_surf = pygame.image.load(join("images", "gun", "bullet.png")).convert_alpha()

        # enemy images
        folders = list(walk(join("images", "enemies")))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join("images", "enemies", folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key= lambda name: int(name.split(".")[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)
                    
    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot_sound.play()
            pos = self.gun.rect.center + self.gun.player_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True
            
    def setup(self):
        map = load_pygame(join("data", "maps", "world.tmx"))
        for x,y,image in map.get_layer_by_name("Ground").tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        for obj in map.get_layer_by_name("Objects"):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in map.get_layer_by_name("Collisions"):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name("Entities"):
            if obj.name == "Player":
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x, obj.y))

    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.score += 1
                    self.impact_sound.play()
                    for sprite in collision_sprites:
                        sprite.destroy()
                    bullet.kill()

    def player_collision(self):
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.game_active = False

    def end_screen(self):
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.bullet_sprites.empty()
        self.enemy_sprites.empty()

        # text
        self.title_screen = self.title_font.render("Vampire Survivor", True, "White")
        self.title_screen_rect = self.title_screen.get_rect(center = (640, 100))

        self.show_score = self.score_font.render(f"Score: {self.score}", True, "White")
        self.show_score_rect = self.show_score.get_rect(center = (640, 180))

        self.play_again = self.start_again_font.render("Press 'space' to play again", True, "White")
        self.play_again_rect = self.play_again.get_rect(center = (640, 620))

        self.show_player = pygame.image.load(join("images", "enemies", "skeleton", "0.png")).convert_alpha()
        self.show_player = pygame.transform.scale2x(self.show_player)
        self.show_player_rect = self.show_player.get_rect(center = (640, 400))

        # display
        self.display_surface.fill("black")
        self.display_surface.blit(self.title_screen, self.title_screen_rect)
        self.display_surface.blit(self.show_score, self.show_score_rect)
        self.display_surface.blit(self.play_again, self.play_again_rect)
        self.display_surface.blit(self.show_player, self.show_player_rect)

        pygame.display.update()

    def start_over(self):
        self.keys = pygame.key.get_pressed()
        if self.keys[pygame.K_SPACE]:
            self.score = 0 
            self.game_active = True
            self.load_images()
            self.setup()
    
    def show_score_main(self, score):
        self.display_score = self.main_score_font.render(str(score), True, "white")
        self.display_score_rect = self.display_score.get_rect(center = (640, 640))
        pygame.draw.rect(self.display_surface, 'white', self.display_score_rect.inflate(20, 10).move(0, -3), 5, 10)
        self.display_surface.blit(self.display_score, self.display_score_rect)

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000
        
            if self.game_active:
                #EVENT LOOP
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == self.enemy_event:
                        Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

                # update
                self.gun_timer()
                self.input()
                self.player.move(dt)
                self.all_sprites.update(dt)
                self.bullet_collision()
                self.player_collision()

                # draw
                self.display_surface.fill("black")
                self.all_sprites.draw(self.player.rect.center)
                self.show_score_main(self.score)
                pygame.display.update()

            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                
                self.end_screen()
                self.start_over()
                

        pygame.quit()
if __name__ == "__main__":
    game = Game()
    game.run()