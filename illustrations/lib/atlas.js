// Анатомический атлас: drawMuscle(opts) -> SVG 900x650.
// Координаты фигур заданы в системе "рост 1000": макушка y=0, подошва y=1000.
// Фас и спина: ось симметрии x=0, мышцы описаны для одной стороны (x>0) и зеркалятся.
// Профиль: смотрит вправо, x>0 = вперёд (кпереди), отвес через ухо, акромион, большой вертел, лодыжку.
'use strict';

const W = 900, H = 650;
const FONT = 'DejaVu Sans, Arial, sans-serif';
const C = {
  outline: '#37474F', body: '#ECEFF1', muscle: '#90A4AE', title: '#263238', hint: '#455A64',
  weak: '#E53935', tight: '#FB8C00', neutral: '#E53935', arrow: '#1E88E5', equip: '#B0BEC5',
};
const STATE = {
  weak: { fill: C.weak, op: 0.8, stroke: '#B71C1C', badge: 'Слабая мышца' },
  tight: { fill: C.tight, op: 0.7, stroke: '#E65100', badge: 'Гипертонус' },
  neutral: { fill: C.neutral, op: 0.8, stroke: '#B71C1C', badge: 'Мышца' },
};

const NAMES = {
  neck_flexors: 'глубокие сгибатели шеи', scm: 'грудино-ключично-сосцевидная', trap_upper: 'верхняя трапеция',
  trap_mid: 'средняя трапеция', trap_low: 'нижняя трапеция', levator: 'мышца, поднимающая лопатку',
  rhomboids: 'ромбовидные', serratus: 'передняя зубчатая', pec_major: 'большая грудная', pec_minor: 'малая грудная',
  delt_ant: 'передняя дельта', delt_mid: 'средняя дельта', delt_post: 'задняя дельта', lats: 'широчайшая',
  erectors_thor: 'разгибатели спины, грудной отдел', erectors_lumb: 'разгибатели спины, поясница',
  rectus_abd: 'прямая мышца живота', obliques: 'косые мышцы живота', transversus: 'поперечная мышца живота',
  iliopsoas: 'подвздошно-поясничная', glute_max: 'большая ягодичная', glute_med: 'средняя ягодичная',
  glute_min: 'малая ягодичная', piriformis: 'грушевидная', tfl: 'напрягатель широкой фасции',
  rectus_fem: 'прямая мышца бедра', vasti: 'широкие мышцы бедра', adductors: 'приводящие мышцы',
  hamstrings: 'задняя поверхность бедра', gastrocnemius: 'икроножная', soleus: 'камбаловидная',
  tib_post: 'задняя большеберцовая', foot_arch: 'мышцы свода стопы', suboccipitals: 'подзатылочные',
  biceps: 'бицепс плеча', triceps: 'трицепс',
  sartorius: 'портняжная', tib_ant: 'передняя большеберцовая', peroneus: 'малоберцовые',
  brachiorad: 'плечелучевая', infraspinatus: 'подостная', teres: 'большая круглая', achilles: 'ахиллово сухожилие',
};
const VIEW_LABEL = { front: 'спереди', back: 'сзади', side: 'сбоку' };

// ---------- геометрия ----------
// точка: [x, y] или [x, y, 1] (1 = угол, без сглаживания)
function smooth(pts, closed = true) {
  const n = pts.length;
  if (n < 2) return '';
  const f = (v) => Math.round(v * 10) / 10;
  const P = (i) => closed ? pts[(i + n) % n] : pts[Math.max(0, Math.min(n - 1, i))];
  let d = `M${f(pts[0][0])},${f(pts[0][1])}`;
  const segs = closed ? n : n - 1;
  for (let i = 0; i < segs; i++) {
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    const t = 1 / 6;
    const c1 = p1[2] ? p1 : [p1[0] + (p2[0] - p0[0]) * t, p1[1] + (p2[1] - p0[1]) * t];
    const c2 = p2[2] ? p2 : [p2[0] - (p3[0] - p1[0]) * t, p2[1] - (p3[1] - p1[1]) * t];
    d += ` C${f(c1[0])},${f(c1[1])} ${f(c2[0])},${f(c2[1])} ${f(p2[0])},${f(p2[1])}`;
  }
  return d + (closed ? ' Z' : '');
}
const mirror = (pts) => pts.map((p) => [-p[0], p[1], p[2]]);
const tf = (pts, T) => pts.map((p) => [T.x + p[0] * T.s, T.y + p[1] * T.s, p[2]]);
const centroid = (pts) => [pts.reduce((a, p) => a + p[0], 0) / pts.length, pts.reduce((a, p) => a + p[1], 0) / pts.length];

// ---------- фас / спина: силуэт ----------
// половина силуэта (правая сторона рисунка), от основания черепа вниз и обратно к промежности
const HALF = [
  [25, 104], [29, 128], [36, 146], [62, 161], [95, 175], [118, 184], [134, 196], [143, 218], [149, 250], [156, 285],
  [164, 330], [171, 375], [184, 415], [194, 470], [197, 497], [204, 520], [208, 555], [203, 592], [192, 608],
  [179, 606], [169, 590], [164, 555], [161, 515], [160, 502], [151, 470], [134, 425], [126, 390], [118, 350],
  [108, 310], [99, 278], [94, 262, 1], [92, 285], [86, 325], [78, 362], [82, 398], [92, 430], [99, 468], [100, 510],
  [95, 570], [85, 640], [74, 700], [75, 745], [81, 790], [76, 850], [68, 915], [66, 950], [73, 975], [81, 992],
  [78, 1000, 1], [34, 1000, 1], [29, 990], [31, 965], [34, 948], [30, 918], [20, 860], [14, 800], [18, 750],
  [22, 712], [18, 660], [10, 590], [4, 525], [0, 506, 1],
];
const BODY_FB = HALF.concat(mirror(HALF.slice(0, -1)).reverse());
const HEAD_FRONT = (() => { const h = [[0, 0], [28, 5], [43, 24], [47, 52], [45, 80], [38, 100], [24, 117], [0, 127]]; return h.concat(mirror(h.slice(1, -1)).reverse()); })();
const HEAD_BACK = (() => { const h = [[0, 0], [28, 5], [43, 24], [47, 52], [45, 80], [38, 97], [22, 107], [0, 110]]; return h.concat(mirror(h.slice(1, -1)).reverse()); })();
const EAR_FB = [[42, 56], [51, 57], [55, 68], [52, 84], [43, 88]];

