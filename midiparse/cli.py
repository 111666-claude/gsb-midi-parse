"""命令行入口：解析内置样本并打印事件。"""

import argparse
import sys

from .midi import MidiError, parse


def _chunk(kind, body):
    return kind + len(body).to_bytes(4, "big") + body


def sample(name):
    """构造样本：running 用省略 status 的第二个音符，wide 用 4 字节变长量。"""
    if name == "running":
        track = bytes([0x00, 0x90, 60, 64,           # note on
                       0x60, 60, 0,                  # running status：省略 0x90
                       0x00, 0xFF, 0x2F, 0x00])
        return _chunk(b"MThd", bytes([0, 1, 0, 1, 0x01, 0xE0])) + _chunk(b"MTrk", track)
    if name == "wide":
        track = bytes([0x81, 0x80, 0x80, 0x00, 0xFF, 0x2F, 0x00])
        return _chunk(b"MThd", bytes([0, 1, 0, 1, 0x01, 0xE0])) + _chunk(b"MTrk", track)
    if name == "tempo":
        track = bytes([0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20,
                       0x00, 0x90, 62, 100,
                       0x81, 0x48, 0x80, 62, 64,
                       0x00, 0xFF, 0x2F, 0x00])
        return _chunk(b"MThd", bytes([0, 1, 0, 1, 0x01, 0xE0])) + _chunk(b"MTrk", track)
    raise MidiError("不认识的样本：%s" % name)


def build_parser():
    parser = argparse.ArgumentParser(prog="midi-parse", description="SMF 解析")
    parser.add_argument("--sample", help="running / wide / tempo")
    parser.add_argument("--events", action="store_true", help="打印事件")
    parser.add_argument("--file", help="解析真实文件")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.file:
            with open(args.file, "rb") as handle:
                data = handle.read()
        elif args.sample:
            data = sample(args.sample)
        else:
            print("错误：需要 --sample 或 --file", file=sys.stderr)
            return 2
        parsed = parse(data)
        print("format=%d division=%d tracks=%d" % (parsed["format"], parsed["division"],
                                                   len(parsed["tracks"])))
        if args.events:
            for index, event in enumerate(parsed["tracks"][0]):
                print("event=%d tick=%d delta=%d type=%s data=%s" % (
                    index, event["tick"], event["delta"], event["type"], event.get("data", "")))
    except (MidiError, OSError, ValueError) as error:
        print("错误：%s" % error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
