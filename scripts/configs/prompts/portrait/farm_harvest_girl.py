# tools/prompts_new/farm_harvest_girl.py
# 田园写真 - 丰收的少女

STYLE = {
    "farm_harvest_girl": {
        "folder": "丰收少女_田园采摘",
        "strength": 0.35,
        "subjects": [
            # ================= 【维度 1：保持番茄/圣女果（原图动作的完美延伸）】 =================
            "realistic portrait photography, beautiful asian woman, long black hair in a ponytail, wearing a light blue tight zip-up sports top and light grey yoga pants, holding a handful of red cherry tomatoes, smiling brightly, standing in a lush green tomato field, rustic house in background, sunny day, shallow depth of field, natural sunlight, 8k",
            "realistic photo, asian woman, black hair, light blue long-sleeve athletic top, grey leggings, standing in an agricultural greenhouse, picking ripe tomatoes from a tall vine, outdoor lighting, rural scenery, beautiful skin texture",

            # ================= 【维度 2：场景扩展 - 草莓园与瓜棚】 =================
            "realistic photography, cute asian woman, black hair in a low bun, light blue tight zip-up jacket, light grey yoga pants, crouching in a sunny strawberry field, holding a large freshly picked red strawberry close to the camera, out of focus green leaves and white strawberry flowers, joyful summer vibe",
            "realistic portrait, asian woman, long black hair, light blue sports top, grey leggings, standing in a large outdoor watermelon patch, holding a huge green watermelon with both hands, looking at the camera with a satisfied smile, clear sky, vibrant natural colors",

            # ================= 【维度 3：场景扩展 - 丰收的葡萄园与向日葵】 =================
            "realistic photo, asian woman, black hair tied back, wearing a light blue zip-up shirt and grey sport pants, standing under a trellis of purple grapes, reaching up to cut a bunch of grapes, sunlight filtering through the leaves, soft dappled lighting, beautiful rural scene",
            "realistic outdoor portrait, asian woman, black ponytail, light blue tight athletic jacket, grey leggings, walking through a tall sunflower field, holding a single large sunflower, looking back over her shoulder, golden hour lighting, dreamy atmosphere, summer vibes",

            # ================= 【维度 4：动作变化 - 挑担、扛锄头、背篓】 =================
            "realistic photography, fit asian woman, black hair in a ponytail, light blue athletic top, grey yoga pants, carrying a traditional bamboo basket filled with fresh vegetables on her back, walking down a rural dirt path, sunset warm lighting, rustic house in background",
            "realistic photo, beautiful asian girl, long black hair, light blue zip-up jacket, grey leggings, holding a farming hoe over her shoulder, walking confidently along a plowed field, looking back with a gentle smile, fresh air, blue sky, outdoors",

            # ================= 【维度 5：气候与光影变化 - 雨后、黄昏、逆光】 =================
            "realistic portrait, asian woman, black hair, light blue long-sleeve sports shirt, light grey pants, standing in a vegetable garden just after a summer rain, fresh water droplets on the green leaves, holding a freshly washed cucumber, vibrant wet textures, overcast but bright daylight",
            "cinematic realistic photo, asian woman, black ponytail, light blue fitted jacket, grey leggings, standing in a cornfield during golden hour, holding a single ear of corn, golden backlighting outlining her figure, lens flare, warm moody atmosphere",

            # ================= 【维度 6：扩大穿搭与配件 - 换上草帽、毛巾】 =================
            "realistic photography, cute asian woman, long black hair, wearing a light blue tight zip-up sport top, white yoga pants, and a straw sun hat, holding a small basket of fresh tomatoes, wiping sweat from her forehead, cute expression, sunny farm background",
            "realistic portrait, asian woman, black hair in a ponytail, light blue tight athletic top, grey yoga pants, holding a large woven basket containing garlic and onions, squatting in a dirt field, looking up at the camera, natural daily life aesthetic"
        ],
        "styles": [
            "photorealistic outdoor portrait, natural sunlight, shallow depth of field, lens flare, realistic skin texture",
            "commercial lifestyle photography, vibrant colors, sharp focus, warm daylight, 8k",
            "cinematic countryside aesthetic, golden hour lighting, atmospheric depth, highly detailed",
            "professional DSLR photography, f/1.8 aperture, beautiful bokeh background, natural makeup"
        ],
        "moods": [
            "joyful, sunny, warm, summer vibe",
            "relaxed, fresh, healthy, rural",
            "satisfied, energetic, cheerful",
            "dreamy, soft, romantic, golden"
        ],
        "content_texts": []
    }
}