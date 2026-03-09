"""
engine/__init__.py
Entry point tunggal untuk seluruh analisis.
Panggil: from engine import run_full_analysis
"""

from .scoring     import score_to_iq, build_cognitive_profile
from .expert_rules import (
    get_archetype, get_combined_profile,
    get_career_recommendations, get_learning_style,
    get_blind_spots, get_roadmap,
)

def run_iq_analysis(answers, session, lang='id'):
    """
    Jalankan analisis IQ lengkap.
    Return dict dengan semua hasil IQ.
    """
    iq_result        = score_to_iq(answers, session)
    cognitive        = build_cognitive_profile(answers, session)
    return {**iq_result, 'cognitive': cognitive}


def run_full_analysis(iq_answers, iq_session, bf_answers, bf_session,
                      bf_scores, lang='id'):
    """
    Jalankan analisis gabungan IQ + Big Five.
    Return dict lengkap dengan semua layer expert engine.
    """
    from engine.scoring import score_to_iq, build_cognitive_profile

    iq_result  = score_to_iq(iq_answers, iq_session)
    cognitive  = build_cognitive_profile(iq_answers, iq_session)
    iq         = iq_result['iq']

    archetype  = get_archetype(bf_scores, lang)
    combined   = get_combined_profile(iq, bf_scores, lang)
    careers    = get_career_recommendations(iq, bf_scores, lang)
    style_name, style_detail = get_learning_style(bf_scores, cognitive, lang)
    blind_spots = get_blind_spots(iq, bf_scores, lang)
    roadmap    = get_roadmap(iq, bf_scores, cognitive, careers, lang)

    from engine.scoring import get_percentile_bf
    try:
        from engine.scoring import get_percentile_bf
        pcts = {t: get_percentile_bf(t, bf_scores[t]) for t in ['O','C','E','A','N']}
    except Exception:
        pcts = {t: 50 for t in ['O','C','E','A','N']}

    return {
        **iq_result,
        'cognitive':   cognitive,
        'archetype':   archetype,
        'combined':    combined,
        'careers':     careers,
        'learning_style_name':   style_name,
        'learning_style_detail': style_detail,
        'blind_spots': blind_spots,
        'roadmap':     roadmap,
        'bf_scores':   bf_scores,
        'bf_pcts':     pcts,
    }