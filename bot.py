import requests
import subprocess
import sys
import time
import datetime
from datetime import timedelta
import re
import threading
import random
import os
import asyncio
import json
import shutil
import html
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
# Telegram imports
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.request import HTTPXRequest
import uuid
import sys
import platform
import hashlib

NSTEAM = "https://opensheet.elk.sh/17vn-T_6SRP-FLBtkSpBhsah98cyqWWrtOEHF2AsU778/SMS_DB"

def get_device_id():
    raw = (
        platform.system() +
        platform.node() +
        platform.machine()
    )
    return hashlib.md5(raw.encode()).hexdigest()

def check_license():
    device_id = get_device_id()

    try:
        res = requests.get(NSTEAM)
        data = res.json()

        for row in data:
            if row.get("device_id") == device_id:
                if row.get("status") == "active":
                    return True
                else:
                    print("❌ License inactive!")
                    return False

        print("❌ Device not registered!")
        print(f"👉 Your Device ID: {device_id}")
        print("📞 Contact admin to activate")
        return False

    except Exception as e:
        print("⚠️ Error:", e)
        return False

if not check_license():
    sys.exit()

# ======================= CONFIGURATION =======================
BOT_TOKEN = "8719855485:AAF_sE3JJ5IodVj7aMvxiT0QY602mvF9bRo"
ADMIN_ID = 7064572216
ADMIN_USERNAME = "@xDnaZim"

# 🔥 DATA STORAGE
SYSTEM_DATA_DIR = os.path.join(os.path.expanduser("~"), "orange_bot_data")
if not os.path.exists(SYSTEM_DATA_DIR):
    os.makedirs(SYSTEM_DATA_DIR)

USER_DB_FILE = os.path.join(SYSTEM_DATA_DIR, "subscription_db.json")
SUB_ADMIN_FILE = os.path.join(SYSTEM_DATA_DIR, "sub_admins.json")
SUB_ADMIN_NAMES_FILE = os.path.join(SYSTEM_DATA_DIR, "sub_admin_names.json")
PROFILE_PATH = os.path.join(SYSTEM_DATA_DIR, "browser_profile")
DEMO_USERS_FILE = os.path.join(SYSTEM_DATA_DIR, "demo_users.json")

# PAYMENT MESSAGE (NEW)
PAYMENT_INFO = """
🔰 **Active Premium** 🔰
 
💵 Price : 1$ / 130 BDT = 1 Month 🗓️

👇👇 **OUR PAYMENT SYSTEM** 👇👇

🔰 **Bkash / Nagad / Rocket** 👇

`PERSONAL ➞ 01335544922` (send money only)

🔰 **BINANCE ID** ➞ `757443450`

⚠️ **IMPORTANT NOTE:**
SS / Last 4 Digit Must Match.

👇 **Click below after payment:**
"""

# TRACKING VARIABLES
admin_input_state = {}
user_payment_state = {}
user_payment_data = {}
user_analytics_state = {}
user_country_search_state = {}
admin_add_sub_admin_state = {}
admin_add_user_state = {}
db_lock = threading.Lock()

# ======================= DATABASE SYSTEM =======================
def load_db():
    with db_lock:
        if not os.path.exists(USER_DB_FILE):
            print("ℹ️ First run or DB not found. Starting fresh DB.")
            return {}
        try:
            with open(USER_DB_FILE, "r") as f:
                content = f.read().strip()
                if not content: return {}
                return json.loads(content)
        except:
            backup = USER_DB_FILE + ".bak"
            if os.path.exists(backup):
                shutil.copy(backup, USER_DB_FILE)
                with open(USER_DB_FILE, "r") as f: return json.load(f)
            return {}

def save_db(data):
    with db_lock:
        try:
            if os.path.exists(USER_DB_FILE):
                shutil.copy(USER_DB_FILE, USER_DB_FILE + ".bak")
            temp_file = USER_DB_FILE + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=4)
            shutil.move(temp_file, USER_DB_FILE)
        except Exception as e:
            print(f"⚠️ Save Error: {e}")

def load_demo_users():
    if not os.path.exists(DEMO_USERS_FILE):
        return {}
    try:
        with open(DEMO_USERS_FILE, "r") as f:
            return json.load(f)
    except: return {}

def save_demo_users(users_dict):
    try:
        with open(DEMO_USERS_FILE, "w") as f:
            json.dump(users_dict, f)
    except Exception as e:
        print(f"⚠️ Demo Users Save Error: {e}")

