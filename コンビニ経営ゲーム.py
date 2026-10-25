import tkinter as tk
from tkinter import messagebox, filedialog
import random
import json

PRODUCTS = {
    "おにぎり": {"cost": 80, "price": 150, "stock": 20},
    "お弁当": {"cost": 280, "price": 480, "stock": 12},
    "飲み物": {"cost": 70, "price": 140, "stock": 25},
    "お菓子": {"cost": 90, "price": 180, "stock": 18},
    "アイス": {"cost": 100, "price": 220, "stock": 12},
}

BUILDINGS = {
    "防犯カメラ": {"cost": 30000, "max": 5},
    "イートイン": {"cost": 50000, "max": 1},
    "駐車場": {"cost": 80000, "max": 1},
    "大型冷蔵庫": {"cost": 45000, "max": 1},
}

LICENSES = {
    "新聞販売": {"cost": 15000, "products": {
        "新聞": {"cost": 70, "price": 150, "stock": 10},
        "スポーツ新聞": {"cost": 90, "price": 160, "stock": 8},
    }},
    "化粧品販売": {"cost": 40000, "products": {
        "化粧水": {"cost": 500, "price": 900, "stock": 5},
        "乳液": {"cost": 550, "price": 980, "stock": 5},
        "リップクリーム": {"cost": 180, "price": 350, "stock": 8},
    }},
    "ホットスナック販売": {"cost": 50000, "products": {
        "からあげ": {"cost": 100, "price": 220, "stock": 10},
        "フランクフルト": {"cost": 90, "price": 200, "stock": 10},
    }},
}

DIFFICULTIES = {
    "イージー": {"money": 250000, "customer": 0.85, "trouble": 0.5},
    "ノーマル": {"money": 180000, "customer": 0.65, "trouble": 1.0},
    "ハード": {"money": 130000, "customer": 0.5, "trouble": 1.5},
}


