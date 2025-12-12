from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import os
import datetime
import threading
import time

app = Flask(__name__)

# 默认headers
default_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    "Cookie": "cPNj_2132_saltkey=IJz8uk80; cPNj_2132_lastvisit=1764366895; cPNj_2132_lastfp=0fdb7fc9f2ebcac91b1e52ed50162555; cPNj_2132_atarget=1; cPNj_2132_st_p=0%7C1764464228%7Cb30bb17f02f39447cc68a8a37741985e; cPNj_2132_st_t=0%7C1764679402%7C644a19807b4abb1d91b1699cadadda99; cPNj_2132_visitedfid=38D37D103; cPNj_2132_viewid=tid_3167763; sl-session=BfF5KBJZOmn6RtBgdnhmAw==; _safe=azh5Pzhj15y11j6o; cPNj_2132_lastact=1765345551%09index.php%09"
}

# 图片下载专用headers
image_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    "Cookie": "cf_clearance=g_P5Eml.uqRnBRosJ1YO4QcXDXUYs_hMFFlO2QlIbxA-1765463791-1.2.1.1-d0zzfiajVwC_Ey6xtppIUuKaVvPF3wutJu3vMkzc3BfjOmh4.XN57zK0ZNRTYpF9HwErtL_cso1bUb4V8AqQ35ckz6iE1dFMaZDlNR8UE0xI41VBZqdy2p3Km2bH4F7myXpg62Vzzez8B8vIxCsQMd22e3bNAbVAlM1UmJaWCepVrP.ODHK5UVR8Vcc7CamnwsUQjDm7PP1omZR6P9Z1A16iyGXBgLrvH3NXj_MrVHs"
}

# 当前使用的headers
current_headers = default_headers.copy()

# 当前使用的基础URL
current_base_url = "https://btd5.thsf7.net"

# 爬取状态
crawl_status = {
    'running': False,
    'paused': False,
    'progress': 0,
    'total': 0,
    'magnet_count': 0,
    'image_count': 0,
    'current_page': 0,
    'message': '',
    'current_url': ''
}

# 最后生成的文件路径
last_generated_file = ''
last_generated_url_file = ''

# 存储当前爬取的磁力链接和地址（用于实时显示）
current_magnet_links = []
current_crawl_urls = []

def parse_topzh_use_bs(url_address: str):
    """
    使用beautifulSoup提取网页中的有效链接
    """
    try:
        response = requests.get(url=url_address, headers=current_headers, timeout=10)
        soup = BeautifulSoup(response.content, "lxml")
        results = set()
        links = soup.find_all('a')
        for link in links:
            link_url = link.get('href')
            if link_url:
                if link_url.startswith('thread') and link_url.endswith('.html'):
                    split_link = link_url.split('-')
                    if len(split_link) == 4:
                        link_url = split_link[0] + '-' + split_link[1] + '-1-' + split_link[3]
                        results.add(link_url)
        return results
    except Exception as e:
        crawl_status['message'] = f'提取链接时出错: {str(e)}'
        return set()

