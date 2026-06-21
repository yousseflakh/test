import streamlit as st
import random
import os
import json
import urllib.request

# محاولة استيراد مكتبات اللغة العربية
try:
    import arabic_reshaper
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False

try:
    from bidi.algorithm import get_display
    BIDI_SUPPORT = True
except ImportError:
    BIDI_SUPPORT = False

def fix_arabic_text(text):
    if not ARABIC_SUPPORT or not BIDI_SUPPORT:
        return text
    try:
        if any("\u0600" <= char <= "\u06FF" for char in text):
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
    except Exception:
        pass
    return text

# إعدادات الملفات
FILE = "words.txt"
SCORE_FILE = "highscore.txt"

DEFAULT_WORDS = [
    {"q": "House", "a": "Maison"},
    {"q": "Book", "a": "Livre"},
    {"q": "Car", "a": "Voiture"},
    {"q": "Cat", "a": "Chat"},
    {"q": "Dog", "a": "Chien"},
    {"q": "Sun", "a": "Soleil"},
    {"q": "Moon", "a": "Lune"},
    {"q": "Star", "a": "Étoile"},
    {"q": "Apple", "a": "Pomme"},
    {"q": "Water", "a": "Eau"}
]

LANGUAGES = {
    "English": "en",
    "French": "fr",
    "Arabic": "ar",
    "Spanish": "es",
    "German": "de"
}

def load_words():
    if not os.path.exists(FILE):
        return DEFAULT_WORDS
    words = []
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "," in line:
                    q, a = line.strip().split(",", 1)
                    if q.strip() and a.strip():
                        words.append({"q": q.strip(), "a": a.strip()})
    except:
        return DEFAULT_WORDS
    if len(words) < 5:
        return DEFAULT_WORDS
    return words

def save_words(words):
    try:
        with open(FILE, "w", encoding="utf-8") as f:
            for w in words:
                f.write(f"{w['q']},{w['a']}\n")
    except:
        pass

def get_high_score():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_high_score(score):
    current_high = get_high_score()
    if score > current_high:
        try:
            with open(SCORE_FILE, "w") as f:
                f.write(str(score))
        except:
            pass

# تهيئة حالة الجلسة - تم حذف المسافات الزائدة
if 'page' not in st.session_state:
    st.session_state.page = 'game'
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'lives' not in st.session_state:
    st.session_state.lives = 5
if 'words_db' not in st.session_state:
    st.session_state.words_db = load_words()
if 'game_over' not in st.session_state:
    st.session_state.game_over = False
if 'selected_word' not in st.session_state:
    st.session_state.selected_word = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'src_lang' not in st.session_state:
    st.session_state.src_lang = "English"
if 'target_lang' not in st.session_state:
    st.session_state.target_lang = "Arabic"
if 'word_to_edit' not in st.session_state:
    st.session_state.word_to_edit = None
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'pairs' not in st.session_state:
    st.session_state.pairs = []
if 'selected_pair' not in st.session_state:
    st.session_state.selected_pair = None
if 'matched_pairs' not in st.session_state:
    st.session_state.matched_pairs = []
if 'attempts' not in st.session_state:
    st.session_state.attempts = 0
if 'round_active' not in st.session_state:
    st.session_state.round_active = False
if 'message' not in st.session_state:
    st.session_state.message = ""
if 'message_type' not in st.session_state:
    st.session_state.message_type = ""

def reset_game():
    st.session_state.score = 0
    st.session_state.lives = 5
    st.session_state.game_over = False
    st.session_state.game_started = False
    st.session_state.pairs = []
    st.session_state.selected_pair = None
    st.session_state.matched_pairs = []
    st.session_state.attempts = 0
    st.session_state.round_active = False
    st.session_state.message = ""
    st.session_state.message_type = ""

def start_game():
    st.session_state.game_started = True
    st.session_state.round_active = True
    st.session_state.matched_pairs = []
    st.session_state.attempts = 0
    st.session_state.message = ""
    generate_pairs()

