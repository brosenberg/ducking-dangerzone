#!/usr/bin/env python

import argparse
import json
import random
import re
import sys

from collections import Counter

BIG_NUMBER = 1000

SIZE_MODIFIERS = { 'fine':        8,
                   'diminutive':  4,
                   'tiny':        2,
                   'small':       1,
                   'medium':      0,
                   'large':      -1,
                   'huge':       -2,
                   'gargantuan': -4,
                   'colossal':   -8
                 }

def roll(die, sides):
    r = 0
    for _i in range(die):
        r += random.randint(1, sides)
    return r

def stat_mod(stat_value):
    return int((stat_value-10)/2)

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

        damage_mod = self.data.get('damage_mod', 0)
        primary_damage_type = self.data['damage'][0].keys()[0]
        try:
            self.data['damage'][0][primary_damage_type]['modifier'] += damage_mod
        except KeyError:
            self.data['damage'][0][primary_damage_type]['modifier'] = damage_mod

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

    def _roll_damage_type(self, damage_type):
        dice  = self.damage_types[damage_type]['dice']
        sides = self.damage_types[damage_type]['sides']
        mod   = self.damage_types[damage_type]['modifier']
        return roll(dice, sides)+mod

    def roll(self, name=None):
        attack = {'hit':{}, 'damage':{}}
        critical = {'hit':{}, 'damage':{}}
        if name is None:
            name = self.name
        try:
            for hit_type, hit in self.data['hit'].items():
                hit_roll = roll(1, 20)
                if hit_roll == 20:
                    attack['hit'][hit_type] = BIG_NUMBER
                elif hit_roll == 1:
                    attack['hit'][hit_type] = -BIG_NUMBER
                else:
                    attack['hit'][hit_type] = hit_roll+hit

                if hit_type == 'ac' and hit_roll >= self.crit_range:
                    confirm_roll = roll(1, 20)
                    if confirm_roll == 20:
                        critical['hit']['ac'] = BIG_NUMBER
                    elif confirm_roll == 1:
                        critical['hit']['ac'] = -BIG_NUMBER
                    else:
                        critical['hit']['ac'] = roll(1, 20)+hit
        except KeyError:
            pass

        for damage_type in self.damage_types:
            attack['damage'][damage_type] = self._roll_damage_type(damage_type)

        if critical['hit']:
            for _i in range(self.crit_multiplier-1):
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
        self.name = self.data.get('name')
        self.attacks = {}
        self.attack_name_len = 0

        stats = self.data['stats']
        self.bab = stats.get('bab', 0)
        self.size = stats.get('size', 'medium')
        self.strength = stats.get('strength', 10)
        self.dexterity = stats.get('dexterity', 10)
        self.melee_attack_mod = self.bab + stat_mod(self.strength) + SIZE_MODIFIERS[self.size]
        self.range_attack_mod = self.bab + stat_mod(self.dexterity) + SIZE_MODIFIERS[self.size]
        self.cmb = self.bab + stat_mod(self.strength) - SIZE_MODIFIERS[self.size]

        self.finesse = stats.get('finesse')

        for attack in self.data['attacks']:
            melee_attack = self.data['attacks'][attack].get('melee_attack', True)

            if 'hit' in self.data['attacks'][attack]:
                if 'ac' in self.data['attacks'][attack]['hit']:
                    if melee_attack and not self.finesse:
                        self.data['attacks'][attack]['hit']['ac'] += self.melee_attack_mod
                    else:
                        self.data['attacks'][attack]['hit']['ac'] += self.range_attack_mod

                if 'cmd' in self.data['attacks'][attack]['hit']:
                    self.data['attacks'][attack]['hit']['cmd'] += self.cmb

            self.attacks[attack] = Attack(attack, self.data['attacks'][attack])

        for attack in self.data['full_attack']:
            if len(attack) > self.attack_name_len:
                self.attack_name_len = len(attack)

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
        # Prune attacks that depended on attacks that critically missed
        for attack in attacks.keys():
            try:
                if 'depends' in self.data['full_attack'][attack] and attacks[attack]['hit']['ac'] == -BIG_NUMBER:
                    del attacks[attack]
            except KeyError:
                pass

        return attacks

    def _print_attack_roll(self, attack, attack_name=None):
        try:
            if attack['hit']['ac'] == -BIG_NUMBER and attack_name:
                print "%s critically missed!" % (attack_name.rjust(self.attack_name_len),)
                return
        except KeyError:
            pass
        hits = ' and '.join(['%s %s' % (t.upper(), h) for (t, h) in attack['hit'].items()])
        damage = ' +'.join(['%s %s' % (d, t) for (t, d) in attack['damage'].items()])
        damage_total = sum([d for d in attack['damage'].values()])
        if attack_name:
            print "%s hit %s for %s (%s total)" % (attack_name.rjust(self.attack_name_len), hits, damage, damage_total)
        else:
            print "Hit %s for %s (%s total)" % (hits, damage, damage_total)

    def attack_summary(self, attacks):
        hit_types = set([x for y in attacks for x in attacks[y]['hit'].keys()])
        single_attacks = [x for x in attacks if len(attacks[x]['hit']) == 1]
        non_single_attacks = [x for x in attacks if len(attacks[x]['hit']) != 1]

        attack_tuples = {}

        for hit_type in hit_types:
            attack_tuples[hit_type] = []
            for attack in single_attacks:
                for ht, to_hit in attacks[attack]['hit'].items():
                    if ht == hit_type and to_hit != -BIG_NUMBER:
                        for damage_type in attacks[attack]['damage']:
                            attack_tuples[hit_type].append((to_hit, attacks[attack]['damage'][damage_type], damage_type))

            summed_damage = Counter()
            damage_totals = {}
            for (to_hit, damage, damage_type) in sorted(attack_tuples[hit_type]):
                summed_damage[damage_type] += damage
                damage_totals[to_hit] = dict(summed_damage)
            for to_hit in sorted(damage_totals):
                self._print_attack_roll( {'hit': {hit_type: to_hit}, 'damage': damage_totals[to_hit]} )
        print '  Non-summed Attacks ---'
        for attack in non_single_attacks:
            self._print_attack_roll(attacks[attack], attack_name=attack)

    def full_attack(self):
        attacks = self._full_attack()
        if self.name:
            print "%s full attacks!" % (self.name,)
        print '  Attack Specifics ---'
        for attack in sorted(attacks):
            self._print_attack_roll(attacks[attack], attack_name=attack)
        print
        print '  Attack Summary ---'
        self.attack_summary(attacks)


def main():
    p = argparse.ArgumentParser(description="Destroy your enemies!")
    p.add_argument('-e', '--enlarged', default=False, action='store_true', help='Enlarge Person modifier')
    p.add_argument('-j', '--json-file', type=str, required=True, help='JSON file to load stats from')
    p.add_argument('-p', '--print-attacks', default=False, action='store_true', help='Print attacks')
    p.add_argument('-u', '--uber', default=False, action='store_true', help='You are incredibly high level')
    args = p.parse_args()

    if args.uber:
        global BIG_NUMBER
        BIG_NUMBER = sys.maxint

    if args.enlarged:
        t = re.split('.json',args.json_file)
        args.json_file = t[0] + '-enlarged.json'

    data = json.load(open(args.json_file))
    c = Character(data)

    if args.print_attacks:
        print c
    else:
        c.full_attack()


if __name__ == '__main__':
    main()
