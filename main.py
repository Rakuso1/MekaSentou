"""
MekaSentou - A turn-based mech combat game.

Survive waves of enemy Mekas by managing
ammo, heat, armor and shields. Each victory grants a stat upgrade.
"""
from __future__ import annotations
from enum import Enum
import random
import time
import os
import math
import json
from datetime import date
from dataclasses import dataclass, field
from collections import deque
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich import box
from typing import NamedTuple, Literal

console = Console()

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
LOW_AMMO_THRESHOLD: int = 2

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
MAX_LOG_LINES: int = 2
LOG_BRIGHT_ENTRIES: int = 2 #How many recent entries render at full brightness

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

AMMO_DESCRIPTIONS: dict[AmmoType, str] = {
    AmmoType.STANDARD:       "Standard       - Can Critically Hit",
    AmmoType.ARMOR_PIERCING: "Armor Piercing - Double Damage to Armor",
    AmmoType.SHIELD_BREAKER: "Shield Breaker - Double Damage to Shields",
}

AMMO_MAX: dict[AmmoType, int] = {
    AmmoType.STANDARD: MAX_STANDARD_AMMO,
    AmmoType.ARMOR_PIERCING: MAX_SPECIAL_AMMO,
    AmmoType.SHIELD_BREAKER: MAX_SPECIAL_AMMO
}

class ActionType(Enum):
    ATTACK = "attack"
    COOL_DOWN = "cool_down"
    RELOAD = "reload"
    RECHARGE_SHIELD = "recharge_shield"

class DamageResult(NamedTuple):
    """The outcome of a single damage calculation."""
    damage: int
    is_crit: bool

def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')

