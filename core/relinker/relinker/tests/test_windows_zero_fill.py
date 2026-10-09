"""Store only the initialized bytes of each Windows section and let the loader zero-fill the rest."""

import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

from test_optional_plt import fixture

LOAD_RVA = 0x10000
ZERO_FILL = 0x1000000


def reading(address, memory_size=0x1000, extra_load=None):
    image = fixture()
    image[0x210:0x21B] = b"\x48\x8b\x05" + struct.pack("<i", address - 0x217) + b"\x83\xc0\x2a\xc3"
    struct.pack_into("<Q", image, 64 + 40, memory_size)
    if extra_load is not None:
        struct.pack_into("<H", image, 56, 3)
        struct.pack_into("<IIQQQQQQ", image, 176, 1, 4, *extra_load)
    return image


def sections(pe):
    header, = struct.unpack_from("<I", pe, 0x3C)
    count, = struct.unpack_from("<H", pe, header + 6)
    table = header + 24 + struct.unpack_from("<H", pe, header + 20)[0]
    result = {}
    for index in range(count):
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", pe, table + index * 40 + 8)
        result[rva] = (virtual_size, raw_size, raw_offset)
    return result


def convert(relinker, work, name, image):
    source = work / (name + ".elf")
    output = work / (name + ".exe")
    source.write_bytes(image)
    result = subprocess.run([str(relinker), "--skip-sce-module", "--windows", str(source), str(output)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0 and output.read_bytes()[:2] == b"MZ", (name, result.stdout, result.stderr)
    if os.name == "nt":
        executed = subprocess.run([str(output)], capture_output=True, text=True, timeout=20)
        assert executed.returncode == 42, (name, executed.returncode, executed.stdout, executed.stderr)
    return output.read_bytes()


def main():
    relinker = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="anyps5-windows-zero-fill-") as directory:
        work = Path(directory)

        pe = convert(relinker, work, "tail", reading(0x1000 + ZERO_FILL - 8, 0x1000 + ZERO_FILL))
        virtual_size, raw_size, _ = sections(pe)[LOAD_RVA]
        assert virtual_size >= 0x1000 + ZERO_FILL and raw_size <= 0x1000, (virtual_size, raw_size)
        assert len(pe) < ZERO_FILL, len(pe)

        pe = convert(relinker, work, "gap", reading(0x3FF8, extra_load=(0, 0x3000, 0x3000, 8, 0x1000, 0x1000)))
        layout = sections(pe)
        assert layout[LOAD_RVA + 0x1000] == (0x2000, 0, 0), layout
        virtual_size, raw_size, raw_offset = layout[LOAD_RVA + 0x3000]
        assert virtual_size == 0x1000 and 0 < raw_size < virtual_size and raw_offset != 0, layout
    print("Windows zero-fill tests passed")


if __name__ == "__main__":
    main()
