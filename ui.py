import streamlit as st
import json
import os
import subprocess
import re

TARGETS_FILE = "targets.json"
YML_FILE = ".github/workflows/sniper.yml"

st.set_page_config(page_title="Web Sniper Target Manager", page_icon="🎯", layout="centered")

st.title("🎯 Web Sniper 타겟 관리자")
st.markdown("스나이퍼 봇이 감시할 웹사이트 목록을 편하게 관리하세요.")

def get_current_cron():
    if os.path.exists(YML_FILE):
        with open(YML_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"cron:\s+'([^']+)'", content)
            if match:
                return match.group(1)
    return "*/15 * * * *"

def update_cron(new_cron):
    if os.path.exists(YML_FILE):
        with open(YML_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        new_content = re.sub(r"cron:\s+'[^']+'", f"cron: '{new_cron}'", content)
        with open(YML_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)

# 사이드바 설정 영역
st.sidebar.title("⚙️ 감시 주기 설정")
cron_options = {
    "*/5 * * * *": "5분마다",
    "*/10 * * * *": "10분마다",
    "*/15 * * * *": "15분마다",
    "*/30 * * * *": "30분마다",
    "0 * * * *": "1시간마다",
    "0 */6 * * *": "6시간마다",
    "0 0 * * *": "하루 1번 (자정)"
}
current_cron = get_current_cron()
current_label = cron_options.get(current_cron, "15분마다")
# 안전한 index 찾기
try:
    default_idx = list(cron_options.values()).index(current_label)
except ValueError:
    default_idx = 1

selected_label = st.sidebar.selectbox("스나이퍼 봇 감시 주기", list(cron_options.values()), index=default_idx)
selected_cron = [k for k, v in cron_options.items() if v == selected_label][0]

if selected_cron != current_cron:
    update_cron(selected_cron)
    st.sidebar.success(f"감시 주기가 {selected_label}로 변경되었습니다. (서버 반영 필요)")

st.sidebar.markdown("---")
st.sidebar.title("🚀 서버 반영")
st.sidebar.markdown("수정이 끝났다면 아래 버튼을 눌러 GitHub 서버에 즉시 반영하세요!")
if st.sidebar.button("GitHub에 즉시 업데이트", type="primary"):
    with st.spinner("서버에 업로드 중입니다..."):
        try:
            status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if "targets.json" not in status.stdout and "sniper.yml" not in status.stdout:
                st.sidebar.info("새로 변경된 사항이 없습니다.")
            else:
                subprocess.run(["git", "add", "targets.json", YML_FILE], check=True)
                try:
                    subprocess.run(["git", "commit", "-m", "UI에서 타겟 목록 및 주기 업데이트"], check=True)
                except subprocess.CalledProcessError:
                    pass # 커밋할 내용이 없는 경우 무시 (이미 커밋된 상태 등)
                
                # 깃허브 액션이 백그라운드에서 푸시한 스냅샷을 충돌 없이 병합
                subprocess.run(["git", "pull", "--rebase", "--autostash"], check=True)
                subprocess.run(["git", "push"], check=True)
                st.sidebar.success("✅ 업데이트 완료! 서버에 반영되었습니다.")
        except Exception as e:
            st.sidebar.error(f"업데이트 실패: {e}")
def load_targets():
    if not os.path.exists(TARGETS_FILE):
        return []
    with open(TARGETS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_targets(targets):
    with open(TARGETS_FILE, "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False, indent=4)

targets = load_targets()

# 타겟 추가 폼
with st.expander("➕ 새로운 타겟 추가하기", expanded=False):
    with st.form("add_target_form"):
        new_name = st.text_input("타겟 이름 (예: 아이폰 15 프로)")
        new_url = st.text_input("URL (실제 감시할 상품 상세 페이지 주소)")
        new_selector = st.text_input("CSS 선택자 (기본값: body)", value="body")
        new_success = st.text_input("성공 텍스트 (쉼표로 구분, 예: 구매하기,장바구니 담기)")
        new_failure = st.text_input("실패 텍스트 (쉼표로 구분, 예: 품절,판매종료,예약마감)")
        
        with st.expander("⚙️ 고급 설정 (정규화 및 필터링)"):
            st.info("성공/실패 텍스트를 비워두면 **[모든 텍스트 변경 감지(Diff) 모드]**로 동작합니다.")
            new_ignore_selectors = st.text_area("무시할 CSS 선택자 (줄바꿈으로 구분)", help="HTML에서 아예 삭제할 요소 (예: .ad-banner, #counter)")
            new_ignore_regex = st.text_area("무시할 정규표현식 (줄바꿈으로 구분)", help="텍스트에서 지워버릴 패턴 (예: [0-9]{2}:[0-9]{2})")
            
        submit_btn = st.form_submit_button("추가하기")
        if submit_btn:
            if new_name and new_url:
                success_list = [t.strip() for t in new_success.split(",") if t.strip()]
                failure_list = [t.strip() for t in new_failure.split(",") if t.strip()]
                ignore_sel_list = [t.strip() for t in new_ignore_selectors.split("\n") if t.strip()]
                ignore_reg_list = [t.strip() for t in new_ignore_regex.split("\n") if t.strip()]
                
                targets.append({
                    "name": new_name,
                    "url": new_url,
                    "selector": new_selector,
                    "success_text": success_list,
                    "failure_text": failure_list,
                    "ignore_selectors": ignore_sel_list,
                    "ignore_regex": ignore_reg_list
                })
                save_targets(targets)
                st.success(f"'{new_name}' 추가 완료!")
                st.rerun()
            else:
                st.error("이름과 URL은 필수 입력 항목입니다.")

st.divider()
st.subheader("📋 현재 등록된 타겟 목록")

if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None

if not targets:
    st.info("등록된 타겟이 없습니다. 위에서 추가해 주세요.")
else:
    for i, target in enumerate(targets):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{target['name']}**")
                st.caption(f"🔗 {target['url']}")
                st.text(f"✅ 성공 텍스트: {', '.join(target['success_text']) if target['success_text'] else '없음 (변경 감지 모드)'}")
                st.text(f"❌ 실패 텍스트: {', '.join(target['failure_text']) if target['failure_text'] else '없음'}")
                if target.get('ignore_selectors') or target.get('ignore_regex'):
                    st.caption("⚙️ 정규화(Ignore) 설정 적용됨")
            with col2:
                if st.button("수정", key=f"edit_btn_{i}"):
                    st.session_state.edit_idx = i
            with col3:
                if st.button("삭제", key=f"del_btn_{i}"):
                    targets.pop(i)
                    save_targets(targets)
                    if st.session_state.edit_idx == i:
                        st.session_state.edit_idx = None
                    st.rerun()
                    
        # 수정 폼 표시
        if st.session_state.edit_idx == i:
            with st.form(key=f"edit_form_{i}"):
                st.markdown("#### ✏️ 타겟 수정")
                edit_name = st.text_input("타겟 이름", value=target['name'])
                edit_url = st.text_input("URL", value=target['url'])
                edit_selector = st.text_input("CSS 선택자", value=target.get('selector', 'body'))
                edit_success = st.text_input("성공 텍스트 (쉼표로 구분)", value=",".join(target['success_text']))
                edit_failure = st.text_input("실패 텍스트 (쉼표로 구분)", value=",".join(target['failure_text']))
                
                with st.expander("⚙️ 고급 설정 (정규화 및 필터링)"):
                    st.info("성공/실패 텍스트를 비워두면 **[모든 텍스트 변경 감지(Diff) 모드]**로 동작합니다.")
                    edit_ignore_selectors = st.text_area("무시할 CSS 선택자 (줄바꿈으로 구분)", value="\n".join(target.get('ignore_selectors', [])))
                    edit_ignore_regex = st.text_area("무시할 정규표현식 (줄바꿈으로 구분)", value="\n".join(target.get('ignore_regex', [])))
                
                c1, c2 = st.columns(2)
                with c1:
                    save_btn = st.form_submit_button("저장하기")
                with c2:
                    cancel_btn = st.form_submit_button("취소")
                    
                if save_btn:
                    if edit_name and edit_url:
                        targets[i]['name'] = edit_name
                        targets[i]['url'] = edit_url
                        targets[i]['selector'] = edit_selector
                        targets[i]['success_text'] = [t.strip() for t in edit_success.split(",") if t.strip()]
                        targets[i]['failure_text'] = [t.strip() for t in edit_failure.split(",") if t.strip()]
                        targets[i]['ignore_selectors'] = [t.strip() for t in edit_ignore_selectors.split("\n") if t.strip()]
                        targets[i]['ignore_regex'] = [t.strip() for t in edit_ignore_regex.split("\n") if t.strip()]
                        save_targets(targets)
                        st.session_state.edit_idx = None
                        st.rerun()
                    else:
                        st.error("이름과 URL은 필수 항목입니다.")
                if cancel_btn:
                    st.session_state.edit_idx = None
                    st.rerun()
                    
        st.markdown("---")
