#!/bin/bash


coredumpctl gdb "/root/prod-bin/angstrom-new" -- \
  -batch \
  -ex "set pagination off" \
  -ex "thread apply all bt full" \
  -ex "info registers" \
  -ex "quit" | sed -n '1,200p'
