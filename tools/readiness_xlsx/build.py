# Собирает xlsx "Цикл базы с поправкой на состояние" для тренера Микаела.
# Правила поправок лежат в RULES и на листе "Настройки": таблица пересчитывается формулами,
# менять числа можно прямо в xlsx. Запуск: python3 tools/readiness_xlsx/build.py <путь.xlsx>
import sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.comments import Comment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule

OUT = sys.argv[1] if len(sys.argv) > 1 else 'templates/Цикл_базы_с_поправкой.xlsx'

# Калькулятор Микаела (база "Тренировочные планы", раздел "Формула" и "Жим: таблица при скорости 4%")
DAYS = ['М', 'С', 'Л', 'Т']
BASE = {'М': 0.69, 'С': 0.80, 'Л': 0.57, 'Т': 0.92}
TAPER = {'М': 0.69, 'С': 0.80, 'Л': 0.57, 'Т': None}  # 4-й микроцикл: подводка, в Т проходка
SETS = {  # подходы по повторы по микроциклам 1-4 (при скорости 4%)
    'М': ['6 по 3', '6 по 3', '5 по 3', '4 по 3'],
    'С': ['6 по 3', '5 по 3', '7 по 2', '4 по 2'],
    'Л': ['4 по 5', '4 по 6', '4 по 6', '4 по 3'],
    'Т': ['4 по 2', '3 по 1 + 92%, 2 по 2', '3 по 1 + 92%, 2 по 2', 'Проходка 95-100%, 1 по 1 + 1 по 1'],
}

# Правила поправки (решение агента по жиму, см. proposals/bench_state_adjustments.md)
RULES = {
    'sleep': [  # нижняя граница часов, уровень, снижение п.п. для М, С, Л, Т, замена Т
        (0, 'Не спал', 0.10, 0.10, 0.05, 0.10, 'Только Л'),
        (3.5, 'Почти не спал', 0.07, 0.07, 0.05, 0.07, 'Т на С'),
        (5, 'Недосып', 0.03, 0.03, 0.00, 0.03, 'Нет'),
        (7, 'Норма', 0.00, 0.00, 0.00, 0.00, 'Нет'),
    ],
    'scale': [(1, 0.05), (2, 0.03), (3, 0.02), (4, 0.00), (5, 0.00)],  # оценка 1-5 -> снижение
    'cap': 0.10,          # максимум суммарного снижения
    'replace_from': 0.05,  # с какого суммарного снижения Т заменяется на С
    'light_from': 0.08,   # с какого снижения любой день становится Л
    'low_c': 0.05,        # "С с низкими процентами": С минус столько пунктов
    'pm_dev': 0.03,       # порог отклонения расчётного ПМ от текущего
}
MICROCYCLES = 6  # строк дневника хватает на сдвиг цикла

FONT = 'Arial'
F = Font(name=FONT, size=10)
FB = Font(name=FONT, size=10, bold=True)
FH = Font(name=FONT, size=12, bold=True)
FIN = Font(name=FONT, size=10, color='0000FF')
FILL_IN = PatternFill('solid', fgColor='FFF2CC')
FILL_HEAD = PatternFill('solid', fgColor='D9E1F2')
FILL_SET = PatternFill('solid', fgColor='EDEDED')
THIN = Side(style='thin', color='BFBFBF')
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical='top')
CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)


def cell(ws, ref, value, font=F, fill=None, fmt=None, align=None, border=True):
    c = ws[ref]
    c.value = value
    c.font = font
    if fill:
        c.fill = fill
    if fmt:
        c.number_format = fmt
    if align:
        c.alignment = align
    if border:
        c.border = BOX
    return c


def inp(ws, ref, value, fmt=None):
    return cell(ws, ref, value, FIN, FILL_IN, fmt, CENTER)


wb = Workbook()

# ---------- Настройки ----------
st = wb.active
st.title = 'Настройки'
st.column_dimensions['A'].width = 34
for col in 'BCDEFGH':
    st.column_dimensions[col].width = 14
