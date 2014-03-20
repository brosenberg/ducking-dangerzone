#!/usr/bin/env python

import json

class Attack(object):
    def __init__(self, data):
        self.data = data
        self.damage_types = {}
        for damage in self.data['damage']:
            for damage_type in damage:
                self.damage_types[damage_type] = {}
                self.damage_types[damage_type]['dice']  = damage[damage_type]['dice']
                self.damage_types[damage_type]['sides'] = damage[damage_type]['sides']
                try:
                    self.damage_types[damage_type]['modifier'] = damage[damage_type]['modifier']
                except KeyError:
                    self.damage_types[damage_type]['modifier'] = 0

    def __str__(self):
        damage = []
        for dt in self.damage_types:
            mod = "+%s" % (self.damage_types[dt]['modifier'],) if self.damage_types[dt]['modifier'] > 0 else ''
            s = "%sd%s%s %s" %(self.damage_types[dt]['dice'], self.damage_types[dt]['sides'], mod, dt)
            damage.append(s)
        return ' +'.join(damage)


class Character(object):
    def __init__(self, data):
        self.data = data
        self.attacks = {}
        for attack in self.data['attacks']:
            self.attacks[attack] = Attack(self.data['attacks'][attack])

    def fullattack(self):
        for attack in self.data['full_attack']:
            print "%s: %s" % (attack.title(), self.attacks[attack])


def main():
    # TODO: Use argparse to specify this
    json_file = 'vorogoth.json'
    data = json.load(open(json_file))
    c = Character(data)
    c.fullattack()

if __name__ == '__main__':
    main()
