# prompts/sketch_portrait.py
# 3D CG 转 2D 铅笔素描/白描

STYLE = {
    "sketch_portrait": {
        "folder": "人像转素描",
        "strength": 0.55,  # 图生图强度，0.55 能保留原图动作，同时重绘为线稿
        
        # ==================== 主体提示词 ====================
        "subjects": [
            "extremely detailed black and white pencil sketch, drawing of a beautiful ancient Chinese woman wearing a flowing purple dress, lounging on a curved wooden recliner, elegant pose, traditional hair ornaments, 2D manga draft style, fine cross-hatching, graphite strokes, white paper background, monochrome, masterpiece, best quality"
        ],
        
        # ==================== 风格 (强制锁定为素描) ====================
        "styles": [
            "pencil drawing on paper, black and white lineart, graphite sketch, hard pencil strokes, baimiao style, 2D flat"
        ],
        
        # ==================== 情绪 ====================
        "moods": [
            "elegant, serene, tranquil, artistic"
        ],
        
        "content_texts": [] 
    }
}