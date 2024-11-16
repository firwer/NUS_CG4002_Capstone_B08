using System;

namespace GameDataNameSpace
{
    public class GameState
    {
        public int hp { get; set; }
        public int bullets { get; set; }
        public int bombs { get; set; }
        public int shield_hp { get; set; }
        public int deaths { get; set; }
        public int shields { get; set; }
    }

    public static class GameConfig
    {
        public const int GAME_MAX_HP = 100;
        public const int GAME_MAX_BULLETS = 6;
        public const int GAME_MAX_BOMBS = 2;
        public const int GAME_MAX_SHIELD_HEALTH = 30;
        public const int GAME_MAX_SHIELDS = 3;
        public const int GAME_BULLET_DMG = 5;
        public const int GAME_AI_DMG = 10;
        public const int GAME_BOMB_DMG = 5;
    }

    public class PlayerData
    {
        public int player_id { get; set; }
        public string action { get; set; }
        public GameState game_state { get; set; }
    }
}