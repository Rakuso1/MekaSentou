from __future__ import annotations
from enum import Enum
import random
import time
import os
import math
import json
from datetime import date

# --- Combat --------------------------------------------------------------
STANDARD_CRIT_CHANCE: float = 0.25 # 25% chance for standard ammo to critically hit
CRIT_DAMAGE_MULTIPLIER: int = 4 # Critical hits do 4x damage
DAMAGE_VARIANCE: int = 2 # Damage can vary by ±2 points

# --- Heat ----------------------------------------------------------------
MAX_HEAT: int = 100
HEAT_GAIN_MIN: int = 10
HEAT_GAIN_MAX: int = 15

# --- Ammo ----------------------------------------------------------------
MAX_STANDARD_AMMO: int = 10
MAX_SPECIAL_AMMO: int = 10
STANDARD_AMMO_RELOAD_AMOUNT: int = 10
SPECIAL_AMMO_RELOAD_AMOUNT: int = 5

# --- Shield Recharge -----------------------------------------------------
SHIELD_RECHARGE_COST_RATE: float = 0.2 # 20% of current power
SHIELD_RECHARGE_GAIN_RATE: float = 0.8 # 80% of missing shield

# --- Level Up Bonuses ----------------------------------------------------
LEVEL_UP_POWER_BONUS: int = 20
LEVEL_UP_ARMOR_BONUS: int = 10
LEVEL_UP_SHIELD_BONUS: int = 10
LEVEL_UP_ATTACK_BONUS: int = 5
POST_BATTLE_HEAL_RATE: float = 0.5 # Heal 50% of max power after each victory

# --- Enemy Scaling -------------------------------------------------------
ENEMY_BASE_POWER: int = 80
ENEMY_POWER_PER_WAVE: int = 10
ENEMY_MAX_POWER: int = 300

ENEMY_BASE_ARMOR: int = 20
ENEMY_ARMOR_PER_WAVE: int = 5
ENEMY_MAX_ARMOR: int = 150

ENEMY_BASE_SHIELD: int = 10
ENEMY_SHIELD_PER_WAVE: int = 5
ENEMY_MAX_SHIELD: int = 150

ENEMY_BASE_ATTACK: int = 4
ENEMY_ATTACK_PER_WAVE: int = 1
ENEMY_MAX_ATTACK: int = 20

ENEMY_BASE_STANDARD_AMMO: int = 5
ENEMY_BASE_SPECIAL_AMMO: int = 3

# --- Enemy AI ------------------------------------------------------------
ENEMY_SHIELD_THREAT_THRESHOLD: int = 1 # If player's shield is above this, enemy prioritizes shield breaker
ENEMY_ARMOR_THREAT_THRESHOLD: int = 1 # If player's armor is above this, enemy prioritizes armor piercing
ENEMY_RELOAD_THREAT_THRESHOLD: int = 10 # If player shield / armor is above this and enemy is out of corresponding ammo, enemy prioritizes reloading that ammo

# --- Player Starting Stats -----------------------------------------------
PLAYER_START_POWER: int = 100
PLAYER_START_HEAT: int = 0
PLAYER_START_ARMOR: int = 50
PLAYER_START_SHIELD: int = 50
PLAYER_START_STANDARD_AMMO: int = 10
PLAYER_START_ARMOR_PIERCING_AMMO: int = 10
PLAYER_START_SHIELD_BREAKER_AMMO: int = 10
PLAYER_START_ATTACK: int = 10

# --- UI ------------------------------------------------------------------
STATUS_BAR_LENGTH: int = 10

# --- Game Settings -------------------------------------------------------
MAX_LEADERBOARD_SCORES: int = 10

LEADERBOARD_FILE = "leaderboard.json"

class AmmoType(Enum):
    STANDARD = "standard"
    ARMOR_PIERCING = "armor_piercing"
    SHIELD_BREAKER = "shield_breaker"

AMMO_TYPES: dict[str, AmmoType] = {
    "1": AmmoType.STANDARD,
    "2": AmmoType.ARMOR_PIERCING,
    "3": AmmoType.SHIELD_BREAKER,
}

class ActionType(Enum):
    ATTACK = "attack"
    COOL_DOWN = "cool_down"
    RELOAD = "reload"
    RECHARGE_SHIELD = "recharge_shield"

def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')

