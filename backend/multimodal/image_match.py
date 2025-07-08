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

file = "/Users/fengyihang/python_code/paper_evaluation/paper_image/clip_part.png"

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

    if resp.visual_search:
        logger.info("Visual Search:")
        for visual_item in resp.visual_search:
            logger.info(f"  Name: {visual_item.name}")
            logger.info(f"  URL: {visual_item.url}")
            logger.info(f"  Thumbnail URL: {visual_item.thumbnail}")
            logger.info(f"  Image URL: {visual_item.image_url}")
            logger.info("-" * 20)

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
            if entity.prfiles:
                logger.info("  Profiles:")
                for profile in entity.profiles:
                    logger.info(f"     {profile.get('social_network')}: {profile.get('url')}")

            logger.info("-" * 20)

    if resp.best_guess:
        logger.info(f"Best Guess: {resp.best_guess}")

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
    asyncio.run(demo_async())
    download_images_from_txt(SAVE_TXT, SAVE_DIR, 5)
