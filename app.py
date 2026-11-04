from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

patients = []
current_token = 0

# ----------------------------
# Priority Mapping
# ----------------------------
MEDICAL_PRIORITY = {"Emergency": 1, "Pregnant": 2, "Senior": 3, "Normal": 4}
REG_PRIORITY = {"Walk-in": 0, "Online": 1}  # Walk-in gets higher priority

# ----------------------------
# Helper Functions
# ----------------------------
def generate_token():
    global current_token
    current_token += 1
    return current_token

def sort_queue():
    # Sort patients by: medical priority -> registration type -> token number
    patients.sort(key=lambda p: (p["medical_priority"], p["reg_priority"], p["token"]))

def waiting_time(pos):
    # Approximate waiting time: each patient takes 10 minutes
    return pos * 10

# ----------------------------
# Routes
# ----------------------------

@app.route("/")
def home():
    return render_template("home.html")

# ----------------------------
# Online Booking
# ----------------------------
@app.route("/online", methods=["GET", "POST"])
def online():
    if request.method == "POST":
        category = request.form["category"]  # "Normal", "Senior", etc.
        patient = {
            "token": generate_token(),
            "name": request.form["name"],
            "age": int(request.form["age"]),
            "gender": request.form["gender"],
            "category": category,
            "type": "Online",
            "medical_priority": MEDICAL_PRIORITY[category],
            "reg_priority": REG_PRIORITY["Online"],
            "status": "Waiting"
        }
        patients.append(patient)
        sort_queue()
    return render_template("online.html")

# ----------------------------
# Walk-in Registration
# ----------------------------
@app.route("/walkin", methods=["GET", "POST"])
def walkin():
    if request.method == "POST":
        category = request.form["category"]
        patient = {
            "token": generate_token(),
            "name": request.form["name"],
            "age": int(request.form["age"]),
            "gender": request.form["gender"],
            "category": category,
            "type": "Walk-in",
            "medical_priority": MEDICAL_PRIORITY[category],
            "reg_priority": REG_PRIORITY["Walk-in"],
            "status": "Waiting"
        }
        patients.append(patient)
        sort_queue()
    return render_template("walkin.html")

# ----------------------------
# Serve Next Patient
# ----------------------------
@app.route("/serve_next")
def serve_next():
    # Complete current serving patient
    for p in patients:
        if p["status"] == "Serving":
            p["status"] = "Completed"
            break
    # Serve next waiting patient
    for p in patients:
        if p["status"] == "Waiting":
            p["status"] = "Serving"
            break
    return redirect(url_for("dashboard"))

# ----------------------------
# Dashboard
# ----------------------------
@app.route("/dashboard")
def dashboard():
    display = []
    queue_no = 0
    for p in patients:
        if p["status"] != "Completed":
            queue_no += 1
            wait = waiting_time(queue_no-1) if p["status"]=="Waiting" else 0
        else:
            wait = 0
        display.append({**p, "queue": queue_no if p["status"]!="Completed" else "-", "wait": wait})
    return render_template("dashboard.html", patients=display)

# ----------------------------
# Check Waiting Time
# ----------------------------
@app.route("/waiting", methods=["GET","POST"])
def waiting():
    result = None
    if request.method == "POST":
        token = int(request.form["token"])
        queue_no = 0
        wait_time = 0
        for idx, p in enumerate(patients):
            if p["status"] != "Completed":
                queue_no += 1
            if p["token"] == token:
                if p["status"]=="Waiting":
                    # Count number of patients ahead in sorted queue
                    patients_sorted = sorted(
                        [x for x in patients if x["status"]!="Completed"],
                        key=lambda x: (x["medical_priority"], x["reg_priority"], x["token"])
                    )
                    pos = 0
                    for x in patients_sorted:
                        if x["token"] == token:
                            break
                        pos +=1
                    wait_time = pos * 10
                result = {
                    "status": p["status"],
                    "queue": queue_no if p["status"]!="Completed" else "-",
                    "wait": wait_time
                }
                break
    return render_template("waiting.html", patient=result)

# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)