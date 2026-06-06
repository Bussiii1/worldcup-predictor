"""
Assemble toutes les sources de données pour un match.
Orchestre : ELO + Forme + WC History + H2H + Odds + Météo
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.elo import get_team_elo
from scrapers.odds_api import get_match_odds
from scrapers.weather import get_weather
from scrapers.fbref import get_team_xg as fbref_xg
from scrapers.transfermarkt import get_injuries as tm_injuries
from scrapers.news import get_news
from engine.form_engine import get_recent_form
from engine.fatigue_engine import get_fatigue_and_neutral
from engine.travel_engine import get_travel_stats
from engine.pressing_engine import get_pressing_stats
from engine.penalty_engine import get_penalty_stats, get_ko_advantage
from engine.referee_engine import get_referee_impact
from engine.wc_features import get_team_wc_stats, get_h2h_stats
from engine.expert_consensus import get_expert_signals


async def assemble_match_data(
    home: str,
    away: str,
    match_date: str,
    stadium: str,
    verbose: bool = True
) -> dict:
    """
    Collecte et fusionne toutes les données pour un match.
    Retourne un dict plat utilisé par MatchPredictorV2.predict()
    """
    data = {}
    log = []

    def _log(msg: str, ok: bool = True):
        symbol = "✓" if ok else "✗"
        if verbose:
            print(f"  {symbol} {msg}")
        log.append(f"{symbol} {msg}")

    print(f"\nAssembling data: {home} vs {away} ({match_date})")

    # ─── 1. ELO (sync) ────────────────────────────────────────────────────
    try:
        elo_h = get_team_elo(home)
        elo_a = get_team_elo(away)
        data[f"elo_{home}"] = elo_h.get("current_elo")
        data[f"elo_{away}"] = elo_a.get("current_elo")
        data[f"elo_trend_{home}"] = elo_h.get("elo_trend_30d")
        data[f"elo_trend_{away}"] = elo_a.get("elo_trend_30d")
        _log(f"ELO: {home}={data[f'elo_{home}']} / {away}={data[f'elo_{away}']}")
    except Exception as e:
        _log(f"ELO failed: {e}", False)

    # ─── 2. Forme récente (sync, eloratings.net) ──────────────────────────
    for team in [home, away]:
        try:
            form = get_recent_form(team, as_of_date=match_date)
            data[f"form_score_{team}"]        = form.get("form_score")
            data[f"form_string_{team}"]       = form.get("form_string")
            data[f"goals_scored_avg_{team}"]  = form.get("goals_scored_avg")
            data[f"goals_conceded_avg_{team}"]= form.get("goals_conceded_avg")
            data[f"form_trend_{team}"]        = form.get("form_trend")
            data[f"clean_sheet_rate_{team}"]  = form.get("clean_sheet_rate")
            # Utilise les buts pondérés comme proxy xG si pas d'autre source
            if form.get("goals_scored_avg"):
                data[f"xg_rolling_{team}"] = form.get("goals_scored_avg")
            _log(f"Form {team}: {form.get('form_score')} ({form.get('form_string')}) trend={form.get('form_trend')}")
        except Exception as e:
            _log(f"Form {team} failed: {e}", False)

    # ─── 3. WC History (sync, Fjelstul DB) ────────────────────────────────
    for team in [home, away]:
        try:
            wc = get_team_wc_stats(team)
            data[f"wc_win_rate_{team}"]       = wc.get("wc_win_rate")
            data[f"wc_ko_win_rate_{team}"]    = wc.get("wc_ko_win_rate")
            data[f"wc_titles_{team}"]         = wc.get("wc_titles")
            data[f"wc_appearances_{team}"]    = wc.get("wc_appearances")
            data[f"wc_experience_{team}"]     = wc.get("wc_experience_score")
            data[f"wc_goals_scored_{team}"]   = wc.get("wc_goals_scored_avg")
            data[f"wc_goals_conceded_{team}"] = wc.get("wc_goals_conceded_avg")
            _log(f"WC History {team}: {wc.get('wc_appearances')} editions, {wc.get('wc_titles')} titles, KO={wc.get('wc_ko_win_rate')}")
        except Exception as e:
            _log(f"WC History {team} failed: {e}", False)

    # ─── 4. H2H (sync, Fjelstul DB) ───────────────────────────────────────
    try:
        h2h = get_h2h_stats(home, away)
        data["h2h_matches"]          = h2h.get("h2h_matches", 0)
        data["h2h_wins_home"]        = h2h.get("h2h_wins_a", 0)
        data["h2h_wins_away"]        = h2h.get("h2h_wins_b", 0)
        data["h2h_draws"]            = h2h.get("h2h_draws", 0)
        data["h2h_win_rate_home"]    = h2h.get("h2h_win_rate_a")
        data["h2h_win_rate_away"]    = h2h.get("h2h_win_rate_b")
        data["h2h_avg_total_goals"]  = h2h.get("h2h_avg_total_goals")
        data["h2h_over25_rate"]      = h2h.get("h2h_over25_rate")
        data["h2h_dominant"]         = h2h.get("h2h_dominant")
        _log(f"H2H: {h2h.get('h2h_matches')} matches | dominant={h2h.get('h2h_dominant')}")
    except Exception as e:
        _log(f"H2H failed: {e}", False)

    # ─── 5. Cotes bookmakers (sync) ────────────────────────────────────────
    try:
        odds = get_match_odds(home, away)
        if odds.get("odds_available"):
            data.update(odds)
            data[f"xg_implied_{home}"] = odds.get("xg_implied_home")
            data[f"xg_implied_{away}"] = odds.get("xg_implied_away")
            _log(f"Odds: {home}={odds.get('odds_home')} Draw={odds.get('odds_draw')} {away}={odds.get('odds_away')} | Pinnacle={odds.get('has_pinnacle')}")
        else:
            data["odds_available"] = False
            _log(f"Odds: not available ({odds.get('error', 'unknown')})", False)
    except Exception as e:
        data["odds_available"] = False
        _log(f"Odds failed: {e}", False)

    # ─── 6. Météo (async) ─────────────────────────────────────────────────
    try:
        weather = await get_weather(stadium, match_date)
        data["weather_temp"]       = weather.get("temp_max_c")
        data["weather_rain"]       = weather.get("precipitation_mm")
        data["weather_wind"]       = weather.get("wind_speed_kmh")
        data["weather_conditions"] = weather.get("playing_conditions_assessment")
        # Impact météo sur le jeu (chaleur extrême = moins de buts)
        if weather.get("temp_max_c") and weather["temp_max_c"] > 33:
            data["weather_lambda_mult"] = 0.88
        elif weather.get("precipitation_mm") and weather["precipitation_mm"] > 10:
            data["weather_lambda_mult"] = 0.92
        else:
            data["weather_lambda_mult"] = 1.0
        _log(f"Weather: {weather.get('temp_max_c')}°C / {weather.get('precipitation_mm')}mm / {weather.get('playing_conditions_assessment')}")
    except Exception as e:
        data["weather_lambda_mult"] = 1.0
        _log(f"Weather failed: {e}", False)

    # ─── 7. Expert consensus (Opta + ESPN) ──────────────────────────────────
    try:
        experts = get_expert_signals(home, away)
        data["expert_espn_winner"]       = experts["espn_pick"]["winner"] if experts["espn_pick"] else None
        data["expert_espn_score"]        = experts["espn_pick"]["score"]  if experts["espn_pick"] else None
        data["expert_opta_win_home"]     = experts["opta_home"]["win_tournament_pct"]
        data["expert_opta_win_away"]     = experts["opta_away"]["win_tournament_pct"]
        data["expert_opta_qualify_home"] = experts["opta_home"]["qualify_from_group_pct"]
        data["expert_opta_qualify_away"] = experts["opta_away"]["qualify_from_group_pct"]
        data["expert_opta_favorite"]     = experts["opta_favorite"]
        data["expert_consensus_aligned"] = experts["consensus_aligned"]
        data["expert_edge"]              = experts["expert_edge"]
        data["expert_insight_home"]      = experts["insight_home"]
        data["expert_insight_away"]      = experts["insight_away"]
        _log(f"Experts: ESPN={data['expert_espn_winner']} ({data['expert_espn_score']}) | Opta favori={data['expert_opta_favorite']} | aligned={data['expert_consensus_aligned']}")
    except Exception as e:
        _log(f"Experts failed: {e}", False)

    # ─── 8. FBref — xG réels (derniers matchs internationaux) ───────────────
    for team in [home, away]:
        try:
            fb = fbref_xg(team)
            if fb.get("xg_rolling") is not None:
                # Override le proxy goals_scored si on a du vrai xG
                data[f"xg_rolling_{team}"] = fb["xg_rolling"]
                data[f"xga_rolling_{team}"] = fb.get("xga_rolling")
                data[f"shots_per90_{team}"] = fb.get("shots_per90")
                data[f"possession_{team}"]  = fb.get("possession_pct")
                _log(f"FBref {team}: xG={fb['xg_rolling']:.2f} xGA={fb.get('xga_rolling','?')} shots={fb.get('shots_per90','?')}")
            else:
                _log(f"FBref {team}: no xG data ({fb.get('error','?')})", False)
        except Exception as e:
            _log(f"FBref {team} failed: {e}", False)

    # ─── 9. Transfermarkt — blessures & squad ─────────────────────────────
    for team in [home, away]:
        try:
            tm = tm_injuries(team)
            data[f"injured_players_{team}"]  = tm.get("injured_players", [])
            data[f"n_injured_{team}"]        = tm.get("n_injured", 0)
            data[f"star_injured_{team}"]     = tm.get("star_injured", False)
            data[f"stars_out_{team}"]        = tm.get("stars_injured_names", [])
            data[f"squad_value_{team}"]      = tm.get("squad_value_eur_m")
            if tm.get("star_injured"):
                stars = ", ".join(tm.get("stars_injured_names", []))
                _log(f"TM {team}: ⚠ STAR OUT ({stars}) — {tm.get('n_injured',0)} blessés total")
            else:
                _log(f"TM {team}: {tm.get('n_injured',0)} blessés, aucune star absente")
        except Exception as e:
            data[f"star_injured_{team}"] = False
            data[f"n_injured_{team}"] = 0
            _log(f"TM {team} failed: {e}", False)

    # ─── 10. News & NLP (Google RSS) — items 8 & 12 ─────────────────────────
    try:
        news = await get_news(home, away)
        for k, v in news.items():
            if k not in ("source", "error", "top5_headlines", "n_articles"):
                data[k] = v
        data["news_headlines"] = news.get("top5_headlines", [])
        h_psych = news.get(f"psych_score_{home}", 0.5)
        a_psych = news.get(f"psych_score_{away}", 0.5)
        conflict_h = news.get(f"internal_conflict_{home}", False)
        conflict_a = news.get(f"internal_conflict_{away}", False)
        coach_h = news.get(f"coach_sentiment_{home}", "neutral")
        coach_a = news.get(f"coach_sentiment_{away}", "neutral")
        _log(f"News: {home} psych={h_psych} coach={coach_h} conflict={conflict_h} | "
             f"{away} psych={a_psych} coach={coach_a} conflict={conflict_a}")
    except Exception as e:
        _log(f"News failed: {e}", False)

    # ─── 11. Fatigue & matchs récents — item 5 ────────────────────────────
    for team in [home, away]:
        try:
            fat = get_fatigue_and_neutral(team, match_date)
            data[f"fatigue_score_{team}"]    = fat.get("fatigue_score", 0.0)
            data[f"fatigue_level_{team}"]    = fat.get("fatigue_level", "low")
            data[f"matches_30d_{team}"]      = fat.get("matches_last_30d", 0)
            data[f"matches_14d_{team}"]      = fat.get("matches_last_14d", 0)
            _log(f"Fatigue {team}: score={fat.get('fatigue_score',0)} "
                 f"({fat.get('fatigue_level','?')}) — {fat.get('matches_last_30d',0)} matchs/30j")
        except Exception as e:
            data[f"fatigue_score_{team}"] = 0.0
            _log(f"Fatigue {team} failed: {e}", False)

    # ─── 12. Distance de voyage — item 10 ─────────────────────────────────
    for team in [home, away]:
        try:
            travel = get_travel_stats(team, stadium)
            data[f"travel_km_{team}"]   = travel.get("travel_km")
            data[f"travel_level_{team}"]= travel.get("travel_level")
            data[f"travel_mult_{team}"] = travel.get("travel_fatigue_mult", 1.0)
            data[f"tz_offset_{team}"]   = travel.get("tz_offset_h")
            _log(f"Travel {team}: {travel.get('travel_km','?')} km "
                 f"({travel.get('travel_level','?')}) tz_offset={travel.get('tz_offset_h','?')}h")
        except Exception as e:
            data[f"travel_mult_{team}"] = 1.0
            _log(f"Travel {team} failed: {e}", False)

    # ─── 13. Pressing style — item 4 ──────────────────────────────────────
    for team in [home, away]:
        try:
            press = get_pressing_stats(team)
            data[f"pressing_score_{team}"]    = press.get("pressing_score")
            data[f"pressing_level_{team}"]    = press.get("pressing_level")
            data[f"press_attack_mult_{team}"] = press.get("press_attack_mult", 1.0)
            data[f"press_defense_mult_{team}"]= press.get("press_defense_mult", 1.0)
        except Exception as e:
            _log(f"Pressing {team} failed: {e}", False)
    _log(f"Pressing: {home}={data.get(f'pressing_level_{home}','?')} "
         f"| {away}={data.get(f'pressing_level_{away}','?')}")

    # ─── 14. Pénaltys / TAB — item 7 ──────────────────────────────────────
    try:
        pen_h = get_penalty_stats(home)
        pen_a = get_penalty_stats(away)
        ko    = get_ko_advantage(home, away)
        data[f"penalty_rate_{home}"]     = pen_h.get("penalty_rate")
        data[f"penalty_rate_{away}"]     = pen_a.get("penalty_rate")
        data[f"shootout_winrate_{home}"] = pen_h.get("shootout_win_rate")
        data[f"shootout_winrate_{away}"] = pen_a.get("shootout_win_rate")
        data["ko_penalty_advantage"]     = ko.get("penalty_advantage")
        data["ko_advantage_team"]        = ko.get("advantage_team")
        _log(f"Penalties: {home}={pen_h.get('penalty_rate','?')} "
             f"{pen_h.get('penalty_strength','?')} | "
             f"{away}={pen_a.get('penalty_rate','?')} "
             f"{pen_a.get('penalty_strength','?')}")
    except Exception as e:
        _log(f"Penalties failed: {e}", False)

    # ─── 15. Arbitre — item 9 ─────────────────────────────────────────────
    try:
        ref = get_referee_impact(home, away, stadium)
        data["ref_style"]           = ref.get("ref_style")
        data["ref_confederation"]   = ref.get("referee_confederation")
        data["ref_advantage_home"]  = ref.get("ref_advantage_a", 0.0)
        data["ref_advantage_away"]  = ref.get("ref_advantage_b", 0.0)
        data["ref_high_card_risk"]  = ref.get("high_card_risk", False)
        _log(f"Referee: style={ref.get('ref_style','?')} "
             f"conf={ref.get('referee_confederation','?')} "
             f"cards_est={ref.get('cards_per_game_est','?')}/match")
    except Exception as e:
        _log(f"Referee failed: {e}", False)

    # ─── 7. Meta ────────────────────────────────────────────────────────────
    data["_home"]       = home
    data["_away"]       = away
    data["_date"]       = match_date
    data["_stadium"]    = stadium
    data["_data_log"]   = log

    # Compte les sources répondues
    signals = {
        "elo":       data.get(f"elo_{home}") is not None,
        "form":      data.get(f"form_score_{home}") is not None,
        "wc":        data.get(f"wc_win_rate_{home}") is not None,
        "h2h":       data.get("h2h_matches", 0) > 0,
        "odds":      data.get("odds_available", False),
        "weather":   data.get("weather_temp") is not None,
        "fbref_xg":  data.get(f"xg_rolling_{home}") is not None,
        "injuries":  data.get(f"n_injured_{home}") is not None,
        "news":      data.get(f"psych_score_{home}") is not None,
        "fatigue":   data.get(f"fatigue_score_{home}") is not None,
        "travel":    data.get(f"travel_km_{home}") is not None,
        "pressing":  data.get(f"pressing_score_{home}") is not None,
        "penalties": data.get(f"penalty_rate_{home}") is not None,
        "referee":   data.get("ref_style") is not None,
    }
    data["_signals_ok"]    = sum(signals.values())
    data["_signals_total"] = len(signals)
    data["_completeness"]  = round(data["_signals_ok"] / data["_signals_total"], 2)

    print(f"  → {data['_signals_ok']}/{data['_signals_total']} sources OK | completeness={data['_completeness']:.0%}")
    return data


def assemble_sync(home, away, date, stadium, verbose=True) -> dict:
    """Version synchrone pour usage dans pipeline.py"""
    return asyncio.run(assemble_match_data(home, away, date, stadium, verbose))


if __name__ == "__main__":
    import json

    data = assemble_sync(
        home="France",
        away="Argentina",
        date="2026-07-14",
        stadium="AT&T Stadium",
        verbose=True
    )

    print("\n=== DATA ASSEMBLED ===")
    # Affiche les clés principales
    for k, v in sorted(data.items()):
        if not k.startswith("_") and v is not None:
            print(f"  {k}: {v}")
