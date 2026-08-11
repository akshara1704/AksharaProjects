from flask import Flask, render_template, request, send_file
import os
import pandas as pd
from docx import Document
from textblob import TextBlob
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import numpy as np

# ================= CONFIG =================

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
CHART_FOLDER = os.path.join("static", "charts")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"csv", "docx"}
MAX_FILE_SIZE_MB = 5

# ================= UTILITIES =================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_data_quality_score(df):
    missing_percent = (df.isnull().sum().sum() / df.size) * 100
    duplicates = df.duplicated().sum()

    score = 100
    score -= min(30, missing_percent)
    score -= min(20, duplicates)

    return round(max(score, 60), 2)

# ================= AI-LIKE INSIGHTS =================

def generate_insights(df):
    insights = []
    num_df = df.select_dtypes(include=np.number)

    if not num_df.empty:
        for col in num_df.columns:
            insights.append(
                f"{col} ranges between {df[col].min():.2f} and {df[col].max():.2f} with an average of {df[col].mean():.2f}."
            )

        corr = num_df.corr()
        strong = np.where((corr > 0.7) & (corr < 1))
        for i, j in zip(*strong):
            insights.append(
                f"Strong positive correlation found between '{corr.index[i]}' and '{corr.columns[j]}'."
            )

    if df.isnull().sum().sum() == 0:
        insights.append("Dataset has no missing values. Data quality is excellent.")
    else:
        insights.append("Dataset contains missing values which can affect accuracy.")

    return insights

# ================= DOCX ANALYSIS =================

def analyze_docx(file_path):
    doc = Document(file_path)
    text = " ".join([p.text for p in doc.paragraphs if p.text.strip()])
    words = text.split()
    sentiment = TextBlob(text).sentiment

    freq = {}
    for w in words:
        w = w.lower().strip(".,!?")
        if len(w) > 3:
            freq[w] = freq.get(w, 0) + 1

    wc_path = None
    if freq:
        wc = WordCloud(width=800, height=400, background_color="white").generate_from_frequencies(freq)
        wc_path = os.path.join(CHART_FOLDER, "wordcloud.png")
        wc.to_file(wc_path)

    return {
        "type": "docx",
        "word_count": len(words),
        "sentiment_polarity": round(sentiment.polarity, 3),
        "sentiment_subjectivity": round(sentiment.subjectivity, 3),
        "summary": text[:1000] + "...",
        "wordcloud_path": wc_path
    }

# ================= CSV ANALYSIS =================

def analyze_csv(file_path):
    df = pd.read_csv(file_path)

    rows, cols = df.shape
    missing = df.isnull().sum().to_dict()
    desc_html = df.describe(include="all").to_html(classes="table table-bordered table-sm", border=0)
    preview_html = df.head(10).to_html(classes="table table-bordered table-striped table-sm", border=0)
    numeric_cols = df.select_dtypes(include=np.number)

    charts = []

    # --- Missing Values Chart ---
    if sum(missing.values()) > 0:
        plt.figure()
        pd.Series(missing)[pd.Series(missing) > 0].plot(kind='bar')
        path = os.path.join(CHART_FOLDER, "missing_values.png")
        plt.title("Missing Values")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        charts.append(os.path.basename(path))

    # --- Correlation Heatmap ---
    if numeric_cols.shape[1] >= 2:
        plt.figure()
        sns.heatmap(numeric_cols.corr(), annot=True, cmap="coolwarm")
        path = os.path.join(CHART_FOLDER, "correlation_heatmap.png")
        plt.title("Correlation Heatmap")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        charts.append(os.path.basename(path))

    # --- Auto Line Charts ---
    for col in numeric_cols.columns:
        plt.figure()
        df[col].plot(kind="line")
        plt.title(f"{col} Trend")
        path = os.path.join(CHART_FOLDER, f"{col}_trend.png")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        charts.append(os.path.basename(path))
    insights = generate_insights(df)
    quality_score = generate_data_quality_score(df)

    return {
        "type": "csv",
        "rows": rows,
        "cols": cols,
        "missing_values": missing,
        "description_html": desc_html,
        "preview_html": preview_html,
        "charts": charts,
        "insights": insights,
        "quality_score": quality_score
    }

# ================= PDF REPORT =================

def generate_pdf_report(data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # ================= HEADER =================
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 40, "Automated File Insight Report")

    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(width / 2, height - 60, "Generated from Web Dashboard")

    y = height - 90

    # ================= BASIC INFO =================
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, "Dataset Overview")
    y -= 20

    pdf.setFont("Helvetica", 11)
    pdf.drawString(60, y, f"Rows: {data.get('rows', 'N/A')}")
    y -= 15
    pdf.drawString(60, y, f"Columns: {data.get('cols', 'N/A')}")
    y -= 15
    pdf.drawString(60, y, f"Data Quality Score: {data.get('quality_score', 'N/A')} / 100")
    y -= 30

    # ================= MISSING VALUES =================
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, "Missing Values")
    y -= 20

    pdf.setFont("Helvetica", 10)
    for col, val in data.get("missing_values", {}).items():
        pdf.drawString(60, y, f"{col}: {val}")
        y -= 14

    y -= 20

    # ================= AI INSIGHTS =================
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, "AI-Generated Insights")
    y -= 20

    pdf.setFont("Helvetica", 10)
    for insight in data.get("insights", []):
        pdf.drawString(60, y, f"- {insight}")
        y -= 14

        if y < 100:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 60

    # ================= CHARTS SECTION =================
    pdf.showPage()
    y = height - 60

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(width / 2, y, "Auto-Generated Visualizations")
    y -= 30

    for chart in data.get("charts", []):
        chart_path = os.path.join(CHART_FOLDER, chart)

        if os.path.exists(chart_path):
            try:
                pdf.drawImage(
                    chart_path,
                    60,
                    y - 220,
                    width=480,
                    height=220,
                    preserveAspectRatio=True,
                    mask="auto"
                )
                y -= 250

                if y < 100:
                    pdf.showPage()
                    y = height - 60
            except:
                pass

    # ================= FOOTER =================
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawCentredString(width / 2, 30, "End of Report - Generated by Automated Report Generator")

    pdf.save()
    buffer.seek(0)
    return buffer
# ================= ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("file")

    if not file or not allowed_file(file.filename):
        return "Invalid file type", 400

    if request.content_length and request.content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
        return "File too large", 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    if file.filename.endswith(".docx"):
        result = analyze_docx(filepath)
    else:
        result = analyze_csv(filepath)

    return render_template("result.html", result=result, filename=file.filename)

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)

    if filename.endswith(".docx"):
        result = analyze_docx(path)
    else:
        result = analyze_csv(path)

    pdf = generate_pdf_report(result)
    return send_file(pdf, as_attachment=True, download_name="report.pdf")

# ================= MAIN =================

if __name__ == "__main__":
    app.run(debug=True)
