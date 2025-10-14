# BookWorm Setup Guide 📚

## How to Add a New Series

### Step 1: Find the Fandom Wiki

Examples:

- Harry Potter: `harrypotter.fandom.com`
- Wheel of Time: `wot.fandom.com`
- Stormlight Archive: `stormlightarchive.fandom.com`
- Mistborn: `mistborn.fandom.com`

### Step 2: Add to `SERIES_CONFIG` in `main.py`

```python
SERIES_CONFIG = {
    "RedRising": {
        "wiki": "red-rising.fandom.com",
        "pages": [...],
        "book_names": ["Red Rising", "Golden Son", ...]
    },

    # ADD YOUR NEW SERIES HERE:
    "HarryPotter": {
        "wiki": "harrypotter.fandom.com",
        "pages": [
            {"title": "Harry_Potter_and_the_Philosopher's_Stone", "type": "books", "name": "Philosopher's Stone", "book_number": 1},
            {"title": "Harry_Potter_and_the_Chamber_of_Secrets", "type": "books", "name": "Chamber of Secrets", "book_number": 2},
            {"title": "Harry_Potter_and_the_Prisoner_of_Azkaban", "type": "books", "name": "Prisoner of Azkaban", "book_number": 3},
            {"title": "Harry_Potter_and_the_Goblet_of_Fire", "type": "books", "name": "Goblet of Fire", "book_number": 4},
            {"title": "Harry_Potter_and_the_Order_of_the_Phoenix", "type": "books", "name": "Order of the Phoenix", "book_number": 5},
            {"title": "Harry_Potter_and_the_Half-Blood_Prince", "type": "books", "name": "Half-Blood Prince", "book_number": 6},
            {"title": "Harry_Potter_and_the_Deathly_Hallows", "type": "books", "name": "Deathly Hallows", "book_number": 7},
            # Characters
            {"title": "Harry_Potter", "type": "characters", "name": "Harry Potter", "book_number": None},
            {"title": "Hermione_Granger", "type": "characters", "name": "Hermione Granger", "book_number": None},
            {"title": "Ron_Weasley", "type": "characters", "name": "Ron Weasley", "book_number": None},
        ],
        "book_names": [
            "Philosopher's Stone",
            "Chamber of Secrets",
            "Prisoner of Azkaban",
            "Goblet of Fire",
            "Order of the Phoenix",
            "Half-Blood Prince",
            "Deathly Hallows"
        ]
    }
}
```

### Step 3: Find Page Titles

Go to the wiki and find the exact page titles:

1. Visit: `https://[wiki-name].fandom.com`
2. Search for a book/character page
3. Look at the URL: `https://harrypotter.fandom.com/wiki/Harry_Potter`
   - Page title = `Harry_Potter`

### Step 4: Run the Script

```bash
python3 app/main.py
```

That's it! 🎉

---

## Configuration Format

### Required Fields

```python
{
    "SeriesName": {  # Use CamelCase, no spaces (this becomes the folder name)
        "wiki": "wiki-name.fandom.com",  # The Fandom wiki domain
        "pages": [  # List of pages to scrape
            {
                "title": "Page_Title_From_URL",  # Exact title from wiki URL
                "type": "books|characters|events|locations",  # Category
                "name": "Display Name",  # Human-readable name
                "book_number": 1  # Order in series (or None for characters)
            },
            # ... more pages
        ],
        "book_names": [  # List of book names in order (for detection)
            "Book 1 Name",
            "Book 2 Name",
            # ... must match "name" field in books
        ]
    }
}
```

---

## Examples of Other Series

### Mistborn

```python
"Mistborn": {
    "wiki": "mistborn.fandom.com",
    "pages": [
        {"title": "The_Final_Empire", "type": "books", "name": "The Final Empire", "book_number": 1},
        {"title": "The_Well_of_Ascension", "type": "books", "name": "The Well of Ascension", "book_number": 2},
        {"title": "The_Hero_of_Ages", "type": "books", "name": "The Hero of Ages", "book_number": 3},
        {"title": "Vin", "type": "characters", "name": "Vin", "book_number": None},
        {"title": "Kelsier", "type": "characters", "name": "Kelsier", "book_number": None},
    ],
    "book_names": ["The Final Empire", "The Well of Ascension", "The Hero of Ages"]
}
```

### Stormlight Archive

