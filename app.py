from flask import Flask, render_template, request, session
import itertools

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for session

# Add min to Jinja2 environment
app.jinja_env.globals.update(min=min)

# Item set (24 items: 1a-6a, 1b-6b, 1c-6c, 1d-6d)
items = [f'{i}{c}' for i in range(1, 7) for c in ['a', 'b', 'c', 'd']]

@app.route('/', methods=['GET', 'POST'])
def calculator():
    # Initialize session defaults
    if 'stake' not in session:
        session['stake'] = 10.0  # Default stake
    if 'odds' not in session:
        session['odds'] = {item: 2.0 for item in items}  # Default odds
    if 'selected_legs' not in session:
        session['selected_legs'] = []  # Default to empty, will be set to all legs on first calculation

    if request.method == 'POST':
    # Get user inputs
    selected_items = request.form.getlist('items')
    selected_legs = []
    for leg in request.form.getlist('legs'):
        if leg and leg.strip():
            try:
                selected_legs.append(int(leg))
            except ValueError:
                pass

    stake = request.form.get('stake', session['stake'])
    try:
        stake = float(stake)
    except ValueError:
        stake = session['stake']

    odds = {}
    for item in items:
        odds_value = request.form.get(f'odds_{item}')
        try:
            odds[item] = float(odds_value) if odds_value else session['odds'].get(item, 0.0)
        except (ValueError, TypeError):
            odds[item] = session['odds'].get(item, 0.0)

    # Update session
    session['stake'] = stake
    session['odds'] = odds
    if selected_legs:
        session['selected_legs'] = selected_legs
    session.modified = True

    if not selected_items:
        return render_template('index.html', items=items, error="請至少選擇 1 個項目。", stake=session['stake'], odds=session['odds'])

    # Group by match
    matches = {i: [] for i in range(1, 7)}
    for item in selected_items:
        match_num = int(item[0])
        matches[match_num].append(item)

    match_numbers = set(int(item[0]) for item in selected_items)
    n = len(match_numbers)
    max_k = min(n, 6)

    results = []
    combination_counts = {}
    match_list = sorted(match_numbers)

    for k in range(1, max_k + 1):
        match_combinations = list(itertools.combinations(match_list, k))
        combination_counts[k] = 0

        for match_combo in match_combinations:
            items_per_match = [matches[match] for match in match_combo]
            if not all(items_per_match):  # 防止空列表
                continue
            for combo in itertools.product(*items_per_match):
                parlay_odds = 1.0
                for item in combo:
                    parlay_odds *= odds.get(item, 0.0)
                payout = stake * parlay_odds
                results.append({
                    'size': k,
                    'combo': ', '.join(combo),
                    'parlay_odds': round(parlay_odds, 2),
                    'payout': payout
                })
                combination_counts[k] += 1

    # Effective legs 處理加強
    effective_legs = selected_legs if selected_legs else session.get('selected_legs', [])
    if not effective_legs and combination_counts:
        effective_legs = list(combination_counts.keys())
        session['selected_legs'] = effective_legs

    total_payout = sum(r['payout'] for r in results if r['size'] in effective_legs)

    result = {
        'selected': selected_items,
        'combinations': results,
        'combination_counts': combination_counts,
        'total_combinations': sum(combination_counts.values()),
        'total_payout': total_payout,
        'selected_legs': effective_legs
    }

    return render_template('index.html', items=items, result=result, stake=session['stake'], odds=session['odds'], max_k=max_k)

    return render_template('index.html', items=items, stake=session['stake'], odds=session['odds'])

if __name__ == '__main__':
    app.run(debug=True)
