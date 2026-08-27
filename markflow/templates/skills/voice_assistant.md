# voice_assistant

## 描述
语音合成（TTS）和语音识别（STT）助手

## 目的
提供文字转语音和语音转文字能力，支持多种语音类型

## 输入
- action: string: 操作类型 (tts/stt/list_voices) (必填)
- text: string: 要合成的文本 (tts 操作需要)
- audio_file: string: 要识别的音频文件路径 (stt 操作需要)
- voice: string: 语音类型 (zh-CN-XiaoxiaoNeural/zh-CN-YunxiNeural/en-US-JennyNeural)，默认 zh-CN-XiaoxiaoNeural
- speed: float: 语速 0.5-2.0，默认 1.0
- pitch: string: 音调 (default/high/low)，默认 default
- output_file: string: 输出文件路径，默认 ./output/audio_{timestamp}.mp3
- language: string: 识别语言 (zh-CN/en-US)，默认 zh-CN
- sample_rate: integer: 采样率，默认 16000
- silence_threshold: float: 静音检测阈值，默认 1.0

## 输出
- audio_path: 合成的音频路径 (tts)
- transcript: 识别的文本内容 (stt)
- duration: 音频时长(秒)
- voices: 可用语音列表 (list_voices)
- processing_time: 处理耗时

## 步骤
1. 验证输入参数
2. 执行对应操作 (tts/stt/list_voices)
3. 返回处理结果

## 依赖
- edge-tts
- openai-whisper
- pydub
- sounddevice (可选，用于录音)
- numpy
- scipy

## 示例
```python
assistant = VoiceAssistant()

# 文字转语音
result = assistant.execute(
    action="tts",
    text="你好，欢迎使用语音助手",
    voice="zh-CN-XiaoxiaoNeural",
    speed=1.2
)
print(f"音频已保存: {result['audio_path']}")

# 语音转文字
result = assistant.execute(
    action="stt",
    audio_file="./audio.mp3"
)
print(f"识别结果: {result['transcript']}")

# 列出可用语音
result = assistant.execute(action="list_voices")
for voice in result['voices']:
    print(f"{voice['name']} ({voice['locale']})")
```