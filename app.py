import json
import os
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- CONFIGURATION ---
SELLER_WHATSAPP = "213541099824" 

# --- 1. SHIPPING RATES (سعر التوصيل) ---
# I have set realistic defaults. You can change the numbers here.
# Format: "Wilaya Code": Price_In_DZD
SHIPPING_RATES = {
    # Algiers (Cheapest)
    "16": 400,
    
    # Coastal/North (Standard ~600DA)
    "9": 600, "2": 600, "42": 600, "35": 600, "15": 600, "6": 600, "19": 600, "25": 600, "31": 600, "13": 600,
    
    # South/Far South (Expensive ~900-1200DA)
    "1": 1000, "3": 900, "8": 1000, "11": 1200, "30": 900, "33": 1200, "39": 900, "47": 900, "50": 1200,
    "53": 1200, "54": 1200, "56": 1200, "58": 1000
}

# Fill the rest with a default of 700 DA if not specified above
for i in range(1, 70):
    code = str(i)
    if code not in SHIPPING_RATES:
        SHIPPING_RATES[code] = 700

# --- 2. DATA: 69 Wilayas ---
WILAYAS = {
    "1":"أدرار", "2":"الشلف", "3":"الأغواط", "4":"أم البواقي", "5":"باتنة", "6":"بجاية", "7":"بسكرة", "8":"بشار", "9":"البليدة", "10":"البويرة",
    "11":"تمنراست", "12":"تبسة", "13":"تلمسان", "14":"تيارت", "15":"تيزي وزو", "16":"الجزائر", "17":"الجلفة", "18":"جيجل", "19":"سطيف", "20":"سعيدة",
    "21":"سكيكدة", "22":"سيدي بلعباس", "23":"عنابة", "24":"قالمة", "25":"قسنطينة", "26":"المدية", "27":"مستغانم", "28":"المسيلة", "29":"معسكر", "30":"ورقلة",
    "31":"وهران", "32":"البيض", "33":"إليزي", "34":"برج بوعريريج", "35":"بومرداس", "36":"الطارف", "37":"تندوف", "38":"تيسمسيلت", "39":"الوادي", "40":"خنشلة",
    "41":"سوق أهراس", "42":"تيبازة", "43":"ميلة", "44":"عين الدفلى", "45":"النعامة", "46":"عين تموشنت", "47":"غرداية", "48":"غليزان", "49":"تيميمون", "50":"برج باجي مختار",
    "51":"أولاد جلال", "52":"بني عباس", "53":"عين صالح", "54":"عين قزام", "55":"تقرت", "56":"جانت", "57":"المغير", "58":"المنيعة",
    "59":"آفلو", "60":"الابيض سيدي الشيخ", "61":"العريشة", "62":"القنطرة", "63":"بريكة", "64":"بوسعادة", "65":"بئر العاتر", "66":"قصر البخاري", "67":"قصر الشلالة", "68":"عين وسارة", "69":"مسعد"
}

