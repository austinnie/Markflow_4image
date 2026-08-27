# tools/prompts_new/medical_professional_nurse.py
# 白衣天使 - 医疗制服人像

STYLE = {
    "medical_professional_nurse": {
        "folder": "医疗制服_白衣天使",
        "strength": 0.35,
        "subjects": [
            # ================= 【维度 1：基础还原（护士帽、白衣、低头/交谈）】 =================
            "realistic portrait, beautiful asian woman, black hair in a bun under a white nurse cap, wearing a fitted white nurse uniform with a deep V-neck, standing in a bright modern hospital office, looking down gently, one hand touching her collar, soft natural lighting, aesthetic medical photography",
            "realistic photography, cute asian nurse, black hair pinned up, white nurse cap, white short-sleeved nurse dress with front buttons, standing face to face with a patient, speaking gently, hospital room background with computers, bright and professional atmosphere",

            # ================= 【维度 2：增加职业配件（听诊器、记录板、口罩）】 =================
            "realistic portrait, elegant asian female doctor, black hair tied back, white medical coat with deep V-neck, a stethoscope hanging around her neck, holding a medical chart in her hand, standing in a bright hospital corridor, looking at the camera with a gentle smile, clinical lighting",
            "realistic photo, beautiful nurse, black hair up, white nurse cap and uniform, wearing a white surgical mask, holding a clipboard and pen, writing a medical record, standing at a hospital nursing station, bright fluorescent lighting, professional and focused",
            "realistic photography, gentle asian nurse, black hair, white deep V-neck nurse dress, carrying a metal medical tray with syringes and medicine, walking down a clean hospital hallway, soft light from the window, confident posture",

            # ================= 【维度 3：空间与动作变化（病房、推车、窗边）】 =================
            "realistic lifestyle portrait, caring asian nurse, black hair in a bun, white nurse cap, fitted white uniform, bending slightly to adjust an IV drip in a patient's room, soft natural light, caring expression, hospital bedside scene, highly detailed",
            "realistic photo, beautiful nurse, black hair tied up, white deep V-neck medical uniform, leaning against a hospital window, looking out at the city view, holding a coffee cup, relaxed and beautiful, afternoon sunlight",
            "realistic photography, asian nurse, black hair, white cap and dress, pushing a medical cart down the hospital hallway, dynamic walking motion, blurred background, clean and modern healthcare environment",

            # ================= 【维度 4：职业装扮变体（白大褂、刷手服、药剂师）】 =================
            "realistic portrait, attractive asian female doctor, black hair loosely tied, wearing a white lab coat over a deep V-neck top, holding a stethoscope, standing in a modern laboratory, confident expression, bright and clean science environment",
            "realistic photo, cute asian medical worker, black hair in a ponytail, wearing blue surgical scrubs and a white nurse cap, holding surgical gloves, standing in a pre-op preparation room, professional and serious atmosphere, soft fluorescent light",
            "realistic lifestyle photography, elegant asian pharmacist, black hair in a low bun, wearing a white deep V-neck nurse-style uniform, standing behind a pharmacy counter, holding a bottle of medicine, smiling at the camera, natural daylight from a shop window",

            # ================= 【维度 5：光影与情绪变化（夕阳、雨天、特写）】 =================
            "cinematic portrait, beautiful asian nurse, black hair in a nurse cap, white V-neck dress, standing in an empty hospital corridor during golden hour, warm sunset light streaming through the window, serene and emotional mood, dreamy atmosphere",
            "close-up portrait, caring nurse, black hair, white uniform, wearing a stethoscope, looking down gently and thoughtfully, clean white hospital background, diffused soft light, highly detailed face and skin texture, medical aesthetic"
        ],
        "styles": [
            "realistic portrait photography, clean bright aesthetic, natural makeup, beautiful skin texture",
            "professional medical lifestyle photography, soft lighting, clinical atmosphere",
            "cinematic drama portrait, shallow depth of field, clear and pure colors",
            "highly detailed photography, realistic fabric folds, soft outdoor/indoor light"
        ],
        "moods": [
            "gentle, caring, professional, elegant",
            "confident, intelligent, compassionate",
            "focused, dedicated, warm, serene",
            "beautiful, clean, clinical, high-end"
        ],
        "content_texts": []
    }
}