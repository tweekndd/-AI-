"""
国家→语言映射表（V2.2 新增）
用于多语言搜索：根据目标国家确定搜索语言、Google hl/lr/cr 参数
"""
from typing import Dict, Optional, Tuple

# 国家→语言信息映射
# 每个条目: (language_name, language_code_for_hl, google_cr_code)
# hl: Google 界面语言参数
# lr: Google 搜索结果语言限制（格式 lang_xx）
# cr: Google 国家限制（格式 countryXX）
_COUNTRY_LANG_MAP: Dict[str, Tuple[str, str, str, str]] = {
    # ── 西班牙语国家 ──
    "spain": ("Spanish", "es", "lang_es", "countryES"),
    "mexico": ("Spanish", "es", "lang_es", "countryMX"),
    "argentina": ("Spanish", "es", "lang_es", "countryAR"),
    "chile": ("Spanish", "es", "lang_es", "countryCL"),
    "colombia": ("Spanish", "es", "lang_es", "countryCO"),
    "peru": ("Spanish", "es", "lang_es", "countryPE"),
    "venezuela": ("Spanish", "es", "lang_es", "countryVE"),
    "ecuador": ("Spanish", "es", "lang_es", "countryEC"),
    "guatemala": ("Spanish", "es", "lang_es", "countryGT"),
    "cuba": ("Spanish", "es", "lang_es", "countryCU"),
    "bolivia": ("Spanish", "es", "lang_es", "countryBO"),
    "dominican republic": ("Spanish", "es", "lang_es", "countryDO"),
    "honduras": ("Spanish", "es", "lang_es", "countryHN"),
    "paraguay": ("Spanish", "es", "lang_es", "countryPY"),
    "el salvador": ("Spanish", "es", "lang_es", "countrySV"),
    "nicaragua": ("Spanish", "es", "lang_es", "countryNI"),
    "costa rica": ("Spanish", "es", "lang_es", "countryCR"),
    "panama": ("Spanish", "es", "lang_es", "countryPA"),
    "uruguay": ("Spanish", "es", "lang_es", "countryUY"),
    "equatorial guinea": ("Spanish", "es", "lang_es", "countryGQ"),

    # ── 葡萄牙语国家 ──
    "portugal": ("Portuguese", "pt", "lang_pt", "countryPT"),
    "brazil": ("Portuguese", "pt", "lang_pt", "countryBR"),
    "angola": ("Portuguese", "pt", "lang_pt", "countryAO"),
    "mozambique": ("Portuguese", "pt", "lang_pt", "countryMZ"),

    # ── 法语国家 ──
    "france": ("French", "fr", "lang_fr", "countryFR"),
    "belgium": ("French", "fr", "lang_fr", "countryBE"),
    "switzerland": ("French", "fr", "lang_fr", "countryCH"),
    "morocco": ("French", "fr", "lang_fr", "countryMA"),
    "algeria": ("French", "fr", "lang_fr", "countryDZ"),
    "tunisia": ("French", "fr", "lang_fr", "countryTN"),
    "senegal": ("French", "fr", "lang_fr", "countrySN"),
    "ivory coast": ("French", "fr", "lang_fr", "countryCI"),
    "cote d'ivoire": ("French", "fr", "lang_fr", "countryCI"),
    "cameroon": ("French", "fr", "lang_fr", "countryCM"),

    # ── 德语国家 ──
    "germany": ("German", "de", "lang_de", "countryDE"),
    "austria": ("German", "de", "lang_de", "countryAT"),
    # Switzerland already mapped to French; for German-speaking Switzerland:
    # We keep the country-level cr code, hl can be overridden later

    # ── 意大利语国家 ──
    "italy": ("Italian", "it", "lang_it", "countryIT"),

    # ── 荷兰语国家 ──
    "netherlands": ("Dutch", "nl", "lang_nl", "countryNL"),

    # ── 波兰语 ──
    "poland": ("Polish", "pl", "lang_pl", "countryPL"),

    # ── 阿拉伯语国家（中东/北非） ──
    "saudi arabia": ("Arabic", "ar", "lang_ar", "countrySA"),
    "uae": ("Arabic", "ar", "lang_ar", "countryAE"),
    "united arab emirates": ("Arabic", "ar", "lang_ar", "countryAE"),
    "qatar": ("Arabic", "ar", "lang_ar", "countryQA"),
    "kuwait": ("Arabic", "ar", "lang_ar", "countryKW"),
    "oman": ("Arabic", "ar", "lang_ar", "countryOM"),
    "bahrain": ("Arabic", "ar", "lang_ar", "countryBH"),
    "jordan": ("Arabic", "ar", "lang_ar", "countryJO"),
    "iraq": ("Arabic", "ar", "lang_ar", "countryIQ"),
    "egypt": ("Arabic", "ar", "lang_ar", "countryEG"),
    "libya": ("Arabic", "ar", "lang_ar", "countryLY"),
    "morocco": ("Arabic", "ar", "lang_ar", "countryMA"),
    "algeria": ("Arabic", "ar", "lang_ar", "countryDZ"),
    "tunisia": ("Arabic", "ar", "lang_ar", "countryTN"),
    "lebanon": ("Arabic", "ar", "lang_ar", "countryLB"),
    "syria": ("Arabic", "ar", "lang_ar", "countrySY"),
    "yemen": ("Arabic", "ar", "lang_ar", "countryYE"),
    "sudan": ("Arabic", "ar", "lang_ar", "countrySD"),

    # ── 俄语国家 ──
    "russia": ("Russian", "ru", "lang_ru", "countryRU"),
    "kazakhstan": ("Russian", "ru", "lang_ru", "countryKZ"),
    "belarus": ("Russian", "ru", "lang_ru", "countryBY"),
    "uzbekistan": ("Russian", "ru", "lang_ru", "countryUZ"),
    "ukraine": ("Ukrainian", "uk", "lang_uk", "countryUA"),

    # ── 日语 ──
    "japan": ("Japanese", "ja", "lang_ja", "countryJP"),

    # ── 韩语 ──
    "south korea": ("Korean", "ko", "lang_ko", "countryKR"),

    # ── 土耳其语 ──
    "turkey": ("Turkish", "tr", "lang_tr", "countryTR"),

    # ── 泰语 ──
    "thailand": ("Thai", "th", "lang_th", "countryTH"),

    # ── 越南语 ──
    "vietnam": ("Vietnamese", "vi", "lang_vi", "countryVN"),

    # ── 印尼语 ──
    "indonesia": ("Indonesian", "id", "lang_id", "countryID"),
    "malaysia": ("Malay", "ms", "lang_ms", "countryMY"),

    # ── 印地语/印度 ──
    "india": ("English", "en", "lang_en", "countryIN"),

    # ── 英语国家（保留英文搜索，但限制国家） ──
    "united kingdom": ("English", "en", "lang_en", "countryGB"),
    "uk": ("English", "en", "lang_en", "countryGB"),
    "australia": ("English", "en", "lang_en", "countryAU"),
    "canada": ("English", "en", "lang_en", "countryCA"),
    "usa": ("English", "en", "lang_en", "countryUS"),
    "united states": ("English", "en", "lang_en", "countryUS"),
    "new zealand": ("English", "en", "lang_en", "countryNZ"),
    "ireland": ("English", "en", "lang_en", "countryIE"),
    "singapore": ("English", "en", "lang_en", "countrySG"),
    "philippines": ("English", "en", "lang_en", "countryPH"),
    "nigeria": ("English", "en", "lang_en", "countryNG"),
    "south africa": ("English", "en", "lang_en", "countryZA"),
    "kenya": ("English", "en", "lang_en", "countryKE"),
    "ghana": ("English", "en", "lang_en", "countryGH"),
    "ethiopia": ("English", "en", "lang_en", "countryET"),
    "tanzania": ("English", "en", "lang_en", "countryTZ"),
    "pakistan": ("English", "en", "lang_en", "countryPK"),
    "bangladesh": ("English", "en", "lang_en", "countryBD"),

    # ── 中文 ──
    "china": ("Chinese", "zh-CN", "lang_zh-CN", "countryCN"),
    "taiwan": ("Chinese", "zh-TW", "lang_zh-TW", "countryTW"),
    "hong kong": ("Chinese", "zh-TW", "lang_zh-TW", "countryHK"),
}


