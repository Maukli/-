# Источники иллюстраций

Фото упражнений взяты из открытой базы free-exercise-db (github.com/yuhonas/free-exercise-db).
Лицензия Unlicense: общественное достояние, можно менять и использовать в коммерческих публикациях без указания автора.

Обработка кодом (prepare.py): вырезан фон нейросетью BiRefNet lite (лицензия MIT), подрезка, приглушены цвета.
На слайде фото стоит на фоне темы со светящимся кругом в цвете акцента. Утка на обложке нарисована кодом (render_slides.js).

Модель для вырезания фона в репозиторий не входит: ~/.u2net/birefnet_lite.onnx
(huggingface.co/onnx-community/BiRefNet_lite-ONNX, onnx/model.onnx).

## Свои фото (папка own/, в git не попадает)
| Файл | Что | Согласие |
|---|---|---|
| own/client_side_01.jpg | Клиент Микаела сбоку, передний наклон таза | Микаел подтвердил использование 23.10 ("Добро"). Лицо размыто |

## Фото на слайдах с 26.10
Лицензия Pexels: бесплатно, коммерческое использование и изменения разрешены, подпись не нужна (pexels.com/license).
| Файл | Где | Страница источника | Лицензия |
|---|---|---|---|
| src/px_5829910.jpg | c2 обложка | pexels.com/photo/cellphone-and-man-practicing-5829910 | Pexels |
| src/px_4162596.jpg | c2 слайд 2 | pexels.com/photo/man-sitting-on-stairs-with-headphones-4162596 | Pexels |
| src/px_27810163.jpg | c2 слайд 5 | pexels.com/photo/a-barbell-and-weights-on-the-floor-in-a-gym-27810163 | Pexels |
| src/px_9898392.jpg | c2 слайд 9 | pexels.com/photo/a-person-holding-a-cellphone-9898392 | Pexels |
| src/px_4519057.jpg | c3 обложка | pexels.com/photo/close-up-of-plates-with-healthy-food-4519057 | Pexels |
| src/px_7991910.jpg | c3 слайд 2 | pexels.com/photo/legs-in-socks-standing-on-scale-7991910 | Pexels |
| src/px_1640777.jpg | c3 слайд 3 | pexels.com/photo/flat-lay-photography-of-vegetable-salad-on-plate-1640777 | Pexels |
| src/px_15319043.jpg | c3 слайд 4 | pexels.com/photo/dietitian-measuring-waist-15319043 | Pexels |
| src/px_10680710.jpg | c3 слайд 5 | pexels.com/photo/vegetable-salad-on-white-ceramic-plate-10680710 | Pexels |
| src/px_9615241.jpg | c3 слайд 7 | pexels.com/photo/man-bed-bedroom-morning-9615241 | Pexels |
| src/px_7343000.jpg | c3 слайд 9 | pexels.com/photo/person-using-smartphone-7343000 | Pexels |
| src/c1_04..07, src/fedb_*.jpg | c1 слайды 4-7, c2 слайды 3, 4, 6, 7, 8, c3 слайд 6 | free-exercise-db (github.com/yuhonas/free-exercise-db) | Unlicense |
| own/client_side_01_*.jpg | c1 слайды 1, 2, 3, 9 | фото клиента Микаела, лицо размыто | согласие подтвердил Микаел 23.10 |

## Фото Микаела (прислал сам 26.10 для публикации)
| Файл | Где | Обработка |
|---|---|---|
| src/mikael_bench.jpg | c2 слайд 3 | без изменений, кадрирование |
| src/mikael_pullup.jpg | c2 слайд 7 | обрезаны полосы скриншота, размыт человек на заднем плане |
| src/mikael_curl.jpg | c3 слайд 6 | обрезаны полосы скриншота, размыты люди на заднем плане |
| src/mikael_sideplank.jpg | c1 слайд 8 | без изменений |
Оригиналы лежат в own/ (вне git).

