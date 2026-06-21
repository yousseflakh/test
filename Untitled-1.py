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
    {"q": "Dog", "a": "Chien"}
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
if 'words_db' not in st.session_state:
    st.session_state.words_db = load_words()
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
if 'word_to_edit' not in st.session_state:
    st.session_state.word_to_edit = None
if 'options' not in st.session_state:
    st.session_state.options = []
if 'correct_ans' not in st.session_state:
    st.session_state.correct_ans = ""
if 'option_colors' not in st.session_state:
    st.session_state.option_colors = ["#ffcc00", "#ffcc00", "#ffcc00"]
if 'waiting_for_next' not in st.session_state:
    st.session_state.waiting_for_next = False
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'round_started' not in st.session_state:
    st.session_state.round_started = False
if 'falling_positions' not in st.session_state:
    st.session_state.falling_positions = [0, 0, 0]
if 'falling_speeds' not in st.session_state:
    st.session_state.falling_speeds = [1, 1.2, 0.8]
if 'game_loop' not in st.session_state:
    st.session_state.game_loop = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if 'player_position' not in st.session_state:
    st.session_state.player_position = 1  # 0=يسار, 1=وسط, 2=يمين
if 'option_texts' not in st.session_state:
    st.session_state.option_texts = ["", "", ""]

def reset_game():
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.game_over = False
    st.session_state.options = []
    st.session_state.option_colors = ["#ffcc00", "#ffcc00", "#ffcc00"]
    st.session_state.waiting_for_next = False
    st.session_state.show_result = False
    st.session_state.round_started = False
    st.session_state.falling_positions = [0, 0, 0]
    st.session_state.game_loop = False
    start_round()

def start_round():
    if st.session_state.lives <= 0:
        save_high_score(st.session_state.score)
        st.session_state.game_over = True
        return
    
    # اختيار كلمة عشوائية
    target = random.choice(st.session_state.words_db)
    st.session_state.question_text = fix_arabic_text(target['q'])
    st.session_state.correct_ans = target['a']
    
    # اختيار 3 خيارات
    opts = [st.session_state.correct_ans]
    temp_words = [w for w in st.session_state.words_db if w['a'] != st.session_state.correct_ans]
    
    random.shuffle(temp_words)
    for w in temp_words:
        if len(opts) < 3:
            if w['a'] not in opts:
                opts.append(w['a'])
    
    # إذا لم يكن هناك 3 خيارات
    fake_options = ["❓ Option X", "❓ Option Y", "❓ Option Z"]
    for fake in fake_options:
        if len(opts) < 3 and fake not in opts:
            opts.append(fake)
    
    random.shuffle(opts)
    st.session_state.options = [fix_arabic_text(opt) for opt in opts]
    st.session_state.option_texts = st.session_state.options.copy()
    st.session_state.option_colors = ["#ffcc00", "#ffcc00", "#ffcc00"]
    st.session_state.waiting_for_next = False
    st.session_state.show_result = False
    st.session_state.round_started = True
    st.session_state.falling_positions = [0, 0, 0]
    st.session_state.game_loop = True
    st.session_state.last_update = time.time()
    
    # سرعات مختلفة لكل خيار
    st.session_state.falling_speeds = [random.uniform(0.8, 1.5) for _ in range(3)]

def update_falling():
    """تحديث مواقع الخيارات المتساقطة"""
    if not st.session_state.game_loop or st.session_state.waiting_for_next:
        return
    
    current_time = time.time()
    delta = current_time - st.session_state.last_update
    st.session_state.last_update = current_time
    
    # تحديث المواقع
    for i in range(3):
        st.session_state.falling_positions[i] += st.session_state.falling_speeds[i] * delta * 80
        
        # إذا وصل الخيار إلى الأسفل
        if st.session_state.falling_positions[i] >= 550:
            # إذا كان هذا هو الخيار الصحيح ولم يتم اختياره بعد
            if st.session_state.options[i] == fix_arabic_text(st.session_state.correct_ans):
                # الخيار الصحيح يضرب الأسفل - خسارة حياة
                if not st.session_state.show_result:
                    st.session_state.lives -= 1
                    st.session_state.option_colors[i] = "#ff0000"
                    st.session_state.show_result = True
                    st.session_state.waiting_for_next = True
                    st.session_state.game_loop = False
                    st.session_state.message = f"❌ ضاع! الإجابة: {fix_arabic_text(st.session_state.correct_ans)}"
                    
                    if st.session_state.lives <= 0:
                        save_high_score(st.session_state.score)
                        st.session_state.game_over = True
            else:
                # خيار خاطئ يضرب الأسفل - إعادة تعيين موقعه
                st.session_state.falling_positions[i] = 0

