"""标准 MIDI 文件（SMF）解析，只用标准库。

缺陷：变长量最多读 3 字节（更长的 delta 被截断），running status 也不支持。
"""

HEADER = b"MThd"
TRACK = b"MTrk"


class MidiError(ValueError):
    """文件不合法。缺陷：不带偏移。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def read_varlen(data, offset):
    """读变长量。缺陷：最多读 3 字节，超过就被截断。"""
    value = 0
    for _ in range(3):
        if offset >= len(data):
            raise MidiError("变长量被截断")
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, offset
    return value, offset


def _read_chunk(data, offset):
    if offset + 8 > len(data):
        raise MidiError("分块头不完整")
    kind = data[offset:offset + 4]
    size = int.from_bytes(data[offset + 4:offset + 8], "big")
    start = offset + 8
    if start + size > len(data):
        raise MidiError("分块长度超出文件")
    return kind, data[start:start + size]


def parse(data):
    """解析 SMF，返回 (格式, 每轨事件列表)。缺陷：不支持 running status。"""
    kind, header = _read_chunk(data, 0)
    if kind != HEADER or len(header) < 6:
        raise MidiError("不是标准 MIDI 文件")
    midi_format = int.from_bytes(header[0:2], "big")
    tracks = int.from_bytes(header[2:4], "big")
    division = int.from_bytes(header[4:6], "big")
    offset = 8 + len(header)
    result = []
    for _ in range(tracks):
        kind, body = _read_chunk(data, offset)
        if kind != TRACK:
            raise MidiError("期望 MTrk 分块")
        offset += 8 + len(body)
        result.append(_parse_track(body))
    return {"format": midi_format, "division": division, "tracks": result}


def _parse_track(body):
    events = []
    offset = 0
    clock = 0
    status = 0
    while offset < len(body):
        delta, offset = read_varlen(body, offset)
        clock += delta
        if offset >= len(body):
            raise MidiError("事件被截断")
        byte = body[offset]
        if byte & 0x80:
            status = byte
            offset += 1
        else:
            # 缺陷：running status（省略 status 字节）直接报错
            raise MidiError("事件缺少 status 字节")
        kind = status & 0xF0
        if status == 0xFF:
            if offset >= len(body):
                raise MidiError("meta 事件被截断")
            meta = body[offset]
            offset += 1
            size, offset = read_varlen(body, offset)
            payload = body[offset:offset + size]
            if len(payload) != size:
                raise MidiError("meta 载荷被截断")
            offset += size
            events.append({"tick": clock, "delta": delta, "type": "meta", "code": meta, "data": payload.hex()})
            if meta == 0x2F:
                break
        elif kind in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            if offset + 2 > len(body):
                raise MidiError("事件参数被截断")
            first, second = body[offset], body[offset + 1]
            offset += 2
            name = {0x80: "note_off", 0x90: "note_on", 0xA0: "aftertouch",
                    0xB0: "control", 0xE0: "pitch"}[kind]
            events.append({"tick": clock, "delta": delta, "type": name,
                           "channel": status & 0x0F, "data": "%02x%02x" % (first, second)})
        elif kind in (0xC0, 0xD0):
            if offset + 1 > len(body):
                raise MidiError("事件参数被截断")
            value = body[offset]
            offset += 1
            name = "program" if kind == 0xC0 else "pressure"
            events.append({"tick": clock, "delta": delta, "type": name,
                           "channel": status & 0x0F, "data": "%02x" % value})
        else:
            raise MidiError("不认识的状态字节：%02x" % status)
    return events
