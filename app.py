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
        selected_legs = [int(leg) for leg in request.form.getlist('legs') if leg]  # Get checked leg sizes
        stake = request.form.get('stake', session['stake'])
        try:
            stake = float(stake)
        except ValueError:
            stake = session['stake']
        odds = {}
        for item in items:
            odds_value = request.form.get(f'odds_{item}')
            try:
                odds[item] = float(odds_value) if odds_value else session['odds'].get(item, 0.0)  # Preserve 0 if set
            except (ValueError, TypeError):
                odds[item] = session['odds'].get(item, 0.0)  # Fall back to session value, default to 0.0

        # Update session
        session['stake'] = stake
        session['odds'] = odds
        if selected_legs:  # Only update session if new legs are selected
            session['selected_legs'] = selected_legs
        session.modified = True

        # Validate: Ensure at least 1 item selected
        if not selected_items:
            return render_template('index.html', items=items, error="Please select at least 1 item.", stake=session['stake'], odds=session['odds'])

        # Group selected items by match
        matches = {i: [] for i in range(1, 7)}
        for item in selected_items:
            match_num = int(item[0])
            matches[match_num].append(item)

        # Determine number of unique matches with at least one selected item
        match_numbers = set(int(item[0]) for item in selected_items)  # Extract unique match numbers
        n = len(match_numbers)  # Number of unique matches
        max_k = min(n, 6)  # Cap at n matches or 6

        # Generate valid combinations (one item per match)
        results = []
        combination_counts = {}
        match_list = sorted(match_numbers)  # List of matches with selections (e.g., [1, 2, 3, 4, 5, 6])

        for k in range(1, max_k + 1):
            # Choose k matches out of the available matches
            match_combinations = list(itertools.combinations(match_list, k))
            combination_counts[k] = 0

            for match_combo in match_combinations:
                # For each match in the combination, get the list of selected items
                items_per_match = [matches[match] for match in match_combo]
                # Generate all possible combinations by picking one item from each match
                combo_iter = itertools.product(*items_per_match)
                for combo in combo_iter:
                    parlay_odds = 1
                    for item in combo:
                        parlay_odds *= odds.get(item, 0.0)  # Use 0.0 for non-winning races
                    payout = stake * parlay_odds  # Removed // 2 as per your instruction
                    results.append({
                        'size': k,
                        'combo': ', '.join(combo),
                        'parlay_odds': round(parlay_odds, 2),
                        'payout': payout  # Keep as float for summation
                    })
                    combination_counts[k] += 1

        # Use session-stored selected_legs if none are provided in the form
        effective_legs = selected_legs if selected_legs else session['selected_legs']
        # If no legs are selected (first submission), default to all available legs
        if not effective_legs:
            effective_legs = list(combination_counts.keys())
            session['selected_legs'] = effective_legs

        # Debug print to verify
        print(f"Selected items: {selected_items}")
        print(f"Unique matches: {match_numbers}")
        print(f"Selected legs (form): {selected_legs}")
        print(f"Effective legs: {effective_legs}")
        print(f"Session selected_legs: {session['selected_legs']}")
        print(f"Combination counts: {combination_counts}")
        print(f"Results sizes: {[r['size'] for r in results]}")
        print(f"Odds: {odds}")

        # Calculate total payout based on effective legs
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