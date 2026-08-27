# prompts/pure_serene_safe.py
# 【安全特供版】全球清纯女孩摄影插画/艺术品（厚衣服、场景化、安全构图）

STYLE = {
    "pure_serene_safe": {
        "folder": "安全壁纸_清纯风景",
        "strength": 0.40,
        
        # ==================== 主体 (安全重构：长衣、风景、画框) ====================
        "subjects": [
            # ========== 🇨🇳 东亚 (清纯国风/日系/韩系) ==========
            "a beautiful young Asian woman, wearing a soft cream-colored knit sweater, sitting by a window looking at a bamboo forest, warm morning sunlight, cozy atmosphere, photorealistic fine art, framed artwork style",
            "a pure Chinese girl, elegant long-sleeved modern hanfu, walking through a misty bamboo forest with dappled sunlight, peaceful expression, serene beauty, landscape photography",
            "a serene Japanese maiden, wearing a simple traditional kimono with long sleeves, cherry blossom petals falling in a temple garden, soft pink light, gentle atmosphere",
            "a sweet Korean girl, wearing an oversized cream white sweater, holding a warm cup of coffee in a cozy cafe with soft warm lighting, natural makeup, peaceful expression",
            "a graceful Chinese girl, wearing a long elegant winter coat, holding an oil-paper umbrella, standing in a misty snowy ancient street, poetic atmosphere, timeless beauty",

            # ========== 🇪🇺 欧洲 (英伦/法式/意大利/北欧/东欧) ==========
            "a graceful European girl, blonde hair, wearing a thick white cable-knit sweater, standing in a lavender field under a golden hour sunset, innocent smile, dreamy fine art landscape",
            "a beautiful British woman, wearing a classic tweed coat, sitting in a rustic garden with morning mist, gentle expression, soft morning light, painted art style",
            "a romantic Italian girl, wearing a warm white scarf and long coat, standing on a balcony overlooking a sunset sea, Mediterranean breeze, peaceful and timeless beauty",
            "a gentle Nordic girl, wearing a simple heavy winter coat, standing in a snowy pine forest, soft cold winter light, crystal clear eyes, pure and elegant artistic portrait",
            "an ethereal Eastern European girl, wearing a long white winter coat, standing in a misty mountain meadow, soft mystical atmosphere, fairy-tale beauty",
            "a serene French girl, wearing a classic Breton striped shirt and white cardigan, sitting on a swing in a lush summer vineyard, warm golden afternoon light, vintage charm",
            "a pretty Greek girl, wearing a white linen shirt, standing by the blue Aegean sea, sea breeze, bright Mediterranean sunlight, radiant smile",
            "a charming Scottish girl, wearing a cozy tartan scarf, standing in a misty highlands moor, purple heather blooming, a sense of ancient and pure landscape",

            # ========== 🇺🇸 北美 & 🇦🇺 大洋洲 (西式随性) ==========
            "a cute American girl, wearing a denim jacket and white shirt, sitting on a sunny wooden porch, golden hour light, relaxed smile, warm summer vibe",
            "an Australian girl, wearing a light beach cover-up, walking along a pristine beach at sunrise, ocean breeze, golden light, peaceful and free",
            "a graceful Canadian girl, wearing a cozy plaid sweater, sitting by a cabin window watching falling autumn leaves, comforting and serene",
            "a beautiful Hawaiian girl, wearing a floral sundress, standing under a palm tree at sunset, warm island breeze, relaxed and radiant",
            "a stunning Californian girl, wearing a white knitted sweater, leaning against a vintage van, soft desert sunset light, bohemian and free-spirited",
            "a beautiful Alaskan girl, wearing a thick white winter parka, standing in a snow-covered pine forest, faint aurora borealis in the night sky, mystical and pure",

            # ========== 🇧🇷 南美 & 🇲🇽 拉美 (热情与阳光) ==========
            "a beautiful Brazilian girl, wearing a simple white linen cover-up, standing in a lush tropical rainforest, dappled sunlight through palm leaves, radiant and pure",
            "a charming Mexican girl, wearing a traditional embroidered white blouse, sitting in a sunny courtyard with blooming cacti and colorful flowers, soft smile, earthy warmth",
            "a young Argentine girl, wearing a light summer dress, standing in a golden pampas grass field, wind sweeping through her hair, soulful and gentle",
            "a graceful Colombian girl, wearing a flowing white dress, standing by a tranquil mountain lake in the Andes, crisp clean air, soft morning light",

            # ========== 🌍 中东 & 非洲 (异域神秘与清纯) ==========
            "a serene Middle Eastern girl, wearing a simple light beige abaya, standing at the edge of a desert oasis, soft golden sunset light, mysterious and elegant beauty",
            "a beautiful Ethiopian girl, wearing traditional white habesha kemis dress, sitting in a lush green highland meadow, soft morning mist, natural and pure",
            "a graceful Moroccan girl, wearing a simple white caftan, standing in a sunlit riad courtyard with orange trees, warm serene afternoon light, timeless beauty",
            "a gentle Egyptian girl, wearing flowing white cotton dress, standing near the ancient pyramids at twilight, soft warm breeze, mystical and serene",
            "a sweet South African girl, wearing a white sundress, standing in a blooming wildflower field near Cape Town, vibrant spring colors, fresh air, peaceful",

            # ========== 🌏 南亚 & 东南亚 (热带风情与灵性) ==========
            "a charming Indian girl, wearing an elegant white saree, standing in a misty tea plantation in the mountains, early morning sunlight, serene and graceful",
            "a beautiful Thai girl, wearing a simple white traditional blouse, standing quietly in a serene tropical temple garden, soft warm sunlight, gentle smile",
            "a sweet Indonesian girl, wearing a traditional white kebaya, standing in a lush rice terrace, bright tropical sunlight, natural fresh beauty",
            "a serene Nepali girl, wearing a traditional white dress, standing in the Himalayas with snow-capped peaks behind, cold crisp air, pure and majestic",
            "a beautiful Burmese girl, wearing a simple white longyi, standing in an ancient temple complex in Bagan, the misty sunrise glowing through the pagodas, ethereal and peaceful",

            # ========== 🌸 节日/特殊氛围/风俗 (精致异域风情) ==========
            "a young woman in Hanbok, traditional Korean dress, standing under a blooming cherry tree in spring, soft pink petals falling, elegant and pure",
            "a girl in a traditional white kimono with long sleeves, standing at a Japanese shrine, soft autumn sunlight, serene and respectful atmosphere",
            "a graceful Austrian girl, wearing a traditional dirndl dress, standing in an alpine meadow, snow-capped mountains in the background, bright and cheerful",
            "a beautiful Ukrainian girl, wearing a traditional white embroidered vyshyvanka, standing in a wheat field with sunflowers, peaceful countryside morning",
            "a lovely Polish girl, wearing a traditional white lace folk dress, standing in a blooming rapeseed field, blue sky and yellow flowers, charming and bright",

            # ========== 🎨 文学艺术与意境 (极具电影感 + 画框保护) ==========
            "a serene girl, in a minimalist library, wearing a cream long-sleeved sweater, reading an old book by a tall window, natural light streaming in, quiet intellectual beauty, fine art photography",
            "a delicate young woman, wearing a white beret and long cardigan, painting on a canvas in a sunlit Parisian studio, artistic, elegant and pure, classical painting style",
            "a beautiful woman, wearing a simple white shift dress, sitting in a quiet opera house seat, empty theater, soft spotlight, timeless elegance, photographic art",
            "a sweet girl, holding a single white lily, wearing a soft white coat, standing in a misty morning garden, soft golden light, floral and peaceful atmosphere, framed oil painting",
            "a graceful musician girl, wearing an elegant dress, playing a grand piano by a large window, warm sunlight and falling leaves, cinematic masterpiece",
            "a sweet storyteller girl, wearing a cozy jacket, sitting on a blanket in a sun-drenched meadow, writing in her journal, a gentle breeze, quiet and introspective",

            # ========== 🎐 极简艺术照 (高冷清纯) ==========
            "a pure woman, stark white background, wearing a crisp white long-sleeved shirt, looking gently at camera, minimalist studio light, soft smile, fine art portrait, printed picture in a white frame",
            "an elegant girl, wearing a white long dress, standing in an empty white room with a single window, dramatic natural light, pure and angelic, high fashion editorial",
            "a graceful girl, wearing a simple white cotton shirt, natural sunlight casting soft shadows on her face, effortless beauty, editorial style"
        ],
        
        # ==================== 风格与情绪 ====================
        "styles": [
            "photorealistic cinematic portrait, natural lighting, blurred scenic background, soft warm color palette, art gallery aesthetic",
            "fine art photography, landscape background, long sleeves, modest fashion, masterpiece"
        ],
        "moods": [
            "serene, peaceful, pure, elegant"
        ],
        
        "content_texts": [] 
    }
}