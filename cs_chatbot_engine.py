import os, json, re, random
from cs_cp_mapping import *

PATIENT_CACHE = None

EMERGENCY_KEYWORDS = [
    "숨이 안 쉬어", "호흡곤란", "가슴통증", "의식이 흐려",
    "쓰러질", "심한 출혈", "피가 멈추지 않아",
    "극심한 통증", "마비", "몸이 움직이지 않아",
    "죽고 싶어", "자해", "출혈이 많아",
    "덩어리", "손바닥보다 큰"
]

WORD_DB = {
    "가": ["가방", "가위", "가스", "가족", "가을", "가사", "가구"],
    "나": ["나무", "나비", "나라", "나이"],
    "다": ["다리", "다이어리", "다이어트", "다람쥐"],
    "라": ["라디오", "라면", "라이터", "라벨"],
    "마": ["마스크", "마음", "마을", "마법", "마늘"],
    "바": ["바다", "바람", "바지", "바나나"],
    "사": ["사과", "사진", "사람", "사탕", "사자"],
    "아": ["아기", "아이", "아침", "안경", "아파트"],
    "자": ["자전거", "자동차", "자석", "자연"],
    "차": ["차량", "차선", "차례"],
    "카": ["카메라", "카드", "카페"],
    "타": ["타이머", "타월", "타이밍"],
    "파": ["파도", "파스타", "파일", "파티"],
    "하": ["하늘", "하나", "하루", "하마"],
    "고": ["고양이", "고기", "고구마", "고래"],
    "노": ["노래", "노트", "노란색", "노트북"],
    "도": ["도서관", "도시", "도넛", "도장"],
    "로": ["로봇", "로켓", "로션"],
    "모": ["모자", "모래", "모니터"],
    "보": ["보호", "보물", "보행기"],
    "소": ["소설", "소금", "소파", "소화기"],
    "오": ["오리", "오이", "오렌지", "오늘"],
    "조": ["조명", "조심", "조각"],
    "초": ["초콜릿", "초밥", "초원"],
    "코": ["코끼리", "코트", "코너"],
    "포": ["포도", "포크", "포장"],
    "호": ["호수", "호랑이", "호박", "호텔"],
    "기": ["기차", "기린", "기사", "기타"],
    "니": ["니트"], "디": ["디지털", "디자인"], "리": ["리본", "리듬", "리모컨"],
    "미": ["미소", "미래", "미역"], "비": ["비누", "비행기", "비밀", "비타민"],
    "시": ["시계", "시장", "시간", "시작"], "이": ["이불", "이야기", "이름", "이빨"],
    "치": ["치약", "치킨", "치마", "치즈"], "티": ["티셔츠", "티켓"],
    "피": ["피아노", "피자", "피리"], "히": ["히터"],
    "수": ["수건", "수박", "수영", "수학"], "우": ["우유", "우산", "우주", "우정"],
    "주": ["주스", "주사", "주말"], "구": ["구두", "구름", "구급차"],
    "두": ["두부", "두통"], "무": ["무지개", "무릎", "무역"],
    "부": ["부엌", "부모", "부채"], "스": ["스포츠", "스트레스"],
    "크": ["크림", "크리스마스"], "트": ["트럭", "트랙"],
    "응": ["응급실", "응원"], "급": ["급식"], "식": ["식사", "식탁", "식물", "식당"],
    "당": ["당근"], "경": ["경찰", "경기", "경치"], "상": ["상처", "상자", "상담"],
    "추": ["추석", "추억", "추천"], "천": ["천사", "천국", "천장"],
    "재": ["재미", "재활"], "통": ["통증"], "증": ["증상"],
    "거": ["거실", "거북이", "거울", "거리"], "지": ["지우개", "지도", "지갑"],
    "철": ["철도"], "학": ["학생", "학교"], "교": ["교실", "교과서"],
    "신": ["신발", "신문", "신호등"], "등": ["등산", "등대"],
    "대": ["대통령", "대기"], "변": ["변호사"], "진": ["진통제"],
    "용": ["용", "용기"], "란": ["란"], "랑": ["랑"],
    "움": ["움"], "울": ["울", "울타리"], "타": ["타이머", "타월"],
}