def generate_pairs():
    words = load_words()
    num_pairs = min(6, len(words))
    selected_words = random.sample(words, num_pairs)
    
    pairs = []
    for word in selected_words:
        pairs.append({
            'word': fix_arabic_text(word['q']),
            'translation': fix_arabic_text(word['a']),
            'word_id': word['q'],
            'matched': False
        })
    
    random.shuffle(pairs)
    st.session_state.pairs = pairs
    st.session_state.selected_pair = None

def check_match(pair_index):
    if st.session_state.game_over or not st.session_state.round_active:
        return
    
    if st.session_state.selected_pair is None:
        st.session_state.selected_pair = pair_index
        return
    
    if st.session_state.selected_pair == pair_index:
        st.session_state.selected_pair = None
        return
    
    first = st.session_state.pairs[st.session_state.selected_pair]
    second = st.session_state.pairs[pair_index]
    
    if first['matched'] or second['matched']:
        st.session_state.selected_pair = None
        return
    
    is_match = False
    if first['word_id'] == second['word_id']:
        is_match = True
    elif first['translation'] == second['translation'] and first['word'] != second['word']:
        is_match = True
    
    if is_match:
        st.session_state.pairs[st.session_state.selected_pair]['matched'] = True
        st.session_state.pairs[pair_index]['matched'] = True
        st.session_state.score += 10
        st.session_state.matched_pairs.append(st.session_state.selected_pair)
        st.session_state.matched_pairs.append(pair_index)
        st.session_state.message = "✅ تطابق!"
        st.session_state.message_type = "success"
    else:
        st.session_state.lives -= 1
        st.session_state.attempts += 1
        st.session_state.message = "❌ لا يتطابقان!"
        st.session_state.message_type = "error"
        
        if st.session_state.lives <= 0:
            save_high_score(st.session_state.score)
            st.session_state.game_over = True
    
    st.session_state.selected_pair = None
    st.session_state.round_active = True
    
    if len(st.session_state.matched_pairs) == len(st.session_state.pairs):
        st.session_state.message = "🎉 تهانينا! أتممت جميع الأزواج!"
        st.session_state.message_type = "success"
        st.session_state.round_active = False

def go_to_dict():
    st.session_state.page = 'dict'
    st.session_state.selected_word = None
    st.session_state.edit_mode = False

def go_to_game():
    st.session_state.page = 'game'
    if st.session_state.lives <= 0:
        reset_game()

def delete_word(index):
    words = load_words()
    if 0 <= index < len(words):
        words.pop(index)
        save_words(words)
        st.session_state.words_db = load_words()
        st.rerun()

def open_edit(index):
    st.session_state.page = 'edit'
    st.session_state.edit_mode = True
    words = load_words()
    if index != -1 and index < len(words):
        st.session_state.selected_word = words[index]
        st.session_state.word_to_edit = index
    else:
        st.session_state.selected_word = {"q": "", "a": ""}
        st.session_state.word_to_edit = -1

def translate_text(text, src, target):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={LANGUAGES[src]}&tl={LANGUAGES[target]}&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        return data[0][0][0]
    except Exception as e:
        return "⚠️ خطأ في الترجمة!"

def save_word(q, a):
    if not q.strip() or not a.strip():
        return False
    
    words = load_words()
    new_data = {"q": q.strip(), "a": a.strip()}
    
    if st.session_state.word_to_edit == -1:
        words.append(new_data)
    else:
        if st.session_state.word_to_edit < len(words):
            words[st.session_state.word_to_edit] = new_data
    
    save_words(words)
    st.session_state.words_db = load_words()
    st.session_state.page = 'dict'
    st.session_state.edit_mode = False
    return True