// ---------- мышцы: фас ----------
// deep: глубокая мышца, рисуется только при выделении, пунктиром поверх
// decor: вспомогательный контур без отдельного id из списка
const FRONT = {
  neck_flexors: { deep: 1, p: [[[3, 126], [12, 124], [14, 162], [4, 164]]] },
  levator: { deep: 1, p: [[[30, 112], [38, 112], [62, 166], [53, 168]]] },
  pec_minor: { deep: 1, p: [[[86, 192], [96, 200], [62, 268], [48, 270], [40, 252], [38, 230]]], lines: [[[90, 197], [42, 248]], [[92, 199], [54, 268]]] },
  transversus: { deep: 1, p: [[[42, 300], [70, 318], [82, 350], [82, 400], [84, 416], [52, 440], [30, 462], [36, 400], [40, 340]]], lines: [[[42, 330], [80, 330]], [[39, 360], [80, 360]], [[37, 390], [81, 390]], [[34, 420], [76, 420]]] },
  iliopsoas: { deep: 1, p: [[[6, 320], [15, 316], [26, 356], [32, 396], [44, 404], [62, 398], [78, 410], [76, 440], [62, 470], [54, 500], [48, 528], [38, 530], [34, 505], [24, 474], [12, 440], [7, 400]]], lines: [[[32, 398], [44, 470]]] },
  trap_upper: { p: [[[28, 124], [36, 126], [40, 146], [64, 154], [100, 168], [124, 180], [116, 184], [98, 181], [64, 173], [40, 164], [30, 152], [26, 138]]] },
  scm: { p: [[[32, 100], [42, 104], [32, 132], [19, 160], [8, 167], [5, 160], [20, 132]]] },
  serratus: { p: [[[86, 270], [88, 290], [84, 315], [80, 336], [74, 336], [80, 324], [70, 318], [78, 306], [66, 298], [74, 288], [66, 278], [80, 268]]] },
  lats: { p: [[[89, 266], [96, 266], [96, 300], [88, 330], [80, 362], [76, 356], [81, 326], [86, 290]]] },
  obliques: { p: [[[46, 282], [66, 298], [70, 318], [74, 336], [84, 350], [80, 362], [84, 398], [86, 416], [60, 440], [36, 470], [22, 490], [26, 466], [34, 410], [40, 350], [44, 310]]] },
  rectus_abd: { p: [[[4, 272], [26, 268], [46, 278], [44, 320], [38, 380], [30, 440], [20, 492], [4, 494]]], lines: [[[4, 318], [44, 318]], [[4, 356], [41, 356]], [[4, 398], [36, 398]]] },
  pec_major: { p: [[[5, 168], [30, 167], [62, 175], [80, 196], [98, 218], [114, 247], [102, 258], [80, 268], [56, 273], [30, 271], [6, 263], [4, 215]]], lines: [[[8, 182], [66, 182]]] },
  triceps: { p: [[[96, 268], [104, 266], [124, 330], [136, 384], [128, 388], [110, 330]]] },
  biceps: { p: [[[114, 250], [130, 248], [146, 290], [156, 340], [153, 376], [144, 379], [132, 345], [120, 300]]] },
  brachiorad: { decor: 1, p: [[[152, 386], [172, 386], [188, 425], [190, 470], [182, 482], [170, 432]]] },
  delt_ant: { p: [[[66, 177], [100, 180], [118, 186], [127, 204], [133, 240], [145, 294], [131, 281], [114, 248], [98, 218], [80, 196]]] },
  delt_mid: { p: [[[118, 186], [138, 190], [148, 216], [154, 250], [160, 284], [145, 296], [133, 240], [127, 204]]] },
  glute_med: { p: [[[84, 402], [94, 404], [102, 440], [102, 468], [96, 466], [90, 436]]] },
  tfl: { p: [[[78, 418], [90, 422], [98, 462], [100, 510], [92, 526], [86, 492], [80, 452], [75, 428]]] },
  adductors: { p: [[[3, 508], [20, 497], [46, 500], [38, 540], [30, 580], [22, 640], [18, 664], [12, 620], [6, 560]]] },
  vasti: { p: [
    [[80, 478], [96, 492], [104, 540], [98, 600], [88, 650], [76, 700], [62, 706], [66, 672], [76, 612], [80, 540], [78, 494]],
    [[48, 560], [46, 620], [44, 668], [44, 692], [36, 706], [26, 702], [22, 670], [28, 620], [38, 590]],
  ] },
  rectus_fem: { p: [[[66, 448], [75, 458], [80, 520], [78, 590], [68, 655], [57, 692], [45, 692], [43, 650], [48, 580], [60, 510], [64, 466]]] },
  sartorius: { decor: 1, p: [[[75, 412], [85, 418], [60, 500], [40, 580], [32, 640], [29, 702], [20, 700], [22, 640], [30, 578], [50, 500]]] },
  gastrocnemius: { p: [[[20, 738], [27, 756], [27, 818], [23, 850], [10, 844], [10, 800], [14, 760]]] },
  soleus: { p: [[[12, 840], [24, 848], [30, 880], [36, 912], [30, 921], [20, 884]]] },
  peroneus: { decor: 1, p: [[[70, 756], [82, 786], [76, 850], [66, 905], [61, 900], [68, 842], [72, 792]]] },
  tib_ant: { decor: 1, p: [[[56, 742], [66, 748], [72, 780], [68, 840], [60, 900], [53, 936], [48, 932], [54, 880], [58, 820], [56, 770]]] },
};
const FRONT_DECOR_LINES = [
  [[6, 166], [40, 168], [72, 175], [114, 184]],
  [[196, 516], [195, 545], [186, 562]],
];

