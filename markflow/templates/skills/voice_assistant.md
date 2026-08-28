# voice_assistant

> 语音合成（TTS）和语音识别（STT）助手

## 技能描述

提供文字转语音和语音转文字能力，支持多种语音类型

## 核心功能

1. 文字转语音 - 将文本转换为语音音频
2. 语音转文字 - 将音频文件转换为文本
3. 多语音支持 - 支持多种语音类型和语速调节
4. 语音列表 - 列出所有可用语音

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| action | string | 是 | - | 操作类型 (tts/stt/list_voices) |
| text | string | 否 | - | 要合成的文本 (tts 操作需要) |
| audio_file | string | 否 | - | 要识别的音频文件路径 (stt 操作需要) |
| voice | string | 否 | zh-CN-XiaoxiaoNeural | 语音类型 |
| speed | float | 否 | 1.0 | 语速，范围 0.5-2.0 |
| pitch | string | 否 | default | 音调 (default/high/low) |
| output_file | string | 否 | - | 输出文件路径 |
| language | string | 否 | zh-CN | 识别语言 (zh-CN/en-US) |
| sample_rate | integer | 否 | 16000 | 采样率 |
| silence_threshold | float | 否 | 1.0 | 静音检测阈值 |

## 输出

| 字段 | 说明 |
|------|------|
| audio_path | 合成的音频路径 (tts) |
| transcript | 识别的文本内容 (stt) |
| duration | 音频时长(秒) |
| voices | 可用语音列表 (list_voices) |
| processing_time | 处理耗时(秒) |

## 步骤

1. 验证输入参数
2. 执行对应操作 (tts/stt/list_voices)
3. 返回处理结果

## 依赖

- edge-tts
- openai-whisper
- pydub
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
```

## 使用示例
```bash
python -m markflow.cli.commands execute voice_assistant action="tts" text="你好世界" voice="zh-CN-XiaoxiaoNeural"

python -m markflow.cli.commands execute voice_assistant action="list_voices"
```
