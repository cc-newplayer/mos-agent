#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时脚本：检查决策对话页面的DOM结构，找到最新消息的选择器"""
import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from playwright.async_api import async_playwright
from config import SYSTEM_URL, LOGIN_USERNAME, LOGIN_PASSWORD


async def main():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto(f"{SYSTEM_URL}/decision", wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    # 登录
    try:
        await page.wait_for_selector('input[type="text"]', timeout=5000)
        await page.fill('input[type="text"]', LOGIN_USERNAME)
        await page.fill('input[type="password"]', LOGIN_PASSWORD)
        btn = await page.query_selector("button")
        if btn:
            await btn.click()
        await page.wait_for_url("**/overview", timeout=10000)
        await page.goto(f"{SYSTEM_URL}/decision", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
    except:
        pass

    # 点击引流号卡片
    clicked = await page.evaluate("""async () => {
        for (let i = 0; i < 20; i++) {
            const cards = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = el.textContent;
                return text && text.includes('引流号') && text.length < 150;
            });
            if (cards.length > 0) {
                cards[0].click();
                return true;
            }
            await new Promise(r => setTimeout(r, 500));
        }
        return false;
    }""")
    print(f"Clicked card: {clicked}")
    await page.wait_for_timeout(3000)

    # 分析对话区域DOM
    structure = await page.evaluate("""() => {
        const allElements = document.querySelectorAll('[class*="message"], [class*="chat"], [class*="conversation"], [class*="dialog"], [class*="bubble"]');
        let result = [];
        for (let el of allElements) {
            if (el.children.length > 0 && el.textContent.length > 20 && el.textContent.length < 5000) {
                result.push({
                    tag: el.tagName,
                    className: el.className.substring(0, 120),
                    childCount: el.children.length,
                    textLength: el.textContent.length,
                    textPreview: el.textContent.substring(0, 120)
                });
            }
        }
        return result.slice(0, 20);
    }""")

    print("\n=== 对话相关DOM元素 ===")
    for item in structure:
        print(f"\n  <{item['tag']}> class=\"{item['className'][:60]}\"")
        print(f"    children={item['childCount']}, textLen={item['textLength']}")
        print(f"    text: {item['textPreview'][:80]}")

    # 尝试找最后一条AI回复
    last_msg = await page.evaluate("""() => {
        // 思路1: 找所有message类的元素，取最后一个
        const msgs = document.querySelectorAll('[class*="message"]');
        let results = [];
        if (msgs.length > 0) {
            const last = msgs[msgs.length - 1];
            results.push({
                method: 'last [class*=message]',
                className: last.className.substring(0, 100),
                text: last.textContent.substring(0, 300)
            });
        }

        // 思路2: 找滚动容器里的最后一个子元素
        const scrollables = document.querySelectorAll('[style*="overflow"], [class*="scroll"], [class*="list"]');
        for (let s of scrollables) {
            if (s.scrollHeight > 500 && s.children.length > 2) {
                const lastChild = s.children[s.children.length - 1];
                results.push({
                    method: 'last child of scrollable',
                    className: s.className.substring(0, 80) + ' > ' + lastChild.className.substring(0, 80),
                    text: lastChild.textContent.substring(0, 300)
                });
                break;
            }
        }

        return results;
    }""")

    print("\n\n=== 最后一条消息候选 ===")
    for item in last_msg:
        print(f"\n  方法: {item['method']}")
        print(f"  class: {item['className']}")
        print(f"  text: {item['text'][:200]}")

    # 截图保存
    await page.screenshot(path="inspect_dom_screenshot.png")
    print("\n截图已保存: inspect_dom_screenshot.png")

    await browser.close()
    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
