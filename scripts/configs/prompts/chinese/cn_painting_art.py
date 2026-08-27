# prompts/cn_painting_art.py
# 中国传统珍贵字画 高清质感还原
# 包含：水墨山水、书法、古画、古籍

STYLE = {
    "cn_painting_art": {
        "folder": "珍贵字画_国风",
        "strength": 0.35,
        "subjects": [
            # --- 水墨山水画 ---
            "ultra-realistic macro photography of an antique Chinese landscape painting, black ink on rice paper, misty mountains, flowing waterfalls, ancient pine trees, traditional xuan paper texture, slight yellowing from age, red seal stamps, museum archival quality",
            "Song dynasty style mountain and water painting, majestic peaks, ink wash technique, subtle brush strokes, delicate details, aged calligraphy, pure white background, high-definition heritage art",
            "traditional Chinese ink brush painting of a bamboo grove, graceful bamboo stalks and leaves, dark ink on aged paper, multiple red signature seals, historical artwork, macro studio shot, 8k",
            
            # --- 书法长卷 ---
            "ancient Chinese calligraphy scroll, flowing cursive script, powerful brush strokes, large horizontal composition, aged rice paper, red ink stamps in corners, masterpiece cultural relic, studio lighting, pure white background",
            "Zhang Xu cursive calligraphy, dramatic ink splashes, chaotic yet balanced brushwork, authentic xuan paper texture, aged materials, archival preservation photograph, museum quality",
            "imperial Qing dynasty calligraphy, elegant standard script, gold leaf on dark blue paper, magnificent imperial seals, stunning cultural heritage, 8k high-resolution scan aesthetic",
            
            # --- 古籍与线装书 ---
            "antique thread-bound Chinese book, yellowed rice paper pages, traditional vertical layout, black ink characters, leather-bound cover, aged intricate details, historical relic photography, macro detail, pure white background",
            "Ming dynasty woodblock printed manuscript, classical text, fine black ink, aged and fragile paper, ancient binding, document preservation photograph, masterpiece heritage art",
            
            # --- 工笔/仕女/花鸟 ---
            "ancient Chinese Gongbi painting, detailed bird and flower, fine intricate lines, vivid mineral colors, aged silk texture, red seals, traditional masterpiece, museum exhibition art, high definition",
            "Tang dynasty style painting of a beautiful court lady, elegant flowing robes, fine brushwork, subtle colors, aged silk tapestry, historical scroll artwork, ancient art preservation"
        ],
        "styles": [
            "ultra-realistic macro archival photography, historic paper texture, aged and weathered aesthetic, museum lighting",
            "masterpiece ancient art documentation, traditional ink and brush, aged xuan paper, red seal details",
            "high-fidelity cultural relic photography, 8k, intricate brush strokes, authentic aging details"
        ],
        "moods": [
            "ancient, majestic, peaceful, scholarly",
            "elegant, historical, cultured, timeless",
            "artistic, delicate, traditional, refined"
        ],
        "content_texts": [] 
    }
}