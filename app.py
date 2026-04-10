from flask import Flask, render_template, request, jsonify
from recommender import (
    User, Recommender,
    save_profile, load_profile,
    log_purchase, get_purchase_history,
    get_category_stats, get_spend_timeline,
    get_platform_spend, remove_from_history,
    toggle_wishlist, load_wishlist,
    get_purchase_history
)

app = Flask(__name__)
recommender = Recommender()


# ─── Pages ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    profile = load_profile()
    catalog_stats = recommender.get_stats()
    return render_template('index.html', profile=profile, catalog_stats=catalog_stats)


# ─── Profile ─────────────────────────────────────────────────────────────────
@app.route('/api/save-profile', methods=['POST'])
def save_profile_route():
    try:
        data = request.json
        user = User(
            name=data['name'],
            age=int(data['age']),
            gender=data['gender'],
            body_type=data['body_type'],
            skin_tone=data['skin_tone'],
            size=data['size'],
            budget_min=int(data['budget_min']),
            budget_max=int(data['budget_max']),
            interests=data.get('interests', [])
        )
        save_profile(user)
        return jsonify({'success': True, 'message': f'Profile saved for {user.name}!'})
    except (KeyError, ValueError) as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/profile', methods=['GET'])
def get_profile():
    profile = load_profile()
    if profile:
        return jsonify({'success': True, 'profile': profile.to_dict()})
    return jsonify({'success': False, 'message': 'No profile found'}), 404


# ─── Recommendations ──────────────────────────────────────────────────────────
@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data    = request.json
        profile = load_profile()
        if not profile:
            return jsonify({'success': False, 'message': 'Please create your profile first!'}), 400

        occasion = data.get('occasion', '')
        sort_by  = data.get('sort_by', 'price')

        if not occasion:
            return jsonify({'success': False, 'message': 'Please select an occasion!'}), 400

        results          = recommender.recommend(profile, occasion, sort_by)
        price_chart      = recommender.get_price_comparison(occasion)
        quality_chart    = recommender.get_quality_comparison(occasion)
        delivery_chart   = recommender.get_delivery_comparison(occasion)

        return jsonify({
            'success': True,
            'results': results,
            'price_chart': price_chart,
            'quality_chart': quality_chart,
            'delivery_chart': delivery_chart,
            'occasion': occasion,
            'user': profile.name
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── Search ───────────────────────────────────────────────────────────────────
@app.route('/api/search', methods=['GET'])
def search():
    try:
        q       = request.args.get('q', '').strip()
        profile = load_profile()
        if not q:
            return jsonify({'success': False, 'message': 'Empty query'}), 400
        results = recommender.search(q, profile)
        return jsonify({'success': True, 'results': results, 'query': q})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── Trending & Deals ────────────────────────────────────────────────────────
@app.route('/api/trending', methods=['GET'])
def trending():
    try:
        results = recommender.get_trending(limit=12)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/deals', methods=['GET'])
def deals():
    try:
        budget  = int(request.args.get('budget', 1000))
        results = recommender.get_budget_deals(budget_max=budget, limit=12)
        return jsonify({'success': True, 'results': results, 'budget': budget})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── Catalog Meta ─────────────────────────────────────────────────────────────
@app.route('/api/catalog/stats', methods=['GET'])
def catalog_stats():
    try:
        return jsonify({'success': True, 'stats': recommender.get_stats()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/catalog/occasions', methods=['GET'])
def catalog_occasions():
    return jsonify({'success': True, 'occasions': recommender.get_all_occasions()})


@app.route('/api/catalog/categories', methods=['GET'])
def catalog_categories():
    return jsonify({'success': True, 'categories': recommender.get_all_categories()})


# ─── Wishlist ─────────────────────────────────────────────────────────────────
@app.route('/api/wishlist/toggle', methods=['POST'])
def wishlist_toggle():
    try:
        data    = request.json
        item_id = int(data.get('item_id'))
        added   = toggle_wishlist(item_id)
        msg     = 'Added to Wishlist ❤️' if added else 'Removed from Wishlist'
        return jsonify({'success': True, 'added': added, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/wishlist', methods=['GET'])
def get_wishlist():
    try:
        ids     = load_wishlist()
        if not ids:
            return jsonify({'success': True, 'items': []})
        import pandas as pd, os
        df      = pd.read_csv(os.path.join(os.path.dirname(__file__), 'data', 'products.csv'))
        items   = df[df['id'].isin(ids)].to_dict(orient='records')
        for item in items:
            item['in_wishlist'] = True
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── Purchase History ─────────────────────────────────────────────────────────
@app.route('/api/log-purchase', methods=['POST'])
def log_purchase_route():
    try:
        data    = request.json
        item_id = data.get('item_id')
        success = log_purchase(item_id)
        if success:
            return jsonify({'success': True, 'message': 'Purchase logged!'})
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def history():
    try:
        items         = get_purchase_history()
        stats         = get_category_stats()
        spend_timeline = get_spend_timeline()
        platform_spend = get_platform_spend()
        total_spend   = sum(float(i.get('price', 0)) for i in items)
        return jsonify({
            'success': True,
            'items': items,
            'stats': stats,
            'spend_timeline': spend_timeline,
            'platform_spend': platform_spend,
            'total_spend': round(total_spend, 2),
            'total_items': len(items)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/history/remove', methods=['POST'])
def history_remove():
    try:
        data    = request.json
        item_id = int(data.get('item_id'))
        success = remove_from_history(item_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