def parse_content_use_bs(url: str, save_images=False, figures_dir=None):
    """
    使用BeautifulSoup提取网页中的磁力链接和图片
    """
    try:
        r = requests.get(url=url, headers=current_headers, timeout=10)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.content, "lxml")
        
        # 获取磁力链接
        magnet_links = []
        for link in soup.find_all('li'):
            magnet_link = link.get_text()
            if magnet_link.startswith('magnet:?xt'):
                magnet_links.append(magnet_link)
        

        # 获取并保存图片
        if save_images and figures_dir:
            # 获取图片URL
            image_urls = []
            for img in soup.find_all('img'):
                # 尝试不同的属性名
                image_url = img.get('file') or img.get('src')
                if image_url:
                    # 如果是相对URL，转换为绝对URL
                    if not image_url.startswith(('http://', 'https://')):
                        if image_url.startswith('/'):
                            image_url = f"https://btd5.thsf7.net{image_url}"
                        else:
                            continue  # 跳过无法处理的相对路径
                    image_urls.append(image_url)
            
            dirname = soup.title.text
            dirname = dirname.split(' ')
            dirname = dirname[0]
            save_dir = figures_dir + "/" + dirname
            print(save_dir)

            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            # 保存图片
            for image_url in image_urls:
                try:
                    # 1. 先检测图片是否可访问
                    print(f'检测图片: {image_url}')
                    head_response = requests.head(image_url, headers=image_headers, timeout=5, allow_redirects=True)
                    
                    # 检查响应状态码和Content-Type
                    if head_response.status_code != 200:
                        print(f'图片不可访问 (状态码: {head_response.status_code}): {image_url}')
                        continue
                    
                    content_type = head_response.headers.get('Content-Type', '')
                    if not content_type.startswith('image/'):
                        print(f'不是有效图片类型 ({content_type}): {image_url}')
                        continue
                    
                    # 2. 图片可访问，进行保存操作
                    print(f'开始保存图片: {image_url}')
                    filename = image_url.split('/')[-1]
                    if not filename:
                        continue  # 跳过没有文件名的URL
                    
                    # 确保文件名合法
                    filename = filename.split('?')[0]  # 移除URL参数
                    if not filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                        filename += '.jpg'  # 默认使用jpg扩展名
                    
                    save_path = os.path.join(save_dir, filename)
                    
                    # 下载图片 - 使用图片专用headers
                    response = requests.get(image_url, headers=image_headers, timeout=10)
                    if response.status_code == 200:
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                        crawl_status['image_count'] += 1
                        print(f'图片保存成功: {image_url}')
                        print(f'保存路径: {save_path}')
                except Exception as e:
                    # 记录图片保存错误，但不中断整个爬取过程
                    print(f'处理图片出错: {image_url} - {str(e)}')
        
        return magnet_links
    except Exception as e:
        crawl_status['message'] = f'提取内容时出错: {str(e)}'
        return []