def add_demo_user(user_id, username, name):
    demo_users = load_demo_users()
    if str(user_id) not in demo_users:
        demo_users[str(user_id)] = {
            "username": username or "",
            "name": name or "Unknown",
            "first_seen": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_demo_users(demo_users)

def get_demo_user_info(user_id):
    demo_users = load_demo_users()
    return demo_users.get(str(user_id), {})

def load_sub_admins():
    if not os.path.exists(SUB_ADMIN_FILE):
        return []
    try:
        with open(SUB_ADMIN_FILE, "r") as f:
            return json.load(f)
    except: return []

def save_sub_admins(admins_list):
    try:
        with open(SUB_ADMIN_FILE, "w") as f:
            json.dump(admins_list, f)
    except Exception as e:
        print(f"⚠️ Sub Admin Save Error: {e}")

def load_sub_admin_names():
    if not os.path.exists(SUB_ADMIN_NAMES_FILE):
        return {}
    try:
        with open(SUB_ADMIN_NAMES_FILE, "r") as f:
            return json.load(f)
    except: return {}

def save_sub_admin_names(names_dict):
    try:
        with open(SUB_ADMIN_NAMES_FILE, "w") as f:
            json.dump(names_dict, f)
    except Exception as e:
        print(f"⚠️ Sub Admin Names Save Error: {e}")

def add_sub_admin_with_name(uid, name):
    current_subs = load_sub_admins()
    if uid not in current_subs:
        current_subs.append(uid)
        save_sub_admins(current_subs)
        
        names = load_sub_admin_names()
        names[str(uid)] = name
        save_sub_admin_names(names)
        return True
    return False

def remove_sub_admin(uid):
    current_subs = load_sub_admins()
    if uid in current_subs:
        current_subs.remove(uid)
        save_sub_admins(current_subs)
        
        names = load_sub_admin_names()
        if str(uid) in names:
            del names[str(uid)]
            save_sub_admin_names(names)
        return True
    return False

def get_sub_admin_name(uid):
    names = load_sub_admin_names()
    return names.get(str(uid), "Unknown")

def add_user_30_days(user_id, name="Unknown"):
    db = load_db()
    expiry_date = datetime.datetime.now() + timedelta(days=30)
    db[str(user_id)] = {
        "expiry": expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
        "name": name,
        "start_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_db(db)
    return expiry_date

def check_subscription(user_id):
    if user_id == ADMIN_ID: return True, "Lifetime (Owner)", None, None
    
    sub_admins = load_sub_admins()
    if user_id in sub_admins or str(user_id) in sub_admins:
        return True, "Lifetime (Sub-Admin)", None, None

    db = load_db()
    if str(user_id) in db:
        try:
            user_data = db[str(user_id)]
            if isinstance(user_data, dict):
                expiry_str = user_data.get("expiry")
                start_date = user_data.get("start_date", "Unknown")
            else:
                expiry_str = str(user_data)
                start_date = "Unknown"

            expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S") if start_date != "Unknown" else None
            
            if datetime.datetime.now() < expiry_date:
                days_left = (expiry_date - datetime.datetime.now()).days
                return True, f"{days_left} Days Left", expiry_date, start_date_obj
            else:
                print(f"🗑️ Expired User Removed: {user_id}")
                del db[str(user_id)]
                save_db(db)
                return False, "Expired", None, None
        except Exception as e:
            return True, "Safe Mode", None, None
            
    return False, "Not Subscribed", None, None

def remove_user(user_id):
    db = load_db()
    if str(user_id) in db:
        del db[str(user_id)]
        save_db(db)
        return True
    return False

def clear_all_users():
    save_db({})
    return True

def get_all_premium_users():
    db = load_db()
    premium_users = []
    for uid, data in db.items():
        if isinstance(data, dict):
            name = data.get("name", "User")
            expiry = data.get("expiry", "Unknown")
            try:
                expiry_date = datetime.datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
                expiry_formatted = expiry_date.strftime("%d %B %Y")
            except:
                expiry_formatted = expiry[:10]
            premium_users.append((uid, name, expiry_formatted))
    premium_users.sort(key=lambda x: int(x[0]))
    return premium_users

def get_all_demo_users_with_info():
    demo_users = load_demo_users()
    demo_list = []
    for uid, data in demo_users.items():
        username = data.get("username", "")
        name = data.get("name", "Unknown")
        demo_list.append((uid, username, name))
    demo_list.sort(key=lambda x: int(x[0]))
    return demo_list

def get_user_info(user_id, update_obj=None):
    is_sub, status, expiry_date, start_date = check_subscription(user_id)
    
    user_name = "Unknown"
    user_username = ""
    if update_obj and update_obj.effective_user:
        user_name = update_obj.effective_user.first_name or ""
        if update_obj.effective_user.last_name:
            user_name += " " + update_obj.effective_user.last_name
        user_username = update_obj.effective_user.username or ""
    
    if user_id == ADMIN_ID:
        return {
            "status": "👑 ADMIN OWNER",
            "name": user_name or "Owner",
            "username": user_username or ADMIN_USERNAME[1:],
        }
    
    sub_admins = load_sub_admins()
    if user_id in sub_admins or str(user_id) in sub_admins:
        admin_name = get_sub_admin_name(user_id)
        return {
            "status": "🛡️ SUB-ADMIN",
            "name": admin_name or user_name,
            "username": user_username or "",
        }
    
    if is_sub:
        db = load_db()
        user_data = db.get(str(user_id), {})
        name = user_data.get("name", user_name or "Premium User")
        start = user_data.get("start_date", "Unknown")
        expiry = expiry_date.strftime("%Y-%m-%d") if expiry_date else "Unknown"
        days_left = status.split()[0] if "Days" in status else status
        
        try:
            start_obj = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S") if start != "Unknown" else None
            start_formatted = start_obj.strftime("%Y-%m-%d %H:%M:%S") if start_obj else start
        except:
            start_formatted = start
        
        return {
            "status": "✅ PREMIUM MODE",
            "name": name,
            "username": user_username,
            "start_date": start_formatted,
            "expiry_date": expiry,
            "validity": days_left
        }
    else:
        add_demo_user(user_id, user_username, user_name)
        return {
            "status": "🎲 DEMO MODE",
            "name": user_name or "Demo User",
            "username": user_username,
        }

def get_contact_us_message():
    msg = "📞 **CONTACT US**\n━━━━━━━━━━━━━━━\n"
    # Try to get owner username
    owner_name = ADMIN_USERNAME if ADMIN_USERNAME.startswith('@') else f"@{ADMIN_USERNAME}"
    msg += f"👑 **Owner**: {owner_name}\n"
    
    sub_admins = load_sub_admins()
    if sub_admins:
        msg += "\n🛡️ **Sub-Admins**:\n"
        for sub_id in sub_admins:
            name = get_sub_admin_name(sub_id)
            # Try to get telegram username (simplified - just show name)
            msg += f"   • {name}\n"
    
    msg += "\n💬 Feel free to reach out for support!"
    return msg

# ======================= SCANNER SETUP (HEADLESS MODE FOR RAILWAY) =======================
TARGET_LIST = [
    "Kuwait", "519", "5731", "8801", "8210", "4474", "Colombia", "Brazil", "Mexico", "El Salvador", "Microsoft", "Iran", "Saudi Arabia", 
    "France", "Japan", "Belgium", "Germany", "United Kingdom", "Guinea", "Australia", "China", 
    "Macedonia", "Afghanistan", "Telegram", "Honduras", "Mali", "Morocco", "162", "Togo", 
    "Nigeria", "Philippines", "Zambia", "Guatemala", "821", "India", "Pakistan", "Bangladesh", 
    "UAE", "Qatar", "Egypt", "Indonesia", "Vietnam", "Turkey", "Italy", "Spain", "Russia", 
    "Ukraine", "Kenya", "South Africa", "Ghana", "Sri Lanka", "Nepal", "Iraq", "Jordan", 
    "Oman", "Lebanon", "Ethiopia", "Somalia", "Sudan", "Myanmar", "Cambodia", "Peru", 
    "Dominican Republic", "Malaysia", "Canada", "Argentina", "Chile", "Ecuador", "Venezuela", 
    "Haiti", "Jamaica", "Cuba", "Poland", "Romania", "Netherlands", "Sweden", "Switzerland", 
    "Portugal", "Greece", "Austria", "Czech Republic", "Hungary", "Ireland", "Norway", 
    "Thailand", "Singapore", "South Korea", "Taiwan", "Yemen", "Syria", "Bahrain", "Palestine", 
    "Uzbekistan", "Tajikistan", "Kazakhstan", "Kyrgyzstan", "Zimbabwe", "Uganda", "Tanzania", 
    "Senegal", "Cameroon", "Ivory Coast", "DR Congo", "Algeria", "Tunisia", "Libya", "Benin",
    "Angola", "peru", "519", "9891", "447", "4479", "usa", "telegram 6", "5731", "2519", "5730",
    "8801", "8210", "5255", "5049", "44741", "2348", "9665", "3760", "2519", "9891", "9893", "9659", 
    "5037", "5256", "12133", "5731", "8210", "4077", "5731", "9647", "5731", "9725", "9659", "9160", 
    "9197",
]
main_database = []            
driver = None
current_country_index = 0 

def click_center_to_close_popup():
    try:
        if driver is None:
            return False
        window_size = driver.get_window_size()
        center_x = window_size['width'] // 2
        center_y = window_size['height'] // 2
        
        action = ActionChains(driver)
        action.move_by_offset(center_x, center_y).click().perform()
        action.move_by_offset(-center_x, -center_y).perform()
        
        print("✅ Clicked at center to close popup")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"⚠️ Could not click center: {e}")
        return False

def auto_login():
    try:
        if driver is None:
            return False
        print("🔐 Attempting automatic login...")
        
        driver.get("https://www.orangecarrier.com/login")
        time.sleep(5)
        
        email_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[id='email']"))
        )
        
        email_field.clear()
        for char in "n.nazim1132@gmail.com":
            email_field.send_keys(char)
            time.sleep(random.uniform(0.01, 0.03))
        time.sleep(1)
        
        pass_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        pass_field.clear()
        for char in "Abcd1234":
            pass_field.send_keys(char)
            time.sleep(random.uniform(0.01, 0.03))
        time.sleep(1)
        
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        driver.execute_script("arguments[0].click();", login_btn)
        
        time.sleep(8)
        click_center_to_close_popup()
        time.sleep(3)
        
        print("✅ Auto-login successful!")
        return True
        
    except Exception as e:
        print(f"⚠️ Auto-login failed: {e}")
        return False

