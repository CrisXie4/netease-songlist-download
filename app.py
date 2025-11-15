import requests
import os
import json
import sys

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

def get_playlist_detail(playlist_id):
    """获取歌单详情"""
    url = 'https://www.oiapi.net/api/NeteasePlaylistDetail'
    data = {'id': playlist_id}
    r = requests.get(url=url, params=data)
    return r.json()

def download_song(song_id, song_name, title=True):
    """下载歌曲"""
    api_url = 'https://api.paugram.com/netease'
    params = {'id': song_id, 'title': str(title).lower()}

    try:
        print(f'正在获取音频链接: {song_name}...')

        # 第一步：获取音频链接
        response = requests.get(url=api_url, params=params, timeout=10)

        if response.status_code != 200:
            print(f'✗ 获取链接失败: {song_name} (状态码: {response.status_code})')
            return False

        # 解析JSON获取真正的音频链接
        data = response.json()
        audio_link = data.get('link')

        if not audio_link:
            print(f'✗ 未找到音频链接: {song_name}')
            return False

        print(f'正在下载音频: {song_name}...')

        # 第二步：下载真正的音频文件
        audio_response = requests.get(audio_link, stream=True, timeout=30)

        if audio_response.status_code != 200:
            print(f'✗ 下载失败: {song_name} (状态码: {audio_response.status_code})')
            return False

        # 创建music文件夹
        if not os.path.exists('music'):
            os.makedirs('music')

        # 清理文件名中的非法字符
        safe_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_', '(', ')')).strip()
        file_path = f'music/{safe_name}.mp3'

        # 下载文件
        with open(file_path, 'wb') as f:
            for chunk in audio_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f'✓ 下载成功: {song_name}')
        return True

    except requests.exceptions.Timeout:
        print(f'✗ 下载超时: {song_name}')
        return False
    except Exception as e:
        print(f'✗ 下载出错: {song_name} - {str(e)}')
        return False

def display_songs(songs):
    """显示歌曲列表"""
    print('\n' + '=' * 80)
    print('歌曲列表：')
    print('=' * 80)
    for idx, song in enumerate(songs, 1):
        song_name = song.get('name')
        artists = ', '.join([artist.get('name', '') for artist in song.get('artists', [])])
        print(f'{idx:3d}. {song_name} - {artists}')
    print('=' * 80)

def get_user_selection(total_songs):
    """获取用户选择的歌曲序号"""
    print('\n选择下载方式：')
    print('1. 下载全部歌曲')
    print('2. 选择特定歌曲下载')

    choice = input('\n请选择 (1/2): ').strip()

    if choice == '1':
        return list(range(1, total_songs + 1))
    elif choice == '2':
        print('\n请输入要下载的歌曲序号：')
        print('提示：')
        print('  - 单个歌曲：输入序号，如 "3"')
        print('  - 多个歌曲：用逗号分隔，如 "1,3,5"')
        print('  - 连续范围：用短横线连接，如 "1-5"')
        print('  - 混合使用：如 "1,3-5,8"')

        selection_input = input('\n请输入: ').strip()
        selected = set()

        try:
            # 解析用户输入
            parts = selection_input.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # 处理范围，如 "1-5"
                    start, end = part.split('-')
                    start, end = int(start.strip()), int(end.strip())
                    if start < 1 or end > total_songs or start > end:
                        print(f'警告：范围 {start}-{end} 无效，已忽略')
                        continue
                    selected.update(range(start, end + 1))
                else:
                    # 处理单个数字
                    num = int(part)
                    if num < 1 or num > total_songs:
                        print(f'警告：序号 {num} 超出范围，已忽略')
                        continue
                    selected.add(num)

            return sorted(list(selected))
        except ValueError:
            print('输入格式错误！')
            return []
    else:
        print('无效的选择！')
        return []

def main():
    # 获取歌单ID
    playlist_id = int(input('请输入歌单ID：'))

    # 获取歌单详情
    print('正在获取歌单信息...')
    result = get_playlist_detail(playlist_id)

    if result.get('code') != 1:
        print('获取歌单失败！')
        return

    songs = result.get('data', [])
    print(f'\n找到 {len(songs)} 首歌曲')

    # 显示歌曲列表
    display_songs(songs)

    # 获取用户选择
    selected_indices = get_user_selection(len(songs))

    if not selected_indices:
        print('没有选择任何歌曲，退出程序')
        return

    print(f'\n将要下载 {len(selected_indices)} 首歌曲')

    # 确认下载
    confirm = input('确认开始下载？(y/n): ')
    if confirm.lower() != 'y':
        print('取消下载')
        return

    # 下载选中的歌曲
    success_count = 0
    for count, idx in enumerate(selected_indices, 1):
        song = songs[idx - 1]  # 列表索引从0开始
        song_id = song.get('id')
        song_name = song.get('name')
        artists = ', '.join([artist.get('name', '') for artist in song.get('artists', [])])

        print(f'\n[{count}/{len(selected_indices)}] {song_name} - {artists}')

        if download_song(song_id, f'{song_name} - {artists}'):
            success_count += 1

    print(f'\n下载完成！成功: {success_count}/{len(selected_indices)}')

if __name__ == '__main__':
    main()