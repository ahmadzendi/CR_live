from flask import Flask, render_template_string, jsonify
import json
from datetime import datetime

app = Flask(__name__)

def get_ranking():
    try:
        with open("last_request.json", "r", encoding="utf-8") as f:
            req = json.load(f)
        t_awal = datetime.strptime(req["start"], "%Y-%m-%d %H:%M")
        t_akhir = datetime.strptime(req["end"], "%Y-%m-%d %H:%M")
        usernames = [u.lower() for u in req.get("usernames", [])]
        mode = req.get("mode", "")
        kata = req.get("kata", None)
    except Exception as e:
        return [], "Tidak ada DATA", "", "", []

    user_info = {}
    try:
        with open("chat_indodax.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                chat = json.loads(line)
                t_chat = datetime.strptime(chat["timestamp_wib"], "%Y-%m-%d %H:%M:%S")
                uname = chat["username"].lower()
                # --- FILTER WAKTU ---
                if not (t_awal <= t_chat <= t_akhir):
                    continue
                # --- FILTER KATA (CONTENT) ---
                if kata and kata not in chat["content"].lower():
                    continue
                # --- FILTER USERNAME (JIKA MODE USERNAME) ---
                if mode == "username" and usernames:
                    if uname not in usernames:
                        continue
                # --- OLAH DATA USER ---
                if uname not in user_info:
                    user_info[uname] = {
                        "count": 1,
                        "last_content": chat["content"],
                        "last_time": chat["timestamp_wib"]
                    }
                else:
                    user_info[uname]["count"] += 1
                    if t_chat > datetime.strptime(user_info[uname]["last_time"], "%Y-%m-%d %H:%M:%S"):
                        user_info[uname]["last_content"] = chat["content"]
                        user_info[uname]["last_time"] = chat["timestamp_wib"]
    except Exception as e:
        return [], "Tidak ada DATA", "", "", []

    if mode == "username" and usernames:
        ranking = [(u, user_info[u]) if u in user_info else (u, {"count": 0, "last_content": "-", "last_time": "-"}) for u in usernames]
    else:
        ranking = sorted(user_info.items(), key=lambda x: x[1]["count"], reverse=True)
    return ranking, None, req["start"], req["end"], usernames

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ranking Chat Indodax</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css"/>
        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 30px; }
            table.dataTable thead th { font-weight: bold; }
        </style>
    </head>
    <body>
    <h2>Top Chatroom Indodax</h2>
    <table id="ranking" class="display" style="width:100%">
        <thead>
        <tr>
            <th>Nomor</th>
            <th>Username</th>
            <th>Jumlah Chat</th>
            <th>Terakhir Chat</th>
            <th>Waktu Chat</th>
        </tr>
        </thead>
        <tbody>
        </tbody>
    </table>
    <p id="periode"></p>
    <script>
        var table = $('#ranking').DataTable({
            "order": [[2, "desc"]],
            "paging": false,
            "info": false,
            "searching": true,
            "language": {
            "emptyTable": "Tidak ada DATA"
            }
        });

        function loadData() {
            $.getJSON("/data", function(data) {
                table.clear();
                if (data.ranking.length === 0) {
                    $("#periode").html("<b>Tidak ada DATA</b>");
                    table.draw();
                    return;
                }
                for (var i = 0; i < data.ranking.length; i++) {
                    var row = data.ranking[i];
                    table.row.add([
                        i+1,
                        row.username,
                        row.count,
                        row.last_content,
                        row.last_time
                    ]);
                }
                table.draw();
                $("#periode").html("Periode: <b>" + data.t_awal + "</b> s/d <b>" + data.t_akhir + "</b>");
            });
        }

        loadData();
        setInterval(loadData, 1000); // refresh setiap 1 detik
    </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/data")
def data():
    ranking, error, t_awal, t_akhir, usernames = get_ranking()
    if error or not ranking:
        return jsonify({"error": "Tidak ada DATA", "ranking": [], "t_awal": "", "t_akhir": ""})
    data = []
    for user, info in ranking:
        data.append({
            "username": user,
            "count": info["count"],
            "last_content": info["last_content"],
            "last_time": info["last_time"]
        })
    return jsonify({
        "ranking": data,
        "t_awal": t_awal,
        "t_akhir": t_akhir
    })
    
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