# CSS محسّن - تم حذف المسافات الزائدة تماماً
st.markdown("""
<style>
    /* إزالة جميع المسافات الزائدة */
    .main > div {
        padding: 0 !important;
        margin: 0 !important;
    }
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    .stApp {
        margin: 0 !important;
        padding: 0 !important;
    }
    .stApp > header {
        display: none !important;
    }
    
    /* تنسيق عام */
    .game-container {
        background: linear-gradient(135deg, #0a0a1a, #1a1a3e);
        border-radius: 0;
        padding: 15px;
        margin: 0;
        min-height: 100vh;
        border: none;
        box-shadow: none;
    }
    
    /* رأس اللعبة */
    .game-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 5px 15px 5px;
        border-bottom: 1px solid rgba(0, 255, 200, 0.1);
        margin-bottom: 15px;
    }
    .score-section {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .score-item {
        color: #00ffcc;
        font-size: 18px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(0, 255, 200, 0.3);
    }
    .lives-item {
        color: #ff3366;
        font-size: 20px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(255, 51, 102, 0.3);
    }
    
    /* بطاقات اللعبة */
    .game-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin: 10px 0;
    }
    .card {
        background: linear-gradient(135deg, rgba(30, 30, 80, 0.8), rgba(20, 20, 60, 0.9));
        border: 2px solid rgba(0, 255, 200, 0.15);
        border-radius: 12px;
        padding: 20px 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        min-height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 16px;
        font-weight: bold;
        position: relative;
        overflow: hidden;
    }
    .card:hover {
        transform: translateY(-3px);
        border-color: #00ffcc;
        box-shadow: 0 10px 30px rgba(0, 255, 200, 0.15);
    }
    .card:active {
        transform: scale(0.95);
    }
    .card.matched {
        background: linear-gradient(135deg, rgba(0, 255, 200, 0.1), rgba(0, 200, 150, 0.05));
        border-color: #00ffcc;
        opacity: 0.6;
        cursor: default;
        transform: none !important;
    }
    .card.matched::after {
        content: '✓';
        position: absolute;
        top: 5px;
        right: 10px;
        color: #00ffcc;
        font-size: 18px;
    }
    .card.selected {
        border-color: #ffcc00;
        box-shadow: 0 0 30px rgba(255, 204, 0, 0.2);
        transform: scale(1.05);
    }
    .card.selected::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #ffcc00, transparent, #ffcc00);
        border-radius: 14px;
        z-index: -1;
        animation: borderGlow 1.5s linear infinite;
    }
    @keyframes borderGlow {
        0% { opacity: 0.3; }
        50% { opacity: 0.8; }
        100% { opacity: 0.3; }
    }
    
    /* الرسائل */
    .message-box {
        text-align: center;
        padding: 12px;
        margin: 10px 0;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        animation: slideIn 0.5s ease;
    }
    @keyframes slideIn {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .success {
        color: #00ff88;
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid #00ff88;
    }
    .error {
        color: #ff4444;
        background: rgba(255, 68, 68, 0.1);
        border: 1px solid #ff4444;
    }
    
    /* أزرار */
    .stButton > button {
        background: linear-gradient(135deg, #00ffcc, #0088ff);
        color: #0a0a1a;
        border: none;
        border-radius: 12px;
        padding: 12px 20px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
        font-size: 16px;
        margin: 5px 0;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0, 255, 200, 0.2);
    }
    .stButton > button:active {
        transform: scale(0.95);
    }
    
    /* شاشة البداية */
    .start-screen {
        text-align: center;
        padding: 60px 20px;
    }
    .start-icon {
        font-size: 80px;
        margin-bottom: 20px;
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
    }
    .start-title {
        color: #00ffcc;
        font-size: 32px;
        font-weight: bold;
        text-shadow: 0 0 40px rgba(0, 255, 200, 0.3);
        margin-bottom: 10px;
    }
    .start-subtitle {
        color: rgba(255, 255, 255, 0.5);
        font-size: 16px;
        margin-bottom: 30px;
    }
    
    /* شاشة النهاية */
    .game-over-box {
        text-align: center;
        padding: 40px 20px;
        background: rgba(20, 20, 50, 0.8);
        border-radius: 15px;
        border: 2px solid rgba(255, 51, 51, 0.2);
        margin: 20px 0;
    }
    .game-over-title {
        color: #ff3366;
        font-size: 36px;
        font-weight: bold;
        text-shadow: 0 0 40px rgba(255, 51, 102, 0.3);
    }
    .final-score {
        color: #ffcc00;
        font-size: 24px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    /* القاموس */
    .dict-container {
        background: linear-gradient(135deg, #0a0a1a, #1a1a3e);
        padding: 15px;
        min-height: 100vh;
    }
    .dict-title {
        color: #00ffcc;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
        text-align: center;
    }
    .word-row {
        background: rgba(20, 20, 50, 0.7);
        border-radius: 10px;
        padding: 12px 15px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(0, 255, 200, 0.05);
        transition: all 0.3s ease;
    }
    .word-row:hover {
        border-color: rgba(0, 255, 200, 0.2);
        transform: translateX(5px);
    }
    .word-text {
        color: white;
        font-size: 15px;
        flex: 1;
        margin: 0 10px;
    }
    .word-actions {
        display: flex;
        gap: 8px;
    }
    .word-actions .stButton > button {
        padding: 5px 15px;
        font-size: 12px;
        margin: 0;
        width: auto;
    }
    
    /* تحسينات الإدخال */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(20, 20, 50, 0.8) !important;
        color: white !important;
        border: 1px solid rgba(0, 255, 200, 0.15) !important;
        border-radius: 10px !important;
        padding: 10px 15px !important;
        font-size: 15px !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #00ffcc !important;
        box-shadow: 0 0 20px rgba(0, 255, 200, 0.1) !important;
    }
    .stSelectbox > div > div {
        background: rgba(20, 20, 50, 0.8) !important;
        color: white !important;
        border: 1px solid rgba(0, 255, 200, 0.15) !important;
        border-radius: 10px !important;
    }
    
    /* إزالة المسافات الزائدة من العناصر */
    .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    .stMarkdown {
        margin: 0 !important;
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# تحذير المكتبات
if not ARABIC_SUPPORT or not BIDI_SUPPORT:
    st.warning("⚠️ دعم اللغة العربية غير مكتمل. للتثبيت: pip install arabic_reshaper python-bidi")

# الصفحات - محتوى مبسط بدون مسافات
if st.session_state.page == 'game':
    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    
    # الرأس المحسن
    st.markdown('<div class="game-header">', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="score-section">
        <span class="score-item">⭐ {st.session_state.score}</span>
        <span class="lives-item">{'❤️' * max(0, st.session_state.lives)}</span>
    </div>
    <div style="color:rgba(255,255,255,0.2);font-size:14px;">
        {len(st.session_state.matched_pairs) // 2}/{len(st.session_state.pairs) // 2 if st.session_state.pairs else 0}
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # شاشة البداية
    if not st.session_state.game_started and not st.session_state.game_over:
        st.markdown('<div class="start-screen">', unsafe_allow_html=True)
        st.markdown('<div class="start-icon">🧩</div>', unsafe_allow_html=True)
        st.markdown('<div class="start-title">مطابقة الكلمات</div>', unsafe_allow_html=True)
        st.markdown('<div class="start-subtitle">طابق الكلمة مع ترجمتها الصحيحة</div>', unsafe_allow_html=True)
        
        if st.button("🚀 ابدأ اللعبة", use_container_width=True):
            start_game()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # اللعبة
    elif not st.session_state.game_over and st.session_state.game_started:
        # الرسالة
        if st.session_state.message:
            msg_type = "success" if "✅" in st.session_state.message or "🎉" in st.session_state.message else "error"
            st.markdown(f'<div class="message-box {msg_type}">{st.session_state.message}</div>', unsafe_allow_html=True)
        
        # الشبكة
        if st.session_state.pairs:
            st.markdown('<div class="game-grid">', unsafe_allow_html=True)
            
            for i, pair in enumerate(st.session_state.pairs):
                is_matched = pair.get('matched', False)
                is_selected = st.session_state.selected_pair == i
                
                if is_matched:
                    st.markdown(f'<div class="card matched">✓</div>', unsafe_allow_html=True)
                else:
                    card_class = "card selected" if is_selected else "card"
                    display_text = pair['word']
                    
                    if st.button(
                        display_text,
                        key=f"card_{i}",
                        use_container_width=True
                    ):
                        if st.session_state.round_active and not st.session_state.game_over:
                            check_match(i)
                            st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # أزرار التحكم
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.round_active and len(st.session_state.matched_pairs) < len(st.session_state.pairs):
                    if st.button("🔄 إعادة ترتيب", use_container_width=True):
                        generate_pairs()
                        st.session_state.selected_pair = None
                        st.session_state.message = ""
                        st.rerun()
            with col2:
                if st.button("📚 القاموس", use_container_width=True):
                    go_to_dict()
                    st.rerun()
        
        # الفوز
        if len(st.session_state.matched_pairs) == len(st.session_state.pairs) and st.session_state.pairs:
            st.markdown('<div style="text-align:center;padding:20px 0;">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:50px;">🎉</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color:#00ffcc;font-size:20px;font-weight:bold;">أكملت جميع الأزواج!</div>', unsafe_allow_html=True)
            if st.button("🔄 لعبة جديدة", use_container_width=True):
                generate_pairs()
                st.session_state.matched_pairs = []
                st.session_state.selected_pair = None
                st.session_state.message = ""
                st.session_state.round_active = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # شاشة Game Over
    if st.session_state.game_over:
        st.markdown('<div class="game-over-box">', unsafe_allow_html=True)
        st.markdown('<div class="game-over-title">💔 انتهت اللعبة</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="final-score">⭐ النقاط: {st.session_state.score}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:rgba(255,255,255,0.5);">🎯 أعلى نتيجة: {get_high_score()}</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 إعادة المحاولة", use_container_width=True):
                reset_game()
                st.rerun()
        with col2:
            if st.button("📚 القاموس", use_container_width=True):
                go_to_dict()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# صفحة القاموس
elif st.session_state.page == 'dict':
    st.markdown('<div class="dict-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="dict-title">📚 القاموس</div>', unsafe_allow_html=True)
    
    # أزرار التحكم
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎮 العودة للعبة", use_container_width=True):
            go_to_game()
            st.rerun()
    with col2:
        if st.button("➕ إضافة كلمة", use_container_width=True):
            open_edit(-1)
            st.rerun()
    
    # عرض الكلمات
    words = load_words()
    if words:
        for i, word in enumerate(words):
            st.markdown(f'''
            <div class="word-row">
                <span style="color:#00ffcc;font-weight:bold;">{fix_arabic_text(word['q'])}</span>
                <span style="color:white;">→</span>
                <span style="color:#ffcc00;">{fix_arabic_text(word['a'])}</span>
            </div>
            ''', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"✏️ تعديل", key=f"edit_{i}", use_container_width=True):
                    open_edit(i)
                    st.rerun()
            with col2:
                if st.button(f"🗑️ حذف", key=f"delete_{i}", use_container_width=True):
                    delete_word(i)
                    st.rerun()
    else:
        st.markdown('<div style="text-align:center;color:rgba(255,255,255,0.3);padding:40px 0;">لا توجد كلمات في القاموس</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# صفحة التعديل
elif st.session_state.page == 'edit':
    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    
    title = "➕ إضافة كلمة جديدة" if st.session_state.word_to_edit == -1 else "✏️ تعديل كلمة"
    st.markdown(f'<h2 style="color:#00ffcc;text-align:center;margin-bottom:20px;">{title}</h2>', unsafe_allow_html=True)
    
    # حقول الإدخال
    word = st.session_state.selected_word
    q = st.text_input("📝 الكلمة الأصلية", value=word['q'] if word else "")
    a = st.text_input("📝 الترجمة", value=word['a'] if word else "")
    
    # خيارات الترجمة
    col1, col2 = st.columns(2)
    with col1:
        src_lang = st.selectbox("من", list(LANGUAGES.keys()), 
                               index=list(LANGUAGES.keys()).index(st.session_state.src_lang))
    with col2:
        target_lang = st.selectbox("إلى", list(LANGUAGES.keys()),
                                  index=list(LANGUAGES.keys()).index(st.session_state.target_lang))
    
    if st.button("🌐 ترجمة تلقائية", use_container_width=True):
        if q.strip():
            translation = translate_text(q, src_lang, target_lang)
            a = translation
            st.rerun()
    
    # أزرار التحكم
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 حفظ", use_container_width=True):
            if save_word(q, a):
                st.rerun()
    with col2:
        if st.button("❌ إلغاء", use_container_width=True):
            st.session_state.page = 'dict'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
