from flask import Flask, request, jsonify, render_template
import mysql.connector

app = Flask(__name__)


def create_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  
        password='root',  
        database='tomato'
    )


# Home route
@app.route('/')
def home():
    return render_template('index.html')


# Place an order (POST)
@app.route('/place_order', methods=['POST'])
def place_order():
    cursor = None
    connection = None
    try:
        order_data = request.get_json()
        cart = order_data['cart']
        address = order_data['address']

        if not cart or not address:
            return jsonify({"error": "Cart is empty or address is missing."}), 400

        connection = create_connection()
        cursor = connection.cursor()

        # Step 1: Create a single order
        user_id = 1  # For demo purposes
        cursor.execute(
            "INSERT INTO orders (user_id, delivery_address) VALUES (%s, %s)",
            (user_id, address)
        )
        order_id = cursor.lastrowid  # Get the new order_id

        # Step 2: Insert items in order_items
        for item in cart:
            item_name = item['name']
            quantity = item['quantity']

            cursor.execute("SELECT item_id, price FROM items WHERE item_name = %s", (item_name,))
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": f"Item {item_name} not found."}), 400

            item_id, price = result

            cursor.execute(
                "INSERT INTO order_items (order_id, item_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, item_id, quantity, price)
            )

        connection.commit()
        return jsonify({"message": "Order placed successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

# Get all orders (GET)
@app.route('/orders', methods=['GET'])
def get_orders():
    cursor = None
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT 
                o.order_id,
                o.delivery_address,
                o.order_date,
                c.first_name,
                c.last_name,
                i.item_name,
                oi.quantity,
                oi.price
            FROM orders o
            JOIN customers c ON o.user_id = c.user_id
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN items i ON oi.item_id = i.item_id
            """
        cursor.execute(query)
        orders = cursor.fetchall()

        return jsonify({"orders": orders}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route('/dashboard', methods=['GET'])
def dashboard():
    cursor = None
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        # Total Revenue
        cursor.execute("SELECT SUM(price * quantity) AS total_revenue FROM order_items")
        total_revenue = cursor.fetchone()

        # Revenue by Item
        cursor.execute("""
            SELECT i.item_name, SUM(oi.price * oi.quantity) AS revenue
            FROM order_items oi
            JOIN items i ON oi.item_id = i.item_id
            GROUP BY i.item_name
        """)
        revenue_by_item = cursor.fetchall()

        return jsonify({
            "total_revenue": total_revenue,
            "revenue_by_item": revenue_by_item
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if connection: connection.close()
    

@app.route('/revenue')
def revenue():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(price * quantity) FROM order_items")
    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify({
        "total_revenue": result if result else 0
    })


if __name__ == '__main__':
    app.run(debug=True)