def rchoice(items):
    return random.choice(list(items)) if isinstance(items, (list, tuple)) else items

def get_last_letter(word):
    if not word: return None
    return word.strip()[-1]

def get_word_starting_with(letter, exclude=None):
    candidates = WORD_DB.get(letter, [])
    if exclude:
        candidates = [w for w in candidates if w != exclude]
    return rchoice(candidates) if candidates else None

def detect_word_chain_game(chat_history):
    if not chat_history or len(chat_history) < 2:
        return None
    for msg in reversed(chat_history):
        if msg["role"] == "bot" and "로 시작" in msg.get("content", ""):
            m = re.search(r"'([^']+)'", msg["content"])
            if not m:
                m = re.search(r"이제\s*'?([가-힣])'?\s*로\s*시작", msg["content"])
            if m:
                return m.group(1)
    return None

def extract_keyword(text):
    text = text.strip()
    return text[:15] if len(text) > 15 else text

def detect_emergency(text):
    t = text.replace(" ", "")
    for kw in EMERGENCY_KEYWORDS:
        if kw.replace(" ", "") in t:
            return True
    return False

EMERGENCY_RESPONSE = "출혈이 많거나 위험 신호가 있다면 바로 확인이 필요합니다. 지금은 혼자 움직이지 말고 즉시 간호사 호출 버튼을 눌러주세요."

def get_patient(index=0):
    global PATIENT_CACHE
    if PATIENT_CACHE is None:
        PATIENT_CACHE = load_patient(index=index)
    return PATIENT_CACHE

