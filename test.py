import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import re
import time
import traceback
import uuid
import requests
import random
import string
import json
import os
from io import BytesIO

# Cấu hình logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token bot Telegram của bạn
BOT_TOKEN = "8244606408:AAEs0lT6bVSyRnNxClcRGzgIg7ZSGewcsyY"

# Biến toàn cục - PROXY SUPPORT
PROXY_LIST = []
current_proxy_index = 0
proxies = None

# File lưu trữ accounts
ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    """Load accounts từ file JSON"""
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_accounts(accounts):
    """Lưu accounts vào file JSON"""
    with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

def set_proxy(proxy_url):
    """Set proxy từ URL trực tiếp"""
    global proxies, PROXY_LIST, current_proxy_index
    
    # Xử lý định dạng proxy
    if proxy_url:
        # Thêm http:// nếu chưa có
        if not proxy_url.startswith(('http://', 'https://')):
            proxy_url = f'http://{proxy_url}'
        
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Thêm vào danh sách proxy
        if proxy_url not in PROXY_LIST:
            PROXY_LIST.append(proxy_url)
            current_proxy_index = len(PROXY_LIST) - 1
        
        logger.info(f"Đã set proxy: {proxy_url}")
        return True
    return False

def remove_proxy():
    """Xóa proxy hiện tại"""
    global proxies
    proxies = None
    logger.info("Đã xóa proxy")

def rotate_proxy():
    """Xoay vòng proxy"""
    global current_proxy_index
    if PROXY_LIST:
        new_index = (current_proxy_index + 1) % len(PROXY_LIST)
        current_proxy_index = new_index
        set_proxy(PROXY_LIST[new_index])
        return True
    return False

def check_proxy_detailed(proxy_url=None):
    """
    Check proxy chi tiết với nhiều endpoint
    """
    test_proxies = proxies if proxy_url is None else {
        'http': proxy_url,
        'https': proxy_url
    }
    
    results = {
        'httpbin': {'status': '❌', 'time': 0, 'ip': ''},
        'google': {'status': '❌', 'time': 0},
        'instagram': {'status': '❌', 'time': 0}
    }
    
    # Test httpbin.org (cơ bản)
    try:
        start_time = time.time()
        response = requests.get('https://httpbin.org/ip', proxies=test_proxies, timeout=10)
        results['httpbin']['time'] = round((time.time() - start_time) * 1000, 2)
        if response.status_code == 200:
            results['httpbin']['status'] = '✅'
            results['httpbin']['ip'] = response.json().get('origin', 'Unknown')
    except:
        pass
    
    # Test Google (kiểm tra kết nối internet)
    try:
        start_time = time.time()
        response = requests.get('https://www.google.com', proxies=test_proxies, timeout=10)
        results['google']['time'] = round((time.time() - start_time) * 1000, 2)
        if response.status_code == 200:
            results['google']['status'] = '✅'
    except:
        pass
    
    # Test Instagram (kiểm tra block)
    try:
        start_time = time.time()
        response = requests.get('https://www.instagram.com', proxies=test_proxies, timeout=10)
        results['instagram']['time'] = round((time.time() - start_time) * 1000, 2)
        if response.status_code == 200:
            results['instagram']['status'] = '✅'
    except:
        pass
    
    return results

def test_proxy(proxy_url=None):
    """Test proxy có hoạt động không"""
    try:
        test_proxies = proxies if proxy_url is None else {
            'http': proxy_url,
            'https': proxy_url
        }
        response = requests.get('https://httpbin.org/ip', proxies=test_proxies, timeout=10)
        return response.status_code == 200
    except:
        return False

def generate_password(length=8):
    chars = string.ascii_letters + "@"
    password = ''.join(random.choice(chars) for _ in range(length))
    return password

def random_string(length=22):
    chars = string.ascii_letters + string.digits + "-_"
    return ''.join(random.choice(chars) for _ in range(length))

def generate_cookies1():
    cookies1 = {
        "csrftoken": random_string(22),
        "datr": random_string(24),
        "ig_did": str(uuid.uuid4()).upper(),
        "mid": random_string(26),
        "ig_nrcb": "1",
        "wd": "833x943",
        "ig_lang": "vi"
    }
    return cookies1

def random_chrome_version():
    major = random.randint(120, 139)
    minor = random.randint(0, 9)
    build = random.randint(4000, 8000)
    patch = random.randint(0, 150)
    return f"{major}.{minor}.{build}.{patch}"

def fake_chrome_headers(cookies):
    chrome_version = random_chrome_version()
    chrome_major = chrome_version.split(".")[0]

    models = ["ThinkPad T14", "VAIO Canvas", "HP EliteBook", "Dell XPS 15"]
    model = random.choice(models)

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.instagram.com",
        "priority": "u=1, i",
        "referer": "https://www.instagram.com/accounts/emailsignup/",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": f'"Google Chrome";v="{chrome_major}", "Chromium";v="{chrome_major}", "Not/A)Brand";v="99"',
        "sec-ch-ua-full-version-list": (
            f'"Google Chrome";v="{chrome_version}", '
            f'"Chromium";v="{chrome_version}", '
            f'"Not/A)Brand";v="99.0.0.0"'
        ),
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": f'"{model}"',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"10.0.0"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": (
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_version} Safari/537.36"
        ),
        "x-asbd-id": str(random.randint(100000, 999999)),
        "x-csrftoken": cookies.get("csrftoken", ""),
        "x-ig-app-id": "936619743392459",
        "x-ig-www-claim": "0",
        "x-instagram-ajax": str(random.randint(1000000000, 1999999999)),
        "x-requested-with": "XMLHttpRequest",
        "x-web-session-id": ":".join(
            ["".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=random.randint(5,7))) for _ in range(3)]
        )
    }
    return headers

