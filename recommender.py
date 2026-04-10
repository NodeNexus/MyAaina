import pandas as pd
import json
import os
from functools import reduce
<<<<<<< HEAD

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.csv')
PROFILE_FILE = os.path.join(DATA_DIR, 'user_profile.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'purchase_history.csv')


# ─── User Profile ────────────────────────────────────────────────
class User:
    def __init__(self, name, age, gender, body_type, skin_tone, size, budget_min, budget_max, interests):
        self.name = name
        self.age = age
        self.gender = gender
        self.body_type = body_type
        self.skin_tone = skin_tone
        self.size = size
        self.budget_min = budget_min
        self.budget_max = budget_max
        self.interests = interests  # list of occasions they like
=======
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.csv')
PROFILE_FILE  = os.path.join(DATA_DIR, 'user_profile.json')
HISTORY_FILE  = os.path.join(DATA_DIR, 'purchase_history.csv')
WISHLIST_FILE = os.path.join(DATA_DIR, 'wishlist.json')


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
>>>>>>> 5734a39 (Upgrade project to max level, fix issues, and overhaul UI)

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


<<<<<<< HEAD
# ─── Clothing Item ────────────────────────────────────────────────
class ClothingItem:
    def __init__(self, row):
        self.id = row['id']
        self.name = row['name']
        self.category = row['category']
        self.occasion = row['occasion']
        self.platform = row['platform']
        self.price = row['price']
        self.quality_rating = row['quality_rating']
        self.delivery_days = row['delivery_days']
        self.color = row['color']
        self.size = row['size']
        self.gender = row['gender']
=======
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
>>>>>>> 5734a39 (Upgrade project to max level, fix issues, and overhaul UI)

    def to_dict(self):
        return self.__dict__


<<<<<<< HEAD
# ─── Purchase History ─────────────────────────────────────────────
def log_purchase(item_id):
    try:
        df = pd.read_csv(PRODUCTS_FILE)
        item = df[df['id'] == int(item_id)]
        if item.empty:
            raise ValueError("Product not found")

        if os.path.exists(HISTORY_FILE):
            history = pd.read_csv(HISTORY_FILE)
        else:
            history = pd.DataFrame()

=======
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
def log_purchase(item_id):
    try:
        df   = pd.read_csv(PRODUCTS_FILE)
        item = df[df['id'] == int(item_id)]
        if item.empty:
            raise ValueError("Product not found")
        if os.path.exists(HISTORY_FILE):
            history = pd.read_csv(HISTORY_FILE)
        else:
            history = pd.DataFrame(columns=df.columns)
>>>>>>> 5734a39 (Upgrade project to max level, fix issues, and overhaul UI)
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


<<<<<<< HEAD
=======
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


>>>>>>> 5734a39 (Upgrade project to max level, fix issues, and overhaul UI)
def get_category_stats():
    """Returns category counts for pie chart"""
    try:
        if not os.path.exists(HISTORY_FILE):
            return {}
        df = pd.read_csv(HISTORY_FILE)
<<<<<<< HEAD
=======
        if df.empty:
            return {}
>>>>>>> 5734a39 (Upgrade project to max level, fix issues, and overhaul UI)
        counts = df['category'].value_counts().to_dict()
        return counts
    except Exception:
        return {}


<<<<<<< HEAD
# ─── Recommender ──────────────────────────────────────────────────
class Recommender:
    def __init__(self):
        self.df = pd.read_csv(PRODUCTS_FILE)

=======
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

>>>>>>> 5734a39 (Upgrade project to max level, fix issues, and overhaul UI)
    def recommend(self, user: User, occasion: str, sort_by: str = 'price'):
        df = self.df.copy()

        # Filter by occasion
        df = df[df['occasion'].str.lower() == occasion.lower()]

        # Filter by gender
        df = df[df['gender'].str.lower() == user.gender.lower()]

        # Filter by budget using lambda
<<<<<<< HEAD
        df = df[df['price'].apply(lambda p: user.budget_min <= p <= user.budget_max)]
=======
        df = df[df['price'].apply(lambda p: user.budget_min <= float(p) <= user.budget_max)]
>>>>>>> 5734a39 (Upgrade project to max level, fix issues, and overhaul UI)

        # Filter by size using filter()
        size_match = list(filter(
            lambda row: row['size'] in [user.size, 'Free Size'],
            df.to_dict(orient='records')
        ))
        df = pd.DataFrame(size_match)

        if df.empty:
            return []

<<<<<<< HEAD
        # Sort based on user preference
=======
        # Compute a composite score
        if not df.empty:
            price_norm   = 1 - (df['price'] - df['price'].min()) / (df['price'].max() - df['price'].min() + 1)
            quality_norm = (df['quality_rating'] - df['quality_rating'].min()) / (df['quality_rating'].max() - df['quality_rating'].min() + 1)
            delivery_norm = 1 - (df['delivery_days'] - df['delivery_days'].min()) / (df['delivery_days'].max() - df['delivery_days'].min() + 1)
            df['score'] = (price_norm * 0.4) + (quality_norm * 0.4) + (delivery_norm * 0.2)

>>>>>>> 5734a39 (Upgrade project to max level, fix issues, and overhaul UI)
        if sort_by == 'price':
            df = df.sort_values('price', ascending=True)
        elif sort_by == 'quality':
            df = df.sort_values('quality_rating', ascending=False)
        elif sort_by == 'delivery':
            df = df.sort_values('delivery_days', ascending=True)
<<<<<<< HEAD

        # Use list comprehension to build result
        results = [ClothingItem(row).to_dict() for _, row in df.iterrows()]
        return results

    def get_price_comparison(self, occasion: str):
        """Average price per platform for charts"""
        df = self.df[self.df['occasion'].str.lower() == occasion.lower()]
        if df.empty:
            return {}
        avg = df.groupby('platform')['price'].mean().round(2).to_dict()
        return avg

    def get_quality_comparison(self, occasion: str):
        """Average quality per platform for charts"""
        df = self.df[self.df['occasion'].str.lower() == occasion.lower()]
        if df.empty:
            return {}
        avg = df.groupby('platform')['quality_rating'].mean().round(2).to_dict()
        return avg
=======
        elif sort_by == 'score':
            df = df.sort_values('score', ascending=False)

        wishlist = load_wishlist()
        results  = []
        for _, row in df.iterrows():
            item      = ClothingItem(row).to_dict()
            item['in_wishlist'] = int(item['id']) in wishlist
            results.append(item)
        return results

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
>>>>>>> 5734a39 (Upgrade project to max level, fix issues, and overhaul UI)
