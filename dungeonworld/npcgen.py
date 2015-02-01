#!/usr/bin/env python

import itemgen
import json
import random

class NPCGenerator(object):
    def __init__(self, json_file="npc.json", mod_chance=10):
        self.json = json.load(open(json_file))
        self.generate()

    def __str__(self):
        return """%s %s the %s %s %s whose desire is %s.
Skills: %s""" % (self.first_name,
        self.last_name,
        self.gender,
        self.race,
        self.profession,
        self.goal,
        "  ".join(["%s:%s" % (x, self.skills[x]) for x in self.skills]))

    def generate(self):
        self.gender = random.choice(self.json["gender"])
        self.race = random.choice(self.json["race"])
        self.goal = random.choice(self.json["goal"])
        self.profession = random.choice(self.json["skills"])
        self.first_name = random.choice(self.json["%s %s first name" % (self.race, self.gender)])
        self.last_name = random.choice(self.json["%s last name" % (self.race,)])

        skill_points = random.randint(2, 10)
        loyalty_max = skill_points-1 if skill_points-1<=4 else 4
        self.skills = { "Loyalty": random.randint(-1, loyalty_max) }
        skill_points -= self.skills["Loyalty"]+1
        self.skills[self.profession] = 1
        while skill_points:
            if random.randint(0,1):
                self.skills[self.profession] += 1
            else:
                random_skill = random.choice(self.json["skills"])
                self.skills[random_skill] = self.skills.get(random_skill, 0) + 1
            skill_points -= 1


if __name__ == "__main__":
    npc = NPCGenerator()
    armor = itemgen.ItemGenerator("armor.json")
    weapons = itemgen.ItemGenerator("weapons.json")
    shield = itemgen.ItemGenerator("shields.json")

    print npc
