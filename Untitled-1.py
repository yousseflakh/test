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
if 'combo' not in st.session_state:
    st.session_state.combo = 0
if 'max_combo' not in st.session_state:
    st.session_state.max_combo = 0
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'current_word' not in st.session_state:
    st.session_state.current_word = ""
if 'current_translation' not in st.session_state:
    st.session_state.current_translation = ""
if 'show_word' not in st.session_state:
    st.session_state.show_word = True
if 'difficulty' not in st.session_state:
    st.session_state.difficulty = 1
if 'words_answered' not in st.session_state:
    st.session_state.words_answered = 0
if 'correct_answers' not in st.session_state:
    st.session_state.correct_answers = 0
if 'time_bonus' not in st.session_state:
    st.session_state.time_bonus = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0
if 'total_time' not in st.session_state:
    st.session_state.total_time = 0
if 'round_active' not in st.session_state:
    st.session_state.round_active = False
if 'waiting_for_next' not in st.session_state:
    st.session_state.waiting_for_next = False

def reset_game():
    st.session_state.score = 0
    st.session_state.lives = 5
    st.session_state.game_over = False
    st.session_state.combo = 0
    st.session_state.max_combo = 0
    st.session_state.game_started = False
    st.session_state.words_answered = 0
    st.session_state.correct_answers = 0
    st.session_state.difficulty = 1
    st.session_state.round_active = False
    st.session_state.waiting_for_next = False
    st.session_state.total_time = 0

def start_game():
    st.session_state.game_started = True
    st.session_state.round_active = True
    st.session_state.start_time = time.time()
    next_word()

