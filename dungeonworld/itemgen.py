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

def filter_item(items, item, keys, test):
    item_value = items[item]
    for key in keys:
        item_value = item_value[key]
    if test['type'] == 'gt':
        if item_value > test['value']:
            return {item: items[item]}
    elif test['type'] == 'gte':
        if item_value >= test['value']:
            return {item: items[item]}
    elif test['type'] == 'lt':
        if item_value < test['value']:
            return {item: items[item]}
    elif test['type'] == 'lte':
        if item_value <= test['value']:
            return {item: items[item]}
    elif test['type'] == 'eq':
        if item_value == test['value']:
            return {item: items[item]}
    elif test['type'] == 'ne':
        if item_value != test['value']:
            return {item: items[item]}
    elif test['type'] == 'in':
        if test['value'] in item_value:
            return {item: items[item]}
    elif test['type'] == 'not in':
        if not test['value'] in item_value:
            return {item: items[item]}
    return None

#FIXME: This is OR'ing the sets together, not AND'ing them.
def filter_items(items, keys, test):
    filtered = {}
    for item in items:
        try:
            filtered.update(filter_item(items, item, keys, test))
        except TypeError:
            pass
    return filtered

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

    def random_item(self, item_list="items", filters=None):
        random_list = self.json[item_list]
        if filters:
            for keys, test in filters:
                random_list = filter_items(random_list, keys, test)
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
    magic = ItemGenerator("spells.json")
    magic_items = ItemGenerator("magic_items.json")

    print "-- Random Armor --"
    print_items( armor.generate(mod_chance=100) )
    print

    print "-- Random Weapon --"
    print_items( weapons.generate(mod_chance=100) )
    print

    print "-- Random Bow Ammo --"
    print_items( weapons.generate(item_list="ammo:bow", mod_chance=100) )
    print

    print "-- Random Shield --"
    print_items( shield.generate(mod_chance=100) )
    print

    print "-- Random Gear --"
    print_items( gear.generate(mod_chance=100) )
    print

    print "-- Random Spell --"
    print_items( magic.generate(item_list="spells") )
    print

    spell_filter = [(['level'], {'type': 'eq', 'value': 5}), (['class'], {'type': 'eq', 'value': 'wizard'})]
    print "-- Random Level 5 Wizard Spell --"
    print_items( magic.generate(item_list="spells", filters=spell_filter) )
    print

    onehand_filter = [(['tags'], {'type': 'not in', 'value': 'two-handed'}),
                      (['_meta', 'type'], {'type': 'eq', 'value': 'melee'})]
    print "-- Random One-handed Weapon --"
    print_items( weapons.generate(mod_chance=100, filters=onehand_filter) )
    print

    print "-- Random Magic Item --"
    print_items( magic_items.generate() )
    print
