# prompts/human_sketch_frame.py
# 真实感人像素描 + 画架/画框

STYLE = {
    "human_sketch_frame": {
        "folder": "人像素描画框",
        "strength": 0.35,
        
        # ==================== 主体主体 (构图方向) ====================
        "subjects": [
            "young woman taking a selfie with a smartphone, relaxed elegant posture, holding phone with one hand, subtle gentle smile",
            "young woman posing in art studio, holding smartphone, casual oversized t-shirt, long hair, natural posture"
        ],
        
        # ==================== 媒介与画布环境 (核心：真实感来源) ====================
        "mediums": [
            "mounted on a wooden easel with a blue backing board and silver binder clips, art studio background, loose sketchy pencil strokes visible",
            "tightly framed inside a minimalist thick white picture frame, hanging on a clean white wall, soft ambient drop shadow behind frame, gallery display lighting"
        ],
        
        # ==================== 风格与技法 ====================
        "styles": [
            "photorealistic pencil sketch, delicate shading, soft graphite texture, ultra-detailed facial features, fine lines",
            "traditional graphite drawing, chiaroscuro, realistic shadow rendering, raw pencil marks on textured paper, unfinished draft style"
        ],
        
        # ==================== 情绪与氛围 ====================
        "moods": [
            "elegant, serene, natural light, subtle, authentic, unpretentious",
            "artistic, raw, expressive, quiet confidence, casual charm"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [
            "artist signature '蒋志辉' and date '2026.6.6' in the bottom left corner"
        ]
    }
}