class ConvenienceStore:
    def __init__(self, root):
        self.root = root
        self.root.title("コンビニ経営ゲーム")
        self.root.geometry("950x700")

        self.timers = []
        self.started = False
        self.difficulty = "ノーマル"
        self.day = 1
        self.money = 180000
        self.reputation = 50
        self.staff = 0
        self.customers = 0
        self.sales = 0
        self.expenses = 0
        self.products = {}
        self.buildings = {}
        self.licenses = []
        self.event_history = []
        self.show_title()

    def clear(self):
        for timer in self.timers:
            try:
                self.root.after_cancel(timer)
            except tk.TclError:
                pass
        self.timers.clear()
        for widget in self.root.winfo_children():
            widget.destroy()

    def later(self, ms, func):
        self.timers.append(self.root.after(ms, func))

    def show_title(self):
        self.started = False
        self.clear()
        frame = tk.Frame(self.root, padx=30, pady=30)
        frame.pack(expand=True)

        tk.Label(frame, text="コンビニ経営ゲーム",
                 font=("Yu Gothic UI", 25, "bold")).pack(pady=20)
        tk.Label(frame, text="商品を売って、お店を大きくしよう！",
                 font=("Yu Gothic UI", 12)).pack(pady=10)

        self.difficulty_var = tk.StringVar(value="ノーマル")
        tk.Label(frame, text="難易度を選択").pack(pady=5)

        for name in DIFFICULTIES:
            tk.Radiobutton(
                frame, text=name, variable=self.difficulty_var,
                value=name
            ).pack(anchor="w")

        tk.Button(frame, text="ゲーム開始", width=20,
                  command=self.start).pack(pady=20)

    def start(self):
        self.difficulty = self.difficulty_var.get()
        self.day = 1
        self.money = DIFFICULTIES[self.difficulty]["money"]
        self.reputation = 50
        self.staff = 0
        self.customers = 0
        self.sales = 0
        self.expenses = 0
        self.products = {k: dict(v) for k, v in PRODUCTS.items()}
        self.buildings = {k: 0 for k in BUILDINGS}
        self.licenses = []
        self.event_history = []
        self.started = True
        self.make_screen()
        self.log("開店しました！商品を仕入れましょう。")
        self.refresh()
        self.later(1500, self.customer_event)
        self.later(8000, self.trouble_event)
        self.later(20000, self.special_event)
        self.later(60000, self.new_day)

    def make_screen(self):
        if not getattr(self, "_keep_timers", False):
            self.clear()
        else:
            for widget in self.root.winfo_children():
                widget.destroy()

        top = tk.Frame(self.root, padx=10, pady=8)
        top.pack(fill="x")

        tk.Label(top, text="コンビニ経営ゲーム",
                 font=("Yu Gothic UI", 18, "bold")).pack(side="left")
        tk.Button(top, text="セーブ", command=self.save).pack(side="right", padx=3)
        tk.Button(top, text="ロード", command=self.load).pack(side="right", padx=3)

        self.status = tk.Label(
            self.root, text="", font=("Yu Gothic UI", 11, "bold"),
            anchor="w", padx=10, pady=8, bg="#e8f2e5"
        )
        self.status.pack(fill="x", padx=10)

        body = tk.Frame(self.root, padx=10, pady=10)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(body, width=300)
        right.pack(side="right", fill="both", padx=(10, 0))
        right.pack_propagate(False)

        tk.Label(left, text="商品管理",
                 font=("Yu Gothic UI", 13, "bold")).pack(anchor="w")

        table = tk.Frame(left, bd=1, relief="groove", padx=5, pady=5)
        table.pack(fill="x")

        for col, title in enumerate(["商品", "在庫", "価格", "仕入れ", "価格調整"]):
            tk.Label(table, text=title, font=("Yu Gothic UI", 9, "bold")).grid(
                row=0, column=col, padx=4, pady=4
            )

        self.product_labels = {}

        for r, name in enumerate(self.products, 1):
            tk.Label(table, text=name, width=9, anchor="w").grid(row=r, column=0)
            stock = tk.Label(table, text="", width=6)
            stock.grid(row=r, column=1)
            price = tk.Label(table, text="", width=7)
            price.grid(row=r, column=2)

            buttons = tk.Frame(table)
            buttons.grid(row=r, column=3)
            tk.Button(buttons, text="+10", command=lambda n=name: self.restock(n, 10)).pack(side="left")
            tk.Button(buttons, text="+30", command=lambda n=name: self.restock(n, 30)).pack(side="left")

            prices = tk.Frame(table)
            prices.grid(row=r, column=4)
            tk.Button(prices, text="-10", command=lambda n=name: self.change_price(n, -10)).pack(side="left")
            tk.Button(prices, text="+10", command=lambda n=name: self.change_price(n, 10)).pack(side="left")

            self.product_labels[name] = (stock, price)

        tk.Label(left, text="スタッフ・イベント",
                 font=("Yu Gothic UI", 13, "bold")).pack(anchor="w", pady=(12, 4))

        actions = tk.Frame(left)
        actions.pack(fill="x")
        tk.Button(actions, text="スタッフを雇う 20,000円",
                  command=self.hire).grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        tk.Button(actions, text="スタッフを解雇",
                  command=self.fire).grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        tk.Button(actions, text="強盗イベント",
                  command=self.robbery).grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        tk.Button(actions, text="次の日へ",
                  command=self.new_day).grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        tk.Label(left, text="設備建設",
                 font=("Yu Gothic UI", 13, "bold")).pack(anchor="w", pady=(12, 4))

        build_frame = tk.Frame(left, bd=1, relief="groove", padx=5, pady=5)
        build_frame.pack(fill="x")
        self.build_labels = {}

        for r, (name, info) in enumerate(BUILDINGS.items()):
            tk.Label(build_frame, text=f"{name}  {info['cost']:,}円").grid(
                row=r, column=0, sticky="w", padx=3, pady=3
            )
            count = tk.Label(build_frame, text="")
            count.grid(row=r, column=1, padx=5)
            tk.Button(build_frame, text="建設",
                      command=lambda n=name: self.build(n)).grid(row=r, column=2)
            self.build_labels[name] = count

        tk.Label(left, text="販売ライセンス",
                 font=("Yu Gothic UI", 13, "bold")).pack(anchor="w", pady=(12, 4))
        license_frame = tk.Frame(left, bd=1, relief="groove", padx=5, pady=5)
        license_frame.pack(fill="x")
        self.license_labels = {}
        for r, (name, info) in enumerate(LICENSES.items()):
            tk.Label(license_frame, text=f"{name}  {info['cost']:,}円").grid(
                row=r, column=0, sticky="w", padx=3, pady=3)
            state_label = tk.Label(license_frame, text="未取得")
            state_label.grid(row=r, column=1, padx=5)
            tk.Button(license_frame, text="取得",
                      command=lambda n=name: self.buy_license(n)).grid(row=r, column=2)
            self.license_labels[name] = state_label

        tk.Label(right, text="店舗状況",
                 font=("Yu Gothic UI", 13, "bold")).pack(anchor="w")
        self.stats = tk.Label(right, text="", justify="left", anchor="nw",
                              bd=1, relief="groove", padx=8, pady=8)
        self.stats.pack(fill="x", pady=5)

        tk.Label(right, text="お店の出来事",
                 font=("Yu Gothic UI", 13, "bold")).pack(anchor="w")
        log_frame = tk.Frame(right)
        log_frame.pack(fill="both", expand=True)

        self.log_box = tk.Text(log_frame, state="disabled", wrap="word")
        scroll = tk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scroll.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def log(self, text):
        if hasattr(self, "log_box") and self.log_box.winfo_exists():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"{self.day}日目：{text}\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

    def refresh(self):
        if not self.started:
            return

        self.status.config(
            text=f" {self.day}日目 | 所持金：{self.money:,}円 | "
                 f"評判：{self.reputation}/100 | 難易度：{self.difficulty}"
        )

        for name, item in self.products.items():
            stock, price = self.product_labels[name]
            stock.config(text=f"{item['stock']}個")
            price.config(text=f"{item['price']}円")

        for name in BUILDINGS:
            self.build_labels[name].config(
                text=f"{self.buildings[name]}/{BUILDINGS[name]['max']}"
            )
        for name in LICENSES:
            self.license_labels[name].config(
                text="取得済み" if name in self.licenses else "未取得")

        self.stats.config(
            text=f"スタッフ：{self.staff}人\n"
                 f"本日の来客：{self.customers}人\n"
                 f"本日の売上：{self.sales:,}円\n"
                 f"本日の支出：{self.expenses:,}円\n\n"
                 "経営のヒント\n"
                 "・在庫切れは評判が下がる\n"
                 "・高すぎる商品は売れにくい\n"
                 "・カメラは万引き対策になる\n"
                 "・スタッフはクレーム対応に役立つ"
        )

    def restock(self, name, amount):
        item = self.products[name]
        cost = item["cost"] * amount
        if self.money < cost:
            messagebox.showwarning("資金不足", f"{cost:,}円必要です。")
            return
        self.money -= cost
        self.expenses += cost
        item["stock"] += amount
        self.log(f"{name}を{amount}個仕入れました。支出：{cost:,}円")
        self.refresh()

    def change_price(self, name, delta):
        self.products[name]["price"] = max(10, self.products[name]["price"] + delta)
        self.log(f"{name}の価格を{self.products[name]['price']}円に変更しました。")
        self.refresh()

    def hire(self):
        if self.staff >= 10:
            messagebox.showinfo("採用", "スタッフは最大10人です。")
            return
        if self.money < 20000:
            messagebox.showwarning("資金不足", "20,000円必要です。")
            return
        self.money -= 20000
        self.expenses += 20000
        self.staff += 1
        self.log("スタッフを1人雇いました。毎日人件費がかかります。")
        self.refresh()

    def fire(self):
        if self.staff == 0:
            messagebox.showinfo("スタッフ", "解雇できるスタッフがいません。")
            return
        self.staff -= 1
        self.log("スタッフを1人解雇しました。")
        self.refresh()

    def build(self, name):
        info = BUILDINGS[name]
        if self.buildings[name] >= info["max"]:
            messagebox.showinfo("設備", "これ以上建設できません。")
            return
        if self.money < info["cost"]:
            messagebox.showwarning("資金不足", f"{info['cost']:,}円必要です。")
            return
        self.money -= info["cost"]
        self.expenses += info["cost"]
        self.buildings[name] += 1
        self.log(f"{name}を建設しました。")
        self.refresh()

    def event_popup(self, title, message):
        """イベント発生をポップアップで知らせ、履歴にも記録する。"""
        if not self.started:
            return
        self.event_history.append(f"{self.day}日目：{title} - {message}")
        if len(self.event_history) > 100:
            self.event_history = self.event_history[-100:]
        self.log(f"【イベント】{title}：{message}")
        try:
            messagebox.showinfo(title, message)
        except tk.TclError:
            pass

    def buy_license(self, name):
        if not self.started:
            return
        if name in self.licenses:
            messagebox.showinfo("ライセンス", "このライセンスは取得済みです。")
            return
        cost = LICENSES[name]["cost"]
        if self.money < cost:
            messagebox.showwarning("資金不足", f"ライセンス取得には{cost:,}円必要です。")
            return
        self.money -= cost
        self.expenses += cost
        self.licenses.append(name)
        for product_name, data in LICENSES[name]["products"].items():
            self.products[product_name] = dict(data)
        self.log(f"{name}を取得！新商品が販売可能になりました。")
        # 画面を作り直すが、既存のタイマーは止めない
        self.rebuild_screen_keep_timers()
        self.refresh()
        self.event_popup("ライセンス取得", f"{name}を取得しました。新商品が追加されました。")

    def rebuild_screen_keep_timers(self):
        # clear() はタイマーも止めるため、画面だけを再構築する
        for widget in self.root.winfo_children():
            widget.destroy()
        self.make_screen_without_clear()

    def make_screen_without_clear(self):
        # make_screen と同じ画面を作るため、通常の画面生成を呼ぶ前に
        # タイマーを保持する専用フラグを使う
        self._keep_timers = True
        self.make_screen()
        self._keep_timers = False

    def special_event(self):
        if not self.started:
            return
        event = random.choice(["セール", "テレビ紹介", "ライバル店開店"])
        if event == "セール":
            bonus = random.randint(3000, 10000)
            self.money += bonus
            self.sales += bonus
            self.reputation = min(100, self.reputation + 2)
            self.event_popup("期間限定セール", f"セールが大成功！売上が{bonus:,}円増え、評判も上がりました。")
        elif event == "テレビ紹介":
            bonus = random.randint(5000, 15000)
            self.money += bonus
            self.sales += bonus
            self.reputation = min(100, self.reputation + 8)
            self.event_popup("テレビで紹介！", f"お店がテレビで紹介されました。売上ボーナス{bonus:,}円、評判+8！")
        else:
            drop = random.randint(3, 8)
            self.reputation = max(0, self.reputation - drop)
            self.event_popup("ライバル店が開店", f"近所にライバル店が開店。評判が{drop}下がりました。")
        self.refresh()
        if self.money < 0:
            self.game_over()
        else:
            self.later(30000, self.special_event)

    def customer_event(self):
        if not self.started:
            return

        settings = DIFFICULTIES[self.difficulty]
        chance = settings["customer"] * (0.5 + self.reputation / 100)
        chance += self.buildings["イートイン"] * 0.08
        chance += self.buildings["駐車場"] * 0.15

        if random.random() < min(chance, 0.95):
            self.customers += 1
            name = random.choice(list(self.products))
            item = self.products[name]
            standard = self.products[name]["price"] if name not in PRODUCTS else PRODUCTS[name]["price"]
            buy_chance = max(0.1, min(0.95, 0.8 - (item["price"] / standard - 1) * 0.8))

            if item["stock"] > 0 and random.random() < buy_chance:
                item["stock"] -= 1
                self.money += item["price"]
                self.sales += item["price"]
                self.log(f"{name}が売れました。売上+{item['price']:,}円")
            elif item["stock"] == 0:
                self.reputation = max(0, self.reputation - 1)
                self.log(f"{name}が品切れ。評判が下がりました。")
            else:
                self.log("お客さんは何も買わずに帰りました。")

            self.refresh()

        self.later(1500, self.customer_event)

    def trouble_event(self):
        if not self.started:
            return

        settings = DIFFICULTIES[self.difficulty]
        if random.random() < settings["trouble"]:
            event = random.choice(["万引き", "故障", "クレーム", "破損"])
            event_message = ""

            if event == "万引き":
                prevention = min(0.9, self.buildings["防犯カメラ"] * 0.18 + self.staff * 0.07)
                if random.random() > prevention:
                    loss = random.randint(1000, 6000)
                    self.money -= loss
                    self.reputation = max(0, self.reputation - 2)
                    event_message = f"万引き被害！{loss:,}円の損失。"
                    self.log(event_message)
                else:
                    event_message = "防犯カメラやスタッフが万引きを防ぎました。"
                    self.log(event_message)

            elif event == "故障":
                cost = random.randint(3000, 9000)
                self.money -= cost
                self.expenses += cost
                event_message = f"設備が故障。修理費{cost:,}円。"
                self.log(event_message)

            elif event == "クレーム":
                if self.staff > 0 and random.random() < 0.65:
                    event_message = "スタッフがクレームを解決しました。"
                    self.log(event_message)
                else:
                    drop = random.randint(1, 4)
                    self.reputation = max(0, self.reputation - drop)
                    event_message = f"クレーム発生。評判-{drop}。"
                    self.log(event_message)

            else:
                name = random.choice(list(self.products))
                if self.products[name]["stock"] > 0:
                    self.products[name]["stock"] -= 1
                    event_message = f"{name}が破損し、1個廃棄しました。"
                    self.log(event_message)
                else:
                    event_message = f"{name}は在庫切れのため破損なし。"
                    self.log(event_message)

            self.event_history.append(f"{self.day}日目：{event} - {event_message}")
            try:
                messagebox.showinfo(f"ランダムイベント：{event}", event_message or event)
            except tk.TclError:
                pass
            self.refresh()

        if self.money < 0:
            self.game_over()
        else:
            self.later(8000, self.trouble_event)

    def robbery(self):
        if not self.started:
            return

        if self.staff > 0 and random.random() < 0.5:
            self.log("強盗発生！スタッフが通報し、被害を防ぎました。")
        else:
            loss = random.randint(10000, 30000)
            if self.buildings["防犯カメラ"] > 0:
                loss = int(loss * 0.75)
            self.money -= loss
            self.reputation = max(0, self.reputation - 5)
            self.log(f"強盗被害！{loss:,}円を失いました。")

        self.refresh()
        if self.money < 0:
            self.game_over()

    def new_day(self):
        if not self.started:
            return

        settings = DIFFICULTIES[self.difficulty]
        wages = int(self.staff * 10000)
        maintenance = int((5000 + self.buildings["防犯カメラ"] * 500 +
                           self.buildings["大型冷蔵庫"] * 1000))
        costs = int((wages + maintenance) * settings["trouble"])
        self.money -= costs
        self.expenses += costs
        self.log(f"1日終了。人件費・維持費で{costs:,}円支払いました。")

        if self.sales > self.expenses:
            self.reputation = min(100, self.reputation + 1)

        self.day += 1
        self.customers = 0
        self.sales = 0
        self.expenses = 0
        self.refresh()

        if self.money < 0:
            self.game_over()
        else:
            self.later(60000, self.new_day)

    def game_over(self):
        self.started = False
        self.clear()
        frame = tk.Frame(self.root, padx=30, pady=30)
        frame.pack(expand=True)
        tk.Label(frame, text="ゲームオーバー",
                 font=("Yu Gothic UI", 25, "bold"), fg="red").pack(pady=15)
        tk.Label(frame, text=f"{self.day}日目で経営破綻しました。\n"
                             f"最終所持金：{self.money:,}円").pack(pady=10)
        tk.Button(frame, text="タイトルへ戻る",
                  command=self.show_title).pack(pady=15)

    def save(self):
        if not self.started:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("セーブデータ", "*.json")],
            initialfile="convenience_store_save.json"
        )
        if not path:
            return

        data = {
            "difficulty": self.difficulty,
            "day": self.day,
            "money": self.money,
            "reputation": self.reputation,
            "staff": self.staff,
            "customers": self.customers,
            "sales": self.sales,
            "expenses": self.expenses,
            "products": self.products,
            "buildings": self.buildings,
            "licenses": self.licenses,
            "event_history": self.event_history,
        }

        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            messagebox.showinfo("セーブ", "保存しました。")
        except OSError as error:
            messagebox.showerror("セーブ失敗", str(error))

    def load(self):
        path = filedialog.askopenfilename(
            filetypes=[("セーブデータ", "*.json")]
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if data["difficulty"] not in DIFFICULTIES:
                raise ValueError("難易度が不正です。")

            for name in PRODUCTS:
                if name not in data["products"]:
                    raise ValueError(f"{name}の商品データがありません。")

            self.difficulty = data["difficulty"]
            self.day = int(data["day"])
            self.money = int(data["money"])
            self.reputation = max(0, min(100, int(data["reputation"])))
            self.staff = max(0, int(data["staff"]))
            self.customers = int(data["customers"])
            self.sales = int(data["sales"])
            self.expenses = int(data["expenses"])
            self.licenses = [name for name in data.get("licenses", []) if name in LICENSES]
            product_names = list(PRODUCTS)
            for license_name in self.licenses:
                product_names.extend(LICENSES[license_name]["products"].keys())
            self.products = {}
            for name in product_names:
                saved = data["products"].get(name)
                if saved is not None:
                    self.products[name] = {
                        "cost": int(saved["cost"]),
                        "price": int(saved["price"]),
                        "stock": int(saved["stock"]),
                    }
                elif name in PRODUCTS:
                    self.products[name] = dict(PRODUCTS[name])
                else:
                    for lic in self.licenses:
                        if name in LICENSES[lic]["products"]:
                            self.products[name] = dict(LICENSES[lic]["products"][name])
                            break
            self.event_history = data.get("event_history", [])[-100:]
            self.buildings = {
                name: max(0, min(BUILDINGS[name]["max"],
                                int(data["buildings"].get(name, 0))))
                for name in BUILDINGS
            }

            self.started = True
            self.make_screen()
            self.refresh()
            self.log("セーブデータを読み込みました。")
            self.later(1500, self.customer_event)
            self.later(8000, self.trouble_event)
            self.later(20000, self.special_event)
            self.later(60000, self.new_day)

        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            messagebox.showerror("ロード失敗", str(error))


if __name__ == "__main__":
    root = tk.Tk()
    game = ConvenienceStore(root)
    root.mainloop()