# pyfastlz-native

This is a native python3 implementation of the FastLZ algorithm (more info in [Lempel-Ziv 77 algorithm](https://en.wikipedia.org/wiki/LZ77_and_LZ78#LZ77)).

Currently it only implements decompression.

## Usage

```
import fastlz_native

comp_data = bytes(raw_data)
decompressed = fastlz_native.fastlz_decompress(comp_data)
```

## Expected format

This implementation expects the decompressed size in bytes in the first uint32_t chunk.
