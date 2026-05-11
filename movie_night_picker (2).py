import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import sqlite3
import random
import urllib.request
import urllib.parse
import json
import threading
import io

# ── PIL for poster images (optional but nice) ──────────────────────────────
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────
TMDB_API_KEY  = "a1cf3958ae286f05fb0372d028b2887d"
TMDB_BASE     = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w300"

GENRE_MAP = {
    "Action":    28,
    "Animation": 16,
    "Comedy":    35,
    "Drama":     18,
    "Horror":    27,
    "Mystery":   9648,
    "Romance":   10749,
    "Sci-Fi":    878,
    "Thriller":  53,
}

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#0d0d0d"
SURFACE  = "#161616"
CARD     = "#1e1e1e"
BORDER   = "#2a2a2a"
ACCENT   = "#e50914"        # Netflix-ish red
ACCENT2  = "#f5a623"        # gold star
TEXT     = "#ffffff"
SUBTEXT  = "#999999"
HOVER    = "#2e2e2e"


# ─────────────────────────────────────────────────────────────────────────────
#  TMDB HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def tmdb_get(endpoint, params=None):
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    url = f"{TMDB_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def _resolve_genre(genre_ids):
    rev = {v: k for k, v in GENRE_MAP.items()}
    for gid in genre_ids:
        if gid in rev:
            return rev[gid]
    return "General"


def _parse_movie(m):
    year = (m.get("release_date") or "")[:4] or "N/A"
    return {
        "title":    m.get("title", "Unknown"),
        "genre":    _resolve_genre(m.get("genre_ids", [])),
        "year":     year,
        "rating":   round(m.get("vote_average", 0), 1),
        "overview": m.get("overview", "No description available."),
        "poster":   m.get("poster_path", ""),
        "votes":    m.get("vote_count", 0),
    }


def tmdb_search(query):
    data = tmdb_get("search/movie", {"query": query, "language": "en-US", "page": 1})
    if not data:
        return []
    return [_parse_movie(m) for m in data.get("results", [])[:8]]


def tmdb_random_movie(genre_id=None):
    page   = random.randint(1, 8)
    params = {"language": "en-US", "sort_by": "popularity.desc",
              "page": page, "vote_count.gte": 200}
    if genre_id:
        params["with_genres"] = genre_id
    data = tmdb_get("discover/movie", params)
    if not data or not data.get("results"):
        return None
    return _parse_movie(random.choice(data["results"]))