# --- 3. DATA: HARDCODED COMMUNES ---
RAW_COMMUNES = {
    "1": "أدرار,تامست,شاروين,رقان,إن زغمير,تيت,قصر قدور,تسabit,أقبلي,أولف,تيمقتن,فنوغيل,زاوية كنتة,بودة,أنزجمير",
    "2": "الشلف,تنس,بنايرية,الكريمية,تاوقريت,بني حواء,الصبحة,منزل,الوادى,اولاد فارس,الشطية,الابيض مجاجة,اولاد بن عبد القادر,تاجنة,الظهرة,المرسى,الحجاج,سيدي عكاشة,سيدي عبد الرحمن,بني راشد,مصدق,سيدي معروف,ام الدروع",
    "3": "الأغواط,قصر الحيران,بن ناصر بن شهرة,سيدي مخلوف,حاسي الدلاعة,حاسي الرمل,عين ماضي,تاجرونة,الخنق,القلتة,بريدة,الغيشة,الحويطة,وادي مرة,وادي مزي",
    "4": "أم البواقي,عين البيضاء,عين مليلة,عين فكرون,عين ببوش,بريش,بوغرارة سعودي,بئر الشهداء,دهالة,الضلعة,فكرينة,هنشير تومغني,الجازية,مسكيانة,واد نيني,أولاد قاسم,أولاد حملة,أولاد زواي,الرحية,سيقوس,سوق نعمان,الزرق",
    "5": "باتنة,بريكة,عين التوتة,مروانة,نقاوس,تازولت,أريس,عين جاسر,الجزار,سريانة,منعة,المعذر,تيمقاد,راس العيون,وادي الماء,اولاد سي سليمان,تكوت,إينوغيسن,الشمرة,تيلاطو,عيون العصافير,فسديس,وادي الشعبة,تالخمت",
    "6": "بجاية,أقبو,أميزور,خراطة,سيدي عيش,صدوق,تيمزريت,سوق الإثنين,توجة,برباشة,القصر,أوقاس,ذراع القايد,كنديرة,بني معوش,شميني,أدكار,تيشي,سمعون,آيث إسماعيل",
    "7": "بسكرة,أولاد جلال,سيدي عقبة,مشونش,القنطرة,الوطاية,جمورة,عين زعطوط,البرانيس,جمورة,زريبة الوادي,المزيرعة,بوشقرون,ليشانة,طولقة,أورلال,أوماش,مليلي",
    "8": "بشار,العبادلة,القنادسة,بني ونيف,تبلبالة,تاغيت,لحمر,مريجة,عرق فراج,بوكايس",
    "9": "البليدة,بوفاريك,الأربعاء,الشفة,موزاية,العفرون,وادي العلايق,حمام ملوان,بوقرة,أولاد يعيش,شريعة,بن خليل,صومعة,قرواو,بوعرفة,عين الرمانة,جبابرة",
    "10": "البويرة,الأخضرية,سور الغزلان,عين بسام,بشلول,مشدالة,القادرية,بئر غبالو,الهاشمية,حيزر,تاغزوت,ايت لعزيز,عمر,الجباجبية,سوق الخميس,المقراني,الأسنام",
    "11": "تمنراست,أبالسة,إدلس,تاظروك,عين أمقل",
    "12": "تبسة,الشريعة,بئر العاتر,الونزة,العقلة,المريج,بولحاف الدير,الكويف,مرسط,العوينات,بوخضرة,الحمامات,نقرين,فركان,صفصاف الوسرة,بئر مقدم",
    "13": "تلمسان,مغنية,منصورة,شتمة,شتوان,ندرومة,الغزوات,سبدو,الحناية,أولاد ميمون,الرمشي,بني سنوس,سيدي الجيلالي,باب العسة,فلاوسن,عين تالوت,بني صاف,مرسى بن مهيدي",
    "14": "تيارت,السوقر,فرندة,قصر الشلالة,مهدية,رحوية,الدحموني,عين كرمس,مدروسة,حمادية,واد ليلي,مشرع الصفا,تخمرت,عين الذهب,شحيمة,قرطوفة",
    "15": "تيزي وزو,ذراع بن خدة,عزازقة,الأربعاء ناث إيراثن,ذراع الميزان,تيزي غنيف,بوزغن,عين الحمام,واضية,أبي يوسف,أزفون,تيقزيرت,إفرحونن,بني يني,مشطراس,بوغني,معاتقة,فريحة,تيميزار",
    "16": "الجزائر الوسطى,سيدي امحمد,المدنية,الحامة,باب الوادي,القصبة,بولوغين,رايس حميدو,وادي قريش,الأبيار,بن عكنون,بني مسوس,بوزريعة,الحراش,بوروبة,وادي السمار,باش جراح,حسين داي,القبة,بئر مراد رايس,حيدرة,المحمدية,الدار البيضاء,باب الزوار,برج الكيفان,برج البحري,المرسى,عين طاية,هراوة,رويبة,رغاية,عين طاية,بئر خادم,جسر قسنطينة,السحاولة,بئر توتة,تسالة المرجة,أولاد شبل,زرالدة,سطاوالي,سودانية,معالمة,الرحمانية,درارية,العاشور,بابا حسن,خرايسية,دويـرة",
    "17": "الجلفة,عين وسارة,مسعد,حاسي بحبح,دار الشيوخ,الشارف,الإدريسية,البيرين,سيدي لعجال,حد الصحاري,فيض البطمة,المجبارة,عين الإبل,قطارة,دلدول,تعظميت",
    "18": "جيجل,الطاهير,الميلية,العنصر,الجمعة بني حبيبي,الشقفة,العوانة,زيامة منصورية,سيدي عبد العزيز,قاول,بوراوي بلهادف,وجانة,سطارة,جيملة,إيراقن سويسي",
    "19": "سطيف,العلمة,عين ولمان,عين أرنات,عين آزال,عين الكبيرة,بوقاعة,جميلة,صالح باي,عموشة,بني عزيز,بابور,حمّام السخنة,ماوكلان,عين السبت,ذراع قائد,تالة إيفاسن",
    "20": "سعيدة,عين الحجر,يوب,سيدي بوبكر,أولاد إبراهيم,الحساسنة,مولاي لعربي,سيدي عمار,عين السلطان,تيرسين,هونت",
    "21": "سكيكدة,القل,عزابة,الحروش,تمالوس,رمضان جمال,بن عزوز,عين قشرة,أم الطوب,الحدائق,حمادي كرومة,felfela,بني زيد,الزيتونة,كركرة,بني بشير",
    "22": "سيدي بلعباس,سفيزف,بن باديس,تلاغ,تنيرة,رأس الماء,عين البرد,سيدي لحسن,سيدي علي بوسيدي,مرحوم,مولاي سليسن,بوخنفيس,تسالة,مصطفى بن ابراهيم,سيدي ابراهيم",
    "23": "عنابة,البوني,الحجار,سيدي عمار,برحال,التريعات,العلمة,الشرفة,واد العنب,سرايدي,شطايبي",
    "24": "قالمة,وادي الزناتي,هيليوبوليس,بوشقوف,عين مخلوف,حمام دباغ,لخزارة,بومهرة أحمد,بلخير,عين العربي,تاملوكة,الركنية,سلاوة عنونة,عين رقادة,بوحشانة",
    "25": "قسنطينة,الخروب,حامة بوزيان,عين سمارة,زيغود يوسف,ديدوش مراد,أولاد رحمون,عين عبيد,ابن باديس,بني حميدان,مسعود بوجريو,ابن زياد",
    "26": "المدية,البرواقية,قصر البخاري,عين بوسيف,تابلاط,بني سليمان,العمارية,شلالة العذاورة,السواقي,الشهبونية,وزرة,سيدي نعمان,عزيز,القلب الكبير,الميهوب",
    "27": "مستغانم,عين تادلس,بوقيرات,سيدي علي,حاسي مماش,مزغران,خير الدين,سيدي لخضر,عشاشة,عين النويصي,بن عبد المالك رمضان,فرناكة,ستيدية,الحسيان,مازونة",
    "28": "المسيلة,بوسعادة,مقرة,أولاد دراج,حمـام الضلعة,سيدي عيسى,عين الحجل,برهوم,الشلال,عين الملح,بن سرور,امجدل,سيدي عامر,تامسة,جبل مساعد",
    "29": "معسكر,سيق,تيغنيف,المحمدية,غريس,وادي الأبطال,عين فكان,بوحنيفية,زهانة,هاشم,عقاز,المطمور,سيدي عبد الجبار,واد تاغية,مطمور,ماوسة",
    "30": "ورقلة,تقرت,الرويسات,عين البيضاء,سيدي خويلد,حاسي مسعود,الطيبات,تماسين,المقارين,الحجيرة,المنقر,البرمة,حاسي بن عبد الله",
    "31": "وهران,بئر الجير,السانية,أرزيو,قديل,بطيوة,حاسي بونيف,حاسي بن عقبة,سيدي الشحمي,مسرغين,العنصر,بوسفر,عين الترك,المرسى,بوتليليس,وادي تليلات,طافراوي,الكرمة,البرية",
    "32": "البيض,بريزينة,بوقطب,الأبيض سيدي الشيخ,الرقاصة,المحرة,بوسمغون,الشلالة,الكاف لحمر,استيتن,سيدي طيفور,سيدي اعمر",
    "33": "إليزي,جانت,عين أميناس,برج الحواس,برج عمر إدريس,دبداب",
    "34": "برج بوعريريج,رأس الوادي,برج زمورة,المنصورة,مجانة,الحمادية,عين تاغروت,بير قاصد علي,خليل,سيدي مبارك,اليشير,حسناوة,القلة",
    "35": "بومرداس,بودواو,دلس,برج منايل,خميس الخشنة,يسر,الثنية,زموري,أولاد موسى,سي مصطفى,تجلابين,شعبت العامر,الناصرية,بغلية,قورصو,حمادي",
    "36": "الطارف,القالة,بوثلجة,بن مهيدي,الذرعان,البسباس,شبيطة مختار,العيون,رامول,عصفور,زريزر,عين العسل,السوارخ",
    "37": "تندوف,أم العسل",
    "38": "تيسمسيلت,ثنية الحد,برج بونعامة,الأزهرية,لرجام,خميستي,العيون,عماري,سيدي عابد,بوقايد,بني شعيب,الملعب,سيدي بوتشنت",
    "39": "الوادي,المغير,جامعة,قمار,الرقيبة,الدبيلة,الرباح,حاسي خليفة,الطريفاوي,البياضة,النخلة,العقلة,وادي العلندة,اميه ونسة",
    "40": "خنشلة,ششار,قايس,أولاد رشاش,بابار,المحمل,عين الطويلة,بوحمامة,الحامة,الرميلة,طامزة,انسيغة,بغاي,يابوس",
    "41": "سوق أهراس,سدراتة,مداوروش,تاورة,الحدادة,المراهنة,أولاد إدريس,بئر بوحوش,المشروحة,أم العظائم,ويلان,سيدي فرج",
    "42": "تيبازة,شرشال,القليعة,بواسماعيل,قوراية,الداموس,حجوط,سيدي اعمر,فوكة,عين تاقورايت,بوهارون,خميستي,الشعيبة,أحمر العين,بورقيقة,سيدي راشد,مناصر",
    "43": "ميلة,شلغوم العيد,فرجيوة,تاجنانت,التلاغمة,وادي العثمانية,بوحاتم,عين البيضاء أحريش,سيدي مروان,القرارم قوقة,ترعي باينان,زغاية,الرواشد",
    "44": "عين الدفلى,خميس مليانة,مليانة,العطاف,الروينة,جندل,بومدفع,جليدة,بوراشد,العامرة,سيدي لخضر,حمام ريغة,عين التركي,طارق بن زياد",
    "45": "النعامة,مشرية,عين الصفراء,عسلة,مغرار,جنيين بورزق,تيوت,سفسيفة,مكمن بن عمار,القصدير,البيوض",
    "46": "عين تموشنت,حمام بوحجر,بني صاف,المالح,عين الأربعاء,ولهاصة,شنتوف,سيدي بن عدة,تارقة,المسعيد,وادي الصباح,عين الطلبة",
    "47": "غرداية,متليلي,القرارة,بريان,ضاية بن ضحوة,العطف,بونورة,زلفانة,المنصورة,سبسب",
    "48": "غليزان,وادي ارهيو,مازونة,زمورة,عمي موسى,يلل,سيدي امحمد بن علي,جديوية,المطمر,الحمادنة,منداس,عين طارق,الرمكة",
    "49": "تيميمون,أوقروت,شروين,طلمين,قصر قدور",
    "50": "برج باجي مختار,تيمياوين",
    "51": "أولاد جلال,سيدي خالد,رأس الميعاد,البسباس,الدوسن,الشعيبـة",
    "52": "بني عباس,الواتة,كيرزاز,إقلي,تامترت,القصابي,بني يخلف",
    "53": "عين صالح,فقارة الزوى,إينغر",
    "54": "عين قزام,تين زواتين",
    "55": "تقرت,تماسين,المقارين,المنقر,الطيبات,بن ناصر,العالية",
    "56": "جانت,برج الحواس",
    "57": "المغير,جامعة,سيدي عمران,سطيل,أم الطيور,تندلة,المرارة",
    "58": "المنيعة,حاسي القارة,حاسي لفحل",
    "59": "آفلو,سبقاق,سيدي بوزيد,البيضاء,قلتة سيدي سعد,بريدة,الحاج مشري",
    "60": "الابيض سيدي الشيخ,البنود,أربوات,عين العراك",
    "61": "العريشة,القور,سيدي جيلالي",
    "62": "القنطرة,عين زعطوط",
    "63": "بريكة,مدوكال,بيطام,عزيل عبد القادر",
    "64": "بوسعادة,الهامل,ولتام,بني يلمان,سيدي عامر",
    "65": "بئر العاتر,عقلة المالحة",
    "66": "قصر البخاري,المفتاحية,السانق,عزيز",
    "67": "قصر الشلالة,سرغين,زمالة الأمير عبد القادر",
    "68": "عين وسارة,قرنيني,سيدي لعجال",
    "69": "مسعد,دلدول,سلمانة,سد الرحال,قطارة"
}

