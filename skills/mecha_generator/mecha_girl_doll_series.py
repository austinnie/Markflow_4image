# tools/prompts_new/mecha_girl_doll_series.py
# 高端手办 - 粉发系列多变服装（面部细节强化版）

STYLE = {
    "mecha_girl_doll_series": {
        "folder": "粉发手办_多变服装",
        "strength": 0.35,
        "subjects": [
            # ================= 【基础维度：还原经典高开叉/蕾丝】 =================
            "highly detailed face, sharp focus on the eyes, realistic skin texture, premium anime girl collectible figure, long pink hair, star-shaped hair clip, wearing a glossy white silk high-slit evening dress with lace sleeves, standing confidently on a sculpted rocky base, dark grey studio background, macro product photography, high-end PVC statue",

            # ================= 【维度 1：制服与战斗装（打破日常感）】 =================
            "highly detailed face, sharp focus on the eyes, high-end anime girl figure, long pink hair, star hairpin, wearing a sleek navy blue sci-fi military pilot suit, holding a futuristic helmet under her arm, standing on a metallic hangar base, dark professional studio lighting, collectible resin statue",
            "highly detailed face, anime girl collectible statue, pink hair, star accessory, wearing a futuristic white and gold armored combat dress, holding a glowing energy sword, dynamic standing pose, dark grey studio background, premium model photography",

            # ================= 【维度 2：幻想风与魔法少女】 =================
            "highly detailed face, premium anime figure, pink haired girl, star hairpin, wearing a translucent ethereal blue fantasy gown with shimmering stars, holding a magic crystal wand, standing on a swirling galaxy-themed base, dark studio photography, elegant magical aesthetic",
            "highly detailed face, anime statue, pink hair, star clip, wearing a red and white traditional Japanese shrine maiden outfit with flowing sleeves, holding a wooden staff, standing on a stone lantern base, dark background, high definition collectible",

            # ================= 【维度 3：动态动作与战斗姿态】 =================
            "highly detailed face, anime girl action figure, pink hair, star ornament, wearing a tight black leather tactical suit, dual-wielding futuristic handguns, in a dynamic mid-air leaping pose, firing guns, effects of muzzle flash, dark grey studio background, dramatic action shot",
            "highly detailed face, collectible figure, pink haired girl, wearing a cute white sundress, sitting on a desk, legs dangling, holding a cup of coffee, relaxed and cute pose, dark neutral background, casual lifestyle model photography",

            # ================= 【维度 4：性感/现代流行穿搭】 =================
            "highly detailed face, premium anime figure, pink hair, star hair clip, wearing a purple velvet corset top, white lace skirt, and black high heels, flirty pose, sitting elegantly on a velvet sofa base, dark studio background, luxury collectible",
            
            # ✨ 已修复：强制锁死“两只手抱猫”的结构，解决多手畸形 ✨
            "highly detailed face, anime girl statue, pink hair, hairpin, wearing a white silk bathrobe, gently cradling a black cat with exactly two hands, one hand supporting the cat's back, the other under its belly, the cat's paws visible, standing on a simple circular base, soft grey background, realistic skin texture, high-end resin figure",

            # ================= 【维度 5：赛博朋克与机械融合（装甲与道具）】 =================
            "highly detailed face, anime girl figure, pink hair, star hairpin, wearing a black and cyan cyberpunk jacket with glowing neon stripes, holding a futuristic katana, standing on a neon-lit street base, dark sleek background, sci-fi aesthetic",
            "highly detailed face, high-end collectible figure, pink haired girl, wearing a mechanical white exoskeleton suit with gold accents, holding a heavy futuristic rifle, standing on a mechanical debris base, premium lighting",

            # ================= 【维度 6：极致场景底座（打破单一底座）】 =================
            "highly detailed face, anime girl statue, pink hair, star accessory, wearing a red floral dress, standing in a blooming rose garden base, holding a bouquet, dark green and moody lighting, garden aesthetic",

            # ✨ 已修复：彻底解决“手与烛台融合”的畸形问题 ✨
            "highly detailed face, anime girl figure, pink hair, star hairpin, wearing a black gothic dress with lace details, standing gracefully on a weathered stone cathedral pillar base, her wrist loosely resting on the top of a tall, thin black candlestick, her fingers open and gracefully splayed out, a single lit white candle on top, elegant and solemn pose, dark moody studio background, mystical gothic aesthetic, perfectly shaped hands, clearly defined fingers"
        ],
        "styles": [
            "photorealistic resin figure, glossy and matte paint finish, realistic fabric textures, macro studio photography",
            "high definition collectible statue, professional product shot, soft shadows, pure grey background",
            "cinematic anime figure photography, atmospheric lighting, intricate sculpt details, premium PVC material",
            "3D rendered collectible, realistic skin and hair, dynamic lighting, diorama base effects"
        ],
        "moods": [
            "elegant, sophisticated, premium quality",
            "cute, lively, dynamic, high-energy",
            "mysterious, cool, futuristic, sexy",
            "graceful, magical, dreamy"
        ],
        "content_texts": []
    }
}