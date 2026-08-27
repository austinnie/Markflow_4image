# prompts/dragon_sketch.py
# 长卷盘龙线稿（横向吐珠构图）

STYLE = {
    "dragon_sketch": {
        "folder": "长卷盘龙线稿",
        "strength": 0.35,
        
        # ==================== 主体 (6种横版构图) ====================
        "subjects": [
            "highly detailed black and white lineart illustration, traditional Chinese dragon in horizontal panoramic composition, dragon head on the left facing right, exhaling swirling flames and holding a fire pearl, long serpentine body coiled in figure-eight shape, four sharp claws, stylized ocean waves and traditional cloud patterns at the bottom, pure white background, fine ink line drawing, clean manga tattoo style",
            "horizontal black ink drawing of a coiled Eastern dragon, head on the left, body winding through thick stylized clouds, classic 'dragon playing with a pearl' motif, detailed scales and flowing mane, white background, intricate line work",
            "baimiao lineart of a Chinese dragon in a wide landscape layout, head emitting fire and smoke, serpentine body forming circular loops, surrounded by intricate wind and cloud swirls, white paper, masterwork black and white illustration",
            "long horizontal sketch of a mythical Chinese Loong, head raised in a roar, claw grasping a flaming orb, body twisting through waves and clouds, high contrast pure black lines on white, traditional scroll painting style draft",
            "horizontal dragon illustration, Chinese dragon with deer horns and whiskers, body looping in a dynamic S-shape, four visible claws, background filled with dense stylized cloud waves, pure lineart, white background",
            "traditional black ink dragon scroll, horizontal composition, dragon breathing fire and chasing a pearl, intertwined with classic cloud scrolls, fine linework, high detail, white empty background"
        ],
        
        # ==================== 风格 (锁定) ====================
        "styles": [
            "intricate black and white lineart, pure white background, baimiao style, high contrast"
        ],
        
        # ==================== 情绪 ====================
        "moods": [
            "majestic, dynamic, flowing, traditional"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}