from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

# ================= SOCKET IMPORTS =================
from flask_socketio import SocketIO
import eventlet

eventlet.monkey_patch()

# ================= APP SETUP =================
app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")

# ================= DATABASE =================
conn = psycopg2.connect(
    host="localhost",
    database="iot",
    user="postgres",
    password="iot@1211"
)

# ================= HOME =================
@app.route("/")
def home():
    return "IoT Backend Running"

# =========================================================
# 1. RESOURCE TREND (WITH RANGE FILTER)
# =========================================================
@app.route("/reports/resource-trend")
def resource_trend():

    device_id = request.args.get("device_id")
    range_val = request.args.get("range", "24h")

    cur = conn.cursor()

    query = """
        SELECT timestamp, cpu_usage, gpu_usage, npu_usage
        FROM device_telemetry
        WHERE device_id=%s
    """

    if range_val == "1h":
        query += " AND timestamp >= NOW() - INTERVAL '1 hour'"
    elif range_val == "7d":
        query += " AND timestamp >= NOW() - INTERVAL '7 days'"
    else:
        query += " AND timestamp >= NOW() - INTERVAL '1 day'"

    query += " ORDER BY timestamp LIMIT 50"

    cur.execute(query, (device_id,))
    rows = cur.fetchall()
    cur.close()

    return jsonify([
        {
            "timestamp": r[0],
            "cpu_usage": float(r[1]),
            "gpu_usage": float(r[2]),
            "npu_usage": float(r[3])
        }
        for r in rows
    ])

# =========================================================
# 2. AVERAGE METRICS
# =========================================================
@app.route("/reports/average-metrics")
def average_metrics():

    device_id = request.args.get("device_id")
    cur = conn.cursor()

    cur.execute("""
        SELECT AVG(cpu_usage), AVG(gpu_usage), AVG(npu_usage), AVG(temperature)
        FROM device_telemetry
        WHERE device_id=%s
    """, (device_id,))

    row = cur.fetchone()
    cur.close()

    return jsonify([
        {"metric": "CPU", "value": round(float(row[0]), 2)},
        {"metric": "GPU", "value": round(float(row[1]), 2)},
        {"metric": "NPU", "value": round(float(row[2]), 2)},
        {"metric": "Temperature", "value": round(float(row[3]), 2)}
    ])

# =========================================================
# 3. RESOURCE DISTRIBUTION
# =========================================================
@app.route("/reports/resource-distribution")
def resource_distribution():

    device_id = request.args.get("device_id")
    cur = conn.cursor()

    cur.execute("""
        SELECT SUM(cpu_usage), SUM(gpu_usage), SUM(npu_usage)
        FROM device_telemetry
        WHERE device_id=%s
    """, (device_id,))

    row = cur.fetchone()
    cur.close()

    return jsonify([
        {"name": "CPU", "value": round(float(row[0]), 2)},
        {"name": "GPU", "value": round(float(row[1]), 2)},
        {"name": "NPU", "value": round(float(row[2]), 2)}
    ])

# =========================================================
# 4. TEMPERATURE TREND
# =========================================================
@app.route("/reports/temperature-trend")
def temperature_trend():

    device_id = request.args.get("device_id")
    cur = conn.cursor()

    cur.execute("""
        SELECT timestamp, temperature
        FROM device_telemetry
        WHERE device_id=%s
        ORDER BY timestamp
        LIMIT 50
    """, (device_id,))

    rows = cur.fetchall()
    cur.close()

    return jsonify([
        {"timestamp": r[0], "temperature": float(r[1])}
        for r in rows
    ])

# =========================================================
# 5. NETWORK USAGE
# =========================================================
@app.route("/reports/network-usage")
def network_usage():

    device_id = request.args.get("device_id")
    cur = conn.cursor()

    cur.execute("""
        SELECT AVG(network_speed),
               AVG(network_speed) * 0.6,
               AVG(bandwidth_used)
        FROM device_telemetry
        WHERE device_id=%s
    """, (device_id,))

    row = cur.fetchone()
    cur.close()

    return jsonify([
        {"metric": "Download Speed", "value": round(float(row[0]), 2)},
        {"metric": "Upload Speed", "value": round(float(row[1]), 2)},
        {"metric": "Bandwidth Used", "value": round(float(row[2]), 2)}
    ])

# =========================================================
# 6. SYSTEM UTILIZATION
# =========================================================
@app.route("/reports/system-utilization")
def system_utilization():

    device_id = request.args.get("device_id")
    cur = conn.cursor()

    cur.execute("""
        SELECT cpu_usage
        FROM device_telemetry
        WHERE device_id=%s
    """, (device_id,))

    rows = cur.fetchall()
    cur.close()

    low = medium = high = 0

    for r in rows:
        cpu = float(r[0])

        if cpu <= 30:
            low += 1
        elif cpu <= 70:
            medium += 1
        else:
            high += 1

    return jsonify([
        {"category": "Low Load", "value": low},
        {"category": "Medium Load", "value": medium},
        {"category": "High Load", "value": high}
    ])

# =========================================================
# 🔥 REAL-TIME WEBSOCKET STREAM
# =========================================================
def stream_live_data():

    while True:
        cur = conn.cursor()

        cur.execute("""
            SELECT device_id, cpu_usage, gpu_usage, npu_usage, timestamp
            FROM device_telemetry
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        row = cur.fetchone()
        cur.close()

        if row:
            socketio.emit("iot_live", {
                "deviceId": row[0],
                "cpu": float(row[1]),
                "gpu": float(row[2]),
                "npu": float(row[3]),
                "time": str(row[4])
            })

        socketio.sleep(2)

# start background streaming
socketio.start_background_task(stream_live_data)

# =========================================================
# SOCKET CONNECTION EVENT
# =========================================================
@socketio.on("connect")
def on_connect():
    print("Client connected 🔥")

# =========================================================
# RUN SERVER
# =========================================================
if __name__ == "__main__":
    socketio.run(app, debug=True)