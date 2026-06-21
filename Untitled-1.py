import streamlit as st
import random
import os
import json
import urllib.request
import time

# محاولة استيراد مكتبات اللغة العربية مع معالجة الأخطاء
try:
    import arabic_reshaper
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    print("Warning: arabic_reshaper not installed. Arabic text will not be reshaped.")

try:
    from bidi.algorithm import get_display
    BIDI_SUPPORT = True
except ImportError:
    BIDI_SUPPORT = False
    print("Warning: python-bidi not installed. Arabic text will not be displayed correctly.")

# دالة معالجة النص العربي مع التعامل مع الأخطاء
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

# الكلمات الافتراضية
DEFAULT_WORDS = [
    {"q": "House", "a": "Maison"},
    {"q": "Book", "a": "Livre"},
    {"q": "Car", "a": "Voiture"},
    {"q": "Cat", "a": "Chat"},
    {"q": "Dog", "a": "Chien"}
]

LANGUAGES = {
    "English": "en",
    "French": "fr",
    "Arabic": "ar",
    "Spanish": "es",
    "German": "de"
}

# دوال المساعدة
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
    if len(words) < 3:
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
    st.session_state.lives = 3
if 'game_active' not in st.session_state:
    st.session_state.game_active = True
if 'round_active' not in st.session_state:
    st.session_state.round_active = False
if 'words_db' not in st.session_state:
    st.session_state.words_db = load_words()
if 'player_pos' not in st.session_state:
    st.session_state.player_pos = 1
if 'options' not in st.session_state:
    st.session_state.options = []
if 'correct_ans' not in st.session_state:
    st.session_state.correct_ans = ""
if 'question_text' not in st.session_state:
    st.session_state.question_text = "Loading..."
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
if 'translation' not in st.session_state:
    st.session_state.translation = ""
if 'word_to_edit' not in st.session_state:
    st.session_state.word_to_edit = None

# دوال اللعبة
def reset_game_stats():
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.game_over = False
    st.session_state.game_active = True
    st.session_state.round_active = False
    st.session_state.options = []

def restart_game():
    reset_game_stats()
    start_round()

def start_round():
    if not st.session_state.game_active:
        return
    
    if st.session_state.lives <= 0:
        save_high_score(st.session_state.score)
        st.session_state.game_over = True
        return
    
    st.session_state.round_active = True
    target = random.choice(st.session_state.words_db)
    
    st.session_state.question_text = fix_arabic_text(target['q'])
    st.session_state.correct_ans = target['a']
    
    opts = [st.session_state.correct_ans]
    while len(opts) < 3:
        w = random.choice(st.session_state.words_db)['a']
        if w not in opts:
            opts.append(w)
    random.shuffle(opts)
    
    st.session_state.options = [fix_arabic_text(opt) for opt in opts]

def check_answer(choice_index):
    if not st.session_state.game_active or not st.session_state.round_active:
        return
    
    st.session_state.round_active = False
    
    if st.session_state.options[choice_index] == fix_arabic_text(st.session_state.correct_ans):
        st.session_state.score += 10
        st.success("✅ Correct!")
    else:
        st.session_state.lives -= 1
        st.error(f"❌ Wrong! Correct answer: {fix_arabic_text(st.session_state.correct_ans)}")
    
    if st.session_state.lives <= 0:
        save_high_score(st.session_state.score)
        st.session_state.game_over = True
    else:
        time.sleep(1)
        start_round()

def go_to_dict():
    st.session_state.page = 'dict'
    st.session_state.selected_word = None
    st.session_state.edit_mode = False

def go_to_game():
    st.session_state.page = 'game'
    if st.session_state.lives <= 0:
        restart_game()
    else:
        start_round()

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
        return "Error! Check Internet."

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

