# tools/prompts_new/ancient_tree_temple_sketch.py
# 古树古建 - 白描重构图

STYLE = {
    "ancient_tree_temple_sketch": {
        "folder": "白描古树_古建交织",
        "strength": 0.35,
        "subjects": [
            # ================= 【维度 1：倾斜/靠边构图（打破居中）】 =================
            "traditional Chinese line drawing, a magnificent ancient pine tree with a dramatically twisted and leaning trunk, growing diagonally from the left edge of the frame, its massive branches extending over and partially sheltering a traditional Chinese wooden temple building on the right, highly detailed bark and roof tiles, pure white background, professional architectural sketch",
            "classical ink line art, a colossal ancient tree with a gnarled trunk positioned on the far right, its thick branches bending horizontally across the upper half of the picture, a small traditional temple entrance and stone lion visible on the lower left, dynamic asymmetrical composition, fine lines",

            # ================= 【维度 2：树干变形与倾斜（改变僵直姿态）】 =================
            "intricate black and white sketch, an ancient tree with a thick, serpentine trunk that twists like a dragon, leaning heavily against the corner of a tiled temple building, roots firmly gripping a stone fence, branches bowing downwards, detailed shadow lines, white paper, elegant classical architecture sketch",
            "line drawing illustration, a weathered ancient tree with a hollow trunk, bending forward in a dramatic curve over a stone archway, the leaves and branches forming a natural canopy, shadows cast on the ground, highly detailed texture, pure white background, atmospheric oriental art",

            # ================= 【维度 3：空间遮挡与交互（改变前后关系）】 =================
            "Chinese ink line art, a dense canopy of an ancient pine tree dominating the foreground, its thick trunk and branches completely obscuring the upper half of the temple roof behind it, creating a strong sense of depth and layering, intricate foliage detail, white background, classic architectural perspective",
            "traditional line sketch, an ancient tree growing over and encompassing a stone tablet, its twisted roots tightly hugging the stone, with a traditional temple building visible behind the tree and tablet, organic integration of nature and architecture, precise hatching, pure white background",

            # ================= 【维度 4：极端姿态与动态（风吹、半倒、盘踞）】 =================
            "traditional Chinese line drawing, an ancient tree struck by lightning, split trunk, half of the branches bending violently to the side as if blown by a strong wind, a small wooden temple in the background, dramatic and powerful composition, wild dynamic nature, high contrast black and white",
            "classical ink sketch, a majestic old tree growing sideways out of a steep stone wall, almost parallel to the ground, its roots stretching horizontally, a traditional stone pagoda below it, extreme growth angle, rich texture and shadow lines, white background, powerful visual impact",

            # ================= 【维度 5：庭院景观变化（不同建筑与植物）】 =================
            "line drawing sketch, an ancient weeping willow tree with its drooping branches intertwining with the eaves of a classic Chinese pavilion, a stone bridge over a small pond below, intricate woodwork of the pavilion, elegant curved lines, pure white paper, serene garden aesthetic",
            "architectural line art, an ancient ginkgo tree with a wide spreading trunk, situated in a corner courtyard, a large stone table under the tree, old brick walls with intricate textures, soft shading, a pair of stone drums at the gate, precise architectural illustration",
            "traditional line painting, a giant ancient tree with sweeping vertical branches, standing to the left of a traditional courtyard, an open door showing a dark interior, a stone carved lion on a pedestal at the entrance, rich detailing on the roof tiles and tree bark, pure white background"
        ],
        "styles": [
            "traditional Chinese line art, classical architectural illustration, intricate roof and bark textures",
            "black and white sketch, professional landscape drawing, fine crosshatching",
            "oriental ink pen drawing, detailed shading and perspective, pure white background",
            "highly detailed architectural linework, expressive tree anatomy, traditional aesthetics"
        ],
        "moods": [
            "ancient, sacred, majestic, harmonious",
            "wild, dramatic, weathered, timeless",
            "peaceful, serene, scholarly, zen",
            "intertwined, organic, powerful, rooted"
        ],
        "content_texts": []
    }
}