// ---------- мышцы: спина ----------
const BACK = {
  suboccipitals: { deep: 1, p: [[[4, 104], [26, 101], [30, 110], [20, 122], [6, 120]]] },
  levator: { deep: 1, p: [[[12, 110], [22, 110], [62, 188], [53, 195]]] },
  rhomboids: { deep: 1, p: [[[4, 166], [14, 165], [50, 194], [57, 212], [61, 262], [53, 267], [4, 250]]], lines: [[[4, 208], [56, 236]]] },
  glute_min: { deep: 1, p: [[[40, 412], [80, 410], [94, 438], [97, 466], [76, 452], [50, 434]]] },
  piriformis: { deep: 1, p: [[[16, 440], [24, 437], [50, 452], [72, 468], [87, 478], [88, 486], [74, 484], [48, 474], [24, 477], [16, 472]]] },
  tib_post: { deep: 1, p: [[[40, 770], [54, 770], [54, 850], [48, 910], [40, 940], [35, 958], [30, 954], [36, 925], [40, 870]]] },
  erectors_thor: { cover: 1, p: [[[4, 196], [24, 200], [28, 260], [30, 340], [4, 340]]] },
  erectors_lumb: { p: [[[4, 340], [30, 340], [36, 380], [34, 420], [18, 440], [4, 440]]] },
  teres: { decor: 1, p: [[[68, 280], [94, 260], [106, 252], [110, 262], [98, 274], [78, 293]]] },
  infraspinatus: { decor: 1, p: [[[58, 214], [86, 210], [100, 226], [104, 244], [94, 258], [70, 278], [62, 250]]] },
  lats: { p: [[[4, 272], [40, 272], [66, 285], [80, 291], [98, 270], [106, 258], [112, 262], [98, 282], [92, 310], [88, 338], [62, 390], [46, 400], [34, 370], [20, 330], [4, 300]]] },
  triceps: { p: [[[100, 268], [124, 262], [142, 296], [160, 340], [166, 376], [150, 389], [134, 372], [116, 320], [100, 280]]] },
  delt_post: { p: [[[66, 200], [100, 192], [118, 188], [128, 204], [134, 240], [145, 293], [128, 272], [110, 240], [90, 216]]] },
  delt_mid: { p: [[[118, 186], [138, 190], [148, 216], [154, 250], [160, 284], [146, 296], [134, 240], [128, 204]]] },
  trap_low: { p: [[[2, 226], [40, 212], [62, 204], [56, 218], [36, 260], [14, 310], [2, 340]]] },
  trap_mid: { p: [[[2, 168], [40, 180], [80, 190], [116, 188], [108, 197], [70, 205], [40, 212], [2, 226]]] },
  trap_upper: { p: [[[2, 102], [26, 102], [36, 130], [40, 146], [64, 154], [100, 168], [126, 180], [116, 188], [80, 190], [40, 180], [2, 168]]] },
  scm: { p: [[[28, 106], [40, 104], [42, 132], [32, 126]]] },
  obliques: { p: [[[86, 336], [92, 370], [90, 402], [66, 400], [62, 390]]] },
  glute_med: { p: [[[24, 418], [40, 402], [66, 392], [88, 398], [100, 420], [104, 450], [102, 490], [94, 486], [80, 462], [56, 446], [30, 436]]] },
  glute_max: { p: [[[3, 430], [30, 423], [56, 437], [78, 458], [94, 478], [104, 500], [96, 515], [78, 527], [50, 535], [22, 533], [3, 527]]] },
  adductors: { p: [[[3, 530], [14, 537], [10, 580], [14, 640], [8, 600], [3, 560]]] },
  vasti: { p: [[[82, 528], [100, 518], [102, 560], [96, 620], [86, 680], [76, 702], [72, 690], [78, 640], [80, 580]]] },
  hamstrings: { p: [[[14, 536], [30, 528], [52, 534], [66, 550], [78, 600], [76, 660], [70, 710], [68, 744], [60, 746], [56, 712], [48, 697], [38, 697], [30, 712], [26, 746], [18, 746], [18, 700], [14, 640], [10, 580]]], lines: [[[40, 540], [44, 692]]] },
  soleus: { p: [[[14, 820], [30, 858], [44, 866], [60, 848], [78, 822], [78, 860], [68, 900], [56, 920], [42, 922], [28, 900], [20, 870]]] },
  gastrocnemius: { p: [
    [[20, 730], [42, 736], [44, 800], [42, 864], [32, 858], [16, 822], [12, 780]],
    [[48, 736], [70, 734], [82, 780], [78, 822], [60, 848], [48, 842], [46, 790]],
  ] },
  achilles: { decor: 1, p: [[[40, 900], [52, 900], [52, 950], [43, 950]]] },
};
const BACK_DECOR_LINES = [
  [[0, 112], [0, 430]],
  [[-20, 428], [20, 428], [7, 478], [-7, 478], [-20, 428, 1]],
  [[0, 478], [0, 524]],
  [[28, 724], [66, 724]],
  [[98, 500], [80, 712]],
];

