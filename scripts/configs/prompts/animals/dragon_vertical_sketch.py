# prompts/dragon_vertical_sketch.py
# 竖版盘龙线稿（经典S型构图，适合做壁纸/竖排版）

STYLE = {
    "dragon_vertical_sketch": {
        "folder": "竖版盘龙线稿",
        "strength": 0.35,
        
        # ==================== 主体 (6种竖版构图) ====================
        "subjects": [
            "highly detailed black and white lineart illustration, traditional Chinese dragon in vertical composition, dragon head positioned at the top looking down, long serpentine body coiling vertically in an S-shape, four sharp claws, holding a flaming fire pearl at the bottom right, stylized cloud waves surrounding the body, pure white background, fine ink line drawing, clean manga tattoo style",
            "vertical black ink drawing of a coiled Eastern dragon, head at the top, body winding down through thick stylized clouds, classic 'dragon playing with a pearl' motif, detailed scales and flowing mane, white background, intricate line work",
            "baimiao lineart of a Chinese dragon in a tall vertical layout, head raised in a roar, serpentine body forming circular loops down the page, surrounded by intricate wind and cloud swirls, white paper, masterwork black and white illustration, vertical wallpaper aesthetic",
            "vertical sketch of a mythical Chinese Loong, coiled in a dynamic downward spiral, claw grasping a flaming orb at the bottom, body twisting through waves and clouds, high contrast pure black lines on white, traditional ink scroll style",
            "vertical dragon illustration, Chinese dragon with deer horns and whiskers, head positioned upper left, body looping in a powerful S-shape down the frame, four visible claws at different heights, background filled with dense stylized cloud waves, pure lineart, white background",
            "traditional black ink dragon scroll, vertical composition, dragon descending from the heavens, intertwined with classic cloud scrolls, fine linework, high detail, white empty background, t-shirt graphic design style"
        ],
        
        # ==================== 风格 (锁定) ====================
        "styles": [
            "intricate black and white lineart, pure white background, baimiao style, high contrast, vertical aspect ratio"
        ],
        
        # ==================== 情绪 ====================
        "moods": [
            "majestic, flowing, dynamic, traditional"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}