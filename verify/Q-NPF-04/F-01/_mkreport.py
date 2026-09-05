import json, itertools
import numpy as np

c14 = json.load(open('result_c14_loop_cert.json'))
c15 = json.load(open('result_c15_c2_lag_cert.json'))
c16 = json.load(open('result_c16_structural.json'))


def subset_scan(R):
    out = {}
    R = np.array(R)
    nm = ('gain', 'efficacy', 'delay')
    for rsz in (1, 2, 3):
        for sub in itertools.combinations(range(3), rsz):
            S = R[:, list(sub)]
            n = np.linalg.norm(S, axis=1)
            aa = []
            for i, j in itertools.combinations(range(3), 2):
                d = n[i] * n[j]
                c = abs(float(S[i] @ S[j] / d)) if d > 1e-12 else 0.0
                aa.append(float(np.degrees(np.arccos(min(c, 1.0)))))
            key = '+'.join(['S%d' % (k + 1) for k in sub])
            out[key] = dict(
                channel_norms=dict(zip(nm, [round(float(x), 3) for x in n])),
                min_pairwise_angle_deg=round(min(aa), 3) if rsz > 1 else None,
                pass_CA=bool(np.all(n >= 2.0)),
                pass_CB=(bool(min(aa) >= 15.0) if rsz > 1 else None))
    return out


