import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

# ===================== DATABASE =====================
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
# ===================== HOME =====================
@app.route("/")
def home():
    return "IoT Backend Running"

# ===================== RESOURCE TREND API ====================
@app.route("/reports/resource-trend")
def resource_trend():

    try:
        device_id = request.args.get("device_id")
        range_val = request.args.get("range", "all")

        cur = conn.cursor()

        query = """
            SELECT timestamp, cpu_usage, gpu_usage, npu_usage
            FROM device_telemetry
            WHERE device_id=%s
        """

        if range_val == "1h":
            query += " AND timestamp >= NOW() - INTERVAL '1 hour'"
        elif range_val == "24h":
            query += " AND timestamp >= NOW() - INTERVAL '1 day'"
        elif range_val == "7d":
            query += " AND timestamp >= NOW() - INTERVAL '7 days'"
        elif range_val == "30d":
            query += " AND timestamp >= NOW() - INTERVAL '30 days'"

        query += " ORDER BY timestamp DESC LIMIT 50"

        cur.execute(query, (device_id,))
        rows = cur.fetchall()

        print("DEVICE ID:", device_id)
        print("ROWS FOUND:", len(rows))

        result = []

        for row in rows:
            result.append({
                "timestamp": row[0].isoformat(),
                "cpu_usage": float(row[1]),
                "gpu_usage": float(row[2]),
                "npu_usage": float(row[3])
            })

        cur.close()

        return jsonify(result)

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


# ===================== RUN APP =====================
@app.route("/reports/average-metrics")
def average_metrics():

    device_id = request.args.get("device_id")

    cur = conn.cursor()

    query = """
        SELECT
            AVG(cpu_usage),
            AVG(gpu_usage),
            AVG(npu_usage)
        FROM device_telemetry
        WHERE device_id=%s
    """

    cur.execute(query, (device_id,))

    row = cur.fetchone()

    result = [
        {
            "metric": "CPU",
            "value": float(row[0] or 0)
        },
        {
            "metric": "GPU",
            "value": float(row[1] or 0)
        },
        {
            "metric": "NPU",
            "value": float(row[2] or 0)
        }
    ]

    cur.close()

    return jsonify(result)
@app.route("/reports/resource-distribution")
def resource_distribution():

    device_id = request.args.get("device_id")

    cur = conn.cursor()

    cur.execute("""
        SELECT
            AVG(cpu_usage),
            AVG(gpu_usage),
            AVG(npu_usage)
        FROM device_telemetry
        WHERE device_id=%s
    """, (device_id,))

    row = cur.fetchone()

    print("RESOURCE DISTRIBUTION ROW:", row)

    cur.close()

    return jsonify([
        {
            "name": "CPU",
            "value": float(row[0] or 0)
        },
        {
            "name": "GPU",
            "value": float(row[1] or 0)
        },
        {
            "name": "NPU",
            "value": float(row[2] or 0)
        }
    ])
@app.route("/reports/temperature-trend")
def temperature_trend():

    device_id = request.args.get("device_id")

    cur = conn.cursor()

    cur.execute("""
        SELECT
            timestamp,
            temperature
        FROM device_telemetry
        WHERE device_id=%s
        ORDER BY timestamp
        LIMIT 50
    """, (device_id,))

    rows = cur.fetchall()

    cur.close()

    result = []

    for row in rows:
        result.append({
            "timestamp": row[0].isoformat(),
            "temperature": float(row[1])
        })

    return jsonify(result)
@app.route("/reports/network-usage")
def network_usage():

    device_id = request.args.get("device_id")

    cur = conn.cursor()

    cur.execute("""
        SELECT
            AVG(network_speed),
            AVG(bandwidth_used)
        FROM device_telemetry
        WHERE device_id=%s
    """, (device_id,))

    row = cur.fetchone()

    cur.close()

    return jsonify([
        {
            "metric": "Network Speed",
            "value": float(row[0] or 0)
        },
        {
            "metric": "Bandwidth Used",
            "value": float(row[1] or 0)
        }
    ])
@app.route("/reports/system-utilization")
def system_utilization():

    device_id = request.args.get("device_id")

    cur = conn.cursor()

    cur.execute("""
        SELECT
            AVG(cpu_usage),
            AVG(gpu_usage),
            AVG(npu_usage)
        FROM device_telemetry
        WHERE device_id=%s
    """, (device_id,))

    row = cur.fetchone()

    cur.close()

    return jsonify([
        {
            "category": "CPU",
            "value": float(row[0] or 0)
        },
        {
            "category": "GPU",
            "value": float(row[1] or 0)
        },
        {
            "category": "NPU",
            "value": float(row[2] or 0)
        }
    ])
@app.route("/reports/latest-metrics")
def latest_metrics():

    device_id = request.args.get("device_id")

    cur = conn.cursor()

    cur.execute("""
        SELECT
            cpu_usage,
            gpu_usage,
            npu_usage,
            temperature
        FROM device_telemetry
        WHERE device_id=%s
        ORDER BY timestamp DESC
        LIMIT 1
    """, (device_id,))

    row = cur.fetchone()

    cur.close()

    if not row:
        return jsonify({
            "cpu": 0,
            "gpu": 0,
            "npu": 0,
            "temperature": 0
        })

    return jsonify({
        "cpu": float(row[0]),
        "gpu": float(row[1]),
        "npu": float(row[2]),
        "temperature": float(row[3])
    })
@app.route("/reports/top-devices")
def top_devices():

    cur = conn.cursor()

    cur.execute("""
        SELECT
            device_id,
            ROUND(AVG(cpu_usage)::numeric,2),
            ROUND(AVG(gpu_usage)::numeric,2),
            ROUND(AVG(temperature)::numeric,2)
        FROM device_telemetry
        GROUP BY device_id
        ORDER BY AVG(cpu_usage) DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    cur.close()

    result = []

    for row in rows:
        result.append({
            "device_id": row[0],
            "avg_cpu": float(row[1]),
            "avg_gpu": float(row[2]),
            "avg_temp": float(row[3])
        })

    return jsonify(result)
@app.route("/reports/device-comparison")
def device_comparison():

    device1 = request.args.get("device1")
    device2 = request.args.get("device2")

    cur = conn.cursor()

    result = []

    for device in [device1, device2]:

        cur.execute("""
            SELECT
                AVG(cpu_usage),
                AVG(gpu_usage),
                AVG(temperature)
            FROM device_telemetry
            WHERE device_id=%s
        """, (device,))

        row = cur.fetchone()

        result.append({
            "device_id": device,
            "cpu": float(row[0] or 0),
            "gpu": float(row[1] or 0),
            "temperature": float(row[2] or 0)
        })

    cur.close()

    return jsonify(result)
@app.route("/reports/notifications")
def notifications():

    cur = conn.cursor()

    cur.execute("""
        SELECT
            device_id,
            cpu_usage,
            temperature,
            timestamp
        FROM device_telemetry
        WHERE cpu_usage > 80
           OR temperature > 70
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    cur.close()

    result = []

    for row in rows:
        result.append({
            "device_id": row[0],
            "cpu": float(row[1]),
            "temperature": float(row[2]),
            "timestamp": row[3].isoformat()
        })

    return jsonify(result)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)