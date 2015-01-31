#!/usr/bin/env python

import json
import random

def clean_list(s):
    if type(s) is list or type(s) is set:
        return "[%s]" % (", ".join(s),)
    else:
        return s

def print_items(items):
    for item in items:
        print item

class Item(object):
    def __init__(self, name, data):
        self.name = name
        self.index_name = name
        self.data = data

    def __str__(self):
        attributes = []
        for attribute in self.data:
            if not attribute.startswith("_"):
                attributes.append("%s: %s" % (attribute, clean_list(self.data[attribute])))
        return "%s: %s" % (self.name, ", ".join(sorted(attributes)))

    def mod(self, mod_name, mod):
        self.name = "%s %s" % (mod_name, self.name)
        for attribute in mod:
            if attribute.startswith("_"):
                continue
            if attribute not in self.data:
                if 'append' in mod[attribute]:
                    self.data[attribute] = set()
                else:
                    self.data[attribute] = 0
            for change in mod[attribute]:
                if change == 'add':
                    self.data[attribute] += mod[attribute][change]
                if change == 'mult':
                    self.data[attribute] = int(self.data[attribute]*mod[attribute][change])
                if change == 'append':
                    try:
                        self.data[attribute] = set(self.data[attribute])
                        self.data[attribute].add(mod[attribute][change])
                    except TypeError:
                        pass


class ItemGenerator(object):
    def __init__(self, json_file):
        self.json = json.load(open(json_file))

    def random_item(self, item_list="items"):
        item = random.choice(self.json[item_list].keys())
        item_data = self.json[item_list][item]
        return (item, item_data)

    def generate(self, item_list="items", mod_chance=10):
        item = Item(*self.random_item(item_list=item_list))

        mod_roll = random.randint(1, 100)
        if mod_roll <= mod_chance:
            mod, mod_data = self.random_mod(item.index_name, item_list=item_list)
            item.mod(mod, mod_data)

        gen_list = self.json[item_list][item.index_name]["_meta"].get("generate")
        if gen_list:
            items = [item]
            if gen_list:
                for gen in gen_list:
                    try:
                        for new_item in self.generate(item_list=gen, mod_chance=mod_chance):
                            items.append(new_item)
                    except KeyError:
                        print "Failed to generate %s for %s" % (gen, item.name)
            return items

        return [item]

    def random_mod(self, item, item_list="items"):
        mod_list = self.json["mods"]["general"]

        for meta in self.json[item_list][item]["_meta"].values():
            try:
                mod_list.update(self.json["mods"][meta])
            except KeyError:
                pass
        mod = random.choice(mod_list.keys())
        mod_data = mod_list[mod]

        return (mod, mod_data)


if __name__ == "__main__":
    armor = ItemGenerator("armor.json")
    weapons = ItemGenerator("weapons.json")
    print "-- Random Armor --"
    print_items( armor.generate(mod_chance=100) )
    print "-- Random Weapon --"
    print_items( weapons.generate(mod_chance=100) )
    print "-- Random Bow Ammo --"
    print_items( weapons.generate(item_list="ammo:bow", mod_chance=100) )
