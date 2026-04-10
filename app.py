import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from flask import Flask, render_template, request, jsonify, Response

from manyavar_service import ManyavarService
from myntra_service import MyntraService
from savana_service import SavanaService

from recommender import (
    User, Recommender,
    save_profile, load_profile,
    log_purchase, get_purchase_history,
    get_category_stats, get_spend_timeline,
    get_platform_spend, remove_from_history,
    toggle_wishlist, load_wishlist
)

app = Flask(__name__)
recommender = Recommender()
myntra_service = MyntraService()
savana_service = SavanaService()
manyavar_service = ManyavarService()


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

        try:
            live_results = myntra_service.fetch_recommendations(profile, occasion, sort_by, limit=24)
        except Exception:
            live_results = []

        try:
            savana_results = savana_service.fetch_recommendations(profile, occasion, sort_by, limit=18)
        except Exception:
            savana_results = []

        try:
            manyavar_limit = 30 if occasion == 'Wedding' else 18
            manyavar_results = manyavar_service.fetch_recommendations(profile, occasion, sort_by, limit=manyavar_limit)
        except Exception:
            manyavar_results = []
        
        local_results = [
            item for item in recommender.recommend(profile, occasion, sort_by, limit=30)
            if item.get('platform') != 'Meesho'
        ]

        if occasion == 'Wedding':
            sources = [manyavar_results[:12], manyavar_results[12:], live_results, local_results]
        else:
            sources = [live_results, savana_results, manyavar_results, local_results]

        results = merge_results(*sources, limit=24)
        chart_results = merge_results(*sources, limit=48)

        price_chart      = build_platform_chart(chart_results, 'price')
        quality_chart    = build_platform_chart(chart_results, 'quality_rating')
        delivery_chart   = build_platform_chart(chart_results, 'delivery_days')

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
        item_payload = data.get('item')
        success = log_purchase(item_id, item_payload)
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


@app.route('/api/image-proxy', methods=['GET'])
def image_proxy():
    try:
        image_url = request.args.get('url', '').strip()
        if not image_url.startswith(('http://', 'https://')):
            return jsonify({'success': False, 'message': 'Invalid image URL'}), 400

        parsed = urlparse(image_url)
        referer_map = {
            'myntra.com': 'https://www.myntra.com/',
            'manyavar.com': 'https://www.manyavar.com/',
            'savana.com': 'https://www.savana.com/',
        }

        referer = None
        for domain, value in referer_map.items():
            if domain in parsed.netloc:
                referer = value
                break

        headers = {'User-Agent': 'Mozilla/5.0'}
        if referer:
            headers['Referer'] = referer

        req = Request(image_url, headers=headers)
        with urlopen(req, timeout=25) as response:
            content = response.read()
            mimetype = response.headers.get_content_type()

        return Response(
            content,
            mimetype=mimetype,
            headers={'Cache-Control': 'public, max-age=21600'}
        )
    except Exception:
        # Return a 1x1 transparent PNG so the browser shows a blank pixel
        # instead of "HTTP Error 471" or a broken image
        import base64
        pixel = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQAB'
            'Nl7BcQAAAABJRU5ErkJggg=='
        )
        return Response(pixel, mimetype='image/png', headers={'Cache-Control': 'public, max-age=60'})


def merge_results(*result_sets, limit=12):
    merged = []
    seen = set()
    buckets = [list(result_set) for result_set in result_sets if result_set]

    while buckets and len(merged) < limit:
        active = False
        for bucket in buckets:
            if len(merged) >= limit:
                break
            while bucket:
                result = bucket.pop(0)
                key = (result.get('platform'), result.get('name'))
                if key in seen:
                    continue
                seen.add(key)
                merged.append(result)
                active = True
                break
        if not active:
            break
    return merged


def build_platform_chart(results, field):
    grouped = {}
    for item in results:
        platform = item.get('platform')
        value = item.get(field)
        if platform is None or value is None:
            continue
        grouped.setdefault(platform, []).append(float(value))

    chart = {}
    for platform, values in grouped.items():
        if values:
            chart[platform] = round(sum(values) / len(values), 2)
    return chart

if __name__ == '__main__':
    app.run(debug=True)
