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
# recipe_data.py
# V17.2 修正版：修复了食材与菜名不符的脏数据 (Data Cleaned)

RECIPES_DB = {
    # ==================================================
    # 🌅 早餐 (Breakfast)
    # ==================================================
    "breakfast": [
        {"name": "🎃 南瓜小米粥", "ingredients": ["南瓜", "小米"], "full_ingredients": "老南瓜 60g，小米 30g", "time": "25分钟", "difficulty": "⭐", "steps_list": ["小米泡20分钟。", "水开下米煮15分钟。", "下南瓜丁煮10分钟。", "压泥混合。"], "nutrition": "养胃", "tags": ["易消化"], "desc": "经典养胃"},
        {"name": "🥕 胡萝卜鸡蛋饼", "ingredients": ["胡萝卜", "鸡蛋", "面粉"], "full_ingredients": "胡萝卜，鸡蛋，面粉", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["胡萝卜擦丝焯水。", "调蛋糊。", "煎两面黄。"], "nutrition": "维A", "tags": ["手指食物"], "desc": "软嫩"},
        {"name": "🥔 土豆丝鸡蛋饼", "ingredients": ["土豆", "鸡蛋", "面粉"], "full_ingredients": "土豆，鸡蛋，面粉", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["土豆擦丝不洗。", "拌蛋液面粉。", "煎熟。"], "nutrition": "能量", "tags": ["焦香"], "desc": "香脆"},
        {"name": "🥛 牛奶燕麦粥", "ingredients": ["牛奶", "燕麦"], "full_ingredients": "牛奶，燕麦", "time": "5分钟", "difficulty": "⭐", "steps_list": ["燕麦煮软。", "加牛奶煮微沸。"], "nutrition": "钙", "tags": ["通便"], "desc": "奶香"},
        {"name": "🥬 青菜瘦肉粥", "ingredients": ["青菜", "猪肉", "大米"], "full_ingredients": "大米，肉末，青菜", "time": "30分钟", "difficulty": "⭐", "steps_list": ["煮白粥。", "肉末滑散放入。", "出锅放青菜。"], "nutrition": "补铁", "tags": ["荤素"], "desc": "全面"},
        {"name": "🐟 鳕鱼鲜蔬粥", "ingredients": ["鳕鱼", "大米", "西兰花"], "full_ingredients": "鳕鱼，大米，西兰花", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["鳕鱼蒸熟捣碎。", "放入粥里煮。", "加菜碎。"], "nutrition": "DHA", "tags": ["补脑"], "desc": "鲜美"},
        {"name": "🥞 香蕉松饼", "ingredients": ["香蕉", "鸡蛋", "面粉"], "full_ingredients": "香蕉，鸡蛋，面粉", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["香蕉压泥加蛋。", "加面粉调糊。", "无油煎熟。"], "nutrition": "钾", "tags": ["无糖"], "desc": "天然甜"},
        {"name": "🍞 芝士厚蛋烧", "ingredients": ["鸡蛋", "奶酪"], "full_ingredients": "鸡蛋，奶酪片", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["蛋液加奶。", "卷入奶酪煎熟。"], "nutrition": "钙", "tags": ["补钙"], "desc": "拉丝"},
        {"name": "🥪 鸡蛋三明治", "ingredients": ["面包", "鸡蛋"], "full_ingredients": "吐司，鸡蛋", "time": "5分钟", "difficulty": "⭐", "steps_list": ["煮蛋压碎拌酱。", "夹入吐司切边。"], "nutrition": "便携", "tags": ["野餐"], "desc": "方便"},
        {"name": "🍠 紫薯芝士球", "ingredients": ["红薯", "奶酪"], "full_ingredients": "紫薯/红薯，芝士", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["薯泥包芝士。", "搓圆烤熟。"], "nutrition": "花青素", "tags": ["零食"], "desc": "软糯"},
        {"name": "🌽 玉米面窝窝", "ingredients": ["玉米", "面粉"], "full_ingredients": "玉米面，面粉", "time": "20分钟", "difficulty": "⭐⭐", "steps_list": ["揉团捏窝。", "蒸15分钟。"], "nutrition": "粗粮", "tags": ["纤维"], "desc": "金黄"},
        {"name": "🥚 蒸水蛋", "ingredients": ["鸡蛋"], "full_ingredients": "鸡蛋，温水", "time": "10分钟", "difficulty": "⭐", "steps_list": ["1.5倍温水搅匀。", "过筛去泡。", "蒸10分钟。"], "nutrition": "易吸收", "tags": ["嫩滑"], "desc": "镜面"},
        {"name": "🍜 鸡汤细面", "ingredients": ["鸡肉", "面条", "青菜"], "full_ingredients": "鸡汤，细面，青菜", "time": "15分钟", "difficulty": "⭐", "steps_list": ["鸡汤煮面。", "加青菜烫熟。"], "nutrition": "滋补", "tags": ["汤面"], "desc": "鲜美"},
        {"name": "🥑 牛油果拌饭", "ingredients": ["牛油果", "鸡蛋", "大米"], "full_ingredients": "牛油果，蛋黄，米饭", "time": "5分钟", "difficulty": "⭐", "steps_list": ["牛油果压泥。", "拌入热饭和蛋黄。"], "nutrition": "好脂肪", "tags": ["大脑"], "desc": "森林黄油"},
        {"name": "🍝 番茄肉酱面", "ingredients": ["猪肉", "西红柿", "面条"], "full_ingredients": "番茄，肉末，面条", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["番茄炒沙加肉炖酱。", "面煮熟。", "浇汁。"], "nutrition": "开胃", "tags": ["酸甜"], "desc": "浓郁"},
        {"name": "🥣 杂粮二米糊", "ingredients": ["小米", "大米"], "full_ingredients": "小米，大米", "time": "20分钟", "difficulty": "⭐", "steps_list": ["破壁机打糊。"], "nutrition": "润肠", "tags": ["好吸收"], "desc": "液体营养"},
        {"name": "🥟 鲜虾小馄饨", "ingredients": ["虾仁", "猪肉", "馄饨皮"], "full_ingredients": "虾仁，肉泥，馄饨皮", "time": "20分钟", "difficulty": "⭐⭐⭐", "steps_list": ["混合做馅。", "包馄饨。", "煮熟。"], "nutrition": "钙", "tags": ["一口一个"], "desc": "皮薄"},
        {"name": "🎃 南瓜发糕", "ingredients": ["南瓜", "面粉"], "full_ingredients": "南瓜泥，面粉，酵母", "time": "40分钟", "difficulty": "⭐⭐⭐", "steps_list": ["发酵至两倍大。", "蒸20分钟。"], "nutrition": "易消化", "tags": ["蓬松"], "desc": "松软"},
        {"name": "🐟 鳕鱼肠蛋卷", "ingredients": ["鸡蛋", "鳕鱼"], "full_ingredients": "鸡蛋，鳕鱼肠", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["摊蛋皮。", "卷入鱼肠。", "切段。"], "nutrition": "蛋白", "tags": ["造型"], "desc": "可爱"},
        {"name": "🥛 奶香馒头片", "ingredients": ["面包", "鸡蛋"], "full_ingredients": "馒头/面包，蛋液", "time": "8分钟", "difficulty": "⭐", "steps_list": ["裹蛋液。", "煎两面黄。"], "nutrition": "能量", "tags": ["改造"], "desc": "剩饭变身"},
    ],

    # ==================================================
    # ☀️ 午餐 (Lunch)
    # ==================================================
    "lunch_meat": [
        {"name": "🍅 番茄土豆炖牛腩", "ingredients": ["牛肉", "土豆", "西红柿"], "full_ingredients": "牛腩，番茄，土豆", "time": "60分钟", "difficulty": "⭐⭐⭐", "steps_list": ["牛肉焯水。", "番茄炒沙炖肉。", "加土豆炖软。"], "nutrition": "补铁", "tags": ["维C"], "desc": "拌饭神器"},
        {"name": "🥩 彩椒牛肉粒", "ingredients": ["牛肉", "彩椒"], "full_ingredients": "牛里脊，彩椒", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["牛肉腌制滑油。", "彩椒快炒。", "混合。"], "nutrition": "维生素", "tags": ["嫩"], "desc": "色彩丰富"},
        {"name": "🥔 土豆肥牛卷", "ingredients": ["牛肉", "土豆"], "full_ingredients": "肥牛，土豆", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["土豆煎焦黄。", "下肥牛调味炒熟。"], "nutrition": "能量", "tags": ["好做"], "desc": "吉野家风味"},
        {"name": "🥩 芦笋炒牛肉", "ingredients": ["牛肉", "芦笋"], "full_ingredients": "牛里脊，芦笋", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["芦笋焯水。", "牛肉快炒。"], "nutrition": "叶酸", "tags": ["清爽"], "desc": "清新"},
        {"name": "🥩 滑蛋牛肉", "ingredients": ["牛肉", "鸡蛋"], "full_ingredients": "牛里脊，鸡蛋", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["牛肉浆好。", "蛋液混合滑炒。"], "nutrition": "双蛋白", "tags": ["软嫩"], "desc": "港式"},
        
        {"name": "🍖 糖醋里脊(番茄)", "ingredients": ["猪肉", "西红柿"], "full_ingredients": "里脊，番茄酱", "time": "30分钟", "difficulty": "⭐⭐⭐", "steps_list": ["肉条炸熟。", "裹番茄浓汁。"], "nutrition": "开胃", "tags": ["酸甜"], "desc": "宝宝最爱"},
        {"name": "🥘 肉末蒸豆腐", "ingredients": ["猪肉", "豆腐"], "full_ingredients": "肉末，内脂豆腐", "time": "15分钟", "difficulty": "⭐", "steps_list": ["肉末炒香。", "铺豆腐上蒸10分。"], "nutrition": "钙", "tags": ["易消化"], "desc": "入口即化"},
        {"name": "🥕 胡萝卜肉丸", "ingredients": ["猪肉", "胡萝卜"], "full_ingredients": "肉泥，胡萝卜", "time": "25分钟", "difficulty": "⭐⭐⭐", "steps_list": ["搅打上劲。", "水煮成丸。"], "nutrition": "低脂", "tags": ["软糯"], "desc": "可汤可菜"},
        {"name": "🥩 肉末茄子", "ingredients": ["猪肉", "茄子"], "full_ingredients": "肉末，茄子", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["茄子炒软。", "加肉末焖煮。"], "nutrition": "软烂", "tags": ["下饭"], "desc": "不爱吃菜也吃"},
        {"name": "🥒 黄瓜炒肉片", "ingredients": ["猪肉", "黄瓜"], "full_ingredients": "里脊，黄瓜", "time": "10分钟", "difficulty": "⭐", "steps_list": ["肉片滑熟。", "下黄瓜快炒。"], "nutrition": "清爽", "tags": ["家常"], "desc": "简单"},

        {"name": "🍗 香菇蒸滑鸡", "ingredients": ["鸡肉", "香菇"], "full_ingredients": "鸡腿肉，香菇", "time": "25分钟", "difficulty": "⭐⭐", "steps_list": ["鸡肉腌制。", "混香菇蒸20分。"], "nutrition": "不上火", "tags": ["嫩滑"], "desc": "原汁原味"},
        {"name": "🌽 玉米鸡丁", "ingredients": ["鸡肉", "玉米", "胡萝卜"], "full_ingredients": "鸡胸，玉米，胡萝卜", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["鸡丁滑炒。", "加蔬菜丁炒熟。"], "nutrition": "纤维", "tags": ["色彩"], "desc": "五彩斑斓"},
        {"name": "🍗 照烧鸡腿", "ingredients": ["鸡肉", "西兰花"], "full_ingredients": "鸡腿，西兰花", "time": "20分钟", "difficulty": "⭐⭐", "steps_list": ["煎两面黄。", "加汁焖煮。"], "nutrition": "蛋白", "tags": ["满足"], "desc": "大口吃肉"},
        {"name": "🐔 宫保鸡丁(免辣)", "ingredients": ["鸡肉", "花生", "黄瓜"], "full_ingredients": "鸡肉，黄瓜，花生", "time": "15分钟", "difficulty": "⭐⭐⭐", "steps_list": ["糖醋汁调味。", "快炒。"], "nutrition": "开胃", "tags": ["下饭"], "desc": "酸甜口"},
        {"name": "🥔 土豆炖鸡块", "ingredients": ["鸡肉", "土豆"], "full_ingredients": "鸡块，土豆", "time": "30分钟", "difficulty": "⭐⭐", "steps_list": ["炒香。", "炖20分钟。"], "nutrition": "能量", "tags": ["家常"], "desc": "软烂"},

        {"name": "🐟 清蒸鳕鱼", "ingredients": ["鳕鱼", "姜"], "full_ingredients": "鳕鱼，姜", "time": "15分钟", "difficulty": "⭐", "steps_list": ["腌制。", "蒸8分钟。"], "nutrition": "DHA", "tags": ["补脑"], "desc": "深海营养"},
        {"name": "🐟 彩椒三文鱼", "ingredients": ["三文鱼", "彩椒"], "full_ingredients": "三文鱼，彩椒", "time": "12分钟", "difficulty": "⭐⭐", "steps_list": ["煎熟鱼丁。", "炒彩椒。"], "nutrition": "Omega3", "tags": ["明目"], "desc": "色彩丰富"},
        {"name": "🦐 虾仁滑蛋", "ingredients": ["虾仁", "鸡蛋"], "full_ingredients": "虾仁，鸡蛋", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["虾仁焯水。", "滑蛋。"], "nutrition": "嫩滑", "tags": ["高蛋白"], "desc": "经典"},
        {"name": "🐟 茄汁巴沙鱼", "ingredients": ["鱼", "西红柿"], "full_ingredients": "巴沙鱼，番茄", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["炒番茄酱。", "煮鱼片。"], "nutrition": "无刺", "tags": ["开胃"], "desc": "酸甜"},
        {"name": "🦐 宫保虾球", "ingredients": ["虾仁", "黄瓜"], "full_ingredients": "虾仁，黄瓜，花生", "time": "15分钟", "difficulty": "⭐⭐⭐", "steps_list": ["糖醋汁。", "快炒。"], "nutrition": "开胃", "tags": ["下饭"], "desc": "酸甜"},
    ],
    
    "lunch_veg": [
        {"name": "🥦 蒜蓉西兰花", "ingredients": ["西兰花"], "full_ingredients": "西兰花，蒜", "time": "8分钟", "difficulty": "⭐", "steps_list": ["焯水。", "爆炒。"], "nutrition": "维C", "tags": ["纤维"], "desc": "必备"},
        {"name": "🥕 清炒胡萝卜", "ingredients": ["胡萝卜"], "full_ingredients": "胡萝卜", "time": "10分钟", "difficulty": "⭐", "steps_list": ["多油煸炒。", "焖软。"], "nutrition": "维A", "tags": ["护眼"], "desc": "甜甜的"},
        {"name": "🥬 蚝油生菜", "ingredients": ["生菜"], "full_ingredients": "生菜，蚝油", "time": "5分钟", "difficulty": "⭐", "steps_list": ["焯水。", "淋汁。"], "nutrition": "纤维", "tags": ["快手"], "desc": "水灵"},
        {"name": "🍄 什锦菌菇", "ingredients": ["香菇", "口蘑"], "full_ingredients": "杂菇", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["焯水。", "炒出汁。"], "nutrition": "免疫力", "tags": ["鲜"], "desc": "鲜美"},
        {"name": "🥔 地三鲜(少油)", "ingredients": ["土豆", "茄子", "彩椒"], "full_ingredients": "土豆，茄子，彩椒", "time": "20分钟", "difficulty": "⭐⭐⭐", "steps_list": ["煎熟。", "炒匀。"], "nutrition": "丰富", "tags": ["下饭"], "desc": "东北菜"},
        {"name": "🥬 菠菜炒蛋", "ingredients": ["菠菜", "鸡蛋"], "full_ingredients": "菠菜，鸡蛋", "time": "10分钟", "difficulty": "⭐", "steps_list": ["焯水。", "混炒。"], "nutrition": "叶酸", "tags": ["补铁"], "desc": "经典"},
        {"name": "🍅 糖拌西红柿", "ingredients": ["西红柿"], "full_ingredients": "番茄，糖", "time": "3分钟", "difficulty": "⭐", "steps_list": ["切片。", "撒糖。"], "nutrition": "茄红素", "tags": ["酸甜"], "desc": "凉菜"},
        {"name": "🥔 酸辣土豆丝", "ingredients": ["土豆"], "full_ingredients": "土豆，醋", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["泡水去淀粉。", "爆炒。"], "nutrition": "开胃", "tags": ["脆"], "desc": "国民菜"},
        {"name": "🎃 蒸贝贝南瓜", "ingredients": ["南瓜"], "full_ingredients": "南瓜", "time": "20分钟", "difficulty": "⭐", "steps_list": ["整只蒸。"], "nutrition": "代餐", "tags": ["甜"], "desc": "粉糯"},
        {"name": "🍆 蒜泥茄子", "ingredients": ["茄子"], "full_ingredients": "茄子，蒜泥", "time": "15分钟", "difficulty": "⭐", "steps_list": ["蒸软。", "撕条拌匀。"], "nutrition": "少油", "tags": ["软"], "desc": "健康"},
        {"name": "🍅 菜花炒西红柿", "ingredients": ["西红柿", "西兰花"], "full_ingredients": "花菜，番茄", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["花菜焯水。", "茄汁炒。"], "nutrition": "抗氧化", "tags": ["酸甜"], "desc": "开胃"},
        {"name": "🥬 手撕包菜", "ingredients": ["青菜"], "full_ingredients": "圆白菜，醋", "time": "8分钟", "difficulty": "⭐", "steps_list": ["手撕。", "爆炒。"], "nutrition": "维C", "tags": ["脆"], "desc": "下饭"},
        {"name": "🥒 拍黄瓜", "ingredients": ["黄瓜"], "full_ingredients": "黄瓜，蒜", "time": "5分钟", "difficulty": "⭐", "steps_list": ["拍碎。", "拌匀。"], "nutrition": "清爽", "tags": ["解腻"], "desc": "凉菜"},
        {"name": "🌽 松仁玉米", "ingredients": ["玉米"], "full_ingredients": "玉米粒", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["炒熟勾芡。"], "nutrition": "粗粮", "tags": ["甜"], "desc": "勺子挖"},
        {"name": "🍄 香菇油菜", "ingredients": ["香菇", "青菜"], "full_ingredients": "香菇，油菜", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["摆盘炒熟。"], "nutrition": "维C", "tags": ["搭配"], "desc": "好看"},
    ],

    # ==================================================
    # 🌙 晚餐 (Dinner) - 清淡/易消化
    # ==================================================
    "dinner_meat": [
        {"name": "🐟 鲈鱼豆腐汤", "ingredients": ["鱼", "豆腐"], "full_ingredients": "鲈鱼，豆腐", "time": "30分钟", "difficulty": "⭐⭐", "steps_list": ["煎鱼。", "炖白汤。", "下豆腐。"], "nutrition": "高钙", "tags": ["汤"], "desc": "好消化"},
        {"name": "🐔 椰子鸡", "ingredients": ["鸡肉"], "full_ingredients": "鸡块，椰子水", "time": "30分钟", "difficulty": "⭐⭐", "steps_list": ["椰子水煮鸡。", "不加调料。"], "nutrition": "清甜", "tags": ["不油"], "desc": "海南菜"},
        {"name": "🥚 蛤蜊蒸蛋", "ingredients": ["鸡蛋", "海鲜"], "full_ingredients": "蛤蜊，鸡蛋", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["煮开口。", "加蛋液蒸。"], "nutrition": "锌", "tags": ["鲜"], "desc": "鲜美"},
        {"name": "🦐 蒸酿秋葵", "ingredients": ["虾仁", "秋葵"], "full_ingredients": "秋葵，虾滑", "time": "15分钟", "difficulty": "⭐⭐⭐", "steps_list": ["填虾滑。", "蒸熟。"], "nutrition": "粘液蛋白", "tags": ["造型"], "desc": "星星"},
        {"name": "🍲 珍珠糯米丸", "ingredients": ["猪肉", "大米"], "full_ingredients": "肉丸，糯米", "time": "30分钟", "difficulty": "⭐⭐⭐", "steps_list": ["裹糯米。", "蒸熟。"], "nutrition": "能量", "tags": ["软糯"], "desc": "晶莹"},
        {"name": "🥬 白菜酿肉", "ingredients": ["猪肉", "青菜"], "full_ingredients": "白菜，肉馅", "time": "20分钟", "difficulty": "⭐⭐⭐", "steps_list": ["白菜卷肉。", "蒸熟。"], "nutrition": "纤维", "tags": ["低脂"], "desc": "翡翠白玉"},
        {"name": "🥚 猪肉炖蛋", "ingredients": ["猪肉", "鸡蛋"], "full_ingredients": "肉饼，鸡蛋", "time": "20分钟", "difficulty": "⭐⭐", "steps_list": ["肉饼铺底。", "打蛋蒸。"], "nutrition": "滋补", "tags": ["传统"], "desc": "客家菜"},
        {"name": "🍄 香菇酿肉", "ingredients": ["猪肉", "香菇"], "full_ingredients": "香菇，肉馅", "time": "20分钟", "difficulty": "⭐⭐⭐", "steps_list": ["填肉。", "蒸熟。"], "nutrition": "多糖", "tags": ["精致"], "desc": "小碗菜"},
        {"name": "🐟 鱼泥豆腐羹", "ingredients": ["鱼", "豆腐"], "full_ingredients": "鱼泥，豆腐", "time": "15分钟", "difficulty": "⭐", "steps_list": ["煮成羹。"], "nutrition": "易吸收", "tags": ["流食"], "desc": "吞咽"},
        {"name": "🥣 冬瓜汆丸子", "ingredients": ["猪肉", "冬瓜"], "full_ingredients": "冬瓜，肉丸", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["煮冬瓜。", "下丸子。"], "nutrition": "低脂", "tags": ["汤菜"], "desc": "清爽"},
        {"name": "🦐 虾仁豆腐", "ingredients": ["虾仁", "豆腐"], "full_ingredients": "虾仁，豆腐", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["炒虾仁。", "焖豆腐。"], "nutrition": "高钙", "tags": ["滑嫩"], "desc": "拌饭"},
        {"name": "🍗 蒸鸡翅", "ingredients": ["鸡肉", "土豆"], "full_ingredients": "鸡翅，土豆", "time": "30分钟", "difficulty": "⭐⭐", "steps_list": ["腌制。", "蒸熟。"], "nutrition": "不上火", "tags": ["脱骨"], "desc": "软烂"},
        {"name": "🦐 丝瓜炒虾仁", "ingredients": ["虾仁"], "full_ingredients": "丝瓜，虾仁", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["快炒。"], "nutrition": "补水", "tags": ["清爽"], "desc": "清甜"},
        {"name": "🥕 胡萝卜肉丸", "ingredients": ["猪肉", "胡萝卜"], "full_ingredients": "肉泥，胡萝卜", "time": "25分钟", "difficulty": "⭐⭐⭐", "steps_list": ["煮丸子。"], "nutrition": "低脂", "tags": ["软糯"], "desc": "连汤吃"},
        {"name": "🥬 莲藕蒸肉饼", "ingredients": ["猪肉", "莲藕"], "full_ingredients": "肉泥，莲藕", "time": "20分钟", "difficulty": "⭐⭐", "steps_list": ["混合蒸。"], "nutrition": "润肺", "tags": ["脆爽"], "desc": "口感好"},
    ],

    "dinner_veg": [
        {"name": "🥬 上汤娃娃菜", "ingredients": ["娃娃菜"], "full_ingredients": "娃娃菜，虾皮", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["高汤煮软。", "连汤吃。"], "nutrition": "汤鲜", "tags": ["软烂"], "desc": "暖胃"},
        {"name": "🌽 玉米烧冬瓜", "ingredients": ["冬瓜", "玉米"], "full_ingredients": "冬瓜，玉米", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["红烧汁焖。"], "nutrition": "利尿", "tags": ["甜"], "desc": "素菜荤做"},
        {"name": "🥬 粉丝娃娃菜", "ingredients": ["娃娃菜"], "full_ingredients": "娃娃菜，粉丝，蒜", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["蒜蓉蒸。"], "nutrition": "入味", "tags": ["下饭"], "desc": "吸汁"},
        {"name": "🥒 腐竹拌黄瓜", "ingredients": ["黄瓜", "豆腐"], "full_ingredients": "腐竹，黄瓜", "time": "10分钟", "difficulty": "⭐", "steps_list": ["凉拌。"], "nutrition": "钙", "tags": ["豆制品"], "desc": "清爽"},
        {"name": "🎃 南瓜蒸百合", "ingredients": ["南瓜"], "full_ingredients": "南瓜，百合", "time": "20分钟", "difficulty": "⭐", "steps_list": ["蒸熟。"], "nutrition": "润肺", "tags": ["甜"], "desc": "养生"},
        {"name": "🥒 响油黄瓜", "ingredients": ["黄瓜"], "full_ingredients": "黄瓜，蒜", "time": "5分钟", "difficulty": "⭐", "steps_list": ["卷起。", "淋热油。"], "nutrition": "补水", "tags": ["造型"], "desc": "精致"},
        {"name": "🌽 奶香玉米", "ingredients": ["玉米", "牛奶"], "full_ingredients": "玉米，牛奶", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["牛奶煮。"], "nutrition": "粗粮", "tags": ["香"], "desc": "奶香"},
        {"name": "🥦 凉拌木耳", "ingredients": ["木耳"], "full_ingredients": "木耳，洋葱", "time": "10分钟", "difficulty": "⭐", "steps_list": ["焯水过凉。", "拌匀。"], "nutrition": "排毒", "tags": ["脆"], "desc": "爽口"},
        {"name": "🥕 蒸胡萝卜丝", "ingredients": ["胡萝卜"], "full_ingredients": "胡萝卜，面粉", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["裹粉蒸。", "蘸汁。"], "nutrition": "维A", "tags": ["主食"], "desc": "老味道"},
        {"name": "🍄 蚝油杏鲍菇", "ingredients": ["香菇"], "full_ingredients": "杏鲍菇，蚝油", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["干煸。", "调味。"], "nutrition": "口感", "tags": ["鲜"], "desc": "像肉"},
    ],

    # ==================================================
    # 🥣 汤羹 (Soup)
    # ==================================================
    "soup": [
        {"name": "🥣 芙蓉鲜蔬汤", "ingredients": ["菠菜", "鸡蛋"], "full_ingredients": "菠菜，蛋清", "time": "5分钟", "difficulty": "⭐", "steps_list": ["淋蛋液。", "撒菜碎。"], "nutrition": "清淡", "tags": ["补水"], "desc": "翡翠白玉"},
        {"name": "🥣 紫菜蛋花汤", "ingredients": ["鸡蛋"], "full_ingredients": "紫菜，鸡蛋", "time": "5分钟", "difficulty": "⭐", "steps_list": ["水开淋蛋。"], "nutrition": "碘", "tags": ["快手"], "desc": "经典"},
        {"name": "🥣 番茄菌菇汤", "ingredients": ["西红柿", "香菇"], "full_ingredients": "番茄，杂菇", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["炒出汁。", "煮菌菇。"], "nutrition": "开胃", "tags": ["酸甜"], "desc": "开胃"},
        {"name": "🥣 丝瓜蛋汤", "ingredients": ["鸡蛋"], "full_ingredients": "丝瓜，鸡蛋", "time": "8分钟", "difficulty": "⭐", "steps_list": ["炒丝瓜。", "煮蛋。"], "nutrition": "补水", "tags": ["夏天"], "desc": "清热"},
        {"name": "🥣 豆腐蛤蜊汤", "ingredients": ["豆腐", "海鲜"], "full_ingredients": "蛤蜊，豆腐", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["煮开口。", "炖豆腐。"], "nutrition": "锌", "tags": ["鲜"], "desc": "海味"},
        {"name": "🥣 猪肝菠菜汤", "ingredients": ["猪肉", "菠菜"], "full_ingredients": "猪肝，菠菜", "time": "10分钟", "difficulty": "⭐⭐", "steps_list": ["煮猪肝。", "烫菠菜。"], "nutrition": "补铁", "tags": ["明目"], "desc": "补血"},
        {"name": "🥣 罗宋汤(儿版)", "ingredients": ["牛肉", "西红柿", "土豆"], "full_ingredients": "牛肉，番茄，土豆", "time": "50分钟", "difficulty": "⭐⭐⭐", "steps_list": ["炒香炖煮。"], "nutrition": "全面", "tags": ["浓郁"], "desc": "西式"},
        {"name": "🥣 玉米排骨汤", "ingredients": ["猪肉", "玉米"], "full_ingredients": "排骨，玉米", "time": "60分钟", "difficulty": "⭐⭐", "steps_list": ["炖1小时。"], "nutrition": "滋补", "tags": ["清甜"], "desc": "啃骨头"},
        {"name": "🥣 山药排骨汤", "ingredients": ["猪肉", "山药"], "full_ingredients": "排骨，山药", "time": "60分钟", "difficulty": "⭐⭐", "steps_list": ["炖烂。"], "nutrition": "健脾", "tags": ["养生"], "desc": "汤浓"},
        {"name": "🥣 莲藕排骨汤", "ingredients": ["猪肉", "莲藕"], "full_ingredients": "排骨，莲藕", "time": "60分钟", "difficulty": "⭐⭐", "steps_list": ["炖粉糯。"], "nutrition": "润肺", "tags": ["秋天"], "desc": "拉丝"},
        {"name": "🥣 白萝卜羊肉汤", "ingredients": ["羊肉"], "full_ingredients": "羊肉，白萝卜", "time": "60分钟", "difficulty": "⭐⭐⭐", "steps_list": ["去膻炖烂。"], "nutrition": "暖身", "tags": ["冬天"], "desc": "温补"},
        {"name": "🥣 鲫鱼豆腐汤", "ingredients": ["鱼", "豆腐"], "full_ingredients": "鲫鱼，豆腐", "time": "40分钟", "difficulty": "⭐⭐⭐", "steps_list": ["煎鱼炖白。"], "nutrition": "高钙", "tags": ["补钙"], "desc": "奶白"},
        {"name": "🥣 鱼头豆腐汤", "ingredients": ["鱼", "豆腐"], "full_ingredients": "鱼头，豆腐", "time": "40分钟", "difficulty": "⭐⭐⭐", "steps_list": ["煎鱼炖白。"], "nutrition": "DHA", "tags": ["聪明"], "desc": "黄金搭档"},
        {"name": "🥣 虫草花鸡汤", "ingredients": ["鸡肉"], "full_ingredients": "鸡肉，虫草花", "time": "50分钟", "difficulty": "⭐⭐", "steps_list": ["炖煮。"], "nutrition": "免疫力", "tags": ["金黄"], "desc": "好喝"},
        {"name": "🥣 南瓜浓汤", "ingredients": ["南瓜", "牛奶"], "full_ingredients": "南瓜，牛奶", "time": "20分钟", "difficulty": "⭐⭐", "steps_list": ["打泥煮开。"], "nutrition": "纤维", "tags": ["西餐"], "desc": "香甜"},
        {"name": "🥣 银耳雪梨汤", "ingredients": ["水果"], "full_ingredients": "银耳，雪梨", "time": "40分钟", "difficulty": "⭐⭐", "steps_list": ["炖出胶。"], "nutrition": "润肺", "tags": ["甜汤"], "desc": "止咳"},
        {"name": "🥣 绿豆汤", "ingredients": ["水果"], "full_ingredients": "绿豆", "time": "40分钟", "difficulty": "⭐", "steps_list": ["煮开花。"], "nutrition": "消暑", "tags": ["夏天"], "desc": "解渴"},
        {"name": "🥣 味噌汤", "ingredients": ["豆腐"], "full_ingredients": "味噌，豆腐", "time": "10分钟", "difficulty": "⭐", "steps_list": ["化开味噌。"], "nutrition": "豆类", "tags": ["日式"], "desc": "异域"},
        {"name": "🥣 酸辣汤(微辣)", "ingredients": ["豆腐", "鸡蛋", "木耳"], "full_ingredients": "豆腐，木耳，蛋", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["勾芡加醋。"], "nutrition": "开胃", "tags": ["暖身"], "desc": "发汗"},
        {"name": "🥣 冬瓜肉丸汤", "ingredients": ["猪肉", "冬瓜"], "full_ingredients": "冬瓜，肉丸", "time": "15分钟", "difficulty": "⭐⭐", "steps_list": ["煮熟。"], "nutrition": "解腻", "tags": ["清爽"], "desc": "不油"},
    ],

    # ==================================================
    # 🍎 水果 (Fruit)
    # ==================================================
    "fruit": [
        "🍎 苹果片", "🍌 香蕉段", "🫐 蓝莓", "🥝 猕猴桃片", "🍊 橙子切块", 
        "🍇 去皮葡萄", "🐉 火龙果", "🍓 草莓", "🍈 哈密瓜", "🍒 车厘子", 
        "🍐 炖雪梨", "🥭 芒果丁", "🍑 桃子", "🍉 西瓜", "🍍 菠萝", 
        "🍅 圣女果", "🍊 砂糖橘", "🥑 牛油果泥", "🥥 椰子肉", "🍐 香梨"
    ]
}
FRIDGE_CATEGORIES = {
    "🥩 肉禽蛋海鲜": ["鸡蛋", "牛肉", "猪肉", "鸡肉", "鳕鱼", "虾仁", "三文鱼", "鱼", "火腿", "排骨", "鸭肉", "蛤蜊", "猪肝", "干贝", "羊肉"],
    "🥦 蔬菜菌菇": ["西红柿", "胡萝卜", "西兰花", "土豆", "南瓜", "青菜", "菠菜", "冬瓜", "香菇", "玉米", "彩椒", "娃娃菜", "红薯", "秋葵", "西葫芦", "口蘑", "山药", "茄子", "莲藕", "黄瓜", "芦笋", "白菜", "洋葱", "荷兰豆", "木耳", "空心菜", "海带", "鲜百合", "白萝卜"],
    "🍚 主食/干货/奶": ["大米", "小米", "面粉", "面条", "豆腐", "燕麦", "牛奶", "奶酪", "面包", "馄饨皮", "紫菜", "粉丝", "腐竹", "年糕", "意面", "黑芝麻粉"]
}
streamlit>=1.28.0
requests>=2.31.0
Pillow>=10.0.0
