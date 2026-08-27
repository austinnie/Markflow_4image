# MusicPlayer

## 描述
AI 智能歌单生成和音乐管理

## 输入
- action: string: 操作 (play/search/playlist/lyrics) (必填)
- query: string: 搜索关键词 (可选)
- playlist_name: string: 播放列表名 (可选)
- mood: string: 情绪 (happy/sad/relax/energetic) (可选)

## 输出
- tracks: 歌曲列表
- playlist: 生成的播放列表
- lyrics: 歌词内容

## 依赖
- spotipy
- yt-dlp
- mutagen
- pygame

## 状态
待实现