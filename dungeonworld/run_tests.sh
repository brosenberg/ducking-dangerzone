#!/bin/bash
# lol tests
while true; do
    ./item_generator.py >/tmp/item_generator.output || break
done