def crawl_thread(base_url, url_pattern, pages, save_images=False, forum_id='103'):
    """
    爬虫线程函数
    """
    global last_generated_file, current_magnet_links, current_crawl_urls
    
    # 重置当前存储的链接
    current_magnet_links = []
    current_crawl_urls = []
    
    crawl_status['running'] = True
    crawl_status['progress'] = 0
    crawl_status['total'] = pages
    crawl_status['magnet_count'] = 0
    crawl_status['image_count'] = 0
    crawl_status['current_page'] = 0
    crawl_status['message'] = '开始爬取...'
    
    # 创建图片保存目录（如果需要保存图片）
    figures_dir = None
    if save_images:
        now = datetime.datetime.now()
        formatted_datetime = now.strftime("%Y_%m_%d_%H_%M_%S")
        figures_dir = f"data/figures/forum_{forum_id}_{formatted_datetime}"
        if not os.path.exists(figures_dir):
            os.makedirs(figures_dir)
    
    # 创建data目录（如果不存在）
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # 生成文件名
    now = datetime.datetime.now()
    formatted_datetime = now.strftime("%Y_%m_%d_%H_%M_%S")
    file_path = f"data/magnet_file_{formatted_datetime}.txt"
    last_generated_file = file_path
    
    # 生成爬取地址文件名
    url_file_path = f"data/url_file_{formatted_datetime}.txt"
    last_generated_url_file = url_file_path
    
    try:
        for page in range(1, pages + 1):
            crawl_status['current_page'] = page
            crawl_status['message'] = f'正在爬取第 {page} 页...'
            
            # 构建当前页面URL
            current_url = url_pattern.format(page)
            
            # 获取帖子链接
            crawl_status['message'] = f'正在获取第 {page} 页的帖子链接...'
            urls = parse_topzh_use_bs(current_url)
            
            if not urls:
                crawl_status['message'] = f'第 {page} 页没有找到帖子链接'
                continue
            
            # 提取磁力链接
            crawl_status['message'] = f'正在从第 {page} 页的帖子中提取磁力链接...'
            for url in urls:
                full_url = f"{base_url}/{url}"
                print(full_url)
                
                crawl_status['current_url'] = full_url
                
                # 将爬取地址写入文件并存储到全局变量
                with open(url_file_path, 'a', encoding='utf-8') as url_file:
                    url_file.write(full_url + '\n')
                    
                # 添加到全局变量
                current_crawl_urls.append(full_url)
                
                # 提取内容（包括磁力链接和图片）
                magnets = parse_content_use_bs(full_url, save_images, figures_dir)
                if magnets:
                    with open(file_path, 'a', encoding='utf-8') as f:
                        for magnet in magnets:
                            f.write(magnet + '\n')
                            crawl_status['magnet_count'] += 1
                            # 添加到全局变量
                            current_magnet_links.append(magnet)
            
            # 检查是否需要暂停
            while crawl_status['paused']:
                time.sleep(0.5)
                if not crawl_status['running']:  # 如果在暂停时被停止，直接退出
                    return
            
            # 更新进度
            crawl_status['progress'] = page
            time.sleep(1)  # 避免爬取过快
        
        # 爬取完成信息
        if crawl_status['image_count'] > 0:
            crawl_status['message'] = f'爬取完成！共获取 {crawl_status["magnet_count"]} 个磁力链接，{crawl_status["image_count"]} 张图片'
        else:
            crawl_status['message'] = f'爬取完成！共获取 {crawl_status["magnet_count"]} 个磁力链接'
    except Exception as e:
        crawl_status['message'] = f'爬取过程中出错: {str(e)}'
    finally:
        crawl_status['running'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_crawl', methods=['POST'])
def start_crawl():
    if crawl_status['running']:
        return {'status': 'error', 'message': '爬虫正在运行中，请稍后再试'}
    
    # 获取表单数据
    forum_id = request.form.get('forum_id', '103')  # 默认板块ID
    pages = int(request.form.get('pages', '1'))
    custom_cookie = request.form.get('cookie', '')  # 获取用户输入的Cookie
    save_images = request.form.get('save_images', 'false').lower() == 'true'  # 获取是否保存图片的选项
    
    # 更新当前使用的headers
    global current_headers, current_base_url
    base_url = request.form.get('base_url', current_base_url)  # 获取用户输入的基础URL
    current_headers = default_headers.copy()
    current_base_url = base_url
    
    if custom_cookie.strip():
        current_headers['Cookie'] = custom_cookie.strip()
    
    # 构建URL模式
    url_pattern = f"{base_url}/forum-{forum_id}-{{}}.html"
    
    # 启动爬虫线程
    threading.Thread(target=crawl_thread, args=(base_url, url_pattern, pages, save_images, forum_id)).start()
    
    return {'status': 'success', 'message': '爬虫已启动'}

@app.route('/crawl_status')
def get_crawl_status():
    return crawl_status

@app.route('/update_image_cookie', methods=['POST'])
def update_image_cookie():
    global image_headers
    custom_cookie = request.form.get('cookie', '')
    
    if custom_cookie.strip():
        image_headers['Cookie'] = custom_cookie.strip()
        return {'status': 'success', 'message': '图片下载Cookie已更新', 'current_cookie': image_headers['Cookie']}
    else:
        return {'status': 'error', 'message': 'Cookie值不能为空'}

@app.route('/get_image_cookie')
def get_image_cookie():
    return {'current_cookie': image_headers.get('Cookie', '')}

@app.route('/pause_crawl')
def pause_crawl():
    if crawl_status['running'] and not crawl_status['paused']:
        crawl_status['paused'] = True
        crawl_status['message'] = '爬取已暂停'
        return {'status': 'success', 'message': '爬虫已暂停'}
    return {'status': 'error', 'message': '爬虫未在运行或已暂停'}

@app.route('/resume_crawl')
def resume_crawl():
    if crawl_status['running'] and crawl_status['paused']:
        crawl_status['paused'] = False
        crawl_status['message'] = '爬取已恢复'
        return {'status': 'success', 'message': '爬虫已恢复'}
    return {'status': 'error', 'message': '爬虫未在运行或未暂停'}

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
    global current_headers
    custom_cookie = request.form.get('cookie', '')
    
    if not custom_cookie.strip():
        return {'status': 'error', 'message': 'Cookie值不能为空'}
    
    # 更新当前使用的headers中的Cookie
    current_headers = default_headers.copy()
    current_headers['Cookie'] = custom_cookie.strip()
    
    return {'status': 'success', 'message': 'Cookie更新成功'}

@app.route('/get_current_cookie')
def get_current_cookie():
    """
    获取当前使用的Cookie
    """
    return {'status': 'success', 'cookie': current_headers.get('Cookie', '')}

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

if __name__ == '__main__':
    app.run(debug=True)