# CSS للتنسيق
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%);
        padding: 20px;
    }
    .game-container {
        background: rgba(10, 10, 30, 0.8);
        border-radius: 20px;
        padding: 20px;
        margin: 10px auto;
        max-width: 450px;
        min-height: 700px;
        border: 1px solid rgba(0, 255, 200, 0.2);
        box-shadow: 0 0 30px rgba(0, 255, 200, 0.1);
    }
    .score-lives {
        display: flex;
        justify-content: space-between;
        padding: 10px 15px;
        margin-bottom: 20px;
    }
    .score-text {
        color: #00ffcc;
        font-size: 20px;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 255, 200, 0.5);
    }
    .lives-text {
        color: #ff3366;
        font-size: 20px;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(255, 51, 102, 0.5);
    }
    .question-box {
        background: rgba(20, 20, 50, 0.6);
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
        border: 1px solid rgba(0, 255, 200, 0.1);
    }
    .question-text {
        color: white;
        font-size: 38px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
    }
    .options-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin: 25px 0;
    }
    .option-btn {
        background: rgba(30, 30, 80, 0.6);
        color: #ffcc00;
        border: 1px solid rgba(255, 204, 0, 0.3);
        border-radius: 12px;
        padding: 15px;
        font-size: 24px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
        cursor: pointer;
        text-align: center;
    }
    .option-btn:hover {
        background: rgba(0, 255, 200, 0.1);
        border-color: #00ffcc;
        transform: scale(1.02);
    }
    .player-indicator {
        text-align: center;
        color: #00ffcc;
        font-size: 28px;
        padding: 15px;
        text-shadow: 0 0 20px rgba(0, 255, 200, 0.5);
        margin: 20px 0;
    }
    .game-over-box {
        background: rgba(20, 20, 50, 0.95);
        border-radius: 25px;
        padding: 30px;
        margin: 20px 0;
        border: 2px solid rgba(255, 51, 51, 0.3);
        text-align: center;
    }
    .game-over-title {
        color: #ff3333;
        font-size: 36px;
        font-weight: bold;
        text-shadow: 0 0 30px rgba(255, 51, 51, 0.5);
    }
    .dict-container {
        background: rgba(10, 10, 30, 0.8);
        border-radius: 20px;
        padding: 20px;
        margin: 10px auto;
        max-width: 450px;
        min-height: 700px;
        border: 1px solid rgba(0, 255, 200, 0.2);
    }
    .word-row {
        background: rgba(20, 20, 50, 0.6);
        border-radius: 10px;
        padding: 10px 15px;
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
    .edit-btn, .delete-btn {
        background: transparent;
        border: none;
        padding: 5px 12px;
        border-radius: 8px;
        font-weight: bold;
        cursor: pointer;
        margin: 0 3px;
    }
    .edit-btn {
        color: #ffcc00;
    }
    .edit-btn:hover {
        background: rgba(255, 204, 0, 0.1);
    }
    .delete-btn {
        color: #ff3333;
    }
    .delete-btn:hover {
        background: rgba(255, 51, 51, 0.1);
    }
    .edit-container {
        background: rgba(10, 10, 30, 0.8);
        border-radius: 20px;
        padding: 25px;
        margin: 10px auto;
        max-width: 450px;
        min-height: 700px;
        border: 1px solid rgba(0, 255, 200, 0.2);
    }
    .stTextInput > div > div > input {
        background: rgba(20, 20, 50, 0.8);
        color: white;
        border: 1px solid rgba(0, 255, 200, 0.3);
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #0d47a1, #1a237e);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(0, 255, 200, 0.2);
    }
    .stSelectbox > div > div {
        background: rgba(20, 20, 50, 0.8);
        color: white;
        border: 1px solid rgba(0, 255, 200, 0.3);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# عرض تحذير إذا كانت مكتبات اللغة العربية غير مثبتة
if not ARABIC_SUPPORT or not BIDI_SUPPORT:
    st.warning("⚠️ Arabic text support libraries are not installed. Arabic text may not display correctly. To fix: pip install arabic_reshaper python-bidi")

# الصفحات
if st.session_state.page == 'game':
    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f'<div class="score-text">🏆 Score: {st.session_state.score}</div>', unsafe_allow_html=True)
    with col2:
        lives_display = '❤' * max(0, st.session_state.lives)
        st.markdown(f'<div class="lives-text" style="text-align:right;">{lives_display}</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="question-box">', unsafe_allow_html=True)
    st.markdown(f'<div class="question-text">{st.session_state.question_text}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.options and not st.session_state.game_over:
        st.markdown('<div class="options-container">', unsafe_allow_html=True)
        for i, option in enumerate(st.session_state.options):
            if st.button(option, key=f"opt_{i}", use_container_width=True):
                check_answer(i)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="player-indicator">◄ {["◄", "■", "►"][st.session_state.player_pos]} ►</div>', unsafe_allow_html=True)
    
    if st.session_state.game_over:
        st.markdown('<div class="game-over-box">', unsafe_allow_html=True)
        st.markdown('<div class="game-over-title">💀 GAME OVER</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:white;font-size:24px;margin:15px 0;">Your Score: {st.session_state.score}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#00ffcc;font-size:22px;margin:15px 0;">Best Score: {get_high_score()}</div>', unsafe_allow_html=True)
        
        if st.button("🔄 Play Again", use_container_width=True):
            restart_game()
            st.rerun()
        
        if st.button("⚙ Dictionary", use_container_width=True):
            go_to_dict()
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("◄ Left", use_container_width=True):
            st.session_state.player_pos = 0
            st.rerun()
    with col2:
        if st.button("■ Center", use_container_width=True):
            st.session_state.player_pos = 1
            st.rerun()
    with col3:
        if st.button("Right ►", use_container_width=True):
            st.session_state.player_pos = 2
            st.rerun()
    
    if st.button("⚙ Dictionary", use_container_width=True):
        go_to_dict()
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == 'dict':
    st.markdown('<div class="dict-container">', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align:center;color:#00ffcc;font-size:26px;font-weight:bold;margin-bottom:20px;">📚 DICTIONARY</div>', unsafe_allow_html=True)
    
    words = load_words()
    for i, word in enumerate(words):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f'<div class="word-text">{fix_arabic_text(word["q"])} ＝ {fix_arabic_text(word["a"])}</div>', unsafe_allow_html=True)
        with col2:
            edit_col, del_col = st.columns([1, 1])
            with edit_col:
                if st.button(f"✏️", key=f"edit_{i}", use_container_width=True):
                    open_edit(i)
                    st.rerun()
            with del_col:
                if st.button(f"🗑️", key=f"del_{i}", use_container_width=True):
                    delete_word(i)
                    st.rerun()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➕ Add Word", use_container_width=True):
            open_edit(-1)
            st.rerun()
    with col2:
        if st.button("🎮 Play Game", use_container_width=True):
            go_to_game()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == 'edit':
    st.markdown('<div class="edit-container">', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align:center;color:#00ffcc;font-size:26px;font-weight:bold;margin-bottom:20px;">✏️ EDIT WORD</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 0.5, 1])
    with col1:
        src_lang = st.selectbox("From", list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index(st.session_state.src_lang))
        st.session_state.src_lang = src_lang
    with col2:
        st.markdown('<div style="text-align:center;padding-top:25px;color:#00ffcc;font-size:20px;">➔</div>', unsafe_allow_html=True)
    with col3:
        target_lang = st.selectbox("To", list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index(st.session_state.target_lang))
        st.session_state.target_lang = target_lang
    
    if st.session_state.selected_word:
        q = st.text_input("Word", value=st.session_state.selected_word.get('q', ''))
        a = st.text_area("Translation", value=st.session_state.selected_word.get('a', ''))
    else:
        q = st.text_input("Word", value="")
        a = st.text_area("Translation", value="")
    
    if st.button("✨ Auto-Translate", use_container_width=True):
        if q.strip():
            translated = translate_text(q, st.session_state.src_lang, st.session_state.target_lang)
            a = translated
            st.session_state.translation = translated
            st.rerun()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("💾 Save Word", use_container_width=True):
            if save_word(q, a):
                st.success("✅ Word saved successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Please fill both fields!")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.page = 'dict'
            st.session_state.edit_mode = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# بدء اللعبة
if st.session_state.page == 'game' and not st.session_state.options and not st.session_state.game_over:
    start_round()
    st.rerun()
