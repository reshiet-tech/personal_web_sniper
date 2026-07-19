import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from src.config import load_targets, get_logger
from src.notifier import send_telegram_message
from src.comparator import load_snapshots, save_snapshots, get_text_diff
from src.fetcher import fetch_and_normalize, fetch_simple
from src.ai_filter import evaluate_diff_with_ai

logger = get_logger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15"
]

async def check_site_status(page, target, snapshots):
    name = target["name"]
    url = target["url"]
    success_texts = target.get("success_text", [])
    failure_texts = target.get("failure_text", [])

    try:
        if target.get("use_simple_fetch", False):
            logger.info(f"[{name}] 접속 중 (Simple Fetch): {url}")
            content = await fetch_simple(target)
        else:
            logger.info(f"[{name}] 접속 중: {url}")
            content = await fetch_and_normalize(page, target)
        old_content = snapshots.get(name, "")
        
        # 변경점 분석
        added, removed = get_text_diff(old_content, content)
        has_changed = bool(added or removed)
        
        # 키워드 감지
        matched_success = next((text for text in success_texts if text in content), None)
        is_success = bool(matched_success)
        is_failure = any(text in content for text in failure_texts) if failure_texts else False

        should_alert = False
        alert_reason = ""
        
        if success_texts:
            if is_success and not is_failure:
                should_alert = True
                alert_reason = f"성공 키워드 감지 ('{matched_success}')"
            elif is_failure:
                logger.info(f"[{name}] 상태: 불가능 (품절/예약마감)")
            else:
                logger.info(f"[{name}] 감지 대기 중...")
        elif failure_texts:
            # 성공 키워드는 비어있고 실패 키워드만 있는 경우 -> "실패 키워드가 사라지면 성공"으로 간주 (리버스 트리거)
            if not is_failure:
                # 과거 상태에는 실패 키워드가 있었는지 확인 (계속 알림 방지)
                was_failure = any(text in old_content for text in failure_texts) if old_content else True
                if was_failure:
                    should_alert = True
                    alert_reason = "실패 키워드(품절/마감) 사라짐 감지"
                else:
                    logger.info(f"[{name}] 상태: 구매/예약 가능 상태 유지 중 (알림 생략)")
            else:
                logger.info(f"[{name}] 상태: 불가능 (품절/예약마감 유지)")
        else:
            # 단순 변경 감지 모드
            if has_changed and old_content:
                should_alert = True
                alert_reason = "웹페이지 내용 변경 감지"
            else:
                logger.info(f"[{name}] 변경사항 없음")

        if should_alert:
            # AI 필터링 (키워드 모드가 아닌 단순 Diff 모드일 경우에만 적용)
            if not success_texts:
                logger.info(f"[{name}] AI에게 변경점 유의미성 질의 중...")
                is_meaningful = evaluate_diff_with_ai(name, added, removed)
                if not is_meaningful:
                    should_alert = False
                    logger.info(f"[{name}] AI 판단: 무의미한 변경으로 알림 생략")

        if should_alert:
            logger.info(f"[{name}] 상태 변경 감지! ({alert_reason})")
            
            diff_msg = ""
            if added:
                diff_msg += "\n<b>[추가된 내용]</b>\n" + "\n".join([f"+ {a}" for a in added[:30]])
                if len(added) > 30: diff_msg += "\n... (생략)"
            if removed:
                diff_msg += "\n<b>[삭제된 내용]</b>\n" + "\n".join([f"- {r}" for r in removed[:30]])
                if len(removed) > 30: diff_msg += "\n... (생략)"
                
            message = f"🚨 <b>{name} 스나이퍼 알림</b> 🚨\n\n✅ <b>상태:</b> {alert_reason}\n🔗 <b>링크:</b> <a href='{url}'>바로가기</a>\n{diff_msg}"
            send_telegram_message(message)
            
        if has_changed or not old_content:
            snapshots[name] = content

    except Exception as e:
        logger.error(f"[{name}] 확인 중 에러 발생: {e}")

async def main():
    logger.info("=== 웹 스나이퍼 봇 실행 시작 ===")
    
    targets = load_targets()
    if not targets:
        logger.info("등록된 타겟이 없습니다.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        user_agent = random.choice(USER_AGENTS)
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        page = await context.new_page()
        
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        snapshots = load_snapshots()

        for target in targets:
            await asyncio.sleep(random.uniform(1.0, 3.0))
            await check_site_status(page, target, snapshots)
            await asyncio.sleep(random.uniform(3.0, 7.0))

        save_snapshots(snapshots)
        await browser.close()
        
    logger.info("=== 웹 스나이퍼 봇 실행 종료 ===")

if __name__ == "__main__":
    asyncio.run(main())
