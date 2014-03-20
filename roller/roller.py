#!/usr/bin/env python

import argparse
import json
import random
import sys

BIGNUMBER = 1000

def roll(die, sides):
    r = 0
    for i in range(die):
        r += random.randint(1, sides)
    return r

class Attack(object):
    def __init__(self, data):
        self.data = data
        try:
            self.crit_range = self.data['crit']['range']
            self.crit_multiplier = self.data['crit']['multiplier']
        except KeyError:
            self.crit_range = 20
            self.crit_multiplier = 2
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

    def __repr__(self):
        return repr(self.data)

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
            s = "%sd%s%s %s" % (self.damage_types[dt]['dice'], self.damage_types[dt]['sides'], mod, dt)
            damage.append(s)
        return attack + ' +'.join(damage)

    def roll(self):
        attack = {'hit':{}, 'damage':{}}

        try:
            for hit_type, hit in self.data['hit'].items():
                hit_roll = roll(1, 20)
                if hit_roll == 20:
                    attack['hit'][hit_type] = BIGNUMBER
                else:
                    attack['hit'][hit_type] = hit_roll+hit
                if hit_type == 'ac' and hit_roll >= self.crit_range:
                    confirm_roll = roll(1, 20)
                    if confirm_roll == 20:
                        attack['hit']['confirm'] = BIGNUMBER
                    else:
                        attack['hit']['confirm'] = roll(1, 20)+hit
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

        # TODO: Make this work later.
        #self.ordered_attacks = []
        #d = {}
        #for attack in sorted(self.data['full_attack']):
            #try:
                #d[attack] = self.data['full_attack']['depends']
            #except KeyError:
                #self.ordered_attacks.append(attack)
        #for attack in d:

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        s = []
        for attack in sorted(self.data['full_attack']):
            try:
                s.append("if %s hit" % (' and '.join(self.data['full_attack'][attack]['depends']),))
            except KeyError:
                pass
            s.append("%8s: %s" % (attack, self.attacks[ self.data['full_attack'][attack]['attack'] ]))
        return "\n".join(s)

    def full_attack(self):
        attacks = {}

        def get_min_hits(attack):
            hits = {}
            for parent in self.data['full_attack'][attack]['depends']:
                for parent_hit in attacks[parent]['hit']:
                    if parent_hit not in hits or attacks[parent]['hit'][parent_hit] < hits[parent_hit]:
                        hits[parent_hit] = attacks[parent]['hit'][parent_hit]
            return hits

        #FIXME: THIS SHOULD REALLY BE SORTED BETTER
        for attack in sorted(self.data['full_attack']):
            attacks[attack] = self.attacks[ self.data['full_attack'][attack]['attack'] ].roll()
        for attack in attacks:
            try:
                hits = get_min_hits(attack)
                hits.update(attacks[attack]['hit'])
                attacks[attack]['hit'] = hits
            except KeyError:
                pass
            print attack, attacks[attack]


def main():
    p = argparse.ArgumentParser(description="Destroy your enemies!")
    p.add_argument('-j', '--json-file', type=str, required=True, help='JSON file to load stats from')
    p.add_argument('-u', '--uber', default=False, action='store_true', help='You are incredibly high level')
    args = p.parse_args()

    if args.uber:
        global BIGNUMBER
        BIGNUMBER = sys.maxint

    data = json.load(open(args.json_file))
    c = Character(data)
    c.full_attack()

if __name__ == '__main__':
    main()
