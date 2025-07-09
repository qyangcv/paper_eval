import cv2

def calculate_orb_similarity(image1_path, image2_path, threshold=0.6):
    img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)

    img1_pixels = img1.shape[0] * img1.shape[1]
    img2_pixels = img2.shape[0] * img2.shape[1]

    larger_image, smaller_image = (img1, img2) if img1_pixels > img2_pixels else (img2, img1)
    ratio = min(img1_pixels, img2_pixels) / max(img1_pixels, img2_pixels)

    orb_larger = cv2.ORB_create(nfeatures=1000)
    orb_smaller = cv2.ORB_create(nfeatures=int(500 * ratio))

    kp1, des1 = orb_larger.detectAndCompute(larger_image, None)
    kp2, des2 = orb_smaller.detectAndCompute(smaller_image, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    # 计算匹配的特征点数量
    match_count = len(matches)

    # 计算原图和裁剪图像的特征点数量
    feature_count_img1 = len(kp1)
    feature_count_img2 = len(kp2)

    # 计算匹配点占特征点数量的比例
    match_ratio_img1 = match_count / feature_count_img1 if feature_count_img1 > 0 else 0
    match_ratio_img2 = match_count / feature_count_img2 if feature_count_img2 > 0 else 0

    print(f"Feature points in Image 1: {feature_count_img1}")
    print(f"Feature points in Image 2: {feature_count_img2}")
    print(f"Matching ratio for Image 1: {match_ratio_img1}")
    print(f"Matching ratio for Image 2: {match_ratio_img2}")

    # 判断是否相似
    if match_ratio_img1 >= threshold or match_ratio_img2 >= threshold:
        return True, match_count 
    else:
        return False, match_count  

def main():
    image1_path = './paper_image/clip_part.png' 
    image2_path = './paper_image/clip_vague.png' 

    is_similar, match_count = calculate_orb_similarity(image1_path, image2_path)
    if is_similar:
        print(f"Images are similar! Number of matching points: {match_count}")
    else:
        print(f"Images are not similar. Number of matching points: {match_count}")

if __name__ == "__main__":
    main()