// ---------- профиль ----------
const BODY_SIDE = [
  [8, 0], [36, 8], [54, 28], [60, 50], [62, 58], [70, 72], [64, 80], [62, 88], [60, 98], [58, 108], [56, 118],
  [46, 126], [38, 132], [37, 150], [40, 166], [52, 184], [64, 212], [70, 242], [68, 266], [60, 286], [56, 310],
  [56, 340], [60, 380], [62, 410], [58, 445], [50, 488], [56, 510], [64, 550], [66, 600], [60, 660], [54, 698],
  [52, 730], [46, 770], [40, 850], [34, 920], [34, 946], [46, 962], [80, 976], [110, 988], [128, 994], [130, 1000, 1],
  [-24, 1000, 1], [-34, 990], [-34, 970], [-26, 950], [-20, 925], [-26, 880], [-40, 820], [-46, 785], [-42, 745],
  [-34, 718], [-40, 680], [-50, 610], [-56, 560], [-58, 536], [-66, 505], [-68, 478], [-62, 446], [-50, 418],
  [-40, 388], [-40, 352], [-48, 310], [-56, 260], [-54, 220], [-46, 190], [-34, 160], [-28, 138], [-34, 118],
  [-46, 102], [-52, 70], [-46, 36], [-26, 10],
];
// плечо вертикально, предплечье опущено на 35 град. от горизонтали (запястье ~ (110, 442)),
// кисть ~0,11 роста, расслаблена, пальцы сомкнуты, большой палец мягким бугорком сверху, зона таза открыта
const ARM_SIDE = [
  [-28, 196], [-18, 184], [-2, 180], [14, 182], [26, 192], [31, 214], [29, 250], [26, 300], [27, 340], [31, 362, 1],
  [56, 382], [86, 407], [116, 433],
  [124, 438], [139, 442], [149, 450], [152, 457], [159, 466], [175, 487], [187, 504], [189, 513], [183, 518],
  [168, 510], [150, 497], [132, 482], [116, 465], [103, 451],
  [69, 431], [36, 410], [10, 402], [-6, 394], [-17, 380], [-22, 350], [-24, 300], [-27, 250], [-30, 216],
];
const EAR_SIDE = [[-6, 62], [6, 60], [12, 72], [8, 90], [-2, 92], [-8, 80]];
const SIDE = {
  neck_flexors: { deep: 1, p: [[[-8, 100], [0, 100], [2, 166], [-6, 168]]] },
  suboccipitals: { deep: 1, p: [[[-46, 96], [-24, 94], [-22, 108], [-38, 113]]] },
  levator: { deep: 1, p: [[[-18, 104], [-8, 106], [-30, 190], [-40, 186]]] },
  rhomboids: { deep: 1, p: [[[-56, 200], [-44, 198], [-44, 260], [-56, 256]]] },
  pec_minor: { deep: 1, p: [[[30, 206], [42, 212], [58, 248], [58, 272], [42, 268], [30, 236]]] },
  erectors_thor: { deep: 1, p: [[[-54, 196], [-42, 200], [-40, 260], [-38, 340], [-50, 340], [-54, 280]]] },
  transversus: { deep: 1, p: [[[-34, 350], [44, 334], [50, 430], [38, 452], [-10, 420], [-36, 396]]], lines: [[[-30, 370], [46, 360]], [[-24, 398], [48, 398]]] },
  iliopsoas: { deep: 1, p: [[[-34, 326], [-24, 326], [-16, 376], [-6, 402], [14, 398], [26, 430], [37, 478], [31, 508], [4, 528], [-4, 520], [14, 494], [2, 464], [-14, 438], [-30, 400]]], lines: [[[-6, 404], [14, 470]]] },
  glute_min: { deep: 1, p: [[[-34, 420], [6, 414], [16, 436], [4, 466], [-6, 478], [-20, 456]]] },
  piriformis: { deep: 1, p: [[[-58, 444], [-48, 440], [-14, 474], [0, 488], [-2, 499], [-20, 490], [-54, 466]]] },
  tib_post: { deep: 1, p: [[[-6, 772], [4, 772], [2, 870], [-4, 932], [4, 960], [24, 970], [22, 980], [0, 973], [-12, 940], [-10, 870]]] },
  foot_arch: { deep: 1, p: [[[-22, 992], [0, 984], [40, 978], [80, 984], [110, 993], [108, 1000], [40, 1000], [-20, 1000]]] },
  erectors_lumb: { p: [[[-50, 336], [-36, 340], [-32, 390], [-42, 422], [-52, 412], [-46, 380]]] },
  trap_low: { p: [[[-60, 226], [-44, 220], [-44, 280], [-60, 292]]] },
  trap_mid: { p: [[[-50, 184], [-30, 178], [-30, 196], [-50, 226], [-62, 226], [-60, 190]]] },
  trap_upper: { p: [[[-50, 100], [-34, 104], [-24, 130], [-10, 160], [6, 176], [12, 184], [-8, 186], [-30, 178], [-50, 186], [-40, 150], [-36, 128]]] },
  scm: { p: [[[-12, 94], [0, 95], [30, 150], [44, 166], [32, 172], [18, 150]]] },
  serratus: { p: [[[28, 262], [46, 272], [40, 282], [54, 292], [46, 302], [58, 312], [48, 324], [34, 330], [26, 300]]] },
  pec_major: { p: [[[38, 168], [54, 180], [68, 212], [74, 244], [68, 266], [50, 276], [32, 250], [28, 210]]] },
  lats: { p: [[[-30, 250], [-56, 262], [-54, 310], [-46, 350], [-38, 388], [-24, 392], [-22, 340], [-26, 300]]] },
  obliques: { p: [[[24, 334], [52, 320], [56, 380], [58, 440], [46, 470], [34, 448], [10, 428], [-20, 412], [-36, 392], [-28, 360]]] },
  rectus_abd: { p: [[[48, 292], [62, 292], [60, 340], [64, 380], [66, 410], [62, 445], [53, 490], [44, 488], [52, 440], [52, 380], [50, 330]]] },
  glute_med: { p: [[[-48, 410], [-20, 401], [10, 405], [24, 426], [14, 452], [-2, 480], [-16, 488], [-32, 456], [-46, 432]]] },
  glute_max: { p: [[[-52, 418], [-66, 446], [-72, 480], [-68, 512], [-60, 542], [-36, 548], [-12, 538], [2, 520], [-16, 490], [-32, 456], [-44, 430]]] },
  tfl: { p: [[[22, 426], [36, 436], [40, 470], [32, 520], [22, 540], [12, 536], [14, 490], [16, 450]]] },
  vasti: { p: [[[30, 540], [40, 560], [44, 620], [40, 694], [44, 704], [28, 716], [8, 712], [-14, 690], [-22, 640], [-18, 580], [-6, 548], [12, 540]]] },
  rectus_fem: { p: [[[36, 500], [58, 515], [68, 560], [68, 600], [60, 660], [52, 700], [40, 694], [44, 620], [40, 560], [32, 520]]] },
  hamstrings: { p: [[[-62, 538], [-36, 548], [-22, 580], [-16, 640], [-16, 690], [-20, 730], [-12, 752], [-22, 757], [-32, 730], [-42, 690], [-54, 620], [-62, 570]]] },
  soleus: { p: [[[-14, 780], [-2, 790], [-4, 850], [-12, 900], [-20, 925], [-28, 900], [-28, 870], [-20, 842], [-14, 800]]] },
  gastrocnemius: { p: [[[-36, 720], [-20, 726], [-14, 760], [-14, 800], [-22, 840], [-34, 864], [-48, 830], [-50, 790], [-46, 750]]] },
  peroneus: { decor: 1, p: [[[4, 760], [22, 770], [24, 860], [14, 930], [4, 946], [0, 920], [2, 850]]] },
  tib_ant: { decor: 1, p: [[[38, 762], [50, 770], [42, 850], [36, 920], [28, 940], [26, 920], [30, 850], [30, 770]]] },
  achilles: { decor: 1, p: [[[-26, 900], [-16, 902], [-18, 956], [-28, 956]]] },
};
const SIDE_ARM = {
  triceps: { p: [[[-32, 250], [-14, 262], [-8, 320], [-4, 378], [-14, 394], [-26, 340], [-32, 280]]] },
  biceps: { p: [[[14, 262], [34, 268], [32, 320], [32, 356], [22, 364], [16, 320]]] },
  brachiorad: { decor: 1, p: [[[22, 346], [34, 360], [60, 385], [90, 411], [112, 431], [106, 437], [84, 419], [56, 399], [30, 381], [20, 364]]] },
  delt_post: { p: [[[-10, 180], [-12, 210], [-8, 260], [4, 302], [-18, 262], [-34, 220], [-32, 190]]] },
  delt_mid: { p: [[[0, 176], [6, 210], [10, 260], [14, 302], [4, 302], [-8, 260], [-12, 210], [-10, 178]]] },
  delt_ant: { p: [[[0, 176], [32, 188], [36, 220], [28, 262], [14, 302], [10, 260], [6, 210]]] },
};
const SIDE_DECOR_LINES = [[[8, 530], [12, 712]]];

