from flask import Flask, render_template, request, send_file
import requests
import os
import datetime
import threading
import time

from crawler_core import CrawlerConfig, ForumCrawler, sanitize_name

app = Flask(__name__)

# 共享的爬虫实例
crawler_config = CrawlerConfig()
crawler = ForumCrawler(crawler_config)
status_lock = threading.Lock()
pause_event = threading.Event()
pause_event.set()
stop_event = threading.Event()
crawl_thread_ref = None
HISTORY_LIMIT = 10

# 爬取状态
crawl_status = {
    'running': False,
    'paused': False,
    'progress': 0,
    'total': 0,
    'magnet_count': 0,
    'image_count': 0,
    'current_page': 0,
    'message': '就绪',
    'current_url': '',
    'magnet_file': '',
    'url_file': '',
    'figures_dir': ''
}

# 最后生成的文件路径
last_generated_file = ''
last_generated_url_file = ''

# 存储当前爬取的磁力链接和地址（用于实时显示）
current_magnet_links = []
current_crawl_urls = []
crawl_history = []


def update_status(**kwargs):
    with status_lock:
        crawl_status.update(kwargs)


def snapshot_status():
    with status_lock:
        status = crawl_status.copy()
    status['magnet_file_name'] = os.path.basename(status['magnet_file']) if status['magnet_file'] else ''
    status['url_file_name'] = os.path.basename(status['url_file']) if status['url_file'] else ''
    status['history'] = list(crawl_history)
    return status


def reset_runtime_state():
    global current_magnet_links, current_crawl_urls, last_generated_file, last_generated_url_file
    current_magnet_links = []
    current_crawl_urls = []
    last_generated_file = ''
    last_generated_url_file = ''
    update_status(
        running=False,
        paused=False,
        progress=0,
        total=0,
        magnet_count=0,
        image_count=0,
        current_page=0,
        message='就绪',
        current_url='',
        magnet_file='',
        url_file='',
        figures_dir=''
    )


def record_history(entry):
    crawl_history.insert(0, entry)
    del crawl_history[HISTORY_LIMIT:]

def parse_topzh_use_bs(url_address: str):
    """
    使用beautifulSoup提取网页中的有效链接
    """
    try:
        return set(crawler.fetch_thread_paths_from_forum_url(url_address))
    except requests.RequestException as e:
        update_status(message=f'提取链接时出错: {str(e)}')
        return set()

def parse_content_use_bs(url: str, save_images=False, figures_dir=None):
    """
    使用BeautifulSoup提取网页中的磁力链接和图片
    """
    try:
        magnet_links, image_urls, soup = crawler.fetch_thread_details(url)
    except requests.RequestException as e:
        update_status(message=f'提取内容时出错: {str(e)}')
        return [], 0, 0

    images_saved = 0
    skipped_images = 0
    if save_images and figures_dir and image_urls:
        dirname = sanitize_name(soup.title.text if soup.title else url)
        save_dir = os.path.join(figures_dir, dirname)
        saved, skipped = crawler.download_images(image_urls, save_dir)
        images_saved += saved
        if skipped:
            skipped_images += len(skipped)
            print(f'Skipped {len(skipped)} images while saving "{dirname}"')

    return magnet_links, images_saved, skipped_images

