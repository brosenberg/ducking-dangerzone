#!/usr/bin/env python

import json
import random
import sys

class Chooser(object):
    def __init__(self, json_file):
        self.json = json.load(open(json_file))

    def choose(self):
        for key in self.json.keys():
            print "%s: %s" % (key, random.choice(self.json[key]))

def main():
    if len(sys.argv) == 1:
        print "usage: %s [thing to choose]" % (sys.argv[0])
        return
    f = sys.argv[1] if sys.argv[1][-5:] == ".json" else "%s.json" % (sys.argv[1],)
    c = Chooser(f)
    c.choose()

if __name__ == '__main__':
    main()
