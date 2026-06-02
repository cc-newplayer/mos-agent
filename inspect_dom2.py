#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查对话区域DOM结构 - 找到最新消息的精确选择器"""
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
    await page.evaluate("""async () => {
        for (let i = 0; i < 20; i++) {
            const cards = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = el.textContent;
                return text && text.includes('引流号') && text.length < 150;
            });
            if (cards.length > 0) { cards[0].click(); return true; }
            await new Promise(r => setTimeout(r, 500));
        }
        return false;
    }""")
    await page.wait_for_timeout(3000)

    # 深入分析右侧对话区域
    result = await page.evaluate("""() => {
        const allDivs = document.querySelectorAll('div');
        let chatArea = null;

        // 找右侧可滚动的对话区域
        for (let div of allDivs) {
            const rect = div.getBoundingClientRect();
            if (rect.left > 300 && rect.height > 400 && div.scrollHeight > div.clientHeight) {
                if (!chatArea || div.scrollHeight > chatArea.scrollHeight) {
                    chatArea = div;
                }
            }
        }

        if (!chatArea) return { error: 'no chat area found' };

        // 分析最后几个子元素
        let children = [];
        for (let i = Math.max(0, chatArea.children.length - 5); i < chatArea.children.length; i++) {
            const child = chatArea.children[i];
            children.push({
                index: i,
                tag: child.tagName,
                className: child.className.substring(0, 150),
                textLength: child.textContent.length,
                textPreview: child.textContent.substring(0, 250),
                childCount: child.children.length
            });
        }

        return {
            chatAreaClass: chatArea.className.substring(0, 150),
            chatAreaTag: chatArea.tagName,
            totalChildren: chatArea.children.length,
            scrollHeight: chatArea.scrollHeight,
            lastChildren: children
        };
    }""")

    print("=== 对话区域分析 ===")
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"容器: <{result['chatAreaTag']}> class=\"{result['chatAreaClass'][:80]}\"")
        print(f"子元素数: {result['totalChildren']}, scrollHeight: {result['scrollHeight']}")
        print(f"\n最后几个子元素:")
        for child in result["lastChildren"]:
            print(f"  [{child['index']}] <{child['tag']}> class=\"{child['className'][:80]}\"")
            print(f"       textLen={child['textLength']}, children={child['childCount']}")
            print(f"       text: {child['textPreview'][:150]}")
            print()

    # 再试另一个思路：找所有包含"MarketingAI"或对话气泡样式的元素
    bubbles = await page.evaluate("""() => {
        const all = document.querySelectorAll('div');
        let results = [];
        for (let el of all) {
            const text = el.textContent;
            const rect = el.getBoundingClientRect();
            // 看起来像单条消息：有一定文本，宽度适中，不是整个页面
            if (text.length > 30 && text.length < 2000 && rect.width > 200 && rect.width < 800 && rect.height > 30 && rect.height < 500) {
                // 检查是否是叶子级别的消息（子元素不多）
                if (el.children.length < 10) {
                    results.push({
                        className: el.className.substring(0, 100),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        top: Math.round(rect.top),
                        textPreview: text.substring(0, 150)
                    });
                }
            }
        }
        // 按top排序，取最后5个
        results.sort((a, b) => b.top - a.top);
        return results.slice(0, 5);
    }""")

    print("\n=== 疑似消息气泡（按位置从下到上）===")
    for i, b in enumerate(bubbles):
        print(f"  [{i}] class=\"{b['className'][:60]}\" size={b['width']}x{b['height']} top={b['top']}")
        print(f"       text: {b['textPreview'][:120]}")
        print()

    await browser.close()
    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
