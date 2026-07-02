import pandas as pd

DATA_PATH = "data/OB_GYN_DATA.csv"

def load_patient(patient_id=None, index=0):
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    if patient_id:
        row = df[df["환자ID"] == patient_id].iloc[0]
    else:
        row = df.iloc[index]
    return row.to_dict()

def get_pod_stage(pod):
    stages = {
        0: "수술/분만 당일",
        1: "1일차",
        2: "2일차",
        3: "3일차",
        4: "4일차",
        5: "5일차"
    }
    return stages.get(pod, f"{pod}일차")

def get_vas_level(vas):
    if vas <= 3: return "경도"
    elif vas <= 6: return "중등도"
    else: return "심함"

def get_ambulation_guide(pod, current_amb, ptype):
    if ptype in ["산전관리"]:
        return "정상 보행 가능합니다. 가벼운 운동을 권장해요."
    if ptype == "자연분만":
        guides = {
            0: "분만 직후라 침상 안정이 필요해요. 화장실은 도움을 받아 다녀오세요.",
            1: "방 안을 천천히 걸어보세요. 회음부 통증이 있으면 무리하지 마세요.",
            2: "복도까지 걸어보세요. 점차 활동량을 늘려가세요."
        }
        return guides.get(pod, "일상 보행 가능합니다.")
    guides = {
        0: "수술 당일은 침상 안정이 필요해요. 침대에서 발목 운동만 해주세요.",
        1: "침대 옆에 앉는 연습부터 시작하세요. 어지러우면 바로 누워주세요.",
        2: "방 안을 천천히 걸어보세요. 처음에는 5분만 시도하세요.",
        3: "복도까지 걸어보세요. 보행기 사용이 필요하면 요청하세요.",
        4: "자유롭게 보행하셔도 좋아요. 무리하지 않는 선에서 활동하세요.",
        5: "일상 보행 가능합니다. 퇴원 준비 단계예요."
    }
    return guides.get(pod, "의료진 지시에 따라 보행해주세요.")

def get_diet_guide(pod, ptype):
    if ptype in ["산전관리"]:
        return "균형 잡힌 일반식 드세요. 철분과 엽산 보충이 중요해요."
    if ptype == "자연분만":
        guides = {
            0: "일반식 드셔도 됩니다. 수분을 충분히 섭취하세요.",
            1: "영양가 있는 식사로 회복을 도와주세요. 모유수유 중이라면 더 충분히 드세요.",
            2: "일반식 자유롭게 드세요."
        }
        return guides.get(pod, "일반식 드세요.")
    guides = {
        0: "금식 또는 미음 단계입니다. 방귀가 나오면 식이 진행이 가능합니다.",
        1: "미음 또는 죽 단계입니다. 부드러운 음식부터 시작하세요.",
        2: "죽 또는 연식 단계입니다. 자극적이지 않은 음식을 선택하세요.",
        3: "연식 이상 가능합니다. 수유 중이라면 영양가 있는 식사가 중요해요.",
        4: "일반식 가능합니다. 변비 예방을 위해 채소와 수분을 충분히 섭취하세요.",
        5: "일반식 자유롭게 드셔도 됩니다."
    }
    return guides.get(pod, "의료진 지시에 따라 식사해주세요.")

def get_pain_killer_guide(killer):
    guides = {
        "NSAID": "비스테로이드성 소염진통제를 사용 중입니다. 통증이 심하면 추가 요청하세요.",
        "마약성진통제": "마약성 진통제를 사용 중입니다. 어지러움, 메스꺼움 있으면 말씀해주세요.",
        "둘다": "NSAID와 마약성 진통제를 병용 중입니다. 통증 조절이 잘 안 되면 알려주세요.",
        "없음": "현재 진통제를 사용하지 않고 있습니다. 통증이 생기면 말씀해주세요."
    }
    return guides.get(killer, "진통제 정보를 확인할 수 없습니다.")

def assess_recovery_status(row):
    ptype = row.get("진단명", "")
    pod = int(row.get("POD", 0))
    vas = int(row.get("VAS", 0))
    wound = row.get("상처상태", "깨끗")
    temp = float(row.get("Temp", 36.5))
    epds = int(row.get("EPDS", 0))

    issues = []
    is_urgent = False

    if vas >= 7:
        issues.append(f"통증 점수 {vas}점으로 심한 통증 상태입니다.")
    if wound in ["발적심함", "분비물"] and ptype not in ["자연분만", "산전관리"]:
        issues.append(f"상처 부위에 이상이 있습니다 ({wound}).")
        is_urgent = True
    if temp >= 38.0:
        issues.append(f"체온 {temp}도로 발열 상태입니다.")
        is_urgent = True
    if epds >= 13:
        issues.append("산후 우울감이 의심됩니다. 마음이 힘드시면 간호사에게 말씀해주세요.")

    recovery_level = "양호"
    if is_urgent:
        recovery_level = "주의"
    elif len(issues) > 0:
        recovery_level = "관찰필요"

    return recovery_level, issues, is_urgent

def get_patient_summary(row):
    pod = int(row.get("POD", 0))
    ptype = row.get("진단명", "")
    return {
        "환자ID": row.get("환자ID", ""),
        "이름": row.get("이름", ""),
        "나이": int(row.get("나이", 0)),
        "진단명": ptype,
        "분만종류": row.get("분만종류", ""),
        "재태주수": int(row.get("재태주수", 0)),
        "BMI": float(row.get("BMI", 0)),
        "수술종류": row.get("수술종류", ""),
        "마취방법": row.get("마취방법", ""),
        "POD": pod,
        "POD단계": get_pod_stage(pod),
        "VAS": int(row.get("VAS", 0)),
        "통증정도": get_vas_level(int(row.get("VAS", 0))),
        "보행단계": row.get("보행단계", ""),
        "보행가이드": get_ambulation_guide(pod, row.get("보행단계", ""), ptype),
        "식이단계": row.get("식이단계", ""),
        "식이가이드": get_diet_guide(pod, ptype),
        "SBP": int(row.get("SBP", 0)),
        "DBP": int(row.get("DBP", 0)),
        "HR": int(row.get("HR", 0)),
        "Temp": float(row.get("Temp", 36.5)),
        "모유수유": row.get("모유수유", ""),
        "유방울혈": row.get("유방울혈", ""),
        "EPDS": int(row.get("EPDS", 0)),
        "수면질": row.get("수면질", ""),
        "상처상태": row.get("상처상태", ""),
        "진통제": row.get("진통제", ""),
        "오로양": row.get("오로양", ""),
        "도뇨관": row.get("도뇨관", ""),
        "방귀": row.get("방귀", ""),
        "입원일수": int(row.get("입원일수", 3)),
        "담당의": row.get("담당의", ""),
        "진통제가이드": get_pain_killer_guide(row.get("진통제", "")),
        "회복상태": assess_recovery_status(row)
    }
