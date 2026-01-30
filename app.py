import streamlit as st
import random
import time
import requests
import datetime
import json
import os
import io
from PIL import Image, ImageDraw, ImageFont

# 🌟 导入数据 (异常处理)
try:
    from recipe_data import RECIPES_DB, FRIDGE_CATEGORIES
except ImportError:
    st.error("❌ 严重错误：找不到 recipe_data.py 文件！请确保它和 app.py 在同一个文件夹内。")
    st.stop()

# ==========================================
# 1. 工程配置
# ==========================================
st.set_page_config(
    page_title="Bluey的美食魔法屋 v32.0",
    page_icon="🦴",
    layout="centered",
    initial_sidebar_state="auto"
)

# 📂 文件路径
HISTORY_FILE = "menu_history.json"
USER_DATA_FILE = "user_data.json"
FONT_FILE = "SimHei.ttf"

# ==========================================
# 2. 核心资源加载 (字体 & 数据)
# ==========================================
@st.cache_resource
def load_custom_font():
    """下载中文字体，确保图片生成不乱码"""
    if not os.path.exists(FONT_FILE):
        url = "https://github.com/StellarCN/scp_zh/raw/master/fonts/SimHei.ttf"
        try:
            r = requests.get(url, timeout=15) # 增加超时容错
            with open(FONT_FILE, "wb") as f: f.write(r.content)
        except: return ImageFont.load_default()
    return FONT_FILE

def get_pil_font(size):
    try: return ImageFont.truetype(load_custom_font(), size)
    except: return ImageFont.load_default()

def load_user_data():
    default = {
        "nickname": "Bingo", "age": "2岁", "height": "90", "weight": "13",
        "nutrition_goals": ["补钙"], "allergens": [], 
        "fridge_items": ["鸡蛋", "牛肉", "西红柿", "土豆"], 
        "pushplus_token": "", "dislikes": [], "likes": []
    }
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default.update(saved)
        except: pass
    return default

def save_user_data():
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.user_data, f, ensure_ascii=False, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history_item(menu_state):
    history = load_history()
    item = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "menu": {
            "breakfast": menu_state['breakfast']['name'],
            "lunch": [menu_state['lunch_meat']['name'], menu_state['lunch_veg']['name'], menu_state['lunch_soup']['name']],
            "dinner": [menu_state['dinner_meat']['name'], menu_state['dinner_veg']['name'], menu_state['dinner_soup']['name']],
            "fruit": menu_state['fruit']
        }
    }
    history.insert(0, item)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    st.toast("已收藏到历史", icon="✅")

# Init Session
if 'user_data' not in st.session_state: st.session_state.user_data = load_user_data()
if 'menu_state' not in st.session_state: st.session_state.menu_state = {"breakfast": None, "lunch_meat": None, "lunch_veg": None, "lunch_soup": None, "dinner_meat": None, "dinner_veg": None, "dinner_soup": None, "fruit": None, "shopping_list": []}
if 'view_mode' not in st.session_state: st.session_state.view_mode = "dashboard"
if 'focus_dish' not in st.session_state: st.session_state.focus_dish = None