class MekaDisplay:
    @staticmethod
    def make_bar(value: int, max_value: int) -> str:
        filled = int((value / max_value) * STATUS_BAR_LENGTH) if max_value else 0
        filled = max(0, min(STATUS_BAR_LENGTH, filled))
        empty = STATUS_BAR_LENGTH - filled
        return "█" * filled + "-" * empty
    
    @staticmethod
    def render_status(meka: "Meka") -> None:
        print(f"\n{meka.pilot_name}")
        print(f"Power:  [{MekaDisplay.make_bar(meka.power, meka.max_power)}] {meka.power}/{meka.max_power}")
        print(f"Heat:   [{MekaDisplay.make_bar(meka.heat, MAX_HEAT)}] {meka.heat}/{MAX_HEAT}")
        print(f"Armor:  [{MekaDisplay.make_bar(meka.armor, meka.max_armor)}] {meka.armor}/{meka.max_armor}")
        print(f"Shield: [{MekaDisplay.make_bar(meka.shield, meka.max_shield)}] {meka.shield}/{meka.max_shield}")
        print(f"Ammo:   {meka.ammo_total()}")
        print(f"  Standard:        [{MekaDisplay.make_bar(meka.ammo.get(AmmoType.STANDARD, 0), MAX_STANDARD_AMMO)}] {meka.ammo.get(AmmoType.STANDARD, 0)}/{MAX_STANDARD_AMMO}")
        print(f"  Armor Piercing:   [{MekaDisplay.make_bar(meka.ammo.get(AmmoType.ARMOR_PIERCING, 0), MAX_SPECIAL_AMMO)}] {meka.ammo.get(AmmoType.ARMOR_PIERCING, 0)}/{MAX_SPECIAL_AMMO}")
        print(f"  Shield Breaker:   [{MekaDisplay.make_bar(meka.ammo.get(AmmoType.SHIELD_BREAKER, 0), MAX_SPECIAL_AMMO)}] {meka.ammo.get(AmmoType.SHIELD_BREAKER, 0)}/{MAX_SPECIAL_AMMO}")