```python
"StormlightArchive": {
    "wiki": "stormlightarchive.fandom.com",
    "pages": [
        {"title": "The_Way_of_Kings", "type": "books", "name": "The Way of Kings", "book_number": 1},
        {"title": "Words_of_Radiance", "type": "books", "name": "Words of Radiance", "book_number": 2},
        {"title": "Oathbringer", "type": "books", "name": "Oathbringer", "book_number": 3},
        {"title": "Rhythm_of_War", "type": "books", "name": "Rhythm of War", "book_number": 4},
        {"title": "Kaladin", "type": "characters", "name": "Kaladin", "book_number": None},
        {"title": "Shallan_Davar", "type": "characters", "name": "Shallan Davar", "book_number": None},
    ],
    "book_names": ["The Way of Kings", "Words of Radiance", "Oathbringer", "Rhythm of War"]
}
```

---

## Output Structure

After running, your data will be organized as:

```
app/data/
├── RedRising/
│   ├── books/
│   │   ├── Red Rising.json
│   │   ├── Golden Son.json
│   │   └── ...
│   └── characters/
│       └── Darrow OLykos.json
├── HarryPotter/
│   ├── books/
│   │   ├── Philosophers Stone.json
│   │   ├── Chamber of Secrets.json
│   │   └── ...
│   └── characters/
│       ├── Harry Potter.json
│       ├── Hermione Granger.json
│       └── ...
└── Mistborn/
    ├── books/
    └── characters/
```

---

## Features That Work Universally

### ✅ Automatic Book Detection for Characters

The system will automatically detect which book character information comes from:

```json
{
  "text": "Harry first learned about Horcruxes in Half-Blood Prince...",
  "section": "Half-Blood Prince",
  "book_number": 6, // ← Auto-detected!
  "source_book": "Half-Blood Prince"
}
```

### ✅ Spoiler Prevention

Works the same for all series:

```python
# User is reading book 3 of Harry Potter
results = collection.query(
    query_texts=["Tell me about Dumbledore"],
    where={
        "$and": [
            {"series": "HarryPotter"},
            {"book_number": {"$lte": 3}}  # Only books 1-3
        ]
    }
)
```

### ✅ Optimal Chunk Sizes

- Max 400 words target
- Hard limit 600 words
- Works for any text content

### ✅ Rich Metadata

Every chunk includes:

- `series`: Which series (e.g., "HarryPotter")
- `book_number`: Which book (1, 2, 3...)
- `source_book`: Book name
- `type`: books/characters/events/locations
- `name`: Entity name
- `section`: Section within source

---

## Tips for Finding Good Pages

### Books

- Look for main book pages with plot summaries
- Usually have titles like `Book_Name_(Novel)` or just `Book_Name`

### Characters

- Main character pages work best
- Usually have biography/history sections organized by book

### What NOT to Include

- ❌ Short stub pages
- ❌ Disambiguation pages
- ❌ Category pages
- ❌ Meta/wiki administration pages

### What DOES Work Well

- ✅ Book pages with plot summaries
- ✅ Major character pages with detailed histories
- ✅ Important location pages
- ✅ Major event pages

---

## Testing Your Configuration

1. **Start small**: Add just 1-2 books first
2. **Check output**: Look at the generated JSON files
3. **Verify metadata**: Make sure `book_number` and `source_book` are correct
4. **Add more**: Once it works, add remaining books and characters

---

## Troubleshooting

### "No content found"

- Check if the page title is exact (case-sensitive, underscores not spaces)
- Visit the wiki URL directly: `https://[wiki]/wiki/[title]`

### Book detection not working for characters

- Make sure book names in `book_names` list match the `name` field in book pages
- Check if character page sections contain the book names

### Chunks still too large

- Some wikis have different formatting
- May need to adjust `max_words` in `SERIES_CONFIG` (advanced)

---

## Advanced: Per-Series Chunking Settings (Optional)

If a series has very dense or sparse text, you can customize:

```python
"SeriesName": {
    "wiki": "...",
    "pages": [...],
    "book_names": [...],
    "chunking": {  # Optional!
        "max_words": 300,      # Smaller chunks
        "max_paragraphs": 3,   # Fewer paragraphs
        "hard_max_words": 500  # Stricter limit
    }
}
```

---

## Your Code is Production-Ready! 🚀

✅ Multi-series support  
✅ Automatic book detection  
✅ Spoiler prevention  
✅ Optimal chunking  
✅ Rich metadata  
✅ Scalable to unlimited series

Just add series to `SERIES_CONFIG` and run! 🎉