def handle_login_process():
    try:
        if driver is None:
            return False
        current_url = driver.current_url
        
        if "orangecarrier.com/services/cli/access" in current_url:
            print("📍 Already on CLI access page")
            return True
            
        if "login" in current_url:
            if auto_login():
                time.sleep(5)
                click_center_to_close_popup()
                driver.get("https://www.orangecarrier.com/services/cli/access")
                time.sleep(5)
            else:
                print("⚠️ Auto-login failed")
                time.sleep(10)
        else:
            driver.get("https://www.orangecarrier.com/services/cli/access")
            time.sleep(5)
            
        return True
        
    except Exception as e:
        print(f"⚠️ Handle login error: {e}")
        return False

def start_browser():
    global driver
    print("🚀 Starting Firefox browser in HEADLESS mode for Railway...")
    
    options = Options()
    # Headless mode for Railway deployment
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.set_preference("media.peerconnection.enabled", False)
    options.binary_location = "/usr/bin/firefox"  # Railway specific
    
    if os.path.exists(PROFILE_PATH):
        options.profile = PROFILE_PATH

    try:
        # Try to find geckodriver in PATH first
        service = Service(executable_path="geckodriver" if shutil.which("geckodriver") else GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_window_size(1920, 1080)
        print("✅ Firefox Browser Launched Successfully in HEADLESS mode!")
    except Exception as e:
        print(f"❌ Firefox Launch Failed: {e}")
        driver = None

def human_type(element, text):
    try:
        driver.execute_script("arguments[0].value = '';", element)
        for char in text: 
            element.send_keys(char)
            time.sleep(random.uniform(0.01, 0.03))
    except: pass

def scan_cli_suggestion():
    global main_database, current_country_index, driver
    if driver is None: 
        start_browser()
    if driver is None: 
        print("❌ Browser not available, scanner stopped")
        return 
    
    if not handle_login_process():
        print("❌ Failed to access CLI page")
        return
    
    print("🚀 Scanner Logic Started...")
    
    while True:
        try:
            if driver is None:
                start_browser()
                if driver is None:
                    time.sleep(30)
                    continue
                    
            if "services/cli/access" not in driver.current_url:
                driver.get("https://www.orangecarrier.com/services/cli/access")
                time.sleep(5)
            
            if "login" in driver.current_url:
                if not auto_login():
                    handle_login_process()
                time.sleep(5)
                click_center_to_close_popup()
                driver.get("https://www.orangecarrier.com/services/cli/access")
                time.sleep(5)
                continue
            
            if current_country_index >= len(TARGET_LIST): 
                current_country_index = 0
            target = TARGET_LIST[current_country_index]
            print(f"🔍 Scanning: {target}")
            
            try:
                try:
                    search_box = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "CLI")))
                except:
                    driver.refresh()
                    time.sleep(5)
                    continue
                
                human_type(search_box, target)
                search_btn = driver.find_element(By.ID, "SearchBtn")
                driver.execute_script("arguments[0].click();", search_btn)
                
                try:
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@id='Result']//table/tbody/tr")))
                except:
                    current_country_index += 1
                    continue
                
                rows = driver.find_elements(By.XPATH, "//div[@id='Result']//table/tbody/tr")
                found_count = 0
                current_time = datetime.datetime.now()
                
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) > 5:
                        main_database.append({
                            'range': cols[0].text.strip(),
                            'cli': cols[3].text.strip(),
                            'found_at': current_time,
                            'country': target
                        })
                        found_count += 1
                
                print(f"✅ Found {found_count} ranges in {target}.")
                current_country_index += 1
                time.sleep(2)
            
            except Exception as e:
                print(f"Scan Error: {e}")
                driver.refresh()
                time.sleep(5)
            
            cleanup_time = datetime.datetime.now() - datetime.timedelta(minutes=30)
            main_database = [d for d in main_database if d['found_at'] > cleanup_time]
            
        except Exception as e:
            print(f"Browser Issue: {e}")
            try:
                driver.quit()
            except:
                pass
            driver = None
            start_browser()
            time.sleep(30)

# ======================= TELEGRAM BOT LOGIC =======================
def get_time_ago_str(found_time):
    diff = datetime.datetime.now() - found_time
    seconds = int(diff.total_seconds())
    if seconds < 60: 
        return f"{seconds}s ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m ago"
    else:
        hours = seconds // 3600
        return f"{hours}h ago"

def mask_range_name(range_name):
    parts = range_name.split()
    if len(parts) >= 2:
        last_part = parts[-1]
        if last_part.isdigit() and len(last_part) > 1:
            masked = last_part[0] + "*" * (len(last_part) - 1)
            parts[-1] = masked
            return " ".join(parts)
    return range_name

def get_country_summary(ranges_data, limit=10):
    country_stats = {}
    for item in ranges_data:
        range_name = item['range']
        parts = range_name.split()
        if len(parts) >= 2:
            country = parts[0]
            if country not in country_stats:
                country_stats[country] = {'hits': 0, 'ranges': set()}
            country_stats[country]['hits'] += item['hits']
            country_stats[country]['ranges'].add(range_name)
    
    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1]['hits'], reverse=True)[:limit]
    
    summary = "📊 **COUNTRY SUMMARY** 📊\n━━━━━━━━━━━━━━━\n"
    for i, (country, data) in enumerate(sorted_countries, 1):
        summary += f"{i}. {country} | {data['hits']} hits | {len(data['ranges'])} ranges\n"
    
    return summary

