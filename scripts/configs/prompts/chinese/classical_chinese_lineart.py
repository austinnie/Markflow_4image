# tools/prompts_new/classical_chinese_lineart.py
# 传统白描 - 高士临窗线稿系列

STYLE = {
    "classical_chinese_lineart": {
        "folder": "白描线稿_高士临窗",
        "strength": 0.35,
        "subjects": [
            # ================= 【维度 1：基础还原（经典临窗远眺）】 =================
            "traditional Chinese line drawing, baimiao style, an ancient Chinese scholar with long beard and flowing robe, standing by an open wooden window of a pavilion, looking out at the river, weeping willow branches with two small birds resting, distant mountains outlined, a wooden boat with woven canopy on the water, flying birds in the sky, pure white background, detailed clean contour lines",
            
            # ================= 【维度 2：视角变化（从户外看向室内/俯视）】 =================
            "traditional Chinese line art, side profile view of a scholar in a hat sitting at a desk inside a study, open window framing the distant lake, inkstone, brush holder, and scrolls on the desk, a bonsai tree nearby, detailed lattice window frame, minimalist outdoor landscape, pure white background, precision line work",
            "traditional Chinese ink sketch, looking down from an elevated angle, a scholar standing in an open-air pavilion on a cliff, leaning on the wooden railing, looking at a boat sailing far below, pine tree branches framing the left, simple contour lines, white background",

            # ================= 【维度 3：季节与环境变换（雪景、秋叶、孤舟）】 =================
            "Chinese line drawing, winter scenery, a scholar in a thick robe looking out a window, snow-covered rooftops, bare tree branches with frost, a single boat stranded in the frozen shallow water, minimalist lines, faint white mist, pure white background, peaceful winter mood",
            "traditional line illustration, an ancient scholar leaning out of a window, a large autumn maple tree with detailed leaf outlines extending into the frame, birds flying in the distance, a fisherman rowing a small skiff, delicate linework, minimalist classic style",
            "traditional Chinese line sketch, a lone scholar standing on a balcony overlooking a misty river, a large crescent moon in the sky, a wooden boat docked at the shore, bamboo branches in the foreground, poetic atmosphere, stark black lines on white background",

            # ================= 【维度 4：建筑形态变化（水榭、长廊、塔楼）】 =================
            "Chinese line drawing, a scholar standing in a long covered waterside corridor, gazing at the calm water, lotus leaves and a small pavilion across the lake, elegant willow branches, flying swallows, clean bamboo outlines, white background, detailed architectural structure",
            "traditional line art, an ancient scholar standing at the bottom of a pagoda on a hill, looking up, plum blossom branches blooming, misty landscape, minimalist contour lines, zen-like tranquility, pure white background",

            # ================= 【维度 5：动作变化（抚琴、持卷、作画）】 =================
            "traditional Chinese line drawing, an ancient scholar in a robe playing a guqin (zither) inside an open pavilion by the lake, tiny waves on the water surface, a solitary crane standing on the shore, wind blowing through the willow trees, elegant and serene mood, crisp linework",
            "traditional line art, a scholar in a study room holding a scroll, pointing at the distant landscape through the window, bookcase filled with ancient books behind him, faint distant mountains, a cup of tea on the desk, light and precise line drawing style",

            # ================= 【维度 6：极致放大细节（白描特写）】 =================
            "close-up traditional Chinese line drawing, half body of a scholar resting his arms on the wooden window frame, intricate details of his robe folds and belt, tree branch with small birds just outside the window, meticulous linework, clean white background, portrait style baimiao art"
        ],
        "styles": [
            "traditional Chinese line drawing, baimiao style, fine contour lines, minimalist black and white",
            "ancient book illustration style, precise ink outlines, clean white paper, detailed architectural lines",
            "classical Chinese sketch, elegant linework, pure white background, uncolored ink art",
            "minimalist line illustration, traditional aesthetic, detailed drapery and tree texture, flowing lines"
        ],
        "moods": [
            "peaceful, poetic, contemplative, tranquil",
            "classical, elegant, nostalgic, zen",
            "breezy, serene, timeless, cultured",
            "melancholic, lonely, deep, introspective"
        ],
        "content_texts": []
    }
}