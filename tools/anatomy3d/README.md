# 3D-картинки упражнений: скелет с мышцами

Свои картинки, не чужие. Скелет и мышцы: открытая научная модель OpenSim (Rajagopal 2016, доработки Lai 2017 и Uhlrich 2022), репозиторий github.com/opensim-org/opensim-models. При публикации указывать источник модели. Рендер: three.js (MIT).

Цвета мышц по участию: 1 бордовый (главные), 2 светло-красный (вторые), 3 зелёный (помощники), 4 синий (в тонусе). Незадействованные не рисуются.

Ограничение модели: мышцы есть только у таза и ног (80 мышц). Для жима, тяг, плеч и рук нужна другая модель с мышцами корпуса и рук.

## Как сделать картинку
1. Модель: `GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --filter=blob:none --sparse https://github.com/opensim-org/opensim-models /home/user/opensim-org/opensim-models`, затем `git sparse-checkout set Models/Rajagopal Geometry`. Python: `pip install opensim==4.6 trimesh scipy`.
2. Поза в `poses/<упражнение>.json`: углы суставов (градусы), тиры мышц, гриф в системе корпуса (`bar_local`), хват (`grip`), желаемый локоть (`elbow_local`), сгибание пальцев `grip_curl` [пястно-фаланговый, средний, ногтевой, большой] (для грифа 25, 80, 45, 30): кисть обхватывает гриф.
3. Руки на гриф: `python3 tools/anatomy3d/hands_ik.py poses/<упражнение>.json`.
4. Сцена: `python3 tools/anatomy3d/export_pose.py poses/<упражнение>.json <scene.json>`.
5. Картинка: `node tools/anatomy3d/render.js <scene.json> <out.png> poses/<упражнение>.view.json` (камера, стрелки, штанга, легенда).
