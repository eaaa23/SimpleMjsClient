_keys = [0x84, 0x5e, 0x4e, 0x42, 0x39, 0xa2, 0x1f, 0x60, 0x1c]
_len_keys = len(_keys)


def decode(data: bytes):
    data = bytearray(data)
    for i in range(len(data)):
        u = (23 ^ len(data)) + 5 * i + _keys[i % _len_keys] & 255
        data[i] ^= u
    return bytes(data)
