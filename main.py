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
            self.ammo[ammo_type] = min(self.ammo.get(ammo_type, 0) + 2, 10)
    
    def is_alive(self):
        return self.power > 0
    

    def take_damage(self, damage, ammo_type="standard"):
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
        return self.heat + random.randint(10, 15) > 100
    
    def apply_heat(self):
        self.heat += random.randint(10, 15)
        if self.heat > 100:
            self.heat = 100
    
    def cool_down(self):
        self.heat = max(0, self.heat - 50) # Cool down reduces heat by 50

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
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy

    def run(self):
        while self.player.is_alive() and self.enemy.is_alive():
            clear_screen()
            self.player.display_status()
            self.enemy.display_status()
            self.player_turn()
            time.sleep(2)
            if self.enemy.is_alive():
                self.enemy_turn()
                time.sleep(2)
        self.end_game()

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
            if self.player.has_ammo(ammo_type) and not self.player.check_overheat():
                self.player.apply_heat()
                damage = self.player.attack + random.randint(-2, 5)
                if ammo_type == "standard" and random.random() < STANDARD_CRIT_CHANCE:
                    damage *= 3
                    print("Hit a vulnerable point!")
                self.enemy.take_damage(damage, ammo_type)
                self.player.consume_ammo(ammo_type)
                print(f"You fired {ammo_type.replace('_', ' ')} ammo for {damage} damage!")
            else:
                self.player.apply_heat()
                print("You cannot attack! Choose a valid ammo type, and make sure you have rounds and are not overheated.")

        elif choice == "2":
            self.player.cool_down()
            print("You cooled down your Meka!")

        elif choice == "3":
            ammo_type = self.pick_ammo()
            if ammo_type:
                self.player.recharge_ammo(ammo_type)
                print(f"You reloaded {ammo_type.replace('_', ' ')} ammo!")
            else:
                print("Invalid ammo type.")

        elif choice == "4":
            self.player.recharge_shield()
            print("You redirected power to recharge your shields")

    def enemy_turn(self):
        available_ammo = self.enemy.available_ammo_types()
        if available_ammo and not self.enemy.check_overheat():
            self.enemy.apply_heat()
            ammo_type = random.choice(available_ammo)
            damage = self.enemy.attack + random.randint(-2, 5)
            if ammo_type == "standard" and random.random() < STANDARD_CRIT_CHANCE:
                damage *= 3
                print("The enemy hit a vulnerable point!")
            self.player.take_damage(damage, ammo_type)
            self.enemy.consume_ammo(ammo_type)
            print(f"The enemy fired {ammo_type.replace('_', ' ')} ammo for {damage} damage!")
        else:
            self.enemy.apply_heat()
            print("The enemy cannot attack! Either they are out of ammo or they have overheated.")
            self.enemy.cool_down()
            self.enemy.recharge_ammo("standard")

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
        "standard": 5,
        "armor_piercing": 2,
        "shield_breaker": 3,
    }, 5)
    enemy = Meka("Enemy Meka", 100, 0, 50, 50, {
        "standard": 5,
        "armor_piercing": 2,
        "shield_breaker": 3,
    }, 5)

    game = Game(player, enemy)
    game.run()

if __name__ == "__main__":
    main()