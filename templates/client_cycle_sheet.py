import sys, docx
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
src, out = sys.argv[1], sys.argv[2]
d = docx.Document(src)
wb = Workbook()
B = Font(bold=True); Y = PatternFill("solid", fgColor="FFF2CC"); G = PatternFill("solid", fgColor="E2EFDA"); H = PatternFill("solid", fgColor="D9E1F2")
thin = Side(style="thin", color="BBBBBB"); BR = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical="top")

# --- Инструкция
ws = wb.active; ws.title = "Как пользоваться"
lines = [
 ("Андрей: цикл 2. Программа, опрос и поправка на самочувствие", True),
 ("ПМ в жиме 87,5 кг. Скорость 6% за микроцикл (ПМ до 120 кг). Цель цикла: плюс 5 кг, проходка на 92,5 кг.", False),
 ("", False),
 ("Андрею: перед каждой тренировкой заполни свою строку на листе \"Опрос и жим\" (жёлтые ячейки).", True),
 ("1. Всё как обычно: выбери \"да\", и остальное можно не трогать. Если что-то не так, поменяй только этот пункт.", False),
 ("2. Сон этой ночью в часах. Если меньше 7, отметь, была ли позапрошлая ночь тоже меньше 7.", False),
 ("3. Энергия, спокойствие и свежесть мышц: звёзды, 5 значит лучше всего, 3 обычный день.", False),
 ("4. Здоровье: выбери самый серьёзный пункт.", False),
 ("5. Разминка тяжелее обычного: да или нет, по желанию, уже в зале.", False),
 ("Таблица сама покажет уровень, что делать сегодня и вес верхнего подхода жима.", False),
 ("После тренировки: вес, повторы и запас в главном рабочем подходе. Таблица посчитает расчётный максимум.", False),
 ("Если что-то болит, напиши мне, разберёмся.", False),
 ("", False),
 ("Тренеру", True),
 ("Уровень = большее из уровня по сну и по звёздам. Плюс 1, если плохи и сон, и звёзды. Плюс 1, если разминка тяжелее. Насморк без температуры: не ниже 2. Потолок 3.", False),
 ("Сон: 7 ч и больше 0, 5-6,9 ч 1, 3,5-4,9 ч 2, меньше 3,5 ч 3; позапрошлая ночь тоже меньше 7: плюс 1. Звёзды: 2 звезды 1 балл, 1 звезда 2 балла; сумма 0-1 уровень 0, 2-3 уровень 1, 4-5 уровень 2, 6 уровень 3.", False),
 ("День с поправкой в следующем микроцикле повторяем без прибавки: веса на следующую неделю правит тренер. Две поправки подряд: проверить ПМ или разгрузка.", False),
 ("Правила из базы \"Тренировочные планы\", раздел \"Поправка на состояние\".", False),
]
for i,(t,b) in enumerate(lines,1):
    c = ws.cell(i,1,t); c.font = Font(bold=b, size=12 if i==1 else 11); c.alignment = Alignment(wrap_text=True)
ws.column_dimensions["A"].width = 120

# --- Программа
wp = wb.create_sheet("Программа")
wp.append(["Неделя","День","Упражнения"])
for c in wp[1]: c.font=B; c.fill=H; c.border=BR
heads = [p.text for p in d.paragraphs if p.style.name=="Heading 2"]
for wname, t in zip(heads, d.tables):
    for r in t.rows[1:]:
        day = r.cells[0].text.strip(); ex = r.cells[1].text.strip()
        if not day: continue
        wp.append([wname, day, ex])
        for c in wp[wp.max_row]: c.alignment=wrap; c.border=BR
wp.column_dimensions["A"].width=11; wp.column_dimensions["B"].width=16; wp.column_dimensions["C"].width=90
for row in range(2, wp.max_row+1):
    wp.row_dimensions[row].height = 15*(wp.cell(row,3).value.count("\n")+1)
wp.append([]); wp.append(["","Растяжка","В конце каждой тренировки 5-7 минут: грудь, передняя поверхность бедра и сгибатели бедра, задняя поверхность бедра, широчайшие."])
wp.freeze_panes="A2"

# --- Опрос и жим
wo = wb.create_sheet("Опрос и жим")
wo["A1"]="ПМ жим, кг"; wo["B1"]=87.5; wo["C1"]="Шаг, кг"; wo["D1"]=2.5
for c in ("A1","C1"): wo[c].font=B
hdr = ["Неделя","День","Тип","План жима","% верх","% Л микроцикла","% С микроцикла",
 "Всё как обычно","Сон, ч","Позапрошлая ночь меньше 7 ч","Энергия","Спокойствие","Свежесть мышц","Здоровье","Разминка тяжелее",
 "Уровень","Что делать сегодня","Жим сегодня, верх, кг",
 "Факт вес, кг","Повторы","Запас","Расчётный ПМ","Комментарий"]
HR=3
for j,h in enumerate(hdr,1):
    c=wo.cell(HR,j,h); c.font=B; c.fill=H; c.alignment=Alignment(wrap_text=True, vertical="center"); c.border=BR
