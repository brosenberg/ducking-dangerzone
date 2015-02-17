#!/usr/bin/env python

import itemgen
import random

class Scroll(object):
    def __init__(self, spellgen, max_level=18):
        self.spellgen = spellgen
        self.generate(mod_chance=max_level)

    def __str__(self):
        return """Level %s %s scroll containing the following spells:
\t%s""" % (self.level,
           self.type,
           "\n\t".join([str(x) for x in self.spells]))

    # Provides the same interface as the other generators
    def generate(self, mod_chance=18):
        self.level = int(random.triangular(1, mod_chance, 1))
        self.type = random.choice(["cleric", "wizard"])
        self.spells = []
        scroll_level = self.level
        spell_filter = (['class'], {'type': 'eq', 'value': self.type})
        while scroll_level:
            [spell] = self.spellgen.generate(item_list="spells", filters=[spell_filter])
            while spell.data["level"] > scroll_level:
                [spell] = self.spellgen.generate(item_list="spells", filters=[spell_filter])
            scroll_level -= spell.data["level"]
            self.spells.append(spell)
        return [self]


if __name__ == '__main__':
    spellgen = itemgen.ItemGenerator("spells.json")
    scroll = Scroll(spellgen)
    print scroll