# ==========================================
# 3. CSS 样式层 (V32.0 Final Optimized)
# ==========================================
st.markdown("""
<style>
    /* 1. 基础设置 */
    .stApp { background-color: #F5F5F7; }
    h1, h2, h3, h4, p, span, div, button { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}

    /* 2. 顶部 Header */
    .header-wrapper {
        display: flex; align-items: center; justify-content: space-between;
        padding: 5px 0 15px 0;
    }
    .header-left { display: flex; align-items: center; gap: 12px; }
    .header-img { width: 55px; height: 55px; border-radius: 50%; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .header-title { font-size: 22px; font-weight: 800; color: #1D1D1F; letter-spacing: -0.5px; }
    
    /* 顶部功能图标 */
    div[data-testid="column"] { flex: 1 !important; min-width: 0 !important; }
    .icon-btn button {
        border-radius: 12px !important; border: none !important;
        height: 40px !important; width: 40px !important;
        padding: 0 !important; margin: 0 auto !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        color: white !important; font-size: 18px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
    }
    
    /* 3. 生成按钮 */
    .gen-btn button {
        width: 100% !important; height: 50px !important; border-radius: 14px !important;
        background: #FF9F1C !important; color: white !important;
        font-size: 18px !important; font-weight: 700 !important; border: none !important;
        box-shadow: 0 4px 12px rgba(255, 159, 28, 0.3) !important;
        margin-top: 5px;
    }
    .hint-text { text-align: center; color: #999; font-size: 12px; margin-top: 8px; margin-bottom: 20px; }

    /* 4. 菜品卡片 (Row Layout) */
    .dish-card {
        background: white; border-radius: 20px; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04); overflow: hidden;
    }
    .card-header { padding: 10px; color: white; font-weight: 800; font-size: 16px; text-align: center; letter-spacing: 2px; }
    .bg-orange { background: #FF9F1C; } .bg-blue { background: #007AFF; } .bg-purple { background: #AF52DE; }

    /* ★★★ 核心：一行4按钮布局 ★★★ */
    
    /* 菜名 */
    .dish-name-text { 
        font-size: 16px; font-weight: 700; color: #1D1D1F; 
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        padding-left: 5px; line-height: 2.2;
    }

    /* 通用操作按钮 (圆形无框) */
    .action-btn button {
        background: transparent !important; border: none !important; 
        width: 32px !important; height: 32px !important; padding: 0 !important;
        font-size: 18px !important; color: #8E8E93 !important;
        box-shadow: none !important; margin: 0 auto !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        border-radius: 50% !important;
    }
    .action-btn button:hover { background: #F2F2F7 !important; }
    
    /* 状态高亮 */
    .btn-liked button { color: #FF3B30 !important; transform: scale(1.1); }
    .btn-disliked button { color: #333 !important; }
    
    /* 烹饪按钮 (品牌色小圆) - 视觉上稍微突出一点 */
    .cook-btn-small button {
        color: #007AFF !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }

    /* 食材条 */
    .ing-scroll { 
        display: flex; overflow-x: auto; gap: 6px; padding: 5px 15px 12px 15px;
        -webkit-overflow-scrolling: touch; scrollbar-width: none;
    }
    .ing-scroll::-webkit-scrollbar { display: none; }
    .ing-pill {
        background: #F2F2F7; color: #666; padding: 3px 10px; 
        border-radius: 10px; font-size: 12px; white-space: nowrap;
    }
    .ing-hit { background: #FFF4E5; color: #FF9500; }

    /* 历史卡片 */
    .hist-card { background: white; border-radius: 12px; padding: 12px; border: 1px solid #EEE; margin-bottom: 8px; }
    .hist-head { color: #FF9F1C; font-weight: bold; font-size: 13px; margin-bottom: 4px; }
    .hist-txt { font-size: 12px; color: #666; line-height: 1.4; }
    
    .receipt-card { background: #FFF; padding: 15px; border: 1px dashed #DDD; border-radius: 10px; font-size: 14px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 逻辑层
# ==========================================

SYNONYM_MAP = {"番茄": "西红柿", "洋柿子": "西红柿", "洋芋": "土豆", "马铃薯": "土豆", "大虾": "虾仁", "基围虾": "虾仁", "花菜": "西兰花", "圆白菜": "青菜", "白菜": "青菜", "娃娃菜": "青菜", "牛腩": "牛肉", "肥牛": "牛肉", "肉末": "猪肉", "里脊": "猪肉", "排骨": "猪肉", "鸡腿": "鸡肉", "鸡翅": "鸡肉", "龙利鱼": "鱼", "巴沙鱼": "鱼", "鳕鱼": "鱼"}
RED_MEAT = ["牛肉", "猪肉", "排骨", "羊肉", "猪肝"]

def normalize_ingredient(name): return SYNONYM_MAP.get(name.strip(), name.strip())
def mock_ocr_process(img): time.sleep(0.8); return ["西红柿", "基围虾", "娃娃菜"]

def toggle_feedback(dish_name, action):
    likes = st.session_state.user_data['likes']
    dislikes = st.session_state.user_data['dislikes']
    if action == 'like':
        if dish_name in likes: likes.remove(dish_name)
        else: 
            if dish_name not in likes: likes.append(dish_name)
            if dish_name in dislikes: dislikes.remove(dish_name)
    elif action == 'dislike':
        if dish_name in dislikes: dislikes.remove(dish_name)
        else:
            if dish_name not in dislikes: dislikes.append(dish_name)
            if dish_name in likes: likes.remove(dish_name)
    save_user_data()

def restock_from_shopping_list():
    needed = st.session_state.menu_state['shopping_list']
    if needed:
        cur = set(st.session_state.user_data['fridge_items']); cur.update(needed)
        st.session_state.user_data['fridge_items'] = list(cur); save_user_data()
        update_shopping_list(); st.success("已入库！"); time.sleep(0.5); st.rerun()

def get_random_dish(pool, fridge, allergens, exclude_names=[], prefer_type=None):
    safe = []
    norm_fridge = set([normalize_ingredient(i) for i in fridge] + fridge)
    for d in pool:
        if d['name'] in exclude_names: continue
        is_safe = True
        for ing in d['ingredients']:
            if ing in allergens: is_safe = False
        if not is_safe: continue
        if prefer_type == "white_meat":
            if any(ing in RED_MEAT for ing in d['ingredients']): continue
        
        miss = sum(1 for ing in d['ingredients'] if normalize_ingredient(ing) not in norm_fridge)
        dc = d.copy(); dc['missing_count'] = miss
        safe.append(dc)
    
    if not safe: return None
    tier0 = [d for d in safe if d['missing_count'] == 0]
    final = tier0 if tier0 else safe
    
    likes = st.session_state.user_data['likes']
    dislikes = st.session_state.user_data['dislikes']
    weighted = []
    for d in final:
        score = 10
        if d.get('missing_count') == 0: score += 50
        if d['name'] in likes: score += 100
        if d['name'] in dislikes: score = 1
        weighted.extend([d] * score)
    return random.choice(weighted) if weighted else None

def generate_full_menu():
    fridge = st.session_state.user_data['fridge_items']; allergies = st.session_state.user_data['allergens']; ms = st.session_state.menu_state
    ms['breakfast'] = get_random_dish(RECIPES_DB['breakfast'], fridge, allergies)
    ms['lunch_meat'] = get_random_dish(RECIPES_DB['lunch_meat'], fridge, allergies)
    ms['lunch_veg'] = get_random_dish(RECIPES_DB['lunch_veg'], fridge, allergies)
    ms['lunch_soup'] = get_random_dish(RECIPES_DB['soup'], fridge, allergies)
    
    lunch_ings = ms['lunch_meat']['ingredients'] if ms['lunch_meat'] else []
    is_red = any(normalize_ingredient(i) in RED_MEAT for i in lunch_ings)
    pool_dm = RECIPES_DB.get('dinner_meat', []) or RECIPES_DB['lunch_meat']
    pool_dv = RECIPES_DB.get('dinner_veg', []) or RECIPES_DB['lunch_veg']
    pref = "white_meat" if is_red else None
    
    ms['dinner_meat'] = get_random_dish(pool_dm, fridge, allergies, [ms['lunch_meat']['name']], pref) or get_random_dish(pool_dm, fridge, allergies, [ms['lunch_meat']['name']])
    ms['dinner_veg'] = get_random_dish(pool_dv, fridge, allergies)
    ms['dinner_soup'] = get_random_dish(RECIPES_DB['soup'], fridge, allergies, [ms['lunch_soup']['name']])
    ms['fruit'] = random.choice(RECIPES_DB['fruit'])
    update_shopping_list(); st.session_state.view_mode = "dashboard"

def update_shopping_list():
    norm_fridge = set([normalize_ingredient(i) for i in st.session_state.user_data['fridge_items']])
    needed = set()
    ms = st.session_state.menu_state
    for k, d in ms.items():
        if isinstance(d, dict):
            for ing in d.get('ingredients', []):
                if normalize_ingredient(ing) not in norm_fridge: needed.add(ing)
    st.session_state.menu_state['shopping_list'] = list(needed)

def swap_dish(key, pool_key):
    fridge = st.session_state.user_data['fridge_items']; allergies = st.session_state.user_data['allergens']
    curr = st.session_state.menu_state[key]; exclude = [curr['name']] if curr else []
    pool = RECIPES_DB.get(pool_key, [])
    if 'meat' in pool_key and not pool: pool = RECIPES_DB['lunch_meat']
    if 'veg' in pool_key and not pool: pool = RECIPES_DB['lunch_veg']
    new_d = get_random_dish(pool, fridge, allergies, exclude)
    if new_d: st.session_state.menu_state[key] = new_d; update_shopping_list()

# Image Gen
def create_menu_card_image(menu, nickname):
    width, height = 800, 1200
    img = Image.new('RGB', (width, height), color='#FFFDF5')
    draw = ImageDraw.Draw(img)
    title_font = get_pil_font(60); header_font = get_pil_font(40); text_font = get_pil_font(30); small_font = get_pil_font(24)
    draw.rectangle([30, 30, 770, 1170], outline="#D4AF37", width=3)
    draw.text((400, 100), f"{nickname} 的今日食谱", font=title_font, fill='#FF9F1C', anchor="mm")
    y = 220
    def draw_section(title, dishes):
        nonlocal y
        draw.text((400, y), f"— {title} —", font=header_font, fill='#333', anchor="mm")
        y += 60
        for dish in dishes:
            draw.text((400, y), dish, font=text_font, fill='#555', anchor="mm")
            y += 50
        y += 40
    draw_section("早餐", [menu['breakfast']['name'], "🥛 热牛奶"])
    draw_section("午餐", [menu['lunch_meat']['name'], menu['lunch_veg']['name'], menu['lunch_soup']['name']])
    draw_section("晚餐", [menu['dinner_meat']['name'], menu['dinner_veg']['name'], menu['dinner_soup']['name']])
    draw.text((400, y+30), f"🍎 加餐：{menu['fruit']}", font=text_font, fill='#555', anchor="mm")
    draw.text((400, height-50), "Generated by Bluey", font=small_font, fill='#CCC', anchor="mm")
    return img

def send_to_wechat(): st.toast("✅ 已推送到微信")
def generate_weekly(): st.toast("✅ 周计划已生成")
def enter_cook_mode(dish): st.session_state.focus_dish = dish; st.session_state.view_mode = "cook"
def exit_cook_mode(): st.session_state.view_mode = "dashboard"

# ==========================================
# 5. UI 视图渲染 (View)
# ==========================================

# 侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/color/480/dog.png", width=80)
    
    with st.expander("📝 档案设置 (含过敏原)", expanded=True):
        st.session_state.user_data['nickname'] = st.text_input("昵称", st.session_state.user_data['nickname'])
        c1, c2 = st.columns(2)
        st.session_state.user_data['height'] = c1.text_input("身高", st.session_state.user_data.get('height',''))
        st.session_state.user_data['weight'] = c2.text_input("体重", st.session_state.user_data.get('weight',''))
        
        default_al = ["牛奶", "奶粉", "牛肉", "鸡蛋", "虾", "鱼", "花生", "麦麸"]
        cur_al = st.session_state.user_data.get('allergens', [])
        sel_al = st.multiselect("过敏原", default_al, default=[x for x in cur_al if x in default_al])
        cust_al = st.text_input("其他", value=",".join([x for x in cur_al if x not in default_al]))
        
        st.session_state.user_data['pushplus_token'] = st.text_input("Token", st.session_state.user_data['pushplus_token'], type="password")
        if st.button("保存档案"):
            final = sel_al
            if cust_al: final.extend([x.strip() for x in cust_al.split(',') if x.strip()])
            st.session_state.user_data['allergens'] = list(set(final))
            save_user_data(); st.success("已保存")

    with st.expander("🧊 冰箱管理"):
        img = st.camera_input("拍照", label_visibility="collapsed")
        if img: 
            items = mock_ocr_process(img); cur = set(st.session_state.user_data['fridge_items']); cur.update(items)
            st.session_state.user_data['fridge_items'] = list(cur); save_user_data(); st.rerun()
        
        cur_f = st.session_state.user_data['fridge_items']
        new_f_std = []
        for c, l in FRIDGE_CATEGORIES.items():
            st.markdown(f"**{c}**")
            new_f_std.extend(st.multiselect(c, l, default=[x for x in l if x in cur_f], key=f"f_{c}", label_visibility="collapsed"))
        
        all_std = [x for l in FRIDGE_CATEGORIES.values() for x in l]
        cust = [x for x in cur_f if x not in all_std]
        st.markdown("**📝 其他**")
        kept_cust = st.multiselect("自定义", cust, default=cust, key="f_cust", label_visibility="collapsed")
        new_in = st.text_input("新增")
        if st.button("保存库存", use_container_width=True):
            if new_in: new_f_std.append(new_in)
            st.session_state.user_data['fridge_items'] = list(set(new_f_std))
            save_user_data(); st.rerun()

# 烹饪模式
if st.session_state.view_mode == "cook" and st.session_state.focus_dish:
    d = st.session_state.focus_dish
    st.button("⬅️ 返回", on_click=exit_cook_mode)
    st.markdown(f"""
    <div style="background:white; border-radius:20px; padding:20px; margin-top:10px;">
        <h2 style="text-align:center;">{d['name']}</h2>
        <div style="text-align:center; color:#888; margin:10px 0;">{d.get('time','--')} | {d.get('difficulty','--')}</div>
        <div style="background:#F9F9F9; padding:15px; border-radius:10px; margin-bottom:20px;">
            {' '.join([f'<span style="background:white; border:1px solid #EEE; padding:2px 8px; border-radius:8px; margin:2px; display:inline-block;">{i}</span>' for i in d['ingredients']])}
        </div>
        {''.join([f'<div style="margin-bottom:15px;"><b>{i+1}.</b> {s}</div>' for i,s in enumerate(d.get('steps_list',[]))])}
    </div>""", unsafe_allow_html=True)

# 仪表盘
else:
    # 顶部 Header
    c1, c2 = st.columns([6, 4])
    with c1:
        st.markdown(f"""
        <div class="header-wrapper">
            <div class="header-left">
                <img src="https://img.icons8.com/color/480/dog.png" class="header-img">
                <div class="header-title">Hi, {st.session_state.user_data['nickname']}!</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        b1, b2, b3 = st.columns(3)
        with b1:
            st.markdown('<div class="icon-btn" style="background:#007AFF !important;">', unsafe_allow_html=True)
            if st.session_state.menu_state['breakfast']:
                img = create_menu_card_image(st.session_state.menu_state, st.session_state.user_data['nickname'])
                buf = io.BytesIO(); img.save(buf, format="PNG")
                st.download_button("📥", buf.getvalue(), "menu.png", key="dl_btn")
            else: st.button("📥", disabled=True, key="dl_btn")
            st.markdown('</div>', unsafe_allow_html=True)
        with b2:
            st.markdown('<div class="icon-btn" style="background:#07C160 !important;">', unsafe_allow_html=True)
            if st.button("💬", key="wx_btn"): send_to_wechat()
            st.markdown('</div>', unsafe_allow_html=True)
        with b3:
            st.markdown('<div class="icon-btn" style="background:#FFCC00 !important;">', unsafe_allow_html=True)
            if st.button("📅", key="pl_btn"): generate_weekly()
            st.markdown('</div>', unsafe_allow_html=True)

    # 主生成按钮
    st.markdown('<div class="gen-btn">', unsafe_allow_html=True)
    if st.button("✨ 生成今日菜单"): 
        with st.spinner("..."): time.sleep(0.5); generate_full_menu()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-text">👆 点击生成菜单</div>', unsafe_allow_html=True)

    # 渲染卡片 (V32 最终修正: 4按钮一行)
    def render_card(title, bg_class, keys, pool_keys):
        st.markdown(f'<div class="dish-card"><div class="card-header {bg_class}">{title}</div>', unsafe_allow_html=True)
        
        for idx, key in enumerate(keys):
            d = st.session_state.menu_state[key]
            if not d: continue
            
            is_liked = d['name'] in st.session_state.user_data['likes']
            is_disliked = d['name'] in st.session_state.user_data['dislikes']
            
            # Row 1: 菜名(3.5) + 4 Buttons(6.5)
            # 比例调优以放下4个按钮
            c_name, c_act = st.columns([3.5, 6.5])
            
            with c_name:
                st.markdown(f'<div class="dish-name-text">{d["name"]}</div>', unsafe_allow_html=True)
            
            # 右侧：4按钮组 [爱] [不爱] [做法] [换]
            with c_act:
                b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                with b1: # 喜欢
                    st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                    label = "🙂"
                    if is_liked: label = "❤️"
                    cls = "btn-liked" if is_liked else ""
                    if st.button(label, key=f"lk_{key}"): toggle_feedback(d['name'], 'like'); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with b2: # 不喜欢
                    st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                    label = "😐"
                    if is_disliked: label = "⚫"
                    cls = "btn-disliked" if is_disliked else ""
                    if st.button(label, key=f"dl_{key}"): toggle_feedback(d['name'], 'dislike'); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with b3: # 做法 (图标)
                    st.markdown('<div class="action-btn cook-btn-small">', unsafe_allow_html=True)
                    if st.button("🍳", key=f"ck_{key}", help="做法"):
                        st.session_state.focus_dish = d
                        st.session_state.view_mode = "cook"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with b4: # 换菜
                    st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                    if st.button("🔄", key=f"sw_{key}"): swap_dish(key, pool_keys[idx]); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # Row 2: 食材条
            fridge = st.session_state.user_data['fridge_items']
            norm = [normalize_ingredient(i) for i in fridge]
            ing_html = ""
            for ing in d['ingredients']:
                hit = normalize_ingredient(ing) in norm
                cls = "ing-pill ing-hit" if hit else "ing-pill"
                ing_html += f'<span class="{cls}">{ing}</span>'
            
            st.markdown(f'<div class="ing-scroll">{ing_html}</div>', unsafe_allow_html=True)
            
            if idx < len(keys) - 1: st.markdown("<hr style='margin:5px 15px; border:0; border-top:1px solid #F0F0F0;'>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.menu_state['breakfast']:
        render_card("早 餐", "bg-orange", ['breakfast'], ['breakfast'])
        render_card("午 餐", "bg-blue", ['lunch_meat', 'lunch_veg', 'lunch_soup'], ['lunch_meat', 'lunch_veg', 'soup'])
        render_card("晚 餐", "bg-purple", ['dinner_meat', 'dinner_veg', 'dinner_soup'], ['dinner_meat', 'dinner_veg', 'soup'])
        
        # 缺货
        missing = st.session_state.menu_state['shopping_list']
        if missing:
            st.markdown(f"""
            <div class="receipt-card">
                <h4>🛒 缺货清单</h4>
                <p>{'、'.join(missing)}</p>
            </div>""", unsafe_allow_html=True)
            if st.button("📦 一键入库", use_container_width=True): restock_from_shopping_list()
        
        # 历史
        with st.expander("📜 历史收藏"):
            history = load_history()
            if not history: st.caption("暂无")
            else:
                for item in history:
                    st.markdown(f"""
                    <div class="hist-card">
                        <div class="hist-head">📅 {item['date']}</div>
                        <div class="hist-txt">
                        🌅 {item['menu']['breakfast']}<br>
                        ☀️ {item['menu']['lunch'][0]}...<br>
                        🌙 {item['menu']['dinner'][0]}...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("👆 点击上方按钮开始")