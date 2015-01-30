#!/usr/bin/env python

import json
import random

def print_item(item_name, item):
    print "%s: %s" % (item_name, ", ".join("%s: %s" % (x, item[x]) for x in item))

def mod_item(item, mod):
    for category in mod:
        if category in item:
            for change in mod[category]:
                if change == 'add':
                    item[category] += mod[category][change]
                if change == 'mult':
                    item[category] = int(item[category]*mod[category][change])
                if change == 'append':
                    try:
                        item[category] = set(item[category])
                        item[category].add(mod[category][change])
                    except TypeError:
                        pass
    return item

class ItemGenerator(object):
    def __init__(self, json_file):
        self.json = json.load(open(json_file))
        self.items = self.json['items']
        self.mods = self.json['mods']

    def generate(self, mod_chance=10):
        item = random.choice(self.items.keys())
        item_data = self.items[item]

        mod_roll = random.randint(1, 100)
        if mod_roll <= mod_chance:
            mod = random.choice(self.mods.keys())
            item = "%s %s" % (mod, item)
            item_data = mod_item(item_data, self.mods[mod])

        return (item, item_data)


if __name__ == "__main__":
    armor = ItemGenerator("armor.json")
    print_item( *armor.generate())
