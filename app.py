from flask import Flask, request, jsonify, render_template_string
import serial
import time

app = Flask(__name__)

# Change COM17 if your Arduino uses another port.
SERIAL_PORT = "COM17"
BAUD_RATE = 9600

arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Allow Arduino to reset after opening serial

HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Arduino Servo Controller</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 520px;
      margin: 24px auto;
      padding: 16px;
      background: #f4f6f8;
      color: #18212b;
    }
    h2 { margin-bottom: 6px; }
    .motor {
      background: white;
      border: 1px solid #d9dee5;
      border-radius: 12px;
      padding: 18px;
      margin: 16px 0;
    }
    .heading {
      display: flex;
      justify-content: space-between;
      font-weight: bold;
      margin-bottom: 18px;
    }
    input[type=range] { width: 100%; }
    button {
      width: 100%;
      padding: 12px;
      background: #18212b;
      color: white;
      border: 0;
      border-radius: 8px;
      font-size: 16px;
      margin-top: 8px;
    }
    #status { margin-top: 14px; font-size: 14px; }
  </style>
</head>
<body>
  <h2>Servo Controller</h2>
  <p>Move a slider to control its servo.</p>

  <div id="controls"></div>
  <button onclick="sendAll()">Send all angles</button>
  <div id="status">Connecting to controller...</div>

  <script>
    const angles = {2: 90, 3: 90, 4: 90, 5: 90};
    const timers = {};

    const controls = document.getElementById("controls");

    for (const pin of [2, 3, 4, 5]) {
      controls.innerHTML += `
        <div class="motor">
          <div class="heading">
            <span>Motor on pin ${pin}</span>
            <span id="value${pin}">90°</span>
          </div>
          <input type="range" min="0" max="180" value="90"
                 id="slider${pin}"
                 oninput="changeAngle(${pin}, this.value)">
        </div>`;
    }

    async function sendAngle(pin, angle) {
      try {
        const response = await fetch("/set", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({pin: pin, angle: angle})
        });
        const result = await response.json();
        document.getElementById("status").textContent =
          result.message || result.error;
      } catch (error) {
        document.getElementById("status").textContent =
          "Connection error. Check the laptop server.";
      }
    }

    function changeAngle(pin, value) {
      angles[pin] = Number(value);
      document.getElementById("value" + pin).textContent = value + "°";

      clearTimeout(timers[pin]);
      timers[pin] = setTimeout(() => sendAngle(pin, angles[pin]), 60);
    }

    async function sendAll() {
      for (const pin of [2, 3, 4, 5]) {
        await sendAngle(pin, angles[pin]);
      }
    }
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/set", methods=["POST"])
def set_angle():
    data = request.get_json(silent=True) or {}

    try:
        pin = int(data["pin"])
        angle = int(data["angle"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Invalid pin or angle"), 400

    if pin not in [2, 3, 4, 5] or not 0 <= angle <= 180:
        return jsonify(error="Pin must be 2-5 and angle 0-180"), 400

    arduino.write(f"{pin} {angle}\n".encode())
    arduino.flush()

    return jsonify(message=f"Motor {pin} set to {angle}°")

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        arduino.close()