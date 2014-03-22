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
            #attacks[attack] = self.attacks[ self.data['full_attack'][attack]['attack'] ].roll()
            attacks.update(self.attacks[ self.data['full_attack'][attack]['attack'] ].roll(name=attack))
            #attacks[attack] =
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

    def full_attack(self):
        attacks = self._full_attack()
        results = {}
        for attack in sorted(attacks):
            hits = ' and '.join(['%s %s' % (t.upper(), h) for (t, h) in attacks[attack]['hit'].items()])
            damage = ' +'.join(['%s %s' % (d, t) for (t, d) in attacks[attack]['damage'].items()])
            damage_total = sum([d for d in attacks[attack]['damage'].values()])
            print "%s hit %s for %s (%s total)" % (attack, hits, damage, damage_total)

            if len(attacks[attack]['hit']) == 1:
                hit_type = attacks[attack]['hit'].keys()[0]
                hit_roll = attacks[attack]['hit'].values()[0]
                if hit_type not in results:
                    results[hit_type] = {hit_roll:{}}
                if hit_roll not in results[hit_type]:
                    results[hit_type].update({hit_roll:{}})
                for damage_type in attacks[attack]['damage']:
                    if damage_type not in results[hit_type][hit_roll]:
                        results[hit_type][hit_roll][damage_type] = attacks[attack]['damage'][damage_type]
                    else:
                        results[hit_type][hit_roll][damage_type] += attacks[attack]['damage'][damage_type]

        # Oh god, what even happened here?
        # This is going through all of the attack results and adding the damage
        # of lower to-hit values to the higher to-hit values.
        # So, an attack roll of 15 would add its damage to an attack roll of 30
        for hit_type in results:
            for hit_roll in results[hit_type].keys():
                for hit_roll2 in results[hit_type].keys():
                    if hit_roll < hit_roll2:
                        for damage_type in results[hit_type][hit_roll]:
                            if damage_type in results[hit_type][hit_roll2]:
                                results[hit_type][hit_roll2][damage_type] += results[hit_type][hit_roll][damage_type]
                            else:
                                results[hit_type][hit_roll2][damage_type] = results[hit_type][hit_roll][damage_type]

        print
        for hit_type in results:
            for hit_roll in sorted(results[hit_type].keys()):
                damage = ' +'.join(['%s %s' % (d, t) for (t, d) in results[hit_type][hit_roll].items()])
                damage_total = sum([d for d in results[hit_type][hit_roll].values()])
                print "Hit %s %s for %s (%s total)" % (hit_type.upper(), hit_roll, damage, damage_total)
        print "Total damage:", sum([attacks[attack]['damage'][type] for attack in attacks for type in attacks[attack]['damage']])


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