class Meka:
    def __init__(
        self,
        name: str,
        power: int,
        heat: int,
        armor: int,
        shield: int,
        ammo: dict[AmmoType, int],
        attack: int
    ) -> None:
        self.pilot_name: str = name
        self.power: int = power
        self.max_power: int = power
        self.heat: int = heat
        self.armor: int = armor
        self.max_armor: int = armor
        self.shield: int = shield
        self.max_shield: int = shield
        self.ammo: dict[AmmoType, int] = ammo
        self.attack: int = attack
        self.exp: int = 0
        self.level: int = 1

    def level_up(self) -> None:
        self.level += 1
        MekaDisplay.render_status(self)
        print(f"\nLevel Up! You are now level {self.level}. Choose your upgrade:")
        print(f"1. Increase Max Power (+{LEVEL_UP_POWER_BONUS})")
        print(f"2. Increase Armor (+{LEVEL_UP_ARMOR_BONUS})")
        print(f"3. Increase Shield (+{LEVEL_UP_SHIELD_BONUS})")
        print(f"4. Increase Attack (+{LEVEL_UP_ATTACK_BONUS})")
        choice = input(">> ")

        if choice == "1":
            self.max_power += LEVEL_UP_POWER_BONUS
            self.power += LEVEL_UP_POWER_BONUS
            print(f"Max Power increased by {LEVEL_UP_POWER_BONUS}!")

        elif choice == "2":
            self.max_armor += LEVEL_UP_ARMOR_BONUS
            self.armor += LEVEL_UP_ARMOR_BONUS
            print(f"Armor increased by {LEVEL_UP_ARMOR_BONUS}!")

        elif choice == "3":
            self.max_shield += LEVEL_UP_SHIELD_BONUS
            self.shield += LEVEL_UP_SHIELD_BONUS
            print(f"Shield increased by {LEVEL_UP_SHIELD_BONUS}!")

        elif choice == "4":
            self.attack += LEVEL_UP_ATTACK_BONUS
            print(f"Attack increased by {LEVEL_UP_ATTACK_BONUS}!")

        else:
            self.attack += LEVEL_UP_ATTACK_BONUS
            print(f"Attack increased by {LEVEL_UP_ATTACK_BONUS} by default!")

        heal = math.ceil(self.max_power * POST_BATTLE_HEAL_RATE)
        self.power = min(self.max_power, self.power + heal)
        print(f"Emergency repairs complete! Power restored by {heal} points.")

    def ammo_total(self) -> int:
        return sum(self.ammo.values())

    def has_ammo(self, ammo_type: AmmoType) -> bool:
        return self.ammo.get(ammo_type, 0) > 0

    def consume_ammo(self, ammo_type: AmmoType) -> None:
        if self.has_ammo(ammo_type):
            self.ammo[ammo_type] -= 1

    def reload_ammo(self, ammo_type: AmmoType) -> None:
        if ammo_type == AmmoType.STANDARD:
            self.ammo[ammo_type] = min(self.ammo.get(ammo_type, 0) + STANDARD_AMMO_RELOAD_AMOUNT, MAX_STANDARD_AMMO)
        else:
            self.ammo[ammo_type] = min(self.ammo.get(ammo_type, 0) + SPECIAL_AMMO_RELOAD_AMOUNT, MAX_SPECIAL_AMMO)
    
    def is_alive(self) -> bool:
        return self.power > 0
    
    def take_damage(self, damage: int, ammo_type: AmmoType) -> None:
        shield_multiplier = 2 if ammo_type == AmmoType.SHIELD_BREAKER else 1
        armor_multiplier = 2 if ammo_type == AmmoType.ARMOR_PIERCING else 1

        # Apply to shield layer first. If the shield is reduced to 0, leftover damage is lost.
        if damage > 0 and self.shield > 0:
            damage = self._absorb(damage, "shield", shield_multiplier)

        # Apply to armor layer. If the armor is reduced to 0, leftover damage is lost.
        if damage > 0 and self.armor > 0:
            damage = self._absorb(damage, "armor", armor_multiplier)

        if damage > 0:
            self.power = max(0, self.power - damage)

    def _absorb(self, damage: int, layer: str, multiplier: int) -> int:
        current = getattr(self, layer)
        effective_damage = min(current, damage * multiplier)
        setattr(self, layer, current - effective_damage)

        if getattr(self, layer) == 0:
            return 0
        else:
            return max(0, damage - math.ceil(effective_damage / multiplier))

    def check_overheat(self) -> bool:
        return self.heat >= MAX_HEAT
    
    def apply_heat(self) -> None:
        self.heat = min(self.heat + random.randint(HEAT_GAIN_MIN, HEAT_GAIN_MAX), MAX_HEAT)
    
    def cool_down(self) -> None:
        self.heat = 0 

    def recharge_shield(self) -> None:
        cost = math.ceil(self.power * SHIELD_RECHARGE_COST_RATE)
        missing_shield = self.max_shield - self.shield
        gain = math.ceil(missing_shield * SHIELD_RECHARGE_GAIN_RATE)
        self.power = max(0, self.power - cost) 
        self.shield = min(self.shield + gain, self.max_shield) 

    def available_ammo_types(self) -> list[AmmoType]:
        return [ammo_type for ammo_type, count in self.ammo.items() if count > 0]

