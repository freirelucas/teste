# 🚀 Quick Start Guide

Get started with Overton Policy Citation Analyzer in 5 minutes!

## 1️⃣ Installation (2 minutes)

### Option A: Using the Run Script (Recommended)

**Linux/Mac:**
```bash
./run.sh
```

**Windows:**
```cmd
run.bat
```

The script will automatically:
- Create a virtual environment
- Install all dependencies
- Start the application

### Option B: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 2️⃣ Get Your API Key (1 minute)

1. Go to [overton.io](https://overton.io/)
2. Sign up for a free account
3. Navigate to API section
4. Copy your API key

## 3️⃣ Start Analyzing (2 minutes)

1. **Open your browser** → `http://localhost:5000`

2. **Enter your configuration:**
   - Paste your Overton API key
   - Enter search query (e.g., "agent based models")
   - Set max results (50-200 for quick test)

3. **Click "Start Analysis"**

4. **Wait 2-5 minutes** while the app:
   - Searches Overton for policies
   - Fetches research metadata from OpenAlex
   - Performs comprehensive analysis
   - Generates visualizations

5. **Explore your results** in the interactive tabs:
   - 📚 Bibliometric Analysis
   - 🔗 Co-Citation Network
   - 📈 Temporal Trends
   - 🎯 Topics & Themes
   - 🌍 Geographic Distribution
   - 🏛️ Sector Comparison

6. **Export results** to JSON or Excel

## 📝 Example First Query

Try this to get started:

```
Query: "climate change policy"
Max Results: 100
```

This should complete in ~3 minutes and give you good example data.

## 🎯 What to Look For

After your first analysis, check out:

1. **Top Cited Works** (Bibliometric tab)
   - See which research papers have the most policy impact

2. **Network Visualization** (Network tab)
   - Interactive graph showing how papers are connected

3. **Publications Timeline** (Temporal tab)
   - See trends over the years

4. **Sector Distribution** (Sectors tab)
   - Compare government vs think tanks vs academia

## ⚡ Tips for Best Results

- **Start small**: Use 50-100 results for your first test
- **Be specific**: "renewable energy economics" is better than just "energy"
- **Use quotes**: For exact phrases like "machine learning"
- **Check SDGs**: See which UN goals your research aligns with

## 🐛 Common Issues

**"No policies found"**
- Try a broader search query
- Check your API key is correct

**Slow performance**
- Reduce max_results to 100 or less
- Your query might be very popular (lots of papers)

**Network won't display**
- Refresh the page
- Check browser console for errors
- Ensure internet connection (loads D3.js from CDN)

## 📊 Understanding Your Results

### H-Index
Measures impact: if h=10, means 10 papers each cited at least 10 times

### PageRank
Higher = more central/influential in the network

### Emerging Topics
Topics growing in popularity in recent years

### Citation Lag
Average time from research publication to policy citation

## 🔄 Running Multiple Analyses

Each analysis is saved with a timestamp in the `reports/` folder. You can:
1. Run multiple queries in sequence
2. Export each to compare later
3. Keep a library of analyses

## 📚 Next Steps

Once comfortable with basic usage:

1. Read the full [README.md](README.md) for details
2. Explore all analysis tabs
3. Try different types of queries
4. Compare results across topics
5. Customize settings in `config.py`

## 💡 Pro Tips

- **Save your API key**: Add to `.env` file so you don't have to enter it each time
- **Use Excel export**: Great for creating your own charts and tables
- **Check the reports folder**: All analyses are saved automatically
- **Network size**: Larger queries = bigger networks = more insights (but slower)

---

**Questions?** Check the full [README.md](README.md) or explore the code!

**Ready to start?** Run `./run.sh` (Linux/Mac) or `run.bat` (Windows)!

🎉 Happy analyzing!
