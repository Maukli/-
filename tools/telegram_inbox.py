# Читает сообщения, которые Микаел переслал своему Telegram-боту.
# Токен берётся из переменной окружения TELEGRAM_BOT_TOKEN (запасное имя mpetrosyan_cloude_bot,
# под ним токен сохранён в окружении Default) и никуда не выводится.
# Запуск: python3 tools/telegram_inbox.py [--check] [--download DIR]
#   --check     только проверить, что бот отвечает
#   --download  скачать фото и видео из новых сообщений в папку DIR
# Прочитанные сообщения подтверждаются (offset), повторно они не придут.
import json, os, sys, urllib.request

TOKEN_VARS = ('TELEGRAM_BOT_TOKEN', 'mpetrosyan_cloude_bot')
TOKEN = next((os.environ[v] for v in TOKEN_VARS if os.environ.get(v)), None)
if not TOKEN:
    sys.exit(f'Нет переменной {" или ".join(TOKEN_VARS)}: её добавляют в настройках облачного окружения, видна в новой сессии.')
API = f'https://api.telegram.org/bot{TOKEN}/'
FILE_API = f'https://api.telegram.org/file/bot{TOKEN}/'


def call(method, **params):
    data = json.dumps(params).encode()
    req = urllib.request.Request(API + method, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if not res.get('ok'):
        sys.exit(f'Ошибка Telegram: {res.get("description")}')
    return res['result']


def main():
    args = sys.argv[1:]
    me = call('getMe')
    print(f'Бот: @{me["username"]}')
    if '--check' in args:
        return
    out = args[args.index('--download') + 1] if '--download' in args else None
    updates = call('getUpdates', timeout=0)
    if not updates:
        print('Новых сообщений нет.')
        return
    for u in updates:
        m = u.get('message') or u.get('channel_post') or {}
        origin = m.get('forward_origin', {})
        src = origin.get('chat', {}).get('title') or origin.get('sender_user', {}).get('first_name') or origin.get('sender_user_name') or ''
        text = m.get('text') or m.get('caption') or ''
        media = []
        if m.get('photo'):
            media.append(('photo', m['photo'][-1]['file_id']))
        for kind in ('video', 'document', 'animation'):
            if m.get(kind):
                media.append((kind, m[kind]['file_id']))
        print(f'--- #{m.get("message_id")} {"переслано из: " + src if src else ""}')
        if text:
            print(text)
        for kind, fid in media:
            line = f'[{kind}]'
            if out:
                os.makedirs(out, exist_ok=True)
                path = call('getFile', file_id=fid).get('file_path')
                if path:
                    dst = os.path.join(out, f'{m.get("message_id")}_{os.path.basename(path)}')
                    urllib.request.urlretrieve(FILE_API + path, dst)
                    line += f' {dst}'
            print(line)
    call('getUpdates', offset=updates[-1]['update_id'] + 1, timeout=0)


if __name__ == '__main__':
    main()
