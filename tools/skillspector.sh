#!/usr/bin/env bash
# Проверка скилла сканером NVIDIA SkillSpector перед установкой.
# Сканер ставится сам при первом запуске (в ~/.cache/skillspector), версия закреплена коммитом.
# Запуск: tools/skillspector.sh <папка | zip | SKILL.md | git-ссылка> [ещё флаги skillspector scan]
# Вывод: оценка риска 0-100 и вердикт. Код выхода 1, если найдены проблемы.
set -euo pipefail

COMMIT=a5425e594d59a14c3d3eaa39e26847613ba08696
VENV="$HOME/.cache/skillspector/venv"

if [ ! -x "$VENV/bin/skillspector" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q "git+https://github.com/NVIDIA/SkillSpector.git@$COMMIT"
fi

[ $# -ge 1 ] || { echo 'Укажи, что проверить: папку скилла, zip, SKILL.md или git-ссылку.'; exit 2; }
exec "$VENV/bin/skillspector" scan --no-llm --fail-on-findings "$@"
