# prompts/flower_sketch.py
# 极简铅笔花卉线稿 / 植物简笔画

STYLE = {
    "flower_sketch": {
        "folder": "极简花朵线稿",
        "strength": 0.35,
        
        # ==================== 主体 (10种) ====================
        "subjects": [
            "minimalist pencil sketch of a blooming rose, few flowing contour lines, elegant floral gesture, uncolored, pure white background, simple lineart",
            "single flower gesture sketch, minimalist line drawing, light pencil strokes, artistic botanical study, clean white page, raw hand-drawn style",
            "loose floral sketch of a lily, graceful curved petals, quick contour lines, unfinished minimalist art, abstract botanical illustration, white background",
            "simplified flower head drawing, just a few continuous lines, elegant floral shape, minimalist lineart, pencil on paper, minimalist composition",
            "minimalist pencil doodle of a sunflower, simple structural lines, loose strokes, botanical art draft, pure white empty background",
            "abstract floral lineart, few strokes conveying flower essence, minimalist contour drawing, rough pencil draft, artistic botanical sketch",
            "elegant minimal flower sketch, graceful stem and petals, simple gesture lines, white background, fine pencil artwork, uncolored",
            "single blooming flower, quick pencil gesture, minimalist artistic expression, clean lines, unpolished rough draft, pure white page",
            "minimalist floral study, just a few elegant pencil strokes, abstract flower form, artistic raw sketch, white background, no extra details",
            "simple flower silhouette, continuous line drawing, elegant floral design, minimalist hand-drawn aesthetic, white paper, uncolored"
        ],
        
        # ==================== 风格 (3种) ====================
        "styles": [
            "minimalist lineart, few flowing pencil strokes, clean white background, simple botanical sketch",
            "continuous contour line drawing, minimalist gesture, raw pencil draft, high contrast black and white",
            "quick pencil gesture, abstract floral form, loose artistic strokes, uncolored minimalist illustration"
        ],
        
        # ==================== 情绪 (4种) ====================
        "moods": [
            "elegant, delicate, serene, calm",
            "minimalist, clean, artistic, expressive",
            "graceful, flowing, organic, natural",
            "raw, unpolished, creative, abstract"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}