const VIEWS = {
  front: { muscles: FRONT, sym: true, xr: [-212, 212] },
  back: { muscles: BACK, sym: true, xr: [-212, 212] },
  side: { muscles: SIDE, arm: SIDE_ARM, sym: false, xr: [-74, 196] },
};

// ---------- текст ----------
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
function cleanText(s) {
  return String(s).replace(/[—–]/g, '-').replace(/[«»“”„]/g, '"')
    .replace(/×/g, 'х').replace(/°/g, ' град.').replace(/[•→]/g, '');
}
const textW = (s, size) => s.length * size * 0.57;
function wrap(s, size, maxW) {
  const words = cleanText(s).split(/\s+/).filter(Boolean);
  const lines = [];
  let cur = '';
  for (const w of words) {
    const t = cur ? cur + ' ' + w : w;
    if (textW(t, size) > maxW && cur) { lines.push(cur); cur = w; } else cur = t;
  }
  if (cur) lines.push(cur);
  return lines;
}

// ---------- отрисовка фигуры ----------
function drawFigure(view, T, hl, st, uid) {
  const V = VIEWS[view];
  const out = [];
  const anchors = {};
  const clipId = `clip_${uid}`;
  const bodyPts = view === 'side' ? BODY_SIDE : BODY_FB;
  const bodyD = smooth(tf(bodyPts, T));
  out.push(`<clipPath id="${clipId}"><path d="${bodyD}"/></clipPath>`);
  out.push(`<path d="${bodyD}" fill="${C.body}" stroke="none"/>`);

  const shapes = (m) => {
    const res = [];
    for (const p of m.p) {
      res.push(p);
      if (V.sym) res.push(mirror(p));
    }
    return res;
  };
  const lines = (m) => {
    const res = [];
    for (const l of m.lines || []) { res.push(l); if (V.sym) res.push(mirror(l)); }
    return res;
  };

  function drawSet(set, clip) {
    const g = [`<g clip-path="url(#${clip})">`];
    const deepLater = [];
    for (const [id, m] of Object.entries(set)) {
      const on = hl.includes(id);
      if (m.deep && !on) continue;
      if (on) {
        // якорь подписи: центр формы с правой стороны рисунка
        const main = m.p.reduce((a, p) => (centroid(p)[0] > centroid(a)[0] ? p : a), m.p[0]);
        const c = centroid(main);
        anchors[id] = [T.x + c[0] * T.s, T.y + c[1] * T.s];
        if (view === 'side' && set === V.muscles) anchors[id] = visibleAnchor(anchors[id], tf(main, T), tf(ARM_SIDE, T));
      }
      if (m.deep || (m.cover && on)) { deepLater.push([id, m]); if (m.deep) continue; }
      for (const p of shapes(m)) {
        const d = smooth(tf(p, T));
        if (on && !m.cover) g.push(`<path d="${d}" fill="${st.fill}" fill-opacity="${st.op}" stroke="${st.stroke}" stroke-width="1.4" stroke-linejoin="round"/>`);
        else g.push(`<path d="${d}" fill="${C.body}" stroke="${C.muscle}" stroke-width="1.2" stroke-linejoin="round"/>`);
      }
      for (const l of lines(m)) g.push(`<path d="${smooth(tf(l, T), false)}" fill="none" stroke="${on ? st.stroke : C.muscle}" stroke-width="1" stroke-opacity="0.8"/>`);
    }
    for (const [, m] of deepLater) {
      for (const p of shapes(m)) {
        g.push(`<path d="${smooth(tf(p, T))}" fill="${st.fill}" fill-opacity="${Math.min(st.op, 0.7)}" stroke="${st.stroke}" stroke-width="1.6" stroke-dasharray="5 3" stroke-linejoin="round"/>`);
      }
      for (const l of lines(m)) g.push(`<path d="${smooth(tf(l, T), false)}" fill="none" stroke="${st.stroke}" stroke-width="1" stroke-opacity="0.8"/>`);
    }
    g.push('</g>');
    return g.join('\n');
  }

  // вспомогательные линии (ключица, позвоночник, IT-тракт)
  const decor = view === 'front' ? FRONT_DECOR_LINES : view === 'back' ? BACK_DECOR_LINES : SIDE_DECOR_LINES;
  const decorSvg = [];
  for (const l of decor) {
    const ls = V.sym && l[0][0] !== 0 ? [l, mirror(l)] : [l];
    for (const x of ls) decorSvg.push(`<path d="${smooth(tf(x, T), false)}" fill="none" stroke="${C.muscle}" stroke-width="1.2"/>`);
  }

  out.push(drawSet(V.muscles, clipId));
  out.push(`<g clip-path="url(#${clipId})">${decorSvg.join('')}</g>`);
  if (view === 'front') {
    const nav = tf([[0, 378]], T)[0];
    out.push(`<ellipse cx="${nav[0]}" cy="${nav[1]}" rx="${3 * T.s}" ry="${5 * T.s}" fill="none" stroke="${C.muscle}" stroke-width="1.2"/>`);
    for (const sx of [1, -1]) {
      const pk = tf([[48 * sx, 712]], T)[0];
      out.push(`<ellipse cx="${pk[0]}" cy="${pk[1]}" rx="${11 * T.s}" ry="${14 * T.s}" fill="none" stroke="${C.muscle}" stroke-width="1.2"/>`);
    }
  }
  if (view === 'side') {
    const pk = tf([[50, 704]], T)[0];
    out.push(`<ellipse cx="${pk[0]}" cy="${pk[1]}" rx="${7 * T.s}" ry="${15 * T.s}" fill="none" stroke="${C.muscle}" stroke-width="1.2"/>`);
  }
  out.push(`<path d="${bodyD}" fill="none" stroke="${C.outline}" stroke-width="2.6" stroke-linejoin="round"/>`);

  if (V.sym) {
    // уши и голова поверх шеи
    for (const e of [EAR_FB, mirror(EAR_FB)]) out.push(`<path d="${smooth(tf(e, T))}" fill="${C.body}" stroke="${C.outline}" stroke-width="2.2"/>`);
    out.push(`<path d="${smooth(tf(view === 'front' ? HEAD_FRONT : HEAD_BACK, T))}" fill="${C.body}" stroke="${C.outline}" stroke-width="2.6" stroke-linejoin="round"/>`);
  } else {
    out.push(`<path d="${smooth(tf(EAR_SIDE, T))}" fill="none" stroke="${C.outline}" stroke-width="2"/>`);
    out.push(`<path d="${smooth(tf([[48, 54], [56, 52]], T), false)}" fill="none" stroke="${C.outline}" stroke-width="2" stroke-linecap="round"/>`);
    // ближняя рука поверх корпуса
    const armClip = `clip_${uid}_arm`;
    const armD = smooth(tf(ARM_SIDE, T));
    out.push(`<clipPath id="${armClip}"><path d="${armD}"/></clipPath>`);
    out.push(`<path d="${armD}" fill="${C.body}" stroke="none"/>`);
    out.push(drawSet(V.arm, armClip));
    // верх дельты тонкой линией (плечо замкнуто), толстый контур руки коротко сходит на нет у линии дельты (y 200-215)
    out.push(`<path d="${armD}" fill="none" stroke="${C.muscle}" stroke-width="1.2" stroke-linejoin="round"/>`);
    const armOpen = ARM_SIDE.slice(4).concat(ARM_SIDE.slice(0, 1));
    const fadeId = `fade_${uid}_arm`;
    const [y0, y1] = [T.y + 200 * T.s, T.y + 215 * T.s];
    out.push(`<linearGradient id="${fadeId}" gradientUnits="userSpaceOnUse" x1="0" y1="${y0.toFixed(1)}" x2="0" y2="${y1.toFixed(1)}">` +
      `<stop offset="0" stop-color="${C.outline}" stop-opacity="0"/><stop offset="1" stop-color="${C.outline}" stop-opacity="1"/></linearGradient>`);
    out.push(`<path d="${smooth(tf(armOpen, T), false)}" fill="none" stroke="url(#${fadeId})" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>`);
  }
  return { svg: out.join('\n'), anchors };
}

