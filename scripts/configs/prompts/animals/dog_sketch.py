# prompts/dog_sketch.py
# 极简狗狗线稿 / 忠诚可爱风格

STYLE = {
    "dog_sketch": {
        "folder": "狗狗线稿",
        "strength": 0.35,
        
        # ==================== 主体 (10种) ====================
        "subjects": [
            "minimalist pencil sketch of a loyal dog, elegant contour lines, playful ears, curved tail, black and white lineart, pure white background, expressive form",
            "traditional Chinese dog lineart, sitting patiently, attentive gaze, wagging tail, minimalist ink brush style, simple raw sketch, clean white page",
            "classic dog pencil sketch, running dog, powerful leg muscles, flowing ears, rough draft, pure white paper texture, energetic composition",
            "dog in a playful bow pose, front legs down, tail up, dynamic movement, traditional baimiao line drawing, high contrast pencil strokes, centered composition, white background",
            "close-up of a dog's head, loyal eyes, floppy ears, prominent nose, uncolored minimalist ink sketch, black and white, white background",
            "simple outline of a standing dog, minimal ink strokes, elegant and sturdy silhouette, few bold lines, clean white background, loyal animal form",
            "classical dog illustration, traditional white sketch, walking proudly, detailed paw structure, meticulous black lineart, white paper, minimalist design",
            "loose pencil gesture of a dog, quick contour lines, happy expression, traditional art draft, uncolored, white background, high contrast lines",
            "sleeping dog curled up, cozy round shape, peaceful atmosphere, rough pencil study, white background, minimalist contour drawing",
            "dog sitting and looking back over shoulder, expressive contour lines, raw artistic draft, pure white background, simple and clean aesthetic"
        ],
        
        # ==================== 风格 (4种) ====================
        "styles": [
            "traditional Chinese baimiao lineart, fine ink brush strokes, minimalist black and white, raw draft style",
            "ancient painting sketch, elegant contour lines, simple shading, white background, artistic pencil draft",
            "ink wash style line drawing, traditional animal illustration, uncolored, high contrast black lines",
            "minimalist pencil sketch, rough strokes, pure white background, simple aesthetic"
        ],
        
        # ==================== 情绪 (5种) ====================
        "moods": [
            "loyal, friendly, joyful, playful",
            "energetic, spirited, lively, happy",
            "artistic, raw, minimalist, traditional",
            "peaceful, calm, devoted, sincere",
            "clean, timeless, simple, heartwarming"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}