def classify_intent(text):
    text = text.lower()

    # ── 위험 증상 (즉시 호출) ──
    danger_severe = ["피가 많이", "출혈 많이", "패드가 금방", "큰 피 덩어리", "덩어리 피",
                     "숨이 안 쉬", "숨참", "숨이 차", "호흡곤란", "가슴통증", "쓰러질",
                     "심한 어지러", "식은땀", "의식이 흐려", "38도", "참기 힘든 복통",
                     "상처가 벌어", "악취 나", "분비물 악취"]
    if any(k in text for k in danger_severe):
        return "emergency"

    # ── 가벼운 출혈 ──
    if any(k in text for k in ["피가 조금", "출혈 조금", "소량 출혈", "피 나와", "피가 나"]):
        return "light_bleeding"

    # ── 어지러움 ──
    if any(k in text for k in ["어지러", "어지럽", "어질어질", "핑 도", "핑 돌"]):
        return "dizziness"

    # ── 게임 요청 ──
    if any(k in text for k in ["끝말잇기", "퀴즈", "놀자", "게임", "밸런스", "스무고개"]):
        return "game_request"

    # ── 심심/잡담 ──
    if any(k in text for k in ["심심", "지루", "말동무", "뭐해", "할 거 없"]):
        return "small_talk"

    # ── 불안/걱정 ──
    if any(k in text for k in ["불안", "걱정", "무서", "두려", "초조", "떨려"]):
        return "anxiety"

    # ── 약/진통제 (통증보다 먼저) ──
    if any(k in text for k in ["진통제", "약 먹", "약 복용", "약 먹어", "투약", "처방"]):
        return "medication"

    # ── 퇴원 관련 (상태 확인보다 먼저) ──
    if any(k in text for k in ["퇴원", "집에 가", "집에가", "집에서", "재방문", "외래",
                                 "퇴원후", "퇴원 후", "집 관리", "조리원", "산후조리원"]):
        return "discharge"

    # ── 상처 ──
    if any(k in text for k in ["상처", "따가워", "따갑", "소독", "드레싱", "흉터", "진물", "붓기", "붓고"]):
        return "wound"

    # ── 통증 ──
    if any(k in text for k in ["아파", "아프", "통증", "배가 아", "배 아", "아랫배", "땡겨", "당겨",
                                 "쑤시", "찌르", "절개", "진통"]):
        return "pain"

    # ── 현재 상태 확인 ──
    if any(k in text for k in ["괜찮", "상태", "어때", "어떻게", "지금 어", "잘 되"]):
        return "recovery_status"

    # ── 식사/물 ──
    if any(k in text for k in ["밥", "식사", "먹어도", "먹어", "금식", "미음", "죽", "식단"]):
        return "meal"
    if any(k in text for k in ["물", "마셔", "마시", "목마르", "수분", "갈증"]):
        return "drink_water"

    # ── 보행/움직임 ──
    if any(k in text for k in ["걷", "걸어", "보행", "일어나", "움직", "화장실 가", "화장실"]):
        return "ambulation"

    # ── 외로움/감정 ──
    if any(k in text for k in ["외로", "힘들", "힘드", "지치", "피곤", "우울", "슬프", "기분"]):
        return "emotional_support"

    # ── 인사 ──
    if any(k in text for k in ["안녕", "반갑", "하이", "hi", "hello", "방가", "여보세요"]):
        return "greeting"

    # ── 감사 ──
    if any(k in text for k in ["고마", "감사", "고맙", "덕분"]):
        return "thanks"

    # ── 기능 문의 ──
    if any(k in text for k in ["뭐 할 수", "무엇을 할", "기능", "도와줘", "도움"]):
        return "what_can_you_do"

    # ── 산후/분만 ──
    if any(k in text for k in ["오로", "출산", "분만", "회음", "자연분만"]):
        return "postpartum"
    if any(k in text for k in ["모유", "수유", "젖", "아기", "유방", "울혈"]):
        return "breastfeeding"

    # ── 산부인과 질환 ──
    if any(k in text for k in ["자궁", "근종", "낭종", "내막증", "골반", "염증"]):
        return "gynecology"

    if len(text) <= 5:
        return "general_health"
    return "general_health"

def get_llm_api_config():
    key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    url = os.environ.get("LLM_API_URL") or "https://api.openai.com/v1/chat/completions"
    model = os.environ.get("LLM_MODEL") or "gpt-4o-mini"
    return key, url, model

def build_system_prompt(character, patient_summary=None, care_phase="inpatient"):
    base = (
        "너는 산부인과 병동에 입원한 환자를 돕는 한국어 케어 챗봇이다.\n"
        "산부인과 환자(자연분만, 제왕절개, 부인과 수술 등)의 회복을 돕는 것이 목적이다.\n\n"
        "반드시 지킬 규칙:\n"
        "- 실제 진단을 확정하지 않는다.\n"
        "- 약 복용, 처방, 치료 결정을 단정하지 않는다.\n"
        "- 응급 증상(심한 출혈, 38도 이상 발열, 심한 통증)은 즉시 의료진 안내한다.\n"
        "- 사용자가 심심하면 실제로 말동무가 되어준다.\n"
        "- 끝말잇기, 퀴즈, 밸런스게임을 요청하면 실제로 진행한다.\n"
        "- 답변은 한국어로 2~5문장 정도로 자연스럽게 한다.\n"
        "- 같은 답변을 반복하지 않는다.\n"
        "- 환자가 이해하기 쉬운 부드러운 말투를 사용한다.\n"
    )
    if care_phase == "inpatient":
        base += "\n사용자는 현재 입원 중이다. 병원 생활, 수술/분만 후 회복, 퇴원 준비에 초점을 맞춰 답변해라."
    elif care_phase == "discharge_ready":
        base += "\n사용자는 곧 퇴원 예정이다. 퇴원 준비, 퇴원 후 생활 안내, 병원 재방문 일정에 초점을 맞춰 답변해라."
    else:
        base += "\n사용자는 퇴원 후 산후관리 중이다. 산후 회복, 수유, 이상 증상 체크, 산후조리, 병원 재방문에 초점을 맞춰 답변해라."

    if character == "heli":
        base += "\n말투: 편한 친구 말투. 반말 사용 가능. 이모지 사용 가능."
    else:
        base += "\n말투: 따뜻한 산부인과 간호사 말투. 존댓말, 부드러운 조언."
    if patient_summary:
        base += f"\n\n환자 정보:\n- 진단명: {patient_summary['진단명']}\n"
        base += f"- 나이: {patient_summary['나이']}세, 분만: {patient_summary['분만종류']}\n"
        if patient_summary.get("재태주수", 0) > 0:
            base += f"- 재태주수: {patient_summary['재태주수']}주\n"
        base += f"- POD{patient_summary['POD']} ({patient_summary['POD단계']})\n"
        base += f"- 통증(VAS): {patient_summary['VAS']}점, 보행: {patient_summary['보행단계']}, 식이: {patient_summary['식이단계']}\n"
        base += f"- 모유수유: {patient_summary.get('모유수유','')}, 상처: {patient_summary.get('상처상태','')}\n"
        base += f"- 담당의: {patient_summary.get('담당의','')}"
    return base

