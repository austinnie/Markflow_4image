# tools/prompts_new/mecha_3d_prototype_dynamic.py
# 3D灰模 - 动态机娘原型

STYLE = {
    "mecha_3d_prototype_dynamic": {
        "folder": "3D灰模_动态机娘",
        "strength": 0.35,
        "subjects": [
            # ================= 【维度 1：基础白模还原（纯悬浮，去掉底座）】 =================
            "unpainted 3D resin prototype, anime girl with short hair, wearing a seamless sci-fi combat suit, dual wielding futuristic handguns, mid-air dynamic floating pose, arms spread wide, legs bent in a jump, no pedestal, pure light grey neutral background, macro 3D render, ZBrush sculpt visible mesh texture",

            # ================= 【维度 2：动作裂变（进攻、落地、格挡）】 =================
            "unpainted grey 3D print prototype, mecha girl, short black hair, futuristic tactical suit, holding a massive sci-fi sniper rifle, standing on one leg, extreme forward leaning action pose, suspended in the air, pure grey studio backdrop, macro details, 3D modeling render",
            "3D clay sculpt prototype, anime mecha girl, short hair, wielding a futuristic energy katana, mid-swing dynamic crouch pose, floating off the ground, plain grey background, intricate panel lines on the armor, soft lighting",

            # ================= 【维度 3：武器裂变（双刀、大锤、巨剑）】 =================
            "unpainted 3D model kit, female mecha warrior, short hair, tight futuristic armor, dual wielding long mechanical swords, crossed in front of her, mid-air leaping stance, grey neutral background, 3D printing preview style",
            "unpainted resin figure prototype, mecha girl, sleek sci-fi armor, holding a heavy futuristic hammer, floating in the air, dynamic falling strike pose, bare light grey background, detailed joint mechanisms",

            # ================= 【维度 4：后背科幻机翼/背包的加入（纯粹机甲感）】 =================
            "unpainted grey 3D print, anime mecha girl, short hair, futuristic combat suit, large mechanical sci-fi wings extended from the back, mid-air soaring pose, arms reaching out, no ground base, pure grey background, ZBrush clay render",
            "3D sculpt prototype, mecha girl, sleek white armor model, equipped with high-tech jetpack on the back, floating in the air, holding a laser cannon, dynamic action shot, plain grey studio background",

            # ================= 【维度 5：不同部位的装甲变形（腿部重装、面罩、机甲猫耳）】 =================
            "unpainted 3D prototype, mecha girl, short white hair, wearing heavy armored leg greaves and thick sci-fi boots, flying mid-air, holding a futuristic handgun, mechanical cat ear headpiece, pure grey background, 3D printing mesh details",
            "unpainted grey resin model, mecha girl, full face futuristic helmet with glowing eye slits, sci-fi armor suit, floating in a jumping pose, arms extended holding a large shield, no base, neutral grey background, 3D render",

            # ================= 【维度 6：打破“纯灰”的限制（如果以后想上色预览）】 =================
            "3D render of an unpainted prototype, anime mecha girl, short hair, futuristic tactical combat suit, dynamic mid-air jump, but with subtle light blue LED glowing accents on the armor joints, floating on a transparent acrylic stand, neutral grey background, product design render"
        ],
        "styles": [
            "unpainted 3D grey resin prototype, ZBrush sculpt details, visible wireframe texture, macro photography",
            "3D printing CAD preview render, clay model sculpt, soft matte grey material, studio lighting",
            "high resolution 3D prototype photography, monochrome aesthetic, micro details, plain grey background",
            "miniature sculpt render, unpainted plastic kit, sharp edges, neutral diffuse lighting"
        ],
        "moods": [
            "dynamic, agile, action-packed, airborne",
            "sleek, futuristic, high-tech, prototype",
            "graceful yet deadly, aerial, floating"
        ],
        "content_texts": []
    }
}