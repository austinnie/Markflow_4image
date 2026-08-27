# prompts/gallery_elegant_safe.py
# 【画廊优雅特供版】全球知性清纯女孩摄影（画廊背景、修身蕾丝、安全尺度）

STYLE = {
    "gallery_elegant_safe": {
        "folder": "优雅画廊_知性清纯",
        "strength": 0.45,  # 稍微提高强度以保持身材与服饰细节
        
        # ==================== 主体 (核心场景：画廊看画、知性优雅、修身服饰) ====================
        "subjects": [
            # ========== 🇨🇳 东亚 (韩系/国风/日系) ==========
            "a beautiful Asian woman with long dark hair, wearing a cream-colored lace V-neck top and beige fitted trousers, standing in an art gallery, looking at a large landscape oil painting, soft gallery lighting, elegant posture, natural smile",
            "a pure Chinese girl with wavy black hair, wearing a white lace knit short-sleeve top and light-colored slim pants, posing in front of a famous painting, warm museum atmosphere, graceful and serene",
            "a stunning Japanese woman, long straight hair, wearing a semi-sheer white floral lace blouse and pale leggings, admiring a Monet-style landscape painting in a fine art museum, soft natural daylight",
            "a beautiful Korean girl with flawless skin, wearing a cream lace crop top and white skinny pants, walking through an art exhibition hall, looking back at the camera with a sweet smile, sophisticated and clean",

            # ========== 🇪🇺 欧洲 (法式/意式/英伦) ==========
            "a graceful European woman with soft blonde hair, wearing a white lace blouse with butterfly bow, standing in front of a scenic oil painting in a gallery, soft warm light, elegant and timeless photography",
            "a charming French girl, wearing a white cream lace top and beige trousers, looking up at a mountain landscape painting in a museum, relaxed and elegant, artistic vibe",
            "a beautiful British woman, wearing a vintage-style lace short-sleeve top, standing in an art gallery near a nature painting, gentle smile, sophisticated composition",
            "an Italian girl, long dark hair, wearing a fitted cream lace top and white trousers, sitting on a bench inside a bright art gallery with painting canvases around, peaceful atmosphere",

            # ========== 🇺🇸 北美 & 🇦🇺 大洋洲 (现代知性) ==========
            "a cute American girl, wearing a white lace top with a ribbon tie and beige fitted pants, standing in a contemporary art gallery with landscape oil paintings, soft natural light, cheerful expression",
            "a stunning Canadian woman, wearing a cream stretch lace blouse, posing in an art gallery with a huge nature painting on the wall, elegant and pure, professional portrait photography",
            "an Australian girl, fresh face, wearing a beige lace top and white trousers, looking at paintings in a sunlit art exhibition, relaxed and refined",

            # ========== 🌍 多元化 (保证整体风格统一) ==========
            "an elegant Middle Eastern woman, wearing a white lace overlay top and cream pants, standing gracefully inside a fine art museum with landscape paintings, serene and beautiful",
            "a beautiful Latina girl with long dark hair, wearing a beige lace blouse and slim pants, looking at a nature painting in an art gallery, warm lighting, gentle smile"
        ],
        
        # ==================== 风格与细节 (重点：服装质感与背景) ====================
        "styles": [
            "photorealistic fine art portrait, gallery interior, large landscape painting background, warm soft lighting, art exhibition setting",
            "professional photography, shallow depth of field, museum aesthetic, clear skin texture, shiny long hair, elegant composition",
            "high quality fashion editorial, subtle makeup, beige and cream color palette, clean aesthetic"
        ],
        "moods": [
            "serene, pure, elegant, graceful, intellectual, peaceful"
        ],
        
        # 补充: 如果您的工具支持 negative prompts，这里可以加入禁止项
        # "negative_prompts": ["extra fingers", "bad hands", "ugly face", "shiny skin", "highly saturated colors", "underwear", "swimsuit", "too much makeup"],
        
        "content_texts": [] 
    }
}