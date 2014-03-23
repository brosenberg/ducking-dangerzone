#!/usr/bin/env python

import argparse
import copy
import json
import pprint
import random
import sys

from collections import Counter

BIGNUMBER = 1000

def roll(die, sides):
    r = 0
    for i in range(die):
        r += random.randint(1, sides)
    return r

class Attack(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data
        try:
            self.crit_range = self.data['crit']['range']
        except KeyError:
            self.crit_range = 20
        try:
            self.crit_multiplier = self.data['crit']['multiplier']
        except KeyError:
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

    def _roll_damage_type(self, type):
        dice  = self.damage_types[type]['dice']
        sides = self.damage_types[type]['sides']
        mod   = self.damage_types[type]['modifier']
        return roll(dice,sides)+mod

    def roll(self, name=None):
        attack = {'hit':{}, 'damage':{}}
        critical = {'hit':{}, 'damage':{}}
        if name is None:
            name = self.name
        try:
            for hit_type, hit in self.data['hit'].items():
                hit_roll = roll(1, 20)
                if hit_roll == 20:
                    attack['hit'][hit_type] = BIGNUMBER
                elif hit_roll == 1:
                    attack['hit'][hit_type] = -BIGNUMBER
                else:
                    attack['hit'][hit_type] = hit_roll+hit

                if hit_type == 'ac' and hit_roll >= self.crit_range:
                    confirm_roll = roll(1, 20)
                    if confirm_roll == 20:
                        critical['hit']['ac'] = BIGNUMBER
                    elif confirm_roll == 1:
                        critical['hit']['ac'] = -BIGNUMBER
                    else:
                        critical['hit']['ac'] = roll(1, 20)+hit
        except KeyError:
            pass

        for type in self.damage_types:
            attack['damage'][type] = self._roll_damage_type(type)

        if critical['hit']:
            for i in range(self.crit_multiplier-1):
                for type in self.damage_types:
                    damage = self._roll_damage_type(type)
                    try:
                        critical['damage'][type] += damage
                    except KeyError:
                        critical['damage'][type] = damage

            return {name: attack, name + ' (critical)': critical}
        else:
            return {name: attack}


class Character(object):
    def __init__(self, data):
        self.data = data
        self.attacks = {}

        for attack in self.data['attacks']:
            self.attacks[attack] = Attack(attack, self.data['attacks'][attack])

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

    def _full_attack(self):
        attacks = {}

        # Find the minimum to-hit rolls for dependent attacks
        def get_min_hits(attack):
            hits = {}
            for parent in self.data['full_attack'][attack]['depends']:
                try:
                    for parent_hit in attacks[parent]['hit']:
                        if parent_hit not in hits or attacks[parent]['hit'][parent_hit] < hits[parent_hit]:
                            hits[parent_hit] = attacks[parent]['hit'][parent_hit]
                except KeyError:
                    raise Exception, "Attack '%s' depends on non-existent attack '%s'" % (attack, parent)
            return hits


        for attack in sorted(self.data['full_attack']):
            attacks.update(self.attacks[ self.data['full_attack'][attack]['attack'] ].roll(name=attack))
        #FIXME: full_attack list needs to be in order of dependency, or things might break.
        # Calculate dependent attack rolls
        for attack in attacks:
            try:
                hits = get_min_hits(attack)
                hits.update(attacks[attack]['hit'])
                attacks[attack]['hit'] = hits
            except KeyError:
                pass

        return attacks

    def attack_specifics(self, attacks):
        for attack in sorted(attacks):
            try:
                if attacks[attack]['hit']['ac'] == -BIGNUMBER:
                    print "%s critically missed!" % (attack,)
                    continue
            except KeyError:
                pass
            hits = ' and '.join(['%s %s' % (t.upper(), h) for (t, h) in attacks[attack]['hit'].items()])
            damage = ' +'.join(['%s %s' % (d, t) for (t, d) in attacks[attack]['damage'].items()])
            damage_total = sum([d for d in attacks[attack]['damage'].values()])
            print "%s hit %s for %s (%s total)" % (attack, hits, damage, damage_total)

    def attack_summary(self, attacks):
        hit_types = set([x for y in attacks for x in attacks[y]['hit'].keys()])
        single_attacks = [x for x in attacks if len(attacks[x]['hit']) == 1]
        non_single_attacks = [x for x in attacks if len(attacks[x]['hit']) != 1]

        attack_tuples = {}

        for hit_type in hit_types:
            attack_tuples[hit_type] = [(z, attacks[y]['damage'][x], x) for y in single_attacks for x in attacks[y]['damage'] for w, z in attacks[y]['hit'].items() if w == hit_type and z != -BIGNUMBER]
            summed_damage = Counter()
            damage_totals = {}
            for (to_hit, damage, damage_type) in sorted(attack_tuples[hit_type]):
                summed_damage[damage_type] += damage
                damage_totals[to_hit] = dict(summed_damage)
            for to_hit in sorted(damage_totals):
                damage = ' +'.join(['%s %s' % (d, t) for (t, d) in damage_totals[to_hit].items()])
                damage_sum = sum([d for d in damage_totals[to_hit].values()])
                print "Hit %s %s for %s damage (%s total)" % (hit_type.upper(), to_hit, damage, damage_sum)
        print
        for attack in non_single_attacks:
            try:
                if attacks[attack]['hit']['ac'] == -BIGNUMBER:
                    print "%s critically missed!" % (attack,)
                    continue
            except KeyError:
                pass
            hits = ' and '.join(['%s %s' % (t.upper(), h) for (t, h) in attacks[attack]['hit'].items()])
            damage = ' +'.join(['%s %s' % (d, t) for (t, d) in attacks[attack]['damage'].items()])
            damage_total = sum([d for d in attacks[attack]['damage'].values()])
            print "%s hit %s for %s (%s total)" % (attack, hits, damage, damage_total)

    def full_attack(self):
        attacks = self._full_attack()
        self.attack_specifics(attacks)
        print
        self.attack_summary(attacks)


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
