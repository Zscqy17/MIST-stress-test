import pandas as pd
import numpy as np
import os
import glob
import re
from scipy.signal import find_peaks, butter, filtfilt, welch, resample
from scipy.interpolate import interp1d
from scipy.fft import fft, fftfreq

# 1. Configuration
DATA_DIR = "data"
RESULTS_DIR = os.path.join(DATA_DIR, "results")
BIO_DIR = os.path.join(DATA_DIR, "bio_data")
FORCE_DIR = os.path.join(DATA_DIR, "force_sensor")
AVATAR_DIR = os.path.join(DATA_DIR, "avatar_scale")

# Experiment Order from 实验顺序.txt
# 1.ABCD
# 2.BADC
# 3.CDAB
# 4.DABC
# 5.BCDA
# 6.ABCD
SUBJECT_ORDER = {
    1: ['A', 'B', 'C', 'D'],
    2: ['B', 'A', 'D', 'C'],
    3: ['C', 'D', 'A', 'B'],
    4: ['D', 'A', 'B', 'C'],
    5: ['B', 'C', 'D', 'A'],
    6: ['A', 'B', 'C', 'D']
}

def find_mist_file(subject_id):
    pattern = os.path.join(RESULTS_DIR, f"mist_results_{subject_id}_*.csv")
    files = glob.glob(pattern)
    if not files:
        # Try subject 11 if subject 1 is missing, etc? 
        # But for now assume strict matching.
        return None
    # If multiple, take the latest one?
    files.sort()
    return files[-1]

def _extract_timestamp_from_filename(path):
    # Expect: mist_results_{id}_{timestamp}.csv
    base = os.path.basename(path)
    m = re.search(r'_(\d+)\.csv$', base)
    return m.group(1) if m else None