rep = dict(
    role='prover-bio', mode='conjecture (card attempt)', question='Q-NPF-04',
    date='2026-09-04',
    routing_receipt='verify/_routing/870ccf52-e14f-4026-af42-39b8f4c7184a.json',
    verdict=('FAILURE REPORT, NO CARD WRITTEN. C1, C2 and C3 all fail precondition P3 '
             '(channel identification certificate). Per verify/Q-NPF-04/spec.md the correct '
             'output is the failure table, not a card.'),
    scope_change_implemented=dict(
        what=('forward model extended from a local recurrent patch to LONG-AXIS FEEDBACK '
              'LOOPS closed by long conduction paths, with per-loop path length L varying '
              'across loops'),
        file='verify/Q-NPF-04/F-01/fwd_loop.py',
        loops_per_animal=8, L_range_m=[0.008, 0.060], v_m_per_s=0.10, tau_syn_s=0.0020,
        note=('the scope change WORKED for its stated purpose: the delay channel is no '
              'longer a micro-perturbation. The prior local-circuit certificate had delay '
              'z = 0.07/0.10/0.18; here the delay channel reaches |z| = 4.17 on the '
              'period-vs-length slope. C1 nevertheless fails, and it fails for a DIFFERENT '
              'reason than its predecessors.')),
    topology_finding=dict(
        claim='the spec C1 slope of EXACTLY 2 selects the loop topology; it is not free',
        single_limb_ring='tau_loop = L/v + tau_syn traversed once -> 1/f = 2(L/v+tau_syn), slope 2',
        two_limb_ring=('tau_loop = 2(L/v+tau_syn) -> slope 4; measured 4.269 / 4.018 / '
                       '4.057 / 4.002 across v in {0.5,0.2,0.1,0.05} and tau_m in {0.020,0.005}'),
        adopted='single-limb ring, matching the SINGLE arctan in the spec resonance equation'),
    P3_certificate=dict(
        criteria=dict(C_A='max|z| >= 2.0 for every channel',
                      C_B='pairwise angle >= 15 deg',
                      placebo='within-phase null must give z = 0 by construction'),
        C1=dict(
            script='c14_loop_cert.py', result_file='result_c14_loop_cert.json',
            statistics={
                'S1': 'slope of measured period 1/f on measured path term L/v0 + tau_syn',
                'S2': 'mean spectral peak sharpness f/FWHM (damping proxy)',
                'S3': 'mean log broadband baseline power'},
            channel_response_matrix_in_null_sd_units=c14['channel_response_matrix'],
            channel_norms=c14['channel_norms'],
            pairwise_angle_deg=c14['pairwise_angle_deg'],
            null_sd=c14['null_sd'], placebo_mean=c14['placebo_mean'],
            per_world=c14['table'],
            pass_CA=c14['pass_CA'], pass_CB=c14['pass_CB'],
            subset_scan=subset_scan(c14['channel_response_matrix']),
            why_it_fails=('C-A and C-B cannot be satisfied together. EVERY one of the seven '
                          'non-empty statistic subsets fails at least one criterion. The '
                          'subsets that detect gain at all (any subset containing S3) '
                          'collapse the gain-efficacy angle to about 4 deg; the subset that '
                          'separates gain from efficacy (S1+S2, 17.3 deg) leaves the gain '
                          'response norm at 0.45, far below the required 2.0.')),
        C2=dict(
            script='c15_c2_lag_cert.py', result_file='result_c15_c2_lag_cert.json',
            statistics={'U1': 'mean pre->post cross-spectral phase-slope lag',
                        'U2': 'mean normalised coupling (root coherence)',
                        'U3': 'mean log broadband power'},
            channel_response_matrix_in_null_sd_units=c15['channel_response_matrix'],
            channel_norms=c15['channel_norms'],
            pairwise_angle_deg=c15['pairwise_angle_deg'],
            per_world=c15['table'], subset_scan=c15['subset_scan'],
            pass_CA=c15['pass_CA'], pass_CB=c15['pass_CB'],
            why_it_fails=('fails C-A outright: delay norm 1.58, gain norm 2.12, and the '
                          'DELAY response on the lag statistic itself is z = -0.23. Root '
                          'cause is an unambiguity ceiling, not estimator quality: at the '
                          'named frame rate the phase-slope lag is unwrappable only up to '
                          '1/(2 f_max) = 0.167 s, while the generating transport times span '
                          '0.080-0.600 s, so 6 of 8 loops wrap. C2 is blind to exactly the '
                          'long loops that carry the first-order delay term.')),
        C3=dict(
            method='analytic, no Monte Carlo needed',
            result_file='result_c16_structural.json',
            why_it_fails=('C3 embeds history in the coordinate and builds a metric from the '
                          'SAME second-order statistics. The gain-efficacy degeneracy below '
                          'is a statement about the power spectrum, so every lagged '
                          'covariance inherits it exactly: the ratio of gain-world to '
                          'efficacy-world lagged autocovariance is the constant 1.2100000 '
                          'over all 400 lags (min 1.2099999999998985, max '
                          '1.2100000000000075). Any history-embedded second-order statistic '
                          'therefore has gain-efficacy angle 0 and fails C-B.'))),
    root_cause=dict(
        name='EXACT gain-efficacy degeneracy of the delayed feedback loop',
        statement=('In the long-axis ring the intrinsic gain g and the coupling strength k '
                   'enter the closed-loop transfer ONLY through the product g*k in the '
                   'denominator, while g additionally multiplies the numerator. '
                   'Consequently a gain change and an efficacy change matched to the same '
                   'loop product differ by a FREQUENCY-INDEPENDENT constant: '
                   'S_gain(w)/S_efficacy(w) = exp(2*dlog g) = 1.2100 exactly.'),
        measured_max_spread_over_grid=c16['degeneracy_max_spread'],
        grid=('42 configurations: L in {8,10.7,14.8,24,33,48,60} mm x node in {0,1} x '
              'k in {1.2,1.6,2.5}'),
        consequence=('The two channels are distinguishable ONLY by an overall multiplicative '
                     'power scale. P2 requires the statistic to be invariant under '
                     'o -> a*o + b. Any statistic satisfying P2 is therefore EXACTLY blind '
                     'to the gain-efficacy contrast, and any statistic that sees it (like S3 '
                     'log baseline power) is not scale invariant and is the same object that '
                     'killed F-03 via the zero-point. This is an identification obstruction, '
                     'not a design failure.')),
    what_DID_work=dict(
        delay_channel_is_now_first_order='yes; this is the scope change paying off',
        noisefree_T1_slope=c16['noisefree_T1_slope'],
        predicted_delay_slope_2_over_1p25=c16['predicted_delay_slope'],
        note=('noise-free, the period-vs-length slope is 2.0045 in the base, gain and '
              'efficacy worlds and 1.6063 in the delay world, against the algebraic '
              'prediction 2/1.25 = 1.6. S1 is a CLEAN, self-calibrating delay separator: '
              'efficacy and gain leave it exactly unmoved. With noise the delay channel '
              'still reaches z = -4.17. The C1 slope-2 law itself is therefore supported '
              'inside the model; what fails is the THREE-channel separation demanded by P3.')),
    estimator_rules_established=dict(
        DISC_1_aliasing_guard=('discard loops whose upper-bound frequency '
                               '1/(2(L/V_MAX+tau_syn)) exceeds 0.80*Nyquist. Uses measured L '
                               'and declared velocity bounds only, never the contrast, so P5 '
                               'independence is preserved.'),
        SEL_1_fundamental_selection=('a delayed loop resonates on a COMB (fundamental plus '
                                     'odd harmonics) and for long loops a HARMONIC is often '
                                     'the largest peak (L = 48 mm: fundamental 1.00 Hz at '
                                     'power 2.8 versus 7.03 Hz harmonic at 13.9). '
                                     'Unrestricted argmax returned harmonics and gave '
                                     'per-loop frequency sd up to 1.94 Hz at a 0.029 Hz bin '
                                     'width. Restricting the search to the path-length '
                                     'window [1/(2(L/V_MIN+ts)), 1/(2(L/V_MAX+ts))] recovers '
                                     'every fundamental exactly. Window width factor '
                                     'V_MAX/V_MIN = 1.5625, so it does not pin the answer: '
                                     'the delay-world shift stays strictly inside it.'),
        background_scale=('the peak prominence sd is estimated over the FULL admissible '
                          'band, not inside the narrow selection window, where the peak '
                          'dominates its own sd.')),
    preconditions_status=dict(
        P1='declared: conditional output-relative Fisher (21.41); not reached, P3 gates it',
        P2=('the degeneracy above shows P2 (invariance under o -> a o + b) is in DIRECT '
            'CONFLICT with detecting the gain-efficacy contrast in this system'),
        P3='FAILED for C1, C2 and C3 - this report',
        P4=('within-phase placebo implemented and clean in both certificates: C1 placebo '
            'z = (0,0,0) by construction with placebo mean (0.0072, -0.125, -0.0018) against '
            'null sd (0.104, 2.848, 0.0282); C2 placebo mean (-0.0018, 0.00028, 0.00093)'),
        P5=('implemented: selection fold and contrast fold are disjoint interleaved blocks '
            'of the record (N_BLOCK = 8, TRAIN_PARITY = 1); loop admission uses the '
            'selection fold only'),
        P6='not reached (P3 gates it)', P7='not reached', P8='not reached'),
    N_declared=dict(mice=8, cells_per_mouse=[54, 52, 33, 17, 35, 62, 38, 63],
                    total_cells=354, trials_per_phase=60, frame_dt_s=0.0670,
                    nyquist_hz=7.4627, frames_per_phase_used=2048,
                    note='named-data structure inherited from fwd.py unchanged'),
    structural_data_note=dict(
        file='verify/Q-NPF-04/bio-reader_connectome_eligibility.json',
        used_for=('the design principle that only RELATIVE path length is fixed while '
                  'absolute velocity is free, which is why C1 regresses on length and reads '
                  'a slope'),
        NOT_used_for=('no cross-species chain was formed; that file explicitly forbids '
                      'combining its structural source with the named functional data in '
                      'one chain')),
    recommendation=dict(
        do_not=('write a fourth card on a three-channel separation endpoint from population '
                'activity alone. Five certificates now agree.'),
        cumulative=('F-01, F-02, F-03 plus the connection/geodesic certificate plus this '
                    'long-axis loop certificate. The obstruction has migrated but not '
                    'disappeared: it was delay-blindness in the local circuit, and it is '
                    'exact gain-efficacy degeneracy in the long loop.'),
        what_would_change_it=[
            ('A perturbation that moves gain and efficacy DIFFERENTLY, breaking the product '
             'g*k (the degeneracy is exact only because both act through that product).'),
            ('An observable with an independent absolute scale, so that the constant 1.21 is '
             'measurable without violating P2.'),
            ('A two-channel endpoint: delay versus everything-else. S1 already satisfies C-A '
             '(|z| = 4.17) and is exactly unmoved by gain and efficacy, so a TWO-channel '
             'card is admissible where a three-channel card is not. This is the strongest '
             'surviving option.')],
        next_single_step=('ask the user whether to reduce the endpoint from three channels '
                          'to two (delay versus non-delay), which the evidence here '
                          'supports, since that is an endpoint change and only the user may '
                          'make it.')),
    artifacts=['verify/Q-NPF-04/F-01/fwd_loop.py',
               'verify/Q-NPF-04/F-01/c14_loop_cert.py',
               'verify/Q-NPF-04/F-01/result_c14_loop_cert.json',
               'verify/Q-NPF-04/F-01/c15_c2_lag_cert.py',
               'verify/Q-NPF-04/F-01/result_c15_c2_lag_cert.json',
               'verify/Q-NPF-04/F-01/result_c16_structural.json'],
    no_data_opened=True, ledger_untouched=True, paper_untouched=True, card_written=False,
    parking=[('the harmonic comb of a delayed loop is itself a delay signature: the SPACING '
              'of the comb is 1/tau_loop and is scale invariant, unlike peak height. Not '
              'pursued here because it does not fix the gain-efficacy degeneracy, which is '
              'what kills the three-channel endpoint.')],
)

json.dump(rep, open('prover_loop_report.json', 'w'), indent=1, ensure_ascii=False)
print('written chars', len(json.dumps(rep)))
