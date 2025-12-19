import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import csv
import os
from datetime import datetime

class MISTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Montreal Image Stress Test (MIST)")
        self.root.geometry("900x700")
        self.root.configure(bg="white")
        
        # --- 配置参数 ---
        self.TOTAL_ROUNDS = 4
        self.QUESTIONS_PER_ROUND = 10  # 每轮题目数量 (调整为10以匹配单词量)
        self.TIME_LIMIT = 8.0          # 初始默认值，后续会根据练习轮调整
        self.INTERMISSION_TIME = 5     # 轮间休息倒计时(秒)
        
        # --- 单词记忆配置 ---
        self.WORD_DISPLAY_TIME = 2000 # 毫秒
        
        # 单词库 (中文, 英文) - 总共需要 4轮 * 10个 = 40个目标词，以及 40个干扰词
        self.all_targets = [
            ("苹果", "Apple"), ("香蕉", "Banana"), ("橙子", "Orange"), ("葡萄", "Grape"), ("西瓜", "Watermelon"),
            ("桌子", "Table"), ("椅子", "Chair"), ("沙发", "Sofa"), ("床", "Bed"), ("柜子", "Cabinet"),
            ("汽车", "Car"), ("火车", "Train"), ("飞机", "Plane"), ("轮船", "Ship"), ("自行车", "Bike"),
            ("猫", "Cat"), ("狗", "Dog"), ("鸟", "Bird"), ("鱼", "Fish"), ("马", "Horse"),
            ("书", "Book"), ("笔", "Pen"), ("纸", "Paper"), ("尺子", "Ruler"), ("橡皮", "Eraser"),
            ("手", "Hand"), ("脚", "Foot"), ("头", "Head"), ("眼睛", "Eye"), ("耳朵", "Ear"),
            ("门", "Door"), ("窗户", "Window"), ("墙", "Wall"), ("地板", "Floor"), ("天花板", "Ceiling"),
            ("灯", "Lamp"), ("钟", "Clock"), ("镜子", "Mirror"), ("照片", "Photo"), ("画", "Painting")
        ]
        
        self.all_distractors = [
            ("手机", "Phone"), ("电脑", "Computer"), ("电视", "TV"), ("冰箱", "Fridge"), ("空调", "AC"),
            ("老虎", "Tiger"), ("狮子", "Lion"), ("大象", "Elephant"), ("熊猫", "Panda"), ("猴子", "Monkey"),
            ("红色", "Red"), ("蓝色", "Blue"), ("绿色", "Green"), ("黄色", "Yellow"), ("白色", "White"),
            ("太阳", "Sun"), ("月亮", "Moon"), ("星星", "Star"), ("云", "Cloud"), ("雨", "Rain"),
            ("衬衫", "Shirt"), ("裤子", "Pants"), ("鞋子", "Shoes"), ("帽子", "Hat"), ("袜子", "Socks"),
            ("面包", "Bread"), ("牛奶", "Milk"), ("鸡蛋", "Egg"), ("米饭", "Rice"), ("面条", "Noodles"),
            ("咖啡", "Coffee"), ("茶", "Tea"), ("果汁", "Juice"), ("水", "Water"), ("酒", "Wine"),
            ("牛肉", "Beef"), ("猪肉", "Pork"), ("鸡肉", "Chicken"), ("鸭肉", "Duck"), ("羊肉", "Lamb")
        ]
        
        self.current_round_targets = []
        self.current_round_distractors = []
        self.recall_stats = [] # 存储每轮的回忆成绩
        
        # --- 状态变量 ---
        self.subject_id = ""
        self.current_round = 0
        self.current_question_index = 0
        self.score = 0
        self.round_data = [] # 暂存当前轮次数据
        self.all_results = [] # 所有结果
        self.round_start_times = {} # 记录每轮开始时间
        self.round_end_times = {}   # 记录每轮结束时间
        
        self.current_question_data = None
        self.timer_running = False
        self.remaining_time = 0
        self.start_time_question = 0
        self.base_time_limit = self.TIME_LIMIT
        self.target_accuracy = 0.5
        self.difficulty_level = 1.0
        self.min_difficulty = 0.6
        self.max_difficulty = 2.0
        self.adaptation_rate = 0.5
        self.performance_window = 12
        self.recent_results = []
        
        # --- 样式 ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", font=("Helvetica", 20), padding=15)
        self.style.configure("TLabel", font=("Helvetica", 18), background="white")
        self.style.configure("Header.TLabel", font=("Helvetica", 32, "bold"), background="white")
        self.style.configure("Timer.Horizontal.TProgressbar", background="#4caf50")
        
        # 绑定键盘事件
        self.root.bind('<Key>', self.handle_keypress)
        
        # 初始化界面容器
        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.show_login_screen()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def handle_keypress(self, event):
        # 仅在测试进行中处理 1-5 的按键
        if hasattr(self, 'state') and self.state == 'testing':
            if event.char in ['1', '2', '3', '4', '5']:
                index = int(event.char) - 1
                self.submit_answer(index)

    # --- 1. 登录界面 ---
    def show_login_screen(self):
        self.state = 'login'
        self.clear_frame()
        
        tk.Label(self.main_frame, text="Montreal Image Stress Test", font=("Helvetica", 40, "bold"), bg="white").pack(pady=60)
        
        input_frame = tk.Frame(self.main_frame, bg="white")
        input_frame.pack(pady=30)
        
        tk.Label(input_frame, text="请输入被试 ID:", font=("Helvetica", 24), bg="white").pack(side="left", padx=15)
        self.id_entry = tk.Entry(input_frame, font=("Helvetica", 24))
        self.id_entry.pack(side="left", padx=15)
        self.id_entry.focus()
        
        start_btn = ttk.Button(self.main_frame, text="开始测试", command=self.start_test)
        start_btn.pack(pady=30)
        
        # 绑定回车键开始
        self.root.bind('<Return>', lambda e: self.start_test())

    def start_test(self):
        subject_id = self.id_entry.get().strip()
        if not subject_id:
            messagebox.showwarning("提示", "请输入被试 ID")
            return
        
        self.subject_id = subject_id
        self.root.unbind('<Return>') # 解绑回车
        self.current_round = 0 # 0 表示练习轮
        self.show_intermission_screen(first_start=True)

    # --- 2. 间隔/说明界面 ---
    def show_intermission_screen(self, first_start=False):
        self.state = 'intermission'
        self.clear_frame()
        
        if self.current_round == 0:
            title_text = "练习轮 (测定基准反应时间)"
            info_text = (
                f"首先进行练习轮，共 5 道算术题。\n"
                f"请以最快速度准确作答。\n"
                f"本轮无时间限制，但会计时。\n"
                f"本轮不包含单词记忆任务。"
            )
        else:
            title_text = f"准备开始第 {self.current_round} 轮"
            info_text = (
                f"本轮共有 {self.QUESTIONS_PER_ROUND} 道算术题。\n"
                f"请尽可能快且准确地回答。\n"
                f"使用鼠标点击选项，或按键盘数字键 1-5 选择。\n"
                f"每题有时间限制！"
            )
            
        tk.Label(self.main_frame, text=title_text, font=("Helvetica", 36, "bold"), bg="white").pack(pady=60)
        tk.Label(self.main_frame, text=info_text, font=("Helvetica", 24), bg="white", justify="center").pack(pady=30)
        
        # 手动开始提示
        tk.Label(self.main_frame, text="请点击下方按钮开始本轮测试", font=("Helvetica", 20), fg="gray", bg="white").pack(pady=40)
        
        btn = ttk.Button(self.main_frame, text="开始本轮", command=self.start_round)
        btn.pack()

    # --- 3. 测试进行中界面 ---
    def start_round(self):
        self.state = 'testing'
        self.current_question_index = 0
        self.round_start_times[self.current_round] = time.time()
        
        # 准备本轮单词
        if self.current_round == 0:
            # 练习轮，无单词
            self.current_round_targets = []
            self.current_round_distractors = []
            self.questions_this_round = 5
        else:
            self.questions_this_round = self.QUESTIONS_PER_ROUND
            start_idx = (self.current_round - 1) * self.QUESTIONS_PER_ROUND
            end_idx = start_idx + self.QUESTIONS_PER_ROUND
            
            # 确保索引不越界
            if end_idx <= len(self.all_targets):
                self.current_round_targets = self.all_targets[start_idx:end_idx]
                self.current_round_distractors = self.all_distractors[start_idx:end_idx]
            else:
                # 备用方案：随机取
                self.current_round_targets = random.sample(self.all_targets, self.QUESTIONS_PER_ROUND)
                self.current_round_distractors = random.sample(self.all_distractors, self.QUESTIONS_PER_ROUND)
            
        self.next_trial_step()

    def next_trial_step(self):
        # 检查是否完成本轮所有题目
        if self.current_question_index >= self.questions_this_round:
            self.end_round_phase()
            return
            
        # 步骤 1: 显示算术题
        self.current_question_index += 1
        self.current_question_data = self.generate_question()
        self.start_time_question = time.time()
        
        self.setup_question_ui()
        self.start_timer()

    def generate_question(self):
        # 生成简单到中等的算术题 (A op B op C)
        ops = ['+', '-', '*']
        # 限制乘法以保持难度适中
        
        while True:
            # 模式 1: A + B - C
            # 模式 2: A * B - C (A, B 较小)
            mode = random.choice([1, 2])
            level = self.difficulty_level
            if mode == 1:
                a_high = max(25, int(35 + 40 * level))
                b_high = max(15, int(20 + 30 * level))
                c_high = max(15, int(20 + 30 * level))
                a = random.randint(12, a_high)
                b = random.randint(8, b_high)
                c = random.randint(8, c_high)
                op1, op2 = random.choice([('+', '-'), ('-', '+'), ('+', '+'), ('-', '-')])
                expression = f"{a} {op1} {b} {op2} {c}"
            else:
                mul_high = max(3, int(4 + 6 * level))
                third_high = max(10, int(15 + 30 * level))
                a = random.randint(2, mul_high)
                b = random.randint(2, mul_high)
                c = random.randint(5, third_high)
                op1 = '*'
                op2 = random.choice(['+', '-'])
                expression = f"{a} {op1} {b} {op2} {c}"
            
            try:
                ans = eval(expression)
                # 确保答案是正整数且不太大
                if 0 <= ans <= 100:
                    break
            except:
                continue
                
        # 生成选项
        options = {ans}
        offset_span = max(3, int(10 - 3 * (self.difficulty_level - 1)))
        while len(options) < 5:
            # 生成干扰项：接近正确答案的数字
            offset = random.randint(-offset_span, offset_span)
            if offset == 0: continue
            fake = ans + offset
            if 0 <= fake <= 100:
                options.add(fake)
        
        options_list = list(options)
        random.shuffle(options_list)
        
        return {
            "expression": expression,
            "answer": ans,
            "options": options_list
        }

    def setup_question_ui(self):
        self.clear_frame()
        
        # 顶部信息
        top_frame = tk.Frame(self.main_frame, bg="white")
        top_frame.pack(fill="x", pady=15)
        
        if self.current_round == 0:
            round_text = "练习轮"
            total_q = self.questions_this_round
        else:
            round_text = f"第 {self.current_round} / {self.TOTAL_ROUNDS} 轮"
            total_q = self.QUESTIONS_PER_ROUND
            
        tk.Label(top_frame, text=round_text, font=("Helvetica", 20), bg="white").pack(side="left")
        tk.Label(top_frame, text=f"题目: {self.current_question_index} / {total_q}", font=("Helvetica", 20), bg="white").pack(side="right")
        
        # 算术题显示
        tk.Label(self.main_frame, text=self.current_question_data["expression"] + " = ?", font=("Helvetica", 72, "bold"), bg="white").pack(pady=50)
        
        # 选项按钮区域
        options_frame = tk.Frame(self.main_frame, bg="white")
        options_frame.pack(pady=30)
        
        self.option_buttons = []
        for i, option in enumerate(self.current_question_data["options"]):
            # 键盘提示 (1-5)
            btn_text = f"{option}\n[{i+1}]"
            btn = tk.Button(options_frame, text=btn_text, font=("Helvetica", 24), width=8, height=2,
                            command=lambda idx=i: self.submit_answer(idx), bg="white", relief="raised")
            btn.grid(row=0, column=i, padx=15)
            self.option_buttons.append(btn)
            
        # 进度条 (压力指示器)
        self.progress_var = tk.DoubleVar()
        self.progress_var.set(100)
        
        # 自定义进度条颜色
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100, style="Timer.Horizontal.TProgressbar", length=800)
        self.progress_bar.pack(pady=40)
        
        self.feedback_label = tk.Label(self.main_frame, text="", font=("Helvetica", 24), bg="white")
        self.feedback_label.pack(pady=10)

    def start_timer(self):
        self.timer_running = True
        # 如果是练习轮，给一个很长的时间，实际上不限制
        if self.current_round == 0:
            self.current_time_limit = 60.0
        else:
            self.current_time_limit = self.TIME_LIMIT
            
        self.remaining_time = self.current_time_limit
        self.update_timer()

    def update_timer(self):
        if not self.timer_running:
            return
            
        self.remaining_time -= 0.05 # 50ms 更新一次
        percentage = (self.remaining_time / self.current_time_limit) * 100
        self.progress_var.set(percentage)
        
        # 颜色变化增加压力
        if percentage < 30:
            self.style.configure("Timer.Horizontal.TProgressbar", background="#e74c3c") # 红色
        elif percentage < 60:
            self.style.configure("Timer.Horizontal.TProgressbar", background="#f39c12") # 橙色
        else:
            self.style.configure("Timer.Horizontal.TProgressbar", background="#4caf50") # 绿色
            
        if self.remaining_time <= 0:
            self.handle_timeout()
        else:
            self.root.after(50, self.update_timer)

    def handle_timeout(self):
        self.timer_running = False
        self.record_result(None, False, self.current_time_limit, timeout=True)
        self.show_feedback(False, timeout=True)

    def submit_answer(self, index):
        if not self.timer_running: return # 防止重复提交
        
        self.timer_running = False
        elapsed_time = time.time() - self.start_time_question
        
        selected_value = self.current_question_data["options"][index]
        correct_value = self.current_question_data["answer"]
        is_correct = (selected_value == correct_value)
        
        self.record_result(selected_value, is_correct, elapsed_time)
        self.show_feedback(is_correct)

    def record_result(self, user_ans, is_correct, time_taken, timeout=False):
        result = {
            "SubjectID": self.subject_id,
            "Round": self.current_round,
            "QuestionIndex": self.current_question_index,
            "Expression": self.current_question_data["expression"],
            "CorrectAnswer": self.current_question_data["answer"],
            "UserAnswer": user_ans if user_ans is not None else "TIMEOUT",
            "IsCorrect": is_correct,
            "TimeTaken": round(time_taken, 3),
            "Timeout": timeout,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.all_results.append(result)
        if self.current_round > 0:
            outcome = 1 if (is_correct and not timeout) else 0
            self.recent_results.append(outcome)
            if len(self.recent_results) > self.performance_window:
                self.recent_results.pop(0)
            self.adjust_difficulty()

    def adjust_difficulty(self):
        if not self.recent_results or self.base_time_limit is None:
            return
        accuracy = sum(self.recent_results) / len(self.recent_results)
        error = accuracy - self.target_accuracy
        self.difficulty_level += error * self.adaptation_rate
        self.difficulty_level = max(self.min_difficulty, min(self.difficulty_level, self.max_difficulty))
        scaled_time = self.base_time_limit / self.difficulty_level
        self.TIME_LIMIT = max(1.5, min(scaled_time, 12.0))

    def show_feedback(self, is_correct, timeout=False):
        if timeout:
            msg = "超时!"
            color = "#e74c3c"
        elif is_correct:
            msg = "正确"
            color = "#2ecc71"
        else:
            msg = "错误"
            color = "#e74c3c"
            
        self.feedback_label.config(text=msg, fg=color, font=("Helvetica", 32, "bold"))
        
        # 禁用按钮
        for btn in self.option_buttons:
            btn.config(state="disabled")
            
        # 延迟后进入单词展示或下一题
        if self.current_round == 0:
            self.root.after(800, self.next_trial_step)
        else:
            self.root.after(800, self.show_word_display)

    def show_word_display(self):
        self.state = 'word_display'
        self.clear_frame()
        
        # 获取当前题目对应的单词 (index 已经是 1-based，所以要 -1)
        word_idx = self.current_question_index - 1
        if word_idx < len(self.current_round_targets):
            zh_word, en_word = self.current_round_targets[word_idx]
        else:
            zh_word, en_word = "无", "None"
            
        tk.Label(self.main_frame, text="请记忆", font=("Helvetica", 24), fg="gray", bg="white").pack(pady=40)
        
        tk.Label(self.main_frame, text=zh_word, font=("Helvetica", 80, "bold"), fg="#2980b9", bg="white").pack(pady=20)
        tk.Label(self.main_frame, text=en_word, font=("Helvetica", 40), fg="#34495e", bg="white").pack(pady=10)
        
        # 自动进入下一题
        self.root.after(self.WORD_DISPLAY_TIME, self.next_trial_step)

    def end_round_phase(self):
        self.round_end_times[self.current_round] = time.time()
        
        if self.current_round == 0:
            # 计算平均反应时间
            practice_results = [r for r in self.all_results if r['Round'] == 0]
            if practice_results:
                total_time = sum(r['TimeTaken'] for r in practice_results)
                avg_time = total_time / len(practice_results)
                # 设置正式测试的时间限制为平均反应时间的 1.2 倍 (加快节奏)
                self.TIME_LIMIT = avg_time * 1.2
                # 确保时间限制在合理范围内 (例如不低于 2秒，不高于 10秒)
                self.TIME_LIMIT = max(2.0, min(self.TIME_LIMIT, 10.0))
            else:
                self.TIME_LIMIT = 6.0 # 默认值加快
            self.base_time_limit = self.TIME_LIMIT
                
            # 进入第一轮
            self.current_round = 1
            self.show_intermission_screen()
        else:
            self.show_recall_screen()

    # --- 4. 单词回忆界面 ---
    def show_recall_screen(self):
        self.state = 'recall'
        self.clear_frame()
        
        tk.Label(self.main_frame, text=f"第 {self.current_round} 轮 - 单词回忆", font=("Helvetica", 40, "bold"), bg="white").pack(pady=20)
        tk.Label(self.main_frame, text="请勾选刚才出现过的所有单词", font=("Helvetica", 24), bg="white").pack(pady=10)
        
        # 混合选项: 本轮目标 + 本轮干扰
        # 提取中文用于显示
        targets_zh = [w[0] for w in self.current_round_targets]
        distractors_zh = [w[0] for w in self.current_round_distractors]
        
        all_options = targets_zh + distractors_zh
        random.shuffle(all_options)
        
        self.recall_vars = {}
        
        # 创建一个 Frame 来放选项，使用 grid 布局
        options_frame = tk.Frame(self.main_frame, bg="white")
        options_frame.pack(pady=20, expand=True)
        
        cols = 5
        for i, word in enumerate(all_options):
            var = tk.BooleanVar()
            self.recall_vars[word] = var
            cb = tk.Checkbutton(options_frame, text=word, variable=var, font=("Helvetica", 18), bg="white")
            cb.grid(row=i//cols, column=i%cols, padx=20, pady=10, sticky="w")
            
        submit_btn = ttk.Button(self.main_frame, text="提交本轮回忆", command=self.submit_recall)
        submit_btn.pack(pady=20)

    def submit_recall(self):
        # 计算回忆成绩
        correct_selections = 0
        false_alarms = 0
        misses = 0
        
        selected_words = [w for w, v in self.recall_vars.items() if v.get()]
        targets_zh = [w[0] for w in self.current_round_targets]
        
        for word in targets_zh:
            if word in selected_words:
                correct_selections += 1
            else:
                misses += 1
                
        for word in selected_words:
            if word not in targets_zh:
                false_alarms += 1
                
        stats = {
            "round": self.current_round,
            "total_targets": len(targets_zh),
            "correct_selections": correct_selections,
            "false_alarms": false_alarms,
            "misses": misses,
            "accuracy": (correct_selections / len(targets_zh) * 100) if targets_zh else 0
        }
        self.recall_stats.append(stats)
        
        self.save_recall_results()
        
        # 决定下一步
        if self.current_round < self.TOTAL_ROUNDS:
            self.current_round += 1
            self.show_intermission_screen()
        else:
            self.show_results_screen()

    def save_recall_results(self):
        if not os.path.exists('results'):
            os.makedirs('results')
            
        filename = f"results/mist_recall_{self.subject_id}_{int(time.time())}.csv"
        
        # 如果是第一轮，写入表头；否则追加
        # 这里简化处理，每次都写全量或者追加。为了简单，每次追加一行记录
        # 但为了分析方便，我们记录详细的每个词的选择情况
        
        # 实际上，我们可以只记录汇总，或者记录详细。
        # 这里记录详细：Round, Word, IsTarget, Selected, IsCorrect
        
        mode = 'a' if os.path.exists(filename) else 'w'
        with open(filename, mode, newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if mode == 'w':
                writer.writerow(["SubjectID", "Round", "Word", "IsTarget", "Selected", "IsCorrectSelection"])
            
            targets_zh = [w[0] for w in self.current_round_targets]
            
            for word, var in self.recall_vars.items():
                is_target = word in targets_zh
                selected = var.get()
                is_correct_sel = (is_target == selected)
                writer.writerow([self.subject_id, self.current_round, word, is_target, selected, is_correct_sel])

    # --- 5. 结果统计界面 ---
    def show_results_screen(self):
        self.state = 'results'
        self.clear_frame()
        self.save_results_to_csv()
        self.save_summary_csv()
        
        tk.Label(self.main_frame, text="测试完成", font=("Helvetica", 40, "bold"), bg="white").pack(pady=40)
        
        # 统计数据
        stats_frame = tk.Frame(self.main_frame, bg="white", padx=30, pady=30, relief="groove", bd=2)
        stats_frame.pack(fill="both", expand=True, padx=60, pady=30)
        
        tk.Label(stats_frame, text="结果统计", font=("Helvetica", 28, "bold"), bg="white").pack(pady=15)
        
        total_correct = sum(1 for r in self.all_results if r['IsCorrect'])
        total_questions = len(self.all_results)
        accuracy = (total_correct / total_questions) * 100 if total_questions > 0 else 0
        
        tk.Label(stats_frame, text=f"总正确率: {accuracy:.1f}%", font=("Helvetica", 22), bg="white").pack(anchor="w", pady=10)
        tk.Label(stats_frame, text=f"设定时间限制: {self.TIME_LIMIT:.2f} 秒", font=("Helvetica", 22), bg="white").pack(anchor="w", pady=10)
        
        # 单词记忆成绩
        if self.recall_stats:
            tk.Label(stats_frame, text="单词记忆成绩 (平均):", font=("Helvetica", 22, "bold"), bg="white").pack(anchor="w", pady=15)
            
            total_correct = sum(s['correct_selections'] for s in self.recall_stats)
            total_targets = sum(s['total_targets'] for s in self.recall_stats)
            total_false = sum(s['false_alarms'] for s in self.recall_stats)
            
            tk.Label(stats_frame, text=f"总正确识别: {total_correct} / {total_targets}", font=("Helvetica", 20), bg="white").pack(anchor="w")
            tk.Label(stats_frame, text=f"总误报: {total_false}", font=("Helvetica", 20), bg="white").pack(anchor="w")

        tk.Label(stats_frame, text="各轮次详情:", font=("Helvetica", 22, "bold"), bg="white").pack(anchor="w", pady=15)
        
        for r in range(1, self.TOTAL_ROUNDS + 1):
            round_res = [x for x in self.all_results if x['Round'] == r]
            r_correct = sum(1 for x in round_res if x['IsCorrect'])
            r_total = len(round_res)
            r_acc = (r_correct / r_total * 100) if r_total > 0 else 0
            
            start_t = self.round_start_times.get(r, 0)
            end_t = self.round_end_times.get(r, 0)
            duration = end_t - start_t
            
            text = f"第 {r} 轮: 正确率 {r_acc:.1f}% | 完成用时: {duration:.1f} 秒"
            tk.Label(stats_frame, text=text, font=("Helvetica", 20), bg="white").pack(anchor="w")

        tk.Label(self.main_frame, text=f"结果已保存至 results/mist_results_{self.subject_id}.csv", font=("Helvetica", 16), fg="gray", bg="white").pack(pady=10)
        tk.Label(self.main_frame, text=f"汇总已保存至 results/mist_summary_{self.subject_id}.csv", font=("Helvetica", 16), fg="gray", bg="white").pack(pady=10)
        
        ttk.Button(self.main_frame, text="退出", command=self.root.quit).pack(pady=10)

    def save_results_to_csv(self):
        if not os.path.exists('results'):
            os.makedirs('results')
            
        filename = f"results/mist_results_{self.subject_id}_{int(time.time())}.csv"
        
        fieldnames = ["SubjectID", "Round", "QuestionIndex", "Expression", "CorrectAnswer", "UserAnswer", "IsCorrect", "TimeTaken", "Timeout", "Timestamp"]
        
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.all_results)

    def save_summary_csv(self):
        if not os.path.exists('results'):
            os.makedirs('results')
            
        filename = f"results/mist_summary_{self.subject_id}_{int(time.time())}.csv"
        
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Round", "Arithmetic_Correct", "Arithmetic_Total", "Arithmetic_Accuracy", "Avg_Response_Time", "Word_Correct", "Word_FalseAlarm", "Word_Total_Targets"])
            
            for r in range(1, self.TOTAL_ROUNDS + 1):
                # Arithmetic Stats
                round_res = [x for x in self.all_results if x['Round'] == r]
                r_correct = sum(1 for x in round_res if x['IsCorrect'])
                r_total = len(round_res)
                r_acc = (r_correct / r_total * 100) if r_total > 0 else 0
                avg_time = sum(x['TimeTaken'] for x in round_res) / r_total if r_total > 0 else 0
                
                # Word Recall Stats
                recall = next((s for s in self.recall_stats if s['round'] == r), None)
                if recall:
                    w_correct = recall['correct_selections']
                    w_false = recall['false_alarms']
                    w_total = recall['total_targets']
                else:
                    w_correct = 0
                    w_false = 0
                    w_total = 0
                
                writer.writerow([r, r_correct, r_total, f"{r_acc:.1f}%", f"{avg_time:.3f}", w_correct, w_false, w_total])

if __name__ == "__main__":
    root = tk.Tk()
    app = MISTApp(root)
    root.mainloop()
