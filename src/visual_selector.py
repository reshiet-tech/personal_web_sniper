import asyncio
import sys
from playwright.async_api import async_playwright

async def run(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url)
            
            # Inject CSS for highlight
            await page.add_style_tag(content=".web-sniper-hover { outline: 4px solid #ff4b4b !important; cursor: crosshair !important; background-color: rgba(255, 75, 75, 0.2) !important; box-shadow: 0 0 10px #ff4b4b !important; }")
            
            # Inject JS to handle selection
            js_code = """
            () => {
                return new Promise((resolve) => {
                    const getCssSelector = (el) => {
                        if (el.tagName.toLowerCase() == "html") return "html";
                        let str = el.tagName.toLowerCase();
                        if (el.id !== "") {
                            str += "#" + el.id;
                            return str; 
                        }
                        if (el.className && typeof el.className === 'string') {
                            let classes = el.className.split(/\\s+/).filter(c => c && !c.includes('web-sniper-hover'));
                            if (classes.length > 0) {
                                str += "." + classes.join(".");
                            }
                        }
                        return getCssSelector(el.parentNode) + " > " + str;
                    };

                    const mouseOverHandler = (e) => {
                        e.target.classList.add('web-sniper-hover');
                        e.stopPropagation();
                    };

                    const mouseOutHandler = (e) => {
                        e.target.classList.remove('web-sniper-hover');
                        e.stopPropagation();
                    };

                    const clickHandler = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        e.target.classList.remove('web-sniper-hover');
                        const selector = getCssSelector(e.target);
                        const text = e.target.innerText || e.target.textContent || "";
                        
                        document.removeEventListener('mouseover', mouseOverHandler, true);
                        document.removeEventListener('mouseout', mouseOutHandler, true);
                        document.removeEventListener('click', clickHandler, true);
                        
                        resolve(JSON.stringify({selector: selector, text: text.trim()}));
                    };

                    document.addEventListener('mouseover', mouseOverHandler, true);
                    document.addEventListener('mouseout', mouseOutHandler, true);
                    document.addEventListener('click', clickHandler, true);
                });
            }
            """
            
            # Wait for user to click
            result_json = await page.evaluate(js_code)
            print(result_json)
            
        except Exception as e:
            print("body", file=sys.stderr)
        finally:
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        asyncio.run(run(target_url))
    else:
        print("body")
