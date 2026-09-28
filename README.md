# midi-parse

标准 MIDI 文件（SMF）解析：变长量、running status、meta 事件与绝对时间，只用 Python 标准库。

```
python3 -m midiparse.cli --sample running --events
python3 -m midiparse.cli --sample wide --events
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **变长量最多 4 字节**：每字节低 7 位有效，最高位表示「还有后续」，最多 4 字节（28 位）。
  `--sample wide --events` 里的事件 delta 是 `0x81 0x80 0x80 0x00`，按口径是 2097152，
  现在只读 3 字节，给 2097152 之外的错值。
- **支持 running status**：通道事件省略 status 字节时沿用上一次的 status。
  `--sample running --events` 按口径要打印两个 note_on 事件（第二个 velocity 0 表示放音结束），
  现在直接报「事件缺少 status 字节」。
- meta 事件：`FF <类型> <变长长度> <载荷>`；`End of Track`（0x2F）之后停止读该轨；类型 0x51（tempo）
  要能把 3 字节的微秒/四分音符解出来。
- 通道事件长度：0x8n/0x9n/0xAn/0xBn/0xEn 两个参数，0xCn/0xDn 一个参数，参数都必须 < 0x80。
- 不变量：所有事件的 tick 单调不减，且等于累计 delta 之和；每轨最后一个事件是 End of Track；
  同一份文件重复解析结果相同；截断的 delta、载荷、事件参数都要报错。
- 规模：10 MB 的 MIDI 文件单遍解析，内存 O(事件数)，不许把整个轨道复制成多层结构。

## 现在的行为

- `read_varlen` 的循环写死 3 次：4 字节的变长量会被截断成错值。
- `_parse_track` 遇到 status 字节小于 0x80 直接报错，running status 完全没实现。
- meta 事件与 tick 累计的逻辑是对的（所以 `--sample tempo` 能跑通）。

## 计划新增的能力

```
--sample 名称    running / wide / tempo 三个内置样本
--events         打印轨道事件
--file 文件      解析真实文件
```

## 输出

```
format=0 division=480 tracks=1
event=0 tick=0 delta=0 type=note_on data=3c40
event=1 tick=96 delta=96 type=note_on data=3c00
```

## 目录

```
midiparse/midi.py    解析
midiparse/cli.py     命令行入口 + 样本
tests/               unittest 用例
```
