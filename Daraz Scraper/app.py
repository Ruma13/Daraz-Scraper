import os
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from scraper import scrape_listing, save_to_csv

app = Flask(__name__)
app.secret_key = "dev-secret"

EXPORT_PATH = os.path.join("static", "exports", "daraz_products.csv")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape_route():
    query = request.form.get("query", "").strip()
    if not query:
        flash("Please enter a search query or URL.")
        return redirect(url_for("index"))

    max_items = int(request.form.get("max_items", 50))
    products = scrape_listing(query, headless=True, max_items=max_items)
    save_to_csv(products, EXPORT_PATH)

    return render_template("results.html", products=products)

@app.route("/download")
def download_csv():
    return send_file(EXPORT_PATH, as_attachment=True)

if __name__ == "__main__":
    os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
    app.run(debug=True)
