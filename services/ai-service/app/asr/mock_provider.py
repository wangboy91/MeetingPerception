from app.asr.base import AsrProvider, AsrResult, SpeechSegment

MIC_LINES = [
    "我检测到麦克风语音，先生成一条模拟实时转写。",
    "这个需求需要确认影响范围、回滚方案和验收标准。",
    "我们先把风险点和下一步负责人记录下来。",
]

SYSTEM_LINES = [
    "系统输出通道已预留，后续接入 Windows loopback。",
    "系统输出音频会被标记为 Remote。",
]


class MockAsrProvider(AsrProvider):
    async def transcribe_segment(self, segment: SpeechSegment) -> AsrResult:
        lines = MIC_LINES if segment.track == "mic" else SYSTEM_LINES
        text = lines[segment.frames % len(lines)]
        return AsrResult(
            text=text,
            language="zh",
            start_ms=segment.start_ms,
            end_ms=segment.end_ms,
            confidence=0.82,
            is_final=True,
        )
