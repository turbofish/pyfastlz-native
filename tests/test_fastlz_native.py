"""Tests for FastLZ native implementation."""

import random
import struct

import pytest  # type: ignore[import-not-found]
from fastlz_native import compress, decompress


class TestFastLZNative:
    """Test cases for FastLZ compression and decompression."""

    def test_small_data(self):
        """Test compression and decompression of small data."""
        data = b"Hello, World!"
        compressed = compress(data)
        decompressed = decompress(compressed)
        assert decompressed == data

    def test_level_1_compression(self):
        """Test explicit level 1 compression."""
        data = b"Test data for level 1 compression"
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

    def test_empty_data(self):
        """Test compression and decompression of empty data."""
        data = b""
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

    def test_single_byte(self):
        """Test compression and decompression of single byte."""
        data = b"A"
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

    def test_repeated_data(self):
        """Test compression of highly repetitive data."""
        data = b"A" * 1000
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data
        # Should achieve good compression ratio
        assert len(compressed) < len(data)

    def test_repeated_pattern(self):
        """Test compression of repeated patterns."""
        data = b"ABCD" * 250  # 1000 bytes total
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data
        # Should achieve good compression ratio
        assert len(compressed) < len(data)

    def test_no_compression_random_data(self):
        """Test that random data doesn't compress well."""
        # Use fixed seed for reproducible tests
        random.seed(42)
        data = bytes([random.randint(0, 255) for _ in range(1000)])
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

    def test_text_data(self):
        """Test compression of text data."""
        data = b"The quick brown fox jumps over the lazy dog. " * 50
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data
        # Should achieve good compression ratio
        assert len(compressed) < len(data)

    def test_binary_data_patterns(self):
        """Test compression of various binary patterns."""
        # Test alternating pattern
        data = b"\x00\xff" * 500
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

        # Test increasing sequence
        data = bytes(range(256)) * 4
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

    def test_large_data(self):
        """Test compression of larger data sets."""
        # Create a 10KB data with some patterns
        base_pattern = b"FastLZ compression test with some repeated content. "
        data = base_pattern * 200  # ~10KB
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data
        # Should achieve good compression ratio
        assert len(compressed) < len(data)

    def test_very_small_inputs(self):
        """Test various very small inputs."""
        test_cases = [
            b"",
            b"a",
            b"ab",
            b"abc",
            b"abcd",
            b"abcde",
        ]
        for data in test_cases:
            compressed = compress(data, level=1)
            decompressed = decompress(compressed)
            assert decompressed == data

    def test_compression_header_structure(self):
        """Test that compression header has correct structure."""
        data = b"test data"
        compressed = compress(data, level=1)

        # Should have at least 5 bytes (4 for length + 1 for level/opcode)
        assert len(compressed) >= 5

        # First 4 bytes should be original length in little-endian
        original_length = struct.unpack("<I", compressed[:4])[0]
        assert original_length == len(data)

        # Fifth byte should encode level (0 for level 1 in upper bits)
        level_byte = compressed[4]
        level = level_byte >> 5
        assert level == 0  # Level 1 is encoded as 0

    def test_different_data_sizes(self):
        """Test compression with various data sizes."""
        sizes = [1, 2, 3, 4, 5, 10, 31, 32, 33, 63, 64, 65, 100, 255, 256, 257, 1000]
        for size in sizes:
            data = b"X" * size
            compressed = compress(data, level=1)
            decompressed = decompress(compressed)
            assert decompressed == data
            assert len(decompressed) == size

    def test_all_byte_values(self):
        """Test compression with all possible byte values."""
        data = bytes(range(256))
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

    def test_long_matches(self):
        """Test compression with long repeated sequences."""
        # Test sequences longer than 8 bytes (triggers long match encoding)
        data = b"ABCDEFGHIJKLMNOP" * 100  # 16-byte pattern repeated
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data
        # Should achieve excellent compression
        assert len(compressed) < len(data) // 4

    def test_mixed_patterns(self):
        """Test compression with mixed literal and match patterns."""
        # Mix of literals and repeating patterns
        data = (
            b"unique_prefix_"
            + b"repeat" * 50
            + b"_unique_suffix_"
            + b"another_repeat" * 30
        )
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

    def test_edge_case_match_lengths(self):
        """Test edge cases around match length boundaries."""
        # Test exactly 3-byte matches (minimum match length)
        data = b"ABC" + b"XYZ" * 100 + b"ABC"  # Should find 3-byte match
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

        # Test 8-byte matches (boundary between short and long matches)
        data = b"12345678" + b"ABCDEFGH" * 50 + b"12345678"
        compressed = compress(data, level=1)
        decompressed = decompress(compressed)
        assert decompressed == data

    def test_compression_roundtrip_consistency(self):
        """Test that multiple compression/decompression cycles are consistent."""
        data = b"Test data for consistency check with some repeated content. " * 20

        # Compress and decompress multiple times
        result = data
        for _ in range(5):
            compressed = compress(result, level=1)
            result = decompress(compressed)

        assert result == data

    def test_error_conditions(self):
        """Test various error conditions."""
        # Test invalid input types
        with pytest.raises(ValueError, match="Input must be bytes"):
            compress("not bytes", level=1)  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="Input must be bytes"):
            decompress("not bytes")  # type: ignore[arg-type]

        # Test invalid compression level
        with pytest.raises(ValueError, match="Compression level must be 1 or 2"):
            compress(b"test", level=3)

        with pytest.raises(ValueError, match="Compression level must be 1 or 2"):
            compress(b"test", level=0)

        # Test decompression with invalid header
        with pytest.raises(ValueError, match="No headerlen present"):
            decompress(b"abc")  # Less than 4 bytes

        # Test decompression with bad header length
        bad_header = struct.pack("<I", 1000000) + b"x"  # Claims 1MB but only has 1 byte
        with pytest.raises(ValueError, match="Bad headerlen"):
            decompress(bad_header)
