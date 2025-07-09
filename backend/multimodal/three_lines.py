import cv2, numpy as np, matplotlib.pyplot as plt

# -------------------- 0. 基本参数 --------------------
img_path = "/Users/fengyihang/python_code/paper_evaluation/paper_image/table_error.png" 
canny_lo, canny_hi = 30, 100
min_len_ratio  = 0.10          
coord_tol, gap_tol = 4, 3

# -------------------- 1. 读取 + 预处理 --------------------
img  = cv2.imread(img_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5,5), 0)

edges = cv2.Canny(blur, canny_lo, canny_hi)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
edges_close = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

# -------------------- 2. HoughLinesP --------------------
raw = cv2.HoughLinesP(edges_close, 1, np.pi/180,
                      threshold=60,
                      minLineLength=10,
                      maxLineGap=5)
raw = [] if raw is None else raw

# -------------------- 3. 方向分类 + 初步长度过滤 --------------------
H_raw, V_raw = [], []
for (x1,y1,x2,y2) in raw[:,0]:
    horiz = abs(y2-y1) < abs(x2-x1)
    length = np.hypot(x2-x1, y2-y1)
    if horiz and length >= min_len_ratio*img.shape[1]:
        H_raw.append((x1,y1,x2,y2))
    elif (not horiz) and length >= min_len_ratio*img.shape[0]:
        V_raw.append((x1,y1,x2,y2))

# -------------------- 4. 黑度过滤 --------------------
def is_dark(line, thr=180, samples=400):
    x1,y1,x2,y2 = line
    xs = np.linspace(x1, x2, samples).astype(int)
    ys = np.linspace(y1, y2, samples).astype(int)
    return gray[ys, xs].mean() < thr

H_dark = [l for l in H_raw if is_dark(l)]
V_dark = [l for l in V_raw if is_dark(l)]

# -------------------- 5. 去重（完全重叠合并） --------------------
def dedup_lines_overlap(lines, is_horiz, coord_tol, gap_tol):
    axis = 1 if is_horiz else 0           
    o0, o1 = (0,2) if is_horiz else (1,3)

    clusters = []
    for ln in lines:
        coord = ln[axis]
        for cl in clusters:
            if abs(cl[0][axis] - coord) <= coord_tol:
                cl.append(ln); break
        else:
            clusters.append([ln])

    merged = []
    for cl in clusters:
        ivals = [tuple(sorted((ln[o0], ln[o1]))) for ln in cl]
        ivals.sort(key=lambda t: t[0])

        segs = [ivals[0]]
        for s,e in ivals[1:]:
            ls, le = segs[-1]
            if s <= le + gap_tol:
                segs[-1] = (ls, max(le, e))
            else:
                segs.append((s,e))

        for s,e in segs:
            if is_horiz:
                merged.append((s, cl[0][1], e, cl[0][1]))
            else:
                merged.append((cl[0][0], s, cl[0][0], e))
    return merged

H_final = dedup_lines_overlap(H_dark, True,  coord_tol, gap_tol)
V_final = dedup_lines_overlap(V_dark, False, coord_tol, gap_tol)

# -------------------- 6. 结果统计 --------------------
print("H_final:", len(H_final), " V_final:", len(V_final))

# -------------------- 7. 可视化展示 --------------------
tmp2 = img.copy()
for x1,y1,x2,y2 in H_final: cv2.line(tmp2,(x1,y1),(x2,y2),(0,255,0),2)
for x1,y1,x2,y2 in V_final: cv2.line(tmp2,(x1,y1),(x2,y2),(255,0,0),2)

cv2.imshow("vis",tmp2); cv2.waitKey(0) 