cell(st, 'A1', 'Настройки цикла и правила поправки', FH, border=False)
rows = [
    ('Клиент', 'Пример: Иван', None),
    ('База', 'Жим лёжа', None),
    ('ПМ, кг', 165, '0.0'),
    ('Шаг округления, кг', 2.5, '0.0'),
    ('Скорость прогрессии за микроцикл', 0.04, '0%'),
    ('Микроцикл (М-С-Л-Т или С-Л-Т)', 'С-Л-Т', None),
]
for i, (label, val, fmt) in enumerate(rows, start=3):
    cell(st, f'A{i}', label, FB)
    inp(st, f'B{i}', val, fmt)
dv = DataValidation(type='list', formula1='"М-С-Л-Т,С-Л-Т"', allow_blank=False)
st.add_data_validation(dv)
dv.add('B8')
st['B5'].comment = Comment('ПМ в базе. Сменили ПМ: все веса в дневнике пересчитаются.', 'Микаел')
st['B7'].comment = Comment('Калькулятор Микаела: от 1% до 6%, по умолчанию 4%.', 'Микаел')

# Проценты по дням
cell(st, 'A11', 'Проценты калькулятора', FH, border=False)
for j, h in enumerate(['День', 'Базовый %', 'Подводка (мк 4)', 'Подходы мк1', 'мк2', 'мк3', 'мк4']):
    cell(st, f'{"ABCDEFG"[j]}12', h, FB, FILL_HEAD, align=CENTER)
for i, d in enumerate(DAYS, start=13):
    cell(st, f'A{i}', d, FB, align=CENTER)
    inp(st, f'B{i}', BASE[d], '0%')
    if TAPER[d] is None:
        inp(st, f'C{i}', 'Проходка')
    else:
        inp(st, f'C{i}', TAPER[d], '0%')
    for k in range(4):
        inp(st, f'{"DEFG"[k]}{i}', SETS[d][k])
cell(st, 'A17', 'Источник: база "Тренировочные планы", калькулятор Микаела. Рабочий % = базовый + скорость х (микроцикл - 1).', F, border=False)

# Сон
cell(st, 'A19', 'Поправка по сну (часы)', FH, border=False)
for j, h in enumerate(['От, часов', 'Уровень', 'М, п.п.', 'С, п.п.', 'Л, п.п.', 'Т, п.п.', 'Замена дня']):
    cell(st, f'{"ABCDEFG"[j]}20', h, FB, FILL_HEAD, align=CENTER)
for i, row in enumerate(RULES['sleep'], start=21):
    inp(st, f'A{i}', row[0], '0.0')
    inp(st, f'B{i}', row[1])
    for k in range(4):
        inp(st, f'{"CDEF"[k]}{i}', row[2 + k], '0%')
    inp(st, f'G{i}', row[6])
cell(st, 'A25', 'Пороги сна от Микаела: меньше 7 ч недосып, меньше 5 ч почти не спал, меньше 3-4 ч не спал. Пункты снижения: решение агента по жиму.', F, border=False)

# Шкала опроса
cell(st, 'A27', 'Поправка по оценкам 1-5 (стресс, крепатура, энергия)', FH, border=False)
cell(st, 'A28', 'Оценка', FB, FILL_HEAD, align=CENTER)
cell(st, 'B28', 'Снижение, п.п.', FB, FILL_HEAD, align=CENTER)
for i, (score, red) in enumerate(RULES['scale'], start=29):
    inp(st, f'A{i}', score)
    inp(st, f'B{i}', red, '0%')
cell(st, 'A34', '5 значит отлично (нет стресса, нет крепатуры, полно энергии), 1 значит очень плохо.', F, border=False)

# Пороги решений
cell(st, 'A36', 'Пороги решений', FH, border=False)
thr = [
    ('Максимум суммарного снижения', RULES['cap']),
    ('Т заменяю на С, если снижение от', RULES['replace_from']),
    ('Любой день делаю Л, если снижение от', RULES['light_from']),
    ('"С с низкими процентами": минус пунктов от С', RULES['low_c']),
    ('Порог отклонения расчётного ПМ', RULES['pm_dev']),
]
for i, (label, val) in enumerate(thr, start=37):
    cell(st, f'A{i}', label, FB)
    inp(st, f'B{i}', val, '0%')

# Именованные ссылки для формул
S = "'Настройки'!"
PM, STEP, SPEED, MC = f'{S}$B$5', f'{S}$B$6', f'{S}$B$7', f'{S}$B$8'
CAP, REPL, LIGHT, LOWC, PMDEV = (f'{S}$B$37', f'{S}$B$38', f'{S}$B$39', f'{S}$B$40', f'{S}$B$41')
DAYCOL = f'{S}$A$13:$A$16'

