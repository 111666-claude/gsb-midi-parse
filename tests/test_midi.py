import unittest

from midiparse.midi import MidiError, parse, read_varlen


class VarlenTest(unittest.TestCase):
    def test_single_byte(self):
        self.assertEqual(read_varlen(bytes([0x60]), 0), (0x60, 1))

    def test_two_bytes(self):
        self.assertEqual(read_varlen(bytes([0x81, 0x48]), 0), (200, 2))

    def test_truncated(self):
        with self.assertRaises(MidiError):
            read_varlen(bytes([0x81]), 0)


class ParseTest(unittest.TestCase):
    def build(self, track):
        header = b"MThd" + (6).to_bytes(4, "big") + bytes([0, 0, 0, 1, 0x01, 0xE0])
        return header + b"MTrk" + len(track).to_bytes(4, "big") + track

    def test_simple_note(self):
        track = bytes([0x00, 0x90, 60, 64, 0x00, 0xFF, 0x2F, 0x00])
        parsed = parse(self.build(track))
        self.assertEqual(parsed["format"], 0)
        self.assertEqual(parsed["division"], 480)
        self.assertEqual(parsed["tracks"][0][0]["type"], "note_on")
        self.assertEqual(parsed["tracks"][0][0]["tick"], 0)

    def test_tempo_meta(self):
        track = bytes([0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20, 0x00, 0xFF, 0x2F, 0x00])
        parsed = parse(self.build(track))
        self.assertEqual(parsed["tracks"][0][0]["type"], "meta")
        self.assertEqual(parsed["tracks"][0][0]["code"], 0x51)

    def test_program_change_reads_one_byte(self):
        track = bytes([0x00, 0xC0, 0x05, 0x00, 0xFF, 0x2F, 0x00])
        parsed = parse(self.build(track))
        self.assertEqual(parsed["tracks"][0][0]["type"], "program")

    def test_not_a_midi_file(self):
        with self.assertRaises(MidiError):
            parse(b"NOPE" + bytes(20))


if __name__ == "__main__":
    unittest.main()