class Display:
    """Handles all terminal rendering for the game,
    
    All methods are static, this class oens no state.
    It receives data as parameters and renders it.
    """
    @staticmethod
    def make_bar(value: int, max_value: int, invert_color: bool = False) -> Text:
        """Build a fixed-width ASCII progress bar.
        
        Args:
            value: The current value to represent.
            max_value: The maximum posibble value (full bar).
            invert_color: True on heat bar.
            
        Returns:
            A rich Text class. 
        """
        filled = int((value / max_value) * STATUS_BAR_LENGTH) if max_value else 0
        filled = max(0, min(STATUS_BAR_LENGTH, filled))
        empty = STATUS_BAR_LENGTH - filled

        ratio = (value / max_value) if max_value else 0.0
        if invert_color:
            ratio = 1.0 - ratio

        color = "green" if ratio > 0.5 else "yellow" if ratio > 0.25 else "red"

        bar = Text()
        bar.append("◼" * filled, style=color)
        bar.append("-" * empty, style="dim")
        return bar
    
    @staticmethod
    def render_status(meka: "Meka") -> None:
        """Print a status dashboard with heat warnings."""
        console.print(f"\n[bold magenta]{meka.pilot_name}[/bold magenta]\n")
        
        table = Table(show_header=False, show_edge=False, box=box.SIMPLE)
        
        # Define our columns (System Name, Bar, Text Stats)
        table.add_column("System", justify="right", style="bold cyan")
        table.add_column("Bar", justify="left")
        table.add_column("Numbers", justify="left", style="dim")

        # Add rows for the core stats
        table.add_row("Power:", Display.make_bar(meka.power, meka.max_power), f"{meka.power}/{meka.max_power}")

        # Heat row - uses invert_color and conditional warning label
        heat_numbers = Text(f"{meka.heat}/{MAX_HEAT}")
        if meka.heat >= MAX_HEAT:
            heat_numbers.append("  OVERHEATED", style="bold red")
        elif meka.heat >= MAX_HEAT * 0.8:
            heat_numbers.append("  CRITICAL", style="bold red")
        elif meka.heat >= MAX_HEAT * 0.5:
            heat_numbers.append("  WARNING", style="yellow")
        table.add_row("Heat:", Display.make_bar(meka.heat, MAX_HEAT, invert_color=True), heat_numbers)

        table.add_row("Armor:", Display.make_bar(meka.armor, meka.max_armor), f"{meka.armor}/{meka.max_armor}")

        shield_numbers = Text(f"{meka.shield}/{meka.max_shield}")
        if meka.shield == 0:
            shield_numbers.append(" SHIELDS OFFLINE", style="bold red")
        table.add_row("Shield:", Display.make_bar(meka.shield, meka.max_shield), shield_numbers)
        
        # Add a blank row or separator for ammo
        table.add_row("", "", "") 
        table.add_row(f"Ammo ({meka.ammo_total()})", "", "")
        
        # Add rows for Ammo Subtypes
        std_ammo = meka.ammo.get(AmmoType.STANDARD, 0)
        ap_ammo = meka.ammo.get(AmmoType.ARMOR_PIERCING, 0)
        sb_ammo = meka.ammo.get(AmmoType.SHIELD_BREAKER, 0)

        table.add_row("Standard:", Display.make_bar(std_ammo, MAX_STANDARD_AMMO), f"{std_ammo}/{MAX_STANDARD_AMMO}")
        table.add_row("Armor Piercing:", Display.make_bar(ap_ammo, MAX_SPECIAL_AMMO), f"{ap_ammo}/{MAX_SPECIAL_AMMO}")
        table.add_row("Shield Breaker:", Display.make_bar(sb_ammo, MAX_SPECIAL_AMMO), f"{sb_ammo}/{MAX_SPECIAL_AMMO}")

        # Print the finished table to the console
        console.print(table)

    @staticmethod
    def render_combat_log(log: deque[Text]) -> None:
        """Render the combat log inside a Panel, with older entries dimmed
        
        Accepts the log as a parameter
        
        Args:
            log: The deque of Text entries owned by Game
        """
        if not log:
            #Show an empty placeholder so the layout doesn't shift on turn 1
            content = Text("Awaiting combat", style="dim")
        else:
            content = Text()
            log_list = list(log) #Convert deque to list for index access
            bright_threshold = len(log_list) - LOG_BRIGHT_ENTRIES

            for i, entry in enumerate(log_list):
                if i > 0:
                    content.append("\n") #separate entries with newlines
                is_recent = i >= bright_threshold
                if is_recent:
                    content.append_text(entry) #Newest entry: full brightness
                else:
                    #older entries: copy first, then dim the copy
                    dimmed = entry.copy()
                    dimmed.stylize("dim")
                    content.append_text(dimmed)

        console.print(Panel(
            content,
            title="[bold]Combat Log[/bold]",
            border_style="dim blue",
            padding=(0, 1),
            expand=False,
        ))

    @staticmethod
    def show_leaderboard(scores: list[dict[str, str | int]], current_name: str, current_waves: int,) -> None:
        """Render the leaderboard as a styled Table inside a Panel.
        
        Args:
            scores: Sorted score list from the leaderboard file.
            current_name: Current player's pilot name
            current_waves: Waves survives this run
        """
        medals: dict[int, str] = {1: "1st", 2: "2nd", 3: "3rd"}

        if not scores:
            console.print(Panel(
                "[dim] No scores yet. Be the first![/dim]",
                title="LEADERBOARD",
            ))
            return
        
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.SIMPLE_HEAD,
            padding=(0, 1),
        )

        table.add_column("#", justify="center", width=4)
        table.add_column("Pilot", justify="left", min_width=20)
        table.add_column("Waves", justify="right", width=6)
        table.add_column("Date", justify="right", width=12)

        for i, entry in enumerate(scores, 1):
            is_current = (
                entry["name"] == current_name
                and entry["waves"] == current_waves
            )
            rank = medals.get(i, str(i))
            name_cell = str(entry["name"])
            waves_cell = str(entry["waves"])
            date_cell = str(entry["date"])

            if is_current:
                name_cell = f"[bold yellow]{name_cell}[/bold yellow]"
                waves_cell = f"[bold yellow]{waves_cell}[/bold yellow]"
                date_cell = f"[bold yellow]{date_cell}[/bold yellow]"
                rank = f"[bold yellow]{rank}[/bold yellow]"

            table.add_row(rank, name_cell, waves_cell, date_cell)

        console.print(Panel(
            table,
            title="LEADERBOARD",
            padding=(0, 1),
            expand=False,
        ))

