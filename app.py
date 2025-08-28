from flask import Flask, render_template, request
import sqlite3
from datetime import datetime

app = Flask(__name__)

# 建立資料庫 (只需第一次執行)
def init_db():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flavor TEXT NOT NULL,
            toppings TEXT,
            total_price INTEGER,
            order_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/order', methods=['POST'])
def order():
    flavor = request.form.get('flavor')
    toppings = request.form.getlist('topping')

    # 價格表
    flavor_price = {"豚骨": 180, "味噌": 170, "鹽味": 160}
    topping_price = {"叉燒": 30, "溏心蛋": 15, "加麵": 20}

    # 計算金額
    total = flavor_price[flavor]
    for t in toppings:
        total += topping_price[t]

    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 存入資料庫
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (flavor, toppings, total_price, order_time)
        VALUES (?, ?, ?, ?)
    ''', (flavor, ", ".join(toppings), total, order_time))
    conn.commit()
    conn.close()

    return render_template(
        'order_success.html',
        flavor=flavor,
        toppings=toppings,
        total=total,
        order_time=order_time
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
