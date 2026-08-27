# prompts/calligraphy_art.py
# 名贵字画风格 - 优雅书香，字画意境，佛经展示

STYLE = {
    "calligraphy_art": {
        "folder": "名贵字画",
        "strength": 0.35,
        
        # ==================== 主体 (24种) ====================
        "subjects": [
            # ----- 书法字画 (12种) -----
            "masterpiece calligraphy art, ancient Chinese scroll hanging on wall, powerful brush strokes, elegant ink calligraphy, meaningful Chinese characters, scholarly atmosphere, exquisite mounting, traditional xuan paper texture, artistic seal stamps",
            "beautiful Chinese calligraphy on rice paper, motivational ancient poem, flowing cursive script, imperial style, hanging scroll, wooden roller, elegant presentation, profound wisdom, inspirational words",
            "framed calligraphy artwork, bold brushwork, Chinese idiom about perseverance and success, hanging in elegant study room, refined taste, scholarly ambiance, artistic expression, cultural heritage",
            "ancient Chinese calligraphy masterpiece, famous poem by Li Bai, dynamic ink strokes, traditional mounting, hanging on bamboo scroll, scholarly atmosphere, timeless beauty, cultural treasure",
            "Buddhist sutra calligraphy, Heart Sutra written in elegant script, golden ink on dark paper, peaceful and serene, hanging in meditation room, spiritual ambiance, divine presence, sacred text",
            "Diamond Sutra calligraphy, exquisite brushwork, classical Chinese characters, hanging scroll with silk mounting, temple atmosphere, spiritual energy, ancient wisdom, Buddhist art",
            "motivational calligraphy, four-character idiom, powerful and inspiring message, bold ink strokes, hanging in office or study, professional ambiance, success motivation, daily inspiration",
            "Chinese poem calligraphy, Tang dynasty poetry, elegant running script, beautiful composition, hanging scroll with brocade mounting, scholarly atmosphere, poetic beauty, literary treasure",
            "ancient Chinese prose calligraphy, classical text, refined brushwork, traditional hanging scroll, library or study setting, intellectual atmosphere, cultural elegance, timeless wisdom",
            "Buddhist mantra calligraphy, Om Mani Padme Hum in elegant script, spiritual energy, Tibetan influence, hanging in peaceful shrine room, sacred atmosphere, meditation focus, divine blessing",
            "Ksitigarbha Sutra calligraphy, earth store bodhisattva teachings, golden ink on dark blue paper, compassionate wisdom, hanging in temple hall, profound spiritual energy, sacred Buddhist text",
            "Lotus Sutra calligraphy, wonderful dharma teachings, elegant script, golden characters, Buddhist art masterpiece, hanging in grand temple, divine radiance, profound wisdom",
            
            # ----- 环境场景 (12种) -----
            "elegant study room, antique wooden desk, traditional Chinese calligraphy tools, ink stone, brush holder, rice paper, hanging scrolls on wall, refined atmosphere, scholarly elegance, warm lighting, peaceful ambiance",
            "traditional Chinese tea room, wooden tea table, tea set, hanging calligraphy scrolls, bamboo blinds, zen atmosphere, peaceful and quiet, scholarly retreat, meditation space, cultural elegance",
            "ancient Chinese library, wooden bookshelves filled with classical books, hanging calligraphy artworks, scholarly ambiance, warm lantern light, intellectual retreat, traditional architecture, literary haven",
            "Buddhist temple study, altar with Buddha statue, incense burner, hanging sutra calligraphy, spiritual atmosphere, peaceful sanctuary, meditation space, sacred ambiance, zen garden view",
            "elegant calligraphy studio, master calligrapher at work, brush in hand, ink on paper, artistic atmosphere, creative energy, traditional setting, scholar's retreat, cultural heritage",
            "zen meditation room, tatami mats, hanging zen calligraphy, simple and minimalist, peaceful atmosphere, natural light, bamboo elements, mindfulness space, spiritual sanctuary",
            "traditional Chinese scholar's study, antique furniture, calligraphy wall scrolls, ceramic tea set, bamboo curtain, serene atmosphere, intellectual pursuit, cultural refinement, timeless elegance",
            "Buddhist shrine room, golden Buddha statue, incense smoke, hanging sutra scrolls, peaceful ambiance, devotional space, spiritual energy, sacred art, meditation focus",
            "elegant art gallery, Chinese calligraphy exhibition, framed artworks on white walls, soft gallery lighting, refined atmosphere, cultural appreciation, artistic journey, masterpiece showcase",
            "peaceful garden pavilion, outdoor calligraphy display, stone tablets with inscriptions, nature surroundings, serene atmosphere, scholarly retreat, cultural landscape, harmonious setting",
            "grand temple hall, golden Buddha statues, hanging sutra scrolls on pillars, sacred atmosphere, chanting energy, Buddhist temple interior, divine radiance, spiritual sanctuary",
            "monastic library, ancient sutra manuscripts, wooden shelves, calligraphy tools, scholarly monk at work, peaceful atmosphere, wisdom preservation, Buddhist culture"
        ],
        
        # ==================== 风格 (10种) ====================
        "styles": [
            "traditional Chinese ink painting style, xuan paper texture, soft ink tones, elegant brushwork",
            "ancient scroll style, aged paper, subtle yellowing, traditional mounting, brocade borders",
            "golden ink on dark paper, luxurious calligraphy style, divine radiance, Buddhist art aesthetic",
            "classical Chinese painting style, ink wash technique, refined brushwork, scholarly elegance",
            "ancient manuscript style, rice paper, traditional seals, red ink stamps, authentic appearance",
            "temple mural style, sutra writing, sacred geometry, divine presence, Buddhist art",
            "minimalist zen style, simple calligraphy, negative space, peaceful composition, meditation art",
            "imperial court style, ornate mounting, yellow silk brocade, royal elegance, prestigious art",
            "elegant literati style, scholarly refinement, bamboo and plum motifs, intellectual art",
            "classical album leaf style, fan-shaped mounting, delicate brushwork, collector's item"
        ],
        
        # ==================== 情绪 (8种) ====================
        "moods": [
            "peaceful and meditative",
            "inspiring and motivational", 
            "elegant and refined",
            "serene and spiritual",
            "profound and wise",
            "calm and contemplative",
            "majestic and awe-inspiring",
            "gentle and harmonious"
        ],
        
        # ==================== 经典佛经句子 (50+条) ====================
        "content_texts": [
            # ----- 地藏经 (Ksitigarbha Sutra) -----
            "地狱不空，誓不成佛。众生度尽，方证菩提。",
            "南无大愿地藏王菩萨，大慈大悲，救苦救难。",
            "地藏菩萨，安忍不动如大地，静虑深密如秘藏。",
            "一切众生，未解脱者，性识无定，恶习结业，善习结果。",
            "阎浮众生，举止动念，无不是业，无不是罪。",
            "南无地藏王菩萨，普度众生，超拔苦难。",
            "地藏菩萨本愿经，孝道度亲，大愿普度众生。",
            "众生度尽，方证菩提；地狱未空，誓不成佛。",
            "地藏大愿，慈悲无尽，救度一切苦难众生。",
            "吾观地藏威神力，恒河沙劫说难尽。",
            
            # ----- 妙法莲华经 (Lotus Sutra) -----
            "诸法从本来，常自寂灭相。佛子行道已，来世得作佛。",
            "妙法莲华，微妙第一，佛法中最，稀有难遇。",
            "三界无安，犹如火宅，众苦充满，甚可怖畏。",
            "以一灯传诸灯，终至万灯皆明。",
            "诸佛世尊，唯以一大事因缘故，出现于世。",
            "开示悟入，佛之知见，皆令众生，入佛知见。",
            "法华经中，佛说一乘，普度众生，皆成佛道。",
            "如来善巧，方便说法，随其根性，皆令欢喜。",
            "妙法莲花经，成佛之妙法，稀有难逢，万劫难遇。",
            "佛告舍利弗，诸佛如来，但教化菩萨，诸有所作，常为一事。",
            
            # ----- 心经 (Heart Sutra) -----
            "色不异空，空不异色，色即是空，空即是色。",
            "心无挂碍，无挂碍故，无有恐怖，远离颠倒梦想。",
            "照见五蕴皆空，度一切苦厄。",
            "般若波罗蜜多，是大神咒，是大明咒，是无上咒。",
            "三世诸佛，依般若波罗蜜多故，得阿耨多罗三藐三菩提。",
            "无智亦无得，以无所得故，菩提萨埵。",
            
            # ----- 金刚经 (Diamond Sutra) -----
            "应无所住，而生其心。",
            "凡所有相，皆是虚妄。若见诸相非相，即见如来。",
            "一切有为法，如梦幻泡影，如露亦如电，应作如是观。",
            "若以色见我，以音声求我，是人行邪道，不能见如来。",
            "过去心不可得，现在心不可得，未来心不可得。",
            "如来者，无所从来，亦无所去，故名如来。",
            
            # ----- 禅宗经典 -----
            "菩提本无树，明镜亦非台。本来无一物，何处惹尘埃。",
            "不是风动，不是幡动，仁者心动。",
            "平常心是道。",
            "明心见性，见性成佛。",
            "不立文字，教外别传，直指人心，见性成佛。",
            "青青翠竹，尽是法身。郁郁黄花，无非般若。",
            
            # ----- 净土宗 -----
            "南无阿弥陀佛，大慈大悲，接引众生往生净土。",
            "愿生西方净土中，九品莲花为父母。",
            "四十八愿度众生，九品咸令登彼岸。",
            "阿弥陀佛，无量光寿，度化众生，同归极乐。",
            
            # ----- 其他经典 -----
            "缘起性空，一切法无常。",
            "诸恶莫作，众善奉行，自净其意，是诸佛教。",
            "慈悲喜舍，四无量心，普度众生。",
            "佛说一切法，为度一切心。若无一切心，何须一切法。",
            "一花一世界，一叶一如来。",
            "大悲无泪，大悟无言，大笑无声。",
            "人成即佛成，是名真现实。",
            "华藏世界，重重无尽，一多相即，大小相容。",
            "发菩提心，深信因果，读诵大乘，劝进行者。",
            "如是我闻，一时佛在，说法度生，皆大欢喜。"
        ]
    }
}