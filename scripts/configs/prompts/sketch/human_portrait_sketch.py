# prompts/human_portrait_sketch.py
# 优雅人像素描 + 画架/木框装裱

STYLE = {
    "human_portrait_sketch": {
        "folder": "人像半身素描",
        "strength": 0.35,
        
        # ==================== 主体与姿势 (构图核心) ====================
        "subjects": [
            "young woman, half-body portrait, long dark hair with parted bangs, high-neck sleeveless top, right hand gently resting on her chest, elegant and melancholic gaze",
            "young woman portrait, minimalist fashion, high neck t-shirt, hand on heart gesture, natural relaxed posture, serene expression"
        ],
        
        # ==================== 物理环境与呈现方式 (真实感核心) ====================
        "presentations": [
            "mounted on a wooden easel with a blue backing board and yellow/pink binder clips, studio ambient light, raw art process visible, attached to white paper with soft shadows",
            "framed in a minimalist light wood frame with a wide white matting, hanging on a clean white wall, soft drop shadow behind frame, gallery quality display"
        ],
        
        # ==================== 素描技法与风格 ====================
        "styles": [
            "realistic graphite pencil sketch, delicate facial shading, cross-hatching texture, expressive eyes, soft and raw pencil strokes",
            "fine art charcoal drawing, intricate hair rendering, chiaroscuro lighting, visible paper grain, traditional draft technique"
        ],
        
        # ==================== 情绪与氛围 ====================
        "moods": [
            "melancholic, elegant, quiet, subtle, artistic, timeless",
            "raw, expressive, nostalgic, gentle, graceful"
        ],
        
        # ==================== 签名设置 ====================
        "signatures": [
            "artist's signature '蒋志辉' and date '2026.7' in the bottom left corner in handwritten pencil style"
        ]
    }
}