# ikuuu 自动签到 - Playwright 版本
# 变量名 ikuuu=账号1#密码1&账号2#密码2

import asyncio
import base64
import os
import random
import re
import sys
from datetime import datetime

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

DOMAIN_CANDIDATES = [
    'https://ikuuu.nl',
    'https://ikuuu.org',
    'https://ikuuu.de',
    'https://ikuuu.eu',
    'https://ikuuu.one',
    'https://ikuuu.me',
    'https://ikuuu.uk',
]


def send_bark(title: str, content: str):
    """发送 Bark 通知"""
    import requests

    bark_key = os.environ.get('BARK_KEY')
    bark_server = os.environ.get('BARK_SERVER', 'https://api.day.app')

    if not bark_key:
        print('[Bark]: BARK_KEY not configured, skipping')
        return

    url = f'{bark_server.rstrip("/")}/push'
    data = {
        'device_key': bark_key,
        'title': title,
        'body': content,
        'group': 'ikuuu',
    }

    try:
        res = requests.post(url, json=data, timeout=30)
        res.raise_for_status()
        print('[Bark]: Message push successful!')
    except Exception as e:
        print(f'[Bark]: Message push failed! Reason: {str(e)}')


class ikuuu:
    def __init__(self, ck):
        self.email = ck[0].strip() if len(ck) >= 2 else ""
        self.passwd = ck[1].strip() if len(ck) >= 2 else ""
        self.base_url = None
        self.login_error = ""
        self.username = None
        self.traffic_before = None
        self.traffic_after = None
        self.already_signed = False

    def _decode_origin_body(self, html):
        match = re.search(r'var originBody = "([A-Za-z0-9+/=]+)";', html)
        if not match:
            return html
        try:
            return base64.b64decode(match.group(1)).decode('utf-8', 'ignore')
        except Exception:
            return html

    def _extract_user_info(self, html):
        page = self._decode_origin_body(html)
        soup = BeautifulSoup(page, 'html.parser')

        name_elem = (
            soup.find('span', {'class': 'navbar-brand'})
            or soup.find('div', {'class': 'd-sm-none d-lg-inline-block'})
        )
        username = name_elem.text.strip() if name_elem else self.email

        traffic = "未知"
        for header in soup.find_all(['h4', 'h5']):
            title = header.get_text(strip=True)
            if '剩余流量' not in title:
                continue

            card = header.find_parent(class_='card') or header.parent
            if not card:
                continue

            counter = card.find('span', {'class': 'counter'})
            if counter:
                traffic = counter.get_text(strip=True)
                break

            body = card.find(class_='card-body')
            if body:
                text = ' '.join(body.stripped_strings)
                match = re.search(r'(\d+(?:\.\d+)?)\s*GB', text, re.I)
                if match:
                    traffic = match.group(1)
                    break

        return username, traffic

    async def resolve_base_url(self, page):
        """通过 Playwright 检测可用域名"""
        for base_url in DOMAIN_CANDIDATES:
            try:
                await page.goto(f'{base_url}/auth/login', wait_until='domcontentloaded', timeout=15000)
                content = await page.content()
                if 'name="email"' in content or 'name="password"' in content or '登录' in content:
                    self.base_url = base_url
                    return base_url
            except Exception:
                continue
        raise RuntimeError('未找到可用的 ikuuu 登录域名')

    async def sign_with_playwright(self, page):
        """使用 Playwright 执行签到"""
        try:
            user_url = f'{self.base_url}/user'
            await page.goto(user_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            content = await page.content()
            self.username, self.traffic_before = self._extract_user_info(content)
            print(f"[登录]：{self.username}\n[签到前流量]：{self.traffic_before}\n")

            sign_btn_selectors = [
                'button:has-text("签到")',
                'a:has-text("签到")',
                '.checkin',
                '#checkin',
                'button:has-text("每日签到")',
                'a:has-text("每日签到")',
                '[href*="checkin"]',
            ]

            sign_clicked = False
            for selector in sign_btn_selectors:
                try:
                    if await page.is_visible(selector, timeout=2000):
                        await page.click(selector)
                        print(f'[Playwright] 已点击签到按钮: {selector}')
                        sign_clicked = True
                        await page.wait_for_timeout(3000)
                        break
                except:
                    continue

            if not sign_clicked:
                print('[Playwright] 未找到签到按钮，尝试直接调用签到API...')
                sign_url = f'{self.base_url}/user/checkin'

                result = await page.evaluate(f'''
                    async () => {{
                        const response = await fetch("{sign_url}", {{
                            method: "POST",
                            headers: {{
                                "X-Requested-With": "XMLHttpRequest",
                                "Accept": "application/json",
                                "Referer": "{user_url}"
                            }},
                            credentials: "include"
                        }});
                        const text = await response.text();
                        try {{
                            return JSON.parse(text);
                        }} catch (e) {{
                            return {{ text: text.substring(0, 200) }};
                        }}
                    }}
                ''')
                print(f'[Playwright] 签到API响应: {result}')

                if isinstance(result, dict):
                    if result.get('ret') == 1 or '已经签到' in str(result.get('msg', '')):
                        msg = result.get('msg', '签到成功')
                        if '已经签到' in msg:
                            self.already_signed = True
                        print(f"[签到]：{msg}\n")
                    else:
                        msg = result.get('msg', result.get('text', '未知结果'))
                        print(f"[签到]：{msg}\n")
                else:
                    print(f"[签到]：{result}\n")
            else:
                await page.wait_for_timeout(2000)
                content = await page.content()
                if '已经签到' in content or '已签到' in content:
                    self.already_signed = True
                    print(f"[签到]：今天已经签到过了\n")
                elif '签到成功' in content or '获得' in content:
                    print(f"[签到]：签到成功\n")
                else:
                    print(f"[签到]：已尝试签到\n")

            await page.goto(user_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            content = await page.content()
            _, self.traffic_after = self._extract_user_info(content)
            print(f"[签到后流量]：{self.traffic_after}\n")

            return True

        except Exception as e:
            print(f'[Playwright] 签到失败: {e}')
            return False

    async def sign(self):
        """签到主流程"""
        print(f"[INFO] 尝试 Playwright 自动登录并签到...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
            )

            page = await context.new_page()

            try:
                # 检测可用域名
                try:
                    await self.resolve_base_url(page)
                except Exception as e:
                    print(f"[ERROR] {e}")
                    await browser.close()
                    return

                login_url = f'{self.base_url}/auth/login'
                print(f'[Playwright] 访问登录页面: {login_url}')
                await page.goto(login_url, wait_until='domcontentloaded', timeout=60000)

                # 等待 CF 验证通过
                for i in range(60):
                    title = await page.title()
                    if 'just a moment' not in title.lower() and 'checking' not in title.lower():
                        print(f'[Playwright] 页面加载完成，title: {title}')
                        break
                    await page.wait_for_timeout(1000)

                try:
                    await page.wait_for_load_state('networkidle', timeout=30000)
                except:
                    pass
                await page.wait_for_timeout(3000)

                # 填写账号密码
                print(f'[Playwright] 填写账号密码...')
                await page.fill('input#email', self.email, timeout=15000)
                await page.fill('input#password', self.passwd, timeout=15000)
                print(f'[Playwright] 已填写账号密码')

                # 点击验证元素
                verify_xpath = '//*[@id="app"]/section/div/div/div/div[2]/form/div/div[4]/div/div[1]/div/div[1]/div[1]'
                try:
                    await page.click(f'xpath={verify_xpath}', timeout=5000)
                    print(f'[Playwright] 已点击验证元素')
                    await page.wait_for_timeout(2000)
                except:
                    pass

                # 点击登录按钮
                login_xpath = '//*[@id="app"]/section/div/div/div/div[2]/form/div/div[6]/button'
                await page.click(f'xpath={login_xpath}', timeout=5000)
                print(f'[Playwright] 已点击登录按钮')

                await page.wait_for_timeout(5000)

                current_url = page.url
                if '/user' not in current_url and '/dashboard' not in current_url:
                    print(f'[登录]：{self.email} 登录失败\n\n')
                    await browser.close()
                    return

                print(f'[Playwright] 登录成功，当前URL: {current_url}')

                await self.sign_with_playwright(page)

                await browser.close()

            except Exception as e:
                print(f'[ERROR] 签到过程出错: {e}')
                await browser.close()


async def main():
    token = os.environ.get("ikuuu", "")
    if not token:
        print("❌ 未检测到 ikuuu 环境变量，程序退出")
        sys.exit(1)

    cks = [x.strip() for x in token.split("&") if x.strip()]
    print(f"✅ 检测到{len(cks)}个账号，开始ikuuu签到\n")

    all_results = []
    success_count = 0
    any_new_sign = False

    for idx, ck_all in enumerate(cks):
        ck = ck_all.split("#")
        if len(ck) != 2:
            print(f"❌ 第{idx+1}个账号格式错误：{ck_all}，跳过\n")
            all_results.append(f"账号{idx+1}: 格式错误")
            continue
        if idx > 0:
            await asyncio.sleep(random.uniform(3, 5))
        run = ikuuu(ck)
        await run.sign()
        if run.username and not run.login_error:
            success_count += 1
            if not run.already_signed:
                any_new_sign = True
                traffic_info = f"签到前: {run.traffic_before or '未知'}\n签到后: {run.traffic_after or '未知'}"
                all_results.append(f"{run.username}:\n{traffic_info}")

    print("✅ 所有账号处理完成\n")

    if any_new_sign:
        current_time = datetime.now().strftime('%m-%d %H:%M:%S')
        title = f'ikuuu 签到 {current_time}'

        content_lines = []
        for result in all_results:
            if "签到失败" not in result and "格式错误" not in result:
                content_lines.append(result)
        content = '\n\n'.join(content_lines) if content_lines else '无流量信息'

        send_bark(title, content)
    else:
        print("今天已全部签到过，不发送 Bark 通知")

    sys.exit(0 if success_count > 0 else 1)


if __name__ == '__main__':
    asyncio.run(main())
