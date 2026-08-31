# tools/prompts_new/mecha_girl_warfare.py
# 机甲少女巷战 - 进阶扩展版 (全新维度)

STYLE = {
    "mecha_girl_warfare": {
        "folder": "机甲少女_巷战_进阶",
        "strength": 0.35,
        "subjects": [
            # ================= 维度 1：基础战术 (单枪/双枪) =================
            "cyberpunk female mecha soldier, silver-white high-gloss armor, flowing long white hair, sci-fi full-face helmet with blue glowing visor, aiming a futuristic tactical assault rifle, dynamic aiming stance, dark urban alleyway background",
            "futuristic female warrior, silver metal cybernetic body, long platinum blonde hair, helmet with glowing blue eyes, holding a heavy sci-fi revolver, crouching in a combat stance, distressed environment, battle sparks in the air",
            
            # ================= 维度 2：极端气候与地形 (雨夜/雪地/废墟) =================
            "female mecha operative, chrome armor, heavy rain pouring down, water droplets hitting the silver metal surface, long white hair soaked, holding a futuristic shotgun, standing in a dark neon-lit cyberpunk alley, dramatic wet reflections",
            "sci-fi female cyborg soldier, sleek white mecha suit, standing in a ruined snowy battlefield, heavy snowfall, thick fog in the background, holding a glowing sci-fi railgun, breathing fog visible in the cold air",
            "mecha girl sniper, white and silver armor, crouching on the edge of a collapsed skyscraper, holding a massive sniper rifle, overlooking a burning dystopian city, smoke and fire in the distance, dramatic orange and blue lighting",

            # ================= 维度 3：武器与战斗概念 (剑/盾/重火力) =================
            "female cyborg warrior, silver mecha armor, glowing blue energy sword in one hand, sleek laser pistol in the other, dynamic combat pose, sparks and flying debris, dark ruined factory background",
            "heavily armored mecha female, bulky exoskeleton suit, holding a massive Gatling gun, heavy metal plating, glowing blue eyes, standing like a tank in a battle-scarred city street, epic scale",

            # ================= 维度 4：造型特殊变体 (半透明装甲/黑金配色/战损) =================
            "sci-fi female with translucent crystal-like silver armor, long white hair floating in zero gravity, face mask with glowing purple LED lights, holding a plasma rifle, floating in a dark sci-fi corridor, ethereal aesthetic",
            "battle-worn mecha girl, silver armor with deep scratches, bullet holes, and rusted edges, exposed dark undersuit, long messy white hair, firing a heavy pistol, intense and gritty combat atmosphere",
            "stealth mecha girl, sleek matte black and silver armor, iridescent visor, long white hair tied in a high ponytail, crouching in a shadowy ruined building, holding a silenced sci-fi submachine gun, ready to strike",

            # ================= 维度 5：动作与情绪特写 (静态威慑/动态射击) =================
            "close-up shot of a cyborg girl, white and silver futuristic armor, helmet with blue digital LED faceplate, white hair, holding a dark metallic gun, intense eyes, floating dust particles, blurred urban background",
            "dynamic action shot of a mecha girl, leaping through the air while firing a heavy weapon, silver armor reflecting the flashes of muzzle fire, white hair wildly flying, exploding debris in the background",
            "high-end tactical doll, flawless white armor, quietly checking a futuristic pistol, standing in a dark, abandoned subway station, dim lights, suspenseful atmosphere, monochromatic palette"
        ],
        "styles": [
            "photorealistic 3D render, highly detailed metallic reflection, high contrast cinematic lighting, macro details",
            "8k resolution, glossy silver paint, intricate mechanical joints, scratches and weathering effects",
            "high definition sci-fi character design, sharp focus, shallow depth of field, realistic metal textures",
            "dynamic photography, action pose, professional studio lighting, dystopian atmosphere",
            "wet and glossy surface physics, raytraced reflections, anime realism style"
        ],
        "moods": [
            "tense, tactical, ready for combat, dangerous",
            "futuristic, cyberpunk, dystopian, gritty",
            "sleek, elegant, powerful, mysterious",
            "battlefield, survival, dark, atmospheric",
            "ethereal, elegant, majestic, high-tech",
            "gritty, war-torn, brutal, industrial"
        ],
        # 为了避免AI画蛇添足（生成毫无关系的卷轴），这里保持空列表
        "content_texts": []
    }
}