# ---------- Дневник ----------
ws = wb.create_sheet('Дневник')
heads = [
    ('A', 'Дата', 11), ('B', 'Микро-цикл', 7), ('C', 'День по плану', 7),
    ('D', 'Сон, часов', 7), ('E', 'Стресс 1-5', 7), ('F', 'Крепатура 1-5', 8), ('G', 'Энергия 1-5', 7),
    ('H', 'Инфекция с температурой (да/нет)', 11), ('I', 'Боль в груди, давление, острая боль (да/нет)', 13),
    ('J', 'Уровень сна', 11), ('K', 'Снижение по сну', 9), ('L', 'Снижение по опросу', 9),
    ('M', 'Итог снижения', 9), ('N', 'Решение', 22), ('O', 'День факт', 7),
    ('P', 'Поправка была', 8), ('Q', 'Сдвиг прогрессии', 8), ('R', 'Микроцикл для %', 8),
    ('S', 'План %', 8), ('T', 'Рабочий %', 8), ('U', 'Рабочий вес, кг', 9), ('V', 'Подходы по повторы', 22),
    ('W', 'Факт: вес', 8), ('X', 'Факт: повторы', 8), ('Y', 'Факт: запас повторов', 8),
    ('Z', 'Расчётный ПМ', 9), ('AA', 'Отклонение от ПМ', 9), ('AB', 'Последнее отклонение', 9), ('AC', 'Сигнал', 30),
]
cell(ws, 'A1', 'Дневник цикла: жёлтое заполняет тренер или клиент, остальное считается само', FH, border=False)
for col, h, w in heads:
    cell(ws, f'{col}3', h, FB, FILL_HEAD, align=CENTER)
    ws.column_dimensions[col].width = w
ws.row_dimensions[3].height = 54
ws.freeze_panes = 'D4'
for col in ('P', 'Q', 'R', 'AB'):
    ws.column_dimensions[col].hidden = False

yes_no = DataValidation(type='list', formula1='"да,нет"', allow_blank=True)
score = DataValidation(type='whole', operator='between', formula1='1', formula2='5', allow_blank=True)
ws.add_data_validation(yes_no)
ws.add_data_validation(score)

