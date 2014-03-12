#!/usr/bin/env python

import random
import sys

def roll(die, sides):
    r = 0
    for i in range(die):
        r += random.randint(1,sides)
    return r

def to_hit(mod):
    result = roll(1,20)
    if result == 20:
        confirm = roll(1,20)+mod
        print "Nat 20! Confirm: %s" % (confirm,)
    if result == 1:
        print "Nat 1!"
    return result+mod

class Vorogoth(object):
    def __init__(self):
        self.attack = []
        self.grabs = []
        self.rend_ac = 0

    def __clear(self):
        self.attack = []
        self.grabs = []
        self.rend_ac = sys.maxint

    def __bite(self, enlarged=False):
        hit = to_hit(13)
        if enlarged:
            damage = roll(3,6)+9
        else:
            damage = roll(1,8)+8 + roll(1,6)
        self.attack.append([hit, damage])
        return [hit, damage]

    def __grab(self, enlarged=False):
        if enlarged:
            cmb = roll(1,20)+20
            damage = roll(2,8)+roll(2,6)+18
        else:
            cmb = roll(1,20)+19
            damage = roll(4,6)+16
        return [cmb, damage]

    def __claw(self, enlarged=False):
        hit = to_hit(13)
        if enlarged:
            damage = roll(4,6)+9
        else:
            damage = roll(3,6)+8
        if self.rend_ac > hit:
            self.rend_ac = hit
        self.attack.append([hit, damage])
        return [hit, damage]

    def __rend(self, enlarged=False):
        if enlarged:
            damage = roll(4,6)+13
        else:
            damage = roll(3,6)+12
        self.attack.append([self.rend_ac, damage])
        return damage

    def bite(self, enlarged=False):
        r = self.__bite(enlarged)
        print "  Bite  AC %s [%s] for %s [%s] damage." % (r[0], r[0]-2, r[1], r[1]+4)

    def claw(self, enlarged=False):
        r = self.__claw(enlarged)
        s = self.__grab(enlarged=enlarged)
        self.grabs.append([r[0], s[0], s[1]])
        print "  Claw  AC %s [%s] for %s [%s] damage." % (r[0], r[0]-2, r[1], r[1]+4)
        print "  Grab CMD %s [%s] for %s [%s] damage." % (s[0], s[0]-2, s[1], s[1]+4)

    def rend(self, enlarged=False):
        r = self.__rend(enlarged)
        rend_ac = self.rend_ac
        print "  Rend  AC %s [%s] for %s [%s] damage." % (rend_ac, rend_ac-2, r, r+4)

    def attacks(self):
        summed_attacks = set()
        summed_grabs = set()
        print
        for rolls in self.attack:
            summed_attacks.add((rolls[0], sum([x[1] for x in self.attack if x[0]>=rolls[0]])))
        for rolls in self.grabs:
            #summed_grabs.add((rolls[0], rolls[1], sum([x[2] for x in self.grabs if x[0]>=rolls[0]])))
            summed_grabs.add((rolls[0], rolls[1], rolls[2]))
        for attack in sorted(summed_attacks):
            print "Hit AC %s for %s damage" % (attack[0], attack[1])
        for grab in sorted(summed_grabs):
            print "Grabbed AC %s CMD %s for %s damage" % (grab[0], grab[1], grab[2])

    def full_attack(self, enlarged=False):
        self.__clear()
        self.bite(enlarged)
        self.claw(enlarged)
        self.claw(enlarged)
        self.rend(enlarged)
        self.attacks()

def main():
    v = Vorogoth()
    print '-'*80
    print 'Normal attack [Power attack]'
    print '-'*80
    print "Normal"
    v.full_attack(enlarged=False)
    print '-'*80
    print "ENLARGED"
    v.full_attack(enlarged=True)
    print '-'*80

if __name__ == '__main__':
    main()