// ---------- подписи в профиле: обход руки ----------
// рука в профиле лежит поверх таза и поясницы; линия подписи не должна резать предплечье и кисть
function segDist(p, q, a, b) {
  const cr = (o, u, v) => (u[0] - o[0]) * (v[1] - o[1]) - (u[1] - o[1]) * (v[0] - o[0]);
  const d1 = cr(a, b, p), d2 = cr(a, b, q), d3 = cr(p, q, a), d4 = cr(p, q, b);
  if (((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0))) return 0;
  const pd = (o, u, v) => {
    const dx = v[0] - u[0], dy = v[1] - u[1], l2 = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((o[0] - u[0]) * dx + (o[1] - u[1]) * dy) / l2));
    return Math.hypot(o[0] - u[0] - t * dx, o[1] - u[1] - t * dy);
  };
  return Math.min(pd(p, a, b), pd(q, a, b), pd(a, p, q), pd(b, p, q));
}
function insidePoly(pt, poly) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}
function pathHits(pts, poly, pad) {
  for (let i = 0; i + 1 < pts.length; i++) {
    for (let j = 0; j < poly.length; j++) {
      if (segDist(pts[i], pts[i + 1], poly[j], poly[(j + 1) % poly.length]) < pad) return true;
    }
  }
  return false;
}

