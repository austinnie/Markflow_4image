# tools/prompts_new/transformers_optimus_prime.py
# 适配 generate_new.py 的核心架构

STYLE = {
    "transformers_optimus_prime": {
        "folder": "变形金刚_擎天柱",
        "strength": 0.35,
        # 主体：优化结构，压制高达，增加武器与动态
        "subjects": [
            # 1. 经典电影造型展示
            "high quality 3D figure of Optimus Prime, Transformers Age of Extinction design, classic silver and blue metallic armor, iconic truck window chest, exposed mechanical joints, strict Classic Optimus Prime faceplate helmet, no Gundam, no V-antenna, standing upright on a flat white surface, neutral white background, strictly no scrolls, no banners, no paper, studio photography, collectible resin statue",
            
            # 2. 汽车人Logo特写 + 战损
            "cinematic Optimus Prime collectible statue, standing heroically, chest open revealing the glowing Autobot insignia, distinct Autobot logo on the shoulder, battle-worn silver and blue paint, strict Optimus Prime helmet design, pure grey seamless studio background, strictly no scrolls, no banners",
            
            # 3. 赛博朋克地台 + 光剑
            "Optimus Prime premium mecha figure, standing on a cyberpunk mechanical platform, fragmented alien metal debris at the feet, dramatic blue underglow, holding a glowing blue energy sword, dynamic studio lighting, chrome texture, strict movie-accurate Optimus Prime head, strictly no scrolls, no Gundam",
            
            # 4. 动态战斗姿态 + 巨盾
            "Optimus Prime action figure, dynamic combat stance, holding a heavy futuristic shield in one hand, exposed mechanical wiring, Autobot emblem glowing in the center of the chest, realistic metallic reflection, standing against a dark energy grid background, no scrolls, no paper, no anime aesthetics",
            
            # 5. 重火力火炮 + 仰视视角
            "low angle shot of Optimus Prime figure, imposing and majestic, holding a massive twin-barrel sci-fi cannon, translucent blue energy rings floating around the body, Autobot insignia glowing brightly on the chest, dark factory background with glowing orange lines, no extra text, no scrolls, no banners",
            
            # 6. 新增：单膝跪地敬礼/休憩姿态（增加变化）
            "Optimus Prime collectible figure, kneeling on one knee on a debris field, lowering his head in a solemn moment, blue and red metallic armor, classic truck window chest, heroic leader vibe, dark atmospheric warehouse background, dramatic spotlight, ultra realistic resin figure"
        ],
        "styles": [
            "hyper-realistic die-cast metal effect, glossy and matte mixed painting, micro detailing, studio product shot, macro photography",
            "cinematic 3D render, photorealistic metal materials, sharp edges, studio spotlight, high contrast shadows",
            "high definition die-cast metal effect, intricate chrome armor, mechanical precision, wet reflections"
        ],
        "moods": [
            "epic, heroic, powerful leader, majestic",
            "cyberpunk, futuristic, heavy metal, tactical",
            "dramatic, cinematic, glowing energy, intense"
        ],
        # ✅ 既然 USE_CONTENT_TEXTS 有用，保留这些标志性词汇，但已修改为“印在装甲上”
        "content_texts": [
            "AUTOBOT",
            "OPTIMUS PRIME",
            "LEADER"
        ]
    }
}