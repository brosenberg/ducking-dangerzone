#!/usr/bin/env python

import itemgen
import json
import random

class NPCGenerator(object):
    def __init__(self, json_file="npc.json", mod_chance=10):
        self.json = json.load(open(json_file))
        self.generate()

    def __str__(self):
        return """%s the %s %s %s, whose desire is %s.
Skill Points:  %s""" % (self.name,
        self.gender,
        self.race,
        self.primary_skill,
        self.goal,
        self.skill_points)

    def generate(self):
        self.gender = random.choice(self.json["gender"])
        self.race = random.choice(self.json["race"])
        self.goal = random.choice(self.json["goal"])
        self.primary_skill = random.choice(self.json["skills"])
        self.name = random.choice(self.json["%s %s first name" % (self.race, self.gender)])
        self.skill_points = random.randint(2, 10)


if __name__ == "__main__":
    npc = NPCGenerator()
    armor = itemgen.ItemGenerator("armor.json")
    weapons = itemgen.ItemGenerator("weapons.json")
    shield = itemgen.ItemGenerator("shields.json")

    print npc