// якорь мышцы в профиле, закрытой рукой: самая "глубокая" видимая точка мышцы вне руки
function visibleAnchor(a, musc, arm) {
  const edgeD = (pt, poly) => {
    let m = Infinity;
    for (let j = 0; j < poly.length; j++) m = Math.min(m, segDist(pt, pt, poly[j], poly[(j + 1) % poly.length]));
    return m;
  };
  if (!insidePoly(a, arm) && edgeD(a, arm) > 6) return a;
  const xs = musc.map((p) => p[0]), ys = musc.map((p) => p[1]);
  let best = null, bestD = 3;
  for (let x = Math.min(...xs); x <= Math.max(...xs); x += 1) {
    for (let y = Math.min(...ys); y <= Math.max(...ys); y += 1) {
      const pt = [x, y];
      if (!insidePoly(pt, musc) || insidePoly(pt, arm)) continue;
      const d = Math.min(edgeD(pt, musc), edgeD(pt, arm));
      if (d > bestD) { bestD = d; best = pt; }
    }
  }
  return best || a;
}

function parseViews(v) {
  if (!v) return ['front'];
  const arr = Array.isArray(v) ? v : String(v).split(/[\s,+|/]+/);
  const res = arr.map((x) => x.trim()).filter((x) => VIEWS[x]);
  return res.length ? res.slice(0, 3) : ['front'];
}