plan = [
 ("1","Жс Сс","С","70 кг 6х3",.80,.57,.80),("1","Жл Нс","Л","50 кг 4х5",.57,.57,.80),("1","Жт Сл","Т","80 кг 4х2",.92,.57,.80),
 ("2","Жс Нл","С","75 кг 5х3",.86,.63,.86),("2","Жл Ст","Л","55 кг 4х6",.63,.63,.86),("2","Жт Нт","Т","85 кг 3х1, 80 кг 2х2",.98,.63,.86),
 ("3","Жс Сс","С","80 кг 5х2",.92,.69,.92),("3","Жл Нс","Л","60 кг 4х6",.69,.69,.92),("3","Жт Сл","Т","90 кг 2х1, 80 кг 2х2",1.04,.69,.92),
 ("4","Жс Нл","С","70 кг 4х2",.80,.57,.80),("4","Жл Ст","Л","50 кг 4х3",.57,.57,.80),("4","Жт Нт","П","Проходка: 90, потом 92,5",.80,.57,.80),
]
HEALTH = ["Здоров","Насморк без температуры","Температура 37,1 и выше","Боль в груди, давление, острая боль"]
for i,p in enumerate(plan):
    r = HR+1+i
    for j,v in enumerate(p,1): wo.cell(r,j,v)
    for j in (5,6,7): wo.cell(r,j).number_format="0%"
    s = f"IF(I{r}<>\"\",I{r},IF(H{r}=\"да\",8,\"\"))"
    sl = f"IF({s}=\"\",0,MIN(3,IF({s}>=7,0,IF({s}>=5,1,IF({s}>=3.5,2,3)))+IF(AND({s}<7,J{r}=\"да\"),1,0)))"
    pts = "+".join(f"IF(LEN({c}{r})=1,2,IF(LEN({c}{r})=2,1,0))" for c in "KLM")
    sc = f"IF(({pts})>=6,3,IF(({pts})>=4,2,IF(({pts})>=2,1,0)))"
    base = f"MIN(3,MAX({sl},{sc})+IF(AND({sl}>=1,{sc}>=1),1,0)+IF(O{r}=\"да\",1,0))"
    lvl = f"IF(N{r}=\"{HEALTH[1]}\",MAX(2,{base}),{base})"
    empty = f"AND(H{r}=\"\",I{r}=\"\",K{r}=\"\",L{r}=\"\",M{r}=\"\",N{r}=\"\")"
    wo.cell(r,16,f"=IF({empty},\"\",IF(OR(N{r}=\"{HEALTH[2]}\",N{r}=\"{HEALTH[3]}\"),\"нет\",{lvl}))")
    P=f"P{r}"; C=f"C{r}"
    dec = (f"=IF({empty},\"Заполни опрос перед тренировкой\",IF(N{r}=\"{HEALTH[2]}\",\"Пропуск, никакой нагрузки\",IF(N{r}=\"{HEALTH[3]}\",\"Не начинать, напиши Микаелу\","
           f"IF({P}=0,\"По плану\",IF({P}=3,\"Вместо этого день Л: все рабочие минус 5 п., 4 по 5\","
           f"IF({C}=\"П\",\"Проходки нет: С минус 5 п., проходка на следующей тренировке\","
           f"IF({P}=1,IF({C}=\"Л\",\"По плану\",\"Верх дня минус 3 п.\"),"
           f"IF({C}=\"Т\",\"Т заменить на С этой недели минус 5 п., 4 подхода\",IF({C}=\"С\",\"Все рабочие минус 5 п., 4 подхода\",\"Все рабочие минус 3 п., 4 подхода\")))))))))")
    wo.cell(r,17,dec)
    pct = (f"IF(OR({P}=\"\",{P}=0),E{r},IF({P}=3,F{r}-0.05,IF({C}=\"П\",G{r}-0.05,IF({P}=1,IF({C}=\"Л\",E{r},E{r}-0.03),"
           f"IF({C}=\"Т\",G{r}-0.05,IF({C}=\"С\",E{r}-0.05,E{r}-0.03))))))")
    wo.cell(r,18,f"=IF({P}=\"нет\",\"\",IF(AND({C}=\"П\",OR({P}=\"\",{P}=0)),\"90, потом 92,5\",MROUND($B$1*{pct},$D$1)))")
    wo.cell(r,22,f"=IF(OR(S{r}=\"\",T{r}=\"\"),\"\",IF(OR(N(U{r})>4,T{r}+N(U{r})>10),\"\",MROUND(S{r}/CHOOSE(T{r}+N(U{r}),1,0.95,0.93,0.9,0.87,0.85,0.83,0.8,0.77,0.75),0.5)))")
    for j in range(1,24):
        c=wo.cell(r,j); c.border=BR; c.alignment=Alignment(wrap_text=True, vertical="top")
        if 8<=j<=15 or 19<=j<=21 or j==23: c.fill=Y
        if 16<=j<=18 or j==22: c.fill=G
    if p[0] in ("2","4"):
        for j in range(1,5): wo.cell(r,j).font=Font(color="333333")
last = HR+len(plan)
def dv(formula, rng):
    v = DataValidation(type="list", formula1=formula, allow_blank=True); wo.add_data_validation(v); v.add(rng)
dv('"да,нет"', f"H{HR+1}:H{last}"); dv('"да,нет"', f"J{HR+1}:J{last}"); dv('"да,нет"', f"O{HR+1}:O{last}")
sleep = ",".join(str(x/2).replace(".0","") for x in range(4,21))
dv(f'"{sleep}"', f"I{HR+1}:I{last}")
dv('"★,★★,★★★,★★★★,★★★★★"', f"K{HR+1}:M{last}")
dv('"'+",".join(HEALTH)+'"', f"N{HR+1}:N{last}")
widths = [8,9,6,22,7,9,9,10,7,12,11,11,11,22,10,8,34,12,9,8,7,10,24]
from openpyxl.utils import get_column_letter
for j,w in enumerate(widths,1): wo.column_dimensions[get_column_letter(j)].width=w
for j in (5,6,7): wo.column_dimensions[get_column_letter(j)].hidden=True
wo.row_dimensions[HR].height=45
wo.freeze_panes = "E4"
wb.move_sheet("Опрос и жим", offset=-1); wb.move_sheet("Программа", offset=-1)
wb.active = 0
wb.save(out)
