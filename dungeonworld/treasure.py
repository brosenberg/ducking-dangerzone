#!/usr/bin/env python

import itemgen
import random
import scrolls
import sys

class Treasure(object):
    def __init__(self, generators):
        self.generators = generators
        self.items = []
        self.coins = 0

    def __str__(self):
        s = ""
        if len(self.items):
            #s += "\n".join(sorted([str(x) for x in self.items]))
            s += "\n".join(self.items)
        if self.coins:
            if len(s):
                s += "\n"
            s += "%d coin%s" % (self.coins, "s" if self.coins > 1 else "")
        return s

    def generate(self, level, items=None):
        if items is None:
            items = random.randint(1+level/2, level+1)
        for i in range(0, items):
            self._generate(level)

    def _generate(self, level):
        # Generate coins half the time
        if random.randint(0, 1):
            self.coins = random.randint((level**2)/2, (5*level**2))
        else:
            mod_chance = 10 + random.randint(level/2, level*2)
            items = random.choice(self.generators).generate(mod_chance=mod_chance)
            self.items += [str(x) for x in items]

def main():
    if len(sys.argv) == 1:
        print "Usage: %s [level]" % (sys.argv[0],)
        return

    level = int(sys.argv[1])

    armorgen = itemgen.ItemGenerator("armor.json")
    weapongen = itemgen.ItemGenerator("weapons.json")
    shieldgen = itemgen.ItemGenerator("shields.json")
    geargen = itemgen.ItemGenerator("gear.json")
    magicgen = itemgen.ItemGenerator("spells.json")
    scrollgen = scrolls.Scroll(magicgen)

    treasure = Treasure([armorgen, weapongen, shieldgen, geargen, scrollgen])
    treasure.generate(level)
    print treasure

if __name__ == '__main__':
    main()
