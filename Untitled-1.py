import streamlit as st
import random
import os
import json
import urllib.request
import time

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

# تهيئة حالة الجلسة
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

def start_game():
    st.session_state.game_started = True
    st.session_state.round_active = True
    st.session_state.matched_pairs = []
    st.session_state.attempts = 0
    generate_pairs()

def generate_pairs():
    """توليد أزواج الكلمات والترجمات"""
    words = load_words()
    # اختيار 4-6 كلمات عشوائية
    num_pairs = min(6, len(words))
    selected_words = random.sample(words, num_pairs)
    
    # إنشاء أزواج (كلمة، ترجمتها)
    pairs = []
    for word in selected_words:
        pairs.append({
            'word': fix_arabic_text(word['q']),
            'translation': fix_arabic_text(word['a']),
            'word_id': word['q'],
            'matched': False
        })
    
    # خلط الأزواج
    random.shuffle(pairs)
    st.session_state.pairs = pairs
    st.session_state.selected_pair = None

def check_match(pair_index):
    """التحقق من تطابق الكلمة مع ترجمتها"""
    if st.session_state.game_over or not st.session_state.round_active:
        return
    
    if st.session_state.selected_pair is None:
        st.session_state.selected_pair = pair_index
        return
    
    # إذا كان نفس العنصر
    if st.session_state.selected_pair == pair_index:
        st.session_state.selected_pair = None
        return
    
    # التحقق من التطابق
    first = st.session_state.pairs[st.session_state.selected_pair]
    second = st.session_state.pairs[pair_index]
    
    # إذا كان أحدهم مطابق بالفعل
    if first['matched'] or second['matched']:
        st.session_state.selected_pair = None
        return
    
    # التحقق مما إذا كانا زوجين (كلمة وترجمتها)
    is_match = False
    if first['word_id'] == second['word_id']:
        is_match = True
    elif first['translation'] == second['translation'] and first['word'] != second['word']:
        is_match = True
    
    if is_match:
        # تطابق ناجح
        st.session_state.pairs[st.session_state.selected_pair]['matched'] = True
        st.session_state.pairs[pair_index]['matched'] = True
        st.session_state.score += 10
        st.session_state.matched_pairs.append(st.session_state.selected_pair)
        st.session_state.matched_pairs.append(pair_index)
        st.session_state.message = "✅ تطابق!"
        st.session_state.message_type = "success"
    else:
        # خطأ
        st.session_state.lives -= 1
        st.session_state.attempts += 1
        st.session_state.message = "❌ لا يتطابقان!"
        st.session_state.message_type = "error"
        
        if st.session_state.lives <= 0:
            save_high_score(st.session_state.score)
            st.session_state.game_over = True
    
    st.session_state.selected_pair = None
    st.session_state.round_active = True
    
    # التحقق من الفوز
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

# CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%);
        padding: 10px;
        min-height: 100vh;
    }
    .game-container {
        background: rgba(10, 10, 30, 0.9);
        border-radius: 20px;
        padding: 15px;
        margin: 0 auto;
        max-width: 500px;
        min-height: 600px;
        border: 1px solid rgba(0, 255, 200, 0.2);
        box-shadow: 0 0 50px rgba(0, 255, 200, 0.1);
    }
    .header {
        display: flex;
        justify-content: space-between;
        padding: 5px 5px 10px 5px;
        flex-wrap: wrap;
        gap: 5px;
    }
    .score-text {
        color: #00ffcc;
        font-size: 18px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(0, 255, 200, 0.5);
    }
    .lives-text {
        color: #ff3366;
        font-size: 18px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(255, 51, 102, 0.5);
    }
    .game-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin: 10px 0;
    }
    .card {
        background: rgba(30, 30, 80, 0.7);
        border: 2px solid rgba(0, 255, 200, 0.2);
        border-radius: 12px;
        padding: 25px 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        min-height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        font-weight: bold;
    }
    .card:hover {
        transform: scale(1.03);
        border-color: #00ffcc;
        box-shadow: 0 0 30px rgba(0, 255, 200, 0.2);
    }
    .card.matched {
        background: rgba(0, 255, 200, 0.15);
        border-color: #00ffcc;
        opacity: 0.6;
        cursor: default;
    }
    .card.matched:hover {
        transform: none;
        box-shadow: none;
    }
    .card.selected {
        border-color: #ffcc00;
        box-shadow: 0 0 30px rgba(255, 204, 0, 0.3);
        transform: scale(1.05);
    }
    .card.word {
        border-color: rgba(100, 100, 255, 0.3);
    }
    .card.translation {
        border-color: rgba(255, 100, 100, 0.3);
    }
    .message-box {
        text-align: center;
        padding: 10px;
        margin: 8px 0;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        animation: slideIn 0.3s ease;
    }
    @keyframes slideIn {
        0% { opacity: 0; transform: translateY(-10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .success {
        color: #00ff00;
        background: rgba(0, 255, 0, 0.1);
        border: 1px solid #00ff00;
    }
    .error {
        color: #ff3333;
        background: rgba(255, 0, 0, 0.1);
        border: 1px solid #ff3333;
    }
    .game-over-box {
        background: rgba(20, 20, 50, 0.95);
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
        border: 2px solid rgba(255, 51, 51, 0.3);
        text-align: center;
        animation: fadeIn 0.5s ease;
    }
    .game-over-title {
        color: #ff3333;
        font-size: 30px;
        font-weight: bold;
        text-shadow: 0 0 30px rgba(255, 51, 51, 0.5);
    }
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin: 12px 0;
    }
    .stat-item {
        background: rgba(20, 20, 50, 0.5);
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid rgba(0, 255, 200, 0.1);
    }
    .stat-label {
        color: rgba(255, 255, 255, 0.5);
        font-size: 11px;
    }
    .stat-value {
        color: #00ffcc;
        font-size: 20px;
        font-weight: bold;
        margin-top: 2px;
    }
    .stat-value.gold {
        color: #ffcc00;
    }
    .dict-container {
        background: rgba(10, 10, 30, 0.9);
        border-radius: 20px;
        padding: 20px;
        margin: 0 auto;
        max-width: 500px;
        min-height: 600px;
        border: 1px solid rgba(0, 255, 200, 0.2);
    }
    .word-row {
        background: rgba(20, 20, 50, 0.7);
        border-radius: 10px;
        padding: 10px 15px;
        margin: 6px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(0, 255, 200, 0.1);
    }
    .word-text {
        color: white;
        font-size: 15px;
        flex: 1;
    }
    .edit-container {
        background: rgba(10, 10, 30, 0.9);
        border-radius: 20px;
        padding: 20px;
        margin: 0 auto;
        max-width: 500px;
        min-height: 600px;
        border: 1px solid rgba(0, 255, 200, 0.2);
    }
    .stButton > button {
        background: linear-gradient(135deg, #0d47a1, #1a237e);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 15px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(0, 255, 200, 0.2);
    }
    .start-btn {
        background: linear-gradient(135deg, #00ffcc, #00cc99) !important;
        color: #0a0a1a !important;
        font-size: 18px !important;
        padding: 12px !important;
    }
    .start-btn:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 40px rgba(0, 255, 200, 0.4) !important;
    }
    .hint-text {
        color: rgba(255, 255, 255, 0.3);
        font-size: 12px;
        text-align: center;
        margin: 5px 0;
    }
    .status-bar {
        display: flex;
        justify-content: space-between;
        font-size: 14px;
        color: rgba(255, 255, 255, 0.4);
        padding: 5px;
        margin: 5px 0;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# تحذير المكتبات
if not ARABIC_SUPPORT or not BIDI_SUPPORT:
    st.warning("⚠️ دعم اللغة العربية غير مكتمل. للتثبيت: pip install arabic_reshaper python-bidi")

# الصفحات
if st.session_state.page == 'game':
    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    
    # الرأس
    st.markdown('<div class="header">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown(f'<div class="score-text">⭐ {st.session_state.score}</div>', unsafe_allow_html=True)
    with col2:
        lives_display = '❤️' * max(0, st.session_state.lives)
        st.markdown(f'<div class="lives-text" style="text-align:center;">{lives_display}</div>', unsafe_allow_html=True)
    with col3:
        matched = len(st.session_state.matched_pairs) // 2
        total = len(st.session_state.pairs) // 2
        st.markdown(f'<div style="text-align:right;color:rgba(255,255,255,0.3);font-size:14px;">{matched}/{total}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # شاشة البداية
    if not st.session_state.game_started and not st.session_state.game_over:
        st.markdown('<div style="text-align:center;padding:30px 0;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:50px;margin-bottom:15px;">🧩</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#00ffcc;font-size:24px;font-weight:bold;">مطابقة الكلمات</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:rgba(255,255,255,0.4);font-size:14px;margin:8px 0 20px 0;">طابق الكلمة مع ترجمتها الصحيحة</div>', unsafe_allow_html=True)
        
        if st.button("🚀 ابدأ اللعب", use_container_width=True):
            start_game()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # اللعبة
    elif not st.session_state.game_over and st.session_state.game_started:
        # الرسالة
        if hasattr(st.session_state, 'message'):
            msg_type = "success" if "✅" in st.session_state.message or "🎉" in st.session_state.message else "error"
            st.markdown(f'<div class="message-box {msg_type}">{st.session_state.message}</div>', unsafe_allow_html=True)
        
        # الشبكة
        if st.session_state.pairs:
            st.markdown('<div class="game-grid">', unsafe_allow_html=True)
            
            for i, pair in enumerate(st.session_state.pairs):
                is_matched = pair.get('matched', False)
                is_selected = st.session_state.selected_pair == i
                
                # تحديد نوع البطاقة
                card_type = "word" if pair.get('word_id') else "translation"
                
                if is_matched:
                    # بطاقة مطابقة
                    card_class = "card matched"
                    display_text = "✅"
                    bg_color = "rgba(0, 255, 200, 0.1)"
                elif is_selected:
                    card_class = "card selected"
                    display_text = pair['word'] if card_type == "word" else pair['translation']
                    bg_color = "rgba(255, 204, 0, 0.1)"
                else:
                    card_class = "card"
                    display_text = pair['word'] if card_type == "word" else pair['translation']
                    bg_color = "rgba(30, 30, 80, 0.7)"
                
                # عرض البطاقة
                if not is_matched:
                    if st.button(
                        display_text,
                        key=f"card_{i}",
                        use_container_width=True,
                        help="انقر للمطابقة"
                    ):
                        if st.session_state.round_active and not st.session_state.game_over:
                            check_match(i)
                            st.rerun()
                else:
                    # بطاقة مطابقة - عرض بدون زر
                    st.markdown(f'''
                    <div class="{card_class}" style="background:{bg_color};">
                        {display_text}
                    </div>
                    ''', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # شريط الحالة
            matched = len(st.session_state.matched_pairs) // 2
            total = len(st.session_state.pairs) // 2
            st.markdown(f'''
            <div class="status-bar">
                <span>📊 {matched}/{total} مطابق</span>
                <span>🔄 {st.session_state.attempts} محاولة</span>
            </div>
            ''', unsafe_allow_html=True)
            
            # زر إعادة تعيين اللعبة
            if st.session_state.round_active and len(st.session_state.matched_pairs) < len(st.session_state.pairs):
                if st.button("🔄 إعادة الترتيب", use_container_width=True):
                    generate_pairs()
                    st.session_state.selected_pair = None
                    st.session_state.message = ""
                    st.rerun()
        
        # نهاية اللعبة (فوز)
        if len(st.session_state.matched_pairs) == len(st.session_state.pairs) and not st.session_state.game_over:
            st.markdown('<div style="text-align:center;padding:20px 0;">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:40px;">🎉</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="game-over-title">💀 انتهت اللعبة</div>', unsafe_allow_html=True)
        
        accuracy = (len(st.session_state.matched_pairs) // 2) / max(1, len(st.session_state.pairs) // 2) * 100
        
        st.markdown(f'''
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-label">⭐ النقاط</div>
                <div class="stat-value gold">{st.session_state.score}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">🏆 أفضل نتيجة</div>
                <div class="stat-value gold">{get_high_score()}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">🧩 المطابقات</div>
                <div class="stat-value">{len(st.session_state.matched_pairs) // 2}/{len(st.session_state.pairs) // 2}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">📊 الدقة</div>
                <div class="stat-value">{accuracy:.0f}%</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 العب مجدداً", use_container_width=True):
                reset_game()
                st.rerun()
        with col2:
            if st.button("📚 القاموس", use_container_width=True):
                go_to_dict()
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # زر القاموس
    if st.session_state.game_started and not st.session_state.game_over:
        if st.button("📚 القاموس", use_container_width=True):
            go_to_dict()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == 'dict':
    st.markdown('<div class="dict-container">', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align:center;color:#00ffcc;font-size:26px;font-weight:bold;margin-bottom:20px;">📚 القاموس</div>', unsafe_allow_html=True)
    
    words = load_words()
    if not words:
        st.info("📝 لا توجد كلمات. أضف كلمات جديدة!")
    
    for i, word in enumerate(words):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f'<div class="word-text">{fix_arabic_text(word["q"])} ＝ {fix_arabic_text(word["a"])}</div>', unsafe_allow_html=True)
        with col2:
            if st.button("✏️", key=f"edit_{i}", use_container_width=True):
                open_edit(i)
                st.rerun()
        with col3:
            if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                delete_word(i)
                st.rerun()
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ أضف كلمة", use_container_width=True):
            open_edit(-1)
            st.rerun()
    with col2:
        if st.button("🎮 العب", use_container_width=True):
            go_to_game()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == 'edit':
    st.markdown('<div class="edit-container">', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align:center;color:#00ffcc;font-size:26px;font-weight:bold;margin-bottom:20px;">✏️ تعديل الكلمة</div>', unsafe_allow_html=True)
    
    # اختيار اللغات
    col1, col2, col3 = st.columns([1, 0.5, 1])
    with col1:
        src_lang = st.selectbox("من", list(LANGUAGES.keys()), 
                               index=list(LANGUAGES.keys()).index(st.session_state.src_lang))
        st.session_state.src_lang = src_lang
    with col2:
        st.markdown('<div style="text-align:center;padding-top:25px;color:#00ffcc;font-size:22px;">➔</div>', unsafe_allow_html=True)
    with col3:
        target_lang = st.selectbox("إلى", list(LANGUAGES.keys()), 
                                  index=list(LANGUAGES.keys()).index(st.session_state.target_lang))
        st.session_state.target_lang = target_lang
    
    # حقول الإدخال
    if st.session_state.selected_word:
        q = st.text_input("الكلمة", value=st.session_state.selected_word.get('q', ''), placeholder="أدخل الكلمة...")
        a = st.text_area("الترجمة", value=st.session_state.selected_word.get('a', ''), height=80, placeholder="الترجمة...")
    else:
        q = st.text_input("الكلمة", value="", placeholder="أدخل الكلمة...")
        a = st.text_area("الترجمة", value="", height=80, placeholder="الترجمة...")
    
    # الترجمة التلقائية
    if st.button("✨ ترجمة تلقائية", use_container_width=True):
        if q.strip():
            with st.spinner("🔄 جاري الترجمة..."):
                translated = translate_text(q, st.session_state.src_lang, st.session_state.target_lang)
                if translated and "خطأ" not in translated:
                    st.session_state.selected_word = {"q": q, "a": translated}
                    st.rerun()
                else:
                    st.error("⚠️ فشلت الترجمة! تأكد من الاتصال بالإنترنت.")
        else:
            st.warning("⚠️ أدخل كلمة أولاً!")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 حفظ", use_container_width=True):
            if save_word(q, a):
                st.success("✅ تم الحفظ!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ املأ كلا الحقلين!")
    with col2:
        if st.button("❌ إلغاء", use_container_width=True):
            st.session_state.page = 'dict'
            st.session_state.edit_mode = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
