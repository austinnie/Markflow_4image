# tools/prompts_new/beach_resort_swimwear.py
# 夏日度假 - 海滨泳装写真

STYLE = {
    "beach_resort_swimwear": {
        "folder": "夏日海滨_泳装度假",
        "strength": 0.35,
        "subjects": [
            # ================= 【维度 1：原图风格还原（比基尼、沙滩、海风）】 =================
            "realistic beach photography, curvy asian woman, long black hair, wearing a cute tropical fruit print bikini, standing on a white sandy beach, palm trees in the background, gentle ocean waves, bright sunny day, relaxed and confident posture, natural skin texture, shallow depth of field",
            "realistic portrait, beautiful mature woman, wavy brown hair, wearing a black lace bikini and a sheer white open beach shirt, standing at the water's edge, wind blowing her hair, turquoise ocean and island in the background, serene mood",

            # ================= 【维度 2：连体泳衣与水上运动（泳池/水上摩托）】 =================
            "realistic photo, curvy asian woman, long black hair, wearing a classic navy blue one-piece swimsuit, sitting on the edge of a bright indoor swimming pool, legs dangling in the water, hands resting on her knee, smiling at the camera, bright natural light from a skylight",
            "realistic action portrait, asian woman, long black hair, wearing a sleek black one-piece swimsuit, sitting on a white jet ski in the middle of the sea, holding the handlebars, blue ocean and clear sky, looking back at the camera, adventure vibe, warm sun",

            # ================= 【维度 3：场景扩展 - 豪华游艇与海上秋千】 =================
            "realistic lifestyle photography, curvy asian woman, long black hair, wearing a white ribbed bikini top and a blue floral wrap skirt, standing on the deck of a luxury yacht, holding a glass of champagne, looking out at the vast ocean, glamorous summer vacation aesthetic",
            "realistic outdoor photo, curvy asian woman, long black hair, wearing a light purple bikini and matching sarong, sitting on a wooden swing hanging from a palm tree on the beach, swinging gently, enjoying the sunset golden hour light, calm and dreamy atmosphere",

            # ================= 【维度 4：配饰革命 - 草帽、墨镜、遮阳伞】 =================
            "realistic beach portrait, curvy asian woman, long black hair, wearing a classic beige one-piece swimsuit, a large straw sun hat, and black sunglasses, holding a colorful beach umbrella, standing on white sand, relaxed summer vacation mood, bright sunlight",
            "realistic close-up photo, beautiful curvy woman, long black hair, wearing a patterned bikini, holding a cold coconut drink with a straw, wearing chic oversized sunglasses, lounging on a sunbed on the beach, clear blue sky and ocean background, lifestyle shot",

            # ================= 【维度 5：动态与光影特写 - 冲浪、日落、逆光】 =================
            "realistic dynamic photo, curvy woman, long black hair, wearing a black swimsuit, walking along the shoreline with her feet in the water, splashing water, bright smile, ocean waves behind her, crystal clear blue water, summer daytime",
            "cinematic beach photo, curvy woman, long black hair, wearing a white bikini, standing waist-deep in the ocean, arms raised gracefully, embracing the sunset, golden backlight outlining her silhouette, warm orange and blue colors, stunning atmosphere",
            "realistic portrait, curvy asian woman, long black hair, wearing a blue one-piece swimsuit, standing on a tropical beach during a gentle evening rain, sky is dramatic with clouds, water droplets on her skin, serene and melancholic vibe",

            # ================= 【维度 6：室内外高级泳池派对】 =================
            "realistic photo, curvy asian woman, black hair tied in a low bun, wearing an elegant nude-colored one-piece swimsuit, standing by the infinity pool of a luxury hotel, leaning against the glass railing, city skyline in the background, elegant and sophisticated atmosphere",
            "realistic party portrait, curvy woman, long black hair, wearing a sparkly gold bikini, holding a cocktail glass, standing in an outdoor pool party, floating pool lights, dusk lighting, laughing and smiling, fun summer night aesthetic"
        ],
        "styles": [
            "realistic outdoor portrait photography, natural sunlight, shallow depth of field, vibrant colors",
            "professional travel lifestyle photography, beach aesthetic, golden hour lighting, warm tones",
            "cinematic summer photography, sharp focus, bright and airy mood, beautiful skin texture",
            "high definition commercial swimwear shoot, clear blue water, sparkling reflections"
        ],
        "moods": [
            "relaxed, sunny, joyful, tropical",
            "elegant, glamorous, serene, chic",
            "energetic, fun, adventurous, vibrant",
            "dreamy, golden, peaceful, romantic"
        ],
        "content_texts": []
    }
}