#!/bin/bash
set -e # Exit on error
cd "$(dirname "$0")/.."

mkdir -p work
rm -f work/*.cf

echo "--- Analyzing ---"
# Compile in order of dependency
ghdl -a --std=08 --workdir=work src/sqrt_standard.vhd
ghdl -a --std=08 --workdir=work src/sqrt_lossy.vhd
ghdl -a --std=08 --workdir=work src/sqrt_top.vhd
ghdl -a --std=08 --workdir=work sim/tb_sqrt_gen.vhd

echo "--- Elaborating ---"
ghdl -e --std=08 --workdir=work tb_sqrt_gen

echo "--- Running 2 Simulations ---"

# Standard
ghdl -r --std=08 --workdir=work tb_sqrt_gen -gsel_gen="'0'"

# Lossy
ghdl -r --std=08 --workdir=work tb_sqrt_gen -gsel_gen="'1'"