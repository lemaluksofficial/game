import unittest
import pygame
from world.tilemap import TileMap
from entities.objects import Player


class TestGameLogic(unittest.TestCase):
    """Tests for core game logic, collisions, and player states."""

    @classmethod
    def setUpClass(cls):
        # Init Pygame in headless mode for testing (no window will open)
        # Needed for Rect calculations and handling surfaces
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)

    def setUp(self):
        """Set up a basic level and player before each test."""
        self.tilemap = TileMap("level1")
        spawn_x, spawn_y = self.tilemap.find_player_spawn()
        self.player = Player(None, self.tilemap, spawn_x, spawn_y)

    def test_tilemap_loading(self):
        """Check if the tilemap loads with valid dimensions."""
        self.assertGreater(self.tilemap.width, 0)
        self.assertGreater(self.tilemap.height, 0)

    def test_is_solid_logic(self):
        """Test wall collisions and map boundaries."""
        # Treat Out-of-Bounds (OOB) coordinates as solid walls
        self.assertTrue(self.tilemap.is_solid(-1, -1))

    def test_player_initial_state(self):
        """Check if the player starts with the correct defaults and position."""
        self.assertTrue(self.player.alive)
        self.assertFalse(self.player.moving)
        self.assertEqual(self.player.x, self.player.spawn_tile_x * 32)

    def test_player_death_logic(self):
        """Test if the player dies correctly and the timer starts."""
        self.player.kill(death_duration=1.0)
        self.assertFalse(self.player.alive)
        self.assertEqual(self.player.death_timer, 1.0)

    def test_player_reset(self):
        """Test if the player resets to the starting state and position."""
        self.player.kill()
        self.player.reset_to_start()
        self.assertTrue(self.player.alive)
        self.assertEqual(self.player.x, self.player.spawn_tile_x * 32)


if __name__ == "__main__":
    unittest.main()