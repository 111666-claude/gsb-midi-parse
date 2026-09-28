"""标准 MIDI 文件解析。"""

from .midi import MidiError, parse, read_varlen

__all__ = ["MidiError", "parse", "read_varlen"]
