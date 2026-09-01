import asyncio
import argparse
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from src.config import get_logger, load_targets
from src.notifier import send_telegram_message
from src.comparator import load_snapshots, save_snapshots
from src.fetcher import fetch_and_normalize, fetch_simple

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
    target_type = target.get("type", "keyword_monitor")

    try:
        if target.get("use_simple_fetch", False):
            logger.info(f"[{name}] requests로 확인 중...")
            result = await fetch_simple(target)
        else:
            logger.info(f"[{name}] 브라우저로 확인 중...")
            result = await fetch_and_normalize(page, target)

        current_text = result["text"]
        current_price = result.get("price")
        
        old_state = snapshots.get(name, {})
        if isinstance(old_state, str):
            # 마이그레이션: 기존 문자열 스냅샷을 딕셔너리로 변환
            old_state = {"text": old_state, "price": None}
            
        old_text = old_state.get("text", "")
        old_price = old_state.get("price")

        should_alert = False
        alert_reason = ""
        msg_body = ""

        if target_type == "price_monitor":
            target_price = target.get("target_price")
            old_target_price = old_state.get("target_price")
            
            if current_price is None:
                logger.info(f"[{name}] 가격을 추출할 수 없습니다.")
            else:
                if old_price is None or current_price != old_price or old_target_price != target_price:
                    # 가격 변동 발생 또는 목표가 설정 변경됨
                    if target_price:
                        if current_price <= target_price:
                            should_alert = True
                            alert_reason = "목표가 도달! 🎉 (가격 하락 감지)"
                            msg_body = f"💰 기존 가격: {old_price if old_price else '모름'}원\n📉 현재 가격: {current_price}원 (목표가 {target_price}원 달성!)"
                        elif current_price <= target_price * 1.05: # 목표가의 5% 이내 접근
                            should_alert = True
                            alert_reason = "목표가 근접! 👀 (5% 이내 진입)"
                            msg_body = f"💰 기존 가격: {old_price if old_price else '모름'}원\n📉 현재 가격: {current_price}원 (목표가 {target_price}원에 거의 다 왔습니다!)"
                        elif target.get("alert_on_any_drop", True) and old_price and current_price < old_price:
                            should_alert = True
                            alert_reason = "가격 하락 감지! 📉"
                            msg_body = f"💰 기존 가격: {old_price}원\n📉 현재 가격: {current_price}원"
                        else:
                            logger.info(f"[{name}] 가격 조건 미달 또는 올랐습니다. (기존: {old_price}, 현재: {current_price})")
                    else:
                        if old_price and current_price < old_price:
                            should_alert = True
                            alert_reason = "가격 하락 감지! 📉"
                            msg_body = f"💰 기존 가격: {old_price}원\n📉 현재 가격: {current_price}원"
                        else:
                            logger.info(f"[{name}] 가격 변동이 없거나 올랐습니다. (기존: {old_price}, 현재: {current_price})")
                else:
                    logger.info(f"[{name}] 가격 변동 없음 (현재: {current_price})")
        
        elif target_type == "keyword_monitor":
            success_texts = target.get("success_text", [])
            failure_texts = target.get("failure_text", [])
            
            matched_success = next((text for text in success_texts if text in current_text), None)
            is_success = bool(matched_success)
            is_failure = any(text in current_text for text in failure_texts) if failure_texts else False
            
            if success_texts:
                if is_success and not is_failure:
                    # 새로 성공 키워드가 감지되었을 때만 알림
                    old_matched = any(text in old_text for text in success_texts)
                    if not old_matched:
                        should_alert = True
                        alert_reason = f"성공 키워드 감지 ('{matched_success}')"
                        msg_body = f"💡 감지된 키워드: {matched_success}"
                elif is_failure:
                    logger.info(f"[{name}] 상태: 불가능 (품절/예약마감)")
                else:
                    logger.info(f"[{name}] 감지 대기 중...")
            
            elif failure_texts:
                if not is_failure:
                    was_failure = any(text in old_text for text in failure_texts) if old_text else True
                    if was_failure:
                        should_alert = True
                        alert_reason = "실패 키워드(품절/마감) 사라짐 감지"
                        msg_body = f"💡 상태: 구매/예약 가능으로 변경됨"
                else:
                    logger.info(f"[{name}] 상태: 불가능 (품절/예약마감 유지)")
                    
            else:
                # 단순 변경 (가격도 아니고 키워드도 없을 때)
                if old_text and current_text != old_text:
                    should_alert = True
                    alert_reason = "웹페이지 내용 변경 감지"
                    msg_body = "💡 웹페이지의 텍스트가 변경되었습니다."

        if should_alert:
            logger.info(f"[{name}] 🚨 상태 변경 감지! ({alert_reason})")
            
            message = (
                f"🚨 <b>{name} 스나이퍼 알림</b> 🚨\n\n"
                f"✅ <b>상태:</b> {alert_reason}\n"
                f"🔗 <b>링크:</b> <a href='{url}'>바로가기</a>\n\n"
                f"{msg_body}"
            )
            
            send_telegram_message(message)

        # 상태 저장
        snapshots[name] = {
            "text": current_text,
            "price": current_price,
            "target_price": target.get("target_price") if target_type == "price_monitor" else None
        }

    except Exception as e:
        logger.error(f"[{name}] 확인 중 에러 발생: {e}")

async def main_loop():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="테스트 모드: 알림 전송 안 함")
    args = parser.parse_args()

    targets = load_targets()
    active_targets = [t for t in targets if t.get("is_active", True)]
    
    if not active_targets:
        logger.info("활성화된 감시 대상이 없습니다.")
        return

    snapshots = load_snapshots()

    async with async_playwright() as p:
        import random
        user_agent = random.choice(USER_AGENTS)
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            bypass_csp=True
        )
        
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        await page.set_extra_http_headers({
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        })

        for target in active_targets:
            await check_site_status(page, target, snapshots)
            await asyncio.sleep(2)

        save_snapshots(snapshots)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main_loop())
