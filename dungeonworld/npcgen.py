#!/usr/bin/env python

import itemgen
import json
import random

class NPCGenerator(object):
    def __init__(self, json_file="npc.json", mod_chance=10):
        self.json = json.load(open(json_file))
        self.generate()

    def __str__(self):
        spells = ""
        if self.spells:
            spells = "\n\nSpells:\n%s" % ("\n".join([str(x) for x in self.spells]),)
        return """%s %s is a %s %s %s whose desire is %s.
%s has %s %s eyes, %s %s hair, and %s skin covering %s %s body.
Their special knack is %s.

Hitpoints: %s
Damage: %s
Skills: %s

Coins: %s
Salary: %s

Wearing:
%s

Wielding:
%s

Inventory:
%s%s""" % (self.first_name,
        self.last_name,
        self.gender,
        self.race,
        self.profession,
        self.goal,
        self.first_name,
        self.eye_type,
        self.eye_color,
        self.hair_style,
        self.hair_color,
        self.skin,
        "her" if self.gender == "female" else "his",
        self.build,
        self.knack,
        self.hitpoints,
        self.damage_die,
        "  ".join(["%s: %s" % (x, self.skills[x]) for x in self.skills]),
        self.coins,
        self.salary,
        "\n".join([str(x) for x in self.armor]),
        "\n".join([str(x) for x in self.wielding]),
        "\n".join(self.inventory),
        spells)

    def generate(self):
        self.gender = random.choice(self.json["gender"])
        self.race = random.choice(self.json["race"])
        self.goal = random.choice(self.json["goal"])
        self.profession = random.choice(self.json["skills"].keys())
        self.inventory = [
            random.choice(self.json["skills"][self.profession]["items"])
        ]
        self.damage_die = self.json["skills"][self.profession]["damage_die"]
        self.knack = random.choice(self.json["knacks"])
        self.first_name = random.choice(self.json["%s %s first name" % (self.race, self.gender)])
        self.last_name = random.choice(self.json["%s last name" % (self.race,)])

        self.eye_type = random.choice(self.json["eye type"])
        self.eye_color = random.choice(self.json["eye color"])
        self.hair_color = random.choice(self.json["hair color"])
        self.hair_style = random.choice(self.json["hair style"])
        self.skin = random.choice(self.json["skin"])
        self.build = random.choice(self.json["build"])

        skill_points = random.randint(2, 10)
        self.salary = int(random.uniform(0.75, 4) * skill_points)
        self.hitpoints = int(random.uniform(1.25, 2.25) * skill_points)
        self.wealth = int(random.triangular(0, 10, skill_points))
        self.coins = 0

        self.spells = set()

        loyalty_max = skill_points-1 if skill_points-1<=4 else 4
        self.skills = { "Loyalty": random.randint(-1, loyalty_max) }
        skill_points -= self.skills["Loyalty"]+1
        self.skills[self.profession] = 1
        while skill_points:
            if random.randint(0,1):
                self.skills[self.profession] += 1
            else:
                random_skill = random.choice(self.json["skills"].keys())
                self.skills[random_skill] = self.skills.get(random_skill, 0) + 1
            skill_points -= 1

        if self.skills[self.profession] < 3:
            self.damage_die = "w[2%s]" % (self.damage_die,)
        if self.skills[self.profession] > 5:
            self.damage_die = "b[2%s]" % (self.damage_die,)

        self.armor = None
        self.wielding = None

    def equip_thyself(self, weapongen, armorgen, shieldgen):
        one_handed = lambda x: not "two-handed" in x[0].data['tags'] and x[0].data['_meta']['type'] == "melee"

        self.armor = armorgen.generate(mod_chance=10+self.wealth)
        self.wielding = weapongen.generate(mod_chance=10+self.wealth)
        # See if the weapon is a one handed melee weapon
        if one_handed(self.wielding):
            roll = random.randint(0,4)
            if roll == 4:
                onehand_filter = [(['tags'], {'type': 'not in', 'value': 'two-handed'}),
                                  (['_meta', 'type'], {'type': 'eq', 'value': 'melee'})]
                self.wielding += weapongen.generate(mod_chance=10+self.wealth, filters=onehand_filter)
            elif roll:
                self.wielding += shieldgen.generate(mod_chance=10+self.wealth)

    def spend_wealth(self, generators, coin_chance=60):
        while self.wealth:
            roll = random.randint(1,100)
            if roll <= coin_chance:
                self.coins += int(random.triangular(1, 10, 1))
            else:
                for item in random.choice(generators).generate(mod_chance=10+self.wealth):
                    self.inventory.append(str(item))
            self.wealth -= 1

    def learn_spells(self, magicgen):

        def _learn_spells(skill, skill_filter):
            if skill in self.skills:
                spell_levels = self.skills[skill]
                while spell_levels:
                    level_filter = [(['level'], {'type': 'lte', 'value': spell_levels})]
                    spells = magicgen.generate(item_list="spells", filters=skill_filter+level_filter)
                    # FIXME: The filtering system should be able to do this
                    # This is ensuring that the spells in the list are unique
                    while set(spells).intersection(self.spells):
                        spells = magicgen.generate(item_list="spells", filters=skill_filter+level_filter)
                    for spell in spells:
                        self.spells.add(str(spell))
                        spell_levels -= spell.data['level']

        adept_filter = [(['class'], {'type': 'eq', 'value': 'wizard'})]
        priest_filter = [(['class'], {'type': 'eq', 'value': 'cleric'})]
        for skill, skill_filter in [('Adept', adept_filter), ('Priest', priest_filter)]:
            _learn_spells(skill, skill_filter)


if __name__ == "__main__":
    npc = NPCGenerator()
    armorgen = itemgen.ItemGenerator("armor.json")
    weapongen = itemgen.ItemGenerator("weapons.json")
    shieldgen = itemgen.ItemGenerator("shields.json")
    geargen = itemgen.ItemGenerator("gear.json")
    magicgen = itemgen.ItemGenerator("spells.json")

    npc.equip_thyself(weapongen, armorgen, shieldgen)
    npc.spend_wealth([weapongen, geargen])
    npc.learn_spells(magicgen)

    print '-'*80
    print npc
    print '-'*80
