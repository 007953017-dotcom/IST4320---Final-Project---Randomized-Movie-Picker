[README.md](https://github.com/user-attachments/files/27580583/README.md)
# 🎬 Movie Night Picker

A desktop app built with Python and Tkinter that takes the stress out of deciding what to watch. Search real movies, build a personal watchlist, and let the app pick one for you — by genre or completely at random.

---

## 📸 Features

- 🎲 **Discover** — Get a random movie suggestion straight from TMDB, no watchlist needed. Filter by genre or go fully random.
- 🔍 **Search** — Search TMDB's entire movie database by title. See ratings, release year, genre, and a short overview for each result.
- 📋 **Watchlist** — Save movies you're interested in to a local database. Pick a random one to watch, filtered by genre if you want.
- 🖼️ **Movie Posters** — Displays real movie poster images pulled from TMDB (requires Pillow).
- 💾 **Persistent Storage** — Your watchlist is saved locally using SQLite, so it's still there next time you open the app.

---

## 🛠️ Built With

- **Python 3** — Core language
- **Tkinter** — Desktop GUI
- **SQLite3** — Local watchlist database (built into Python, no setup needed)
- **TMDB API** — Movie data, posters, and ratings ([themoviedb.org](https://www.themoviedb.org))
- **Pillow** *(optional)* — Movie poster image rendering

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/movie-night-picker.git
cd movie-night-picker
```

### 2. (Optional) Install Pillow for movie posters
```bash
pip install Pillow
```
> The app works fine without Pillow — it just shows a placeholder icon instead of real posters.

### 3. Run the app
```bash
python movie_night_picker.py
```

> **Note:** Python 3 must be installed. Tkinter comes built into most Python installations. No other setup is required.

---

## 📁 Project Structure

```
movie-night-picker/
│
├── movie_night_picker.py   # Main application (all-in-one)
├── watchlist.db            # Auto-created on first run (SQLite database)
└── README.md               # You're reading it!
```

---

## 🔑 API Key

This project uses the [TMDB API](https://www.themoviedb.org/documentation/api). The API key is included in the source code for demo purposes. If you'd like to use your own:

1. Create a free account at [themoviedb.org](https://www.themoviedb.org/signup)
2. Go to **Settings → API** and copy your API key
3. Replace the `TMDB_API_KEY` value near the top of `movie_night_picker.py`

---

## 📋 How to Use

| Tab | What to do |
|-----|-----------|
| 🎲 Discover | Select a genre (or leave it on "Any Genre") and click **Surprise Me!** |
| 🔍 Search | Type a movie title and press Enter or click **Search**, then click **＋ Add to Watchlist** |
| 📋 Watchlist | View your saved movies, pick a random one, or remove ones you've already watched |

---

## ✅ Project Criteria

| # | Requirement | Implementation |
|---|-------------|----------------|
| 1 | **App UI (Tkinter)** | Full Tkinter GUI with custom widgets, navigation bar, movie cards, and comboboxes |
| 2 | **Custom Functions** | `tmdb_search()`, `tmdb_random_movie()`, `db_add()`, `db_random()`, `fetch_poster()`, and more |
| 3 | **Input does something** | Searches the live TMDB API, saves results to a local SQLite database, and randomly picks a movie |
| 4 | **Hosted on GitHub** | See repository link above |

---

## 🙏 Credits

- Movie data provided by [The Movie Database (TMDB)](https://www.themoviedb.org)
- Built as a final project for an introductory Python course
