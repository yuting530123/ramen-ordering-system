import psycopg2cffi.compat
psycopg2cffi.compat.register() 

from flask import Flask, render_template, request
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# 資料庫連線設定
def get_db_connection():
    # 方法1: 使用環境變數 (建議)
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    



# 建立資料庫表格
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 建立訂單表格 (PostgreSQL 語法)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                flavor VARCHAR(50) NOT NULL,
                toppings TEXT,
                total_price INTEGER,
                order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ 資料庫表格建立成功！")
        
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/order', methods=['POST'])
def order():
    try:
        flavor = request.form.get('flavor')
        toppings = request.form.getlist('topping')
        
        # 價格表
        flavor_price = {"豚骨": 180, "味噌": 170, "鹽味": 160}
        topping_price = {"叉燒": 30, "溏心蛋": 15, "加麵": 20}
        
        # 計算金額
        total = flavor_price.get(flavor, 0)
        for t in toppings:
            total += topping_price.get(t, 0)
        
        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 存入 PostgreSQL 資料庫
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (flavor, toppings, total_price, order_time)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (flavor, ", ".join(toppings), total, order_time))
        
        order_id = cursor.fetchone()[0]  # 取得新訂單的 ID
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ 訂單 #{order_id} 建立成功！")
        
        return render_template(
            'order_success.html',
            order_id=order_id,
            flavor=flavor,
            toppings=toppings,
            total=total,
            order_time=order_time
        )
        
    except Exception as e:
        print(f"❌ 訂單處理失敗: {e}")
        return "訂單處理失敗，請稍後再試", 500

# 新增：查看所有訂單的功能 (可選)
@app.route('/orders')
def view_orders():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, flavor, toppings, total_price, order_time 
            FROM orders 
            ORDER BY order_time DESC 
            LIMIT 50
        ''')
        
        orders = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('orders.html', orders=orders)
        
    except Exception as e:
        print(f"❌ 查詢訂單失敗: {e}")
        return "查詢失敗", 500

# 新增：取得今日銷售統計 (可選)
@app.route('/stats')
def daily_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 今日訂單數量和總金額
        cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(total_price), 0)
            FROM orders 
            WHERE DATE(order_time) = CURRENT_DATE
        ''')
        
        count, total_sales = cursor.fetchone()
        
        # 最受歡迎的口味
        cursor.execute('''
            SELECT flavor, COUNT(*) as count
            FROM orders 
            WHERE DATE(order_time) = CURRENT_DATE
            GROUP BY flavor 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        
        popular_flavor = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "今日訂單數": count,
            "今日銷售額": total_sales,
            "最受歡迎口味": popular_flavor[0] if popular_flavor else "無"
        }
        
    except Exception as e:
        print(f"❌ 統計查詢失敗: {e}")
        return {"error": "統計查詢失敗"}, 500

if __name__ == '__main__':
    init_db()  # 啟動時初始化資料庫
    app.run(debug=True)