first, n_rows = 4, MICROCYCLES * 4
for r in range(first, first + n_rows):
    k = r - first  # номер строки с нуля
    nd = f'IF({MC}="С-Л-Т",3,4)'
    # микроцикл и день по плану из типа микроцикла
    cell(ws, f'B{r}', f'=IF({k}<{MICROCYCLES}*{nd},INT({k}/{nd})+1,"")', align=CENTER)
    cell(ws, f'C{r}', f'=IF(B{r}="","",IF({MC}="С-Л-Т",CHOOSE(MOD({k},3)+1,"С","Л","Т"),CHOOSE(MOD({k},4)+1,"М","С","Л","Т")))', align=CENTER)
    for col in 'ADEFGHIWXY':
        c = ws[f'{col}{r}']
        c.font, c.fill, c.border, c.alignment = FIN, FILL_IN, BOX, CENTER
    ws[f'A{r}'].number_format = 'DD.MM.YY'
    yes_no.add(f'H{r}')
    yes_no.add(f'I{r}')
    for col in 'EFG':
        score.add(f'{col}{r}')
    # Уровень сна и снижение по сну (столбец дня в таблице сна: М=C, С=D, Л=E, Т=F)
    cell(ws, f'J{r}', f'=IF(D{r}="","",LOOKUP(D{r},{S}$A$21:$A$24,{S}$B$21:$B$24))', align=CENTER)
    cell(ws, f'K{r}', f'=IF(OR(D{r}="",C{r}=""),0,LOOKUP(D{r},{S}$A$21:$A$24,INDEX({S}$C$21:$F$24,0,MATCH(C{r},{DAYCOL},0))))', fmt='0%', align=CENTER)
    sc = lambda col: f'IF({col}{r}="",0,LOOKUP({col}{r},{S}$A$29:$A$33,{S}$B$29:$B$33))'
    cell(ws, f'L{r}', f'={sc("E")}+{sc("F")}+{sc("G")}', fmt='0%', align=CENTER)
    cell(ws, f'M{r}', f'=MIN({CAP},K{r}+L{r})', fmt='0%', align=CENTER)
    sleep_repl = f'IF(D{r}="","Нет",LOOKUP(D{r},{S}$A$21:$A$24,{S}$G$21:$G$24))'
    cell(ws, f'N{r}', (
        f'=IF(C{r}="","",IF(H{r}="да","Пропуск: инфекция",IF(I{r}="да","К тренеру, не тренироваться",'
        f'IF(OR({sleep_repl}="Только Л",M{r}>={LIGHT}),"Лёгкий день",'
        f'IF(AND(C{r}="Т",OR({sleep_repl}="Т на С",M{r}>={REPL})),"Т на С с низкими %",'
        f'IF(M{r}>0,"Снижение","По плану"))))))'), align=WRAP)
    cell(ws, f'O{r}', f'=IF(C{r}="","",IF(LEFT(N{r},6)="Пропус","",IF(N{r}="К тренеру, не тренироваться","",IF(N{r}="Лёгкий день","Л",IF(N{r}="Т на С с низкими %","С",C{r})))))', align=CENTER)
    cell(ws, f'P{r}', f'=IF(OR(N{r}="",N{r}="По плану"),0,1)', align=CENTER)
    prev = f'$C${first}:C{r-1}' if r > first else None
    if prev:
        cell(ws, f'Q{r}', f'=COUNTIFS({prev},C{r},$P${first}:P{r-1},1)', align=CENTER)
    else:
        cell(ws, f'Q{r}', 0, align=CENTER)
    cell(ws, f'R{r}', f'=IF(B{r}="","",MAX(1,B{r}-Q{r}))', align=CENTER)
    base = f'INDEX({S}$B$13:$B$16,MATCH(C{r},{DAYCOL},0))'
    taper = f'INDEX({S}$C$13:$C$16,MATCH(C{r},{DAYCOL},0))'
    cell(ws, f'S{r}', f'=IF(C{r}="","",IF(R{r}<=3,{base}+{SPEED}*(R{r}-1),IF(R{r}=4,{taper},"Новый цикл")))', fmt='0%', align=CENTER)
    base_c = f'(INDEX({S}$B$13:$B$16,2)+{SPEED}*(MIN(R{r},3)-1))'
    base_l = f'(INDEX({S}$B$13:$B$16,3)+{SPEED}*(MIN(R{r},3)-1))'
    cell(ws, f'T{r}', (
        f'=IF(OR(O{r}="",NOT(ISNUMBER(S{r}))),"",'
        f'IF(N{r}="Т на С с низкими %",{base_c}-{LOWC},'
        f'IF(N{r}="Лёгкий день",MIN(S{r},{base_l})-IF(C{r}="Л",M{r},0),S{r}-M{r})))'), fmt='0%', align=CENTER)
    cell(ws, f'U{r}', f'=IF(ISNUMBER(T{r}),ROUND({PM}*T{r}/{STEP},0)*{STEP},"")', fmt='0.0', align=CENTER)
    sets = f'INDEX({S}$D$13:$G$16,MATCH(O{r},{DAYCOL},0),MIN(R{r},4))'
    cell(ws, f'V{r}', f'=IF(O{r}="","",IF(NOT(ISNUMBER(S{r})),S{r},IF(O{r}="Л",INDEX({S}$D$13:$G$16,3,MIN(R{r},4)),{sets})&IF(M{r}>0," (подходов не меньше 4)","")))', align=WRAP)
    cell(ws, f'Z{r}', f'=IF(AND(N(W{r})>0,N(X{r})>0,N(X{r})+N(Y{r})<=10),W{r}*(1+(X{r}+N(Y{r}))/30),"")', fmt='0.0', align=CENTER)
    cell(ws, f'AA{r}', f'=IF(Z{r}="","",Z{r}/{PM}-1)', fmt='0.0%', align=CENTER)
    prev_ab = f'AB{r-1}' if r > first else '""'
    cell(ws, f'AB{r}', f'=IF(AA{r}="",{prev_ab},AA{r})', fmt='0.0%', align=CENTER)
    prev_mc = f'COUNTIFS($B${first}:$B${first + n_rows - 1},B{r}-1,$P${first}:$P${first + n_rows - 1},1)'
    cell(ws, f'AC{r}', (
        f'=IF(C{r}="","",TRIM(IF(AND(P{r}=1,{prev_mc}>0),"Две поправки подряд: проверить ПМ или разгрузка. ","")'
        f'&IF(AA{r}="","",IF(AND(AA{r}>{PMDEV},N({prev_ab})>{PMDEV}),"ПМ выше расчёта 2 раза: обновить ПМ. ",'
        f'IF(AND(AA{r}<-{PMDEV},N({prev_ab})<-{PMDEV}),"ПМ ниже расчёта 2 раза: проверить ПМ. ","")))))'), align=WRAP)