@dataclass
class Meka:
    """A combat Meka unit with layered defences: shield -> armor -> power.
    
    Damage passes through each layer in order. If layer is depleted, leftover
    damage is lost.
    
    Atributes:
        pilot_name: Display name shown in combat.
        power: Current HP.
        heat: Accumulates when firing. At MAX_HEAT the Meka cannot fire.
        armor: First physical layer. Doubles damage taken from armor_piercing.
        shield: Outer layer. Doubles damage taken from shield_breaker.
        ammo: Remaining rounds per ammo type.
        attack: Base damage output before variance.
    """
    pilot_name: str
    power: int
    heat: int
    armor: int
    shield: int
    ammo: dict[AmmoType, int]
    attack: int
    max_power: int = field(default=0, init=False)
    max_armor: int = field(default=0, init=False)
    max_shield: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        """Initialise derived max-stat fields from their starting values."""
        self.max_power = self.power
        self.max_armor = self.armor
        self.max_shield = self.shield


    def apply_upgrade(self, choice: str) -> str:
        """Applies a stat upgrade from a menu choice.
        
        Args:
            choice: The player's input string ("1"-"4").
            
        Returns:
            A human-readable message describing what changed.
        """
        if choice == "1":
            self.max_power += LEVEL_UP_POWER_BONUS
            self.power += LEVEL_UP_POWER_BONUS
            return f"Max Power increased by {LEVEL_UP_POWER_BONUS}!"
        
        elif choice == "2":
            self.max_armor += LEVEL_UP_ARMOR_BONUS
            self.armor += LEVEL_UP_ARMOR_BONUS
            return f"Armor increased by {LEVEL_UP_ARMOR_BONUS}!"
        
        elif choice == "3":
            self.max_shield += LEVEL_UP_SHIELD_BONUS
            self.shield += LEVEL_UP_SHIELD_BONUS
            return f"Shield increased by {LEVEL_UP_SHIELD_BONUS}!"
        
        else:
            self.attack += LEVEL_UP_ATTACK_BONUS
            return f"Attack increased by {LEVEL_UP_ATTACK_BONUS}!"
        
    def apply_post_battle_heal(self) -> int:
        """Restore POST_BATTLE_HEAL_RATE of max power after a victory.
        
        Returns:
            The number of power points restored.
        """
        heal = math.ceil(self.max_power * POST_BATTLE_HEAL_RATE)
        self.power = min(self.max_power, self.power + heal)
        return heal

    def ammo_total(self) -> int:
        """Return the total number of rounds across all ammo types."""
        return sum(self.ammo.values())

    def has_ammo(self, ammo_type: AmmoType) -> bool:
        """Return True if at least one round of ammo_type remains."""
        return self.ammo.get(ammo_type, 0) > 0

    def consume_ammo(self, ammo_type: AmmoType) -> None:
        """Spend one round of ammo_type if any remain."""
        if self.has_ammo(ammo_type):
            self.ammo[ammo_type] -= 1

    def reload_ammo(self, ammo_type: AmmoType) -> None:
        """Refill ammo_type"""
        if ammo_type == AmmoType.STANDARD:
            self.ammo[ammo_type] = min(self.ammo.get(ammo_type, 0) + STANDARD_AMMO_RELOAD_AMOUNT, MAX_STANDARD_AMMO)
        else:
            self.ammo[ammo_type] = min(self.ammo.get(ammo_type, 0) + SPECIAL_AMMO_RELOAD_AMOUNT, MAX_SPECIAL_AMMO)
    
    def is_alive(self) -> bool:
        """Return True if the Meka still has power remaining."""
        return self.power > 0
    
    def take_damage(self, damage: int, ammo_type: AmmoType) -> None:
        """Apply incoming damage through the shield -> armor -> power layers.
        
        Args:
            damage: Raw incoming damage before layer absorption.
            ammo_type: Determines which layer receives double damage.
        """
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
        """Absorb damage into one defensive layer.
        
        If the layer is fully depleted, excess damage is intentionally lost
        and does not carry through to the hext layer.
        
        Args:
            damage: Incoming damage before the multiplier is applied.
            layer: Attribute name of the layer ("shield" or "armor").
            multiplier: Damage multiplier for the relevant ammo type.
            
        Returns:
            Remaining damage that passed through the layer, or 0 if the
            layer was fully depleted.
        """
        current = getattr(self, layer)
        effective_damage = min(current, damage * multiplier)
        setattr(self, layer, current - effective_damage)

        if getattr(self, layer) == 0:
            return 0
        else:
            return max(0, damage - math.ceil(effective_damage / multiplier))

    def check_overheat(self) -> bool:
        """Return True if the Meka has reached maximum heat and cannot fire."""
        return self.heat >= MAX_HEAT
    
    def apply_heat(self) -> None:
        """Increase heat by a random amount within the configured range."""
        self.heat = min(self.heat + random.randint(HEAT_GAIN_MIN, HEAT_GAIN_MAX), MAX_HEAT)
    
    def cool_down(self) -> None:
        """Reset heat to zero."""
        self.heat = 0 

    def recharge_shield(self) -> None:
        """Spend a portion of current power to partially restore shields."""
        cost = math.ceil(self.power * SHIELD_RECHARGE_COST_RATE)
        missing_shield = self.max_shield - self.shield
        gain = math.ceil(missing_shield * SHIELD_RECHARGE_GAIN_RATE)
        self.power = max(0, self.power - cost) 
        self.shield = min(self.shield + gain, self.max_shield) 

    def available_ammo_types(self) -> list[AmmoType]:
        """Return all ammo types that still have at least one round remaining."""
        return [ammo_type for ammo_type, count in self.ammo.items() if count > 0]