def get_language_info(country: str) -> Optional[Dict]:
    """
    根据国家名称获取语言信息

    Returns:
        {
            "language": "Spanish",      # 语言名称（英文）
            "hl": "es",                 # Google hl 参数
            "lr": "lang_es",            # Google lr 参数
            "cr": "countryES",          # Google cr 参数
            "gl": "es",                 # Google gl 参数（国家代码）
        }
    """
    key = country.strip().lower()
    info = _COUNTRY_LANG_MAP.get(key)

    if not info:
        # 尝试部分匹配
        for country_key, lang_info in _COUNTRY_LANG_MAP.items():
            if country_key in key or key in country_key:
                info = lang_info
                break

    if not info:
        return None

    language_name, hl_code, lr_code, cr_code = info
    # gl 从 cr 中提取（去掉 "country" 前缀，转为小写）
    gl_code = cr_code.replace("country", "").lower()

    return {
        "language": language_name,
        "hl": hl_code,
        "lr": lr_code,
        "cr": cr_code,
        "gl": gl_code,
    }


def get_country_gl_code(country: str) -> str:
    """获取国家的 gl 代码（SerpAPI 地理位置参数）"""
    info = get_language_info(country)
    if info:
        return info["gl"]
    return ""


def get_all_mapped_countries() -> list:
    """获取所有已映射的国家名称列表（用于前端选择提示等）"""
    return sorted(set(k.title() for k in _COUNTRY_LANG_MAP.keys()))
