# prompts/anime_greyscale_portrait.py
# 高级灰阶动漫半身像（强化安全、多表情、多季节）

STYLE = {
    "anime_greyscale_portrait": {
        "folder": "灰阶半身动漫",
        "strength": 0.35,
        
        # ==================== 主体 (12种不同变化，安全适配版) ====================
        "subjects": [
            # --- 微风与飘发（最安全，图2/图5风格）---
            "masterpiece, high quality anime portrait, bust shot, beautiful girl with long flowing hair blowing in the wind, wearing a high-neck soft white sweater, soft neutral expression, looking directly at viewer, refined monochrome grey tones, soft studio lighting, blurred outdoor park background, fully clothed, modest neckline, 8k",
            
            # --- 神秘与香氛（图4风格）---
            "stunning greyscale anime illustration, half-body shot of a girl holding a small smoldering incense stick, wispy smoke curling, gentle mysterious look, wearing a casual t-shirt, soft charcoal shading, blurred dark room background, cinematic lighting, fully clothed, safe content",
            
            # --- 秋日飘叶（秋季专属）---
            "elegant monochrome anime portrait, young woman with side-swept long hair, wearing a neat autumn coat, holding a falling leaf, calm and focused gaze, soft natural grey shading, blurred autumn street background, falling leaves, high definition, fully clothed",
            
            # --- 手拿咖啡（生活感）---
            "beautiful grey-scale anime rendering, half-body shot, girl with twin-tails hairstyle, wearing a winter sweater, holding a warm coffee cup, playful calm expression, soft natural sunlight, blurred cafe interior background, fully clothed",
            
            # --- 仰望天空（唯美意境）---
            "high-end anime portrait, monochromatic artwork, girl with long straight hair and bangs, wearing a hoodie, looking up at the sky, dreamy and peaceful expression, soft blurred cloud background, artistic grey tone illustration, modest outfit, 8k",
            
            # --- 看书的静谧（图1宁静感）---
            "breathtaking greyscale anime art, half-body portrait, girl with ponytail hairstyle, wearing a stylish high-collar jacket, reading a book, gentle and focused gaze, blurred library window background, soft atmospheric lighting, fully clothed",
            
            # --- 手持花朵（清新文艺）---
            "masterpiece anime monochrome painting, bust shot, girl with braided hair, wearing a white blouse, gentle and kind smile, holding a small flower, blurred garden background, elegant charcoal grey tones, modest neckline, safe image",
            
            # --- 回眸一笑（动态互动）---
            "highly detailed greyscale anime illustration, half-body shot, girl with long wavy hair, wearing an elegant high-collar dress, graceful pose, looking back over her shoulder with a gentle smile, blurred museum hall background, refined soft lighting, fully clothed",
            
            # --- 冬天哈气（冷暖对比）---
            "artistic monochrome anime portrait, young girl with long hair, wearing a thick winter scarf and coat, breathing out a puff of white air in the cold, energetic and cheerful expression, blurred snowy background, detailed grey shading, safe winter outfit",
            
            # --- 发呆的午后（慵懒风）---
            "stunning greyscale digital painting, half-body anime girl, loose fluffy hair, wearing a comfy vest and shirt, relaxed and calm expression, holding a pen, blurred cozy room background, warm atmospheric lighting, fully clothed",
            
            # --- 侧面眺望（原图经典侧脸）---
            "elegant grey-tone anime art, bust shot, girl with layered hair and hair clips, wearing a lace top, looking out to the side, mysterious gentle smile, soft focus, blurred nature scenery background, high contrast soft shadow, masterpiece, modest neckline",
            
            # --- 撑伞的人（雨天氛围）---
            "high-quality greyscale anime portrait, half-body shot, girl with long hair tied in a low ponytail, wearing a coat, holding an umbrella, raindrops falling, cool and quiet look, blurred rainy city background, sophisticated lighting, fully clothed"
        ],
        
        # ==================== 风格 ====================
        "styles": [
            "monochromatic greyscale, anime style, soft shading, cinematic lighting, blurred background, masterpiece, fully clothed"
        ],
        
        # ==================== 情绪 ====================
        "moods": [
            "elegant, refined, calm, beautiful"
        ],
        
        "content_texts": [] 
    }
}