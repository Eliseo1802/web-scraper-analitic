from flask import Flask, render_template, request, send_file
from ABCD_Scraper import WebScraper  # Import your WebScraper class
import os

app = Flask(__name__)
DRIVER_PATH = "C:/Users/Equipo/Desktop/PRÁCTICA INTERMEDIA PUCV/Web Scraper/WebScraper_Analitic/chromedriver.exe"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape():
    query = request.form.get("query")
    if not query:
        return "Please enter a query.", 400

    scraper = WebScraper(DRIVER_PATH)
    try:
        scraper.scrape_adnradio(query)
        scraper.scrape_biobiochile(query)
        scraper.scrape_duckduckgo(query)
        scraper.scrape_cooperativa(query)

        filename = "scraped_articles.csv"
        scraper.save_to_csv(filename)
        return send_file(filename, as_attachment=True)
    finally:
        scraper.close()

if __name__ == "__main__":
    app.run(debug=True)
