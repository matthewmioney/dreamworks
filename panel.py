from flask import Flask, render_template, redirect
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    conn = get_db()
    loas = conn.execute("SELECT * FROM loas ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", loas=loas)

@app.route("/cancel/<int:loa_id>")
def cancel_loa(loa_id):
    conn = get_db()
    conn.execute("UPDATE loas SET status='Cancelled' WHERE id=?", (loa_id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/delete/<int:loa_id>")
def delete_loa(loa_id):
    conn = get_db()
    conn.execute("DELETE FROM loas WHERE id=?", (loa_id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
