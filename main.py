import flet as ft
import sqlite3
from datetime import date


# ================= 1. 数据库模块 (为朋友专属定制) =================
def init_db():
    conn = sqlite3.connect('bestie_discipline.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS records
                   (
                       date
                       TEXT
                       PRIMARY
                       KEY,
                       study_hours
                       REAL,
                       research_hours
                       REAL,
                       exercise_done
                       INTEGER,
                       water_drank
                       INTEGER,
                       friends_contacted
                       INTEGER,
                       expense_amount
                       REAL,
                       sleep_early
                       INTEGER,
                       good_deed
                       INTEGER,
                       reading
                       INTEGER,
                       finance_study
                       INTEGER,
                       daily_score
                       INTEGER
                   )
                   ''')
    conn.commit()
    return conn


db_conn = init_db()


# ================= 2. 界面与交互模块 =================
def main(page: ft.Page):
    # 你可以帮她把名字改成她喜欢的
    page.title = "玉米成长快乐"
    page.window_width = 450
    page.window_height = 850
    page.theme_mode = ft.ThemeMode.LIGHT

    # ================= [页面 1] 打卡界面的所有控件 =================
    checkin_title = ft.Text("🌽 玉米成长快乐 - 今日打卡", size=28, weight="bold")

    def create_time_counter(label_text, step=0.5):
        txt_number = ft.TextField(value="0", text_align="center", width=80, keyboard_type="number")

        def minus_click(e):
            val = float(txt_number.value)
            if val >= step:
                txt_number.value = str(round(val - step, 1))
                txt_number.update()

        def plus_click(e):
            val = float(txt_number.value)
            txt_number.value = str(round(val + step, 1))
            txt_number.update()

        row = ft.Row([
            ft.Text(label_text, width=120, weight="bold"),
            ft.FilledTonalButton(content=" - ", on_click=minus_click),
            txt_number,
            ft.FilledTonalButton(content=" + ", on_click=plus_click)
        ], alignment=ft.MainAxisAlignment.START)
        return row, txt_number

    # 1. 时长类
    study_row, study_input = create_time_counter("学习时间 (h):", step=0.5)
    research_row, research_input = create_time_counter("科研时间 (h):", step=0.5)

    # 2. 数字输入类
    friends_input = ft.TextField(label="今日联络好友个数 (+10分/人)", value="0", width=300, keyboard_type="number")
    expense_input = ft.TextField(label="今日花销总额 (元) [仅记录]", value="0", width=300, keyboard_type="number")

    # 3. 纯加分项
    exercise_check = ft.Checkbox(label="今日是否运动 (+10)", value=False)
    water_check = ft.Checkbox(label="今早有无喝水 (+10)", value=False)

    # 4. 奖惩双向项 (+10 / -10)
    sleep_check = ft.Checkbox(label="早睡早起 (+10 / -10)", value=False)
    good_deed_check = ft.Checkbox(label="做一件好事 (+10 / -10)", value=False)
    reading_check = ft.Checkbox(label="读书 (+10 / -10)", value=False)
    finance_check = ft.Checkbox(label="学习理财知识 (+10 / -10)", value=False)

    result_text = ft.Text(size=20, weight="bold", color="blue")

    def submit_data(e):
        try:
            record_date = str(date.today())

            # 获取数据
            study = float(study_input.value)
            research = float(research_input.value)
            friends = int(friends_input.value)
            expense_amt = float(expense_input.value)

            exercise = 1 if exercise_check.value else 0
            water = 1 if water_check.value else 0

            sleep = sleep_check.value
            good_deed = good_deed_check.value
            reading = reading_check.value
            finance = finance_check.value

            # 朋友专属计分算法
            score = 0
            score += int(study * 10) + int(research * 10)
            score += friends * 10
            score += exercise * 10 + water * 10

            score += 10 if sleep else -10
            score += 10 if good_deed else -10
            score += 10 if reading else -10
            score += 10 if finance else -10

            # 花销不再影响分数

            # 存入数据库
            cursor = db_conn.cursor()
            cursor.execute('''
                           INSERT INTO records
                           (date, study_hours, research_hours, exercise_done, water_drank, friends_contacted,
                            expense_amount, sleep_early, good_deed, reading, finance_study, daily_score)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(date) DO
                           UPDATE SET
                               study_hours=excluded.study_hours, research_hours=excluded.research_hours,
                               exercise_done=excluded.exercise_done, water_drank=excluded.water_drank,
                               friends_contacted=excluded.friends_contacted, expense_amount=excluded.expense_amount,
                               sleep_early=excluded.sleep_early, good_deed=excluded.good_deed,
                               reading=excluded.reading, finance_study=excluded.finance_study,
                               daily_score=excluded.daily_score
                           ''', (record_date, study, research, exercise, water, friends, expense_amt,
                                 int(sleep), int(good_deed), int(reading), int(finance), score))
            db_conn.commit()

            result_text.value = f"打卡成功！今日花销 {expense_amt}元\n单日得分：{score} 分"
            result_text.color = "blue"
            page.update()

        except ValueError:
            result_text.value = "请检查数字格式是否正确！"
            result_text.color = "red"
            page.update()

    submit_btn = ft.FilledButton(content="提交打卡数据", on_click=submit_data, width=300)

    # ================= [页面 2] 核心：动态读取数据库生成统计与奖励 =================
    def load_stats_ui():
        try:
            cursor = db_conn.cursor()
            cursor.execute("SELECT * FROM records ORDER BY date DESC LIMIT 7")
            rows = cursor.fetchall()

            if not rows:
                return [ft.Text("暂无打卡数据，快去首页打卡吧！", color="grey", size=16)]

            def safe_get(row, index):
                if index < len(row) and row[index] is not None:
                    return row[index]
                return 0

            # 对应数据库中的列索引
            total_score = sum(safe_get(row, 11) for row in rows)
            total_study = sum(safe_get(row, 1) for row in rows)
            total_research = sum(safe_get(row, 2) for row in rows)
            total_exercise = sum(safe_get(row, 3) for row in rows)
            total_friends = sum(safe_get(row, 5) for row in rows)
            total_expense = sum(safe_get(row, 6) for row in rows)

            reward_title = ""
            reward_desc = ""
            reward_color = "black"

            if total_score >= 1200:
                reward_title = "👑 满级大佬"
                reward_desc = "当前解锁：新体验！你这周简直是神！"
                reward_color = "#d97706"
            elif total_score >= 1000:
                reward_title = "🍗 黄金段位"
                reward_desc = f"当前解锁：自由创作！ (距【新体验】还差 {1200 - total_score} 分)"
                reward_color = "#b91c1c"
            elif total_score >= 800:
                reward_title = "🍜 白银段位"
                reward_desc = f"当前解锁：不同风格衣服！ (距【自由创作】还差 {1000 - total_score} 分)"
                reward_color = "#0369a1"
            elif total_score >= 600:
                reward_title = "🥤 青铜段位"
                reward_desc = f"当前解锁：搞笑玩具！ (距【不同风格衣服】还差 {800 - total_score} 分)"
                reward_color = "#15803d"
            else:
                reward_title = "🌱 新手村"
                reward_desc = f"暂无奖励 (距最低奖励【搞笑玩具】还差 {600 - total_score} 分，冲鸭！)"
                reward_color = "#4b5563"

            content = [
                ft.Text("📈 近7天元气战报", size=28, weight="bold"),

                ft.Container(
                    content=ft.Column([
                        ft.Text("🎁 本周战利品", size=18, weight="bold", color="white"),
                        ft.Text(reward_title, size=24, weight="bold", color="white"),
                        ft.Text(reward_desc, size=14, color="white"),
                    ]),
                    padding=15,
                    bgcolor=reward_color,
                    border_radius=10,
                    width=400
                ),
                ft.Divider(height=10, color="transparent"),

                ft.Container(
                    content=ft.Column([
                        ft.Text(f"🏆 累计得分: {total_score} 分", size=22, weight="bold", color="green"),
                        ft.Divider(color="white"),
                        ft.Text(f"📚 沉浸学习: {total_study} 小时", size=16),
                        ft.Text(f"🔬 潜心科研: {total_research} 小时", size=16),
                        ft.Text(f"🏃 运动天数: {total_exercise} 天", size=16),
                        ft.Text(f"💬 联络好友: {total_friends} 人", size=16),
                        ft.Text(f"💰 累计花销: {total_expense} 元", size=16),
                    ]),
                    padding=20,
                    bgcolor="#fce7f3",  # 为朋友换了一个淡粉色/柔和的统计面板背景
                    border_radius=15,
                    width=400
                ),
                ft.Divider(),
                ft.Text("📅 历史打卡明细:", weight="bold", size=18)
            ]

            for row in sorted(rows, key=lambda x: x[0]):
                date_str = row[0] if len(row) > 0 else "未知日期"
                score = safe_get(row, 11)
                expense = safe_get(row, 6)
                content.append(ft.Text(f"{date_str} | 得分: {score} | 花销: {expense}元", size=15))

            return content

        except Exception as e:
            return [
                ft.Text("⚠️ 数据读取出错！", color="red", size=20, weight="bold"),
                ft.Text(f"错误信息: {str(e)}", color="red")
            ]

    # ================= 3. 终极防白屏页面架构 (使用可见性切换) =================
    checkin_container = ft.Column(
        controls=[
            checkin_title,
            ft.Divider(),
            study_row, research_row, ft.Divider(),
            friends_input, expense_input, ft.Divider(),
            ft.Row([exercise_check, water_check]), ft.Divider(),
            sleep_check, good_deed_check, reading_check, finance_check, ft.Divider(),
            submit_btn, result_text
        ],
        scroll="adaptive",
        expand=True,
        visible=True
    )

    stats_container = ft.Column(
        controls=[],
        scroll="adaptive",
        expand=True,
        visible=False
    )

    def switch_tab(e, index):
        if index == 0:
            checkin_container.visible = True
            stats_container.visible = False
        else:
            stats_container.controls = load_stats_ui()
            checkin_container.visible = False
            stats_container.visible = True
        page.update()

    main_content = ft.Column(
        controls=[checkin_container, stats_container],
        expand=True
    )

    bottom_bar = ft.Container(
        content=ft.Row(
            controls=[
                ft.FilledTonalButton("📝 今日打卡", on_click=lambda e: switch_tab(e, 0), expand=True, height=50),
                ft.FilledTonalButton("📊 数据统计", on_click=lambda e: switch_tab(e, 1), expand=True, height=50),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY
        ),
        padding=10,
        bgcolor="#f3f4f6",
        border_radius=10
    )

    page.add(main_content, bottom_bar)


ft.app(target=main)