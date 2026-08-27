# tools/prompts_new/anime_figures.py
# 动漫手办/模型/雕塑 生成风格提示词库

STYLE = {
    "anime_figure_girl": {
        "folder": "动漫手办_女孩",
        "strength": 0.35,
        "subjects": [
            # 通用展示底座造型
            "high quality 3D figure of an anime girl, sitting on a white cylindrical pedestal, elegant posture, simple grey studio background, macro photography, collectible PVC statue",
            
            # 经典兔女郎
            "detailed anime bunny girl figure, long hair, glossy black bunny suit, high heels, standing dynamic pose, studio lighting, pure white background",
            
            # 飘逸长发 + 旗袍造型
            "anime collectible statue of a girl, long flowing hair, wearing a purple slit cheongsam, pointing finger, expressive face, painted resin, glossy finish",
            
            # 大翅膀/天使造型
            "beautiful 3D figure of an angel girl, white translucent dress, large white feathered wings, standing gracefully, soft grey background, premium collectible",
            
            # 双马尾/坐姿
            "cute anime figurine, girl with twin tails, casual dress, sitting pose, relaxed expression, smooth PVC texture, neutral photography background",
            
            # 黑色哥特/恶魔风格
            "dark fantasy anime figure, girl with devil horns, black outfit, small bat wings, elegant dark atmosphere, black backdrop, dramatic studio light",
            
            # 白毛/红眼特色造型
            "high end anime figure of a white-haired girl with red eyes, wearing a dark dress and oversized beige jacket, sitting on a pedestal, cross-legged, choker necklace, geometric halo",
            
            # 浅色系/居家风
            "sweet anime girl figurine, light blue hair, lavender dress, white thigh-high socks, sitting relaxed, soft pastel colors, clean white background"
        ],
        "styles": [
            "high definition resin figure, glossy painted finish, macro studio photography",
            "3D collectible statue, sculpted details, product shot, premium lighting",
            "anime figurine photography, soft shadows, realistic material textures"
        ],
        "moods": [
            "elegant, sophisticated, premium",
            "cute, vibrant, high-end",
            "mysterious, dark, collectible"
        ],
        "content_texts": []
    }
}