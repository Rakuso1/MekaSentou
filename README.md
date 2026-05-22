# メカ戦闘

A basic 1 vs 1 Meka battle game, deplete the power of the rival Meka.

<img width="1116" height="628" alt="Recording 2026-05-21 210747" src="https://github.com/user-attachments/assets/588d2da3-cb06-4bc0-9a99-e3a3532feb0d" />

## How to play

Objective:
- Defeat the enemy Meka by reducing its Power to 0.

Stats:
- Power: Your Meka's health (max 100). If it reaches 0 you lose.
- Heat: Weapon/system heat (0–100). Attacking increases heat; at 100 you cannot attack.
- Armor: Secondary buffer that absorbs damage after Shield (max shown as 50).
- Shield: First layer that absorbs incoming damage (max shown as 50).
- Ammo: Number of attacks you can perform (max 10).

Actions (choose by entering the number):
1) Attack
- Consumes 1 ammo and triggers a heat increase.
- The game first subtracts damage from Shield, then Armor, then Power.
- If your Heat reaches 100 from attacking, your Meka overheats and cannot attack until cooled.

2) Cool Down
- Reduces Heat by a large amount (helps recover from near-overheat).
- Use this when Heat is high to avoid being unable to attack.

3) Recharge Ammo
- Refills Ammo (up to the maximum of 10).
- Use when you're low on ammo and cannot attack.

Enemy Behavior:
- The enemy has the same actions and rules as the player: it uses ammo to attack, gains heat when attacking, and will cool down and recharge if it cannot attack.

Tips and Strategy:
- Balance attacking and cooling: spam attacks early, but cool before Heat reaches 100.
- Manage Ammo: recharge when low so you can continue attacking.
- Watch the bars shown on-screen to make informed choices.

That's it — good luck, pilot!

## Controls

NumberKey + Enter

## License
GNU General Public License