# Khởi tạo cookies và headers
cookies = generate_cookies1()
headers = fake_chrome_headers(cookies)

ho_list = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan",
    "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"
]
ten_dem_list = [
    "Văn", "Hữu", "Đức", "Công", "Quốc", "Thành",
    "Thị", "Ngọc", "Thuỳ", "Phương", "Minh", "Anh"
]
ten_list = [
    "Nam", "Long", "Sơn", "Hùng", "Dũng", "Phong", "Quang", "Tuấn",
    "Lan", "Hoa", "Mai", "Hương", "Trang", "Dung", "Ngân", "Nhung"
]

def random_vietnamese_name():
    ho = random.choice(ho_list)
    ten_dem = random.choice(ten_dem_list)
    ten = random.choice(ten_list)
    return f"{ho} {ten_dem} {ten}"

def create(mail, username, code, mk):
    url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"

    data = {
        "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{mk}",
        "day": str(random.randint(1, 25)),
        "email": mail,
        "failed_birthday_year_count": "{}",
        "first_name": random_vietnamese_name(),
        "month": str(random.randint(1, 9)),
        "username": username,
        "year": str(random.randint(2000, 2006)),
        "client_id": cookies.get("mid"),
        "seamless_login_enabled": "1",
        "tos_version": "row",
        "force_sign_up_code": code,
        "extra_session_id": headers.get("extra_session_id"),
        "jazoest": "21818"
    }

    resp = requests.post(url, headers=headers, cookies=cookies, data=data, proxies=proxies, timeout=30)
    js = resp.json()

    print("Status:", resp.status_code)
    print("Response:", js)
    
    # Chuyển đổi cookies thành dict
    cookies_dict = {}
    for cookie in resp.cookies:
        cookies_dict[cookie.name] = cookie.value
    
    return js.get("account_created"), cookies_dict

def sendcode(mail):
    url = "https://www.instagram.com/api/v1/accounts/send_verify_email/"

    data = {
        "device_id": cookies.get("mid"),
        "email": mail,
        "jazoest": "21818"
    }

    resp = requests.post(url, headers=headers, cookies=cookies, data=data, proxies=proxies, timeout=30)
    print("Send Code Status:", resp.status_code)
    print("Send Code Response:", resp.json())
    return resp.json().get("email_sent")

def verycode(code, mail):
    url = "https://www.instagram.com/api/v1/accounts/check_confirmation_code/"

    data = {
        "code": code,
        "device_id": cookies.get("mid"),
        "email": mail,
        "jazoest": "21818"
    }

    resp = requests.post(url, headers=headers, cookies=cookies, data=data, proxies=proxies, timeout=30)
    dataa = resp.json()
    print("Verify Code Status:", resp.status_code)
    print("Verify Code Response:", dataa)
    return dataa.get("signup_code")

def get_username(mail):
    url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/"
    
    data = {
        "email": mail,
        "failed_birthday_year_count": "{}",
        "first_name": "",
        "username": "",
        "opt_into_one_tap": "false",
        "use_new_suggested_user_name": "true",
        "jazoest": "22766",
    }

    try:
        resp = requests.post(url, headers=headers, cookies=cookies, data=data, timeout=30, proxies=proxies)
        print("Get Username Status:", resp.status_code)
        js = resp.json()
        print("Get Username Response:", js)
        
        if js.get("username_suggestions"):
            suggestion = js["username_suggestions"][0]
            return str(suggestion) if suggestion else ""
        else:
            email_prefix = mail.split('@')[0]
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            return f"{email_prefix}_{random_suffix}"
            
    except Exception as e:
        print(f"Error in get_username: {e}")
        email_prefix = mail.split('@')[0]
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{email_prefix}_{random_suffix}"

def check_account_status_ultra_accurate(email, username, password):
    """
    Check cực kỳ chính xác trạng thái account với proxy support
    """
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # Phương pháp 1: Kiểm tra login và phát hiện checkpoint
            login_url = "https://www.instagram.com/api/v1/web/accounts/login/ajax/"
            
            login_data = {
                "username": username,
                "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}",
                "queryParams": "{}",
                "optIntoOneTap": "false"
            }
            
            login_headers = headers.copy()
            session = requests.Session()
            
            # Sử dụng proxy cho request
            if proxies:
                session.proxies.update(proxies)
            
            login_resp = session.post(login_url, headers=login_headers, data=login_data, 
                                    cookies=cookies, timeout=15)
            
            if login_resp.status_code == 200:
                login_data = login_resp.json()
                
                # PHÁT HIỆN CHECKPOINT - QUAN TRỌNG!
                if login_resp.url and "challenge" in login_resp.url:
                    return "🔴 CHECKPOINT", "Account bị checkpoint (yêu cầu xác minh)"
                
                if login_data.get("message") == "checkpoint_required":
                    return "🔴 CHECKPOINT", "Account bị checkpoint (yêu cầu xác minh)"
                
                if login_data.get("authenticated"):
                    user_id = login_data.get("userId")
                    
                    # Phương pháp 2: Kiểm tra profile sau khi login
                    profile_url = f"https://www.instagram.com/api/v1/users/{user_id}/info/"
                    profile_resp = session.get(profile_url, headers=headers, timeout=15)
                    
                    if profile_resp.status_code == 200:
                        return "🟢 LIVE", "Account hoạt động hoàn toàn bình thường"
                    else:
                        return "🟡 LIMITED", "Account live nhưng bị giới hạn"
                
                elif login_data.get("user") and not login_data.get("authenticated"):
                    if "checkpoint" in str(login_data):
                        return "🔴 CHECKPOINT", "Account bị checkpoint"
                    return "🔴 SUSPENDED", "Account bị suspended"
                
                else:
                    # Phương pháp 3: Kiểm tra public profile
                    public_url = f"https://www.instagram.com/{username}/?__a=1"
                    public_resp = session.get(public_url, headers=headers, timeout=15)
                    
                    if public_resp.status_code == 200:
                        return "🟡 SHADOW BAN", "Account bị shadow ban (chỉ thấy public)"
                    elif public_resp.status_code == 404:
                        return "🔴 DIE", "Account không tồn tại"
                    else:
                        return "🔴 DIE", "Account đã bị xóa/blocked"
            
            # Nếu request fail, xoay proxy và thử lại
            elif login_resp.status_code in [403, 429, 500, 502, 503]:
                logger.warning(f"Request bị block, đang xoay proxy...")
                if rotate_proxy():
                    continue
            
        except requests.exceptions.Timeout:
            if rotate_proxy() and attempt < max_retries - 1:
                continue
            return "⚪ TIMEOUT", "Timeout khi kiểm tra"
        except requests.exceptions.ConnectionError:
            if rotate_proxy() and attempt < max_retries - 1:
                continue
            return "⚪ CONNECTION_ERROR", "Lỗi kết nối"
        except Exception as e:
            logger.error(f"Lỗi khi check status: {e}")
            if rotate_proxy() and attempt < max_retries - 1:
                continue
    
    return "🔴 DIE", "Không thể xác định trạng thái sau nhiều lần thử"

