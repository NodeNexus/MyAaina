import pandas as pd
import json
import os
from functools import reduce
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.csv')
PROFILE_FILE  = os.path.join(DATA_DIR, 'user_profile.json')
HISTORY_FILE  = os.path.join(DATA_DIR, 'purchase_history.csv')
WISHLIST_FILE = os.path.join(DATA_DIR, 'wishlist.json')

SIZE_ORDER = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
SKIN_TONE_COLOR_PREFERENCES = {
    'Fair': {'red', 'maroon', 'emerald', 'green', 'lavender', 'black', 'blue', 'navy', 'pink', 'navy blue'},
    'Wheatish': {'mustard', 'teal', 'maroon', 'navy', 'olive', 'cream', 'rust', 'purple', 'navy blue'},
    'Dusky': {'white', 'mustard', 'magenta', 'teal', 'rust', 'pink', 'yellow', 'gold'},
    'Dark': {'white', 'yellow', 'green', 'emerald', 'blue', 'royal blue', 'orange', 'gold', 'red', 'cream'},
}
BODY_TYPE_CATEGORY_PREFERENCES = {
    'Slim': {'lehenga', 'saree', 'kurti', 'kurtis', 'indo-western'},
    'Athletic': {'sherwani', 'indo-western', 'nehru jacket', 'bandhgala', 'dhoti'},
    'Curvy': {'saree', 'salwar', 'lehenga'},
    'Plus Size': {'salwar', 'saree', 'kurta sets'},
    'Petite': {'kurti', 'kurtis', 'indo-western'},
}


# ─── User Profile ────────────────────────────────────────────────────────────
class User:
    def __init__(self, name, age, gender, body_type, skin_tone,
                 size, budget_min, budget_max, interests):
        self.name       = name
        self.age        = int(age)
        self.gender     = gender
        self.body_type  = body_type
        self.skin_tone  = skin_tone
        self.size       = size
        self.budget_min = int(budget_min)
        self.budget_max = int(budget_max)
        self.interests  = interests  # list of occasion strings

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(d):
        return User(**d)


def save_profile(user: User):
    with open(PROFILE_FILE, 'w') as f:
        json.dump(user.to_dict(), f, indent=2)


def load_profile():
    try:
        with open(PROFILE_FILE, 'r') as f:
            data = json.load(f)
        if not data:
            return None
        return User.from_dict(data)
    except (FileNotFoundError, KeyError, TypeError):
        return None


# ─── Clothing Item ────────────────────────────────────────────────────────────
class ClothingItem:
    def __init__(self, row):
        self.id             = row['id']
        self.name           = row['name']
        self.category       = row['category']
        self.occasion       = row['occasion']
        self.platform       = row['platform']
        self.price          = float(row['price'])
        self.quality_rating = float(row['quality_rating'])
        self.delivery_days  = int(row['delivery_days'])
        self.color          = row['color']
        self.size           = row['size']
        self.gender         = row['gender']
        self.description    = row.get('description', '')
        self.image_keyword  = row.get('image_keyword', 'indian clothing')

    def to_dict(self):
        return self.__dict__