// ---------- страница ----------
function drawMuscle(opts = {}) {
  const views = parseViews(opts.views);
  const hl = Array.isArray(opts.highlight) ? opts.highlight : opts.highlight ? [opts.highlight] : [];
  const state = STATE[opts.state] ? opts.state : 'neutral';
  const st = STATE[state];
  const notes = (opts.notes || []).slice(0, 4);

  // раскладка: фигуры слева, справа колонка с подписью и заметками
  const figTop = 104, figBottom = 604;
  const s = (figBottom - figTop) / 1000;
  const gap = 44;
  const widths = views.map((v) => (VIEWS[v].xr[1] - VIEWS[v].xr[0]) * s);
  const groupW = widths.reduce((a, b) => a + b, 0) + gap * (views.length - 1);
  let left = Math.max(30, (40 + 480) / 2 - groupW / 2);
  const parts = [];
  const figs = [];
  views.forEach((v, i) => {
    const T = { x: left - VIEWS[v].xr[0] * s, y: figTop, s };
    const r = drawFigure(v, T, hl, st, `${(opts.key || 'm').replace(/[^\w]/g, '')}_${i}`);
    figs.push({ v, T, left, right: left + widths[i], anchors: r.anchors });
    parts.push(r.svg);
    parts.push(`<text x="${left + widths[i] / 2}" y="${figBottom + 28}" text-anchor="middle" font-family="${FONT}" font-size="16" fill="#607D8B">${VIEW_LABEL[v]}</text>`);
    left += widths[i] + gap;
  });
  const groupRight = figs[figs.length - 1].right;
  const colX = Math.max(groupRight + 44, 490);
  const colW = W - 36 - colX;

  // заметки
  const noteSize = 18, lineH = 24, noteGap = 12, noteIndent = 18;
  const noteLines = notes.map((n) => wrap(n, noteSize, colW - noteIndent));
  const notesH = noteLines.reduce((a, l) => a + l.length * lineH, 0) + noteGap * Math.max(0, notes.length - 1);

  // подписи выделенных мышц: линия от самой правой фигуры, где мышца есть
  const labels = [];
  for (const id of hl) {
    const f = [...figs].reverse().find((fg) => fg.anchors[id]);
    if (!f) continue;
    const a = f.anchors[id];
    const name = cleanText(hl.length === 1 && opts.label ? opts.label : (NAMES[id] || id));
    const L = { id, a, lines: wrap(name, 18, colW), y: a[1] };
    if (f.v === 'side') {
      // если прямая линия к колонке задевает руку, подпись опускаем ниже кисти
      L.arm = tf(ARM_SIDE, f.T).map((p) => [p[0], p[1]]);
      L.armBottom = Math.max(...L.arm.map((p) => p[1]));
      L.pad = insidePoly(a, L.arm) ? 0 : 5;
      if (L.pad && pathHits([a, [colX - 10, L.y]], L.arm, L.pad)) L.y = Math.max(L.y, L.armBottom + 14);
    }
    labels.push(L);
  }
  labels.sort((p, q) => p.y - q.y);
  let minY = figTop + 24;
  for (const L of labels) { L.y = Math.max(L.y, minY); minY = L.y + L.lines.length * 22 + 16; }
  let lblTop = labels.length ? labels[0].y - 24 : 9999;
  let lblBot = labels.length ? labels[labels.length - 1].y + labels[labels.length - 1].lines.length * 22 : -1;
  // заметки сверху колонки, если подписи внизу, иначе снизу
  const topStart = 128, bottomEnd = 628;
  let notesTop = topStart;
  if (lblTop < topStart + notesH + 20) notesTop = Math.max(lblBot + 40, bottomEnd - notesH);
  if (notesTop + notesH > bottomEnd + 10) notesTop = bottomEnd - notesH;
  // подпись, опущенная под кисть, не влезла над заметками: заметки наверх, подписи под них
  if (labels.some((L) => L.y > L.a[1]) && notesTop < lblBot + 24) {
    const dy = topStart + notesH + 32 - lblTop;
    if (dy > 0 && lblBot + dy <= bottomEnd) {
      for (const L of labels) L.y += dy;
      lblTop += dy; lblBot += dy; notesTop = topStart;
    }
  }
  for (const L of labels) {
    const end = [colX - 10, L.y];
    L.path = [L.a, end];
    if (!L.arm || !L.pad || !pathHits(L.path, L.arm, L.pad)) continue;
    // линия с изломом под кистью: наклонный отрезок от якоря, дальше горизонтально к колонке
    for (let ex = colX - 20; ex >= L.a[0]; ex -= 6) {
      const cand = [L.a, [ex, L.y], end];
      if (!pathHits(cand, L.arm, L.pad)) { L.path = cand; break; }
    }
  }

  const labelSvg = labels.map((L) => {
    const t = L.lines.map((ln, k) => `<tspan x="${colX}" y="${L.y + k * 22 + 6}">${esc(ln)}</tspan>`).join('');
    const d = L.path.map((p, k) => `${k ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
    return `<path d="${d}" stroke="${C.outline}" stroke-width="1.4" fill="none" stroke-linejoin="round"/>` +
      `<circle cx="${L.a[0].toFixed(1)}" cy="${L.a[1].toFixed(1)}" r="3.5" fill="${C.outline}"/>` +
      `<text font-family="${FONT}" font-size="18" font-weight="bold" fill="${st.stroke}">${t}</text>`;
  }).join('\n');

  // шапка
  const title = esc(cleanText(opts.title || NAMES[hl[0]] || ''));
  const latin = opts.latin ? esc(cleanText(opts.latin)) : '';
  const badge = st.badge;
  const bw = badge.length * 16 * 0.68 + 28;
  const anyDeep = hl.some((id) => views.some((v) => { const m = VIEWS[v].muscles[id] || (VIEWS[v].arm || {})[id] || {}; return m.deep || m.cover; }));
  const dl = 'глубокая мышца, под другими';
  const dlx = W - 40 - textW(dl, 14);
  const head = [
    `<text x="40" y="48" font-family="${FONT}" font-size="28" font-weight="bold" fill="${C.title}">${title}</text>`,
    latin ? `<text x="40" y="78" font-family="${FONT}" font-size="18" font-style="italic" fill="${C.hint}">${latin}</text>` : '',
    `<rect x="${W - 40 - bw}" y="26" width="${bw}" height="30" rx="15" fill="${st.fill}"/>`,
    `<text x="${W - 40 - bw / 2}" y="47" text-anchor="middle" font-family="${FONT}" font-size="16" font-weight="bold" fill="#ffffff">${badge}</text>`,
    anyDeep ? `<rect x="${dlx - 32}" y="68" width="22" height="14" rx="3" fill="${st.fill}" fill-opacity="0.6" stroke="${st.stroke}" stroke-width="1.5" stroke-dasharray="4 2"/>` +
      `<text x="${dlx}" y="80" font-family="${FONT}" font-size="14" fill="${C.hint}">${dl}</text>` : '',
  ].join('\n');

  const noteSvg = [];
  let y = notesTop + 16;
  noteLines.forEach((ls) => {
    noteSvg.push(`<circle cx="${colX + 5}" cy="${y - 6}" r="5" fill="${st.fill}"/>`);
    ls.forEach((ln) => { noteSvg.push(`<text x="${colX + noteIndent}" y="${y}" font-family="${FONT}" font-size="${noteSize}" fill="${C.hint}">${esc(ln)}</text>`); y += lineH; });
    y += noteGap;
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<rect width="${W}" height="${H}" fill="#ffffff"/>
${head}
${parts.join('\n')}
${labelSvg}
${noteSvg.join('\n')}
</svg>`;
}

module.exports = { drawMuscle, NAMES, MUSCLE_IDS: Object.keys(NAMES).slice(0, 36), VIEWS };