def find_recall_file(subject_id, ts=None):
    # Deprecated: recall files are created per round, and timestamps differ from mist_results.
    # Kept for backwards compatibility; prefer load_recall_map_for_session().
    if ts:
        candidate = os.path.join(RESULTS_DIR, f"mist_recall_{subject_id}_{ts}.csv")
        if os.path.exists(candidate):
            return candidate
    pattern = os.path.join(RESULTS_DIR, f"mist_recall_{subject_id}_*.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    files.sort()
    return files[-1]

def load_recall_map_for_session(subject_id, mist_ts):
    """
    Each recall CSV is saved per round (contains a single Round value).
    We select recall files with timestamp <= mist_results timestamp,
    then keep the latest file for each Round.
    """
    pattern = os.path.join(RESULTS_DIR, f"mist_recall_{subject_id}_*.csv")
    files = glob.glob(pattern)
    if not files:
        return {}

    keep = []
    for f in files:
        ts = _extract_timestamp_from_filename(f)
        if ts is None:
            continue
        try:
            if int(ts) <= int(mist_ts):
                keep.append((int(ts), f))
        except Exception:
            continue
    keep.sort(key=lambda x: x[0])

    round_map = {}  # round -> (ts, df)
    for ts_int, f in keep:
        try:
            d = pd.read_csv(f)
        except Exception:
            continue
        if 'Round' not in d.columns:
            continue
        rounds = sorted(set(pd.to_numeric(d['Round'], errors='coerce').dropna().astype(int).tolist()))
        if not rounds:
            continue
        # expected: exactly one round per file; if multiple, still handle by taking each
        for r in rounds:
            # keep latest per round
            prev = round_map.get(r)
            if prev is None or ts_int >= prev[0]:
                round_map[r] = (ts_int, d[d['Round'] == r].copy())

    # return only dfs
    return {r: d for r, (ts_int, d) in round_map.items()}

def compute_recall_correct_targets(recall_df, round_num):
    # “记对单词数量”按：目标词(IsTarget=True) 且被选中(Selected=True) 的数量（即 hits）
    if recall_df is None or recall_df.empty:
        return np.nan
    d = recall_df[recall_df['Round'] == round_num]
    if d.empty:
        return np.nan
    # Normalize types
    is_target = d['IsTarget'].astype(str).str.lower().isin(['true', '1', 'yes'])
    selected = d['Selected'].astype(str).str.lower().isin(['true', '1', 'yes'])
    return int((is_target & selected).sum())

def _extract_subject_id_from_serial(serial_value):
    """
    Serial Number 列里可能含有额外文本（例如 '2 相反'）。
    这里取第一个连续数字作为 SubjectID。
    """
    if serial_value is None or (isinstance(serial_value, float) and np.isnan(serial_value)):
        return None
    s = str(serial_value)
    m = re.search(r'(\d+)', s)
    return int(m.group(1)) if m else None

def _collapse_avatar_items(row, cols_by_qnum):
    """
    对同一题号出现多个列（例如 Q22/Q23 的两种英文版本），合并为单个数值：
    - 将可转数值的条目转为 float
    - 对同题号多个列取 mean（忽略 NaN）
    """
    def _coerce(v):
        # 支持：数值（-3..3）/ Wenjuan星导出字母选项（A..G）/ none
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return np.nan
        s = str(v).strip()
        if s == "" or s.lower() in {"none", "nan"}:
            return np.nan
        # Numeric?
        n = pd.to_numeric(s, errors='coerce')
        if not pd.isna(n):
            return float(n)
        # Letter mapping (A..G -> -3..3)
        letter_map = {"A": -3.0, "B": -2.0, "C": -1.0, "D": 0.0, "E": 1.0, "F": 2.0, "G": 3.0}
        up = s.upper()
        if up in letter_map:
            return letter_map[up]
        return np.nan

    out = {}
    for qnum, cols in cols_by_qnum.items():
        vals = []
        for c in cols:
            v = _coerce(row.get(c, np.nan))
            if not pd.isna(v):
                vals.append(float(v))
        out[qnum] = float(np.mean(vals)) if vals else np.nan
    return out

def _likert_minus3_to_1to7(v):
    # 将对称刻度（-3..3）映射到论文推荐的 1..7（-3->1, 0->4, 3->7）
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return np.nan
    try:
        return float(v) + 4.0
    except Exception:
        return np.nan

def _compute_revised_avatar_eq_from_q(qvals_minus3):
    """
    参考 Peck & Gonzalez-Franco 2021 (Frontiers in VR)：
    Table 2 中的 R1..R16 与原 Q 的映射，以及 5.1 Computing the Score 的子量表公式。

    R1=Q15, R2=Q16, R3=Q8, R4=Q17, R5=Q18, R6=Q20, R7=Q24, R8=Q22, R9=Q21,
    R10=Q1, R11=Q19, R12=Q14, R13=Q6, R14=Q10, R15=Q12, R16=Q13
    """
    # map to 1..7 first (paper recommended)
    q = {k: _likert_minus3_to_1to7(v) for k, v in qvals_minus3.items()}

    R = {
        "R1": q.get(15, np.nan),
        "R2": q.get(16, np.nan),
        "R3": q.get(8, np.nan),
        "R4": q.get(17, np.nan),
        "R5": q.get(18, np.nan),
        "R6": q.get(20, np.nan),
        "R7": q.get(24, np.nan),
        "R8": q.get(22, np.nan),
        "R9": q.get(21, np.nan),
        "R10": q.get(1, np.nan),
        "R11": q.get(19, np.nan),
        "R12": q.get(14, np.nan),
        "R13": q.get(6, np.nan),
        "R14": q.get(10, np.nan),
        "R15": q.get(12, np.nan),
        "R16": q.get(13, np.nan),
    }

    def mean_of(keys):
        xs = [R[k] for k in keys if k in R and not pd.isna(R[k])]
        return (float(np.mean(xs)) if xs else np.nan), int(len(xs))

    appearance, app_n = mean_of(["R1","R2","R3","R4","R5","R6","R9","R16"])
    response, res_n = mean_of(["R4","R6","R7","R8","R9","R15"])
    ownership, own_n = mean_of(["R5","R10","R11","R12","R13","R14"])
    multisensory, ms_n = mean_of(["R3","R12","R13","R14","R15","R16"])
    # overall embodiment
    emb, emb_n = mean_of([k for k in ["R1","R2","R3","R4","R5","R6","R7","R8","R9","R10","R11","R12","R13","R14","R15","R16"]])
    if not pd.isna(appearance) and not pd.isna(response) and not pd.isna(ownership) and not pd.isna(multisensory):
        embodiment = float(np.mean([appearance, response, ownership, multisensory]))
    else:
        embodiment = np.nan

    # Optional agency subscore per paper suggestion: Agency = R3 + R13 (here also provide mean)
    agency_sum = np.nan
    agency_mean = np.nan
    if (not pd.isna(R["R3"])) and (not pd.isna(R["R13"])):
        agency_sum = float(R["R3"] + R["R13"])
        agency_mean = float(np.mean([R["R3"], R["R13"]]))

    return R, {
        "AvatarEQ_Appearance": appearance,
        "AvatarEQ_Response": response,
        "AvatarEQ_Ownership": ownership,
        "AvatarEQ_MultiSensory": multisensory,
        "AvatarEQ_Embodiment": embodiment,
        "AvatarEQ_Appearance_N": app_n,
        "AvatarEQ_Response_N": res_n,
        "AvatarEQ_Ownership_N": own_n,
        "AvatarEQ_MultiSensory_N": ms_n,
        "AvatarEQ_R_N": emb_n,
        "AvatarEQ_Agency_Sum": agency_sum,
        "AvatarEQ_Agency_Mean": agency_mean,
    }

def export_avatar_scale_all_table(output_path="CHI_result/tables/avatar_scale_all_items_subscales.csv"):
    """
    输出“所有 avatar 问卷数据集中到一个表中”：
    每行 = SubjectID × Condition(C/D)；列包含：
    - Q1..Q25（原始 -3..3）
    - Q1..Q25_Likert（映射到 1..7，便于与论文一致）
    - R1..R16（1..7）
    - 论文子量表（Appearance/Response/Ownership/Multi-Sensory/Embodiment）
    """
    avatar_map = process_avatar_scale()
    if not avatar_map:
        return False

    # Re-read raw xlsx to capture meta fields (Name, submitted time, Serial raw) and build Q maps.
    xlsx_files = glob.glob(os.path.join(AVATAR_DIR, "*.xlsx"))
    rows = []
    for f in xlsx_files:
        try:
            d = pd.read_excel(f)
            d["__file"] = os.path.basename(f)
            rows.append(d)
        except Exception:
            continue
    if not rows:
        return False
    df = pd.concat(rows, ignore_index=True)
    if "Serial Number" not in df.columns:
        return False
    if "提交答卷时间" in df.columns:
        df["__submitted_at"] = pd.to_datetime(df["提交答卷时间"], errors="coerce")
    else:
        df["__submitted_at"] = pd.NaT
    df["__subject_id"] = df["Serial Number"].apply(_extract_subject_id_from_serial)
    df = df[~df["__subject_id"].isna()].copy()
    df["__subject_id"] = df["__subject_id"].astype(int)
    df = df.sort_values("__submitted_at").groupby("__subject_id", as_index=False).tail(1)

    qcols = [c for c in df.columns if isinstance(c, str) and re.match(r"^Q\d+\.", c)]
    base_cols = [c for c in qcols if not c.endswith(".1")]
    alt_cols = [c for c in qcols if c.endswith(".1")]

    def build_cols_by_num(cols):
        m = {}
        for c in cols:
            mm = re.match(r"^Q(\d+)\.", c)
            if not mm:
                continue
            qn = int(mm.group(1))
            m.setdefault(qn, []).append(c)
        return m

    base_by_num = build_cols_by_num(base_cols)
    alt_by_num = build_cols_by_num(alt_cols)

    out_rows = []
    for _, r in df.iterrows():
        sid = int(r["__subject_id"])
        serial_raw = str(r.get("Serial Number", ""))
        swapped = "相反" in serial_raw
        name = r.get("Name", np.nan)
        submitted = r.get("提交答卷时间", np.nan)
        src_file = r.get("__file", np.nan)

        base_q = _collapse_avatar_items(r, base_by_num)  # -3..3
        alt_q = _collapse_avatar_items(r, alt_by_num)

        c_q, d_q = (alt_q, base_q) if swapped else (base_q, alt_q)

        for cond, qmap in [("C", c_q), ("D", d_q)]:
            R, scores = _compute_revised_avatar_eq_from_q(qmap)
            row_out = {
                "SubjectID": sid,
                "Condition": cond,
                "Name": name,
                "SerialNumberRaw": serial_raw,
                "SubmittedAt": submitted,
                "SourceFile": src_file,
                "SwappedCD": swapped,
            }
            # Q1..Q25 raw and likert
            for i in range(1, 26):
                row_out[f"Q{i}"] = qmap.get(i, np.nan)
                row_out[f"Q{i}_Likert"] = _likert_minus3_to_1to7(qmap.get(i, np.nan))
            # R1..R16 (likert)
            for k, v in R.items():
                row_out[k] = v
            # subscales
            row_out.update(scores)
            out_rows.append(row_out)

    out_df = pd.DataFrame(out_rows).sort_values(["SubjectID", "Condition"])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_df.to_csv(output_path, index=False)
    return True

def process_avatar_scale():
    """
    读取 data/avatar_scale 下的 Avatar Embodiment Questionnaire（两段：默认 + .1）。
    输出：avatar_map[(SubjectID, Condition)] -> { Avatar_* metrics }

    约定：
    - 默认段（无 .1 后缀）对应 C（Naked Robot）
    - .1 段对应 D（Clothed Robot）
    - 若 Serial Number 含 '相反'，则交换 C/D 映射
    """
    if not os.path.exists(AVATAR_DIR):
        return {}

    xlsx_files = glob.glob(os.path.join(AVATAR_DIR, "*.xlsx"))
    if not xlsx_files:
        return {}

    rows = []
    for f in xlsx_files:
        try:
            d = pd.read_excel(f)
            d["__file"] = os.path.basename(f)
            rows.append(d)
        except Exception as e:
            print(f"Error reading avatar_scale {f}: {e}")

    if not rows:
        return {}

    df = pd.concat(rows, ignore_index=True)
    if "Serial Number" not in df.columns:
        return {}

    # identify Q columns by question number; handle duplicates (Q22/Q23 variants)
    qcols = [c for c in df.columns if isinstance(c, str) and re.match(r"^Q\d+\.", c)]
    base_cols = [c for c in qcols if not c.endswith(".1")]
    alt_cols = [c for c in qcols if c.endswith(".1")]

    def build_cols_by_num(cols):
        m = {}
        for c in cols:
            mm = re.match(r"^Q(\d+)\.", c)
            if not mm:
                continue
            qn = int(mm.group(1))
            m.setdefault(qn, []).append(c)
        return m

    base_by_num = build_cols_by_num(base_cols)
    alt_by_num = build_cols_by_num(alt_cols)

    # choose latest submission per subject if multiple
    if "提交答卷时间" in df.columns:
        df["__submitted_at"] = pd.to_datetime(df["提交答卷时间"], errors="coerce")
    else:
        df["__submitted_at"] = pd.NaT

    df["__subject_id"] = df["Serial Number"].apply(_extract_subject_id_from_serial)
    df = df[~df["__subject_id"].isna()].copy()
    df["__subject_id"] = df["__subject_id"].astype(int)

    # keep latest per subject
    df = df.sort_values("__submitted_at").groupby("__subject_id", as_index=False).tail(1)

    avatar_map = {}
    for _, r in df.iterrows():
        sid = int(r["__subject_id"])
        serial_raw = str(r.get("Serial Number", ""))
        swapped = "相反" in serial_raw

        base_vals = _collapse_avatar_items(r, base_by_num)   # Q1..Q25 -> value
        alt_vals = _collapse_avatar_items(r, alt_by_num)

        def summarize(vals):
            def rev(v):
                # 量表为对称刻度（如 -3..3）时，反向题可用取负号近似反向计分
                return -v if (v is not None and not pd.isna(v)) else np.nan

            def mean_of(qnums):
                xs = []
                for q in qnums:
                    v = vals.get(q, np.nan)
                    v = float(v) if (v is not None and not pd.isna(v)) else np.nan
                    if not pd.isna(v):
                        xs.append(v)
                return float(np.mean(xs)) if xs else np.nan, int(len(xs))

            # Overall (raw mean of available items)
            items = [vals.get(i) for i in range(1, 26)]
            items = [float(v) for v in items if v is not None and not pd.isna(v)]
            overall_mean = float(np.mean(items)) if items else np.nan
            overall_n = int(len(items))

            # Constructed subscales (transparent + common structure)
            # Ownership: include reverse-coded “someone else” items
            # Q1 own; Q2 other(reverse); Q4 mirror-own; Q5 mirror-other(reverse); Q14 location-own
            ownership_items = []
            for q, is_rev in [(1, False), (2, True), (4, False), (5, True), (14, False), (17, False), (18, False), (19, False)]:
                v = vals.get(q, np.nan)
                v = float(v) if (v is not None and not pd.isna(v)) else np.nan
                if not pd.isna(v):
                    ownership_items.append(-v if is_rev else v)
            ownership = float(np.mean(ownership_items)) if ownership_items else np.nan
            ownership_n = int(len(ownership_items))

            # Agency/Control: reverse-code Q9 (“moving by itself”)
            agency_items = []
            for q, is_rev in [(6, False), (7, False), (8, False), (9, True)]:
                v = vals.get(q, np.nan)
                v = float(v) if (v is not None and not pd.isna(v)) else np.nan
                if not pd.isna(v):
                    agency_items.append(-v if is_rev else v)
            agency = float(np.mean(agency_items)) if agency_items else np.nan
            agency_n = int(len(agency_items))

            # Touch/Referral: Q10-13
            touch, touch_n = mean_of([10, 11, 12, 13])

            # Avatar Embodiment Questionnaire (Peck & Gonzalez-Franco 2021) revised subscales
            # Compute on the same underlying raw (-3..3) values
            R_map, eq_scores = _compute_revised_avatar_eq_from_q(vals)

            return {
                "Avatar_Embodiment_Mean": overall_mean,
                "Avatar_Embodiment_N": overall_n,
                "Avatar_Ownership_Score": ownership,
                "Avatar_Ownership_N": ownership_n,
                "Avatar_Agency_Score": agency,
                "Avatar_Agency_N": agency_n,
                "Avatar_Touch_Score": touch,
                "Avatar_Touch_N": touch_n,
                # expose a few interpretable single-items (safety / control), if present
                "Avatar_Q1_Ownership": vals.get(1, np.nan),
                "Avatar_Q6_Control": vals.get(6, np.nan),
                "Avatar_Q9_SpontaneousMove": vals.get(9, np.nan),
                "Avatar_Q25_HarmConcern": vals.get(25, np.nan),
                # Revised (R1..R16) subscales and overall embodiment (1..7)
                **eq_scores,
            }

        base_sum = summarize(base_vals)
        alt_sum = summarize(alt_vals)

        # map to conditions
        c_metrics, d_metrics = (alt_sum, base_sum) if swapped else (base_sum, alt_sum)
        avatar_map[(sid, "C")] = c_metrics
        avatar_map[(sid, "D")] = d_metrics

    return avatar_map

def find_bio_file(subject_id, condition):
    # Pattern: {id}{cond}[_]?Entity...
    # Examples: 1A_Entity..., 6CEntity...
    pattern_str = f"^{subject_id}{condition}[_]?Entity.*\\.csv$"
    regex = re.compile(pattern_str)
    
    for fname in os.listdir(BIO_DIR):
        if regex.match(fname):
            return os.path.join(BIO_DIR, fname)
    return None

def find_force_file(subject_id, condition):
    # Condition C = No Clothes (没衣服, 无衣服)
    # Condition D = Clothes (有衣服, 穿衣服)
    
    keywords = []
    if condition == 'C':
        keywords = ["没衣服", "无衣服"]
    elif condition == 'D':
        keywords = ["有衣服", "穿衣服"]
    else:
        return None
        
    for kw in keywords:
        pattern = f"{subject_id}_{kw}.csv"
        path = os.path.join(FORCE_DIR, pattern)
        if os.path.exists(path):
            return path
    return None

def process_force_data(file_path):
    try:
        df = pd.read_csv(file_path)
        # NOTE: 实际只有一个力传感器，Thumb/Index 是同一传感器的两个通道/位置。
        # 因此这里按用户要求：将 Thumb 与 Index 的力幅值相加，得到“总力”用于比较（C vs D）。
        #
        # 使用 M1 的三轴（IPS1610）作为主通道；若存在缺失/截断行，按 0 处理。

        needed = [
            'Thumb_M1_IPS1610_Fx', 'Thumb_M1_IPS1610_Fy', 'Thumb_M1_IPS1610_Fz',
            'Index_M1_IPS1610_Fx', 'Index_M1_IPS1610_Fy', 'Index_M1_IPS1610_Fz',
        ]
        for c in needed:
            if c not in df.columns:
                return {}

        df_needed = df[needed].apply(pd.to_numeric, errors='coerce').fillna(0.0)

        thumb_mag = np.sqrt(
            df_needed['Thumb_M1_IPS1610_Fx']**2 +
            df_needed['Thumb_M1_IPS1610_Fy']**2 +
            df_needed['Thumb_M1_IPS1610_Fz']**2
        )
        index_mag = np.sqrt(
            df_needed['Index_M1_IPS1610_Fx']**2 +
            df_needed['Index_M1_IPS1610_Fy']**2 +
            df_needed['Index_M1_IPS1610_Fz']**2
        )

        total_mag = thumb_mag + index_mag

        return {
            "Force_Total_Mean": float(total_mag.mean()),
            "Force_Total_Max": float(total_mag.max()),
        }
    except Exception as e:
        print(f"Error reading force file {file_path}: {e}")
        return {}

# --- Signal Processing Helpers ---
def butter_bandpass(lowcut, highcut, fs, order=3):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_lowpass(cutoff, fs, order=3):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def calculate_hr_hrv(bvp_signal, fs=1000):
    try:
        # BVP usually 0.5-4Hz
        b, a = butter_bandpass(0.5, 4.0, fs, order=2)
        filtered = filtfilt(b, a, bvp_signal)
        
        # Find peaks (systolic)
        distance = int(0.4 * fs)
        peaks, _ = find_peaks(filtered, distance=distance)
        
        if len(peaks) < 2:
            return np.nan, np.nan, np.nan
            
        # Calculate IBIs in ms
        ibis = np.diff(peaks) / fs * 1000
        
        # Outlier removal (Simple Hampel-like: remove > 3std)
        mean_ibi = np.mean(ibis)
        std_ibi = np.std(ibis)
        clean_ibis = ibis[np.abs(ibis - mean_ibi) < 3 * std_ibi]
        
        if len(clean_ibis) < 2:
             return np.nan, np.nan, np.nan

        # HR
        hr = 60000 / np.mean(clean_ibis)
        
        # RMSSD
        diff_ibis = np.diff(clean_ibis)
        rmssd = np.sqrt(np.mean(diff_ibis**2))
        
        # LF/HF Ratio (Frequency Domain)
        # 1. Resample IBI to uniform series (e.g. 4Hz)
        # Create time axis for IBIs
        ibi_times = np.cumsum(clean_ibis) / 1000.0 # seconds
        ibi_times = ibi_times - ibi_times[0]
        
        # Interpolate
        f_interp = interp1d(ibi_times, clean_ibis, kind='cubic', fill_value="extrapolate")
        fs_resample = 4.0 # Hz
        duration = ibi_times[-1]
        t_new = np.arange(0, duration, 1/fs_resample)
        ibis_resampled = f_interp(t_new)
        
        # 2. Welch PSD
        f, pxx = welch(ibis_resampled, fs=fs_resample, nperseg=min(len(ibis_resampled), 256))
        
        # 3. Integrate bands
        # LF: 0.04 - 0.15 Hz
        # HF: 0.15 - 0.4 Hz
        lf_mask = (f >= 0.04) & (f <= 0.15)
        hf_mask = (f >= 0.15) & (f <= 0.4)
        
        lf_power = np.trapz(pxx[lf_mask], f[lf_mask])
        hf_power = np.trapz(pxx[hf_mask], f[hf_mask])
        
        lf_hf_ratio = lf_power / hf_power if hf_power > 0 else np.nan
        
        return hr, rmssd, lf_hf_ratio
    except Exception:
        return np.nan, np.nan, np.nan

def calculate_gsr_gradient_features(eda_signal, fs=1000):
    """
    Paper Method:
    1. Downsample to 20Hz
    2. Compute Gradient
    3. FFT -> Mean Freq, Peak Freq, Power @ 0.05Hz
    """
    try:
        # 1. Downsample to 20Hz
        target_fs = 20
        num_samples = int(len(eda_signal) * target_fs / fs)
        eda_down = resample(eda_signal, num_samples)
        
        # 2. Gradient
        gradient = np.gradient(eda_down)
        
        # 3. FFT
        # Use rfft for real input
        N = len(gradient)
        yf = fft(gradient)
        xf = fftfreq(N, 1 / target_fs)
        
        # Take positive half
        idx_pos = xf >= 0
        freqs = xf[idx_pos]
        power = np.abs(yf[idx_pos])**2 # Power spectrum
        
        # Metrics
        # Mean Frequency: sum(f * p) / sum(p)
        mean_freq = np.sum(freqs * power) / np.sum(power) if np.sum(power) > 0 else 0
        
        # Peak Frequency: f with max power
        peak_freq = freqs[np.argmax(power)]
        
        # Power at 0.05 Hz (approximate)
        # Find index closest to 0.05
        idx_005 = (np.abs(freqs - 0.05)).argmin()
        power_005 = power[idx_005]
        
        return mean_freq, peak_freq, power_005
    except Exception:
        return np.nan, np.nan, np.nan

def calculate_eda_features(eda_signal, fs=1000):
    try:
        # SCL: Low pass < 0.05 Hz
        b, a = butter_lowpass(0.05, fs, order=2)
        scl = filtfilt(b, a, eda_signal)
        scl_mean = np.mean(scl)
        
        # SCR: High pass > 0.05 Hz (Phasic)
        # Or just subtract SCL
        phasic = eda_signal - scl
        
        # Find peaks in phasic
        # Threshold: 0.01 uS (common)
        # Distance: 1s
        peaks, properties = find_peaks(phasic, height=0.01, distance=fs)
        
        duration_min = len(eda_signal) / fs / 60
        scr_freq = len(peaks) / duration_min if duration_min > 0 else 0
        
        return scl_mean, scr_freq
    except Exception:
        return np.nan, np.nan

def calculate_resp_rate(resp_signal, fs=1000):
    try:
        # Bandpass 0.1 - 0.5 Hz (6 - 30 breaths/min)
        b, a = butter_bandpass(0.1, 0.5, fs, order=2)
        filtered = filtfilt(b, a, resp_signal)
        
        peaks, _ = find_peaks(filtered, distance=fs*2) # at least 2s per breath
        
        duration_min = len(resp_signal) / fs / 60
        rate = len(peaks) / duration_min if duration_min > 0 else 0
        
        return rate
    except Exception:
        return np.nan

def process_bio_data(file_path):
    try:
        # Skip first row if it's metadata? Header is usually line 1 (0-indexed)
        # File read showed: 
        # Line 1: ID,StorageTime,...
        df = pd.read_csv(file_path)
        
        # Columns: ...BVP, ...EDA, ...RESP
        # Use regex to find columns
        bvp_col = [c for c in df.columns if "BVP" in c][0]
        eda_col = [c for c in df.columns if "EDA" in c][0]
        resp_col = [c for c in df.columns if "RESP" in c][0]
        
        # Assume 1000Hz based on file inspection
        fs = 1000
        
        hr, rmssd, lf_hf = calculate_hr_hrv(df[bvp_col].values, fs)
        scl, scr_freq = calculate_eda_features(df[eda_col].values, fs)
        eda_mean_f, eda_peak_f, eda_p005 = calculate_gsr_gradient_features(df[eda_col].values, fs)
        resp_rate = calculate_resp_rate(df[resp_col].values, fs)
        
        return {
            "Bio_BVP_Mean": df[bvp_col].mean(), # Keep original
            "Bio_HR_Mean": hr,
            "Bio_HRV_RMSSD": rmssd,
            "Bio_HRV_LFHF": lf_hf,
            "Bio_EDA_Mean": df[eda_col].mean(), # Keep original
            "Bio_SCL_Mean": scl,
            "Bio_SCR_Freq": scr_freq,
            "Bio_EDA_MeanFreq": eda_mean_f,
            "Bio_EDA_PeakFreq": eda_peak_f,
            "Bio_EDA_Power005": eda_p005,
            "Bio_RESP_Rate": resp_rate
        }
    except Exception as e:
        print(f"Error reading bio file {file_path}: {e}")
        return {}

def process_nasa_tlx():
    try:
        df = pd.read_excel("data/NASA-TLX_6_6.xlsx")
        # Rename column for easier access
        df.rename(columns={'志愿者编号 Number ': 'SubjectID'}, inplace=True)
        
        # Dimensions
        dims = ['心理需求 Mental Demand', '身体需求 Physical Demand', '时间压力 Temporal Demand', 
                '个人表现 Performance', '努力程度 Effort', '挫败感 Frustration Level']
        
        nasa_data = {} # (SubjectID, RoundIndex 0-3) -> {metrics}
        
        for _, row in df.iterrows():
            sub_id = row['SubjectID']
            if pd.isna(sub_id): continue
            sub_id = int(sub_id)
            
            for i in range(4):
                suffix = "" if i == 0 else f".{i}"
                
                # Calculate Mean TLX for this block
                scores = []
                for d in dims:
                    col = f"{d}{suffix}"
                    if col in df.columns:
                        scores.append(row[col])
                
                if scores:
                    mean_tlx = np.mean(scores)
                    nasa_data[(sub_id, i+1)] = { # Round is 1-based
                        "NASA_TLX_Score": mean_tlx,
                        "NASA_Mental": row.get(f"心理需求 Mental Demand{suffix}", np.nan),
                        "NASA_Frustration": row.get(f"挫败感 Frustration Level{suffix}", np.nan)
                    }
        return nasa_data
    except Exception as e:
        print(f"Error reading NASA TLX: {e}")
        return {}

def main():
    final_data = []
    
    # Load NASA TLX first
    nasa_map = process_nasa_tlx()
    avatar_map = process_avatar_scale()
    
    for sub_id in range(1, 7):
        print(f"Processing Subject {sub_id}...")
        
        # 1. MIST Data
        mist_file = find_mist_file(sub_id)
        if not mist_file:
            print(f"  No MIST file found for Subject {sub_id}")
            continue
            
        mist_df = pd.read_csv(mist_file)
        ts = _extract_timestamp_from_filename(mist_file)

        # 1.1 Word recall (saved per round). Build a round->df map for this session.
        recall_map = load_recall_map_for_session(sub_id, mist_ts=ts) if ts else {}
        if not recall_map:
            print(f"  Missing Recall files for Subject {sub_id} (session ts={ts})")
        
        # 2. Iterate Rounds
        order = SUBJECT_ORDER.get(sub_id)
        
        for round_num in range(1, 5): # Rounds 1-4
            condition = order[round_num-1] # index 0-3
            
            # Filter MIST
            round_data = mist_df[mist_df['Round'] == round_num]
            if round_data.empty:
                print(f"  No data for Round {round_num} (Condition {condition})")
                continue
                
            # MIST Stats
            avg_time = round_data['TimeTaken'].mean()
            timeouts = round_data['Timeout'].sum()
            recall_df_round = recall_map.get(round_num)
            word_correct = compute_recall_correct_targets(recall_df_round, round_num)
            
            row = {
                "SubjectID": sub_id,
                "Condition": condition,
                "Round": round_num,
                "MIST_ResponseTime": avg_time,
                "MIST_Timeouts": timeouts,
                "Word_Recall_Correct": word_correct
            }
            
            # 3. Bio Data
            bio_file = find_bio_file(sub_id, condition)
            if bio_file:
                # print(f"  Found Bio: {os.path.basename(bio_file)}")
                bio_stats = process_bio_data(bio_file)
                row.update(bio_stats)
            else:
                print(f"  Missing Bio for Subject {sub_id} Condition {condition}")
                
            # 4. Force Data (Only C and D)
            if condition in ['C', 'D']:
                force_file = find_force_file(sub_id, condition)
                if force_file:
                    # print(f"  Found Force: {os.path.basename(force_file)}")
                    force_stats = process_force_data(force_file)
                    row.update(force_stats)
                else:
                    print(f"  Missing Force for Subject {sub_id} Condition {condition}")

                # 4.1 Avatar Embodiment Questionnaire (only for robot conditions)
                if (sub_id, condition) in avatar_map:
                    row.update(avatar_map[(sub_id, condition)])
            
            # 5. NASA TLX
            # Round num is 1-4.
            if (sub_id, round_num) in nasa_map:
                row.update(nasa_map[(sub_id, round_num)])
                
            final_data.append(row)
            
    # Save
    final_df = pd.DataFrame(final_data)
    final_df.to_csv("combined_analysis.csv", index=False)
    print("Done. Saved to combined_analysis.csv")
    print(final_df.head())

if __name__ == "__main__":
    main()

