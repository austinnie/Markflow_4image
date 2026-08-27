# prompts/bird_sketch.py
# 极简铅笔鸟类线稿 / 动物简笔画

STYLE = {
    "bird_sketch": {
        "folder": "极简飞鸟线稿",
        "strength": 0.35,
        
        # ==================== 主体 (10种) ====================
        "subjects": [
            "minimalist pencil sketch of a flying bird, few flowing wing lines, elegant gesture, simple contour drawing, uncolored, pure white background",
            "simple bird silhouette, continuous line drawing, minimalist animal sketch, graceful form, quick pencil stroke, white page, raw art style",
            "loose gesture sketch of a perched bird, minimal contour lines, light pencil strokes, abstract animal form, clean white background, unfinished art",
            "elegant bird in flight, minimal lineart, just a few dynamic strokes, artistic animal contour, unpolished pencil draft, pure white page",
            "simplified bird drawing, minimal pencil lines capturing essence, quick gesture sketch, rough draft, minimalist composition, white empty background",
            "abstract bird lineart, few flowing strokes, minimalist animal illustration, quick hand-drawn gesture, black and white, white background",
            "minimalist pencil sketch of a bird's wing, elegant curve lines, simple structure study, artistic raw draft, white paper, uncolored",
            "graceful bird silhouette, minimal contour lines, light gesture drawing, unpolished rough sketch, abstract animal art, pure white background",
            "quick pencil gesture of a bird, minimalist strokes, simple animal form, fluid lines, raw artistic draft, white background",
            "simple bird sketch, minimalist lineart, flowing gesture lines, elegant form study, clean white background, uncolored raw pencil style"
        ],
        
        # ==================== 风格 (3种) ====================
        "styles": [
            "minimalist lineart, few flowing pencil strokes, clean white background, simple animal sketch",
            "continuous contour line drawing, minimalist gesture, raw pencil draft, high contrast black and white",
            "quick pencil gesture, abstract animal form, loose artistic strokes, uncolored minimalist illustration"
        ],
        
        # ==================== 情绪 (4种) ====================
        "moods": [
            "elegant, graceful, free, serene",
            "minimalist, clean, artistic, expressive",
            "playful, natural, organic, flowing",
            "raw, unpolished, creative, abstract"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}