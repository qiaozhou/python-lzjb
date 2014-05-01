#!/usr/bin/env python
#
# An attempt at re-implementing LZJB compression in native Python.
#

import math

NBBY = 8
MATCH_BITS = 6
MATCH_MIN = 3
MATCH_MAX = ((1 << MATCH_BITS) + (MATCH_MIN - 1))
OFFSET_MASK = ((1 << (16 - MATCH_BITS)) - 1)
LEMPEL_SIZE_BASE = 1024

def compress(s, compression = 1, c_compatible = True):
	LEMPEL_SIZE = LEMPEL_SIZE_BASE
	EXPAND = True
	if compression != 1:
		LEMPEL_SIZE *= 2
		compression = max(1, min(compression, 9)) - 1
		EXPAND = 1 << int(math.floor(compression / 2))
		if compression & 1:
			EXPAND = round(EXPAND * 1.5)
		if compression >= 2 and compression <= 4:
			EXPAND += 1
	out = ""
	return out

if __name__ == "__main__":
	for c in xrange(1, 9):
		compress("whatever ever is what this ever?", c)
