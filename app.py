import json
import os
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- CONFIGURATION ---
SELLER_WHATSAPP = "213541099824" 

# --- 1. SHIPPING RATES (سعر التوصيل) ---
# Preserved from your previous pricing request
SHIPPING_RATES = {
    # 550 DA
    "19": 550,  # Setif

    # 600 DA
    "34": 600, "16": 600,

    # 650 DA
    "25": 650,

    # 700 DA
    "23": 700, "5": 700, "6": 700, "9": 700, "10": 700, "35": 700, "18": 700,
    "28": 700, "42": 700, "15": 700, "2": 700, "31": 700,

    # 800 DA
    "40": 800, "26": 800, "43": 800, "4": 800, "21": 800, "44": 800, "27": 800,
    "46": 800, "29": 800, "48": 800, "22": 800, "14": 800, "13": 800,

    # 850 DA
    "36": 850, "24": 850, "41": 850, "12": 850, "38": 850,

    # 900 DA
    "20": 900, "7": 900, "51": 900, "17": 900, "3": 900,

    # 1000 DA
    "39": 1000, "57": 1000, "47": 1000, "58": 1000, "30": 1000, "55": 1000,

    # 1200 DA
    "8": 1200, "52": 1200, "32": 1200, "45": 1200,

    # 1500 DA
    "1": 1500, "49": 1500,

    # Special / Deep South
    "37": 1700,  # Tindouf
    "53": 1800,  # In Salah
    "33": 1900,  # Illizi
    "11": 2000,  # Tamanrasset
    
    # Missing from pricing list (Deep South Defaults)
    "50": 1800, "54": 1800, "56": 1800
}

# Default for any new/unknown codes (e.g. newly created wilayas)
for i in range(1, 70):
    code = str(i)
    if code not in SHIPPING_RATES:
        SHIPPING_RATES[code] = 900

# --- 2. DYNAMIC LOCATION LOADING (From algeria_cities.json) ---
WILAYAS = {}
LOCATIONS_DATA = {}

def load_geo_data():
    """Loads Wilayas and Communes from the JSON file dynamically"""
    global WILAYAS, LOCATIONS_DATA
    json_path = os.path.join(os.path.dirname(__file__), 'algeria_cities.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            cities = json.load(f)
            
        for entry in cities:
            # Convert "01" -> "1", "02" -> "2" to match our pricing keys
            w_code = str(int(entry['wilaya_code'])) 
            w_name = entry['wilaya_name']
            c_name = entry['commune_name']
            
            # Build Wilaya Dictionary
            WILAYAS[w_code] = w_name
            
            # Build Locations Dictionary (Key: "16 - Alger")
            key = f"{w_code} - {w_name}"
            if key not in LOCATIONS_DATA:
                LOCATIONS_DATA[key] = []
            
            if c_name not in LOCATIONS_DATA[key]:
                LOCATIONS_DATA[key].append(c_name)
        
        # Sort communes alphabetically
        for k in LOCATIONS_DATA:
            LOCATIONS_DATA[k].sort()
            
        print(f"✅ Successfully loaded {len(WILAYAS)} Wilayas and {len(cities)} Communes.")

    except FileNotFoundError:
        print("⚠️ ERROR: algeria_cities.json not found! Using fallback data.")
        # Minimal Fallback to prevent crash if file is missing
        WILAYAS = {"16": "الجزائر"}
        LOCATIONS_DATA = {"16 - الجزائر": ["الجزائر الوسطى", "باب الزوار"]}
    except Exception as e:
        print(f"⚠️ Error parsing JSON: {e}")

# Load data immediately when app starts
load_geo_data()

# --- 3. FLASK APP & TEMPLATE ---
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
                                    <span class="mr-2 font-semibold">قطعتين (تخفيض)</span>
                                </div>
                                <span class="font-bold text-brand-dark">6,500 دج</span>
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
                                    {% for location_key in locations.keys() %}
                                    <option value="{{ location_key }}">{{ location_key }}</option>
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

                        <div id="orderSummary" class="bg-gray-50 p-4 rounded-xl border border-gray-200 mt-4 space-y-2 text-sm">
                            <div class="flex justify-between text-gray-600">
                                <span>سعر المنتج:</span>
                                <span id="productPriceDisplay" class="font-bold">3900 دج</span>
                            </div>
                            <div class="flex justify-between text-gray-600">
                                <span>سعر التوصيل:</span>
                                <span id="shippingPriceDisplay" class="font-bold text-green-600">-- دج</span>
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
        // Sort keys numerically for display 1, 2, 3... instead of 1, 10, 11...
        // We pass the locations dict to JS
        const locations = {{ locations | tojson }};
        const shippingRates = {{ shipping_rates | tojson }};
        
        // Define product prices numerically for calculation
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
            
            // 1. Reset and Populate Communes
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

            // 2. Recalculate Totals based on new location
            updateTotal();
        }

        function updateTotal() {
            const wilayaSelect = document.getElementById("wilaya");
            
            // 1. Get Product Price
            const selectedOfferInput = document.querySelector('input[name="offer"]:checked');
            if (!selectedOfferInput) return;
            
            const selectedOfferValue = selectedOfferInput.value;
            // Force Number conversion
            const productPrice = Number(prices[selectedOfferValue] || 0);

            // 2. Get Shipping Price
            let shippingPrice = 0;
            let total = 0;

            if (wilayaSelect.value) {
                // Extract the code (e.g. "16" from "16 - Alger")
                const code = wilayaSelect.value.split(" - ")[0];
                
                if (shippingRates[code]) {
                    // Force Number conversion
                    shippingPrice = Number(shippingRates[code]);
                } else {
                    shippingPrice = 900; // Default
                }
            }

            // 3. Calculate Total (Math Addition)
            total = productPrice + shippingPrice;

            // 4. Update the UI
            document.getElementById("productPriceDisplay").innerText = productPrice + " دج";
            
            if (shippingPrice > 0) {
                document.getElementById("shippingPriceDisplay").innerText = shippingPrice + " دج";
                document.getElementById("totalPriceDisplay").innerText = total + " دج";
                // Update hidden input so backend gets the total
                document.getElementById("final_total_input").value = total;
            } else {
                document.getElementById("shippingPriceDisplay").innerText = "اختر الولاية";
                document.getElementById("totalPriceDisplay").innerText = "-- دج";
            }
        }
        
        // Run once on load to set initial state
        window.onload = updateTotal;
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    # Sort locations by ID (1, 2, 3...) instead of random dictionary order
    sorted_locations = dict(sorted(LOCATIONS_DATA.items(), key=lambda item: int(item[0].split(' - ')[0])))
    
    return render_template_string(HTML_TEMPLATE, locations=sorted_locations, seller_phone=SELLER_WHATSAPP, shipping_rates=SHIPPING_RATES)

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

    # WhatsApp Message
    msg = f"سلام عليكم، أريد تأكيد طلبي:%0A👤 الاسم: {fullname}%0A📞 الهاتف: {phone}%0A📍 العنوان: {wilaya} - {commune}%0A📦 العرض: {offer}%0A💰 المجموع الكلي: {final_total} دج"
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
            <p class="text-gray-600 mb-6">تم تسجيل طلبك بقيمة <strong>{final_total} دج</strong>. لتسريع عملية التوصيل، يرجى تأكيد العنوان عبر واتساب.</p>
            
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
