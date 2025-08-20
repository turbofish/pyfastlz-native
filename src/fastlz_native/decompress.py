#!/usr/bin/env python3
"""FastLZ decompression algorithm in python native

Author: Oscar Diaz <odiaz@ieee.org>
Additional documentation: Tomas Hellström <turbofish@fripost.org>
Copyright (c) 2023 Oscar Diaz <odiaz@ieee.org>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import struct


def decompress(datain: bytes) -> bytes:
    """Decompress data compressed with the FastLZ algorithm.

    Automatically detects the compression level from the header and uses the
    appropriate decompression algorithm (level 1 or level 2).

    Parameters
    ----------
    datain : bytes
        Compressed data including header. Must be output from the compress() function.
        Expected format:
        - First 4 bytes: Original data length (little-endian uint32)
        - Fifth byte: Level info in upper 3 bits + first opcode in lower 5 bits
        - Remaining bytes: Compressed data stream

    Returns
    -------
    bytes
        Decompressed data, restored to original form.

    Raises
    ------
    ValueError
        If input is not bytes, header is malformed, or compression level is unknown.
        Specific errors:
        - "Input must be bytes": Input is not a bytes object
        - "No headerlen present": Input too short (< 4 bytes)
        - "Bad headerlen": Claimed length is unreasonably large
        - "Unknown compression level": Level not 0 (level 1) or 1 (level 2)

    Examples
    --------
    >>> original = b"Hello, World!"
    >>> compressed = compress(original)
    >>> decompressed = decompress(compressed)
    >>> decompressed == original
    True
    """
    if not isinstance(datain, bytes):
        raise ValueError("Input must be bytes")

    # expect compress output length in the first uint32 value
    if len(datain) < 4:
        raise ValueError("No headerlen present")

    doutlen = int.from_bytes(datain[:4], byteorder="little")

    if (doutlen / 256) > len(datain):
        raise ValueError("Bad headerlen")

    # level
    level = datain[4] >> 5
    if level == 0:
        return _fastlz_decompress_lv1(datain[4:], doutlen)
    if level == 1:
        return _fastlz_decompress_lv2(datain[4:], doutlen)
    raise ValueError(f"Unknown compression level ({level})")


def _fastlz_decompress_lv1(datain: bytes, doutlen: int) -> bytes:
    """Decompress data using FastLZ level 1 algorithm.

    Internal function that implements the FastLZ level 1 decompression algorithm.
    Processes opcodes and reconstructs the original data using literal runs and
    backward references (matches).

    Parameters
    ----------
    datain : bytes
        Compressed data stream starting with the first opcode (level info included).
        The level information is encoded in the upper 3 bits of the first byte.
    doutlen : int
        Expected length of decompressed output in bytes.

    Returns
    -------
    bytes
        Decompressed data of exactly doutlen bytes.

    Notes
    -----
    Level 1 opcode format:
    - Literal run: opcode = length - 1, followed by literal bytes
    - Short match: 2 bytes, length = 2 + (opcode >> 5), offset from remaining bits
    - Long match: 3 bytes, starts with 0xE0 prefix, variable length encoding
    """
    if doutlen == 0:
        return b""

    opcode_0 = datain[0]
    datain_idx = 1

    dataout = bytearray(doutlen)
    dataout_idx = 0

    while True:
        op_type = opcode_0 >> 5
        op_data = opcode_0 & 31

        if op_type == 0b000:
            # literal run
            run = 1 + opcode_0
            dataout[dataout_idx : dataout_idx + run] = datain[
                datain_idx : datain_idx + run
            ]
            datain_idx += run
            dataout_idx += run

        elif op_type == 0b111:
            # long match
            opcode_1 = datain[datain_idx]
            datain_idx += 1
            opcode_2 = datain[datain_idx]
            datain_idx += 1

            match_len = 9 + opcode_1
            ofs = (op_data << 8) + opcode_2 + 1

            _memmove(dataout, dataout_idx, ofs, match_len)
            dataout_idx += match_len

        else:
            # short match
            opcode_1 = datain[datain_idx]
            datain_idx += 1

            match_len = 2 + op_type
            ofs = (op_data << 8) + opcode_1 + 1

            _memmove(dataout, dataout_idx, ofs, match_len)
            dataout_idx += match_len

        if datain_idx < len(datain):
            opcode_0 = datain[datain_idx]
            datain_idx += 1
        else:
            break

    return bytes(dataout)


def _fastlz_decompress_lv2(datain: bytes, doutlen: int) -> bytes:
    """Decompress data using FastLZ level 2 algorithm.

    Internal function that implements the FastLZ level 2 decompression algorithm.
    Supports longer matches and 16-bit offsets compared to level 1, with variable
    length encoding for long matches.

    Parameters
    ----------
    datain : bytes
        Compressed data stream starting with the first opcode (level info included).
        The level information is encoded in the upper 3 bits of the first byte.
    doutlen : int
        Expected length of decompressed output in bytes.

    Returns
    -------
    bytes
        Decompressed data of exactly doutlen bytes.

    Notes
    -----
    Level 2 opcode format:
    - Literal run: op_type=0, length = 1 + op_data
    - Short match: op_type=1-6, length = 2 + op_type, supports 16-bit offsets
    - Long match: op_type=7, variable length encoding, supports 16-bit offsets

    Level 2 supports extended 16-bit offsets when offset == 8191, allowing
    much larger lookback distances than level 1.
    """
    if doutlen == 0:
        return b""

    opcode_0 = datain[0]
    datain_idx = 1

    dataout = bytearray(doutlen)
    dataout_idx = 0

    while True:
        op_type = opcode_0 >> 5
        op_data = opcode_0 & 31

        if op_type == 0b000:
            # literal run
            run = 1 + op_data
            dataout[dataout_idx : dataout_idx + run] = datain[
                datain_idx : datain_idx + run
            ]
            datain_idx += run
            dataout_idx += run

        elif op_type == 0b111:
            # long match
            match_len = 9

            while True:
                nn = datain[datain_idx]
                datain_idx += 1

                match_len += nn
                if nn != 255:
                    break

            ofs = op_data << 8
            ofs += datain[datain_idx]
            datain_idx += 1

            if ofs == 8191:
                # match from 16-bit distance
                ofs += struct.unpack("=h", datain[datain_idx : datain_idx + 2])[0]
                datain_idx += 2

            _memmove(dataout, dataout_idx, ofs, match_len)
            dataout_idx += match_len

        else:
            # short match
            match_len = 2 + op_type

            ofs = op_data << 8
            ofs += datain[datain_idx]
            datain_idx += 1

            if ofs == 8191:
                # match from 16-bit distance
                _ofs = datain[datain_idx : datain_idx + 2]
                datain_idx += 2
                ofs += _ofs[0] << 8
                ofs += _ofs[1]

            _memmove(dataout, dataout_idx, ofs, match_len)
            dataout_idx += match_len

        if datain_idx < len(datain):
            opcode_0 = datain[datain_idx]
            datain_idx += 1
        else:
            break

    return bytes(dataout)


def _memmove(data: bytearray, stidx: int, offset: int, mlen: int) -> None:
    """Copy data within a bytearray, handling overlapping regions correctly.

    Emulates the behavior of C's memmove function for copying data from one
    location to another within the same buffer. Handles overlapping source
    and destination regions correctly by copying byte by byte.

    Parameters
    ----------
    data : bytearray
        The bytearray to perform the copy operation on.
    stidx : int
        Starting index in the destination (where to copy to).
    offset : int
        Backward offset from stidx to the source location (where to copy from).
        The source starts at position (stidx - offset).
    mlen : int
        Number of bytes to copy.

    Notes
    -----
    This function is crucial for FastLZ decompression as matches often refer
    to recently decompressed data, creating overlapping copy operations.
    The byte-by-byte copying ensures that each byte is available for subsequent
    copies within the same operation.

    For example, copying "ABC" with offset=3 and length=9 will produce
    "ABCABCABC" by repeatedly copying the pattern.
    """
    for i in range(mlen):
        data[stidx + i] = data[stidx - offset + i]