# подсветка решений
red = PatternFill('solid', fgColor='F8CBAD')
amber = PatternFill('solid', fgColor='FFE699')
rng = f'N{first}:N{first + n_rows - 1}'
ws.conditional_formatting.add(rng, FormulaRule(formula=[f'OR(LEFT(N{first},6)="Пропус",LEFT(N{first},7)="К трене")'], fill=red))
ws.conditional_formatting.add(rng, FormulaRule(formula=[f'OR(N{first}="Снижение",N{first}="Т на С с низкими %",N{first}="Лёгкий день")'], fill=amber))

# ---------- Инструкция ----------
ins = wb.create_sheet('Инструкция', 0)
ins.column_dimensions['A'].width = 110
lines = [
    ('Цикл базы с поправкой на состояние', FH),
    ('Что делает таблица', FB),
    ('По опросу перед тренировкой считает снижение в процентных пунктах от ПМ, решает: по плану, снижение, Т на С с низкими процентами, лёгкий день или пропуск. Считает рабочий вес на сегодня и сдвигает дальнейший цикл: день с поправкой в следующем микроцикле повторяется без прибавки.', F),
    ('Что заполнять (жёлтые ячейки)', FB),
    ('1. Лист "Настройки": клиент, ПМ, шаг округления, скорость прогрессии, тип микроцикла. Правила поправки тоже там, их можно менять.', F),
    ('2. Лист "Дневник", перед тренировкой: дата, сон в часах, стресс, крепатура, энергия (1-5, где 5 отлично), инфекция с температурой да/нет, боль в груди или давление или острая боль да/нет.', F),
    ('3. После тренировки: фактический вес, повторы и запас повторов в главном рабочем подходе. Таблица посчитает расчётный ПМ и подскажет, когда его обновить.', F),
    ('Опрос для клиента (отправить в бот перед тренировкой)', FB),
    ('Сколько часов спал? Стресс от 1 до 5 (5 = спокоен)? Крепатура в мышцах, которые сегодня работают, от 1 до 5 (5 = нет)? Энергия от 1 до 5 (5 = полно сил)? Есть инфекция с температурой? Есть боль в груди, скачет давление или острая боль в суставе?', F),
    ('Правила', FB),
    ('Инфекция с температурой: тренировки нет (решение Микаела). Боль в груди, давление, острая боль: тренировки нет, решает Микаел. Снижение не больше максимума с листа "Настройки". База не меньше 4 рабочих подходов.', F),
    ('Сигналы', FB),
    ('"Две поправки подряд": поправки в двух микроциклах подряд, проверить ПМ или поставить разгрузку. "ПМ выше/ниже расчёта 2 раза": расчётный ПМ по факту дважды подряд отличается больше порога, обновить ПМ на листе "Настройки".', F),
    ('Пример', FB),
    ('В первых двух строках дневника стоит пример (сон 6 ч, стресс 3, крепатура 4, энергия 4). Замените своими данными.', F),
    ('Расчётный ПМ = вес х (1 + (повторы + запас) / 30), формула Эпли с запасом повторов. Считается, только если повторы + запас не больше 10.', F),
]
for i, (text, font) in enumerate(lines, start=1):
    c = ins[f'A{i}']
    c.value, c.font, c.alignment = text, font, Alignment(wrap_text=True, vertical='top')

# пример в первых двух строках
for ref, val in (('A4', None), ('D4', 6), ('E4', 3), ('F4', 4), ('G4', 4), ('H4', 'нет'), ('I4', 'нет'),
                 ('D5', 7.5), ('E5', 5), ('F5', 5), ('G5', 5), ('H5', 'нет'), ('I5', 'нет')):
    if val is not None:
        ws[ref].value = val

wb.save(OUT)
print('saved', OUT)
