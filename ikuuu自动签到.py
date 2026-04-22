# ikuuu 自动签到 - Playwright 版本
# 变量名 ikuuu=账号1#密码1&账号2#密码2

import asyncio
import base64
import os
import random
import re
import sys
import time
from datetime import datetime

import requests
import urllib3
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# 关闭 SSL 警告
urllib3.disable_warnings()

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


async def get_waf_cookies_with_playwright(login_url: str):
    """使用 Playwright 获取 WAF cookies 并自动登录"""
    print(f'[Playwright] 启动浏览器访问: {login_url}')

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
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )

        page = await context.new_page()

        try:
            # 访问登录页面
            await page.goto(login_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # 等待页面完全加载（包括可能的 CF 验证）
            for i in range(30):
                title = await page.title()
                url = page.url
                print(f'[Playwright] 等待页面加载... {i+1}s, title: {title}, url: {url}')

                # 检查是否已通过 CF 验证（标题不再是 "Just a moment..."）
                if 'just a moment' not in title.lower() and 'checking' not in title.lower():
                    break

                await page.wait_for_timeout(1000)

            # 获取当前 cookies
            cookies = await context.cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies}
            print(f'[Playwright] 获取到 {len(cookie_dict)} 个 cookies: {list(cookie_dict.keys())}')

            await browser.close()
            return cookie_dict

        except Exception as e:
            print(f'[Playwright] 获取 cookies 失败: {e}')
            await browser.close()
            return None


