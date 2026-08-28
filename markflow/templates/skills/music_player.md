# music_player

> AI 智能歌单生成和音乐管理

## 技能描述

AI 驱动的音乐播放器，支持智能歌单生成、音乐搜索、歌词显示和本地播放

## 核心功能

1. 音乐搜索 - 在线搜索音乐
2. 播放控制 - 播放、暂停、停止、上一首、下一首
3. 智能歌单 - 根据情绪生成播放列表
4. 歌词显示 - 显示当前歌曲歌词
5. 音量控制 - 调节播放音量
6. 歌单保存 - 保存播放列表到本地
7. 本地扫描 - 扫描本地音乐文件

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| action | string | 是 | - | 操作 (play/search/playlist/lyrics/info/scan) |
| query | string | 否 | - | 搜索关键词 |
| playlist_name | string | 否 | - | 播放列表名 |
| mood | string | 否 | happy | 情绪 (happy/sad/relax/energetic) |
| save | boolean | 否 | false | 是否保存歌单 |

## 输出

| 字段 | 说明 |
|------|------|
| tracks | 歌曲列表 |
| playlist | 生成的播放列表 |
| lyrics | 歌词内容 |
| status | 播放状态 |

## 步骤

1. 验证输入参数
2. 根据 action 类型执行对应操作
3. 返回处理结果

## 依赖

- spotipy
- yt-dlp
- mutagen
- pygame

## 示例

```python
player = MusicPlayer()

# 搜索并播放
result = player.execute(
    action="play",
    query="周杰伦 稻香"
)

# 生成开心歌单
result = player.execute(
    action="playlist",
    mood="happy",
    count=5
)
```

## 使用示例
```bash
python -m markflow.cli.commands execute music_player action="play" query="周杰伦 稻香"

python -m markflow.cli.commands execute music_player action="playlist" mood="happy" count=5

python -m markflow.cli.commands execute music_player action="info"
```