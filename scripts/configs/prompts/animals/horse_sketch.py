# prompts/horse_sketch.py
# 中国传统骏马线稿 / 极简奔腾风格

STYLE = {
    "horse_sketch": {
        "folder": "骏马线稿",
        "strength": 0.35,
        
        # ==================== 主体 (10种) ====================
        "subjects": [
            "traditional Chinese horse lineart, majestic galloping posture, dynamic flowing mane, powerful muscular legs, raw ink brush style, black and white illustration, pure white background, minimalist contour",
            "classic horse pencil sketch, beautiful equine form, flying tail, expressive eyes, rough draft, elegant simple lineart, white paper texture, minimalist composition",
            "horse face close-up, proud profile, flared nostrils, powerful neck, traditional baimiao line drawing, high contrast pencil strokes, centered composition, white background",
            "dynamic Chinese horse in full gallop, wind flowing through mane, powerful stride, raw graphite sketch, clean minimalist lines, empty white page, artistic raw draft",
            "rearing horse sketch, powerful stance, arched neck, intense movement, uncolored ink sketch, minimalist black and white, white background",
            "horse masterpiece sketch, detailed muscle definition, flowing tail, traditional baimiao technique, fine linework, white background, raw penciling style",
            "simple outline of a running horse, minimal ink strokes, elegant ancient art style, smooth curves, few bold lines, clean white background, powerful silhouette",
            "classical horse illustration, traditional Chinese white sketch, dynamic movement, detailed hooves and joints, meticulous black lineart, white paper, minimalist design",
            "loose pencil gesture of a horse, quick contour lines, majestic animal form, traditional Asian art draft, uncolored, white background, high contrast lines",
            "horse in a calm standing pose, traditional artistic expression, well-proportioned body, rough pencil study, white background, minimalist contour drawing"
        ],
        
        # ==================== 风格 (4种) ====================
        "styles": [
            "traditional Chinese baimiao lineart, fine ink brush strokes, minimalist black and white, raw draft style",
            "ancient Chinese painting sketch, elegant contour lines, simple shading, white background, artistic pencil draft",
            "ink wash style line drawing, traditional wild animal illustration, uncolored, high contrast black lines",
            "minimalist pencil sketch, traditional Chinese art, rough strokes, pure white background, simple aesthetic"
        ],
        
        # ==================== 情绪 (5种) ====================
        "moods": [
            "dynamic, powerful, free, galloping",
            "majestic, noble, spirited, untamed",
            "artistic, raw, elegant, traditional",
            "graceful, flowing, energetic, wild",
            "minimalist, clean, monumental, fearless"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}