# prompts/autumn_anime_portrait.py
# 秋日/暖阳动漫少女半身像（高质量氛围插画）

STYLE = {
    "autumn_anime_portrait": {
        "folder": "氛围感动漫少女",
        "strength": 0.35,
        
        # ==================== 主体 (12种不同场景与穿搭) ====================
        "subjects": [
            # --- 原图复刻：秋日落叶 + 白衣 ---
            "masterpiece, high quality anime illustration, half-body portrait of a beautiful girl in side profile view, eyes gently closed, long dark hair blowing heavily in the wind, wearing a soft white knit sweater, beautiful golden autumn leaves falling around her, soft warm sunset backlight, lens flare, blurred autumn street background, cinematic lighting, 8k",
            
            # --- 变化1：拿着红枫叶 ---
            "anime art, beautiful girl, half-body shot, looking gently at a red maple leaf held in her hand, long hair flowing, white loose sweater, warm autumn sunlight shining on her face, blurred park background with golden trees, soft focus, masterpiece, 8k",
            
            # --- 变化2：樱花雨 + 风衣 ---
            "stunning anime illustration, half-body portrait of a girl, turned slightly to the side, wearing a beige trench coat, long hair blowing, gentle smile, pink cherry blossoms falling in the wind, soft spring afternoon light, blurred outdoor path background, exquisite art style",
            
            # --- 变化3：下雨天 + 透明雨伞 ---
            "cinematic anime art, half-body shot of a girl holding a transparent umbrella, wearing a cream-colored cardigan, rain droplets sliding down the umbrella, misty rain, gentle expression looking up, blurred city street background, moody and soft lighting, masterpiece",
            
            # --- 变化4：雪景 + 围巾 ---
            "breathtaking anime illustration, half-body portrait of a girl in a snowy scene, wearing a thick white coat and red scarf, breath visible in the cold air, looking at the camera with a warm smile, blurred winter landscape, soft soft snowflakes, cinematic lighting, 8k",
            
            # --- 变化5：逆光 + 微卷发 + 圆领毛衣 ---
            "high quality anime art, half-body shot of a girl with medium wavy hair, wearing a light grey cozy sweater, her hair glowing in the strong golden sunset backlight, relaxed calm expression, blurred beach background at sunset, warm sunny atmosphere",
            
            # --- 变化6：双马尾 + 运动服 ---
            "masterpiece anime illustration, half-body portrait of a cheerful girl, twin-tail hairstyle, wearing a white sports hoodie, looking directly at the viewer with a bright energetic smile, sunny outdoor track background, vibrant natural sunlight, 8k",
            
            # --- 变化7：低头看书 + 眼镜 + 针织衫 ---
            "elegant anime art, half-body shot of a girl with glasses, wearing a soft knit sweater, long hair falling forward, looking down quietly reading a book, peaceful expression, autumn leaves blowing past, blurred library or garden background, soft warm light",
            
            # --- 变化8：海边漫步 + 白色连衣裙 ---
            "beautiful anime illustration, half-body shot of a girl with short bob hair, wearing a white summer dress, walking along the beach, sea breeze blowing her hair, gentle smile, clear blue sky, bright sunny lighting, blurred ocean background, 8k",
            
            # --- 变化9：靠着路灯 + 皮夹克 ---
            "cinematic anime portrait, half-body shot of a cool girl, short hair, wearing a leather jacket, leaning against a vintage street lamp, looking up at the streetlights, night scene with warm orange light, blurred city street background, atmospheric lighting",
            
            # --- 变化10：向日葵田 + 草帽 ---
            "masterpiece anime illustration, half-body portrait of a girl in a sunflower field, wearing a straw hat, long wavy hair, holding a sunflower, bright sunny day, gorgeous golden sunlight, blurred nature background, vibrant colors, 8k",
            
            # --- 变化11：侧脸仰头 + 高领毛衣 ---
            "high quality anime art, half-body shot of a girl in side profile, looking up at the sky, wearing an oversized white turtleneck sweater, long hair blowing beautifully in the wind, autumn leaves falling, warm soft afternoon glow, masterpiece",
            
            # --- 变化12：雨天 + 回眸 + 风衣 ---
            "cinematic anime illustration, half-body shot of a girl walking in the rain, turning her head to look back over her shoulder, hair wet and flowing, wearing a trench coat, gentle expression, blurred street with rain puddles reflecting light, moody atmosphere, masterpiece"
        ],
        
        # ==================== 风格 (保证插画质感) ====================
        "styles": [
            "anime illustration, cinematic soft lighting, warm color palette, blurred background, highly detailed, masterpiece"
        ],
        
        # ==================== 情绪 ====================
        "moods": [
            "peaceful, romantic, warm, cozy"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}