class Game:
    """Manages the overall game loop, wave progression, and battle resolution.
    
    Atributes:
        player: The human player's Meka.
        enemy: The current enemy Meka. None between waves.
        wave: Current wave numbre, increments after each victory.
    """
    def __init__(self, player: Meka) -> None:
        self.player: Meka = player
        self.enemy: Meka | None = None
        self.wave: int = 1
        self.combat_log: deque[Text] = deque(maxlen=MAX_LOG_LINES)

    def run(self) -> None:
        """Main loop - spawn enemies and advance waves until the player is destroyed"""
        while self.player.is_alive():
            self.enemy = self.generate_enemy(self.wave)
            console.print(f"\n[bold magenta]{self.enemy.pilot_name}[/bold magenta] approaches! Prepare for battle!")
            time.sleep(2)
            self.battle_loop()
            if self.player.is_alive():
                self.wave += 1
                console.print(f"You destroyed [bold magenta]{self.enemy.pilot_name}[/bold magenta] Meka!")
                time.sleep(2)
                clear_screen()
                self.handle_upgrade()
                time.sleep(2)
                self.combat_log.clear()
                clear_screen()
        self.end_game()

    def battle_loop(self) -> None:
        """Run one complete battle until either Meka's power reaches zero."""
        while self.player.is_alive() and self.enemy.is_alive():
            clear_screen()
            Display.render_status(self.player)
            Display.render_status(self.enemy)
            player_action = self.player_choose()
            enemy_action = self.enemy_choose()
            self.resolve(player_action, enemy_action)
            Display.render_combat_log(self.combat_log)
            input()

    def log(self, message: Text) -> None:
        """Append a styled Text entry to the combat log.
        
        The deque's maxlen handles trimming automatically -
        no manual pop() or length check needed.
        """
        self.combat_log.append(message)


    def handle_upgrade(self) -> None:
        """Manage the full upgrade sequence: display, prompt, upgrade and heal."""
        Display.render_status(self.player)
        console.print(f"\nChoose your upgrade:")
        print(f"1. Increase Max Power (+{LEVEL_UP_POWER_BONUS})")
        print(f"2. Increase Armor (+{LEVEL_UP_ARMOR_BONUS})")
        print(f"3. Increase Shield (+{LEVEL_UP_SHIELD_BONUS})")
        print(f"4. Increase Attack (+{LEVEL_UP_ATTACK_BONUS})")

        while True:
            choice = input(">> ").strip()
            if choice in ("1", "2", "3", "4"):
                break
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

        message = self.player.apply_upgrade(choice)
        print(message)
        healed = self.player.apply_post_battle_heal()
        print(f"Emergency repairs complete! Power restored by {healed} points.")


    def player_choose(self) -> dict[str, ActionType | AmmoType]:
        """Prompt the player to pick an action. Re-prompts on invalid input."""
        while True:
            console.print("\n[bold]Choose your action:[/bold]")
            console.print("1. Attack")
            console.print("2. Cool Down")
            console.print("3. Reload Ammo")
            console.print("4. Recharge Shields")
            choice = input(">> ").strip()

            if choice == "1":
                #Guard before entering the ammo submenu.
                #If all ammo types are empty, pick_ammo would show three EMPTY
                if not self.player.available_ammo_types():
                    console.print("[red]No ammo remaining! Choose another action.[/red]")
                    continue
                ammo_type = self.pick_ammo(context="attack")
                return {"type": ActionType.ATTACK, "ammo": ammo_type}

            elif choice == "2":
                return {"type": ActionType.COOL_DOWN}

            elif choice == "3":
                ammo_type = self.pick_ammo(context="reload")
                return {"type": ActionType.RELOAD, "ammo": ammo_type}
            
            elif choice == "4":
                return {"type": ActionType.RECHARGE_SHIELD}

            else:
                console.print("[red]Invalid action. Please enter 1, 2, 3, or 4.[/red]")
            
    def enemy_choose(self) -> dict[str, ActionType | AmmoType]:
        """Determine the enemy's action using priority-based AI."""
        if self.enemy.check_overheat():
            return {"type": ActionType.COOL_DOWN}
        
        ammo_type = self.enemy_pick_ammo()
        if ammo_type:
            return {"type": ActionType.ATTACK, "ammo": ammo_type}
        else:
            ammo_reload = self.enemy_reload_ammo()
            return {"type": ActionType.RELOAD, "ammo": ammo_reload or AmmoType.STANDARD}
    
    def resolve(self, player_action: dict[str, ActionType | AmmoType], enemy_action: dict[str, ActionType | AmmoType]) -> None:
        """Calculate and apply both sides actions simultaneously."""
        player_result =  self.calculate_damage(self.player, player_action)
        enemy_result = self.calculate_damage(self.enemy, enemy_action)

        self.apply_action(self.player, self.enemy, player_action, player_result)
        self.apply_action(self.enemy, self.player, enemy_action, enemy_result)

    def calculate_damage(self, attacker: Meka, action: dict[str, ActionType | AmmoType]) -> DamageResult:
        """Calculate raw damage for an attack action.
        
        Returns:
            A DamageResult with the damage dealt and whether it was a critical hit.
            Returns DamageResult(damage=0, is_crit=False) for non-attack actions.
        """
        if action["type"] != ActionType.ATTACK:
            return DamageResult(damage=0, is_crit=False)
        
        damage = attacker.attack + random.randint(-DAMAGE_VARIANCE, DAMAGE_VARIANCE)
        is_crit = (
            action["ammo"] == AmmoType.STANDARD
            and random.random() < STANDARD_CRIT_CHANCE
        )

        if is_crit:
            damage *= CRIT_DAMAGE_MULTIPLIER

        return DamageResult(damage=damage, is_crit=is_crit)
    
    def apply_action(self,attacker: Meka, defender: Meka, action: dict[str, ActionType | AmmoType], result: DamageResult) -> None:
        """Execute one action and push a styled event into the combat log."""
        msg = Text() #Start with a empty Text; build it up with .append() calls

        if action["type"] == ActionType.ATTACK:
            if attacker.check_overheat():
                msg.append(attacker.pilot_name, style="bold")
                msg.append(" is OVERHEATED and couldn't fire!", style="red")
                self.log(msg)
                return #Early return: no damage, no ammo consumed, no heat gained
            defender.take_damage(result.damage, action["ammo"])
            attacker.consume_ammo(action["ammo"])
            attacker.apply_heat()
            ammo_name = action["ammo"].value.replace("_", " ")

            if result.is_crit:
                msg.append("YOU HIT A VULNERABLE SPOT! \n", style="bold yellow")
            damage_style = "bold yellow" if result.is_crit else "bold red"
            msg.append(attacker.pilot_name, style="bold")
            msg.append(f" fired {ammo_name} for ")
            msg.append(str(result.damage), style=damage_style)
            msg.append(" damage!")
            
        elif action["type"] == ActionType.COOL_DOWN:
            attacker.cool_down()
            msg.append(attacker.pilot_name, style="bold")
            msg.append(" Meka is cooling down!", style="cyan")

        elif action["type"] == ActionType.RELOAD:
            attacker.reload_ammo(action["ammo"])
            ammo_name = action["ammo"].value.replace("_", " ")
            msg.append(attacker.pilot_name, style="bold")
            msg.append(f" Meka reloaded {ammo_name} ammo!", style="green")

        elif action["type"] == ActionType.RECHARGE_SHIELD:
            attacker.recharge_shield()
            msg.append(attacker.pilot_name, style="bold")
            msg.append(f" Meka recharged its shields!", style="cyan")

        self.log(msg)

    def end_game(self) -> None:
        """Display the game-over screen, save the score, and show the leaderboard."""
        clear_screen()

        wave_word = "wave" if self.wave == 1 else "waves"
        console.print(f"[bold red] GAME OVER[/bold red] You survived [bold]{self.wave} {wave_word}[/bold]\n",)
        scores = self.save_score()
        Display.show_leaderboard(scores, self.player.pilot_name, self.wave)
        input("\nPress Enter to exit...")

    def save_score(self) -> None:
        """Append this run to the leaderboard, keeping only the top MAX_LEADERBOARD_SCORES entries."""
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
        return scores

    def load_scores(self) -> list[dict[str, str | int]]:
        """Load scores from disk. Returns an empty list if the file is missing or corrupted."""
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
        

    def enemy_pick_ammo(self) -> AmmoType | None:
        """Choose the best ammo type based on the player's current defences.
        
        Returns:
            The chosen AmmoType, or None if the enemy has no ammo left.
        """
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
        """Choose which ammo to reload based on the player's current stats.
        
        Returns:
            The AmmoType to reload, or None if no reload is prioritised.
        """
        player = self.player
        enemy = self.enemy

        if player.shield > ENEMY_RELOAD_THREAT_THRESHOLD and enemy.ammo.get(AmmoType.SHIELD_BREAKER, 0) == 0:
            return AmmoType.SHIELD_BREAKER
        
        if player.armor > ENEMY_RELOAD_THREAT_THRESHOLD and enemy.ammo.get(AmmoType.ARMOR_PIERCING, 0) == 0:
            return AmmoType.ARMOR_PIERCING
        return None
    
    def generate_enemy(self, wave: int) -> Meka:
        """Create a wave-scaled enemy Meka with stats capped at defined maximums.
        
        Args:
            wave: Current wave number, used to scale all stats.
            
        Returns:
            A new enemy Meka ready for battle.
        """
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

        return Meka(
            pilot_name=name,
            power=power,
            heat=0,
            armor=armor,
            shield=shield,
            ammo=ammo,
            attack=attack,
        )

    def pick_ammo(self, context: Literal["attack", "reload"] = "attack") -> AmmoType:
        """Prompt the player to choose an ammo type with contextual status display.
        
        Args:
            context: Controls how ammo status is presented.
            "attack" empty ammo dims the option
            "reload" empty ammo his highlighted as a priority candidate.
            
        Returns:
            The chosen AmmoType.
        """
        desc_width = max(len(d) for d in AMMO_DESCRIPTIONS.values())
        while True:
            title = "Choose ammo to reload:" if context == "reload" else "Choose ammo type:"
            console.print(f"\n[bold]{title}[/bold]")

            for key, ammo_type in AMMO_TYPES.items():
                count = self.player.ammo.get(ammo_type, 0)
                max_count = AMMO_MAX[ammo_type]
                desc = AMMO_DESCRIPTIONS[ammo_type]
                is_empty = count == 0
                is_low = 0 < count <= LOW_AMMO_THRESHOLD

                #Determine the status tag based on count and context
                if is_empty:
                    if context == "reload":
                        status = f"[bold yellow]{count}/{max_count} <- Reload[/bold yellow]"
                    else:
                        status = "EMPTY"
                elif is_low:
                    status = f"[red]{count}/{max_count}  LOW[/red]"
                else:
                    status = f"[green]{count}/{max_count}[/green]"

                #Dim the entire line in attack context when ammo is empty
                if is_empty and context == "attack":
                    console.print(f"  [dim]{key}. {desc:<{desc_width}}  {status}[/dim]")
                else:
                    console.print(f"  {key}. {desc:<{desc_width}}  {status}")

            choice = input(">> ").strip()
            ammo = AMMO_TYPES.get(choice)

            if ammo is None:
                console.print("[red]Invalid choice. Please enter 1, 2, or 3.[/red]")
                continue

            if context == "attack" and not self.player.has_ammo(ammo):
                ammo_name = AMMO_DESCRIPTIONS[ammo].split(" - ")[0].strip()
                console.print(f"[red]{ammo_name} is empty! Choose a different type.[/red]")
                continue

            return ammo

def main() -> None:
    """Entry point - schow the title screen, create the player, and start the game."""
    console.print(Panel(
        "[bold cyan]メカ戦闘[/bold cyan]",
        border_style="cyan",
        padding=(1,4),
        expand=False,
    ))

    pilot_name = input("Enter your name, Pilot: ").strip()
    if not pilot_name:
        pilot_name = "Unknown Pilot"

    player = Meka(
        pilot_name=pilot_name,
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