def crawl_thread(base_url, url_pattern, pages, save_images=False, forum_id='103'):
    """
    爬虫线程函数
    """
    global last_generated_file, last_generated_url_file, current_magnet_links, current_crawl_urls, crawl_thread_ref

    update_status(
        running=True,
        paused=False,
        progress=0,
        total=pages,
        magnet_count=0,
        image_count=0,
        current_page=0,
        message='开始爬取...',
        current_url=''
    )
    current_magnet_links = []
    current_crawl_urls = []

    figures_dir = None
    if save_images:
        now = datetime.datetime.now()
        formatted_datetime = now.strftime("%Y_%m_%d_%H_%M_%S")
        figures_dir = f"data/figures/forum_{forum_id}_{formatted_datetime}"
        os.makedirs(figures_dir, exist_ok=True)
        update_status(figures_dir=figures_dir)

    os.makedirs('data', exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    file_path = f"data/magnet_file_{timestamp}.txt"
    url_file_path = f"data/url_file_{timestamp}.txt"
    last_generated_file = file_path
    last_generated_url_file = url_file_path
    update_status(magnet_file=file_path, url_file=url_file_path)

    magnet_total = 0
    image_total = 0
    skipped_image_total = 0

    try:
        for page in range(1, pages + 1):
            if stop_event.is_set():
                update_status(message='爬取已停止', current_url='')
                break

            pause_event.wait()
            update_status(current_page=page, message=f'正在获取第 {page} 页的帖子链接...')
            current_url = url_pattern.format(page)

            urls = parse_topzh_use_bs(current_url)
            if not urls:
                update_status(message=f'第 {page} 页没有找到帖子链接', progress=page)
                continue

            update_status(message=f'正在从第 {page} 页帖子中提取磁力链接...')
            for url in urls:
                if stop_event.is_set():
                    update_status(message='爬取已停止', current_url='')
                    break
                pause_event.wait()

                full_url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
                update_status(current_url=full_url)

                with open(url_file_path, 'a', encoding='utf-8') as url_file:
                    url_file.write(full_url + '\n')
                current_crawl_urls.append(full_url)

                magnets, saved_images, skipped_images = parse_content_use_bs(full_url, save_images, figures_dir)
                if magnets:
                    with open(file_path, 'a', encoding='utf-8') as fh:
                        for magnet in magnets:
                            fh.write(magnet + '\n')
                    magnet_total += len(magnets)
                    current_magnet_links.extend(magnets)
                    update_status(magnet_count=magnet_total)
                if saved_images or skipped_images:
                    image_total += saved_images
                    skipped_image_total += skipped_images
                    status_msg = f'Images saved: {image_total}'
                    if skipped_image_total:
                        status_msg += f' (skipped {skipped_image_total})'
                    update_status(image_count=image_total, message=status_msg)

            update_status(progress=page)
            time.sleep(1)

        else:
            msg = f'爬取完成！共获取 {magnet_total} 个磁力链接'
            if image_total > 0:
                msg += f'，{image_total} 张图片'
            if skipped_image_total:
                msg += f'，跳过 {skipped_image_total} 张图片'
            update_status(message=msg, current_url='', progress=pages)

        if not stop_event.is_set():
            record_history({
                'timestamp': timestamp,
                'forum_id': forum_id,
                'pages': pages,
                'magnets': magnet_total,
                'images': image_total,
                'images_skipped': skipped_image_total,
                'magnet_file': file_path,
                'url_file': url_file_path,
                'figures_dir': figures_dir
            })

    except Exception as e:
        update_status(message=f'爬取过程中出错: {str(e)}', current_url='')
    finally:
        update_status(running=False, paused=False)
        pause_event.set()
        crawl_thread_ref = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_crawl', methods=['POST'])
def start_crawl():
    global crawl_thread_ref
    if crawl_status['running']:
        return {'status': 'error', 'message': '爬虫正在运行中，请稍后再试'}
    
    # 获取表单数据
    forum_id = request.form.get('forum_id', '103')  # 默认板块ID
    try:
        pages = int(request.form.get('pages', '1'))
    except ValueError:
        pages = 1
    pages = max(1, min(20, pages))
    custom_cookie = request.form.get('cookie', '')  # 获取用户输入的Cookie
    save_images = request.form.get('save_images', 'false').lower() == 'true'  # 获取是否保存图片的选项
    
    base_url = request.form.get('base_url', crawler.config.base_url)
    update_kwargs = {'base_url': base_url}
    if custom_cookie.strip():
        update_kwargs['cookie'] = custom_cookie.strip()
    crawler.update_config(**update_kwargs)
    reset_runtime_state()
    pause_event.set()
    stop_event.clear()
    
    # 构建URL模式
    url_pattern = f"{crawler.config.base_url}/forum-{forum_id}-{{}}.html"
    
    # 启动爬虫线程
    crawl_thread_ref = threading.Thread(
        target=crawl_thread,
        args=(crawler.config.base_url, url_pattern, pages, save_images, forum_id),
        daemon=True,
    )
    crawl_thread_ref.start()
    
    return {'status': 'success', 'message': '爬虫已启动'}

@app.route('/crawl_status')
def get_crawl_status():
    return snapshot_status()

@app.route('/update_image_cookie', methods=['POST'])
def update_image_cookie():
    custom_cookie = request.form.get('cookie', '')
    
    if custom_cookie.strip():
        crawler.update_config(image_cookie=custom_cookie.strip())
        return {
            'status': 'success',
            'message': '图片下载Cookie已更新',
            'current_cookie': crawler.config.image_cookie or ''
        }
    else:
        return {'status': 'error', 'message': 'Cookie值不能为空'}

@app.route('/get_image_cookie')
def get_image_cookie():
    return {'current_cookie': crawler.config.image_cookie or ''}

@app.route('/pause_crawl')
def pause_crawl():
    if crawl_status['running'] and not crawl_status['paused']:
        pause_event.clear()
        update_status(paused=True, message='爬取已暂停')
        return {'status': 'success', 'message': '爬虫已暂停'}
    return {'status': 'error', 'message': '爬虫未在运行或已暂停'}

@app.route('/resume_crawl')
def resume_crawl():
    if crawl_status['running'] and crawl_status['paused']:
        pause_event.set()
        update_status(paused=False, message='爬取已恢复')
        return {'status': 'success', 'message': '爬虫已恢复'}
    return {'status': 'error', 'message': '爬虫未在运行或未暂停'}

@app.route('/stop_crawl')
def stop_crawl():
    if crawl_status['running']:
        stop_event.set()
        pause_event.set()
        update_status(paused=False, message='正在停止爬虫...')
        return {'status': 'success', 'message': '停止命令已发送'}
    return {'status': 'error', 'message': '爬虫未在运行'}

@app.route('/download')
def download_file():
    global last_generated_file
    if not last_generated_file or not os.path.exists(last_generated_file):
        return {'status': 'error', 'message': '没有可下载的磁力链接文件'}
    
    return send_file(last_generated_file, as_attachment=True)

@app.route('/download_urls')
def download_url_file():
    global last_generated_url_file
    if not last_generated_url_file or not os.path.exists(last_generated_url_file):
        return {'status': 'error', 'message': '没有可下载的爬取地址文件'}
    
    return send_file(last_generated_url_file, as_attachment=True)

@app.route('/update_cookie', methods=['POST'])
def update_cookie():
    """
    更新当前使用的Cookie
    """
    custom_cookie = request.form.get('cookie', '')
    
    if not custom_cookie.strip():
        return {'status': 'error', 'message': 'Cookie值不能为空'}
    
    crawler.update_config(cookie=custom_cookie.strip())
    
    return {'status': 'success', 'message': 'Cookie更新成功'}

@app.route('/get_current_cookie')
def get_current_cookie():
    """
    获取当前使用的Cookie
    """
    return {'status': 'success', 'cookie': crawler.config.cookie or ''}

@app.route('/get_magnet_links')
def get_magnet_links():
    """
    获取当前爬取的所有磁力链接
    """
    return current_magnet_links

@app.route('/get_crawl_urls')
def get_crawl_urls():
    """
    获取当前爬取的所有地址
    """
    return current_crawl_urls

@app.route('/crawl_history')
def get_crawl_history():
    return {'history': list(crawl_history)}

if __name__ == '__main__':
    app.run(debug=True)
