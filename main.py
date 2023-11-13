import os
import tqdm
import requests

import interact

api_url = 'https://music.ghxi.com/wp-admin/admin-ajax.php'
secret_url = 'https://ghxcx.lovestu.com/api/index/today_secret'

def ajax(url, data, cookies = None):
    return requests.post(url, data=data, headers = {
        'Cache-Control': 'no-cache', 
        'Pragma': 'no-cache', 
        'Origin': 'https://music.ghxi.com', 
        'Referer': 'https://music.ghxi.com/', 
        'Sec-CH-UA': '" Not A;Brand";v="99", "Chromium";v="8"', 
        'Sec-CH-UA-Mobile': '?0', 
        'Sec-Fetch-Dest': 'empty', 
        'Sec-Fetch-Mode': 'cors', 
        'Sec-Fetch-Site': 'same-origin', 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36', 
        'X-Requested-With': 'XMLHttpRequest'
    }, cookies = cookies)

def get_secret():
    with requests.get(secret_url) as response:
        return response.json().get('data')

def get_authorized_cookies():
    with ajax(api_url, {
        'action': 'gh_music_ajax', 
        'type': 'postAuth', 
        'code': get_secret(), 
    }) as response:
        if response.json()['code'] == 200:
            return response.cookies

global_config = {
    'cookies': get_authorized_cookies(), 
    'type': 'qq', # 'wy'
}

def post(data, key='data'):
    with ajax(api_url, data, cookies=global_config['cookies']) as response:
        jsonData = response.json()
        if jsonData['code'] == 200:
            return jsonData.get(key)


def do_search(search_word):
    return post({
        'action': 'gh_music_ajax', 
        'type': 'search', 
        'music_type': global_config['type'], 
        'search_word': search_word
    })
    
def do_getMusicUrl(songid, filetype = 'flac'):
    return post({
        'action': 'gh_music_ajax', 
        'type': 'getMusicUrl', 
        'music_type': global_config['type'], 
        'music_size': filetype, 
        'songid': songid
    }, 'url')

def download_file(url, filepath, chunk_size = 2048):
    try:
        with requests.get(url, stream=True) as res:
            if not res.ok:
                raise requests.exceptions.HTTPError('response is not ok')
            totalSize = int(res.headers.get('Content-Length', '0'))
            pardir = os.path.split(filepath)[0]
            if pardir and not os.path.isdir(pardir):
                os.makedirs(pardir)
            with tqdm.tqdm(total=totalSize, unit='B', unit_scale=True, colour='#006699', leave=False, desc='Downloading: ') as pbar, \
                    open(filepath, 'wb') as fw:
                for chunk in res.iter_content(chunk_size=chunk_size):
                    if chunk:
                        chunkSize = len(chunk)
                        pbar.update(chunkSize)
                        fw.write(chunk)
    except Exception as e:
        if os.path.isfile(filepath):
            os.unlink(filepath)
        raise e

def try_to_download(songEntity):
    if (download_url := do_getMusicUrl(songEntity['songid'], 'flac' if songEntity['sizeflac'] else '320' if songEntity['size320'] else '128')) is not None:
        origin_fn, file_ext = os.path.splitext(os.path.basename(requests.utils.urlparse(download_url).path))
        song_title = f'{songEntity["singer"]} - {songEntity["songname"]}' + (f' [{songEntity["albumname"]}]' if songEntity["albumname"] else '')
        filename = f'{origin_fn} - {song_title}{file_ext}' \
                    .translate({ord(c): '_' for c in r'\/:*?"<>|'})
        try:
            download_file(download_url, 'Songs/' + filename)
        except Exception:
            print('Could not download...', file=interact.sys.stdout)

if __name__ == '__main__':
    scrollView = interact.ScrollView([], bottom_text=lambda conf: '回车下载 "{title}" 的音乐源文件。'.format(**conf), immediate=False)
    def key_input_handler(event):
        ch = event.detail['char']
        if ch == b'\x1b':
            scrollView.hide()
        elif ch == b'\x0d':
            if scrollView.displayed and not scrollView.paused:
                # scrollView.hide()
                scrollView.paused = True
                try_to_download(data[scrollView.option_index])
                scrollView.paused = False
                # scrollView.show()
    scrollView.addEventListener('key-input', key_input_handler)

    while True:
        try:
            keywords = input('请输入搜索的关键字：').strip()
            if keywords:
                data = do_search(keywords)
                if data is None or not len(data):
                    print('没有搜索到任何结果。')
                    continue
                songs_list = [
                    (f'{songEntity["singer"].strip()} - {songEntity["songname"].strip()}' + (f' [{songEntity["albumname"].strip()}]' if songEntity["albumname"].strip() else '') ).replace('\t', ' ')
                    for songEntity in data]
                scrollView.options = songs_list
                if scrollView.option_index >= len(songs_list):
                    scrollView.option_index = len(songs_list) - 1
                # interact.keyboard.add_hotkey('enter', enter_to_download)
                scrollView.show()
        except (KeyboardInterrupt, EOFError):
            print('\n已退出程序。')
            exit(0)
