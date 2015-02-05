#!/usr/bin/env python

import copy
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

class NoModsFound(Exception):
    pass

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
        return "%s (%s)" % (self.name, "  ".join(sorted(attributes)))

    def mod(self, mod_name, mod):
        self.name = "%s %s" % (mod_name, self.name)
        for attribute in mod:
            if attribute.startswith("_"):
                continue
            if attribute not in self.data:
                if 'append' in mod[attribute] or 'remove' in mod[attribute]:
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
                if change == 'remove':
                    try:
                        self.data[attribute] = set(self.data[attribute])
                        self.data[attribute].remove(mod[attribute][change])
                    except KeyError:
                        pass
                    except TypeError:
                        pass


class ItemGenerator(object):
    def __init__(self, json_file, mods=True):
        self.json = json.load(open(json_file))
        if mods and not "mods" in self.json.keys():
            mods = False
        self.mods = mods

    # filters is list of a tuples of (key, value) where only things in the 
    # list that contain the key 'key' with value 'value' will be chosen from.
    def random_item(self, item_list="items", filters=None):
        random_list = copy.deepcopy(self.json[item_list])
        if filters:
            for filter_key, filter_value in filters:
                for key in random_list.keys():
                    if random_list[key].get(filter_key) != filter_value:
                        try:
                            del random_list[key]
                        except KeyError:
                            pass
        item = random.choice(random_list.keys())
        item_data = self.json[item_list][item]
        return (item, item_data)

    def generate(self, item_list="items", mod_chance=10, filters=None):
        item = Item(*self.random_item(item_list=item_list, filters=filters))

        if self.mods:
            mod_roll = random.randint(1, 100)
            if mod_roll <= mod_chance:
                try:
                    mod, mod_data = self.random_mod(item.index_name, item_list=item_list)
                    item.mod(mod, mod_data)
                except NoModsFound:
                    pass

        if "_meta" in self.json[item_list][item.index_name].keys():
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

        if "_meta" in self.json[item_list][item].keys():
            for meta in self.json[item_list][item]["_meta"].values():
                if type(meta) is list:
                    continue
                try:
                    mod_list.update(self.json["mods"][meta])
                except KeyError:
                    pass
        if len(mod_list.keys()) == 0:
            raise NoModsFound
        mod = random.choice(mod_list.keys())
        mod_data = mod_list[mod]

        return (mod, mod_data)


if __name__ == "__main__":
    armor = ItemGenerator("armor.json")
    weapons = ItemGenerator("weapons.json")
    shield = ItemGenerator("shields.json")
    gear = ItemGenerator("gear.json")
    magic = ItemGenerator("magic.json")

    print "-- Random Armor --"
    print_items( armor.generate(mod_chance=100) )
    print "-- Random Weapon --"
    print_items( weapons.generate(mod_chance=100) )
    print "-- Random Bow Ammo --"
    print_items( weapons.generate(item_list="ammo:bow", mod_chance=100) )
    print "-- Random Shield --"
    print_items( shield.generate(mod_chance=100) )
    print "-- Random Gear --"
    print_items( gear.generate(mod_chance=100) )
    print "-- Random Spell --"
    print_items( magic.generate(item_list="spells") )
    print "-- Random Level 5 Wizard Spell--"
    print_items( magic.generate(item_list="spells", filters=[("class", "wizard"), ("level", 5)]) )
