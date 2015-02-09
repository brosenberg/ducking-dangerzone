#!/usr/bin/env python

import itemgen
import random

if __name__ == '__main__':
    magic = itemgen.ItemGenerator("magic.json")
    scroll_level = int(random.triangular(1, 18, 1))
    scroll_type = random.choice(["cleric", "wizard"])
    scroll_spells = []
    print "Level %s %s scroll containing the following spells:" % (scroll_level, scroll_type)
    while scroll_level:
        [spell] = magic.generate(item_list="spells", filters=[("class", scroll_type)])
        while spell.data["level"] > scroll_level:
            [spell] = magic.generate(item_list="spells", filters=[("class", scroll_type)])
        scroll_level -= spell.data["level"]
        scroll_spells.append(spell)

    itemgen.print_items(scroll_spells)
