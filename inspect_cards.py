#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查左侧卡片列表的DOM结构和文本内容"""
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

    # 分析左侧卡片
    cards_info = await page.evaluate("""() => {
        const allElements = Array.from(document.querySelectorAll('*'));
        const cards = allElements.filter(el => {
            const rect = el.getBoundingClientRect();
            return rect.left < 350 && rect.width > 150 && rect.width < 400
                && rect.height > 40 && rect.height < 150
                && el.textContent.length > 5 && el.textContent.length < 200
                && el.children.length >= 1;
        });

        let result = [];
        for (let card of cards) {
            let isInner = true;
            for (let other of cards) {
                if (other !== card && card.contains(other) && other.textContent.length > 5) {
                    isInner = false;
                    break;
                }
            }
            if (isInner && result.length < 15) {
                const rect = card.getBoundingClientRect();
                result.push({
                    tag: card.tagName,
                    className: card.className.substring(0, 120),
                    top: Math.round(rect.top),
                    height: Math.round(rect.height),
                    text: card.textContent.substring(0, 180).replace(/\\s+/g, ' ').trim()
                });
            }
        }
        result.sort((a, b) => a.top - b.top);
        return result;
    }""")

    print("=== 左侧卡片列表 ===")
    for i, card in enumerate(cards_info):
        print(f"  [{i}] top={card['top']} h={card['height']} <{card['tag']}> class=\"{card['className'][:60]}\"")
        print(f"      text: {card['text'][:150]}")
        print()

    # 再试一下：用指令前10个字去匹配
    test_instructions = [
        "用一个引流号就@elonmusk最新的帖子执行KOL跟评",
        "用一个号执行ai方向的新闻热点蹭热度闭环",
        "用一个引流号就事件源中博主最新一条视频执行油管内容转写",
    ]

    print("\n=== 指令匹配测试 ===")
    for instr in test_instructions:
        prefix = instr[:10]
        found = await page.evaluate("""(prefix) => {
            const allElements = Array.from(document.querySelectorAll('*'));
            const matches = allElements.filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.left < 350 && el.textContent.includes(prefix)
                    && el.textContent.length < 200 && rect.height > 30;
            });
            if (matches.length > 0) {
                return {
                    found: true,
                    count: matches.length,
                    text: matches[0].textContent.substring(0, 100).replace(/\\s+/g, ' ').trim(),
                    top: Math.round(matches[0].getBoundingClientRect().top)
                };
            }
            return { found: false };
        }""", prefix)
        print(f"  指令: \"{instr[:30]}...\"")
        print(f"  前缀: \"{prefix}\"")
        print(f"  结果: {found}")
        print()

    await browser.close()
    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