# --- 4. DATA PROCESSING ---
LOCATIONS_DATA = {}

def prepare_locations():
    global LOCATIONS_DATA
    for code, name in WILAYAS.items():
        key = f"{code} - {name}"
        if code in RAW_COMMUNES:
            communes_list = RAW_COMMUNES[code].split(',')
            LOCATIONS_DATA[key] = sorted(communes_list)
        else:
            LOCATIONS_DATA[key] = [] 

prepare_locations()

# --- 5. FLASK APP & TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>بينك كومفورت - الحل المثالي</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
    
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Cairo', 'sans-serif'] },
                    colors: {
                        brand: { light: '#FCE7F3', DEFAULT: '#EC4899', dark: '#831843', grey: '#374151' },
                        whatsapp: '#25D366'
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-gray-50 text-brand-grey font-sans antialiased">

    <a href="https://wa.me/{{ seller_phone }}" target="_blank" 
       class="fixed bottom-6 left-6 z-50 bg-whatsapp hover:bg-green-600 text-white p-4 rounded-full shadow-2xl transition transform hover:scale-110 flex items-center gap-2">
        <i class="fab fa-whatsapp text-3xl"></i>
    </a>

    <nav class="bg-white shadow-sm py-4 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 flex justify-between items-center">
            <div class="text-2xl font-bold text-brand-dark tracking-tight flex items-center">
                <i class="fas fa-heart text-brand ml-2"></i>ComfortPad
            </div>
            <div class="text-sm font-semibold text-green-600 bg-green-50 px-3 py-1 rounded-full flex items-center">
                <i class="fas fa-shipping-fast ml-2"></i> توصيل 58 ولاية
            </div>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto px-4 py-8 md:py-12">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            
            <div class="space-y-8">
                
                <div class="space-y-4">
                    <div class="rounded-3xl overflow-hidden shadow-lg border border-brand-light bg-white relative group">
                        <img id="mainImage" src="https://i.ibb.co/4R8MwySb/Whats-App-Image-2026-01-26-at-17-34-44-1.jpg" 
                             alt="وسادة التدفئة" class="w-full h-auto object-cover transform transition">
                        
                        <div class="absolute bottom-4 right-4 bg-white/90 backdrop-blur px-4 py-2 rounded-lg text-sm font-bold text-brand-dark shadow-sm">
                            ⭐ 4.9/5
                        </div>
                    </div>

                    <div class="grid grid-cols-3 md:grid-cols-6 gap-2">
                        <button onclick="changeImage('https://i.ibb.co/4R8MwySb/Whats-App-Image-2026-01-26-at-17-34-44-1.jpg')" class="border-2 border-brand rounded-xl overflow-hidden hover:opacity-75 transition">
                            <img src="https://i.ibb.co/4R8MwySb/Whats-App-Image-2026-01-26-at-17-34-44-1.jpg" class="w-full object-cover aspect-square">
                        </button>
                        <button onclick="changeImage('https://i.ibb.co/7tKKM2Wn/Whats-App-Image-2026-01-26-at-17-34-44.jpg')" class="border-2 border-transparent rounded-xl overflow-hidden hover:opacity-75 transition">
                            <img src="https://i.ibb.co/7tKKM2Wn/Whats-App-Image-2026-01-26-at-17-34-44.jpg" class="w-full object-cover aspect-square">
                        </button>
                        <button onclick="changeImage('https://i.ibb.co/Kxhc6kP8/Whats-App-Image-2026-01-26-at-17-35-39.jpg')" class="border-2 border-transparent rounded-xl overflow-hidden hover:opacity-75 transition">
                            <img src="https://i.ibb.co/Kxhc6kP8/Whats-App-Image-2026-01-26-at-17-35-39.jpg" class="w-full object-cover aspect-square">
                        </button>
                        <button onclick="changeImage('https://i.ibb.co/WpYpdw7x/Whats-App-Image-2026-01-26-at-17-35-40-1.jpg')" class="border-2 border-transparent rounded-xl overflow-hidden hover:opacity-75 transition">
                            <img src="https://i.ibb.co/WpYpdw7x/Whats-App-Image-2026-01-26-at-17-35-40-1.jpg" class="w-full object-cover aspect-square">
                        </button>
                        <button onclick="changeImage('https://i.ibb.co/Pv7rkY0c/Whats-App-Image-2026-01-26-at-17-35-40.jpg')" class="border-2 border-transparent rounded-xl overflow-hidden hover:opacity-75 transition">
                            <img src="https://i.ibb.co/Pv7rkY0c/Whats-App-Image-2026-01-26-at-17-35-40.jpg" class="w-full object-cover aspect-square">
                        </button>
                        <button onclick="changeImage('https://i.ibb.co/pG04PYs/Whats-App-Image-2026-01-26-at-17-35-41.jpg')" class="border-2 border-transparent rounded-xl overflow-hidden hover:opacity-75 transition">
                            <img src="https://i.ibb.co/pG04PYs/Whats-App-Image-2026-01-26-at-17-35-41.jpg" class="w-full object-cover aspect-square">
                        </button>
                    </div>
                </div>
                
                <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-4">
                    <h2 class="text-2xl font-black text-brand-dark leading-tight">
                        💗 تعانين كل شهر من آلام الدورة؟
                    </h2>
                    <p class="text-lg text-gray-600 font-medium">
                        تشنجات مزعجة وآلام أسفل الظهر تفسد يومك؟
                    </p>
                    
                    <div class="bg-brand-light/30 p-4 rounded-xl border border-brand-light">
                        <p class="font-bold text-brand-dark mb-3 text-lg">
                            ✨ وسادة التدفئة والتدليك الذكية تمنحك راحة فورية من أول استعمال:
                        </p>
                        <ul class="space-y-3">
                            <li class="flex items-start">
                                <span class="text-brand mt-1 ml-2"><i class="fas fa-check-circle"></i></span>
                                <span class="font-semibold text-gray-700">تخفف آلام الحيض بشكل ملحوظ</span>
                            </li>
                            <li class="flex items-start">
                                <span class="text-brand mt-1 ml-2"><i class="fas fa-fire"></i></span>
                                <span class="font-semibold text-gray-700">تدفئة عميقة + تدليك مهدّئ</span>
                            </li>
                            <li class="flex items-start">
                                <span class="text-brand mt-1 ml-2"><i class="fas fa-battery-full"></i></span>
                                <span class="font-semibold text-gray-700">لاسلكية، خفيفة وسهلة الحمل</span>
                            </li>
                        </ul>
                    </div>

                    <div class="flex items-center justify-between text-sm text-gray-500 pt-2 border-t border-gray-100">
                        <span><i class="fas fa-box ml-1"></i> الدفع عند الاستلام</span>
                        <span><i class="fas fa-shield-alt ml-1"></i> ضمان الرضا</span>
                    </div>
                </div>
            </div>

            <div class="sticky top-24">
                <div class="bg-white rounded-2xl shadow-xl border border-brand-light p-6 md:p-8 relative">
                    
                    <div class="bg-red-50 border border-red-100 rounded-lg p-3 mb-4 flex justify-between items-center animate-pulse">
                        <span class="text-red-600 font-bold text-sm flex items-center">
                            <i class="fas fa-fire mr-2"></i> الكمية محدودة
                        </span>
                        <span class="text-red-600 font-extrabold text-sm">اغتنمي الفرصة الأن!</span>
                    </div>

                    <h2 class="text-2xl font-bold text-brand-dark mb-1">اطلب الآن والدفع عند الاستلام</h2>
                    <p class="text-sm text-gray-500 mb-6">املأ المعلومات بعناية لضمان وصول الطلب.</p>

                    <form action="/order" method="POST" class="space-y-4">
                        <div class="bg-brand-light/30 p-4 rounded-xl border border-brand-light mb-6">
                            <label class="flex items-center justify-between cursor-pointer mb-3">
                                <div class="flex items-center">
                                    <input type="radio" name="offer" value="1 Pack" class="w-5 h-5 text-brand focus:ring-brand" checked onchange="updateTotal()">
                                    <span class="mr-2 font-semibold">حبة واحدة</span>
                                </div>
                                <span class="font-bold text-brand-dark">3,900 دج</span>
                            </label>
                            <hr class="border-brand-light my-2">
                            <label class="flex items-center justify-between cursor-pointer">
                                <div class="flex items-center">
                                    <input type="radio" name="offer" value="2 Packs" class="w-5 h-5 text-brand focus:ring-brand" onchange="updateTotal()">
                                    <span class="mr-2 font-semibold">حبتين (تخفيض)</span>
                                </div>
                                <span class="font-bold text-brand-dark">7,5400 دج</span>
                            </label>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">الاسم الكامل</label>
                            <input type="text" name="fullname" required class="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-brand">
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">رقم الهاتف</label>
                            <input type="tel" name="phone" required dir="ltr" style="text-align:right" placeholder="05 XX XX XX XX" 
                                class="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-brand">
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">الولاية</label>
                                <select id="wilaya" name="wilaya" onchange="loadCommunes()" required 
                                    class="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-brand bg-white">
                                    <option value="" disabled selected>اختر الولاية</option>
                                    {% for wilaya_key in locations.keys() %}
                                    <option value="{{ wilaya_key }}">{{ wilaya_key }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">البلدية</label>
                                <select id="commune" name="commune" required disabled 
                                    class="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-brand bg-white disabled:bg-gray-100">
                                    <option value="">اختر الولاية أولاً</option>
                                </select>
                            </div>
                        </div>

                        <div id="orderSummary" class="hidden bg-gray-50 p-4 rounded-xl border border-gray-200 mt-4 space-y-2 text-sm">
                            <div class="flex justify-between text-gray-600">
                                <span>سعر المنتج:</span>
                                <span id="productPriceDisplay" class="font-bold">3900 دج</span>
                            </div>
                            <div class="flex justify-between text-gray-600">
                                <span>سعر التوصيل:</span>
                                <span id="shippingPriceDisplay" class="font-bold">-- دج</span>
                            </div>
                            <div class="border-t border-gray-200 pt-2 flex justify-between text-brand-dark text-lg font-bold">
                                <span>المجموع الكلي:</span>
                                <span id="totalPriceDisplay">-- دج</span>
                            </div>
                        </div>

                        <input type="hidden" name="final_total" id="final_total_input">

                        <button type="submit" class="w-full bg-brand hover:bg-brand-dark text-white font-bold py-4 rounded-xl shadow-lg mt-4 transition transform active:scale-95">
                            تأكيد الطلب
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        const locations = {{ locations | tojson }};
        const shippingRates = {{ shipping_rates | tojson }};
        
        // Prices matching the Radio Buttons above
        const prices = {
            "1 Pack": 3900,
            "2 Packs": 6500
        };

        function changeImage(src) {
            document.getElementById('mainImage').src = src;
        }

        function loadCommunes() {
            const wilayaSelect = document.getElementById("wilaya");
            const communeSelect = document.getElementById("commune");
            const selectedWilaya = wilayaSelect.value;
            
            // 1. Logic for Communes
            communeSelect.innerHTML = '<option value="">اختر البلدية</option>';
            communeSelect.disabled = false;

            if (selectedWilaya && locations[selectedWilaya]) {
                locations[selectedWilaya].sort().forEach(commune => {
                    const option = document.createElement("option");
                    option.value = commune;
                    option.text = commune;
                    communeSelect.appendChild(option);
                });
            } else {
                communeSelect.disabled = true;
            }

            // 2. Trigger Price Calculation
            updateTotal();
        }

        function updateTotal() {
            const wilayaSelect = document.getElementById("wilaya");
            const summaryBox = document.getElementById("orderSummary");
            
            // Get selected product price
            const selectedOffer = document.querySelector('input[name="offer"]:checked').value;
            const productPrice = prices[selectedOffer];

            // Get shipping price
            let shippingPrice = 0;
            if (wilayaSelect.value) {
                // Extract code (e.g., "16" from "16 - Alger")
                const code = wilayaSelect.value.split(" - ")[0];
                shippingPrice = shippingRates[code] || 700; // Default 700 if error
                
                // Show the box if hidden
                summaryBox.classList.remove("hidden");
            }

            // Calculate Total
            const total = productPrice + shippingPrice;

            // Update UI
            document.getElementById("productPriceDisplay").innerText = productPrice + " دج";
            
            if (shippingPrice > 0) {
                document.getElementById("shippingPriceDisplay").innerText = shippingPrice + " دج";
                document.getElementById("totalPriceDisplay").innerText = total + " دج";
                // Update hidden input for server
                document.getElementById("final_total_input").value = total;
            } else {
                document.getElementById("shippingPriceDisplay").innerText = "اختر الولاية";
                document.getElementById("totalPriceDisplay").innerText = "-- دج";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    # Pass Shipping Rates to HTML
    return render_template_string(HTML_TEMPLATE, locations=LOCATIONS_DATA, seller_phone=SELLER_WHATSAPP, shipping_rates=SHIPPING_RATES)

@app.route('/order', methods=['POST'])
def order():
    data = request.form
    fullname = data.get('fullname')
    phone = data.get('phone')
    wilaya = data.get('wilaya')
    commune = data.get('commune')
    offer = data.get('offer')
    
    # Get the calculated total from the hidden input
    final_total = data.get('final_total')

    # Construct WhatsApp URL with Total Price
    msg = f"سلام عليكم، أريد تأكيد طلبي:%0A👤 الاسم: {fullname}%0A📞 الهاتف: {phone}%0A📍 العنوان: {wilaya} - {commune}%0A📦 العرض: {offer}%0A💰 المجموع الكلي (مع التوصيل): {final_total} دج"
    wa_link = f"https://wa.me/{SELLER_WHATSAPP}?text={msg}"

    return f"""
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    </head>
    <body class="bg-gray-50 flex items-center justify-center min-h-screen font-[Cairo]">
        <div class="bg-white p-8 rounded-2xl shadow-xl text-center max-w-md mx-4">
            <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">🎉</div>
            <h1 class="text-2xl font-bold text-gray-800 mb-2">شكراً لك، {fullname}!</h1>
            <p class="text-gray-600 mb-6">تم تسجيل طلبك بقيمة إجمالية <strong>{final_total} دج</strong>.</p>
            
            <a href="{wa_link}" class="block w-full bg-[#25D366] hover:bg-green-600 text-white font-bold py-4 rounded-xl shadow-lg transition transform hover:scale-105 flex items-center justify-center gap-2">
                <span>تأكيد الطلب عبر واتساب</span>
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
            </a>
            
            <a href="/" class="block mt-4 text-gray-400 text-sm">العودة للصفحة الرئيسية</a>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4300))
    app.run(debug=False, host='0.0.0.0', port=port)