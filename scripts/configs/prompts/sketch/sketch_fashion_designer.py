# tools/prompts_new/sketch_fashion_designer.py
# 铅笔素描 - 时装设计师的日常

STYLE = {
    "sketch_fashion_designer": {
        "folder": "铅笔素描_时装设计师",
        "strength": 0.35,
        "subjects": [
            # ================= 【维度 1：经典还原（人台、挂衣架、裁缝桌）】 =================
            "hyper-realistic pencil sketch, graphite drawing, a beautiful young fashion designer with long wavy hair, wearing a fitted long-sleeve top and jeans, standing in a bright atelier, looking at a dress on a sewing mannequin, clothes rack in background, detailed shading, textured paper, fine art illustration",

            # ================= 【维度 2：服装变化（把长袖换成吊带、西装、大衣）】 =================
            "realistic charcoal sketch, a fashion designer in a studio, wearing a sleek silk camisole and high-waisted trousers, holding a pencil and sketching on a large drawing board, background full of garment sketches pinned to the wall, dramatic window light, vintage sketchbook aesthetic",
            "detailed pencil drawing, a female fashion designer with messy bun, wearing an oversized blazer over a tank top, standing by a full-length mirror, adjusting a fabric swatch on a dummy, cluttered but creative studio, sharp graphite lines, white paper",

            # ================= 【维度 3：场景变化（裁缝店、时装秀后台、面料市场）】 =================
            "pencil sketch illustration, a female designer working in the backstage of a fashion show, holding a clipboard and checking the model's outfit, busy environment with sewing machines and clothes rails, intense focused expression, dynamic sketching style, medium grey tone",
            "hyper-realistic graphite drawing, a woman sitting at a large wooden table in a fabric market, touching rolls of colorful fabric, looking at swatches, her design portfolio open beside her, realistic studio light, highly detailed clothing folds, paper texture",
            "high-end charcoal portrait, a fashion designer in her home studio, sitting comfortably on a mid-century sofa, laptop on her lap, surrounded by books and fabric samples, relaxed but professional vibe, soft eraser highlights, detailed curtains and window light",

            # ================= 【维度 4：环境氛围变化（雨夜工作室、顶楼天光、深夜台灯）】 =================
            "moody pencil sketch, a female designer sitting in a darkened studio at night, illuminated by a single warm desk lamp, holding a cup of coffee, looking at sketches, clothes rack in shadow, atmospheric lighting, dark graphite shading, fine art aesthetic",
            "pencil portrait, a young designer working at a large window overlooking a rainy city street, natural diffuse light illuminating her face, wearing an elegant turtleneck sweater, drafting clothes on a paper pad, moody and quiet atmosphere, soft pencil strokes",
            "architectural pencil sketch style, a designer working in a high-ceilinged loft with exposed brick, standing at an angled drafting table, wearing a loose artist's smock, large windows letting in bright daylight, detailed interior perspective, sharp shadows and precise lines",

            # ================= 【维度 5：视角与构图变换（俯视、仰视、背影、特写）】 =================
            "charcoal sketch, a fashion designer viewed from behind, looking at a life-size body sketch on an easel, wearing a simple t-shirt and jeans, hands on her hips, deep in thought, clothes rack in background, textured paper grain, light graphite wash",
            "realistic pencil drawing, close-up portrait of a female designer, holding a pencil to her chin while looking up thoughtfully, sketching on a page, slight motion blur on the hand, soft lighting, highly expressive eyes and facial features, classic portrait sketch",
            "dynamic pencil sketch, a designer moving quickly across her studio, grabbing a tape measure from a dummy, wind blowing through her hair, motion lines suggested in the sketch, chaotic but creative energy, casual clothes, energetic drawing style"
        ],
        "styles": [
            "hyper-realistic pencil sketch, graphite shading, fine textured white paper, delicate highlights",
            "highly detailed charcoal drawing, tonal contrast, realistic fabric and skin textures",
            "fine art illustration, clean linework with soft eraser wash, elegant composition",
            "studio sketchbook style, professional artistic draft, balanced light and shadow"
        ],
        "moods": [
            "creative, focused, professional, elegant",
            "quiet, atmospheric, inspiring, dedicated",
            "busy, energetic, passionate, intense",
            "relaxed, cozy, thoughtful, artistic"
        ],
        "content_texts": []
    }
}