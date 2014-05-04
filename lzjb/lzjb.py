#!/usr/bin/env python
#
# An attempt at re-implementing LZJB compression in native Python.
#

import math
import sys
import time

NBBY = 8
MATCH_BITS = 6
MATCH_MIN = 3
MATCH_MAX = ((1 << MATCH_BITS) + (MATCH_MIN - 1))
OFFSET_MASK = ((1 << (16 - MATCH_BITS)) - 1)
LEMPEL_SIZE_BASE = 1024


def compress(s, with_size = True):
	"""
	Compresses the source string, returning a string holding the compressed data.
	If with_size is not false, the length of the input string is prepended to the result,
	in a special variable-length binary encoding.
	"""

	LEMPEL_SIZE = LEMPEL_SIZE_BASE

	# During compression, treat output string as list of code points.
	dst = []

	# Encode input size. This uses a variable-length encoding.
	if with_size:
		size = len(s)
		if size:
			sbytes = []
			size += 1
			while True:
				sbytes.append(size & 0x7f)
				size = int(math.floor(size / 128))
				if size == 0:
					break
			sbytes[0] |= 0x80
			for sb in reversed(sbytes):
				dst.append(sb)

	lempel = [0] * LEMPEL_SIZE
	copymask = 1 << (NBBY - 1)
	src = 0 # Current input offset.
	while src < len(s):
		copymask <<= 1
		if (copymask == (1 << NBBY)):
			copymask = 1
			copymap = len(dst)
			dst.append(0)
		if src > len(s) - MATCH_MAX:
			dst.append(ord(s[src]))
			src += 1
			continue
		hsh = (ord(s[src]) << 16) + (ord(s[src + 1]) << 8) + ord(s[src + 2])
		hsh += hsh >> 9
		hsh += hsh >> 5
		hsh &= LEMPEL_SIZE - 1
		offset = (src - lempel[hsh]) & OFFSET_MASK
		lempel[hsh] = src
		cpy = src - offset
		if cpy >= 0 and cpy != src and s[src:src+3] == s[cpy:cpy+3]:
			dst[copymap] = dst[copymap] | copymask
			for mlen in xrange(MATCH_MIN, MATCH_MAX):
				if s[src + mlen] != s[cpy + mlen]:
					break
			dst.append(((mlen - MATCH_MIN) << (NBBY - MATCH_BITS)) | (offset >> NBBY))
			dst.append(offset & 0xff)
			src += mlen
		else:
			dst.append(ord(s[src]))
			src += 1
	# Now implode the list of codepoints into an actual string.
	return "".join(map(chr, dst))


def decompressed_size(s):
	"""
	Returns a tuple (original length, length of size) from a string of compressed data.

	The original length is the length of the string passed to compress(), and length of
	size is the number of bytes that are used in s to express this size.
	"""
	dstSize = 0
	src = 0
	# Extract prefixed encoded size, if present.
	while True:
		c = ord(s[src])
		src += 1
		if (c & 0x80):
			dstSize |= c & 0x7f
			break
		dstSize = (dstSize | c) << 7
	dstSize -= 1	# -1 means "not known".		
	return (dstSize, src)


def decompress(s, with_size = True):
	"""
	Decompresses a string of compressed data, returning the original string.

	The value of with_size must match the value given when s was generated
	by compress().
	"""

	src = 0
	dstSize = 0
	if with_size:
		dstSize, src = decompressed_size(s)
		if dstSize < 0:
			return None

	dst = ""
	copymask = 1 << (NBBY - 1)
	while src < len(s):
		copymask <<= 1
		if copymask == (1 << NBBY):
			copymask = 1
			copymap = ord(s[src])
			src += 1
		if copymap & copymask:
			mlen = (ord(s[src]) >> (NBBY - MATCH_BITS)) + MATCH_MIN
			offset = ((ord(s[src]) << NBBY) | ord(s[src + 1])) & OFFSET_MASK
			src += 2
			cpy = len(dst) - offset
			if cpy < 0:
				return None
			while mlen > 0:
				dst += dst[cpy]
				cpy += 1
				mlen -= 1
		else:
			dst += s[src]
			src += 1
	return dst


if __name__ == "__main__":
	for a in sys.argv[1:]:
		if a.startswith("-"):
			print "**Ignoring unknown option '%s'" % a
		else:
			try:
				inf = open(a, "rb")
				data = inf.read()
				inf.close()
			except:
				print "**Failed to open '%s'" % a
				continue
			print "Loaded %u bytes from '%s'" % (len(data), a)
			t0 = time.clock()
			compr = compress(data)
			elapsed = time.clock() - t0
			rate = len(data) / (1024 * 1024 * elapsed)
			print " Compressed to %u bytes, %.2f%% in %s s [%.1f MB/s]" % (len(compr), 100.0 * len(compr) / len(data), elapsed, rate)
			decompr = decompress(compr)
			if decompr != data:
				print "**Decompression failed!"