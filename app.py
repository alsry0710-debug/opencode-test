import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import date, timedelta
from cs_chatbot_engine import chat as cs_chat
from cs_cp_mapping import load_patient, get_patient_summary, assess_recovery_status

st.set_page_config(page_title="알려준닥", page_icon="💗", layout="wide")

if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = 0
if "messages" not in st.session_state:
    st.session_state.messages = []
if "page" not in st.session_state:
    st.session_state.page = "chat"

def is_near_discharge(s):
    remaining = max(0, s.get("입원일수", 5) - s.get("POD", 0))
    return remaining <= 2

row = load_patient(index=st.session_state.selected_patient)
s = get_patient_summary(row)
rec_level, rec_issues, rec_urgent = assess_recovery_status(row)
remaining_days = max(0, s.get("입원일수", 5) - s.get("POD", 0))
is_d2 = remaining_days <= 2

st.markdown("""
<style>
[data-testid="stSidebar"]{background:#fdf2f8}
[data-testid="stSidebar"] *{color:#831843!important}
.sb-brand{font-size:20px;font-weight:800;color:#be185d!important;padding:8px 0}
.sb-phase{font-size:11px;color:#db2777!important;padding:2px 0 12px;border-bottom:1px solid #f9a8d4;margin-bottom:8px}
.sb-menu{margin:16px 0 6px;font-size:11px;font-weight:700;color:#9d174d!important;letter-spacing:1px}
.sb-item{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:7px;font-size:13px;margin:1px 0;cursor:pointer;color:#831843!important}
.sb-item.on{background:#fbcfe8;color:#9d174d!important;font-weight:600}
.sb-item:hover{background:#fce7f3}
.sb-f{text-align:center;font-size:10px;color:#be185d!important;margin-top:auto;padding:16px 0}
.sb-pt{background:#fce7f3;border:1px solid #f9a8d4;border-radius:10px;padding:14px;margin:8px 0}
.sb-pt .n{font-size:17px;font-weight:700;color:#9d174d!important}
.sb-pt .m{font-size:11px;color:#be185d!important}
.sb-pt .v{font-size:11px;color:#db2777!important;margin-top:6px;display:flex;flex-wrap:wrap;gap:4px 12px}
.sb-badge{font-size:10px;padding:2px 7px;border-radius:8px;font-weight:600}
.badge-ok{background:#d1fae5;color:#065f46!important}
.badge-warn{background:#fef3c7;color:#92400e!important}
.badge-danger{background:#fee2e2;color:#991b1b!important}
.sb-doc{font-size:11px;color:#be185d!important;margin-top:4px;padding:6px 0}
.sb-doc span{font-weight:600;color:#9d174d!important}

/* 앱 소개 */
.app-card{background:#fff;border-radius:14px;padding:20px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,0.06);border:1px solid #fce7f3;margin-bottom:12px}
.app-card h4{color:#9d174d;margin:10px 0 6px}
.app-card p{font-size:12px;color:#888}
.info-box{background:#fdf2f8;border:1px solid #f9a8d4;color:#9d174d;padding:16px;border-radius:12px;margin:12px 0}

/* 실제 음성 버튼은 화면 밖으로 숨김 */
div.st-key-voice_input{
    position:fixed!important;left:-10000px!important;top:-10000px!important;
    width:1px!important;height:1px!important;opacity:0!important;pointer-events:auto!important
}
/* 텍스트가 버튼과 겹치지 않게 */
[data-testid="stChatInput"] textarea{padding-right:80px!important}
</style>
""", unsafe_allow_html=True)

