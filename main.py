import random
import time
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class Meka:
    def __init__(self, name, power, heat, armor, shield, ammo, attack):
        self.name = name
        self.power = power
        self.heat = heat
        self.armor = armor
        self.shield = shield
        self.ammo = ammo
        self.attack = attack
    
    def is_alive(self):
        return self.power > 0
    
    def take_damage(self, damage):
        remaining = damage

        if self.shield > 0 and remaining > 0:
            absorbed = min(self.shield, remaining)
            self.shield -= absorbed
            remaining -= absorbed

        if self.armor > 0 and remaining > 0:
            absorbed = min(self.armor, remaining)
            self.armor -= absorbed
            remaining -= absorbed

        if remaining > 0:
            self.power -= remaining
            if self.power < 0:
                self.power = 0

    def overheat(self):
        self.heat += 10
        if self.heat >= 100:
            self.heat = 100
            print(f"{self.name} has overheated and cannot attack!")
            return True
        return False
    
    def cool_down(self):
        self.heat -= 60
        if self.heat < 0:
            self.heat = 0

    def recharge_ammo(self):
        self.ammo += 10
        if self.ammo > 10:
            self.ammo = 10

    def make_bar(self, value, max_value):
        bar_length = 10
        filled = int((value / max_value) * bar_length) if max_value else 0
        filled = max(0, min(bar_length, filled))
        empty = bar_length - filled
        return "█" * filled + "-" * empty

    def display_status(self):
        print(f"\n{self.name}")
        print(f"Power:  [{self.make_bar(self.power, 100)}] {self.power}/100")
        print(f"Heat:   [{self.make_bar(self.heat, 100)}] {self.heat}/100")
        print(f"Armor:  [{self.make_bar(self.armor, 50)}] {self.armor}/50")
        print(f"Shield: [{self.make_bar(self.shield, 50)}] {self.shield}/50")
        print(f"Ammo:   [{self.make_bar(self.ammo, 10)}] {self.ammo}/10")

player = Meka("Player Meka", 100, 0, 50, 50, 10, 5)
enemy = Meka("Enemy Meka", 100, 0, 50, 50, 10, 5)

while player.is_alive() and enemy.is_alive():

    print("========================")
    print("      メカ戦闘")
    print("========================")

    input("\nPress Enter to battle...")

    clear_screen()

    player.display_status()
    enemy.display_status()

    print("\nChoose your action:")
    print("1. Attack")
    print("2. Cool Down")
    print("3. Recharge Ammo")
    choice = input(">> ")

    if choice == "1":
        if player.ammo > 0 and not player.overheat():
            damage = player.attack + random.randint(-5, 5)
            enemy.take_damage(damage)
            player.ammo -= 1
            print(f"You attacked the enemy for {damage} damage!")
        else:
            print("You cannot attack! Either you are out of ammo or you have overheated.")

    elif choice == "2":
        player.cool_down()
        print("You cooled down your Meka!")

    elif choice == "3":
        player.recharge_ammo()
        print("You recharged your ammo!")

    time.sleep(2)

    if enemy.is_alive():
        if enemy.ammo > 0 and not enemy.overheat():
            damage = enemy.attack + random.randint(-5, 4)
            player.take_damage(damage)
            enemy.ammo -= 1
            print(f"The enemy attacked you for {damage} damage!")
        else:
            print("The enemy cannot attack! Either they are out of ammo or they have overheated.")
            enemy.cool_down()
            enemy.recharge_ammo()

    time.sleep(2)

clear_screen()
if player.is_alive():
    print("Congratulations! You have defeated the enemy Meka!")
else:
    print("Game Over! The enemy Meka has defeated you!")