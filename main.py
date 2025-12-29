import cv2
import numpy as np
import pandas as pd

# ================================================================
# 0) UTILITAIRES
# ================================================================
def crop_roi_from_percent(img, x_pct, y_pct, w_pct, h_pct):
    H, W = img.shape[:2]

    x = int(x_pct * W)
    y = int(y_pct * H)
    w = int(w_pct * W)
    h = int(h_pct * H)

    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if x + w > W:
        w = W - x
    if y + h > H:
        h = H - y

    roi = img[y:y + h, x:x + w].copy()
    return roi, (x, y, w, h)


def group_positions(pos, min_gap=4):
    if len(pos) == 0:
        return []
    groups = [[pos[0]]]
    for p in pos[1:]:
        if p - groups[-1][-1] <= min_gap:
            groups[-1].append(p)
        else:
            groups.append([p])
    return [int(np.mean(g)) for g in groups]


def analyze_cells(cells, reference=None, threshold_factor=1.8, max_candidates=2):
    """
    Analyse les cellules d’un tableau (entier ou décimal).

    Retourne :
      - idx_checked : index choisi ou None
      - reference   : référence utilisée
      - black_sums  : densité de noir par case
      - subcells    : (top, bottom) par case (pour debug éventuel)
      - info        : dict avec 'status' et 'candidates'
    """
    black_sums = []
    subcells = []

    for idx, cell in enumerate(cells):
        h, w = cell.shape[:2]
        top = cell[0:h//2, :]
        bottom = cell[h//2:h, :]
        subcells.append((top, bottom))
        
        gray_b = cv2.cvtColor(bottom, cv2.COLOR_BGR2GRAY)
        th_b = cv2.adaptiveThreshold(
            gray_b, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            15, 8
        )
        
        black = np.sum(th_b == 255)
        black_sums.append(black)

    info = {
        "status": "unknown",
        "candidates": [],
        "black_sums": black_sums
    }

    if len(black_sums) == 0:
        info["status"] = "no_cells"
        return None, reference, black_sums, subcells, info

    if reference is None:
        reference = np.mean(black_sums)

    differences = np.array(black_sums) - reference
    max_diff = np.max(differences)

    if max_diff <= 0:
        info["status"] = "no_mark"
        return None, reference, black_sums, subcells, info

    threshold = max_diff / threshold_factor

    candidate_indices = [i for i, d in enumerate(differences) if d >= threshold]
    info["candidates"] = candidate_indices

    nb_cand = len(candidate_indices)

    if nb_cand == 0:
        info["status"] = "no_candidate"
        return None, reference, black_sums, subcells, info

    if nb_cand == 1:
        idx_checked = candidate_indices[0]
        info["status"] = "single_candidate"
        return idx_checked, reference, black_sums, subcells, info

    if 1 < nb_cand <= max_candidates:
        # 2 candidats max : on garde le meilleur si suffisamment plus fort
        sorted_cand = sorted(candidate_indices, key=lambda i: black_sums[i], reverse=True)
        best = sorted_cand[0]
        if len(sorted_cand) > 1:
            second = sorted_cand[1]
            diff_best = black_sums[best] - black_sums[second]
            ratio = diff_best / float(black_sums[best]) if black_sums[best] > 0 else 0.0
            if ratio < 0.1:  # < 10% de différence => trop proche
                info["status"] = "ambiguous_two"
                return None, reference, black_sums, subcells, info

        info["status"] = "two_candidates_resolved"
        return best, reference, black_sums, subcells, info

    # Plus de 2 candidats => bruit
    info["status"] = "too_many_candidates"
    return None, reference, black_sums, subcells, info


def is_valid_index(idx, info_status):
    return (idx is not None) and (info_status not in [
        "no_cells", "no_mark", "no_candidate",
        "ambiguous_two", "too_many_candidates"
    ])


# ================================================================
# 1) FONCTION PRINCIPALE D'ANALYSE D'UNE PAGE
# ================================================================
def analyze_page(image_path):
    """
    Analyse une page anis*.jpg et renvoie un dict avec :
      - filename
      - valid_grid
      - status_int, status_dec
      - idx_int, idx_dec
      - note_detected (float ou NaN)
    """
    result = {
        "filename": image_path,
        "valid_grid": False,
        "status_int": "not_processed",
        "status_dec": "not_processed",
        "idx_int": np.nan,
        "idx_dec": np.nan,
        "note_detected": np.nan,
        "error": ""
    }

    img = cv2.imread(image_path)
    if img is None:
        result["error"] = "image_not_found"
        return result

    # ---------- 1) Correction orientation via QR / code-barres ----------
    qr_detector = cv2.QRCodeDetector()
    data, points, straight_qrcode = qr_detector.detectAndDecode(img)

    if points is not None and len(points) > 0:
        pts = points[0]
        y_mean = np.mean(pts[:, 1])
        H, W = img.shape[:2]
        if y_mean > 0.5 * H:
            img = cv2.rotate(img, cv2.ROTATE_180)

    # ---------- 2) ROI du tableau global ----------
    TAB1_XP = 0.0000
    TAB1_YP = 0.2391
    TAB1_WP = 0.9800
    TAB1_HP = 0.1056

    roi, (x, y, w, h) = crop_roi_from_percent(
        img,
        TAB1_XP, TAB1_YP, TAB1_WP, TAB1_HP
    )
    if roi.size == 0:
        result["error"] = "empty_roi"
        return result

    # ---------- 3) Seuillage + morpho ----------
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    th = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        15, 8
    )

    kernel_open  = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    th_open = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel_open, iterations=1)
    th_clean = cv2.morphologyEx(th_open, cv2.MORPH_CLOSE, kernel_close, iterations=1)

    h_th, w_th = th_clean.shape[:2]

    TOP_MARG_PCT    = 0.10
    BOTTOM_MARG_PCT = 0.10
    LEFT_MARG_PCT   = 0.02
    RIGHT_MARG_PCT  = 0.02

    top    = int(TOP_MARG_PCT          * h_th)
    bottom = int((1 - BOTTOM_MARG_PCT) * h_th)
    left   = int(LEFT_MARG_PCT         * w_th)
    right  = int((1 - RIGHT_MARG_PCT)  * w_th)

    top = max(0, min(top, h_th-1))
    bottom = max(top+1, min(bottom, h_th))
    left = max(0, min(left, w_th-1))
    right = max(left+1, min(right, w_th))

    th_proj = th_clean[top:bottom, left:right].copy()
    offset_y = top
    offset_x = left

    # ---------- 4) Projections ----------
    vertical_proj = np.sum(th_proj, axis=0)
    horizontal_proj = np.sum(th_proj, axis=1)

    v_max = vertical_proj.max() if vertical_proj.max() > 0 else 1
    h_max = horizontal_proj.max() if horizontal_proj.max() > 0 else 1

    v_norm = vertical_proj / v_max
    h_norm = horizontal_proj / h_max

    H_THRESH = 0.70
    V_THRESH = 0.70

    h_peaks = np.where(h_norm > H_THRESH)[0]
    v_peaks = np.where(v_norm > V_THRESH)[0]

    # ---------- 5) Lignes ----------
    h_lines_local = group_positions(h_peaks, min_gap=6)
    v_lines_local = group_positions(v_peaks, min_gap=6)

    h_lines = [yy + offset_y for yy in h_lines_local]
    v_lines = [xx + offset_x for xx in v_lines_local]

    cells_int = []
    cells_dec = []
    valid_grid = True

    if len(h_lines) >= 2 and len(v_lines) >= 3:
        y1 = h_lines[0]
        y2 = h_lines[-1]

        diffs = np.diff(v_lines)
        idx_split = int(np.argmax(diffs))

        v_lines_int = v_lines[:idx_split+1]
        v_lines_dec = v_lines[idx_split+1:]

        for i in range(len(v_lines_int) - 1):
            x1 = v_lines_int[i]
            x2 = v_lines_int[i+1]
            cell = roi[y1:y2, x1:x2].copy()
            cells_int.append(cell)

        for i in range(len(v_lines_dec) - 1):
            x1 = v_lines_dec[i]
            x2 = v_lines_dec[i+1]
            cell = roi[y1:y2, x1:x2].copy()
            cells_dec.append(cell)
    else:
        valid_grid = False

    EXPECTED_INT = 21
    EXPECTED_DEC = 4
    EXPECTED_TOTAL = EXPECTED_INT + EXPECTED_DEC

    total_cells = len(cells_int) + len(cells_dec)
    if total_cells != EXPECTED_TOTAL:
        if abs(total_cells - EXPECTED_TOTAL) > 2:
            valid_grid = False

    result["valid_grid"] = valid_grid

    # Si grille pas fiable => on s’arrête là
    if not valid_grid:
        result["status_int"] = "invalid_grid"
        result["status_dec"] = "invalid_grid"
        return result

    # ---------- 6) Analyse des cellules ----------
    idx_int, ref_int, bs_int, subs_int, info_int = analyze_cells(cells_int)
    idx_dec, ref_dec, bs_dec, subs_dec, info_dec = analyze_cells(cells_dec)

    result["status_int"] = info_int["status"]
    result["status_dec"] = info_dec["status"]

    # ---------- 7) Note finale ----------
    note = np.nan

    if is_valid_index(idx_int, info_int["status"]) and is_valid_index(idx_dec, info_dec["status"]):
        valeurs_entieres = list(range(0, len(cells_int)))  # 0..20
        valeurs_decimales = [0.00, 0.25, 0.50, 0.75]

        if idx_int < len(valeurs_entieres) and idx_dec < len(valeurs_decimales):
            note = valeurs_entieres[idx_int] + valeurs_decimales[idx_dec]
            result["idx_int"] = idx_int
            result["idx_dec"] = idx_dec
            result["note_detected"] = note
        else:
            result["error"] = "index_out_of_range"
    else:
        # Ambiguïté / trop de cases / pas assez de cases cochées
        result["error"] = "no_reliable_note"

    return result


# ================================================================
# 2) BOUCLE SUR TOUTES LES PAGES ET GÉNÉRATION EXCEL
# ================================================================
all_results = []

for i in range(1, 71):  # 1..70
    fname = f"anis121125_page-{i:04d}.jpg"
    res = analyze_page(fname)

    # colonne pour la note de vérité (ground truth), à remplir à la main
    res["note_ground_truth"] = np.nan

    # colonne pour savoir si correct (sera calculée plus tard)
    res["correct"] = np.nan

    all_results.append(res)

df = pd.DataFrame(all_results)

# Sauvegarde Excel
output_excel = "resultats_anis121125.xlsx"
df.to_excel(output_excel, index=False)

print(f"✅ Fichier Excel généré : {output_excel}")