def fetch_poster(path):
    """Download poster image bytes, returns PhotoImage or None."""
    if not PIL_OK or not path:
        return None
    try:
        url = TMDB_IMG_BASE + path
        with urllib.request.urlopen(url, timeout=6) as r:
            data = r.read()
        img = Image.open(io.BytesIO(data)).resize((120, 180), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def make_placeholder(w=120, h=180):
    """A dark gradient placeholder when no poster is available."""
    if not PIL_OK:
        return None
    img  = Image.new("RGB", (w, h), "#1e1e1e")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w, h], fill="#1e1e1e")
    draw.text((w//2 - 14, h//2 - 8), "🎬", fill="#444444")
    return ImageTk.PhotoImage(img)


# ─────────────────────────────────────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("watchlist.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, genre TEXT, year TEXT,
        rating REAL, overview TEXT, poster TEXT)""")
    conn.commit(); conn.close()


def db_add(movie):
    conn   = sqlite3.connect("watchlist.db")
    cur    = conn.cursor()
    cur.execute("SELECT id FROM watchlist WHERE title=?", (movie["title"],))
    if cur.fetchone():
        conn.close(); return False
    cur.execute("INSERT INTO watchlist(title,genre,year,rating,overview,poster) VALUES(?,?,?,?,?,?)",
                (movie["title"], movie["genre"], movie["year"],
                 movie["rating"], movie["overview"], movie["poster"]))
    conn.commit(); conn.close(); return True


def db_all():
    conn  = sqlite3.connect("watchlist.db")
    rows  = conn.execute("SELECT title,genre,year,rating,overview,poster FROM watchlist").fetchall()
    conn.close()
    return [{"title": r[0], "genre": r[1], "year": r[2],
             "rating": r[3], "overview": r[4], "poster": r[5]} for r in rows]


def db_remove(title):
    conn = sqlite3.connect("watchlist.db")
    conn.execute("DELETE FROM watchlist WHERE title=?", (title,))
    conn.commit(); conn.close()


def db_random(genre=None):
    movies = db_all()
    if genre and genre != "All Genres":
        movies = [m for m in movies if m["genre"] == genre]
    return random.choice(movies) if movies else None


# ─────────────────────────────────────────────────────────────────────────────
#  CUSTOM WIDGETS
# ─────────────────────────────────────────────────────────────────────────────
class HoverButton(tk.Label):
    """A flat label-button with hover highlight."""
    def __init__(self, master, text, command, bg=ACCENT, fg=TEXT,
                 font_size=10, bold=True, padx=18, pady=8, **kw):
        f = ("Helvetica", font_size, "bold" if bold else "normal")
        super().__init__(master, text=text, bg=bg, fg=fg, font=f,
                         padx=padx, pady=pady, cursor="hand2", **kw)
        self._bg = bg
        self._hbg = self._lighten(bg)
        self.bind("<Enter>",  lambda e: self.config(bg=self._hbg))
        self.bind("<Leave>",  lambda e: self.config(bg=self._bg))
        self.bind("<Button-1>", lambda e: command())

    @staticmethod
    def _lighten(hex_color):
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, r + 30); g = min(255, g + 30); b = min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"


class MovieCard(tk.Frame):
    """A single movie card widget showing poster + info."""
    def __init__(self, master, movie, on_add=None, on_remove=None,
                 show_remove=False, width=680, **kw):
        super().__init__(master, bg=CARD, bd=0, highlightthickness=1,
                         highlightbackground=BORDER, **kw)
        self._photo = None
        self._build(movie, on_add, on_remove, show_remove)

    def _build(self, movie, on_add, on_remove, show_remove):
        # Poster
        poster_frame = tk.Frame(self, bg=CARD, width=100, height=150)
        poster_frame.pack(side="left", padx=(14, 12), pady=14)
        poster_frame.pack_propagate(False)
        self._poster_lbl = tk.Label(poster_frame, bg="#2a2a2a", text="🎬",
                                    font=("Helvetica", 24), fg="#555")
        self._poster_lbl.pack(fill="both", expand=True)

        # Info
        info = tk.Frame(self, bg=CARD)
        info.pack(side="left", fill="both", expand=True, pady=14)

        tk.Label(info, text=movie["title"], font=("Helvetica", 13, "bold"),
                 fg=TEXT, bg=CARD, anchor="w", wraplength=360,
                 justify="left").pack(anchor="w")

        meta_row = tk.Frame(info, bg=CARD)
        meta_row.pack(anchor="w", pady=(3, 6))
        tk.Label(meta_row, text=f"⭐ {movie['rating']}", font=("Helvetica", 10, "bold"),
                 fg=ACCENT2, bg=CARD).pack(side="left")
        tk.Label(meta_row, text=f"  {movie['year']}  ·  {movie['genre']}",
                 font=("Helvetica", 10), fg=SUBTEXT, bg=CARD).pack(side="left")

        overview = movie.get("overview", "")
        if overview:
            short = overview[:160] + ("…" if len(overview) > 160 else "")
            tk.Label(info, text=short, font=("Helvetica", 9),
                     fg="#bbbbbb", bg=CARD, wraplength=360,
                     justify="left").pack(anchor="w")

        # Buttons
        btn_row = tk.Frame(info, bg=CARD)
        btn_row.pack(anchor="w", pady=(8, 0))
        if on_add:
            HoverButton(btn_row, "＋ Add to Watchlist", on_add,
                        bg=ACCENT, fg=TEXT, font_size=9, padx=12, pady=5
                        ).pack(side="left", padx=(0, 8))
        if show_remove and on_remove:
            HoverButton(btn_row, "✕ Remove", lambda: on_remove(movie["title"]),
                        bg="#333333", fg="#ff6b6b", font_size=9, padx=12, pady=5
                        ).pack(side="left")

        # Load poster async
        if movie.get("poster"):
            threading.Thread(target=self._load_poster,
                             args=(movie["poster"],), daemon=True).start()
        else:
            ph = make_placeholder()
            if ph:
                self._photo = ph
                self._poster_lbl.config(image=ph, text="")

    def _load_poster(self, path):
        photo = fetch_poster(path)
        if photo:
            self._photo = photo
            self._poster_lbl.after(0, lambda: self._poster_lbl.config(
                image=photo, text="", bg=CARD))
        else:
            ph = make_placeholder()
            if ph:
                self._photo = ph
                self._poster_lbl.after(0, lambda: self._poster_lbl.config(
                    image=ph, text="", bg=CARD))


class ScrollableFrame(tk.Frame):
    """A vertically scrollable container."""
    def __init__(self, master, **kw):
        super().__init__(master, bg=BG, **kw)
        canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        sb     = tk.Scrollbar(self, orient="vertical", command=canvas.yview,
                              bg=SURFACE, troughcolor=BG)
        self.inner = tk.Frame(canvas, bg=BG)
        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────────────────────────────
class MovieNightPickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Night Picker")
        self.root.geometry("820x680")
        self.root.minsize(820, 600)
        self.root.configure(bg=BG)
        self._search_results   = []
        self._discovered_movie = None
        init_db()
        self._build_ui()

    # ── SHELL ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_nav()
        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(fill="both", expand=True)
        self._pages = {}
        self._pages["discover"] = self._build_discover_page()
        self._pages["search"]   = self._build_search_page()
        self._pages["watchlist"]= self._build_watchlist_page()
        self._show_page("discover")

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=SURFACE, pady=0)
        hdr.pack(fill="x")
        inner = tk.Frame(hdr, bg=SURFACE)
        inner.pack(side="left", padx=24, pady=14)
        tk.Label(inner, text="🎬", font=("Helvetica", 20), bg=SURFACE,
                 fg=ACCENT).pack(side="left")
        tk.Label(inner, text="  MOVIE NIGHT PICKER", font=("Helvetica", 15, "bold"),
                 bg=SURFACE, fg=TEXT).pack(side="left")
        tk.Label(hdr, text="Powered by TMDB", font=("Helvetica", 9),
                 bg=SURFACE, fg=SUBTEXT).pack(side="right", padx=24)

    def _build_nav(self):
        nav = tk.Frame(self.root, bg=SURFACE)
        nav.pack(fill="x")
        sep = tk.Frame(self.root, bg=BORDER, height=1)
        sep.pack(fill="x")
        self._nav_btns = {}
        tabs = [("discover", "🎲  Discover"), ("search", "🔍  Search"), ("watchlist", "📋  Watchlist")]
        for key, label in tabs:
            btn = tk.Label(nav, text=label, font=("Helvetica", 10, "bold"),
                           bg=SURFACE, fg=SUBTEXT, padx=22, pady=10, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._show_page(k))
            btn.bind("<Enter>",    lambda e, b=btn: b.config(fg=TEXT) if b.cget("fg") != TEXT else None)
            btn.bind("<Leave>",    lambda e, b=btn, k=key: (
                b.config(fg=TEXT) if self._current_page == k else b.config(fg=SUBTEXT)))
            self._nav_btns[key] = btn
        self._current_page = None

    def _show_page(self, key):
        for k, p in self._pages.items():
            p.pack_forget()
        self._pages[key].pack(fill="both", expand=True)
        self._current_page = key
        for k, b in self._nav_btns.items():
            b.config(fg=TEXT if k == key else SUBTEXT,
                     bg=CARD  if k == key else SURFACE)
        if key == "watchlist":
            self._refresh_watchlist_page()

    # ── DISCOVER PAGE ─────────────────────────────────────────────────────────
    def _build_discover_page(self):
        page = tk.Frame(self.content, bg=BG)

        # Hero strip
        hero = tk.Frame(page, bg=SURFACE, pady=28)
        hero.pack(fill="x")
        tk.Label(hero, text="What should we watch tonight?",
                 font=("Helvetica", 20, "bold"), fg=TEXT, bg=SURFACE).pack()
        tk.Label(hero, text="Let us pick a random movie from TMDB — no watchlist needed.",
                 font=("Helvetica", 10), fg=SUBTEXT, bg=SURFACE).pack(pady=(4, 16))

        # Genre row
        gf = tk.Frame(hero, bg=SURFACE)
        gf.pack()
        tk.Label(gf, text="Genre:", font=("Helvetica", 10, "bold"),
                 fg=SUBTEXT, bg=SURFACE).pack(side="left", padx=(0, 8))
        self._disc_genre = tk.StringVar(value="Any Genre")
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.TCombobox",
                        fieldbackground=CARD, background=CARD,
                        foreground=TEXT, arrowcolor=TEXT,
                        selectbackground=CARD, selectforeground=TEXT)
        cb = ttk.Combobox(gf, textvariable=self._disc_genre,
                          values=["Any Genre"] + sorted(GENRE_MAP.keys()),
                          state="readonly", width=16,
                          font=("Helvetica", 10), style="Dark.TCombobox")
        cb.pack(side="left", padx=(0, 16))
        HoverButton(gf, "🎲  Surprise Me!", self._do_discover_thread,
                    bg=ACCENT, fg=TEXT, font_size=11, padx=22, pady=9).pack(side="left")

        # Result area
        self._disc_card_frame = tk.Frame(page, bg=BG)
        self._disc_card_frame.pack(fill="x", padx=30, pady=24)
        self._disc_placeholder = tk.Label(
            self._disc_card_frame,
            text="Hit  🎲 Surprise Me!  to get a random movie from TMDB",
            font=("Helvetica", 12), fg=SUBTEXT, bg=BG)
        self._disc_placeholder.pack(pady=40)

        return page

    def _do_discover_thread(self):
        for w in self._disc_card_frame.winfo_children():
            w.destroy()
        tk.Label(self._disc_card_frame, text="⏳  Fetching from TMDB…",
                 font=("Helvetica", 12), fg=SUBTEXT, bg=BG).pack(pady=40)
        threading.Thread(target=self._fetch_discover, daemon=True).start()

    def _fetch_discover(self):
        genre_name = self._disc_genre.get()
        genre_id   = GENRE_MAP.get(genre_name) if genre_name != "Any Genre" else None
        movie      = tmdb_random_movie(genre_id)
        self.root.after(0, lambda: self._show_discover_result(movie))

    def _show_discover_result(self, movie):
        for w in self._disc_card_frame.winfo_children():
            w.destroy()
        if not movie:
            tk.Label(self._disc_card_frame,
                     text="⚠️  Could not fetch a movie. Check your connection.",
                     font=("Helvetica", 11), fg="#ff6b6b", bg=BG).pack(pady=40)
            return
        self._discovered_movie = movie

        def add_it():
            if db_add(movie):
                messagebox.showinfo("Saved!", f'"{movie["title"]}" added to your watchlist 🎬')
            else:
                messagebox.showinfo("Already saved", f'"{movie["title"]}" is already in your watchlist.')

        card = MovieCard(self._disc_card_frame, movie, on_add=add_it)
        card.pack(fill="x", pady=4)

    # ── SEARCH PAGE ───────────────────────────────────────────────────────────
    def _build_search_page(self):
        page = tk.Frame(self.content, bg=BG)

        # Search bar strip
        bar = tk.Frame(page, bg=SURFACE, pady=20)
        bar.pack(fill="x")
        tk.Label(bar, text="Search for a Movie",
                 font=("Helvetica", 16, "bold"), fg=TEXT, bg=SURFACE).pack(pady=(0, 10))
        sf = tk.Frame(bar, bg=SURFACE)
        sf.pack()
        self._search_var = tk.StringVar()
        entry = tk.Entry(sf, textvariable=self._search_var,
                         font=("Helvetica", 12), bg=CARD, fg=TEXT,
                         insertbackground=TEXT, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT, width=32)
        entry.pack(side="left", ipady=8, padx=(0, 10))
        entry.bind("<Return>", lambda e: self._do_search_thread())
        HoverButton(sf, "Search", self._do_search_thread,
                    bg=ACCENT, fg=TEXT, font_size=11, padx=20, pady=8).pack(side="left")

        tk.Frame(page, bg=BORDER, height=1).pack(fill="x")

        # Results scrollable area
        self._search_scroll = ScrollableFrame(page)
        self._search_scroll.pack(fill="both", expand=True, padx=20, pady=16)
        self._search_status = tk.Label(self._search_scroll.inner,
                                       text="Search for a movie above to see results.",
                                       font=("Helvetica", 11), fg=SUBTEXT, bg=BG)
        self._search_status.pack(pady=30)
        return page

    def _do_search_thread(self):
        q = self._search_var.get().strip()
        if not q:
            messagebox.showwarning("Empty", "Please enter a movie title.")
            return
        for w in self._search_scroll.inner.winfo_children():
            w.destroy()
        tk.Label(self._search_scroll.inner, text="⏳  Searching TMDB…",
                 font=("Helvetica", 11), fg=SUBTEXT, bg=BG).pack(pady=30)
        threading.Thread(target=lambda: self._fetch_search(q), daemon=True).start()

    def _fetch_search(self, q):
        results = tmdb_search(q)
        self.root.after(0, lambda: self._show_search_results(results))

    def _show_search_results(self, results):
        for w in self._search_scroll.inner.winfo_children():
            w.destroy()
        if not results:
            tk.Label(self._search_scroll.inner, text="No results found.",
                     font=("Helvetica", 11), fg=SUBTEXT, bg=BG).pack(pady=30)
            return
        tk.Label(self._search_scroll.inner,
                 text=f"{len(results)} result(s) found",
                 font=("Helvetica", 10), fg=SUBTEXT, bg=BG).pack(anchor="w", pady=(0, 8))
        for movie in results:
            def make_adder(m=movie):
                def add():
                    if db_add(m):
                        messagebox.showinfo("Saved!", f'"{m["title"]}" added to watchlist 🎬')
                    else:
                        messagebox.showinfo("Already saved",
                                            f'"{m["title"]}" is already in your watchlist.')
                return add
            card = MovieCard(self._search_scroll.inner, movie, on_add=make_adder())
            card.pack(fill="x", pady=5)

    # ── WATCHLIST PAGE ────────────────────────────────────────────────────────
    def _build_watchlist_page(self):
        page = tk.Frame(self.content, bg=BG)

        # Top bar
        top = tk.Frame(page, bg=SURFACE, pady=16)
        top.pack(fill="x")
        left_top = tk.Frame(top, bg=SURFACE)
        left_top.pack(side="left", padx=24)
        tk.Label(left_top, text="My Watchlist",
                 font=("Helvetica", 16, "bold"), fg=TEXT, bg=SURFACE).pack(anchor="w")
        self._wl_count_lbl = tk.Label(left_top, text="0 movies saved",
                                      font=("Helvetica", 9), fg=SUBTEXT, bg=SURFACE)
        self._wl_count_lbl.pack(anchor="w")

        # Pick panel (right side of top bar)
        right_top = tk.Frame(top, bg=SURFACE)
        right_top.pack(side="right", padx=24)
        tk.Label(right_top, text="Pick from watchlist:",
                 font=("Helvetica", 9, "bold"), fg=SUBTEXT, bg=SURFACE).pack(anchor="e")
        prow = tk.Frame(right_top, bg=SURFACE)
        prow.pack(pady=(4, 0))
        self._wl_genre = tk.StringVar(value="All Genres")
        cb2 = ttk.Combobox(prow, textvariable=self._wl_genre,
                           values=["All Genres"] + sorted(GENRE_MAP.keys()),
                           state="readonly", width=14,
                           font=("Helvetica", 10), style="Dark.TCombobox")
        cb2.pack(side="left", padx=(0, 8))
        HoverButton(prow, "🎯 Pick!", self._pick_from_watchlist,
                    bg=ACCENT, fg=TEXT, font_size=10, padx=14, pady=6).pack(side="left")

        tk.Frame(page, bg=BORDER, height=1).pack(fill="x")

        # Pick result banner
        self._wl_pick_banner = tk.Frame(page, bg="#1a0a00")
        self._wl_pick_lbl    = tk.Label(self._wl_pick_banner, text="",
                                        font=("Helvetica", 11, "bold"),
                                        fg=ACCENT2, bg="#1a0a00", pady=10)
        self._wl_pick_lbl.pack()

        # Scrollable list
        self._wl_scroll = ScrollableFrame(page)
        self._wl_scroll.pack(fill="both", expand=True, padx=20, pady=12)
        self._wl_empty = tk.Label(self._wl_scroll.inner,
                                  text="Your watchlist is empty.\nSearch for movies and add them!",
                                  font=("Helvetica", 12), fg=SUBTEXT, bg=BG, justify="center")
        self._wl_empty.pack(pady=50)
        return page

    def _refresh_watchlist_page(self):
        for w in self._wl_scroll.inner.winfo_children():
            w.destroy()
        movies = db_all()
        self._wl_count_lbl.config(text=f"{len(movies)} movie{'s' if len(movies) != 1 else ''} saved")
        if not movies:
            tk.Label(self._wl_scroll.inner,
                     text="Your watchlist is empty.\nSearch for movies and add them!",
                     font=("Helvetica", 12), fg=SUBTEXT, bg=BG, justify="center").pack(pady=50)
            return
        for movie in movies:
            def make_remover(title):
                def remove():
                    if messagebox.askyesno("Remove", f'Remove "{title}" from your watchlist?'):
                        db_remove(title)
                        self._refresh_watchlist_page()
                        self._wl_pick_banner.pack_forget()
                return remove
            card = MovieCard(self._wl_scroll.inner, movie,
                             on_remove=make_remover(movie["title"]), show_remove=True)
            card.pack(fill="x", pady=5)

    def _pick_from_watchlist(self):
        genre = self._wl_genre.get()
        movie = db_random(genre if genre != "All Genres" else None)
        if not movie:
            msg = (f'No "{genre}" movies in your watchlist!'
                   if genre != "All Genres" else "Your watchlist is empty!")
            messagebox.showwarning("Nothing to pick", msg)
            return
        self._wl_pick_banner.pack(fill="x", after=self._wl_scroll.master.children.get(
            list(self._wl_scroll.master.children)[0], self._wl_scroll))
        # Re-pack in correct order: below top bar separator, above scroll
        self._wl_pick_banner.pack_forget()
        # Insert between separator and scroll
        self._wl_pick_lbl.config(
            text=f'🎬  Tonight\'s pick: "{movie["title"]}"  ({movie["year"]})  '
                 f'[{movie["genre"]}]  ⭐ {movie["rating"]}')
        self._wl_pick_banner.pack(fill="x")
        self._wl_scroll.pack(fill="both", expand=True, padx=20, pady=12)


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        from PIL import Image, ImageTk, ImageDraw
        PIL_OK = True
    except ImportError:
        PIL_OK = False

    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.3)
    except Exception:
        pass
    app = MovieNightPickerApp(root)
    root.mainloop()