# ── 사이드바 ──
with st.sidebar:
    st.markdown(f"""
    <div class="sb-brand">알려준닥</div>
    <div class="sb-phase">입원 중 케어</div>
    """, unsafe_allow_html=True)

    badge_class = {"양호": "badge-ok", "관찰필요": "badge-warn", "주의": "badge-danger"}
    ptype = s.get("진단명", "")
    if ptype == "산전관리":
        info_line = f"임신 {s['재태주수']}주"
        info_tags = f"<span>{s['분만종류']}</span>"
    elif ptype == "자연분만":
        info_line = f"POD{s['POD']} ({s['POD단계']})"
        info_tags = f"<span>통증 {s['VAS']}점</span><span>보행 {s['보행단계']}</span><span>식이 {s['식이단계']}</span><span>수유 {'O' if s['모유수유']=='유' else 'X'}</span>"
    else:
        info_line = f"{ptype} · POD{s['POD']} ({s['POD단계']})"
        info_tags = f"<span>통증 {s['VAS']}점</span><span>보행 {s['보행단계']}</span><span>식이 {s['식이단계']}</span>"

    st.markdown(f"""
    <div class="sb-pt">
        <div class="n">OOO님 <span class="sb-badge {badge_class.get(rec_level,'badge-ok')}">{rec_level}</span></div>
        <div class="m">{info_line}</div>
        <div class="v">{info_tags}</div>
        <div class="sb-doc">주치의 <span>{s['담당의']}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-menu">메뉴</div>', unsafe_allow_html=True)
    menu_items = [
        ("chat", "💬", "알려준닥"),
        ("menu_dummy", "💊", "투약 정보"),
        ("menu_dummy", "📅", "진료 일정"),
        ("menu_dummy", "🍽️", "식사 안내"),
    ]
    for pid, icon, label in menu_items:
        active = "on" if st.session_state.page == pid else ""
        if st.button(f"{icon} {label}", key=f"nav_{pid}_{label}", use_container_width=True):
            if pid == "chat":
                st.session_state.page = pid
            else:
                st.toast(f"'{label}' 기능은 준비 중입니다.", icon=icon)
            st.rerun()

    # ── 좌측 하단 앱 홍보 ──
    st.markdown("---")
    with st.container(border=True):
        st.markdown('<p style="font-size:13px;font-weight:600;color:#9d174d;margin:0 0 8px">📱 알려준닥 모바일 앱</p>', unsafe_allow_html=True)
        st.image("data/3d2107aa-421f-4043-965d-4882758860f4.png", use_container_width=True)
        st.markdown('<p style="font-size:11px;color:#be185d;text-align:center">퇴원 후 케어까지, 알려준닥 앱에서 한 번에.</p>', unsafe_allow_html=True)
        if st.button("📱 자세히 보기", key="banner_sidebar", use_container_width=True):
            st.session_state.page = "app_intro"
            st.rerun()

    df_all = pd.read_csv("data/OB_GYN_DATA.csv", encoding="utf-8-sig")
    pid_list = df_all.index.tolist()
    pid_labels = [f"{r['환자ID']} - {r['진단명']}" for _, r in df_all.iterrows()]
    sel_idx = st.selectbox("환자", pid_list, index=st.session_state.selected_patient,
                           format_func=lambda i: pid_labels[i], label_visibility="collapsed")
    if sel_idx != st.session_state.selected_patient:
        st.session_state.selected_patient = sel_idx
        st.session_state.messages = []
        st.rerun()

    st.markdown('<div class="sb-f">© 2026 알려준닥</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════
#  CHAT
# ═══════════════════════════════════════════
def show_chat():
    if not st.session_state.messages:
        greet = f"안녕하세요, OOO님. 알려준닥입니다. 현재 {s['진단명']} 수술 후 {s['POD']}일차 회복 관리 중이에요. 통증, 식사, 보행, 상처 관리처럼 궁금한 점을 편하게 물어보세요."
        st.session_state.messages = [{"role": "bot", "content": greet}]

    for msg in st.session_state.messages:
        avatar = "👩" if msg["role"] == "user" else "💗"
        with st.chat_message("user" if msg["role"] == "user" else "assistant", avatar=avatar):
            st.write(msg["content"])

    if prompt := st.chat_input("궁금한 점을 물어보세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        resp, intent = cs_chat(prompt, "nurse", st.session_state.messages, st.session_state.selected_patient, "inpatient")
        st.session_state.messages.append({"role": "bot", "content": resp, "intent": intent})
        st.rerun()

    voice_btn = st.button("🎤", key="voice_input")
    if voice_btn:
        try:
            import speech_recognition as sr
            rec = sr.Recognizer()
            with sr.Microphone() as source:
                audio = rec.listen(source, timeout=5)
                v = rec.recognize_google(audio, language="ko-KR")
            st.session_state.messages.append({"role": "user", "content": v})
            resp, intent = cs_chat(v, "nurse", st.session_state.messages, st.session_state.selected_patient, "inpatient")
            st.session_state.messages.append({"role": "bot", "content": resp, "intent": intent})
            st.rerun()
        except:
            st.toast("음성인식 실패", icon="🎤")

    components.html("""
    <script>
    (function () {
        const parentDoc = window.parent.document;

        function findChatInputBox() {
            const byTestId = parentDoc.querySelector('[data-testid="stChatInput"]');
            if (byTestId) return byTestId;
            const textarea = parentDoc.querySelector('textarea[placeholder="궁금한 점을 물어보세요..."]');
            if (textarea) return textarea.closest('div');
            const input = parentDoc.querySelector('input[placeholder="궁금한 점을 물어보세요..."]');
            if (input) return input.closest('div');
            return null;
        }

        function findRealVoiceButton() {
            const keyWrapper = parentDoc.querySelector('div.st-key-voice_input');
            if (keyWrapper) { const btn = keyWrapper.querySelector('button'); if (btn) return btn; }
            return null;
        }

        function ensureVoiceOverlayButton() {
            const chatBox = findChatInputBox();
            const realVoiceButton = findRealVoiceButton();
            let overlayButton = parentDoc.getElementById('voice-overlay-button');

            if (!chatBox || !realVoiceButton) {
                if (overlayButton) overlayButton.remove();
                if (window.parent.__voiceInterval) { clearInterval(window.parent.__voiceInterval); window.parent.__voiceInterval = null; }
                return;
            }

            if (!overlayButton) {
                overlayButton = parentDoc.createElement('button');
                overlayButton.id = 'voice-overlay-button';
                overlayButton.type = 'button';
                overlayButton.innerHTML = '&#127908;';
                overlayButton.style.position = 'fixed';
                overlayButton.style.zIndex = '2147483647';
                overlayButton.style.width = '36px';
                overlayButton.style.height = '36px';
                overlayButton.style.minWidth = '36px';
                overlayButton.style.border = 'none';
                overlayButton.style.borderRadius = '10px';
                overlayButton.style.background = 'transparent';
                overlayButton.style.boxShadow = 'none';
                overlayButton.style.cursor = 'pointer';
                overlayButton.style.fontSize = '18px';
                overlayButton.style.display = 'flex';
                overlayButton.style.alignItems = 'center';
                overlayButton.style.justifyContent = 'center';
                overlayButton.style.padding = '0';
                overlayButton.setAttribute('aria-label', '음성으로 물어보기');
                overlayButton.addEventListener('mouseenter', function () { overlayButton.style.background = 'rgba(230, 235, 241, 0.9)'; });
                overlayButton.addEventListener('mouseleave', function () { overlayButton.style.background = 'transparent'; });
                overlayButton.addEventListener('click', function (e) {
                    e.preventDefault(); e.stopPropagation();
                    realVoiceButton.click();
                });
                parentDoc.body.appendChild(overlayButton);
            }

            const rect = chatBox.getBoundingClientRect();
            overlayButton.style.left = (rect.right - 86) + 'px';
            overlayButton.style.top = (rect.top + rect.height / 2 - 18) + 'px';
            overlayButton.style.display = 'flex';
        }

        ensureVoiceOverlayButton();
        if (window.parent.__voiceInterval) clearInterval(window.parent.__voiceInterval);
        window.parent.__voiceInterval = setInterval(ensureVoiceOverlayButton, 300);
        window.parent.addEventListener('resize', ensureVoiceOverlayButton);
        window.parent.addEventListener('scroll', ensureVoiceOverlayButton);
    })();
    </script>
    """, height=0)


# ═══════════════════════════════════════════
#  APP INTRO
# ═══════════════════════════════════════════
def show_app_intro():
    st.markdown("""
    <div style="max-width:560px;margin:40px auto;text-align:center">
        <div style="font-size:48px;margin-bottom:16px">📱</div>
        <h2 style="color:#9d174d;margin:0 0 8px">알려준닥 모바일 앱</h2>
        <p style="color:#888;font-size:14px">퇴원 후에도 회복 관리는 계속됩니다</p>
    </div>
    """, unsafe_allow_html=True)

    features = [
        ("🩺", "매일 회복 체크", "통증, 출혈, 상처 상태 기록"),
        ("⚠️", "위험 증상 알림", "발열·과다출혈 즉시 병원 연계"),
        ("💬", "24시간 챗봇", "수유, 식단, 우울감 상담"),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i]:
            st.markdown(f"""
            <div class="app-card">
                <div style="font-size:28px;margin-bottom:6px">{icon}</div>
                <h4 style="color:#9d174d;margin:0 0 4px;font-size:14px">{title}</h4>
                <p style="font-size:11px;color:#888;margin:0">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style="max-width:560px;margin:20px auto" class="info-box">
        <strong style="font-size:13px">앱 주요 기능</strong>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;margin-top:10px;font-size:12px;color:#666;line-height:1.8">
            <div>✓ 회복 상태 기록</div><div>✓ 위험 증상 체크</div>
            <div>✓ 산후 챗봇 상담</div><div>✓ 병원 재방문 일정</div>
            <div>✓ 산후조리원 정보</div><div>✓ 수유·식단 가이드</div>
            <div>✓ 산후우울감(EPDS)</div><div>✓ 응급 병원 연계</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        if st.button("📲 앱 다운로드 / 시작하기", use_container_width=True, type="primary"):
            st.toast("병원 간호사실에서 앱 설치 코드를 안내해 드립니다.", icon="📱")
        if st.button("← 챗봇으로 돌아가기", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()

    components.html("""
    <script>
    (function(){
        var w=window.parent;
        if(w.__voiceInterval){clearInterval(w.__voiceInterval);w.__voiceInterval=null;}
        var b=w.document.getElementById('voice-overlay-button');
        if(b)b.remove();
        var all=w.document.querySelectorAll('button');
        for(var i=0;i<all.length;i++){
            if(all[i].id==='voice-overlay-button'||(all[i].getAttribute('aria-label')||'').includes('음성'))all[i].remove();
        }
    })();
    </script>
    """, height=0)


# ═══════════════════════════════════════════
#  ROUTER
# ═══════════════════════════════════════════
if st.session_state.page == "app_intro":
    show_app_intro()
else:
    show_chat()