def call_llm(messages, system_prompt):
    key, url, model = get_llm_api_config()
    if not key:
        return None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {"model": model, "messages": [{"role": "system", "content": system_prompt}] + messages, "max_tokens": 500, "temperature": 0.7}
    try:
        import urllib.request
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except:
        return None

def convert_history(chat_history, max_turns=10):
    if not chat_history: return []
    converted = []
    for msg in chat_history[-max_turns:]:
        role = "assistant" if msg["role"] == "bot" else msg["role"]
        converted.append({"role": role, "content": msg["content"]})
    return converted

def _discharge_response(text, s):
    """퇴원 관련 질문에 대한 응답 - 답변 제공 후 자연스럽게 앱 안내"""
    text_lower = text.lower()
    doc = s.get("담당의", "담당 의료진")

    # 위험 증상 언급 시 의료진 확인 우선
    danger_keywords = ["출혈", "피가", "덩어리", "심한 통증", "참을 수 없", "열이", "발열",
                       "38도", "악취", "진물", "붓", "곪", "상처 벌어", "벌어짐"]
    has_danger = any(k in text_lower for k in danger_keywords)

    # 질문 유형별 답변
    if any(k in text_lower for k in ["상처", "소독", "벌어", "붓", "진물", "악취"]):
        base = "상처 부위는 깨끗하게 유지하고, 손으로 자주 만지지 않는 것이 좋아요. 진물, 악취, 심한 붓기, 열감, 상처 벌어짐이 있으면 병원에 연락해야 합니다."
        app_hint = "알려준닥 앱의 회복 체크 기능으로 상처 상태를 매일 기록해둘 수 있어요."

    elif any(k in text_lower for k in ["약", "복용", "처방", "먹"]):
        base = f"퇴원 후 약은 병원에서 안내받은 처방 시간과 용량에 맞춰 복용해야 해요. 임의로 중단하거나 추가 복용하지 말고, 헷갈리면 {doc} 선생님께 확인하는 것이 안전합니다."
        app_hint = "알려준닥 모바일 앱에서 투약 정보와 복용 일정을 함께 확인할 수 있어요."

    elif any(k in text_lower for k in ["재방문", "외래", "일정", "예약"]):
        base = "재방문 일정은 병원에서 안내받은 외래 예약 정보를 기준으로 확인해야 해요. 일정이 헷갈리면 병원 예약 안내를 다시 확인하는 것이 좋습니다."
        app_hint = "알려준닥 모바일 앱에서도 재방문 일정을 관리할 수 있어요."

    elif any(k in text_lower for k in ["조리원", "산후조리원"]):
        base = "산후조리원 이용 가능 여부는 현재 회복 상태와 의료진 안내를 기준으로 결정하는 것이 안전해요. 출혈, 발열, 심한 통증이 있으면 먼저 병원 확인이 필요합니다."
        app_hint = "알려준닥 앱에서 산후조리원 정보와 퇴원 후 회복 관리 가이드를 함께 확인할 수 있어요."

    elif any(k in text_lower for k in ["물어", "물어볼", "질문", "궁금", "계속"]):
        base = "네, 퇴원 후에도 회복 과정에서 궁금한 점이 생길 수 있어요. 통증, 출혈, 상처, 식사, 약 복용처럼 헷갈리는 내용을 계속 확인하실 수 있습니다."
        app_hint = "알려준닥 모바일 앱에서 언제든지 확인하실 수 있어요. 위험 증상이 느껴질 때는 앱 확인보다 병원 연락이 우선이에요."

    elif any(k in text_lower for k in ["집에 가", "집에가", "가도 돼", "가도 되", "언제"]):
        base = f"퇴원 가능 여부는 현재 회복 상태와 {doc} 선생님의 판단에 따라 결정돼요. 통증, 출혈, 식사 가능 여부, 보행 상태 등을 확인한 뒤 안내받는 것이 안전합니다."
        app_hint = "퇴원 후에는 알려준닥 앱에서 회복 상태와 재방문 일정을 이어서 확인할 수 있어요."

    else:
        # 일반 퇴원 질문
        base = "퇴원 후에는 통증, 출혈, 체온, 상처 상태를 매일 확인하는 것이 중요해요. 갑작스러운 출혈, 심한 복통, 38도 이상 발열이 있으면 병원에 바로 연락해야 합니다."
        app_hint = "퇴원 후에도 알려준닥 모바일 앱에서 회복 체크, 투약 정보, 재방문 일정을 계속 관리할 수 있어요."

    # 위험 증상 있으면 의료진 확인을 먼저 강조
    if has_danger:
        return f"{base}\n\n입력하신 증상이 있다면 앱 확인보다 먼저 {doc} 선생님이나 병원에 바로 연락하는 것이 가장 중요해요."

    return f"{base}\n\n{app_hint}"

