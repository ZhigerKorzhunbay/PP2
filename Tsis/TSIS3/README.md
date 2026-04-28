# TSIS3 Compact Street Racer

Compact single-file version of the Pygame race project.

## Run

```bash
pip install pygame
python main.py
```

## Files

- `main.py` — all game logic, UI, persistence, sprites.
- `settings.json` — saved sound/difficulty.
- `leaderboard.json` — top 10 scores.
- `assets/` — images and sounds.

## Notes

The road fills the whole window width. The game is endless until the player loses. Difficulty changes the initial speed and obstacle spawn frequency: Easy spawns fewer obstacles, Hard spawns more.

Nitro now works like a temporary ram mode: while it is active, the player can destroy traffic cars, barriers, moving barriers, and slow-down zones without losing.