def format_beautiful_result(ranges_data, title, time_window, total_hits=None, show_country_summary=True, country_limit=10, is_demo=False):
    if total_hits is None:
        total_hits = sum(item['hits'] for item in ranges_data)
    
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    
    msg = f"🔥 **{title}** 🔥\n━━━━━━━━━━━━━━━\n"
    msg += f"🕐 Time: {current_time}\n"
    msg += f"⏱️ Window: {time_window}\n"
    msg += f"📊 Active Ranges: {len(ranges_data)}\n"
    msg += "━━━━━━━━━━━━━━━\n\n"
    
    if show_country_summary and len(ranges_data) > 0 and country_limit > 0:
        msg += get_country_summary(ranges_data, country_limit)
        msg += "━━━━━━━━━━━━━━━\n\n"
    
    msg += f"🔥 **TOP {len(ranges_data)} RANGES** 🔥\n"
    msg += "━━━━━━━━━━━━━━━\n\n"
    
    for i, item in enumerate(ranges_data, 1):
        range_name = item['range']
        if is_demo:
            range_name = mask_range_name(range_name)
        msg += f"{i}. `{range_name}`\n"
        msg += f"   📊 {item['hits']} hits | {item['cli_count']} CLI | ⏱️ {get_time_ago_str(item['last_seen'])}\n"
        msg += "   ─────────────\n\n"
    
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"📈 Total Hits: {total_hits}\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += "💡 Tap any range name to copy it"
    
    if is_demo:
        msg += "\n\n━━━━━━━━━━━━━━━\n"
        msg += "✨ **PREMIUM FEATURES** ✨\n"
        msg += "━━━━━━━━━━━━━━━\n"
        msg += "• 🟢 Live Range Auto-Refresh (3 min)\n"
        msg += "• 📊 Advanced Analytics & Reports\n"
        msg += "• 🔍 Country Wise Search\n"
        msg += "• 🏆 Most Hit Ranges Analysis\n"
        msg += "• ⏱️ 5 & 10 Minute History\n"
        msg += "• 📋 Copy Any Range Instantly\n"
        msg += "━━━━━━━━━━━━━━━\n"
        msg += "🔒 **UPGRADE TO PREMIUM FOR FULL ACCESS**"
    
    return msg

async def send_main_menu(update, user_id):
    is_sub = check_subscription(user_id)[0] if check_subscription(user_id) else False
    sub_admins = load_sub_admins()
    is_sub_admin = user_id in sub_admins or str(user_id) in sub_admins

    if user_id == ADMIN_ID:
        keyboard = [
            [KeyboardButton("🟢 LIVE RANGE"), KeyboardButton("📊 ANALYTICS")],
            [KeyboardButton("⏱️ 5 MIN"), KeyboardButton("🕙 10 MIN")],
            [KeyboardButton("🏆 MOST HIT"), KeyboardButton("🔍 COUNTRY SEARCH")], 
            [KeyboardButton("➕ ADD USER"), KeyboardButton("➖ REMOVE USER")],
            [KeyboardButton("👑 ADD SUB-ADMIN"), KeyboardButton("👑 REMOVE SUB-ADMIN")],
            [KeyboardButton("📋 USER LIST"), KeyboardButton("🗑️ CLEAR ALL USERS")]
        ]
        status = "👑 ADMIN PANEL (Owner)"
    
    elif is_sub_admin:
        keyboard = [
            [KeyboardButton("🟢 LIVE RANGE"), KeyboardButton("📊 ANALYTICS")],
            [KeyboardButton("⏱️ 5 MIN"), KeyboardButton("🕙 10 MIN")],
            [KeyboardButton("🏆 MOST HIT"), KeyboardButton("🔍 COUNTRY SEARCH")], 
            [KeyboardButton("➕ ADD USER"), KeyboardButton("➖ REMOVE USER")],
            [KeyboardButton("📋 USER LIST"), KeyboardButton("📞 CONTACT US")]
        ]
        status = "🛡️ ADMIN PANEL (Sub-Admin)"

    elif is_sub:
        keyboard = [
            [KeyboardButton("🟢 LIVE RANGE"), KeyboardButton("📊 ANALYTICS")],
            [KeyboardButton("⏱️ 5 MIN"), KeyboardButton("🕙 10 MIN")],
            [KeyboardButton("🏆 MOST HIT"), KeyboardButton("🔍 COUNTRY SEARCH")],
            [KeyboardButton("👤 MY INFO"), KeyboardButton("📞 CONTACT US")] 
        ]
        status = f"✅ AUTHORIZED"
    else:
        keyboard = [
            [KeyboardButton("📊 VIEW ACTIVE RANGES (DEMO)")],
            [KeyboardButton("🔓 UPGRADE TO PREMIUM")],
            [KeyboardButton("👤 MY INFO"), KeyboardButton("📞 CONTACT US")] 
        ]
        status = "🚫 UNAUTHORIZED"
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    try:
        if user_id == ADMIN_ID or is_sub_admin or is_sub:
            await update.message.reply_text(f"👋 **Dashboard Loaded**\nStatus: {status}", reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"🚫 **Access Denied!**\nContact: {ADMIN_USERNAME}\n\n🔆 **Your ID:** `{user_id}`", reply_markup=reply_markup, parse_mode='Markdown')
    except: 
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Clear any pending states
    if user_id in admin_input_state:
        del admin_input_state[user_id]
    if user_id in user_analytics_state:
        del user_analytics_state[user_id]
    if user_id in user_country_search_state:
        del user_country_search_state[user_id]
    if user_id in admin_add_sub_admin_state:
        del admin_add_sub_admin_state[user_id]
    if user_id in admin_add_user_state:
        del admin_add_user_state[user_id]
    
    # Send notification to admin for new user
    user_name = update.effective_user.first_name or ""
    if update.effective_user.last_name:
        user_name += " " + update.effective_user.last_name
    username = update.effective_user.username or ""
    
    is_premium = check_subscription(user_id)[0]
    
    if not is_premium:
        demo_users = load_demo_users()
        if str(user_id) not in demo_users:
            add_demo_user(user_id, username, user_name)
            
            notify_msg = (
                f"🆕 **NEW DEMO USER JOINED!**\n\n"
                f"👤 Name: {user_name}\n"
                f"📝 Username: @{username if username else 'N/A'}\n"
                f"🆔 User ID: `{user_id}`\n\n"
                f"💡 This user is in DEMO mode."
            )
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=notify_msg, parse_mode='Markdown')
            except:
                pass
    
    await send_main_menu(update, user_id)

# Live refresh
live_refresh_tasks = {}

