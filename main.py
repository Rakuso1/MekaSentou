from __future__ import annotations
from enum import Enum
import random
import time
import os
import math
import json
from datetime import date 

STANDARD_CRIT_CHANCE = 0.25 # 25% chance for standard ammo to critically hit


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
        bar_length = 10
        filled = int((value / max_value) * bar_length) if max_value else 0
        filled = max(0, min(bar_length, filled))
        empty = bar_length - filled
        return "█" * filled + "-" * empty
    
    @staticmethod
    def render_status(meka: "Meka") -> None:
        print(f"\n{meka.pilot_name}")
        print(f"Power:  [{MekaDisplay.make_bar(meka.power, meka.max_power)}] {meka.power}/{meka.max_power}")
        print(f"Heat:   [{MekaDisplay.make_bar(meka.heat, 100)}] {meka.heat}/100")
        print(f"Armor:  [{MekaDisplay.make_bar(meka.armor, meka.max_armor)}] {meka.armor}/{meka.max_armor}")
        print(f"Shield: [{MekaDisplay.make_bar(meka.shield, meka.max_shield)}] {meka.shield}/{meka.max_shield}")
        print(f"Ammo:   {meka.ammo_total()}")
        print(f"  Standard:        [{MekaDisplay.make_bar(meka.ammo.get(AmmoType.STANDARD, 0), 10)}] {meka.ammo.get(AmmoType.STANDARD, 0)}/10")
        print(f"  Armor Piercing:   [{MekaDisplay.make_bar(meka.ammo.get(AmmoType.ARMOR_PIERCING, 0), 10)}] {meka.ammo.get(AmmoType.ARMOR_PIERCING, 0)}/10")
        print(f"  Shield Breaker:   [{MekaDisplay.make_bar(meka.ammo.get(AmmoType.SHIELD_BREAKER, 0), 10)}] {meka.ammo.get(AmmoType.SHIELD_BREAKER, 0)}/10")


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
        print("1. Increase Max Power (+20)")
        print("2. Increase Armor (+10)")
        print("3. Increase Shield (+10)")
        print("4. Increase Attack (+5)")
        choice = input(">> ")

        if choice == "1":
            self.max_power += 20
            self.power += 20 # Also heal current power by 20 when max power increases
            print("Max Power increased by 20!")

        elif choice == "2":
            self.max_armor += 10
            self.armor += 10 # Also heal current armor by 10 when max armor increases
            print("Armor increased by 10!")

        elif choice == "3":
            self.max_shield += 10
            self.shield += 10 # Also heal current shield by 10 when max shield increases
            print("Shield increased by 10!")

        elif choice == "4":
            self.attack += 5
            print("Attack increased by 5!")

        else:
            self.attack += 5
            print("Attack increased by 5 by default!")

        heal = math.ceil(self.max_power * 0.5) # Heal 50% of max power after each victory
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
            self.ammo[ammo_type] = min(self.ammo.get(ammo_type, 0) + 10, 10)
        else:
            self.ammo[ammo_type] = min(self.ammo.get(ammo_type, 0) + 5, 10)
    
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
        return self.heat >= 100
    
    def apply_heat(self) -> None:
        self.heat += random.randint(10, 15)
        if self.heat > 100:
            self.heat = 100
    
    def cool_down(self) -> None:
        self.heat = 0 

    def recharge_shield(self) -> None:
        cost = math.ceil(self.power * 0.2) # Cost is 20% of current power, rounded up
        missing_shield = self.max_shield - self.shield
        gain = math.ceil(missing_shield * 0.8) # Gain is 80% of missing shield, rounded up
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
        damage = attacker.attack + random.randint(-2, 2)
        if action["ammo"] == AmmoType.STANDARD and random.random() < STANDARD_CRIT_CHANCE:
            damage *= 4
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
        scores = scores[:10] # Keep only top 10 scores
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

        if player.shield >= 1 and enemy.has_ammo(AmmoType.SHIELD_BREAKER): # Prioritize shield breaker if player's shield is strong
            return AmmoType.SHIELD_BREAKER
        
        if player.armor >= 1 and enemy.has_ammo(AmmoType.ARMOR_PIERCING): # Prioritize armor piercing if player's armor is strong
            return AmmoType.ARMOR_PIERCING
        
        if enemy.has_ammo(AmmoType.STANDARD):
            return AmmoType.STANDARD
        
        available = enemy.available_ammo_types()
        return random.choice(available) if available else None
    
    def enemy_reload_ammo(self) -> AmmoType | None:
        player = self.player
        enemy = self.enemy

        if player.shield > 10 and enemy.ammo.get(AmmoType.SHIELD_BREAKER, 0) == 0:
            return AmmoType.SHIELD_BREAKER
        
        if player.armor > 10 and enemy.ammo.get(AmmoType.ARMOR_PIERCING, 0) == 0:
            return AmmoType.ARMOR_PIERCING
        return None
    
    def generate_enemy(self, wave: int) -> Meka:
        names = ["Cadet", "Ranger", "Officer", "Marshal"]
        name = names[min(wave - 1, len(names) - 1)] # caps name at "Marshal" for higher waves

        power = 80 + (wave * 10) # Base 80, +10 per wave
        armor = 20 + (wave * 5) # Base 20, +5 per wave
        shield = 10 + (wave * 5) # Base 10, +5 per wave
        attack = 4 + (wave * 1 ) # Base 4, +1 per wave

        power = min(power, 300) # Cap power at 300
        armor = min(armor, 150) # Cap armor at 150
        shield = min(shield, 150) # Cap shield at 150
        attack = min(attack, 20) # Cap attack at 20

        ammo = {
            AmmoType.STANDARD: min(5 + wave, 15), # Base 5, +1 per wave, cap at 15
            AmmoType.ARMOR_PIERCING: min(2 + wave, 10), # Base 2, +1 per wave, cap at 10
            AmmoType.SHIELD_BREAKER: min(3 + wave, 10), # Base 3, +1 per wave, cap at 10
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
    
    player = Meka(pilot_name, 100, 0, 50, 50, {
        AmmoType.STANDARD: 10,
        AmmoType.ARMOR_PIERCING: 10,
        AmmoType.SHIELD_BREAKER: 10,
    }, 10)

    game = Game(player)
    game.run()

if __name__ == "__main__":
    main()