def next_word():
    if st.session_state.lives <= 0:
        save_high_score(st.session_state.score)
        st.session_state.game_over = True
        return
    
    # زيادة الصعوبة
    st.session_state.difficulty = 1 + (st.session_state.words_answered // 3)
    
    # اختيار كلمة عشوائية
    word = random.choice(st.session_state.words_db)
    st.session_state.current_word = word['q']
    st.session_state.current_translation = word['a']
    st.session_state.show_word = True
    st.session_state.round_active = True
    st.session_state.waiting_for_next = False
    st.session_state.start_time = time.time()

def check_answer(user_answer):
    if not st.session_state.round_active or st.session_state.waiting_for_next:
        return
    
    st.session_state.round_active = False
    st.session_state.waiting_for_next = True
    st.session_state.words_answered += 1
    
    # حساب الوقت المستغرق
    elapsed = time.time() - st.session_state.start_time
    st.session_state.total_time += elapsed
    
    # التحقق من الإجابة
    if user_answer.lower().strip() == st.session_state.current_translation.lower().strip():
        # نقاط الكومبو
        combo_bonus = st.session_state.combo * 3
        time_bonus = max(0, int((5 - elapsed) * 2))
        
        points = 10 + combo_bonus + time_bonus
        st.session_state.score += points
        st.session_state.combo += 1
        st.session_state.correct_answers += 1
        
        if st.session_state.combo > st.session_state.max_combo:
            st.session_state.max_combo = st.session_state.combo
        
        st.session_state.message = f"✅ صحيح! +{points} نقاط (كومبو: {st.session_state.combo}x)"
        st.session_state.message_type = "success"
    else:
        st.session_state.lives -= 1
        st.session_state.combo = 0
        st.session_state.message = f"❌ خطأ! الإجابة: {st.session_state.current_translation}"
        st.session_state.message_type = "error"
        
        if st.session_state.lives <= 0:
            save_high_score(st.session_state.score)
            st.session_state.game_over = True
            return
    
    # عرض الكلمة والترجمة الصحيحة
    st.session_state.show_word = False
    st.session_state.current_translation_display = st.session_state.current_translation

def go_to_dict():
    st.session_state.page = 'dict'
    st.session_state.selected_word = None
    st.session_state.edit_mode = False

def go_to_game():
    st.session_state.page = 'game'
    if st.session_state.lives <= 0:
        reset_game()
    elif not st.session_state.game_started:
        start_game()

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
        padding: 20px;
        min-height: 100vh;
    }
    .game-container {
        background: rgba(10, 10, 30, 0.9);
        border-radius: 25px;
        padding: 30px;
        margin: 0 auto;
        max-width: 500px;
        min-height: 650px;
        border: 1px solid rgba(0, 255, 200, 0.2);
        box-shadow: 0 0 50px rgba(0, 255, 200, 0.1);
        position: relative;
        overflow: hidden;
    }
    .header {
        display: flex;
        justify-content: space-between;
        padding: 5px 5px 15px 5px;
        flex-wrap: wrap;
        gap: 8px;
    }
    .score-text {
        color: #00ffcc;
        font-size: 20px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(0, 255, 200, 0.5);
    }
    .lives-text {
        color: #ff3366;
        font-size: 20px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(255, 51, 102, 0.5);
    }
    .combo-text {
        color: #ffcc00;
        font-size: 18px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(255, 204, 0, 0.5);
        animation: pulse 0.5s ease-in-out;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.3); }
        100% { transform: scale(1); }
    }
    .word-box {
        background: rgba(20, 20, 50, 0.8);
        border-radius: 20px;
        padding: 40px 20px;
        margin: 20px 0 30px 0;
        text-align: center;
        border: 2px solid rgba(0, 255, 200, 0.2);
        min-height: 150px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: all 0.5s ease;
    }
    .word-display {
        color: white;
        font-size: 42px;
        font-weight: bold;
        text-shadow: 0 0 40px rgba(255, 255, 255, 0.2);
        margin: 0;
        transition: all 0.5s ease;
    }
    .translation-display {
        color: #00ffcc;
        font-size: 28px;
        font-weight: bold;
        text-shadow: 0 0 30px rgba(0, 255, 200, 0.3);
        margin: 10px 0 0 0;
        animation: fadeIn 0.5s ease;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .input-area {
        margin: 20px 0;
    }
    .input-area input {
        width: 100%;
        padding: 15px 20px;
        font-size: 24px;
        border: 2px solid rgba(0, 255, 200, 0.3);
        border-radius: 15px;
        background: rgba(20, 20, 50, 0.8);
        color: white;
        text-align: center;
        transition: all 0.3s ease;
        font-weight: bold;
    }
    .input-area input:focus {
        outline: none;
        border-color: #00ffcc;
        box-shadow: 0 0 30px rgba(0, 255, 200, 0.2);
    }
    .message-box {
        text-align: center;
        padding: 15px;
        margin: 10px 0 15px 0;
        font-size: 20px;
        font-weight: bold;
        border-radius: 12px;
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
        border-radius: 25px;
        padding: 30px;
        margin: 20px 0;
        border: 2px solid rgba(255, 51, 51, 0.3);
        text-align: center;
        animation: fadeIn 0.5s ease;
    }
    .game-over-title {
        color: #ff3333;
        font-size: 36px;
        font-weight: bold;
        text-shadow: 0 0 30px rgba(255, 51, 51, 0.5);
    }
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin: 15px 0;
    }
    .stat-item {
        background: rgba(20, 20, 50, 0.5);
        padding: 12px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid rgba(0, 255, 200, 0.1);
    }
    .stat-label {
        color: rgba(255, 255, 255, 0.5);
        font-size: 12px;
    }
    .stat-value {
        color: #00ffcc;
        font-size: 22px;
        font-weight: bold;
        margin-top: 3px;
    }
    .stat-value.gold {
        color: #ffcc00;
    }
    .stat-value.red {
        color: #ff3366;
    }
    .dict-container {
        background: rgba(10, 10, 30, 0.9);
        border-radius: 20px;
        padding: 25px;
        margin: 0 auto;
        max-width: 500px;
        min-height: 650px;
        border: 1px solid rgba(0, 255, 200, 0.2);
    }
    .word-row {
        background: rgba(20, 20, 50, 0.7);
        border-radius: 10px;
        padding: 12px 15px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(0, 255, 200, 0.1);
    }
    .word-text {
        color: white;
        font-size: 16px;
        flex: 1;
    }
    .edit-container {
        background: rgba(10, 10, 30, 0.9);
        border-radius: 20px;
        padding: 25px;
        margin: 0 auto;
        max-width: 500px;
        min-height: 650px;
        border: 1px solid rgba(0, 255, 200, 0.2);
    }
    .stButton > button {
        background: linear-gradient(135deg, #0d47a1, #1a237e);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 20px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(0, 255, 200, 0.2);
    }
    .stTextInput > div > div > input {
        background: rgba(20, 20, 50, 0.8);
        color: white;
        border: 1px solid rgba(0, 255, 200, 0.3);
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
    }
    .stTextArea > div > div > textarea {
        background: rgba(20, 20, 50, 0.8);
        color: white;
        border: 1px solid rgba(0, 255, 200, 0.3);
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
    }
    .stSelectbox > div > div {
        background: rgba(20, 20, 50, 0.8);
        color: white;
        border: 1px solid rgba(0, 255, 200, 0.3);
        border-radius: 10px;
    }
    .difficulty-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: bold;
        background: rgba(255, 204, 0, 0.15);
        color: #ffcc00;
        border: 1px solid rgba(255, 204, 0, 0.2);
    }
    .hint-text {
        color: rgba(255, 255, 255, 0.3);
        font-size: 14px;
        margin-top: 5px;
    }
    .start-btn {
        background: linear-gradient(135deg, #00ffcc, #00cc99) !important;
        color: #0a0a1a !important;
        font-size: 20px !important;
        padding: 15px !important;
    }
    .start-btn:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 40px rgba(0, 255, 200, 0.4) !important;
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
        st.markdown(f'<div class="score-text">🏆 {st.session_state.score}</div>', unsafe_allow_html=True)
    with col2:
        lives_display = '❤️' * max(0, st.session_state.lives)
        st.markdown(f'<div class="lives-text" style="text-align:center;">{lives_display}</div>', unsafe_allow_html=True)
    with col3:
        if st.session_state.combo > 0:
            st.markdown(f'<div class="combo-text" style="text-align:right;">🔥 {st.session_state.combo}x</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align:right;color:rgba(255,255,255,0.2);font-size:14px;">المستوى {st.session_state.difficulty}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # شاشة البداية
    if not st.session_state.game_started and not st.session_state.game_over:
        st.markdown('<div style="text-align:center;padding:40px 0;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:60px;margin-bottom:20px;">🌍</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#00ffcc;font-size:28px;font-weight:bold;">مترجم النخبة</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:rgba(255,255,255,0.5);font-size:16px;margin:10px 0 30px 0;">ترجم الكلمات بأسرع وقت ممكن</div>', unsafe_allow_html=True)
        
        if st.button("🚀 ابدأ اللعب", use_container_width=True):
            start_game()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # عرض الكلمة والإدخال
    elif not st.session_state.game_over and st.session_state.game_started:
        # عرض الكلمة
        st.markdown('<div class="word-box">', unsafe_allow_html=True)
        if st.session_state.show_word:
            st.markdown(f'<div class="word-display">{fix_arabic_text(st.session_state.current_word)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="hint-text">✍️ اكتب الترجمة...</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="word-display" style="font-size:28px;">{fix_arabic_text(st.session_state.current_word)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="translation-display">➜ {fix_arabic_text(st.session_state.current_translation_display)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # الرسالة
        if hasattr(st.session_state, 'message') and st.session_state.waiting_for_next:
            msg_type = "success" if "✅" in st.session_state.message else "error"
            st.markdown(f'<div class="message-box {msg_type}">{st.session_state.message}</div>', unsafe_allow_html=True)
        
        # حقل الإدخال
        if st.session_state.round_active and not st.session_state.waiting_for_next:
            user_input = st.text_input("", placeholder="اكتب الترجمة هنا...", key="word_input")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ تأكيد", use_container_width=True):
                    if user_input.strip():
                        check_answer(user_input.strip())
                        st.rerun()
                    else:
                        st.warning("⚠️ أدخل الترجمة!")
            
            with col2:
                if st.button("💡 تلميح", use_container_width=True):
                    # إظهار أول حرف من الترجمة
                    if st.session_state.current_translation:
                        hint = st.session_state.current_translation[0] + "..." 
                        st.info(f"💡 التلميح: {hint}")
        
        # زر التالي (يظهر بعد الإجابة)
        if st.session_state.waiting_for_next and not st.session_state.game_over:
            if st.button("➡️ كلمة جديدة", use_container_width=True):
                next_word()
                st.rerun()
    
    # شاشة Game Over
    if st.session_state.game_over:
        st.markdown('<div class="game-over-box">', unsafe_allow_html=True)
        st.markdown('<div class="game-over-title">💀 انتهت اللعبة</div>', unsafe_allow_html=True)
        
        # إحصائيات
        accuracy = (st.session_state.correct_answers / max(1, st.session_state.words_answered)) * 100
        avg_time = st.session_state.total_time / max(1, st.session_state.words_answered)
        
        st.markdown(f'''
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-label">🎯 النقاط</div>
                <div class="stat-value gold">{st.session_state.score}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">🔥 أفضل كومبو</div>
                <div class="stat-value gold">{st.session_state.max_combo}x</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">📊 الدقة</div>
                <div class="stat-value">{accuracy:.1f}%</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">⏱️ متوسط الوقت</div>
                <div class="stat-value">{avg_time:.1f}s</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">✅ صحيح</div>
                <div class="stat-value" style="color:#00ff00;">{st.session_state.correct_answers}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">🏆 أفضل نتيجة</div>
                <div class="stat-value gold">{get_high_score()}</div>
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
    if st.session_state.game_started and not st.session_state.game_over and not st.session_state.waiting_for_next:
        if st.button("📚 القاموس", use_container_width=True):
            go_to_dict()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == 'dict':
    st.markdown('<div class="dict-container">', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align:center;color:#00ffcc;font-size:28px;font-weight:bold;margin-bottom:25px;">📚 القاموس</div>', unsafe_allow_html=True)
    
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
    
    st.markdown('<div style="text-align:center;color:#00ffcc;font-size:28px;font-weight:bold;margin-bottom:25px;">✏️ تعديل الكلمة</div>', unsafe_allow_html=True)
    
    # اختيار اللغات
    col1, col2, col3 = st.columns([1, 0.5, 1])
    with col1:
        src_lang = st.selectbox("من", list(LANGUAGES.keys()), 
                               index=list(LANGUAGES.keys()).index(st.session_state.src_lang))
        st.session_state.src_lang = src_lang
    with col2:
        st.markdown('<div style="text-align:center;padding-top:25px;color:#00ffcc;font-size:24px;">➔</div>', unsafe_allow_html=True)
    with col3:
        target_lang = st.selectbox("إلى", list(LANGUAGES.keys()), 
                                  index=list(LANGUAGES.keys()).index(st.session_state.target_lang))
        st.session_state.target_lang = target_lang
    
    # حقول الإدخال
    if st.session_state.selected_word:
        q = st.text_input("الكلمة", value=st.session_state.selected_word.get('q', ''), placeholder="أدخل الكلمة...")
        a = st.text_area("الترجمة", value=st.session_state.selected_word.get('a', ''), height=100, placeholder="الترجمة...")
    else:
        q = st.text_input("الكلمة", value="", placeholder="أدخل الكلمة...")
        a = st.text_area("الترجمة", value="", height=100, placeholder="الترجمة...")
    
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