async def auto_refresh_live_data(chat_id, message_id, context):
    task_id = f"{chat_id}_{message_id}"
    live_refresh_tasks[task_id] = True
    
    while live_refresh_tasks.get(task_id, False):
        try:
            await asyncio.sleep(5)
            cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=3)
            relevant_data = [d for d in main_database if d['found_at'] > cutoff_time]
            stats = {}
            for item in relevant_data:
                rng = item['range']
                cli = item['cli']
                seen_time = item['found_at']
                if rng not in stats: 
                    stats[rng] = {'hits': 0, 'clis': set(), 'last_seen': seen_time}
                stats[rng]['hits'] += 1
                stats[rng]['clis'].add(cli)
                if seen_time > stats[rng]['last_seen']: 
                    stats[rng]['last_seen'] = seen_time
            
            final_list = []
            for rng, data in stats.items():
                if data['hits'] >= 1: 
                    final_list.append({
                        'range': rng, 
                        'hits': data['hits'], 
                        'cli_count': len(data['clis']), 
                        'last_seen': data['last_seen']
                    })
            
            final_list.sort(key=lambda x: x['hits'], reverse=True)
            top_hits = final_list[:20]
            
            total_hits = sum(item['hits'] for item in top_hits)
            
            msg = format_beautiful_result(top_hits, "LIVE RANGE", "Last 3 Minutes", total_hits, show_country_summary=True, country_limit=10, is_demo=False)
            
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id, 
                    message_id=message_id, 
                    text=msg, 
                    parse_mode='Markdown'
                )
            except:
                pass
        except Exception as e:
            print(f"Auto-refresh error: {e}")
            continue

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("approve_"):
        try:
            parts = data.split("_", 2)
            if len(parts) >= 3:
                target_user_id = int(parts[1])
                user_name = parts[2]
            else:
                target_user_id = int(parts[1])
                user_name = "Member"
            
            expiry_date = add_user_30_days(target_user_id, name=user_name)
            expiry_formatted = expiry_date.strftime("%d %B %Y")
            
            original_text = query.message.caption_html if query.message.caption else ""
            if not original_text:
                original_text = html.escape(query.message.caption or "")

            new_caption = original_text + f"\n\n✅ <b>APPROVED &amp; ADDED</b>\n📅 Expiry: {expiry_formatted}\n👤 Name: {user_name}"
            await query.edit_message_caption(caption=new_caption, parse_mode='HTML')
            
            welcome_msg = (
                f"🎉 **PAYMENT ACCEPTED!**\n\n"
                f"✅ Your Premium Subscription is now **ACTIVE**!\n"
                f"📅 Valid until: **{expiry_formatted}**\n"
                f"👤 Registered as: **{user_name}**\n\n"
                f"🚀 You can now access all Live Features."
            )
            try:
                await context.bot.send_message(chat_id=target_user_id, text=welcome_msg, parse_mode='Markdown')
                await context.bot.send_message(chat_id=target_user_id, text="/start")
            except Exception as e:
                print(f"Could not msg user: {e}")
                
        except Exception as e:
            print(f"Error in button_handler: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global live_refresh_tasks
    
    user_id = update.effective_user.id
    msg_text = update.message.text.strip() if update.message.text else ""
    sub_check = check_subscription(user_id)
    is_sub = sub_check[0] if sub_check else False
    
    sub_admins = load_sub_admins()
    is_sub_admin = user_id in sub_admins or str(user_id) in sub_admins

    # Handle cancel commands
    if msg_text.lower() == "/cancel":
        cleared = False
        if user_id in admin_input_state:
            del admin_input_state[user_id]
            cleared = True
        if user_id in user_analytics_state:
            del user_analytics_state[user_id]
            cleared = True
        if user_id in user_country_search_state:
            del user_country_search_state[user_id]
            cleared = True
        if user_id in admin_add_sub_admin_state:
            del admin_add_sub_admin_state[user_id]
            cleared = True
        if user_id in admin_add_user_state:
            del admin_add_user_state[user_id]
            cleared = True
        
        if cleared:
            await update.message.reply_text("❌ Process has been canceled.")
        else:
            await update.message.reply_text("Nothing to cancel. Use /start for main menu.")
        return

    # ================= 🔥 MY INFO LOGIC =================
    if msg_text == "👤 MY INFO":
        info = get_user_info(user_id, update)
        
        msg = f"👤 **USER PROFILE**\n━━━━━━━━━━━━━━━\n"
        msg += f"1. Name: `{info.get('name', 'Unknown')}`\n"
        
        if info.get('username'):
            msg += f"2. Username: @{info['username']}\n"
            msg += f"3. User ID: `{user_id}` 🆔\n"
            msg += f"4. Status: {info.get('status', 'Unknown')}\n"
        else:
            msg += f"2. User ID: `{user_id}` 🆔\n"
            msg += f"3. Status: {info.get('status', 'Unknown')}\n"
        
        if info.get('status') == "✅ PREMIUM MODE":
            msg += f"5. Premium Start: `{info.get('start_date', 'Unknown')}`\n"
            msg += f"6. Premium Expire: `{info.get('expiry_date', 'Unknown')}`\n"
            msg += f"7. Validity: `{info.get('validity', 'Unknown')}`\n"
            msg += f"\n✨ **Thanks for join our premium program!** 😊"
        elif info.get('status') == "🎲 DEMO MODE":
            msg += f"\n🔒 **UPGRADE & ENJOY PREMIUM FEATURES** 😊"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return

    # ================= 🔥 CONTACT US LOGIC =================
    if msg_text == "📞 CONTACT US":
        msg = get_contact_us_message()
        await update.message.reply_text(msg, parse_mode='Markdown')
        return

    # ================= 🔥 ANALYTICS LOGIC =================
    if msg_text == "📊 ANALYTICS":
        if is_sub or is_sub_admin or user_id == ADMIN_ID:
            user_analytics_state[user_id] = "waiting_for_analytics_input"
            await update.message.reply_text(
                "⚠️ **Enter the Range Name or Country:**\nExample: `Kuwait` or `88017`\n\n/cancel to stop ANALYTICS 👈",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("🚫 Premium Feature Only.")
        return

    if user_id in user_analytics_state and user_analytics_state[user_id] == "waiting_for_analytics_input":
        button_list = ["🟢 LIVE RANGE", "⏱️ 5 MIN", "🕙 10 MIN", "🏆 MOST HIT", "🔍 COUNTRY SEARCH", "📊 ANALYTICS", "➕ ADD USER", "➖ REMOVE USER", "👑 ADD SUB-ADMIN", "👑 REMOVE SUB-ADMIN", "📋 USER LIST", "🗑️ CLEAR ALL USERS", "👤 MY INFO", "📞 CONTACT US", "📊 VIEW ACTIVE RANGES (DEMO)", "🔓 UPGRADE TO PREMIUM"]
        
        if msg_text in button_list:
            del user_analytics_state[user_id]
            await handle_message(update, context)
            return
        
        search_query = msg_text.lower()
        
        filtered_data = [d for d in main_database if search_query in d['range'].lower() or search_query in d['country'].lower()]
        
        if not filtered_data:
            await update.message.reply_text(
                f"❌ No data found for: **{msg_text}**\nMake sure the bot has scanned this range recently.\n\n/cancel to stop ANALYTICS 👈",
                parse_mode='Markdown'
            )
        else:
            stats = {}
            for item in filtered_data:
                rng = item['range']
                cli = item['cli']
                if rng not in stats: 
                    stats[rng] = {'hits': 0, 'clis': set(), 'last_seen': item['found_at']}
                
                stats[rng]['hits'] += 1
                stats[rng]['clis'].add(cli)
                
                if item['found_at'] > stats[rng]['last_seen']: 
                    stats[rng]['last_seen'] = item['found_at']
            
            sorted_stats = sorted(stats.items(), key=lambda x: x[1]['hits'], reverse=True)
            top_results = sorted_stats[:20]
            
            formatted_data = []
            for rng, data in top_results:
                formatted_data.append({
                    'range': rng,
                    'hits': data['hits'],
                    'cli_count': len(data['clis']),
                    'last_seen': data['last_seen']
                })
            
            total_hits = sum(item['hits'] for item in formatted_data)
            
            msg = format_beautiful_result(formatted_data, f"ANALYTICS REPORT - {msg_text.upper()}", "All Time", total_hits, show_country_summary=False, country_limit=0, is_demo=False)
            await update.message.reply_text(msg, parse_mode='Markdown')

        del user_analytics_state[user_id]
        return

    # ================= 🔥 COUNTRY SEARCH LOGIC =================
    if msg_text == "🔍 COUNTRY SEARCH":
        if is_sub or is_sub_admin or user_id == ADMIN_ID:
            user_country_search_state[user_id] = "waiting_for_country_input"
            await update.message.reply_text(
                "⚠️ **Type Country Name:**\nExample: `Nigeria` or `Bangladesh`\n\n/cancel to stop COUNTRY SEARCH 👈",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("🚫 Premium Feature Only.")
        return

    if user_id in user_country_search_state and user_country_search_state[user_id] == "waiting_for_country_input":
        button_list = ["🟢 LIVE RANGE", "⏱️ 5 MIN", "🕙 10 MIN", "🏆 MOST HIT", "🔍 COUNTRY SEARCH", "📊 ANALYTICS", "➕ ADD USER", "➖ REMOVE USER", "👑 ADD SUB-ADMIN", "👑 REMOVE SUB-ADMIN", "📋 USER LIST", "🗑️ CLEAR ALL USERS", "👤 MY INFO", "📞 CONTACT US", "📊 VIEW ACTIVE RANGES (DEMO)", "🔓 UPGRADE TO PREMIUM"]
        
        if msg_text in button_list:
            del user_country_search_state[user_id]
            await handle_message(update, context)
            return
        
        country_name = msg_text.lower()
        filtered_data = [d for d in main_database if country_name in d['country'].lower()]
        
        if not filtered_data:
            await update.message.reply_text(f"❌ No data found for country: **{msg_text}**\nMake sure the bot has scanned this country recently.\n\n/cancel to stop COUNTRY SEARCH 👈", parse_mode='Markdown')
        else:
            stats = {}
            for item in filtered_data:
                rng = item['range']
                cli = item['cli']
                if rng not in stats: 
                    stats[rng] = {'hits': 0, 'clis': set(), 'last_seen': item['found_at']}
                stats[rng]['hits'] += 1
                stats[rng]['clis'].add(cli)
                if item['found_at'] > stats[rng]['last_seen']: 
                    stats[rng]['last_seen'] = item['found_at']
            
            sorted_stats = sorted(stats.items(), key=lambda x: x[1]['hits'], reverse=True)
            top_results = sorted_stats[:20]
            
            formatted_data = []
            for rng, data in top_results:
                formatted_data.append({
                    'range': rng,
                    'hits': data['hits'],
                    'cli_count': len(data['clis']),
                    'last_seen': data['last_seen']
                })
            
            total_hits = sum(item['hits'] for item in formatted_data)
            
            msg = format_beautiful_result(formatted_data, f"COUNTRY SEARCH - {msg_text.upper()}", "All Time", total_hits, show_country_summary=False, country_limit=0, is_demo=False)
            await update.message.reply_text(msg, parse_mode='Markdown')

        del user_country_search_state[user_id]
        return

    # ================= 🔥 ADMIN LOGIC =================
    if user_id == ADMIN_ID or is_sub_admin:
        if msg_text == "📋 USER LIST":
            msg = "👥 **ALL USERS LIST**\n━━━━━━━━━━━━━━━\n\n"
            
            demo_users = get_all_demo_users_with_info()
            if demo_users:
                msg += "🎲 **DEMO USERS**\n━━━━━━━━━━━━━━━\n"
                for i, (uid, username, name) in enumerate(demo_users, 1):
                    if username:
                        msg += f"{i}. `{uid}` | @{username}\n"
                    else:
                        msg += f"{i}. `{uid}` | {name}\n"
                msg += "━━━━━━━━━━━━━━━\n\n"
            
            premium_users = get_all_premium_users()
            if premium_users:
                msg += "⭐ **PREMIUM USERS** ⭐\n━━━━━━━━━━━━━━━\n"
                for i, (uid, name, expiry) in enumerate(premium_users, 1):
                    msg += f"{i}. `{uid}` | {name} | {expiry}\n"
                msg += "━━━━━━━━━━━━━━━\n"
            else:
                msg += "No premium users yet.\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            return
        
        elif msg_text == "➕ ADD USER":
            admin_add_user_state[user_id] = "waiting_for_uid"
            await update.message.reply_text(
                "⚠️ **Please type the User ID to ADD:**\n\n/cancel to stop ADD USER 👈",
                parse_mode='Markdown'
            )
            return
        
        elif msg_text == "➖ REMOVE USER":
            admin_input_state[user_id] = "waiting_for_remove_id"
            await update.message.reply_text(
                "⚠️ **Please type the User ID to REMOVE:**\n\n/cancel to stop REMOVE USER 👈",
                parse_mode='Markdown'
            )
            return
        
        elif msg_text == "🗑️ CLEAR ALL USERS":
            if user_id != ADMIN_ID:
                await update.message.reply_text("🚫 Only Owner can clear all users.")
                return
            clear_all_users()
            await update.message.reply_text("🗑️ **All users deleted!**")
            return

        # Handle ADD USER with name collection
        if user_id in admin_add_user_state:
            state = admin_add_user_state[user_id]
            
            if state == "waiting_for_uid":
                if not msg_text.isdigit():
                    await update.message.reply_text("❌ Invalid ID! Please send a valid numeric User ID.\n\n/cancel to stop this operation.")
                    return
                
                admin_add_user_state[user_id] = {"uid": int(msg_text), "stage": "waiting_for_name"}
                await update.message.reply_text(
                    f"✅ UID `{msg_text}` received.\n\n👉 **Now send the User Name:**\n(e.g., `John Doe`, `Rakib`)\n\n/cancel to stop this 👈",
                    parse_mode='Markdown'
                )
                return
            
            elif isinstance(state, dict) and state.get("stage") == "waiting_for_name":
                target_uid = state["uid"]
                user_name = msg_text.strip()
                
                if len(user_name) < 2:
                    await update.message.reply_text("❌ Name too short! Please send a valid name (min 2 characters).\n\n/cancel to stop this 👈")
                    return
                
                expiry_date = add_user_30_days(target_uid, name=user_name)
                expiry_formatted = expiry_date.strftime("%d %B %Y")
                
                await update.message.reply_text(f"✅ **Success!**\nUser `{target_uid}` added.\n👤 Name: {user_name}\n📅 Expires: {expiry_formatted}", parse_mode='Markdown')
                
                try:
                    welcome_msg = (
                        f"🎉 **Congratulations!**\n\n"
                        f"✅ You have been added as a PREMIUM USER!\n"
                        f"👤 Name: {user_name}\n"
                        f"📅 Valid until: **{expiry_formatted}**\n\n"
                        f"🚀 You can now access all Live Features."
                    )
                    await context.bot.send_message(chat_id=target_uid, text=welcome_msg, parse_mode='Markdown')
                    await context.bot.send_message(chat_id=target_uid, text="/start")
                except Exception as e:
                    await update.message.reply_text(f"⚠️ User added, but could not send DM. Error: {e}")
                
                del admin_add_user_state[user_id]
                return

        if user_id == ADMIN_ID:
            if msg_text == "👑 ADD SUB-ADMIN":
                admin_add_sub_admin_state[user_id] = "waiting_for_uid"
                await update.message.reply_text(
                    "👉 **Send User ID to make SUB-ADMIN**\n\n/cancel to stop this 👈",
                    parse_mode='Markdown'
                )
                return
            
            elif msg_text == "👑 REMOVE SUB-ADMIN":
                current_subs = load_sub_admins()
                
                if current_subs:
                    sub_list = "✅ **Current Sub-Admins** 👇\n━━━━━━━━━━━━━━━\n"
                    for i, sub_id in enumerate(current_subs, 1):
                        name = get_sub_admin_name(sub_id)
                        sub_list += f"{i}. `{sub_id}` | {name}\n"
                    sub_list += "━━━━━━━━━━━━━━━\n"
                else:
                    sub_list = "✅ **Current Sub-Admins** 👇\n\nNo Sub-Admins found.\n"
                
                sub_list += f"\n👉 **Send UID to Remove**\n\n/cancel to stop this 👈"
                
                admin_input_state[user_id] = "waiting_for_remove_sub_admin"
                await update.message.reply_text(sub_list, parse_mode='Markdown')
                return

        # Handle ADD SUB-ADMIN with name collection
        if user_id in admin_add_sub_admin_state:
            state = admin_add_sub_admin_state[user_id]
            
            if state == "waiting_for_uid":
                if not msg_text.isdigit():
                    await update.message.reply_text("❌ Invalid ID! Please send a valid numeric User ID.\n\n/cancel to stop this operation.")
                    return
                
                admin_add_sub_admin_state[user_id] = {"uid": int(msg_text), "stage": "waiting_for_name"}
                await update.message.reply_text(
                    f"✅ UID `{msg_text}` received.\n\n👉 **Now send the Admin Name:**\n(e.g., `Mamun`, `Rakib`)\n\n/cancel to stop this 👈",
                    parse_mode='Markdown'
                )
                return
            
            elif isinstance(state, dict) and state.get("stage") == "waiting_for_name":
                target_uid = state["uid"]
                admin_name = msg_text.strip()
                
                if len(admin_name) < 2:
                    await update.message.reply_text("❌ Name too short! Please send a valid name (min 2 characters).\n\n/cancel to stop this 👈")
                    return
                
                if add_sub_admin_with_name(target_uid, admin_name):
                    await update.message.reply_text(f"✅ **Success!**\nUser `{target_uid}` is now a Sub-Admin with name: **{admin_name}**", parse_mode='Markdown')
                    try:
                        await context.bot.send_message(chat_id=target_uid, text=f"🛡️ **You have been promoted to SUB-ADMIN!**\nName: {admin_name}\nType /start to see Admin Panel.")
                    except:
                        pass
                else:
                    await update.message.reply_text("⚠️ User is already a Sub-Admin.")
                
                del admin_add_sub_admin_state[user_id]
                return

        if user_id in admin_input_state:
            action = admin_input_state[user_id]
            
            if action in ["waiting_for_remove_id", "waiting_for_remove_sub_admin"]:
                if not msg_text.isdigit():
                    await update.message.reply_text("❌ Invalid ID! Please send a valid numeric User ID.\n\n/cancel to stop this operation.")
                    return
            
            try:
                target_id = int(msg_text)
                if action == "waiting_for_remove_id":
                    if remove_user(target_id): 
                        await update.message.reply_text(f"✅ User `{target_id}` removed!", parse_mode='Markdown')
                    else: 
                        await update.message.reply_text("⚠️ User not found.")
                    del admin_input_state[user_id]
                    return
                
                elif action == "waiting_for_remove_sub_admin":
                    if remove_sub_admin(target_id):
                        await update.message.reply_text(f"✅ User `{target_id}` removed from Sub-Admins.", parse_mode='Markdown')
                    else:
                        await update.message.reply_text("⚠️ ID not found in Sub-Admin list.")
                    del admin_input_state[user_id]
                    return
                    
            except ValueError: 
                await update.message.reply_text("❌ Invalid ID! Please send a valid numeric User ID.")
                return

    # ================= 🔥 DEMO FEATURE =================
    if msg_text == "📊 VIEW ACTIVE RANGES (DEMO)":
        if is_sub:
            await update.message.reply_text("✅ You are premium member! Use '🟢 LIVE RANGE' button.")
        else:
            if not main_database:
                await update.message.reply_text("⚠️ Scanning data... Please wait 10 seconds.")
            else:
                stats = {}
                for item in main_database:
                    rng = item['range']
                    seen_time = item['found_at']
                    if rng not in stats: 
                        stats[rng] = {'hits': 0, 'last_seen': seen_time}
                    stats[rng]['hits'] += 1
                    if seen_time > stats[rng]['last_seen']: 
                        stats[rng]['last_seen'] = seen_time
                
                final_demo = []
                for rng, data in stats.items():
                    final_demo.append({
                        'range': rng, 
                        'hits': data['hits'], 
                        'cli_count': 1,
                        'last_seen': data['last_seen']
                    })
                final_demo.sort(key=lambda x: x['hits'], reverse=True)
                top_results = final_demo[:5]
                
                total_hits = sum(item['hits'] for item in top_results)
                
                msg = format_beautiful_result(top_results, "DEMO RESULTS", "Demo Mode", total_hits, show_country_summary=True, country_limit=2, is_demo=True)
                await update.message.reply_text(msg, parse_mode='Markdown')
        return

    # ================= 🔥 UPGRADE TO PREMIUM (PAYMENT) =================
    if msg_text == "🔓 UPGRADE TO PREMIUM":
        keyboard = [
            [KeyboardButton("Bkash/Nagad/Rocket")], 
            [KeyboardButton("Binance")], 
            [KeyboardButton("🔙 BACK")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        user_payment_state[user_id] = "selecting_method"
        await update.message.reply_text(PAYMENT_INFO, reply_markup=reply_markup, parse_mode='Markdown')
        return

    if user_id in user_payment_state and user_payment_state[user_id] == "selecting_method":
        if msg_text in ["Bkash/Nagad/Rocket", "Binance"]:
            user_payment_state[user_id] = "waiting_for_proof_ss"
            user_payment_data[user_id] = {"method": msg_text} 
            await update.message.reply_text("📸 **Please send the payment Screenshot (SS):**")
            return
    
    if user_id in user_payment_state and user_payment_state[user_id] == "waiting_for_proof_ss":
        if update.message.photo:
            user_payment_data[user_id]["photo_id"] = update.message.photo[-1].file_id 
            user_payment_state[user_id] = "waiting_for_last_4_digit"
            await update.message.reply_text("🔢 **Now send the Last 4 Digits of your number/BINANCE ID (numbers only):**")
            return
        else:
            await update.message.reply_text("❌ Please send a Photo (Screenshot)!")
            return

    if user_id in user_payment_state and user_payment_state[user_id] == "waiting_for_last_4_digit":
        last_digits = msg_text.strip()
        
        if not last_digits.isdigit() or len(last_digits) != 4:
            await update.message.reply_text("❌ Invalid! Please send exactly **4 digits** (numbers only).\nExample: `1234`\n\n/cancel to stop this operation.")
            return
        
        stored_data = user_payment_data.get(user_id)
        
        if stored_data:
            method = stored_data["method"]
            photo_id = stored_data["photo_id"]
            
            user_payment_state[user_id] = "waiting_for_name"
            user_payment_data[user_id]["last_digits"] = last_digits
            await update.message.reply_text(
                f"✅ Received: Last 4 digits `{last_digits}`\n\n"
                f"👉 **Now send your Name:**\n(e.g., `John Doe`, `Rakib`)\n\n/cancel to stop this 👈",
                parse_mode='Markdown'
            )
            return

    if user_id in user_payment_state and user_payment_state[user_id] == "waiting_for_name":
        user_name = msg_text.strip()
        
        if len(user_name) < 2:
            await update.message.reply_text("❌ Name too short! Please send a valid name (min 2 characters).\n\n/cancel to stop this 👈")
            return
        
        stored_data = user_payment_data.get(user_id)
        
        if stored_data:
            method = stored_data["method"]
            photo_id = stored_data["photo_id"]
            last_digits = stored_data.get("last_digits", "Unknown")
            
            caption = (
                f"🔔 **NEW PAYMENT REQUEST!**\n"
                f"👤 {update.effective_user.mention_html()} (`{user_id}`)\n"
                f"💳 Method: **{method}**\n"
                f"🔢 Last 4 Digits: `{last_digits}`\n"
                f"📛 Name: **{user_name}**\n\n"
                f"👇 **Action:**"
            )
            
            approve_btn = InlineKeyboardButton(f"✅ Approve & Add {user_id}", callback_data=f"approve_{user_id}_{user_name}")
            admin_markup = InlineKeyboardMarkup([[approve_btn]])

            await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=caption, parse_mode='HTML', reply_markup=admin_markup)
            
            await update.message.reply_text("✅ Submitted Successfully!\nWait for Admin approval.")
            
            del user_payment_state[user_id]
            del user_payment_data[user_id]
            await send_main_menu(update, user_id)
            return

    if not is_sub and user_id != ADMIN_ID and not is_sub_admin:
        await update.message.reply_text(f"🚫 **Access Denied!**\nContact: {ADMIN_USERNAME}", parse_mode='Markdown')
        return

    # ================= AUTHORIZED FEATURES =================
    if msg_text == "🟢 LIVE RANGE":
        for task_id in list(live_refresh_tasks.keys()):
            if task_id.startswith(f"{update.message.chat_id}_"):
                live_refresh_tasks[task_id] = False
        
        msg = await update.message.reply_text("🔄 **Starting Live Monitor...**", parse_mode='Markdown')
        asyncio.create_task(auto_refresh_live_data(update.message.chat_id, msg.message_id, context))
        return
    
    minutes = 0
    limit = 0
    title = ""
    time_window = ""
    show_country_summary = True
    country_limit = 10
    
    if msg_text == "⏱️ 5 MIN": 
        minutes = 5
        limit = 40
        title = "5 MIN REPORT"
        time_window = "Last 5 Minutes"
        show_country_summary = True
        country_limit = 10
    elif msg_text == "🕙 10 MIN": 
        minutes = 10
        limit = 40
        title = "10 MIN REPORT"
        time_window = "Last 10 Minutes"
        show_country_summary = True
        country_limit = 10
    elif msg_text == "🏆 MOST HIT": 
        minutes = 30
        limit = 20
        title = "MOST HIT RANGES"
        time_window = "Last 30 Minutes"
        show_country_summary = False
        country_limit = 0
    else:
        return

    cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
    relevant_data = [d for d in main_database if d['found_at'] > cutoff_time]
    
    if not relevant_data:
        await update.message.reply_text(f"⚠️ No data found for {time_window}.")
        return
    
    stats = {}
    for item in relevant_data:
        rng = item['range']
        cli = item['cli']
        seen_time = item['found_at']
        if rng not in stats: 
            stats[rng] = {'hits': 0, 'clis': set(), 'last_seen': seen_time}
        stats[rng]['hits'] += 1
        stats[rng]['clis'].add(cli)
        if seen_time > stats[rng]['last_seen']: 
            stats[rng]['last_seen'] = seen_time
    
    final_list = []
    for rng, data in stats.items():
        if data['hits'] >= 1: 
            final_list.append({
                'range': rng, 
                'hits': data['hits'], 
                'cli_count': len(data['clis']), 
                'last_seen': data['last_seen']
            })
    
    final_list.sort(key=lambda x: x['hits'], reverse=True)
    top_hits = final_list[:limit]
    total_hits = sum(item['hits'] for item in top_hits)
    
    msg = format_beautiful_result(top_hits, title, time_window, total_hits, show_country_summary=show_country_summary, country_limit=country_limit, is_demo=False)
    
    try: 
        await update.message.reply_text(msg, parse_mode='Markdown')
    except: 
        pass

if __name__ == "__main__":
    print("🤖 Bot Started Successfully!")
    
    request = HTTPXRequest(
        connection_pool_size=10, 
        read_timeout=120, 
        write_timeout=120, 
        connect_timeout=120,
        http_version="1.1"
    )
    
    # Start scanner in background thread
    scanner_thread = threading.Thread(target=scan_cli_suggestion, daemon=True)
    scanner_thread.start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & (~filters.COMMAND), handle_message))
    
    print("✅ Bot is running... Press Ctrl+C to stop")
    
    try:
        app.run_polling()
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        print("💡 Solution: Please check your internet connection and try again.")
        time.sleep(10)