def check_answer(choice_index):
    """التحقق من الإجابة عند النقر"""
    if st.session_state.waiting_for_next or st.session_state.game_over:
        return
    
    st.session_state.game_loop = False
    st.session_state.waiting_for_next = True
    
    # العثور على الخيار الصحيح
    correct_index = -1
    for i, opt in enumerate(st.session_state.options):
        if opt == fix_arabic_text(st.session_state.correct_ans):
            correct_index = i
            break
    
    # تغيير الألوان
    st.session_state.option_colors = ["#ffcc00", "#ffcc00", "#ffcc00"]
    
    if choice_index == correct_index:
        st.session_state.score += 10
        st.session_state.option_colors[choice_index] = "#00ff00"
        st.session_state.message = "✅ صحيح!"
    else:
        st.session_state.lives -= 1
        st.session_state.option_colors[choice_index] = "#ff0000"
        if correct_index != -1:
            st.session_state.option_colors[correct_index] = "#00ff00"
        st.session_state.message = f"❌ خطأ! الإجابة: {fix_arabic_text(st.session_state.correct_ans)}"
    
    st.session_state.show_result = True
    
    if st.session_state.lives <= 0:
        save_high_score(st.session_state.score)
        st.session_state.game_over = True

def go_to_dict():
    st.session_state.page = 'dict'
    st.session_state.selected_word = None
    st.session_state.edit_mode = False
    st.session_state.game_loop = False