class Game:
    def __init__(self, player: Meka) -> None:
        self.player: Meka = player
        self.enemy: Meka | None = None
        self.wave: int = 1

    def run(self) -> None:
        while self.player.is_alive():
            self.enemy = self.generate_enemy(self.wave)
            print(f"\n{self.enemy.pilot_name} approaches! Prepare for battle!")
            time.sleep(2)
            self.battle_loop()
            if self.player.is_alive():
                self.wave += 1
                clear_screen()
                self.player.level_up()
                time.sleep(3)
                clear_screen()
        self.end_game()

    def battle_loop(self) -> None:
        while self.player.is_alive() and self.enemy.is_alive():
            clear_screen()
            MekaDisplay.render_status(self.player)
            MekaDisplay.render_status(self.enemy)
            player_action = self.player_choose()
            enemy_action = self.enemy_choose()
            print("\nResolving actions...")
            time.sleep(1)
            self.resolve(player_action, enemy_action)
            time.sleep(2)

    def player_choose(self) -> dict[str, str]:
        print("\nChoose your action:")
        print("1. Attack")
        print("2. Cool Down")
        print("3. Reload Ammo")
        print("4. Recharge Shields")
        choice = input(">> ")

        if choice == "1":
            ammo_type = self.pick_ammo()
            if ammo_type and self.player.has_ammo(ammo_type):
                return {"type": ActionType.ATTACK, "ammo": ammo_type}
            else:
                print("Invalid action - defaulting to cool down.")
                return {"type": ActionType.COOL_DOWN}

        elif choice == "2":
            return {"type": ActionType.COOL_DOWN}

        elif choice == "3":
            ammo_type = self.pick_ammo()
            return {"type": ActionType.RELOAD, "ammo": ammo_type or AmmoType.STANDARD}
        
        elif choice == "4":
            return {"type": ActionType.RECHARGE_SHIELD}

        else:
            print("Invalid action - defaulting to cool down.")
            return {"type": ActionType.COOL_DOWN}
        
    def enemy_choose(self) -> dict[str, str]:
        if self.enemy.check_overheat():
            return {"type": ActionType.COOL_DOWN}
        
        ammo_type = self.enemy_pick_ammo()
        if ammo_type:
            return {"type": ActionType.ATTACK, "ammo": ammo_type}
        else:
            ammo_reload = self.enemy_reload_ammo()
            return {"type": ActionType.RELOAD, "ammo": ammo_reload or AmmoType.STANDARD}
    
    def resolve(self, player_action: dict[str, str], enemy_action: dict[str, str]) -> None:
        player_damage =  self.calculate_damage(self.player, player_action)
        enemy_damage = self.calculate_damage(self.enemy, enemy_action)

        self.apply_action(self.player, self.enemy, player_action, player_damage)
        self.apply_action(self.enemy, self.player, enemy_action, enemy_damage)

    def calculate_damage(self, attacker: Meka, action: dict[str, ActionType | AmmoType]) -> int:
        if action["type"] != ActionType.ATTACK:
            return 0
        damage = attacker.attack + random.randint(-DAMAGE_VARIANCE, DAMAGE_VARIANCE)
        if action["ammo"] == AmmoType.STANDARD and random.random() < STANDARD_CRIT_CHANCE:
            damage *= CRIT_DAMAGE_MULTIPLIER
        return damage
    
    def apply_action(self, attacker: Meka, defender: Meka, action: dict[str, ActionType | AmmoType], damage: int) -> None:
        if action["type"] == ActionType.ATTACK:
            if attacker.check_overheat():
                print(f"{attacker.pilot_name} Meka OVERHEATED and couldn't fire!")
                return
            defender.take_damage(damage, action["ammo"])
            attacker.consume_ammo(action["ammo"])
            attacker.apply_heat()
            print(f"{attacker.pilot_name} fired {action['ammo'].value.replace('_', ' ')} ammo for {damage} damage!")

        elif action["type"] == ActionType.COOL_DOWN:
            attacker.cool_down()
            print(f"{attacker.pilot_name} Meka is cooling down!")

        elif action["type"] == ActionType.RELOAD:
            attacker.reload_ammo(action["ammo"])
            print(f"{attacker.pilot_name} Meka reloaded {action['ammo'].value.replace('_', ' ')} ammo!")

        elif action["type"] == ActionType.RECHARGE_SHIELD:
            attacker.recharge_shield()
            print(f"{attacker.pilot_name} Meka recharged its shields!")

    def end_game(self) -> None:
        clear_screen()
        print(f"Game Over! You Survived {self.wave} waves.")
        print("\nFinal Stats")
        MekaDisplay.render_status(self.player)
        self.save_score()
        self.show_leaderboard()
        input("\nPress Enter to exit...")

    def save_score(self) -> None:
        scores = self.load_scores()
        scores.append({
            "name": self.player.pilot_name,
            "waves": self.wave,
            "date": str(date.today())
        })
        scores.sort(key=lambda x: x["waves"], reverse=True)
        scores = scores[:MAX_LEADERBOARD_SCORES] # Keep only top 10 scores
        try:
            with open(LEADERBOARD_FILE, "w") as f:
                json.dump(scores, f, indent=2)
        except OSError as e:
            print(f"Warning: Error saving leaderboard: {e}")

    def load_scores(self) -> list[dict[str, str | int]]:
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            print("Warning: Leaderboard file is corrupted. Scores reset.")
            return []
        except OSError as e:
            print(f"Warning: Error loading leaderboard: {e}")
            return []
        
    def show_leaderboard(self) -> None:
        scores = self.load_scores()
        print("\n========================")
        print("      LEADERBOARD")
        print("========================")
        if not scores:
            print("No scores yet. Be the first to set a record!")
            return
        for i, entry in enumerate(scores, 1):
            arrow = "->" if entry["name"] == self.player.pilot_name and entry["waves"] == self.wave else "  "
            print(f"{arrow} {i}. {entry['name']:<20} {entry['waves']} waves       {entry['date']}")

    def enemy_pick_ammo(self) -> AmmoType | None:
        player = self.player
        enemy = self.enemy

        if player.shield >= ENEMY_SHIELD_THREAT_THRESHOLD and enemy.has_ammo(AmmoType.SHIELD_BREAKER): # Prioritize shield breaker if player's shield is strong
            return AmmoType.SHIELD_BREAKER
        
        if player.armor >= ENEMY_SHIELD_THREAT_THRESHOLD and enemy.has_ammo(AmmoType.ARMOR_PIERCING): # Prioritize armor piercing if player's armor is strong
            return AmmoType.ARMOR_PIERCING
        
        if enemy.has_ammo(AmmoType.STANDARD):
            return AmmoType.STANDARD
        
        available = enemy.available_ammo_types()
        return random.choice(available) if available else None
    
    def enemy_reload_ammo(self) -> AmmoType | None:
        player = self.player
        enemy = self.enemy

        if player.shield > ENEMY_RELOAD_THREAT_THRESHOLD and enemy.ammo.get(AmmoType.SHIELD_BREAKER, 0) == 0:
            return AmmoType.SHIELD_BREAKER
        
        if player.armor > ENEMY_RELOAD_THREAT_THRESHOLD and enemy.ammo.get(AmmoType.ARMOR_PIERCING, 0) == 0:
            return AmmoType.ARMOR_PIERCING
        return None
    
    def generate_enemy(self, wave: int) -> Meka:
        names = ["Cadet", "Ranger", "Officer", "Marshal"]
        name = names[min(wave - 1, len(names) - 1)] # caps name at "Marshal" for higher waves

        power = min(ENEMY_BASE_POWER + (wave * ENEMY_POWER_PER_WAVE), ENEMY_MAX_POWER)
        armor = min(ENEMY_BASE_ARMOR + (wave * ENEMY_ARMOR_PER_WAVE), ENEMY_MAX_ARMOR)
        shield = min(ENEMY_BASE_SHIELD + (wave * ENEMY_SHIELD_PER_WAVE), ENEMY_MAX_SHIELD)
        attack = min(ENEMY_BASE_ATTACK + (wave * ENEMY_ATTACK_PER_WAVE), ENEMY_MAX_ATTACK)

        ammo = {
            AmmoType.STANDARD: min(ENEMY_BASE_STANDARD_AMMO + wave, MAX_STANDARD_AMMO),
            AmmoType.ARMOR_PIERCING: min(ENEMY_BASE_SPECIAL_AMMO + wave, MAX_SPECIAL_AMMO),
            AmmoType.SHIELD_BREAKER: min(ENEMY_BASE_SPECIAL_AMMO + wave, MAX_SPECIAL_AMMO),
        }

        return Meka(f"{name}", power, 0, armor, shield, ammo, attack)

    def pick_ammo(self) -> str | None:
        print("\nChoose ammo type:")
        print("1. Standard - Can Critically Hit")
        print("2. Armor Piercing - Double Damage to Armor")
        print("3. Shield Breaker - Double Damage to Shields")
        ammo_choice = input(">> ")
        return AMMO_TYPES.get(ammo_choice)

def main() -> None:
    print("========================")
    print("      メカ戦闘")
    print("========================")

    pilot_name = input("Enter your name, Pilot: ").strip()
    if not pilot_name:
        pilot_name = "Unknown Pilot"

    input("\nPress Enter to battle...")
    
    player = Meka(
        name=pilot_name,
        power=PLAYER_START_POWER,
        heat=PLAYER_START_HEAT,
        armor=PLAYER_START_ARMOR,
        shield=PLAYER_START_SHIELD,
        ammo={
            AmmoType.STANDARD: PLAYER_START_STANDARD_AMMO,
            AmmoType.ARMOR_PIERCING: PLAYER_START_ARMOR_PIERCING_AMMO,
            AmmoType.SHIELD_BREAKER: PLAYER_START_SHIELD_BREAKER_AMMO,
        },
        attack=PLAYER_START_ATTACK,
    )

    game = Game(player)
    game.run()

if __name__ == "__main__":
    main()