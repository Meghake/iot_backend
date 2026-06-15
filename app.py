from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

# ===================== DATABASE =====================
conn = psycopg2.connect(
    host="localhost",
    database="iot",
    user="postgres",
    password="iot@1211"
)

# ===================== HOME =====================
@app.route("/")
def home():
    return "IoT Backend Running"

# ===================== RESOURCE TREND API ====================
@app.route("/reports/resource-trend")
def resource_trend():

    try:
        device_id = request.args.get("device_id")

        cur = conn.cursor()

        query = """
            SELECT timestamp, cpu_usage, gpu_usage, npu_usage
            FROM device_telemetry
            WHERE device_id=%s
            ORDER BY timestamp DESC
            LIMIT 50
        """

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)