def go_to_game():
    st.session_state.page = 'game'
    if st.session_state.lives <= 0:
        reset_game()
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
        border-radius: 20px;
        padding: 25px;
        margin: 0 auto;
        max-width: 500px;
        min-height: 700px;
        border: 1px solid rgba(0, 255, 200, 0.2);
        box-shadow: 0 0 50px rgba(0, 255, 200, 0.1);
        position: relative;
        overflow: hidden;
    }
    .header {
        display: flex;
        justify-content: space-between;
        padding: 10px 5px;
        margin-bottom: 20px;
        z-index: 10;
        position: relative;
    }
    .score-text {
        color: #00ffcc;
        font-size: 22px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(0, 255, 200, 0.5);
    }
    .lives-text {
        color: #ff3366;
        font-size: 22px;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(255, 51, 102, 0.5);
    }
    .question-box {
        background: rgba(20, 20, 50, 0.8);
        border-radius: 15px;
        padding: 25px 20px;
        margin: 10px 0 20px 0;
        text-align: center;
        border: 1px solid rgba(0, 255, 200, 0.15);
        min-height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
        position: relative;
    }
    .question-text {
        color: white;
        font-size: 32px;
        font-weight: bold;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.2);
        margin: 0;
    }
    .falling-container {
        position: relative;
        height: 450px;
        margin: 10px 0;
        overflow: hidden;
        z-index: 1;
    }
    .falling-option {
        position: absolute;
        left: 10%;
        width: 80%;
        padding: 15px;
        border-radius: 12px;
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        cursor: pointer;
        transition: all 0.1s ease;
        z-index: 2;
        background: rgba(30, 30, 80, 0.8);
        border: 2px solid #ffcc00;
        color: #ffcc00;
    }
    .falling-option:hover {
        transform: scale(1.05);
        box-shadow: 0 0 30px rgba(0, 255, 200, 0.3);
    }
    .player-indicator {
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        color: #00ffcc;
        font-size: 32px;
        font-weight: bold;
        text-shadow: 0 0 30px rgba(0, 255, 200, 0.8);
        z-index: 10;
        background: rgba(10, 10, 30, 0.8);
        padding: 8px 20px;
        border-radius: 15px;
        border: 2px solid rgba(0, 255, 200, 0.3);
    }
    .controls {
        display: flex;
        gap: 10px;
        margin-top: 10px;
        z-index: 10;
        position: relative;
    }
    .controls button {
        flex: 1;
        padding: 12px;
        border: none;
        border-radius: 10px;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        background: rgba(30, 30, 80, 0.8);
        color: #00ffcc;
        border: 1px solid rgba(0, 255, 200, 0.3);
    }
    .controls button:hover {
        background: rgba(0, 255, 200, 0.2);
        transform: scale(1.05);
    }
    .game-over-box {
        background: rgba(20, 20, 50, 0.95);
        border-radius: 25px;
        padding: 30px;
        margin: 20px 0;
        border: 2px solid rgba(255, 51, 51, 0.3);
        text-align: center;
        z-index: 20;
        position: relative;
    }
    .game-over-title {
        color: #ff3333;
        font-size: 36px;
        font-weight: bold;
        text-shadow: 0 0 30px rgba(255, 51, 51, 0.5);
    }
    .message-box {
        text-align: center;
        padding: 15px;
        margin: 10px 0;
        font-size: 20px;
        font-weight: bold;
        border-radius: 10px;
        z-index: 10;
        position: relative;
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
</style>
""", unsafe_allow_html=True)

# تحذير المكتبات
if not ARABIC_SUPPORT or not BIDI_SUPPORT:
    st.warning("⚠️ دعم اللغة العربية غير مكتمل. للتثبيت: pip install arabic_reshaper python-bidi")

# الصفحات
if st.session_state.page == 'game':
    # تحديث الحركة
    if st.session_state.game_loop and not st.session_state.waiting_for_next and not st.session_state.game_over:
        update_falling()
    
    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    
    # الرأس
    st.markdown('<div class="header">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="score-text">🏆 {st.session_state.score}</div>', unsafe_allow_html=True)
    with col2:
        lives_display = '❤' * max(0, st.session_state.lives)
        st.markdown(f'<div class="lives-text" style="text-align:right;">{lives_display}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # السؤال
    st.markdown('<div class="question-box">', unsafe_allow_html=True)
    st.markdown(f'<div class="question-text">{st.session_state.question_text}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # عرض الرسالة
    if st.session_state.show_result and hasattr(st.session_state, 'message'):
        if "✅" in st.session_state.message:
            st.markdown(f'<div class="message-box success">{st.session_state.message}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message-box error">{st.session_state.message}</div>', unsafe_allow_html=True)
    
    # الخيارات المتساقطة
    if st.session_state.options and not st.session_state.game_over and not st.session_state.waiting_for_next:
        st.markdown('<div class="falling-container">', unsafe_allow_html=True)
        
        # عرض الخيارات في مواقعها المتساقطة
        for i, option in enumerate(st.session_state.options):
            if i < len(st.session_state.falling_positions):
                y_pos = st.session_state.falling_positions[i]
                color = st.session_state.option_colors[i] if i < len(st.session_state.option_colors) else "#ffcc00"
                
                # إذا كان الخيار قد نزل إلى الأسفل ولم يتم اختياره بعد
                if y_pos >= 550:
                    continue
                
                # عرض الخيار
                option_html = f'''
                <div class="falling-option" 
                     style="top: {y_pos}px; 
                            border-color: {color};
                            color: {color};"
                     onclick="alert('اخترت: {option}')">
                    {option}
                </div>
                '''
                st.markdown(option_html, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # أزرار اختيار الموضع (يسار، وسط، يمين)
        st.markdown('<div class="controls">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("◄ يسار", use_container_width=True):
                st.session_state.player_position = 0
                # التحقق من الخيار في الموضع الأيسر
                if len(st.session_state.options) > 0 and st.session_state.falling_positions[0] >= 450:
                    check_answer(0)
                    st.rerun()
        with col2:
            if st.button("■ وسط", use_container_width=True):
                st.session_state.player_position = 1
                if len(st.session_state.options) > 1 and st.session_state.falling_positions[1] >= 450:
                    check_answer(1)
                    st.rerun()
        with col3:
            if st.button("► يمين", use_container_width=True):
                st.session_state.player_position = 2
                if len(st.session_state.options) > 2 and st.session_state.falling_positions[2] >= 450:
                    check_answer(2)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # مؤشر اللاعب
        st.markdown(f'''
        <div class="player-indicator">
            {["◄", "■", "►"][st.session_state.player_position]}
        </div>
        ''', unsafe_allow_html=True)
    
    # زر التالي
    if st.session_state.waiting_for_next and not st.session_state.game_over:
        if st.button("➡️ السؤال التالي", use_container_width=True):
            start_round()
            st.rerun()
    
    # شاشة Game Over
    if st.session_state.game_over:
        st.markdown('<div class="game-over-box">', unsafe_allow_html=True)
        st.markdown('<div class="game-over-title">💀 انتهت اللعبة</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:white;font-size:28px;margin:15px 0;">النقاط: {st.session_state.score}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#00ffcc;font-size:22px;margin:15px 0;">🏆 أفضل: {get_high_score()}</div>', unsafe_allow_html=True)
        
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
    if not st.session_state.game_over and not st.session_state.waiting_for_next:
        if st.button("📚 القاموس", use_container_width=True):
            go_to_dict()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # تحديث تلقائي للحصول على حركة سقوط الخيارات
    if st.session_state.game_loop and not st.session_state.waiting_for_next and not st.session_state.game_over:
        time.sleep(0.1)
        st.rerun()

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

# بدء الجولة الأولى
if st.session_state.page == 'game' and not st.session_state.round_started and not st.session_state.game_over:
    start_round()
    st.rerun()
