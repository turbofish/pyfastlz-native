#!/usr/bin/env python3
"""FastLZ compression algorithm in python native

Author: Tomas Hellström <turbofish@fripost.org>
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
from typing import Optional


def compress(data: bytes, level: int = 1) -> bytes:
    """Compress data using the FastLZ algorithm.

    Parameters
    ----------
    data : bytes
        Input data to compress. Must be a bytes object.
    level : int, default=1
        Compression level. Must be 1 or 2. Level 1 provides faster compression
        with good compression ratio. Level 2 is currently not implemented.

    Returns
    -------
    bytes
        Compressed data with header. Format:
        - First 4 bytes: Original data length (little-endian uint32)
        - Fifth byte: Level information encoded in upper 3 bits + first opcode
        - Remaining bytes: Compressed data stream

    Raises
    ------
    ValueError
        If data is not bytes or level is not 1 or 2.
    NotImplementedError
        If level 2 is requested (not yet implemented).

    Examples
    --------
    >>> data = b"Hello, World!"
    >>> compressed = compress(data, level=1)
    >>> len(compressed) < len(data)  # Compression achieved
    True
    """

    if not isinstance(data, bytes):
        raise ValueError("Input must be bytes")

    if level not in (1, 2):
        raise ValueError("Compression level must be 1 or 2")

    if len(data) == 0 or data == b"":
        # Return empty compressed data with header
        header = struct.pack("<I", 0)  # decompressed length = 0
        return header + bytes([(level - 1) << 5])  # level in upper 3 bits

    # Compress the data
    if level == 1:
        compressed = _fastlz_compress_lv1(data)
    else:
        raise NotImplementedError("Level 2 compression is not implemented")

    # Build header: decompressed length (4 bytes) + level in first byte of compressed data
    header = struct.pack("<I", len(data))
    level_byte = (
        ((level - 1) << 5) | (compressed[0] & 0x1F)
        if compressed
        else ((level - 1) << 5)
    )

    if compressed:
        return header + bytes([level_byte]) + compressed[1:]
    return header + bytes([level_byte])


def _fastlz_compress_lv1(data: bytes) -> bytes:
    """Compress data using FastLZ level 1 algorithm.

    This is the internal compression function that implements the FastLZ level 1
    algorithm. It uses a greedy approach to find matches with a maximum lookback
    distance of 8191 bytes and maximum match length of 264 bytes.

    Parameters
    ----------
    data : bytes
        Input data to compress. Should not be empty.

    Returns
    -------
    bytes
        Raw compressed data stream without header. Contains opcodes and data:
        - Literal runs: opcode (length-1) followed by literal bytes
        - Short matches: 2-byte instruction (length <= 8)
        - Long matches: 3-byte instruction (length > 8)

    Notes
    -----
    The algorithm uses the following constants:
    - MAX_DISTANCE: 8191 bytes (13-bit offset)
    - MAX_MATCH_LEN: 264 bytes
    - MIN_MATCH_LEN: 3 bytes
    """
    if len(data) == 0:
        return b""

    output = bytearray()
    pos = 0
    anchor = 0  # Start of current literal run

    # Maximum lookback distance for level 1 (13-bit offset)
    MAX_DISTANCE = 8191
    # Maximum match length for level 1
    MAX_MATCH_LEN = 264
    # Minimum match length
    MIN_MATCH_LEN = 3

    while pos < len(data):
        # Look for matches
        best_match = _find_match_lv1(
            data, pos, MAX_DISTANCE, MIN_MATCH_LEN, MAX_MATCH_LEN
        )

        if best_match is None:
            # No match found, advance position
            pos += 1
            continue

        match_offset, match_length = best_match

        # Emit any pending literals
        if pos > anchor:
            _emit_literals(output, data[anchor:pos])

        # Emit the match
        _emit_match_lv1(output, match_offset, match_length)

        # Advance position past the match
        pos += match_length
        anchor = pos

    # Emit any remaining literals
    if anchor < len(data):
        _emit_literals(output, data[anchor:])

    return bytes(output)


def _find_match_lv1(
    data: bytes, pos: int, max_distance: int, min_match_len: int, max_match_len: int
) -> Optional[tuple[int, int]]:
    """Find the best backward match for level 1 compression.

    Searches backwards from the current position to find the longest match
    within the specified distance constraints. Uses a simple linear search
    for all possible offsets.

    Parameters
    ----------
    data : bytes
        Input data being compressed.
    pos : int
        Current position in the data to find matches for.
    max_distance : int
        Maximum backward distance to search (typically 8191 for level 1).
    min_match_len : int
        Minimum match length to consider valid (typically 3).
    max_match_len : int
        Maximum match length to consider (typically 264 for level 1).

    Returns
    -------
    Optional[tuple[int, int]]
        If a match is found, returns (offset, length) where:
        - offset: 1-based backward offset to the match position
        - length: length of the match in bytes
        Returns None if no valid match is found.

    Notes
    -----
    The function prioritizes longer matches over shorter ones when multiple
    matches exist at different offsets.
    """
    if pos + min_match_len > len(data):
        return None

    best_length = 0
    best_offset = 0

    # Search backwards for matches
    start = max(0, pos - max_distance)

    for offset in range(1, min(pos - start + 1, max_distance + 1)):
        match_pos = pos - offset
        if match_pos < 0:
            break

        # Check how long the match is
        length = 0
        while (
            pos + length < len(data)
            and match_pos + length >= 0
            and length < max_match_len
            and data[pos + length] == data[match_pos + length]
        ):
            length += 1

        if length >= min_match_len and length > best_length:
            best_length = length
            best_offset = offset

    if best_length >= min_match_len:
        return (best_offset, best_length)

    return None


def _emit_literals(output: bytearray, literals: bytes) -> None:
    """Emit literal run instructions for level 1 compression.

    Encodes literal bytes into the output stream using FastLZ level 1 format.
    Large literal runs are split into chunks of maximum 32 bytes each.

    Parameters
    ----------
    output : bytearray
        Output buffer to append the encoded literal instructions to.
    literals : bytes
        Literal bytes to encode.

    Notes
    -----
    Level 1 literal format:
    - Opcode byte: length - 1 (0-31, representing 1-32 bytes)
    - Followed by the literal bytes

    For literals longer than 32 bytes, multiple instructions are emitted.
    """
    pos = 0
    while pos < len(literals):
        # Maximum literal run is 32 bytes (L = 31, meaning 32 bytes)
        chunk_size = min(32, len(literals) - pos)
        chunk = literals[pos : pos + chunk_size]

        # Opcode: 000 (literal run) + L (length - 1)
        opcode = chunk_size - 1  # L = length - 1
        output.append(opcode)
        output.extend(chunk)

        pos += chunk_size


def _emit_match_lv1(output: bytearray, offset: int, length: int) -> None:
    """Emit match instruction for level 1 compression.

    Parameters
    ----------
    output : bytearray
        The output bytearray to append the encoded match instruction to
    offset : int
        The backward offset to the match position (1-based)
    length : int
        The length of the match in bytes

    Notes
    -----
    For short matches (length <= 8):
        - Uses 2-byte instruction format
        - M = length - 2 (3-8 becomes 1-6)
        - R = offset - 1 (13 bits: 5 from first byte + 8 from second byte)

    For long matches (length > 8):
        - Uses 3-byte instruction format
        - First byte: 0xE0 | (offset >> 8)
        - Second byte: length - 9
        - Third byte: offset & 0xFF
    """
    # Offset is 1-based in the algorithm, but we need 0-based for encoding
    encoded_offset = offset - 1

    if length <= 8:
        # Short match: 2-byte instruction
        # M = length - 2 (so 3-8 becomes 1-6)
        # R = offset (13 bits total: 5 from opcode[0] + 8 from opcode[1])
        M = length - 2
        R = encoded_offset

        opcode0 = (M << 5) | (R >> 8)  # M in upper 3 bits, upper 5 bits of R
        opcode1 = R & 0xFF  # lower 8 bits of R

        output.append(opcode0)
        output.append(opcode1)
    else:
        # Long match: 3-byte instruction
        # opcode[0] = 111 + upper 5 bits of offset
        # opcode[1] = match length - 9
        # opcode[2] = lower 8 bits of offset
        M = length - 9
        R = encoded_offset

        opcode0 = 0xE0 | (R >> 8)  # 111 (0xE0) + upper 5 bits of R
        opcode1 = M & 0xFF  # match length - 9
        opcode2 = R & 0xFF  # lower 8 bits of R

        output.append(opcode0)
        output.append(opcode1)
        output.append(opcode2)