# ─── Wishlist ─────────────────────────────────────────────────────────────────
def load_wishlist():
    try:
        with open(WISHLIST_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_wishlist(items: list):
    with open(WISHLIST_FILE, 'w') as f:
        json.dump(items, f, indent=2)


def toggle_wishlist(item_id: int):
    """Add if not present, remove if present. Returns True if added."""
    wishlist = load_wishlist()
    if item_id in wishlist:
        wishlist.remove(item_id)
        save_wishlist(wishlist)
        return False
    else:
        wishlist.append(item_id)
        save_wishlist(wishlist)
        return True


# ─── Purchase History ─────────────────────────────────────────────────────────
def log_purchase(item_id, item_payload=None):
    try:
        if item_payload:
            item = pd.DataFrame([item_payload])
        else:
            df   = pd.read_csv(PRODUCTS_FILE)
            item = df[df['id'] == int(item_id)]
            if item.empty:
                raise ValueError("Product not found")
        if os.path.exists(HISTORY_FILE):
            history = pd.read_csv(HISTORY_FILE)
        else:
            history = pd.DataFrame(columns=item.columns if not item.empty else [])
        history = pd.concat([history, item], ignore_index=True)
        history.to_csv(HISTORY_FILE, index=False)
        return True
    except Exception as e:
        print(f"Error logging purchase: {e}")
        return False


def get_purchase_history():
    try:
        if not os.path.exists(HISTORY_FILE):
            return []
        df = pd.read_csv(HISTORY_FILE)
        return df.to_dict(orient='records')
    except Exception:
        return []


def remove_from_history(item_id: int):
    try:
        if not os.path.exists(HISTORY_FILE):
            return False
        df = pd.read_csv(HISTORY_FILE)
        df = df[df['id'] != item_id]
        df.to_csv(HISTORY_FILE, index=False)
        return True
    except Exception:
        return False


def get_category_stats():
    """Returns category counts for pie chart"""
    try:
        if not os.path.exists(HISTORY_FILE):
            return {}
        df = pd.read_csv(HISTORY_FILE)
        if df.empty:
            return {}
        counts = df['category'].value_counts().to_dict()
        return counts
    except Exception:
        return {}


def get_spend_timeline():
    """Returns spend grouped by a rolling purchase index (simulated date)"""
    try:
        if not os.path.exists(HISTORY_FILE):
            return {}
        df = pd.read_csv(HISTORY_FILE)
        if df.empty:
            return {}
        df = df.reset_index()
        grouped = df.groupby('index')['price'].sum().to_dict()
        # rename keys to "Purchase N"
        return {f"#{k+1}": v for k, v in grouped.items()}
    except Exception:
        return {}


def get_platform_spend():
    """Total spend per platform"""
    try:
        if not os.path.exists(HISTORY_FILE):
            return {}
        df = pd.read_csv(HISTORY_FILE)
        if df.empty:
            return {}
        return df.groupby('platform')['price'].sum().round(2).to_dict()
    except Exception:
        return {}


# ─── Recommender ──────────────────────────────────────────────────────────────
class Recommender:
    def __init__(self):
        self._load_data()

    def _load_data(self):
        self.df = pd.read_csv(PRODUCTS_FILE)

    def reload(self):
        self._load_data()

    def recommend(self, user: User, occasion: str, sort_by: str = 'price', limit: int = 12):
        df = self.df.copy()

        # Filter by occasion and gender first
        df = df[df['occasion'].str.lower() == occasion.lower()]
        df = df[df['gender'].str.lower() == user.gender.lower()]

        if df.empty:
            return []

        scored_rows = []
        for _, row in df.iterrows():
            item = row.to_dict()
            size_penalty = self._size_penalty(user.size, item['size'])
            budget_penalty = self._budget_penalty(user.budget_min, user.budget_max, item['price'])
            profile_penalty = self._profile_penalty(user, item, occasion)
            match_reason = self._match_reason(size_penalty, budget_penalty, profile_penalty)
            
            scored_rows.append({
                **item,
                '_size_penalty': size_penalty,
                '_budget_penalty': budget_penalty,
                '_profile_penalty': profile_penalty,
                '_match_reason': match_reason,
            })

        ranked = pd.DataFrame(scored_rows)
        ranked = self._sort_ranked(ranked, sort_by)

        wishlist = load_wishlist()
        results  = []
        for _, row in ranked.iterrows():
            item      = ClothingItem(row).to_dict()
            item['in_wishlist'] = int(item['id']) in wishlist
            item['match_reason'] = row['_match_reason']
            results.append(item)
            if len(results) >= limit:
                break
        return results

    def _sort_ranked(self, df, sort_by):
        sort_columns = ['_budget_penalty', '_size_penalty', '_profile_penalty']
        ascending = [True, True, True]

        if sort_by == 'price':
            sort_columns.append('price')
            ascending.append(True)
        elif sort_by == 'quality':
            sort_columns.append('quality_rating')
            ascending.append(False)
        elif sort_by == 'delivery':
            sort_columns.append('delivery_days')
            ascending.append(True)
        else:
            sort_columns.append('price')
            ascending.append(True)

        sort_columns.append('id')
        ascending.append(True)
        return df.sort_values(sort_columns, ascending=ascending)

    def _size_penalty(self, user_size, item_size):
        if item_size == 'Free Size':
            return 0.05
        if item_size == user_size:
            return 0.0
        if user_size not in SIZE_ORDER or item_size not in SIZE_ORDER:
            return 0.8
        distance = abs(SIZE_ORDER.index(user_size) - SIZE_ORDER.index(item_size))
        return 0.25 * distance

    def _budget_penalty(self, budget_min, budget_max, price):
        if budget_min <= price <= budget_max:
            return 0.0
        if price < budget_min:
            return round((budget_min - price) / max(budget_min, 1), 3)
        return round((price - budget_max) / max(budget_max, 1), 3)

    def _profile_penalty(self, user, item, occasion):
        penalty = 0.0
        preferred_colors = SKIN_TONE_COLOR_PREFERENCES.get(user.skin_tone, set())
        color = str(item.get('color') or '').strip().lower()
        if preferred_colors and color not in preferred_colors:
            penalty += 0.18

        preferred_categories = BODY_TYPE_CATEGORY_PREFERENCES.get(user.body_type, set())
        category_text = ' '.join([
            str(item.get('category') or '').strip().lower(),
            str(item.get('name') or '').strip().lower(),
        ])
        if preferred_categories and not any(pref in category_text for pref in preferred_categories):
            penalty += 0.22

        if user.interests and occasion not in user.interests:
            penalty += 0.08
        return round(penalty, 3)

    def _match_reason(self, size_penalty, budget_penalty, profile_penalty):
        if size_penalty <= 0.05 and budget_penalty == 0:
            return 'Exact match' if profile_penalty <= 0.12 else 'Good match'
        if budget_penalty == 0:
            return 'More sizes' if profile_penalty <= 0.12 else 'Style compromise'
        if size_penalty <= 0.05:
            return 'Budget stretch'
        return 'Close match'

    def get_price_comparison(self, occasion: str):
        df = self.df[self.df['occasion'].str.lower() == occasion.lower()]
        if df.empty:
            return {}
        return df.groupby('platform')['price'].mean().round(2).to_dict()

    def get_quality_comparison(self, occasion: str):
        df = self.df[self.df['occasion'].str.lower() == occasion.lower()]
        if df.empty:
            return {}
        return df.groupby('platform')['quality_rating'].mean().round(2).to_dict()

    def get_delivery_comparison(self, occasion: str):
        df = self.df[self.df['occasion'].str.lower() == occasion.lower()]
        if df.empty:
            return {}
        return df.groupby('platform')['delivery_days'].mean().round(1).to_dict()

    def search(self, query: str, user: User = None):
        """Full-text search across name, category, color, description"""
        df  = self.df.copy()
        q   = query.lower()
        mask = (
            df['name'].str.lower().str.contains(q, na=False) |
            df['category'].str.lower().str.contains(q, na=False) |
            df['color'].str.lower().str.contains(q, na=False) |
            df.get('description', pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
        )
        df = df[mask]
        if user:
            df = df[df['gender'].str.lower() == user.gender.lower()]
        wishlist = load_wishlist()
        results  = []
        for _, row in df.iterrows():
            item = ClothingItem(row).to_dict()
            item['in_wishlist'] = int(item['id']) in wishlist
            results.append(item)
        return results

    def get_trending(self, limit: int = 8):
        """Returns top-rated products across all categories"""
        df = self.df.copy().sort_values('quality_rating', ascending=False).head(limit)
        wishlist = load_wishlist()
        results  = []
        for _, row in df.iterrows():
            item = ClothingItem(row).to_dict()
            item['in_wishlist'] = int(item['id']) in wishlist
            results.append(item)
        return results

    def get_budget_deals(self, budget_max: int = 1000, limit: int = 8):
        """Returns best-quality products under a given budget"""
        df = self.df[self.df['price'] <= budget_max].sort_values('quality_rating', ascending=False).head(limit)
        wishlist = load_wishlist()
        results  = []
        for _, row in df.iterrows():
            item = ClothingItem(row).to_dict()
            item['in_wishlist'] = int(item['id']) in wishlist
            results.append(item)
        return results

    def get_all_occasions(self):
        return sorted(self.df['occasion'].dropna().unique().tolist())

    def get_all_categories(self):
        return sorted(self.df['category'].dropna().unique().tolist())

    def get_stats(self):
        """Overall catalog stats"""
        return {
            'total_products': len(self.df),
            'total_categories': self.df['category'].nunique(),
            'total_platforms': self.df['platform'].nunique(),
            'avg_price': round(self.df['price'].mean(), 2),
            'avg_quality': round(self.df['quality_rating'].mean(), 2),
            'price_range': [int(self.df['price'].min()), int(self.df['price'].max())],
        }