def fallback_response(text, intent, character="nurse", chat_history=None, patient_index=0):
    row = load_patient(index=patient_index)
    s = get_patient_summary(row)
    pod = s["POD"]
    kw = extract_keyword(text)

    word_chain_next = detect_word_chain_game(chat_history)
    if word_chain_next:
        user_word = text.strip()
        if user_word and len(user_word) > 0 and user_word[0] == word_chain_next:
            last = get_last_letter(user_word)
            bot_word = get_word_starting_with(last, exclude=user_word)
            if bot_word:
                bot_last = get_last_letter(bot_word)
                return f"{bot_word}! 이제 '{bot_last}' 로 시작하는 단어를 말해줘."
            else:
                return f"내가 졌네! ㅎㅎ 다음에 또 하자. {rchoice(['심심하면 또 불러', '재밌었다'])}."
        else:
            return f"아까 '{word_chain_next}' (으)로 시작하는 단어를 말해야 해. 다시 해볼까?"

    if intent == "game_request":
        word = get_word_starting_with("사")
        if word and "끝말잇기" in text:
            last = get_last_letter(word)
            return f"좋아, 끝말잇기 시작! 내가 먼저 할게. {word}! 이제 '{last}' 로 시작하는 단어를 말해줘."
        return rchoice(["좋아! 끝말잇기, 퀴즈, 밸런스게임 중에 뭐 할래?", "게임 고고! 끝말잇기 도전할래?"])

    if intent == "small_talk":
        return rchoice([
            "심심했구나. 끝말잇기, 퀴즈, 밸런스게임 중에 뭐 할래? 내가 말동무 해줄게.",
            "아이고 심심하셨군요. 제가 말동무가 되어드릴게요. 끝말잇기 한판 할까요?",
            "심심하면 나랑 놀자! 하고 싶은 이야기 있으면 편하게 말해줘.",
        ])

    if intent == "breastfeeding":
        if row.get("유방울혈", "무") == "유":
            return "유방이 울혈된 상태군요. 따뜻한 수건으로 찜질하거나 샤워 후 유축을 시도해보세요. 통증이 심하면 의료진에게 알려주세요."
        if row.get("모유수유", "유") == "유":
            return "모유수유 중이시군요! 수유 전에는 손을 깨끗이 씻고, 아기가 정확히 물도록 도와주세요. 젖몸살이 의심되면 바로 말씀해주세요."
        return "모유수유에 대해 궁금하시군요. 수유 자세, 횟수, 유축 방법 등 무엇이든 물어보세요."

    if intent == "postpartum":
        if s.get("분만종류") == "자연분만":
            return f"자연분만 후 회복 중이시군요. 오로는 '{s.get('오로양','')}' 상태이며, 회음부 통증이 있으면 좌욕이 도움됩니다. 충분한 휴식과 수분 섭취가 중요해요."
        return "산후 회복에 대해 궁금하시군요. 오로 양, 회음부 관리, 골반 회복 등 무엇이든 물어보세요."

    if intent == "gynecology":
        ptype = s.get("진단명", "")
        return f"현재 '{ptype}'으로 입원 중이세요. 수술 후 회복 단계이며, 궁금하신 점 편하게 물어보세요."

    if intent == "pregnancy":
        return "임신 중 관리에 대해 궁금하시군요. 정기 검진, 영양 관리, 운동 등 어떤 부분이 궁금하신가요?"

    nurse_t = {
        "greeting": f"안녕하세요, OOO님. 알려준닥입니다. 현재 {s['진단명']} 수술 후 {s['POD']}일차 회복 관리 중이에요. 통증, 식사, 보행, 상처 관리처럼 궁금한 점을 편하게 물어보세요.",

        "pain": "수술 후 {0}일차에는 아랫배나 수술 부위가 당기고 아플 수 있어요. 움직일 때 통증이 느껴지면 무리하지 말고 천천히 움직이는 게 좋아요. 통증이 갑자기 심해지거나 출혈, 어지러움이 같이 있으면 바로 알려주세요.".format(s['POD']),

        "wound": "수술 부위가 따갑거나 당기는 느낌은 회복 중에 생길 수 있어요. 상처 부위는 손으로 자주 만지지 말고 깨끗하게 유지하는 것이 중요합니다. 진물, 심한 붓기, 열감, 악취가 있으면 바로 확인이 필요해요.",

        "meal": f"현재 OOO님의 식이 상태는 '{s['식이단계']}'이에요. 아직은 임의로 음식을 드시지 않는 것이 좋아요. 식사가 시작되면 보통 물이나 미음처럼 부담이 적은 것부터 천천히 진행됩니다.",

        "drink_water": "현재 식이 상태가 금식이라 물도 아직은 조심해야 해요. 수술 후 장운동이나 상태에 따라 물부터 시작할 수 있습니다. 지금은 입이 마르면 입안을 적시는 정도로 관리하는 것이 좋아요.",

        "ambulation": "현재 보행 상태는 복도걷기로 표시되어 있어요. 짧게 걷는 것은 회복에 도움이 될 수 있습니다. 처음 일어날 때는 어지러울 수 있으니 천천히 앉았다가 일어나고, 무리하지 않는 선에서 움직여 주세요.",

        "bathroom": "먼저 침대에서 천천히 일어나 앉은 뒤 어지러운지 확인해 주세요. 괜찮다면 천천히 이동하면 됩니다. 어지럽거나 힘이 빠지는 느낌이 있으면 혼자 움직이지 않는 게 좋아요.",

        "light_bleeding": "수술 후 회복 과정에서 소량의 출혈이 보일 수 있어요. 양이 늘어나는지, 색이 진해지는지, 어지러움이 같이 있는지 확인해 주세요. 갑자기 많아지지 않는다면 상태를 지켜보면서 기록해두면 좋아요.",

        "dizziness": "수술 후에는 일어날 때 어지러움을 느낄 수 있어요. 지금은 바로 걷지 말고 침대에 앉거나 누워서 잠시 쉬어주세요. 어지러움이 심하거나 식은땀, 출혈이 함께 있으면 즉시 호출이 필요합니다.",

        "medication": "진통제는 처방된 시간과 용량에 맞춰 복용하는 것이 좋아요. 이미 복용한 약이 있다면 추가 복용은 간격을 확인해야 합니다. 알려준닥 투약 정보에서 복용 시간과 약 정보를 확인할 수 있어요.",

        "recovery_status": f"현재 기록상으로는 {s['진단명']} 수술 후 {s['POD']}일차 회복 관리 중으로 표시되어 있어요. 통증이 조금 있거나 몸이 무거운 느낌은 회복 과정에서 나타날 수 있습니다. 출혈이 많아지거나 열, 심한 복통이 없다면 무리하지 않고 회복 상태를 지켜보면 좋아요.",

        "discharge": _discharge_response(text, s),

        "anxiety": "수술 후에는 몸 상태가 평소와 달라서 불안하게 느껴질 수 있어요. 지금처럼 궁금한 점을 하나씩 확인하면서 관리하면 도움이 됩니다. 알려준닥이 회복 과정에서 필요한 내용을 쉽게 안내해드릴게요.",

        "thanks": f"천천히 회복하시면 됩니다, OOO님. 불편한 점이 생기면 언제든지 알려준닥에 물어보세요. 퇴원 후에도 모바일 앱에서 회복 상태와 일정을 이어서 관리할 수 있어요.",

        "emotional_support": "입원 중에는 몸도 마음도 평소와 달라 힘들 수 있어요. 지금처럼 궁금한 점이 있으면 편하게 물어보시고, 무리하지 않는 선에서 하루하루 회복에 집중하는 게 좋아요.",

        "what_can_you_do": "알려준닥이 도와드릴 수 있는 것들:\n* 통증, 상처, 수유 관리\n* 보행, 식이, 퇴원 안내\n* 분만 후 회복 관리\n* 부인과 수술 후 관리\n* 투약 정보 확인\n* 감정 케어와 불안 완화",

        "general_health": f"현재 회복 상태를 요약해드릴게요.\n* 진단: {s['진단명']}\n* POD{s['POD']} ({s['POD단계']})\n* 통증 VAS {s['VAS']}점\n* 보행: {s['보행단계']}, 식이: {s['식이단계']}\n* 담당의: {s.get('담당의','')}\n\n궁금하신 점 편하게 물어보세요!",
    }

    return nurse_t.get(intent, nurse_t["general_health"])


def chat(text, character="nurse", chat_history=None, patient_index=0, care_phase="inpatient"):
    if detect_emergency(text):
        return EMERGENCY_RESPONSE, "emergency"
    intent = classify_intent(text)
    if intent == "emergency":
        return EMERGENCY_RESPONSE, "emergency"

    row = load_patient(index=patient_index)
    s = get_patient_summary(row)

    key, url, model = get_llm_api_config()
    if key:
        sp = build_system_prompt(character, s, care_phase)
        conv = convert_history(chat_history)
        conv.append({"role": "user", "content": text})
        llm_r = call_llm(conv, sp)
        if llm_r:
            return llm_r, intent

    return fallback_response(text, intent, character, chat_history, patient_index), intent
