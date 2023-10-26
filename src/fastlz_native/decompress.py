#!/usr/bin/env python3
"""FastLZ decompression algorithm in python native

Author: Oscar Diaz <odiaz@ieee.org>
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

def fastlz_decompress(datain: bytes) -> bytes:
    """Decompress with FastLZ algorithm.
    
    @param data input buffer
    @type bytes
    @return decompressed data
    @rtype bytes
    """
    if not isinstance(datain, bytes):
        raise ValueError("Input must be bytes")
        
    # expect compress output length in the first uint32 value
    if len(datain) < 4:
        raise ValueError("No headerlen present")
        
    doutlen = int.from_bytes(datain[:4], byteorder='little')
    
    if (doutlen / 256) > len(datain):
        raise ValueError("Bad headerlen")
        
    # level
    level = datain[4] >> 5
    if level == 0:
        return _fastlz_decompress_lv1(datain[4:], doutlen)
    elif level == 1:
        return _fastlz_decompress_lv2(datain[4:], doutlen)
    else:
        raise ValueError(f"Unknown compression level ({level})")
        
def _fastlz_decompress_lv1(datain: bytes, doutlen: int) -> bytes:
    """Internal function: level1 type decompression"""
    opcode_0 = datain[0]
    datain_idx = 1
    
    dataout = bytearray(doutlen)
    dataout_idx = 0;

    while True:
        op_type = opcode_0 >> 5
        op_data = opcode_0 & 31

        if op_type == 0b000:
            # literal run
            run = 1 + opcode_0
            dataout[dataout_idx:dataout_idx + run] = datain[datain_idx:datain_idx + run]
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
    """Internal function: level2 type decompression"""
    opcode_0 = datain[0]
    datain_idx = 1
    
    dataout = bytearray(doutlen)
    dataout_idx = 0;

    while True:
        op_type = opcode_0 >> 5
        op_data = opcode_0 & 31
        
        if op_type == 0b000:
            # literal run
            run = 1 + op_data
            dataout[dataout_idx:dataout_idx + run] = datain[datain_idx:datain_idx + run]
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
                ofs += struct.unpack('=h', datain[datain_idx:datain_idx+2])[0]
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
                _ofs = datain[datain_idx:datain_idx+2]
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
    """Internal function: helper to emulate memmove behavior"""
    for i in range(mlen):
        data[stidx + i] = data[stidx - offset + i]
    