async def auto_login_with_playwright(login_url: str, email: str, password: str):
    """使用 Playwright 自动填写表单并登录"""
    print(f'[Playwright] 自动登录: {email}')

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
            # 访问登录页面
            print(f'[Playwright] 访问登录页面...')
            await page.goto(login_url, wait_until='networkidle', timeout=30000)

            # 等待 CF 验证通过
            for i in range(30):
                title = await page.title()
                if 'just a moment' not in title.lower() and 'checking' not in title.lower():
                    print(f'[Playwright] 页面加载完成，title: {title}')
                    break
                await page.wait_for_timeout(1000)

            await page.wait_for_timeout(2000)

            # 检查是否有验证码
            captcha_selectors = [
                'img[src*="captcha"]',
                'img[id*="captcha"]',
                '.captcha',
                '#captcha',
                'input[name*="captcha"]',
                'input[placeholder*="验证码"]',
            ]

            has_captcha = False
            for selector in captcha_selectors:
                try:
                    captcha_elem = await page.query_selector(selector)
                    if captcha_elem:
                        has_captcha = True
                        print(f'[Playwright] 检测到验证码元素: {selector}')
                        break
                except:
                    continue

            if has_captcha:
                # 尝试读取验证码图片
                try:
                    # 先截图看页面状态
                    await page.screenshot(path='/tmp/ikuuu_login.png', full_page=True)
                    print(f'[Playwright] 已保存页面截图: /tmp/ikuuu_login.png')
                except Exception as e:
                    print(f'[Playwright] 截图失败: {e}')

                print(f'[Playwright] 检测到验证码，自动登录可能需要验证码处理')
                # 继续尝试，可能验证码不是强制的

            # 查找并填写邮箱输入框
            print(f'[Playwright] 填写登录表单...')
            try:
                # 尝试多种选择器
                email_selectors = [
                    'input[name="email"]',
                    'input[type="email"]',
                    'input#email',
                    'input[placeholder*="邮箱"]',
                    'input[placeholder*="Email"]',
                ]

                for selector in email_selectors:
                    try:
                        await page.fill(selector, email, timeout=2000)
                        print(f'[Playwright] 已填写邮箱: {selector}')
                        break
                    except:
                        continue

                # 查找并填写密码输入框
                passwd_selectors = [
                    'input[name="passwd"]',
                    'input[name="password"]',
                    'input[type="password"]',
                    'input#passwd',
                    'input#password',
                ]

                for selector in passwd_selectors:
                    try:
                        await page.fill(selector, password, timeout=2000)
                        print(f'[Playwright] 已填写密码: {selector}')
                        break
                    except:
                        continue

                # 点击验证元素（根据用户指定的XPath）
                verify_xpath = '//*[@id="app"]/section/div/div/div/div[2]/form/div/div[4]/div/div[1]/div/div[1]/div[1]'
                try:
                    await page.click(f'xpath={verify_xpath}', timeout=5000)
                    print(f'[Playwright] 已点击验证元素')
                    # 等待2秒
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f'[Playwright] 点击验证元素失败（可能不存在）: {e}')

                # 查找并点击登录按钮（根据用户指定的XPath）
                login_xpath = '//*[@id="app"]/section/div/div/div/div[2]/form/div/div[6]/button'
                try:
                    await page.click(f'xpath={login_xpath}', timeout=5000)
                    print(f'[Playwright] 已点击登录按钮（XPath）')
                except Exception as e:
                    print(f'[Playwright] 使用XPath点击登录按钮失败，尝试备用选择器: {e}')
                    # 备用选择器
                    login_btn_selectors = [
                        'button[type="submit"]',
                        'button:has-text("登录")',
                        'button:has-text("Login")',
                        '#app button',
                        'form button',
                    ]
                    for selector in login_btn_selectors:
                        try:
                            await page.click(selector, timeout=2000)
                            print(f'[Playwright] 已点击登录按钮: {selector}')
                            break
                        except:
                            continue

                # 点击登录按钮后等待导航或响应
                print(f'[Playwright] 等待登录响应...')

                # 等待网络请求完成
                try:
                    await page.wait_for_load_state('networkidle', timeout=15000)
                except:
                    pass

                # 额外等待确保登录请求完成
                await page.wait_for_timeout(5000)

                # 检查登录结果
                current_url = page.url
                title = await page.title()
                print(f'[Playwright] 当前URL: {current_url}, 标题: {title}')

                # 获取登录后的 cookies
                cookies = await context.cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies}
                print(f'[Playwright] Cookies: {list(cookie_dict.keys())}')

                # 判断是否登录成功（多种方式）
                success_markers = ['/user', '/dashboard', '/home', '/ucenter']
                if any(marker in current_url for marker in success_markers):
                    print(f'[Playwright] 登录成功！(URL 跳转)')
                    await browser.close()
                    return True, cookie_dict, current_url

                # 检查页面内容
                content = await page.content()
                if any(marker in content for marker in ['退出', 'logout', '用户中心', '个人信息', '签到']):
                    print(f'[Playwright] 登录成功！(页面内容)')
                    await browser.close()
                    return True, cookie_dict, current_url

                # 检查是否有登录错误提示
                error_markers = ['密码错误', '账号不存在', '登录失败', '验证码', '错误']
                if any(marker in content for marker in error_markers):
                    print(f'[Playwright] 登录失败：检测到错误提示')
                    # 提取错误信息
                    try:
                        error_elem = await page.query_selector('.alert, .error, .toast, [class*="error"], [class*="alert"]')
                        if error_elem:
                            error_text = await error_elem.text_content()
                            print(f'[Playwright] 错误信息: {error_text}')
                    except:
                        pass
                    await browser.close()
                    return False, cookie_dict, current_url

                # 检查 session cookie
                if cookie_dict.get('session') or cookie_dict.get('PHPSESSID') or cookie_dict.get('auth'):
                    print(f'[Playwright] 检测到登录会话 cookie，验证中...')
                    # 尝试访问用户中心验证
                    try:
                        await page.goto(f'{base_url}/user', wait_until='domcontentloaded', timeout=10000)
                        await page.wait_for_timeout(3000)
                        current_url = page.url
                        if '/user' in current_url:
                            print(f'[Playwright] 确认登录成功！')
                            cookies = await context.cookies()
                            cookie_dict = {c['name']: c['value'] for c in cookies}
                            await browser.close()
                            return True, cookie_dict, current_url
                    except Exception as e:
                        print(f'[Playwright] 验证跳转失败: {e}')

                print(f'[Playwright] 登录状态不确定，当前页面: {current_url}')
                await browser.close()
                return False, cookie_dict, current_url

            except Exception as e:
                print(f'[Playwright] 表单操作失败: {e}')
                await browser.close()
                return False, None, None

        except Exception as e:
            print(f'[Playwright] 自动登录失败: {e}')
            await browser.close()
            return False, None, None


