import pygame
import sys
import traceback
import os
import json

# Set working directory to project root
project_root = r"C:\Users\adm\Documents\[x]Code\BattleShips\BattleShipsPython"
os.chdir(project_root)
sys.path.append(project_root)

try:
    print("Initializing Pygame...")
    pygame.init()
    
    from settings import WIDTH, HEIGHT
    print(f"Resolution: {WIDTH}x{HEIGHT}")
    
    print("Setting display mode...")
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    
    print("Importing game module...")
    import game
    
    print("Testing if battle_phase variables are defined (simulated call start)...")
    # Mocking arguments for battle_phase
    class MockNet:
        def __init__(self):
            self.client = None
    
    # We won't actually call it because of the while True loop, 
    # but we can check the bytecode or just check if the function exists.
    if hasattr(game, 'battle_phase'):
        print("battle_phase function exists.")
    else:
        raise Exception("battle_phase function NOT found!")

    print("Checking if load_spritesheet works...")
    game.load_spritesheet("wybuch.png", 6, 8, (100, 100))
    print("load_spritesheet OK")

    print("Restoration check successful!")

except Exception as e:
    print("\n--- CRASH DETECTED ---")
    traceback.print_exc()
    sys.exit(1)
finally:
    pygame.quit()