## Карусель c4 "Тир-лист: грудь" (12.11)
| Файл | Где | Источник | Лицензия |
|---|---|---|---|
| src/c4_*.jpg | слайды 2-7 | free-exercise-db (github.com/yuhonas/free-exercise-db) | Unlicense |
| src/fedb_Barbell_Bench_Press_-_Medium_Grip_0.jpg | слайд 2 | free-exercise-db | Unlicense |
| src/mikael_bench.jpg | обложка | фото Микаела (прислал 26.10) | своё |
| src/mikael_challenge_stand.jpg | слайд 8 | кадр из видео челленджа Микаела 07.11, цвет как в челлендже | своё |

## Карусели c5-c7 (18.11, версия 2 с графикой)
Графика на слайдах (шкалы, схемы, углы, номера точек) нарисована кодом: content/carousels/build_18-11.py. Подсветка мышц: img/glow.py (маска MediaPipe Pose).
| Файл | Где | Источник | Лицензия |
|---|---|---|---|
| src/c5_gym_phone.jpg (IMG_9694), c5_smile.jpg (IMG_9704), c6_cover.jpg (IMG_9686), c6_cta.jpg (IMG_9695), c7_phone.jpg (IMG_9709) | c5 слайды 7-8, c6 слайды 1 и 9, c7 слайд 3 | фото Микаела со съёмки про осанку 12.11 (Google Диск) | своё |
| src/c7_cover.jpg, c7_bad.jpg, c7_good_side.jpg, c7_good_close.jpg, c7_good_top.jpg, c7_protocol.jpg, c7_cta.jpg | c7 | кадры из видео Микаела (IMG_9691, 9668, 9669, 9667, 9673, 9692), увеличены Real-ESRGAN general x4v3 (BSD-3), люди на заднем плане размыты. c7_cta.jpg с ухмылкой больше не используется | своё |
| src/c7_cta_calm.jpg | c7 слайд 8 (с 19.11) | кадр IMG_9673 на 13,9 с, спокойное лицо в камеру (правило 18.11 про лица), Real-ESRGAN, фон размыт по маске MediaPipe | своё |
| src/mikael_bench.jpg, mikael_curl.jpg, mikael_pullup.jpg | c5 слайды 2-3, c6 слайд 4 | фото Микаела (прислал 26.10) | своё |
| src/c5_night.jpg | c5 обложка | pexels.com/photo/light-dawn-sunset-man-6944004 | Pexels |
| src/c5_tired_gym.jpg | c5 обложка | pexels.com/photo/tired-male-athlete-resting-on-bench-during-weightlifting-workout-in-gym-3838706 | Pexels |
| src/c5_clock.jpg | c5 слайд 4 | pexels.com/photo/old-style-alarm-clock-in-a-dark-room-18542702 | Pexels |
| src/c5_bedroom.jpg | c5 слайд 5 | pexels.com/photo/books-bed-stack-standing-9615255 | Pexels |
| src/c6_scoop.jpg | c6 слайд 2 | pexels.com/photo/photo-of-a-white-powder-and-a-scoop-lying-on-the-blue-background-12625114 | Pexels |
| src/c6_container.jpg | c6 слайды 3 и 8 | pexels.com/photo/a-white-container-and-a-pile-of-dry-food-with-a-clear-spoon-13779116 | Pexels |
| src/px_1640777.jpg | c6 слайд 5 | см. c3 выше | Pexels |
| src/bg_grid.jpg | c5 слайд 6, c6 слайды 6-7 | чертёжная сетка, нарисована кодом | своё |

## Карусель c8 "Наклон таза" (19.11)
| Файл | Где | Источник | Лицензия |
|---|---|---|---|
| src/c8_cover.jpg | обложка, слева | кадр из видео Микаела IMG_9675, увеличен Real-ESRGAN, фон размыт по маске | своё |
| src/c8_wall.jpg | слайд 5 | кадр из видео Микаела IMG_9674 (тест у стены), увеличен, фон и люди размыты | своё |
| src/c8_cta.jpg | слайд 9 | кадр из видео Микаела IMG_9674, увеличен, фон размыт | своё |
| src/c8_cover_sch.jpg, c8_neutral.jpg, c8_three.jpg, c8_force.jpg | обложка справа, слайды 2, 4, 6 | схемы таза, нарисованы кодом (tools/posture_reel/pelvis.py) | своё |
| src/bg_grid.jpg | слайды 3, 7, 8 | чертёжная сетка, нарисована кодом | своё |
