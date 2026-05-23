# メカ戦闘

A 1v1 meka battle game where you must deplete the rival meka's power.

<img width="1116" height="628" alt="Recording 2026-05-21 210747" src="https://github.com/user-attachments/assets/5911bbd1-d453-4266-8369-21794e5a4503" />

## How to Play

### Objective
- Defeat the enemy meka by reducing its Power to 0.

### Stats
- **Power:** Your meka's health (max 100). If it reaches 0, you lose.
- **Heat:** Weapon/system heat level (0–100). Attacking increases heat; at 100, you cannot attack.
- **Armor:** A secondary buffer that absorbs damage after Shields.
- **Shield:** The first layer that absorbs incoming damage.
- **Ammo:** The number of attacks you can perform.

### Actions
Choose an action by entering its corresponding number.

#### 1) Attack
- Consumes 1 ammo and increases Heat.
- Choose between 3 ammo types: Standard, Armor Piercing, and Shield Breaker.
- Standard ammo can land critical hits.
- Armor Piercing and Shield Breaker deal double damage to their corresponding defenses.
- Damage is applied in this order: Shield → Armor → Power.
- If your Heat reaches 100 after attacking, your meka overheats and cannot attack until it cools down.

#### 2) Cool Down
- Reduces Heat by a large amount.
- Use this when Heat is high to avoid overheating.

#### 3) Recharge Ammo
- Refills ammo: 10 Standard rounds or 2 Shield Breaker / Armor Piercing rounds.
- Use this when you are low on ammo and cannot attack.

#### 4) Recharge Shields
- Redirects 20% of your current Power to recharge 50% of missing Shields.

### Enemy Behavior
- The enemy follows the same rules as the player.
- It uses ammo to attack, gains heat when attacking, and will cool down and recharge when necessary.

That's it — good luck, pilot!

## Controls

- Number key + Enter

## Installation

### Windows
- Download the `.zip` file from Releases, extract it, and run `mekasentou.exe`.

### Linux

- Download the `Source code (zip)` file from Releases. 
```bash
unzip MekaSentou-0.2.0.zip
cd MekaSentou-0.2.0
python main.py
```

## License

GNU General Public License
