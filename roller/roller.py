#!/usr/bin/env python

import argparse
import random
import json

def roll(die, sides):
    r = 0
    for i in range(die):
        r += random.randint(1,sides)
    return r


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
        attack = ''
        # I think the data structure for this might need to be rethought.
        try:
            for hit_type, hit in self.data['hit'].items():
                attack += "+%s %s " % (hit, hit_type.upper())
        except KeyError:
            pass
        damage = []
        for dt in self.damage_types:
            mod = "+%s" % (self.damage_types[dt]['modifier'],) if self.damage_types[dt]['modifier'] != 0 else ''
            s = "%sd%s%s %s" %(self.damage_types[dt]['dice'], self.damage_types[dt]['sides'], mod, dt)
            damage.append(s)
        return attack + ' +'.join(damage)

    def roll(self):
        attack = {'hit':{}, 'damage':{}}
        try:
            for hit_type, hit in self.data['hit'].items():
                attack['hit'][hit_type] = roll(1,20)+hit
        except KeyError:
            pass
        for dt in self.damage_types:
            attack['damage'][dt] = roll(self.damage_types[dt]['dice'], self.damage_types[dt]['sides']) + self.damage_types[dt]['modifier']
        return attack


class Character(object):
    def __init__(self, data):
        self.data = data
        self.attacks = {}
        for attack in self.data['attacks']:
            self.attacks[attack] = Attack(self.data['attacks'][attack])

    def fullattack(self):
        for attack in sorted(self.data['full_attack']):
            try:
                print "if %s hit" % (' and '.join(self.data['full_attack'][attack]['depends']),)
            except KeyError:
                pass
            print "%8s: %s" % (attack, self.attacks[ self.data['full_attack'][attack]['attack'] ])
            print self.attacks[ self.data['full_attack'][attack]['attack'] ].roll()


def main():
    p = argparse.ArgumentParser(description="Destroy your enemies!")
    p.add_argument('-j', '--json', type=str, required=True, help='JSON file to load stats from')
    args = p.parse_args()

    data = json.load(open(args.json))
    c = Character(data)
    c.fullattack()

if __name__ == '__main__':
    main()