# Dictionary để lưu trạng thái user
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {"step": "waiting_email"}
    
    keyboard = [
        [InlineKeyboardButton("📧 Đăng ký account mới", callback_data="register_new")],
        [InlineKeyboardButton("🔍 Check account status", callback_data="check_status")],
        [InlineKeyboardButton("📊 Quản lý account", callback_data="manage_accounts")],
        [InlineKeyboardButton("🔧 Proxy Manager", callback_data="proxy_manager")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    proxy_status = f"✅ {PROXY_LIST[current_proxy_index]}" if PROXY_LIST else "❌ No proxy"
    
    await update.message.reply_text(
        f"🤖 **Instagram Auto Register & Checker Bot**\n\n"
        f"🔧 **Proxy Status:** {proxy_status}\n"
        f"🎯 **Check Accuracy:** Ultra Accurate\n\n"
        f"Chọn chức năng bạn muốn sử dụng:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "register_new":
        user_sessions[user_id] = {"step": "waiting_email"}
        current_proxy = PROXY_LIST[current_proxy_index] if PROXY_LIST else "None"
        await query.edit_message_text(
            f"📧 **ĐĂNG KÝ ACCOUNT MỚI**\n\n"
            f"🔧 **Proxy đang dùng:** `{current_proxy}`\n\n"
            "Vui lòng gửi email để bắt đầu đăng ký Instagram.\n\n"
            "Bot sẽ tự động:\n"
            "• Tạo username\n• Generate password\n• Xác thực email\n• Đăng ký tài khoản\n• Check status chính xác"
        )
        
    elif data == "manage_accounts":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        if not user_accounts:
            await query.edit_message_text(
                "📭 **Bạn chưa có account nào.**\n\n"
                "Hãy đăng ký account mới để bắt đầu."
            )
            return
        
        # Tạo menu quản lý account
        keyboard = [
            [InlineKeyboardButton("📋 Xem danh sách account", callback_data="view_accounts")],
            [InlineKeyboardButton("🗑️ Xóa account", callback_data="delete_accounts")],
            [InlineKeyboardButton("📤 Export accounts", callback_data="export_accounts")],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        total_accounts = len(user_accounts)
        live_accounts = sum(1 for acc in user_accounts.values() if acc.get('status') == '🟢 LIVE')
        
        await query.edit_message_text(
            f"📊 **QUẢN LÝ ACCOUNT**\n\n"
            f"• 📧 Tổng số account: {total_accounts}\n"
            f"• 🟢 Account LIVE: {live_accounts}\n"
            f"• 🔴 Account DIE: {total_accounts - live_accounts}\n\n"
            f"Chọn chức năng quản lý:",
            reply_markup=reply_markup
        )
        
    elif data == "view_accounts":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        if not user_accounts:
            await query.edit_message_text("📭 Bạn chưa có account nào.")
            return
        
        # Hiển thị danh sách account với phân trang
        page = int(context.user_data.get('account_page', 0))
        accounts_list = list(user_accounts.items())
        items_per_page = 5
        total_pages = (len(accounts_list) + items_per_page - 1) // items_per_page
        
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_accounts = accounts_list[start_idx:end_idx]
        
        accounts_text = f"📋 **DANH SÁCH ACCOUNT CỦA BẠN**\n\n"
        accounts_text += f"📄 Trang {page + 1}/{total_pages}\n\n"
        
        for i, (acc_id, acc_data) in enumerate(current_accounts, start_idx + 1):
            email = acc_data.get('email', 'Unknown')
            username = acc_data.get('username', 'Unknown')
            password = acc_data.get('password', 'Unknown')
            status = acc_data.get('status', '⚪ UNKNOWN')
            created_time = time.strftime('%d/%m/%Y %H:%M', time.localtime(acc_data.get('created_at', time.time())))
            
            accounts_text += f"**#{i}** {status}\n"
            accounts_text += f"👤 **Username:** `{username}`\n"
            accounts_text += f"📧 **Email:** `{email}`\n"
            accounts_text += f"🔑 **Password:** `{password}`\n"
            accounts_text += f"⏰ **Tạo lúc:** {created_time}\n"
            accounts_text += f"🆔 **ID:** `{acc_id[:8]}...`\n"
            accounts_text += "─" * 30 + "\n"
        
        # Tạo nút phân trang
        keyboard = []
        if page > 0:
            keyboard.append([InlineKeyboardButton("⬅️ Trang trước", callback_data=f"page_{page-1}")])
        if end_idx < len(accounts_list):
            keyboard.append([InlineKeyboardButton("Trang sau ➡️", callback_data=f"page_{page+1}")])
        
        keyboard.append([InlineKeyboardButton("🔄 Làm mới", callback_data="view_accounts")])
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="manage_accounts")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(accounts_text, reply_markup=reply_markup)
        
    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        context.user_data['account_page'] = page
        await button_handler(update, context)
        
    elif data == "delete_accounts":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        if not user_accounts:
            await query.edit_message_text("📭 Bạn chưa có account nào để xóa.")
            return
        
        # Tạo menu xóa account
        keyboard = []
        for acc_id, acc_data in list(user_accounts.items())[:10]:  # Giới hạn 10 account
            username = acc_data.get('username', 'Unknown')
            status = acc_data.get('status', '⚪ UNKNOWN')
            keyboard.append([InlineKeyboardButton(f"🗑️ {status} @{username}", callback_data=f"delete_{acc_id}")])
        
        keyboard.append([InlineKeyboardButton("🗑️ Xóa tất cả DIE", callback_data="delete_all_die")])
        keyboard.append([InlineKeyboardButton("🗑️ Xóa tất cả", callback_data="delete_all_confirm")])
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="manage_accounts")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        total_accounts = len(user_accounts)
        die_accounts = sum(1 for acc in user_accounts.values() if acc.get('status') in ['🔴 DIE', '🔴 CHECKPOINT', '🔴 SUSPENDED'])
        
        await query.edit_message_text(
            f"🗑️ **XÓA ACCOUNT**\n\n"
            f"⚠️ **CẢNH BÁO:** Hành động này không thể hoàn tác!\n\n"
            f"• 📧 Tổng số account: {total_accounts}\n"
            f"• 🔴 Account DIE: {die_accounts}\n"
            f"• 🟢 Account LIVE: {total_accounts - die_accounts}\n\n"
            f"Chọn account để xóa:",
            reply_markup=reply_markup
        )
        
    elif data.startswith("delete_"):
        acc_id = data.split("_")[1]
        accounts = load_accounts()
        
        if acc_id in accounts and str(user_id) in accounts[acc_id].get('owners', []):
            account = accounts[acc_id]
            username = account.get('username', 'Unknown')
            
            # Xác nhận xóa
            keyboard = [
                [InlineKeyboardButton("✅ XÓA NGAY", callback_data=f"confirm_delete_{acc_id}")],
                [InlineKeyboardButton("❌ HỦY", callback_data="delete_accounts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"⚠️ **XÁC NHẬN XÓA ACCOUNT**\n\n"
                f"Bạn có chắc chắn muốn xóa account này?\n\n"
                f"👤 **Username:** @{username}\n"
                f"📧 **Email:** {account.get('email', 'Unknown')}\n"
                f"🎯 **Status:** {account.get('status', 'Unknown')}\n\n"
                f"❌ **Hành động này không thể hoàn tác!**",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text("❌ Account không tồn tại hoặc không thuộc quyền sở hữu của bạn.")
            
    elif data.startswith("confirm_delete_"):
        acc_id = data.split("_")[2]
        accounts = load_accounts()
        
        if acc_id in accounts and str(user_id) in accounts[acc_id].get('owners', []):
            account = accounts[acc_id]
            username = account.get('username', 'Unknown')
            
            # Xóa account
            del accounts[acc_id]
            save_accounts(accounts)
            
            await query.edit_message_text(f"✅ **ĐÃ XÓA ACCOUNT THÀNH CÔNG**\n\n👤 @{username}\n\nAccount đã được xóa khỏi hệ thống.")
        else:
            await query.edit_message_text("❌ Account không tồn tại hoặc không thuộc quyền sở hữu của bạn.")
            
    elif data == "delete_all_die":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        if not user_accounts:
            await query.edit_message_text("📭 Bạn chưa có account nào.")
            return
        
        # Đếm account DIE - SỬA LỖI: Tìm account DIE trong user_accounts
        die_accounts = {}
        for acc_id, acc_data in user_accounts.items():
            if acc_data.get('status') in ['🔴 DIE', '🔴 CHECKPOINT', '🔴 SUSPENDED']:
                die_accounts[acc_id] = acc_data
        
        if not die_accounts:
            await query.edit_message_text("✅ Không có account DIE nào để xóa.")
            return
        
        # Xác nhận xóa tất cả DIE
        keyboard = [
            [InlineKeyboardButton(f"✅ XÓA {len(die_accounts)} ACCOUNT DIE", callback_data="confirm_delete_all_die")],
            [InlineKeyboardButton("❌ HỦY", callback_data="delete_accounts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        die_list = "\n".join([f"• @{acc.get('username')} - {acc.get('status')}" for acc in list(die_accounts.values())[:10]])
        if len(die_accounts) > 10:
            die_list += f"\n... và {len(die_accounts) - 10} account khác"
        
        await query.edit_message_text(
            f"⚠️ **XÁC NHẬN XÓA TẤT CẢ ACCOUNT DIE**\n\n"
            f"Bạn có chắc chắn muốn xóa **{len(die_accounts)}** account DIE?\n\n"
            f"📋 Danh sách account sẽ bị xóa:\n{die_list}\n\n"
            f"❌ **Hành động này không thể hoàn tác!**",
            reply_markup=reply_markup
        )
        
    elif data == "confirm_delete_all_die":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        # Tìm và xóa account DIE - SỬA LỖI: Xóa từ accounts chứ không phải user_accounts
        deleted_count = 0
        accounts_to_delete = []
        
        for acc_id, acc_data in user_accounts.items():
            if acc_data.get('status') in ['🔴 DIE', '🔴 CHECKPOINT', '🔴 SUSPENDED']:
                accounts_to_delete.append(acc_id)
        
        # Xóa tất cả account DIE
        for acc_id in accounts_to_delete:
            if acc_id in accounts:
                del accounts[acc_id]
                deleted_count += 1
        
        save_accounts(accounts)
        
        await query.edit_message_text(f"✅ **ĐÃ XÓA {deleted_count} ACCOUNT DIE THÀNH CÔNG**")
        
    elif data == "delete_all_confirm":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        if not user_accounts:
            await query.edit_message_text("📭 Bạn chưa có account nào.")
            return
        
        # Xác nhận xóa tất cả
        keyboard = [
            [InlineKeyboardButton(f"✅ XÓA TẤT CẢ {len(user_accounts)} ACCOUNT", callback_data="confirm_delete_all")],
            [InlineKeyboardButton("❌ HỦY", callback_data="delete_accounts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        account_list = "\n".join([f"• @{acc.get('username')} - {acc.get('status')}" for acc in list(user_accounts.values())[:10]])
        if len(user_accounts) > 10:
            account_list += f"\n... và {len(user_accounts) - 10} account khác"
        
        await query.edit_message_text(
            f"⚠️ **XÁC NHẬN XÓA TẤT CẢ ACCOUNT**\n\n"
            f"Bạn có chắc chắn muốn xóa **TẤT CẢ {len(user_accounts)}** account?\n\n"
            f"📋 Tất cả account của bạn sẽ bị xóa:\n{account_list}\n\n"
            f"❌ **Hành động này không thể hoàn tác!**",
            reply_markup=reply_markup
        )
        
    elif data == "confirm_delete_all":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        # Xóa tất cả account của user - SỬA LỖI: Xóa từ accounts chứ không phải user_accounts
        accounts_to_delete = list(user_accounts.keys())
        deleted_count = 0
        
        for acc_id in accounts_to_delete:
            if acc_id in accounts:
                del accounts[acc_id]
                deleted_count += 1
        
        save_accounts(accounts)
        
        await query.edit_message_text(f"✅ **ĐÃ XÓA TẤT CẢ {deleted_count} ACCOUNT THÀNH CÔNG**")
        
    elif data == "export_accounts":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        if not user_accounts:
            await query.edit_message_text("📭 Bạn chưa có account nào để export.")
            return
        
        # Tạo file export
        export_text = "📋 DANH SÁCH ACCOUNT INSTAGRAM\n\n"
        for i, (acc_id, acc_data) in enumerate(user_accounts.items(), 1):
            export_text += f"#{i}\n"
            export_text += f"Username: {acc_data.get('username', 'Unknown')}\n"
            export_text += f"Email: {acc_data.get('email', 'Unknown')}\n"
            export_text += f"Password: {acc_data.get('password', 'Unknown')}\n"
            export_text += f"Status: {acc_data.get('status', 'Unknown')}\n"
            export_text += f"Created: {time.strftime('%d/%m/%Y %H:%M', time.localtime(acc_data.get('created_at', time.time())))}\n"
            export_text += "─" * 40 + "\n"
        
        # Gửi dưới dạng file text
        export_file = BytesIO(export_text.encode('utf-8'))
        export_file.name = f"instagram_accounts_{user_id}_{int(time.time())}.txt"
        
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=export_file,
            filename=export_file.name,
            caption=f"📤 **EXPORT ACCOUNT THÀNH CÔNG**\n\nĐã export {len(user_accounts)} account của bạn."
        )
        
        await query.edit_message_text(f"✅ **ĐÃ EXPORT {len(user_accounts)} ACCOUNT THÀNH CÔNG**\n\nFile đã được gửi trong chat.")
        
    elif data == "check_status":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        if not user_accounts:
            await query.edit_message_text(
                "❌ Bạn chưa có account nào được lưu trữ.\n\n"
                "Vui lòng đăng ký account mới trước."
            )
            return
        
        # Tạo menu chọn account để check
        keyboard = []
        for acc_id, acc_data in list(user_accounts.items())[:10]:
            username = acc_data.get('username', 'Unknown')
            status = acc_data.get('status', '⚪ UNKNOWN')
            keyboard.append([InlineKeyboardButton(f"{status} @{username}", callback_data=f"check_{acc_id}")])
        
        keyboard.append([InlineKeyboardButton("🔄 Check tất cả", callback_data="check_all")])
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔍 **CHỌN ACCOUNT ĐỂ CHECK STATUS**\n\n"
            "Chọn account bạn muốn kiểm tra trạng thái:",
            reply_markup=reply_markup
        )
        
    elif data == "check_all":
        accounts = load_accounts()
        user_accounts = {k: v for k, v in accounts.items() if str(user_id) in v.get('owners', [])}
        
        if not user_accounts:
            await query.edit_message_text("❌ Bạn chưa có account nào.")
            return
            
        await query.edit_message_text("🔍 Đang kiểm tra tất cả account...")
        
        results = []
        total_accounts = len(user_accounts)
        
        # SỬA LỖI: Duyệt qua tất cả account và xử lý từng cái
        for i, (acc_id, account) in enumerate(user_accounts.items(), 1):
            email = account.get('email', '')
            username = account.get('username', '')
            password = account.get('password', '')
            
            # Cập nhật trạng thái đang check
            await query.edit_message_text(f"🔍 Đang kiểm tra account {i}/{total_accounts}\n👤 @{username}")
            
            # Thực hiện check status CHÍNH XÁC
            status, message = check_account_status_ultra_accurate(email, username, password)
            
            # Cập nhật trạng thái
            account['status'] = status
            account['last_check'] = time.strftime("%Y-%m-%d %H:%M:%S")
            account['status_message'] = message
            accounts[acc_id] = account
            
            results.append(f"{status} **@{username}** - {message}")
            
            # Delay và xoay proxy giữa các lần check (tránh bị block)
            if i < total_accounts:  # Không delay sau account cuối
                await asyncio.sleep(5)
                rotate_proxy()
        
        save_accounts(accounts)
        
        # Hiển thị kết quả
        result_text = "🔍 **KẾT QUẢ CHECK TẤT CẢ ACCOUNT**\n\n"
        for i, result in enumerate(results, 1):
            result_text += f"{i}. {result}\n"
            
        result_text += f"\n✅ Đã check {len(results)} account"
        
        await query.edit_message_text(result_text)
        
    elif data == "proxy_manager":
        keyboard = [
            [InlineKeyboardButton("➕ Thêm proxy", callback_data="add_proxy")],
            [InlineKeyboardButton("🔄 Xoay proxy", callback_data="rotate_proxy")],
            [InlineKeyboardButton("❌ Xóa proxy", callback_data="remove_proxy")],
            [InlineKeyboardButton("📊 Proxy info", callback_data="proxy_info")],
            [InlineKeyboardButton("🔍 Check proxy", callback_data="check_proxy")],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔧 **PROXY MANAGER**\n\n"
            "Quản lý proxy system:",
            reply_markup=reply_markup
        )
        
    elif data == "add_proxy":
        user_sessions[user_id] = {"step": "waiting_proxy"}
        await query.edit_message_text(
            "🔧 **THÊM PROXY**\n\n"
            "Vui lòng gửi proxy theo định dạng:\n"
            "• `username:password@ip:port`\n"
            "• `ip:port`\n"
            "• `http://ip:port`\n\n"
            "Ví dụ:\n"
            "• `123.456.789:8080`\n"
            "• `user:pass@123.456.789:8080`\n"
            "• `http://123.456.789:8080`\n\n"
            "Gửi CANCEL để hủy."
        )
        
    elif data == "rotate_proxy":
        if rotate_proxy():
            current_proxy = PROXY_LIST[current_proxy_index] if PROXY_LIST else "None"
            await query.edit_message_text(f"✅ Đã xoay proxy thành: `{current_proxy}`")
        else:
            await query.edit_message_text("❌ Không có proxy để xoay")
            
    elif data == "remove_proxy":
        remove_proxy()
        await query.edit_message_text("✅ Đã xóa proxy hiện tại")
            
    elif data == "proxy_info":
        if PROXY_LIST:
            info_text = f"🔧 **PROXY INFORMATION**\n\n"
            info_text += f"• **Total proxies:** {len(PROXY_LIST)}\n"
            info_text += f"• **Current proxy:** `{PROXY_LIST[current_proxy_index]}`\n"
            info_text += f"• **Index:** {current_proxy_index + 1}/{len(PROXY_LIST)}\n"
            
            # Test current proxy
            await query.edit_message_text(f"{info_text}\n🔄 Đang test proxy...")
            is_working = test_proxy()
            status = "✅ Working" if is_working else "❌ Not working"
            info_text += f"• **Status:** {status}"
            
            await query.edit_message_text(info_text)
        else:
            await query.edit_message_text("❌ Chưa có proxy nào được thêm vào")
    
    elif data == "check_proxy":
        if not PROXY_LIST:
            await query.edit_message_text("❌ Chưa có proxy nào để check")
            return
            
        current_proxy = PROXY_LIST[current_proxy_index]
        await query.edit_message_text(f"🔍 **ĐANG CHECK PROXY CHI TIẾT**\n\n`{current_proxy}`\n\nVui lòng chờ...")
        
        # Check proxy chi tiết
        results = check_proxy_detailed()
        
        result_text = f"🔍 **KẾT QUẢ CHECK PROXY**\n\n"
        result_text += f"🌐 **Proxy:** `{current_proxy}`\n\n"
        
        result_text += f"**📊 Chi tiết kết nối:**\n"
        result_text += f"• **HttpBin.org:** {results['httpbin']['status']} ({results['httpbin']['time']}ms)\n"
        if results['httpbin']['ip']:
            result_text += f"  → IP: `{results['httpbin']['ip']}`\n"
        
        result_text += f"• **Google.com:** {results['google']['status']} ({results['google']['time']}ms)\n"
        result_text += f"• **Instagram.com:** {results['instagram']['status']} ({results['instagram']['time']}ms)\n\n"
        
        # Đánh giá tổng quan
        working_tests = sum(1 for service in results.values() if service['status'] == '✅')
        if working_tests == 3:
            result_text += "🎯 **Đánh giá:** ✅ Proxy hoạt động hoàn toàn"
        elif working_tests >= 1:
            result_text += "⚠️ **Đánh giá:** Proxy hoạt động một phần"
        else:
            result_text += "❌ **Đánh giá:** Proxy không hoạt động"
        
        await query.edit_message_text(result_text)
        
    elif data == "help":
        await query.edit_message_text(
            "📖 **HƯỚNG DẪN SỬ DỤNG**\n\n"
            "🤖 **Chức năng chính:**\n"
            "• 📧 Đăng ký account mới\n"
            "• 🔍 Check account status\n"
            "• 📊 Quản lý account (xem, xóa, export)\n"
            "• 🔧 Quản lý proxy\n\n"
            "🎯 **Trạng thái account (CHÍNH XÁC):**\n"
            "• 🟢 LIVE: Hoạt động hoàn toàn\n"
            "• 🔴 CHECKPOINT: Bị yêu cầu xác minh\n"
            "• 🔴 SUSPENDED: Bị tạm ngưng\n"
            "• 🟡 SHADOW BAN: Bị giới hạn\n"
            "• 🔴 DIE: Account đã chết\n\n"
            "📊 **Quản lý Account:**\n"
            "• 📋 Xem danh sách đầy đủ (email + password)\n"
            "• 🗑️ Xóa account riêng lẻ\n"
            "• 🗑️ Xóa tất cả account DIE\n"
            "• 🗑️ Xóa tất cả account\n"
            "• 📤 Export account ra file text\n\n"
            "🔧 **Proxy Manager:**\n"
            "• ➕ Thêm proxy trực tiếp\n"
            "• 🔄 Xoay proxy tự động\n"
            "• ❌ Xóa proxy hiện tại\n"
            "• 📊 Thông tin proxy\n"
            "• 🔍 Check proxy chi tiết\n\n"
            "📞 **Hỗ trợ:** Liên hệ admin nếu có lỗi"
        )
        
    elif data == "back_to_main":
        keyboard = [
            [InlineKeyboardButton("📧 Đăng ký account mới", callback_data="register_new")],
            [InlineKeyboardButton("🔍 Check account status", callback_data="check_status")],
            [InlineKeyboardButton("📊 Quản lý account", callback_data="manage_accounts")],
            [InlineKeyboardButton("🔧 Proxy Manager", callback_data="proxy_manager")],
            [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        proxy_status = f"✅ {PROXY_LIST[current_proxy_index]}" if PROXY_LIST else "❌ No proxy"
        
        await query.edit_message_text(
            f"🤖 **Instagram Auto Register & Checker Bot**\n\n"
            f"🔧 **Proxy Status:** {proxy_status}\n"
            f"🎯 **Check Accuracy:** Ultra Accurate\n\n"
            f"Chọn chức năng bạn muốn sử dụng:",
            reply_markup=reply_markup
        )
        
    elif data.startswith("check_"):
        acc_id = data.split("_")[1]
        accounts = load_accounts()
        
        if acc_id in accounts:
            account = accounts[acc_id]
            email = account.get('email', '')
            username = account.get('username', '')
            password = account.get('password', '')
            
            await query.edit_message_text(f"🔍 Đang kiểm tra account @{username}...")
            
            # Thực hiện check status CHÍNH XÁC
            status, message = check_account_status_ultra_accurate(email, username, password)
            
            # Cập nhật trạng thái
            account['status'] = status
            account['last_check'] = time.strftime("%Y-%m-%d %H:%M:%S")
            account['status_message'] = message
            accounts[acc_id] = account
            save_accounts(accounts)
            
            current_proxy = PROXY_LIST[current_proxy_index] if PROXY_LIST else "None"
            
            result_text = (
                f"🔍 **KẾT QUẢ CHECK STATUS**\n\n"
                f"👤 **Username:** @{username}\n"
                f"📧 **Email:** {email}\n"
                f"🔑 **Password:** {password}\n\n"
                f"🎯 **Trạng thái:** {status}\n"
                f"📝 **Chi tiết:** {message}\n\n"
                f"⏰ **Thời gian check:** {account['last_check']}\n"
                f"🔧 **Proxy used:** `{current_proxy}`"
            )
            
            await query.edit_message_text(result_text)
        else:
            await query.edit_message_text("❌ Account không tồn tại.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {"step": "waiting_email"}
    
    session = user_sessions[user_id]
    
    try:
        if session["step"] == "waiting_email":
            if "@" in text and "." in text:
                session["email"] = text
                session["step"] = "processing"
                
                await update.message.reply_text("🔄 Đang xử lý email...")
                
                us = get_username(text)
                session["username"] = us
                session["password"] = generate_password()
                
                await update.message.reply_text(f"✅ Đã tạo username: `{us}`")
                
                await update.message.reply_text("🔄 Đang gửi mã xác nhận...")
                if sendcode(text):
                    session["step"] = "waiting_code"
                    await update.message.reply_text(
                        f"✅ **Đã gửi mã xác nhận!**\n\n"
                        f"📧 Email: `{text}`\n"
                        f"👤 Username: `{us}`\n"
                        f"🔑 Password: `{session['password']}`\n\n"
                        f"📨 **Vui lòng kiểm tra email và nhập mã xác nhận 6 số:**"
                    )
                else:
                    await update.message.reply_text("❌ Không gửi được mã xác nhận. Thử lại với email khác.")
                    session["step"] = "waiting_email"
                    
            else:
                await update.message.reply_text("❌ Email không hợp lệ. Vui lòng gửi email hợp lệ (ví dụ: example@gmail.com).")
                
        elif session["step"] == "waiting_code":
            if re.match(r'^\d{6}$', text):
                code = text
                email = session["email"]
                username = session["username"]
                password = session["password"]
                
                await update.message.reply_text("🔄 Đang xác thực mã và đăng ký...")
                
                signup_code = verycode(code, email)
                if signup_code:
                    await update.message.reply_text("🔄 Đang tạo tài khoản...")
                    reg, session_cookies = create(email, username, signup_code, password)
                    
                    if reg:
                        # Check status CHÍNH XÁC ngay sau khi tạo
                        await update.message.reply_text("🔍 Đang kiểm tra trạng thái account...")
                        status, message = check_account_status_ultra_accurate(email, username, password)
                        
                        # Lưu account vào database
                        accounts = load_accounts()
                        acc_id = str(uuid.uuid4())
                        accounts[acc_id] = {
                            'email': email,
                            'username': username,
                            'password': password,
                            'status': status,
                            'status_message': message,
                            'session_cookies': session_cookies,
                            'last_check': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'owners': [str(user_id)],
                            'created_at': time.time()
                        }
                        save_accounts(accounts)
                        
                        current_proxy = PROXY_LIST[current_proxy_index] if PROXY_LIST else "None"
                        
                        result_text = (
                            f"🎉 **ĐĂNG KÝ THÀNH CÔNG!**\n\n"
                            f"📧 **Email:** `{email}`\n"
                            f"👤 **Username:** `{username}`\n"
                            f"🔑 **Password:** `{password}`\n\n"
                            f"🔍 **Trạng thái:** {status}\n"
                            f"📝 **Chi tiết:** {message}\n\n"
                            f"🔧 **Proxy used:** `{current_proxy}`\n\n"
                            f"💾 Account đã được lưu vào danh sách. Sử dụng menu **Quản lý account** để xem chi tiết."
                        )
                        
                    else:
                        result_text = "❌ Đăng ký thất bại. Có thể email đã được sử dụng hoặc có lỗi xảy ra."
                else:
                    result_text = "❌ Mã xác nhận không hợp lệ hoặc đã hết hạn."
                
                await update.message.reply_text(result_text)
                user_sessions[user_id] = {"step": "waiting_email"}
                
            else:
                await update.message.reply_text("❌ Mã xác nhận phải là 6 chữ số. Vui lòng nhập lại:")
        
        elif session["step"] == "waiting_proxy":
            if text.lower() == "cancel":
                user_sessions[user_id] = {"step": "waiting_email"}
                await update.message.reply_text("✅ Đã hủy thêm proxy")
                return
                
            # Thêm proxy
            if set_proxy(text):
                # Test proxy chi tiết
                await update.message.reply_text("🔄 Đang test proxy chi tiết...")
                results = check_proxy_detailed()
                
                result_text = f"✅ **ĐÃ THÊM PROXY THÀNH CÔNG!**\n\n"
                result_text += f"🌐 **Proxy:** `{text}`\n\n"
                
                result_text += f"**📊 Kết quả test:**\n"
                result_text += f"• HttpBin.org: {results['httpbin']['status']} ({results['httpbin']['time']}ms)\n"
                if results['httpbin']['ip']:
                    result_text += f"  → IP: `{results['httpbin']['ip']}`\n"
                result_text += f"• Google.com: {results['google']['status']} ({results['google']['time']}ms)\n"
                result_text += f"• Instagram.com: {results['instagram']['status']} ({results['instagram']['time']}ms)\n"
                
                await update.message.reply_text(result_text)
            else:
                await update.message.reply_text("❌ Proxy không hợp lệ. Vui lòng thử lại.")
            
            user_sessions[user_id] = {"step": "waiting_email"}
                
    except Exception as e:
        await update.message.reply_text(f"❌ Có lỗi xảy ra: {str(e)}")
        logger.error(f"Error: {e}")
        traceback.print_exc()
        user_sessions[user_id] = {"step": "waiting_email"}

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Hướng dẫn sử dụng:**\n\n"
        "Sử dụng /start để mở menu chính với các chức năng:\n\n"
        "📧 **Đăng ký account mới:**\n"
        "• Tự động tạo username\n• Generate password\n• Xác thực email\n• Auto register\n• Auto check status\n\n"
        "🔍 **Check account status:**\n"
        "• Phát hiện CHECKPOINT chính xác\n• Nhận diện LIVE/DIE thực tế\n• Đa phương pháp xác minh\n• Tự động xoay proxy\n\n"
        "📊 **Quản lý Account (QUAN TRỌNG):**\n"
        "• 📋 Xem danh sách đầy đủ (email + password)\n"
        "• 🗑️ Xóa account riêng lẻ\n"
        "• 🗑️ Xóa tất cả account DIE\n"
        "• 🗑️ Xóa tất cả account\n"
        "• 📤 Export account ra file\n\n"
        "🔧 **Proxy Manager:**\n"
        "• ➕ Thêm proxy + auto test\n• 🔄 Xoay proxy tự động\n• ❌ Xóa proxy hiện tại\n• 📊 Thông tin proxy\n• 🔍 Check proxy chi tiết\n\n"
        "⚡ **Bot phiên bản 9.1 - Fixed Delete & Check All**"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(user_sessions)
    accounts = load_accounts()
    total_accounts = len(accounts)
    
    # Thống kê trạng thái
    status_count = {}
    for acc in accounts.values():
        status = acc.get('status', '⚪ UNKNOWN')
        status_count[status] = status_count.get(status, 0) + 1
    
    status_text = "\n".join([f"• {status}: {count}" for status, count in status_count.items()])
    
    proxy_status = f"{len(PROXY_LIST)} proxy" if PROXY_LIST else "No proxy"
    current_proxy = PROXY_LIST[current_proxy_index] if PROXY_LIST else "None"
    
    await update.message.reply_text(
        f"📊 **Bot Status:**\n\n"
        f"• 👥 Active users: {total_users}\n"
        f"• 📧 Total accounts: {total_accounts}\n"
        f"• 🔧 Proxy: {proxy_status}\n"
        f"• 🌐 Current: `{current_proxy}`\n"
        f"• 🟢 Bot: Online\n"
        f"• ⚡ Version: 9.1\n"
        f"• 🔍 Check: Ultra Accurate\n"
        f"• 🌐 Proxy Test: Full Support\n"
        f"• 📊 Account Management: Fixed Delete & Check All\n\n"
        f"**Thống kê trạng thái:**\n{status_text}"
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot đang chạy...")
    print("🔧 Proxy system: Full Support with Detailed Testing")
    print("📊 Account Management: Fixed Delete & Check All")
    if PROXY_LIST:
        print(f"🌐 Current proxy: {PROXY_LIST[current_proxy_index]}")
    
    application.run_polling()

if __name__ == '__main__':
    main()