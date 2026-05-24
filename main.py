import random
import time
import os
import math

STANDARD_CRIT_CHANCE = 0.10 # 10% chance for standard ammo to critically hit

AMMO_TYPES = {
    "1": "standard",
    "2": "armor_piercing",
    "3": "shield_breaker",
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class Meka:
    def __init__(self, name, power, heat, armor, shield, ammo, attack):
        self.name = name
        self.power = power
        self.max_power = power
        self.heat = heat
        self.max_heat = 100
        self.armor = armor
        self.max_armor = armor
        self.shield = shield
        self.max_shield = shield
        self.ammo = ammo
        self.attack = attack

    def ammo_total(self):
        return sum(self.ammo.values())

    def has_ammo(self, ammo_type):
        return self.ammo.get(ammo_type, 0) > 0

    def consume_ammo(self, ammo_type):
        if self.has_ammo(ammo_type):
            self.ammo[ammo_type] -= 1

    def recharge_ammo(self, ammo_type):
        if ammo_type == "standard":
            self.ammo[ammo_type] = min(self.ammo.get(ammo_type, 0) + 10, 10)
        else:
            self.ammo[ammo_type] = min(self.ammo.get(ammo_type, 0) + 5, 10)
    
    def is_alive(self):
        return self.power > 0
    
    def take_damage(self, damage, ammo_type):
        shield_multiplier = 2 if ammo_type == "shield_breaker" else 1
        armor_multiplier = 2 if ammo_type == "armor_piercing" else 1

        # Apply to shield layer first. If the shield is reduced to 0, leftover damage is lost.
        if damage > 0 and self.shield > 0:
            damage = self._absorb(damage, "shield", shield_multiplier)

        # Apply to armor layer. If the armor is reduced to 0, leftover damage is lost.
        if damage > 0 and self.armor > 0:
            damage = self._absorb(damage, "armor", armor_multiplier)

        if damage > 0:
            self.power = max(0, self.power - damage)

    def _absorb(self, damage, layer, multiplier):
        current = getattr(self, layer)
        effective_damage = min(current, damage * multiplier)
        setattr(self, layer, current - effective_damage)

        if getattr(self, layer) == 0:
            return 0
        else:
            return max(0, damage - math.ceil(effective_damage / multiplier))

    def check_overheat(self):
        return self.heat >= 100
    
    def apply_heat(self):
        self.heat += random.randint(10, 15)
        if self.heat > 100:
            self.heat = 100
    
    def cool_down(self):
        self.heat = 0 

    def recharge_shield(self):
        cost = math.ceil(self.power * 0.2) # Cost is 20% of current power, rounded up
        missing_shield = self.max_shield - self.shield
        gain = math.ceil(missing_shield * 0.5) # Gain is 50% of missing shield, rounded up
        self.power = max(0, self.power - cost) 
        self.shield = min(self.shield + gain, self.max_shield) 

    def make_bar(self, value, max_value):
        bar_length = 10
        filled = int((value / max_value) * bar_length) if max_value else 0
        filled = max(0, min(bar_length, filled))
        empty = bar_length - filled
        return "█" * filled + "-" * empty

    def display_status(self):
        print(f"\n{self.name}")
        print(f"Power:  [{self.make_bar(self.power, self.max_power)}] {self.power}/{self.max_power}")
        print(f"Heat:   [{self.make_bar(self.heat, self.max_heat)}] {self.heat}/{self.max_heat}")
        print(f"Armor:  [{self.make_bar(self.armor, self.max_armor)}] {self.armor}/{self.max_armor}")
        print(f"Shield: [{self.make_bar(self.shield, self.max_shield)}] {self.shield}/{self.max_shield}")
        print(f"Ammo:   {self.ammo_total()}")
        print(f"  Standard:        [{self.make_bar(self.ammo.get('standard', 0), 10)}] {self.ammo.get('standard', 0)}/10")
        print(f"  Armor Piercing:   [{self.make_bar(self.ammo.get('armor_piercing', 0), 10)}] {self.ammo.get('armor_piercing', 0)}/10")
        print(f"  Shield Breaker:   [{self.make_bar(self.ammo.get('shield_breaker', 0), 10)}] {self.ammo.get('shield_breaker', 0)}/10")

    def available_ammo_types(self):
        return [ammo_type for ammo_type, count in self.ammo.items() if count > 0]

class Game:
    def __init__(self, player):
        self.player = player
        self.enemy = None

    def run(self):
        wave = 1
        while self.player.is_alive():
            self.enemy = self.generate_enemy(wave)
            print(f"\n{self.enemy.name} approaches! Prepare for battle!")
            time.sleep(2)
            self.battle_loop()
            if self.player.is_alive():
                print(f"You have defeated {self.enemy.name}!")
                wave += 1
                time.sleep(2)
                clear_screen()
        self.end_game()

    def battle_loop(self):
        while self.player.is_alive() and self.enemy.is_alive():
            clear_screen()
            self.player.display_status()
            self.enemy.display_status()
            self.player_turn()
            time.sleep(2)
            if self.enemy.is_alive():
                self.enemy_turn()
            time.sleep(2)

    def end_game(self):
        clear_screen()
        if self.player.is_alive():
            print("Congratulations! You have defeated the enemy Meka!")
        else:
            print("Game Over! The enemy Meka has defeated you!")
        input("\nPress Enter to exit...")

    def player_turn(self):
        print("\nChoose your action:")
        print("1. Attack")
        print("2. Cool Down")
        print("3. Recharge Ammo")
        print("4. Recharge Shields")
        choice = input(">> ")

        if choice == "1":
            ammo_type = self.pick_ammo()
            if ammo_type and self.player.has_ammo(ammo_type):
                if not self.player.check_overheat():
                    self.do_attack(self.player, self.enemy, ammo_type)
                    self.player.apply_heat()
                else:
                    print("MEKA OVERHEATED!")
            else:
                print("OUT OF AMMO.")

        elif choice == "2":
            self.player.cool_down()
            print("MEKA COOLED DOWN!")

        elif choice == "3":
            ammo_type = self.pick_ammo()
            if ammo_type:
                self.player.recharge_ammo(ammo_type)
                print(f"You reloaded {ammo_type.replace('_', ' ')} ammo!")
            else:
                print("Invalid ammo type.")

        elif choice == "4":
            self.player.recharge_shield()
            print("POWER REDISTRIBUTED TO SHIELDS!")

        else:
            print("Invalid action. Turn skipped.")

    def enemy_turn(self):
        if self.enemy.check_overheat():
            self.enemy.cool_down()
            self.enemy_recharge_ammo()
            print("Enemy MEKA is cooling down and reloading!")
            return
        ammo_type = self.enemy_pick_ammo()

        if ammo_type:
            self.do_attack(self.enemy, self.player, ammo_type)
            self.enemy.apply_heat()
        else:
            self.enemy_recharge_ammo()

    def enemy_pick_ammo(self):
        player = self.player
        enemy = self.enemy

        if player.shield > 10 and enemy.has_ammo("shield_breaker"): # Prioritize shield breaker if player's shield is strong
            return "shield_breaker"
        
        if player.armor > 10 and enemy.has_ammo("armor_piercing"): # Prioritize armor piercing if player's armor is strong
            return "armor_piercing"
        
        if enemy.has_ammo("standard"):
            return "standard"
        
        available = enemy.available_ammo_types()
        if available:
            return random.choice(available)
        
        return None
    
    def enemy_recharge_ammo(self):
        player = self.player
        enemy = self.enemy

        if player.shield > 10 and enemy.ammo.get("shield_breaker", 0) == 0:
            enemy.recharge_ammo("shield_breaker")
            print ("Enemy MEKA reloaded shield breaker ammo!")
            return
        
        if player.armor > 10 and enemy.ammo.get("armor_piercing", 0) == 0:
            enemy.recharge_ammo("armor_piercing")
            print ("Enemy MEKA reloaded armor piercing ammo!")
            return
        
        enemy.recharge_ammo("standard")
        print ("Enemy MEKA reloaded standard ammo!")

    def generate_enemy(self, wave):
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
            "standard": min(5 + wave, 15), # Base 5, +1 per wave, cap at 15
            "armor_piercing": min(2 + wave, 10), # Base 2, +1 per wave, cap at 10
            "shield_breaker": min(3 + wave, 10), # Base 3, +1 per wave, cap at 10
        }

        return Meka(f"{name}", power, 0, armor, shield, ammo, attack)

    def do_attack(self, attacker, defender, ammo_type):
        damage = attacker.attack + random.randint(-2, 5)
        if ammo_type == "standard" and random.random() < STANDARD_CRIT_CHANCE:
            damage *= 3
            if attacker is self.player:
                print("You hit a vulnerable point!")
            else:
                print("The enemy hit a vulnerable point!")
        defender.take_damage(damage, ammo_type)
        attacker.consume_ammo(ammo_type)
        if attacker is self.player:
            print(f"You fired {ammo_type.replace('_', ' ')} ammo for {damage} damage!")
        else:
            print(f"The enemy fired {ammo_type.replace('_', ' ')} ammo for {damage} damage!")

    def pick_ammo(self):
        print("\nChoose ammo type:")
        print("1. Standard - Can Critically Hit")
        print("2. Armor Piercing - Double Damage to Armor")
        print("3. Shield Breaker - Double Damage to Shields")
        ammo_choice = input(">> ")
        return AMMO_TYPES.get(ammo_choice)

def main():
    print("========================")
    print("      メカ戦闘")
    print("========================")
    input("\nPress Enter to battle...")
    
    player = Meka("Player Meka", 100, 0, 50, 50, {
        "standard": 10,
        "armor_piercing": 10,
        "shield_breaker": 10,
    }, 5)

    game = Game(player)
    game.run()

if __name__ == "__main__":
    main()