class ikuuu:
    def __init__(self, ck):
        self.email = ck[0].strip() if len(ck) >= 2 else ""
        self.passwd = ck[1].strip() if len(ck) >= 2 else ""
        self.session = requests.Session()
        self.base_url = None
        self.login_error = ""
        self.username = None
        self.traffic_before = None  # 签到前流量
        self.traffic_after = None   # 签到后流量
        self.already_signed = False  # 是否已经签到过
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Connection': 'keep-alive'
        })

    def _decode_origin_body(self, html):
        match = re.search(r'var originBody = "([A-Za-z0-9+/=]+)";', html)
        if not match:
            return html
        try:
            return base64.b64decode(match.group(1)).decode('utf-8', 'ignore')
        except Exception:
            return html

    def _is_login_page(self, html):
        page = self._decode_origin_body(html)
        markers = [
            'name="email"',
            'name="password"',
            'url: "/auth/login"',
            '登录',
        ]
        return any(marker in page for marker in markers), page

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

    def resolve_base_url(self):
        if self.base_url:
            return self.base_url

        for base_url in DOMAIN_CANDIDATES:
            try:
                res = self.session.get(f'{base_url}/auth/login', timeout=15)
                is_login_page, decoded_page = self._is_login_page(res.text)
                if not is_login_page:
                    continue

                self.base_url = base_url
                self.session.headers.update({
                    'Referer': f'{base_url}/auth/login',
                    'Origin': base_url,
                })

                host_match = re.search(r'window\.location\.host', decoded_page)
                if host_match or 'name="password"' in decoded_page:
                    return self.base_url
            except Exception:
                continue

        raise RuntimeError('未找到可用的 ikuuu 登录域名')

    async def login_with_playwright(self):
        """使用 Playwright 自动登录"""
        try:
            base_url = self.resolve_base_url()
        except Exception as e:
            self.login_error = str(e)
            return False

        login_url = f'{base_url}/auth/login'

        # 使用 Playwright 自动登录
        success, cookies, final_url = await auto_login_with_playwright(
            login_url, self.email, self.passwd
        )

        if success and cookies:
            # 将 cookies 添加到 session
            for name, value in cookies.items():
                self.session.cookies.set(name, value, domain='ikuuu.org')
                self.session.cookies.set(name, value, domain='.ikuuu.org')

            # 更新请求头以匹配浏览器
            self.session.headers.update({
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Origin': base_url,
            })

            self.base_url = base_url
            return True
        else:
            self.login_error = 'Playwright 自动登录失败'
            return False

    def login(self, retry=3):
        """传统登录方式（备用）"""
        try:
            base_url = self.resolve_base_url()
        except Exception as e:
            self.login_error = str(e)
            return False

        login_url = f'{base_url}/auth/login'
        time.sleep(random.uniform(1, 3))
        for i in range(retry):
            try:
                page_loaded_at = str(int(time.time() * 1000) - random.randint(2000, 5000))
                self.session.get(login_url, timeout=15)
                data = {
                    'host': base_url.replace('https://', ''),
                    'email': self.email,
                    'passwd': self.passwd,
                    'code': '',
                    'remember_me': 'on',
                    'pageLoadedAt': page_loaded_at,
                }
                res = self.session.post(
                    login_url,
                    data=data,
                    headers={
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Origin': base_url,
                        'Referer': login_url,
                    },
                    timeout=15,
                    allow_redirects=False,
                )

                login_json = res.json()
                if login_json.get('ret') == 1:
                    return True
                if login_json.get('ret') == 2:
                    self.login_error = '账号开启了两步验证，脚本暂不支持自动输入验证码'
                else:
                    self.login_error = login_json.get('msg', '服务端返回未知错误')
                if i < retry - 1:
                    print(f"⚠️ 第{i+1}次登录失败，{self.email}，原因：{self.login_error}，重试中...")
                    time.sleep(random.uniform(2, 4))
            except Exception as e:
                self.login_error = str(e)
                if i < retry - 1:
                    print(f"⚠️ 第{i+1}次登录异常 {self.email}：{str(e)}，重试中...")
                    time.sleep(random.uniform(2, 4))
        return False

    async def sign_with_playwright(self, page, context):
        """使用 Playwright 在已登录页面执行签到"""
        try:
            # 访问用户中心页面
            user_url = f'{self.base_url}/user'
            await page.goto(user_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # 获取页面内容提取用户名和签到前流量
            content = await page.content()
            self.username, self.traffic_before = self._extract_user_info(content)
            print(f"[登录]：{self.username}\n[签到前流量]：{self.traffic_before}\n")

            # 尝试找到签到按钮并点击
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
                # 尝试直接访问签到API
                print('[Playwright] 未找到签到按钮，尝试直接调用签到API...')
                sign_url = f'{self.base_url}/user/checkin'

                # 执行签到请求
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
                # 获取点击后的页面内容或弹窗信息
                await page.wait_for_timeout(2000)
                content = await page.content()
                if '已经签到' in content or '已签到' in content:
                    self.already_signed = True
                    print(f"[签到]：今天已经签到过了\n")
                elif '签到成功' in content or '获得' in content:
                    print(f"[签到]：签到成功\n")
                else:
                    print(f"[签到]：已尝试签到\n")

            # 刷新页面获取签到后流量
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
        """签到"""
        # 使用 Playwright 登录并签到
        print(f"[INFO] 尝试 Playwright 自动登录并签到...")

        login_url = f'{self.base_url}/auth/login' if self.base_url else None

        # 重新获取 base_url 如果还没有
        if not self.base_url:
            try:
                self.resolve_base_url()
                login_url = f'{self.base_url}/auth/login'
            except Exception as e:
                print(f"[ERROR] 无法解析登录域名: {e}")
                return

        # 使用 Playwright 登录并在同一浏览器会话中签到
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
                # 访问登录页面
                print(f'[Playwright] 访问登录页面...')
                await page.goto(login_url, wait_until='domcontentloaded', timeout=60000)

                # 等待 CF 验证通过
                for i in range(60):
                    title = await page.title()
                    if 'just a moment' not in title.lower() and 'checking' not in title.lower():
                        print(f'[Playwright] 页面加载完成，title: {title}')
                        break
                    await page.wait_for_timeout(1000)

                # 等待页面完全加载
                try:
                    await page.wait_for_load_state('networkidle', timeout=30000)
                except:
                    pass
                await page.wait_for_timeout(3000)

                # 调试：截图并打印页面内容
                try:
                    await page.screenshot(path='/tmp/ikuuu_debug.png', full_page=True)
                    print(f'[DEBUG] 已保存截图: /tmp/ikuuu_debug.png')
                except:
                    pass

                content = await page.content()
                print(f'[DEBUG] 页面内容长度: {len(content)}')

                # 保存 HTML 用于调试
                with open('/tmp/ikuuu_debug.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'[DEBUG] 已保存 HTML: /tmp/ikuuu_debug.html')

                # 查找 passwd 相关的 HTML
                passwd_match = re.search(r'<input[^>]*name=["\']passwd["\'][^>]*>', content)
                if passwd_match:
                    print(f'[DEBUG] passwd 输入框 HTML: {passwd_match.group(0)}')

                # 检查是否有隐藏属性
                if 'type="hidden"' in content and 'passwd' in content:
                    print(f'[DEBUG] 页面中有隐藏的密码输入框')

                # 等待更长时间让页面完全渲染
                await page.wait_for_timeout(5000)

                # 检查页面是否有密码输入框
                try:
                    has_passwd = await page.is_visible('input[name="passwd"]', timeout=5000)
                    print(f'[DEBUG] 密码输入框可见: {has_passwd}')
                except Exception as e:
                    print(f'[DEBUG] 检查密码框失败: {e}')

                # 填写邮箱和密码（邮箱ID是email，密码框ID是password）
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

                # 等待登录完成
                await page.wait_for_timeout(5000)

                # 检查是否登录成功
                current_url = page.url
                if '/user' not in current_url and '/dashboard' not in current_url:
                    print(f'[登录]：{self.email} 登录失败\n\n')
                    await browser.close()
                    return

                print(f'[Playwright] 登录成功，当前URL: {current_url}')

                # 在同一浏览器会话中执行签到
                await self.sign_with_playwright(page, context)

                await browser.close()

            except Exception as e:
                print(f'[ERROR] 签到过程出错: {e}')
                await browser.close()

        return


async def main():
    token = os.environ.get("ikuuu", "")
    if not token:
        print("❌ 未检测到 ikuuu 环境变量，程序退出")
        sys.exit(1)

    cks = [x.strip() for x in token.split("&") if x.strip()]
    print(f"✅ 检测到{len(cks)}个账号，开始ikuuu签到\n")

    all_results = []
    success_count = 0
    any_new_sign = False  # 是否有新签到（非重复签到）

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
            # 只有新签到才记录流量变化
            if not run.already_signed:
                any_new_sign = True
                traffic_info = f"签到前: {run.traffic_before or '未知'}\n签到后: {run.traffic_after or '未知'}"
                all_results.append(f"{run.username}:\n{traffic_info}")

    print("✅ 所有账号处理完成\n")

    # 只有新签到时才发送 Bark 通知
    if any_new_sign:
        current_time = datetime.now().strftime('%m-%d %H:%M:%S')
        title = f'ikuuu 签到 {current_time}'

        # 构建流量详情内容
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
