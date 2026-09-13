#!/usr/bin/env python3
"""CADENCE FORGE — neon rhythm-tap arcade. Python 3 + pygame. ElbowOS."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
if RECORD:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

W, H, FPS = 1080, 1920, 30
TITLE = "CADENCE FORGE"
HANDLE = "x.com/ElbowOS"
OUT = os.environ.get(
    "ELBOWOS_MP4",
    "/home/workdir/artifacts/CADENCE_FORGE_ElbowOS.mp4",
)
BG = (12, 8, 22)
INK = (18, 12, 32)
MINT = (72, 255, 186)
CORAL = (255, 92, 108)
AMBER = (255, 186, 64)
LILAC = (196, 140, 255)
WHITE = (246, 240, 255)
LANE_COLS = (MINT, CORAL, AMBER, LILAC)
KEYS = (pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k)
N_LANES = 4
HIT_Y = 1580
NOTE_H = 36
FALL = 980
JUDGE = 58


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, col):
        a = random.uniform(-2.6, -0.5)
        sp = random.uniform(90, 520)
        self.x, self.y, self.vx, self.vy = x, y, math.cos(a) * sp, math.sin(a) * sp
        self.life = random.uniform(0.18, 0.5)
        self.col, self.r = col, random.randint(2, 6)

    def tick(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 420 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, s):
        pygame.draw.circle(s, self.col, (int(self.x), int(self.y)), max(1, self.r))


class Note:
    __slots__ = ("lane", "y", "hit")

    def __init__(self, lane, y):
        self.lane, self.y, self.hit = lane, y, False


class Game:
    def __init__(self):
        self.t = 0.0
        self.score = 0
        self.combo = 0
        self.best = 0
        self.hits = 0
        self.misses = 0
        self.notes = []
        self.sparks = []
        self.flashes = [0.0] * N_LANES
        self.spawn_acc = 0.0
        self.spawn_iv = 0.42
        self.beat = 0
        self.floaters = []
        self.stars = [
            (random.randrange(W), random.randrange(H), random.randint(1, 3),
             random.choice(LANE_COLS + (WHITE,)))
            for _ in range(80)
        ]
        self.lane_w = 188
        self.gap = 28
        total = N_LANES * self.lane_w + (N_LANES - 1) * self.gap
        self.ox = (W - total) // 2
        for i in range(8):
            self.notes.append(Note(i % N_LANES, -80 - i * 220))

    def lane_x(self, i):
        return self.ox + i * (self.lane_w + self.gap)

    def burst(self, x, y, col, n=18):
        for _ in range(n):
            self.sparks.append(Spark(x, y, col))

    def judge_lane(self, i):
        self.flashes[i] = 0.16
        best, pick = 9999.0, None
        for n in self.notes:
            if n.lane != i or n.hit:
                continue
            d = abs(n.y - HIT_Y)
            if d < best:
                best, pick = d, n
        if pick is None or best > JUDGE * 1.6:
            self.combo = 0
            self.misses += 1
            self.floaters.append([self.lane_x(i) + self.lane_w // 2, HIT_Y - 40, "MISS", CORAL, 0.5])
            return
        pick.hit = True
        self.hits += 1
        self.combo += 1
        self.best = max(self.best, self.combo)
        if best < 16:
            pts, tag = 300 + self.combo * 8, "PERFECT"
        elif best < 34:
            pts, tag = 180 + self.combo * 4, "GREAT"
        else:
            pts, tag = 80 + self.combo * 2, "OK"
        self.score += pts
        col = LANE_COLS[i]
        cx = self.lane_x(i) + self.lane_w // 2
        self.burst(cx, HIT_Y, col, 22)
        self.floaters.append([cx, HIT_Y - 50, tag, col, 0.55])

    def autoplay(self):
        for i in range(N_LANES):
            for n in self.notes:
                if n.lane == i and not n.hit and abs(n.y - HIT_Y) < 22:
                    self.judge_lane(i)
                    break

    def tick(self, dt, keys, auto):
        self.t += dt
        self.spawn_acc += dt
        self.spawn_iv = max(0.26, 0.42 - self.t * 0.008)
        while self.spawn_acc >= self.spawn_iv:
            self.spawn_acc -= self.spawn_iv
            self.beat += 1
            pattern = [self.beat % N_LANES]
            if self.beat % 5 == 0:
                pattern.append((self.beat + 2) % N_LANES)
            if self.beat % 7 == 0:
                pattern = [random.randrange(N_LANES)]
            for ln in pattern:
                self.notes.append(Note(ln, -60))
        speed = FALL + min(260, self.t * 12)
        live = []
        for n in self.notes:
            n.y += speed * dt
            if n.hit:
                continue
            if n.y > HIT_Y + 90:
                self.combo = 0
                self.misses += 1
                continue
            live.append(n)
        self.notes = live
        self.sparks = [p for p in self.sparks if p.tick(dt)]
        self.flashes = [max(0.0, f - dt) for f in self.flashes]
        kept = []
        for fl in self.floaters:
            fl[1] -= 90 * dt
            fl[4] -= dt
            if fl[4] > 0:
                kept.append(fl)
        self.floaters = kept
        if auto:
            self.autoplay()
        elif keys:
            for i, k in enumerate(KEYS):
                if keys[k]:
                    pass

    def draw(self, s, font, big, tiny):
        s.fill(BG)
        pulse = 18 + int(14 * abs(math.sin(self.t * 3.1)))
        pygame.draw.circle(s, (28, 14, 48), (W // 2, 420), 380 + pulse)
        pygame.draw.circle(s, (20, 10, 36), (W // 2, 420), 220)
        for x, y, r, c in self.stars:
            yy = (y + int(self.t * (14 + r * 8))) % H
            pygame.draw.circle(s, c, (x, yy), r)
        pts = []
        for x in range(0, W + 8, 8):
            y = 360 + int(46 * math.sin(x * 0.018 + self.t * 4.2) * math.sin(self.t * 1.7))
            pts.append((x, y))
        if len(pts) > 1:
            pygame.draw.lines(s, (60, 30, 90), False, pts, 3)
        top = 220
        bot = 1760
        pygame.draw.rect(s, INK, (self.ox - 24, top, N_LANES * self.lane_w + (N_LANES - 1) * self.gap + 48, bot - top),
                         border_radius=22)
        pygame.draw.rect(s, LILAC, (self.ox - 24, top, N_LANES * self.lane_w + (N_LANES - 1) * self.gap + 48, bot - top),
                         3, border_radius=22)
        for i in range(N_LANES):
            x = self.lane_x(i)
            col = LANE_COLS[i]
            dim = tuple(max(8, v // 6) for v in col)
            pygame.draw.rect(s, dim, (x, top + 16, self.lane_w, bot - top - 32), border_radius=14)
            if self.flashes[i] > 0:
                glow = pygame.Surface((self.lane_w, bot - top - 32), pygame.SRCALPHA)
                glow.fill((*col, int(90 * self.flashes[i] / 0.16)))
                s.blit(glow, (x, top + 16))
            pygame.draw.rect(s, col, (x, HIT_Y - 10, self.lane_w, 20), border_radius=8)
            pygame.draw.rect(s, WHITE, (x + 8, HIT_Y - 4, self.lane_w - 16, 8), border_radius=4)
            label = tiny.render("DFJK"[i], True, col)
            s.blit(label, (x + self.lane_w // 2 - label.get_width() // 2, bot - 48))
        for n in self.notes:
            x = self.lane_x(n.lane)
            col = LANE_COLS[n.lane]
            pygame.draw.rect(s, col, (x + 18, int(n.y) - NOTE_H // 2, self.lane_w - 36, NOTE_H), border_radius=10)
            pygame.draw.rect(s, WHITE, (x + 28, int(n.y) - 6, self.lane_w - 56, 12), border_radius=6)
        for p in self.sparks:
            p.draw(s)
        for fl in self.floaters:
            img = font.render(fl[2], True, fl[3])
            s.blit(img, img.get_rect(center=(int(fl[0]), int(fl[1]))))
        bar = pygame.Surface((W, 168), pygame.SRCALPHA)
        bar.fill((8, 4, 16, 230))
        s.blit(bar, (0, 0))
        s.blit(big.render(TITLE, True, AMBER), (40, 16))
        s.blit(font.render(f"SCORE  {self.score:06d}   COMBO {self.combo}   BEST {self.best}", True, MINT), (40, 100))
        s.blit(tiny.render(HANDLE, True, CORAL), (W - 360, 36))
        acc = 100 if self.hits + self.misses == 0 else int(100 * self.hits / (self.hits + self.misses))
        s.blit(tiny.render(f"HITS {self.hits}   MISS {self.misses}   ACC {acc}%", True, LILAC), (40, H - 64))
        pygame.draw.line(s, AMBER, (0, 168), (W, 168), 3)
        pygame.draw.line(s, CORAL, (0, H - 88), (W, H - 88), 2)


def record_reel(game, surf, font, big, tiny):
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "fast", "-movflags", "+faststart", OUT,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    frames = FPS * 15
    dt = 1.0 / FPS
    try:
        for _ in range(frames):
            game.tick(dt, None, auto=True)
            game.draw(surf, font, big, tiny)
            proc.stdin.write(pygame.image.tostring(surf, "RGB"))
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
        rc = proc.wait(timeout=60)
        if rc != 0:
            raise RuntimeError(err[-2000:])
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        raise


def main():
    pygame.init()
    pygame.font.init()
    if RECORD:
        screen = pygame.Surface((W, H))
    else:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(f"{TITLE} — {HANDLE}")
    font = pygame.font.SysFont("DejaVu Sans Mono", 34, bold=True)
    big = pygame.font.SysFont("DejaVu Sans", 62, bold=True)
    tiny = pygame.font.SysFont("DejaVu Sans Mono", 26, bold=True)
    game = Game()
    if RECORD:
        record_reel(game, screen, font, big, tiny)
        print("WROTE", OUT)
        pygame.quit()
        return
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                game = Game()
            if e.type == pygame.KEYDOWN:
                for i, k in enumerate(KEYS):
                    if e.key == k:
                        game.judge_lane(i)
        game.tick(dt, pygame.key.get_pressed(), auto=False)
        game.draw(screen, font, big, tiny)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
