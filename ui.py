import streamlit as st
import json
import os

TARGETS_FILE = "targets.json"

st.set_page_config(page_title="Web Sniper Target Manager", page_icon="🎯", layout="centered")

st.title("🎯 Web Sniper 타겟 관리자")
st.markdown("스나이퍼 봇이 감시할 웹사이트 목록을 편하게 관리하세요. \\n**주의:** 로컬에서 수정 후, 변경된 `targets.json` 파일을 반드시 GitHub에 Push 하셔야 Actions 봇에 반영됩니다!")

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
        
        submit_btn = st.form_submit_button("추가하기")
        if submit_btn:
            if new_name and new_url:
                success_list = [t.strip() for t in new_success.split(",") if t.strip()]
                failure_list = [t.strip() for t in new_failure.split(",") if t.strip()]
                
                targets.append({
                    "name": new_name,
                    "url": new_url,
                    "selector": new_selector,
                    "success_text": success_list,
                    "failure_text": failure_list
                })
                save_targets(targets)
                st.success(f"'{new_name}' 추가 완료!")
                st.rerun()
            else:
                st.error("이름과 URL은 필수 입력 항목입니다.")

st.divider()
st.subheader("📋 현재 등록된 타겟 목록")

if not targets:
    st.info("등록된 타겟이 없습니다. 위에서 추가해 주세요.")
else:
    for i, target in enumerate(targets):
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{target['name']}**")
                st.caption(f"🔗 {target['url']}")
                st.text(f"✅ 성공 텍스트: {', '.join(target['success_text']) if target['success_text'] else '없음'}")
                st.text(f"❌ 실패 텍스트: {', '.join(target['failure_text']) if target['failure_text'] else '없음'}")
            with col2:
                if st.button("삭제", key=f"del_{i}"):
                    targets.pop(i)
                    save_targets(targets)
                    st.rerun()
        st.markdown("---")
