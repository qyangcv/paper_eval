import asyncio
from pathlib import Path
import uuid
import requests
from loguru import logger
from PicImageSearch import Bing, Network
from PicImageSearch.model import BingResponse
from PicImageSearch.sync import Bing as BingSync

PROXIES = None
SAVE_DIR = Path("downloaded_images")
SAVE_DIR.mkdir(exist_ok=True)
SAVE_TXT = Path("./downloaded_images/image_urls.txt") 

file = "/Users/yang/Documents/bupt/code/github/paper_eval/backend/multimodal/images/image4.png"

@logger.catch()
async def demo_async() -> None:
    async with Network(proxies=PROXIES) as client:
        bing = Bing(client=client)
        resp = await bing.search(file=file)
        show_result(resp)


@logger.catch()
def demo_sync() -> None:
    bing = BingSync(proxies=PROXIES)
    resp = bing.search(file=file)
    show_result(resp)  # pyright: ignore[reportArgumentType]


def show_result(resp: BingResponse) -> None:
    logger.info(f"Search URL: {resp.url}")
    
    # 记录是否找到了任何图片URL
    found_urls = False

    if resp.pages_including:
        logger.info("Pages Including:")
        with SAVE_TXT.open("a", encoding="utf-8") as f:             
            for page_item in resp.pages_including:
                logger.info(f"  Name: {page_item.name}")
                logger.info(f"  URL: {page_item.url}")
                logger.info(f"  Thumbnail URL: {page_item.thumbnail}")
                logger.info(f"  Image URL: {page_item.image_url}")
                logger.info("-" * 20)
                if page_item.image_url:                           
                    f.write(page_item.image_url + "\n")
                    found_urls = True
    else:
        logger.warning("未找到包含该图片的页面")

    if resp.visual_search:
        logger.info("Visual Search:")
        with SAVE_TXT.open("a", encoding="utf-8") as f:
            for visual_item in resp.visual_search:
                logger.info(f"  Name: {visual_item.name}")
                logger.info(f"  URL: {visual_item.url}")
                logger.info(f"  Thumbnail URL: {visual_item.thumbnail}")
                logger.info(f"  Image URL: {visual_item.image_url}")
                logger.info("-" * 20)
                if visual_item.image_url:
                    f.write(visual_item.image_url + "\n")
                    found_urls = True
    else:
        logger.warning("未找到相似的图片")

    if resp.related_searches:
        logger.info("Related Searches:")
        for search_item in resp.related_searches:
            logger.info(f"  Text: {search_item.text}")
            logger.info(f"  Thumbnail URL: {search_item.thumbnail}")
            logger.info("-" * 20)

    if resp.travel:
        logger.info("Travel:")
        logger.info(f"  Destination: {resp.travel.destination_name}")
        logger.info(f"  Travel Guide URL: {resp.travel.travel_guide_url}")

        if resp.travel.attractions:
            logger.info("  Attractions:")
            for attraction in resp.travel.attractions:
                logger.info(f"    Title: {attraction.title}")
                logger.info(f"    URL: {attraction.url}")
                logger.info(f"    Requery URL: {attraction.search_url}")
                logger.info(f"    Interest Types: {', '.join(attraction.interest_types)}")
                logger.info("-" * 20)

        if resp.travel.travel_cards:
            logger.info("  Travel Cards:")
            for card in resp.travel.travel_cards:
                logger.info(f"    Card Type: {card.card_type}")
                logger.info(f"    Title: {card.title}")
                logger.info(f"    Click URL: {card.url}")
                logger.info(f"    Image URL: {card.image_url}")
                logger.info(f"    Image Source URL: {card.image_source_url}")
                logger.info("-" * 20)

    if resp.entities:
        logger.info("Entities:")
        for entity in resp.entities:
            logger.info(f"  Name: {entity.name}")
            logger.info(f"  Thumbnail URL: {entity.thumbnail}")
            logger.info(f"  Description: {entity.description}")
            logger.info(f"  Short Description: {entity.short_description}")
            if hasattr(entity, 'profiles') and entity.profiles:
                logger.info("  Profiles:")
                for profile in entity.profiles:
                    logger.info(f"     {profile.get('social_network')}: {profile.get('url')}")

            logger.info("-" * 20)

    if resp.best_guess:
        logger.info(f"Best Guess: {resp.best_guess}")
    
    # 如果没有找到任何图片URL，创建空文件
    if not found_urls:
        logger.warning("未找到任何图片URL，创建空的URL文件")
        SAVE_TXT.touch()  # 创建空文件

def download_images_from_txt(txt_path: Path, save_dir: Path, max_images: int = 5) -> None:
    if not txt_path.exists():
        logger.error(f"文件 {txt_path} 不存在")
        return

    with txt_path.open("r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        logger.warning("URL 列表为空，跳过下载。")
        return

    logger.info(f"准备下载前 {min(max_images, len(urls))} 张图片…")
    for i, url in enumerate(urls[:max_images], 1):        
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            suffix = Path(url).suffix or ".jpg"
            filename = save_dir / f"{uuid.uuid4().hex}{suffix}"
            filename.write_bytes(resp.content)
            logger.info(f"[{i}/{max_images}] → {filename.name}")
        except Exception as e:
            logger.warning(f"[{i}/{max_images}] 下载失败：{url} | {e}")

    logger.success("下载任务完成。")


if __name__ == "__main__":
    try:
        logger.info("开始图像搜索...")
        asyncio.run(demo_async())
        logger.info("图像搜索完成")
        
        logger.info("开始下载图片...")
        download_images_from_txt(SAVE_TXT, SAVE_DIR, 5)
    except Exception as e:
        logger.error(f"程序执行出现错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
