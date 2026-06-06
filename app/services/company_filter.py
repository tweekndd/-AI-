"""
公司结果过滤服务（V2.0）
自动过滤社交媒体、招聘、新闻、政府、教育等非企业官网
V2.1 更新：补充西语国家域名后缀和常见非企业站点，降低无效Token消耗
"""
import re
from typing import List, Dict
from urllib.parse import urlparse


# 需要过滤的完整域名黑名单（精确匹配域名主体）
BLACKLIST_DOMAINS_EXACT = {
    # ── 社交媒体 ──
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com",
    "x.com", "youtube.com", "tiktok.com", "pinterest.com",
    "snapchat.com", "reddit.com", "medium.com", "tumblr.com",
    "flickr.com", "vimeo.com", "telegram.org", "whatsapp.com",
    # ── 百科 ──
    "wikipedia.org", "wikidata.org", "wikimedia.org",
    # ── 招聘网站（英语） ──
    "indeed.com", "monster.com", "glassdoor.com", "careerbuilder.com",
    "ziprecruiter.com", "simplyhired.com", "dice.com",
    "upwork.com", "freelancer.com", "fiverr.com",
    # ── 招聘网站（西语） ──
    "infojobs.net", "infojobs.com", "computrabajo.com", "trabajo.org",
    "tecnoempleo.com", "empleo.com", "empleosit.com", "empleate.com",
    "bumeran.com", "zonajobs.com", "occ.com.mx", "occ mundial",
    "trabajando.cl", "trabajando.pe", "trabajando.com",
    "laborum.cl", "laborum.pe", "laborum.com",
    # ── 新闻网站（英语） ──
    "cnn.com", "bbc.com", "bbc.co.uk", "reuters.com", "bloomberg.com",
    "forbes.com", "businesswire.com", "prnewswire.com",
    "globenewswire.com", "newsweek.com", "theguardian.com",
    "nytimes.com", "wsj.com", "economist.com", "apnews.com",
    "usatoday.com", "latimes.com", "washingtonpost.com",
    # ── 新闻网站（西语） ──
    "elmundo.es", "elpais.com", "abc.es", "lavanguardia.com",
    "elmundo.com", "expansion.com", "eleconomista.es",
    "eleconomista.com.mx", "eltiempo.com", "eltiempo.es",
    "larepublica.pe", "larepublica.co", "elcomercio.pe",
    "elcomercio.com", "clarin.com", "lanacion.com.ar",
    "lanacion.com", "infobae.com", "cronista.com",
    "ambito.com", "perfil.com", "diariocorreo.pe",
    "eluniversal.com.mx", "eluniversal.com.co",
    "milenio.com", "excelsior.com.mx", "jornada.com.mx",
    "elmexicano.com", "debate.com.mx", "sdpnoticias.com",
    "aristeguinoticias.com", "proceso.com.mx",
    "emol.com", "latercera.com", "cooperativa.cl",
    "publimetro.cl", "publimetro.com.mx", "publimetro.pe",
    "noticias.uol.com.br", "folha.uol.com.br", "estadao.com.br",
    "globo.com", "g1.globo.com", "uol.com.br",
    "terra.com.br", "terra.com", "rpp.pe",
    # ── 政府域名（含西语） ──
    "usa.gov", "gov.uk", "gob.mx", "gob.ar", "gob.cl", "gob.pe",
    "gob.ec", "gob.bo", "gob.py", "gob.uy", "gob.co", "gob.do",
    "gob.hn", "gob.sv", "gob.gt", "gob.pa", "gob.cr",
}

# 西语新闻门户关键词（域名片段中包含这些词也过滤）
SPANISH_NEWS_KEYWORDS = {
    "noticias", "prensa", "diario", "periodico", "informacion",
    "reporte", "nuevodiario", "tiempo", "cronic", "opinion",
}


def _extract_domain(url: str) -> str:
    """从URL中提取纯域名（不含www）"""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url.lower()


def is_blacklisted(url: str) -> bool:
    """判断URL是否属于应过滤的黑名单"""
    if not url:
        return True

    domain = _extract_domain(url)
    if not domain:
        return True

    # ─── 1. 精确匹配完整域名 ───
    if domain in BLACKLIST_DOMAINS_EXACT:
        return True

    # ─── 2. 政府域名后缀过滤（兼容西语）.gob / .gob.ar / .gob.mx ───
    if domain.endswith(".gob"):
        return True
    if re.search(r'\.gob\.[a-z]{2,}$', domain):
        return True
    # .gov / .gov.ar / .gov.mx
    if domain.endswith(".gov"):
        return True
    if re.search(r'\.gov\.[a-z]{2,}$', domain):
        return True
    # .govt
    if domain.endswith(".govt"):
        return True

    # ─── 3. 教育域名后缀过滤 ───
    # .edu / .edu.ar / .edu.mx / .edu.pe
    if domain.endswith(".edu"):
        return True
    if re.search(r'\.edu\.[a-z]{2,}$', domain):
        return True
    # .ac.uk / .ac.kr 等学术域名
    if re.search(r'\.ac\.[a-z]{2,}$', domain):
        return True

    # ─── 4. 域名关键词段匹配 ───
    parts = domain.split(".")

    for part in parts:
        # 跳过通用顶级域和常见国家代码
        if part in {
            "com", "org", "net", "co", "uk", "au", "de", "fr", "jp",
            "cn", "gov", "edu", "ac", "io", "www",
            "br", "mx", "ar", "cl", "pe", "co", "ec", "bo", "py",
            "uy", "ve", "cr", "pa", "gt", "hn", "sv", "do", "cu",
            "es", "pt", "it", "nl", "be", "ch", "at", "se", "no",
            "dk", "fi", "pl", "cz", "hu", "ro", "bg", "gr", "tr",
            "ru", "in", "id", "my", "th", "vn", "ph", "sg",
            "za", "ng", "ke", "eg", "ma", "tn",
            "au", "nz",
        }:
            continue

        # 社交媒体/百科
        if part in {
            "wikipedia", "linkedin", "facebook", "instagram",
            "twitter", "youtube", "tiktok", "reddit", "pinterest",
        }:
            return True

        # 西语新闻门户
        if part in SPANISH_NEWS_KEYWORDS:
            return True

        # 大学（西语常见词）
        if part in {
            "universidad", "universidade", "universitate",
            "university", "universitas", "universitycollege",
            "facultad", "faculdade", "instituto", "institut",
            "college", "school", "campus",
        }:
            return True

    # ─── 5. 已知非企业域名 ───
    # 黄页/目录（英+西）
    if domain in {
        "yellowpages.com", "yell.com", "manta.com", "thomasnet.com",
        "alibaba.com", "made-in-china.com", "tradekey.com", "ec21.com",
        "ecplaza.net", "exportersindia.com", "tradesparq.com",
        "industryweek.com", "kompass.com", "kompass.es",
        "paginasamarillas.es", "paginasamarillas.com",
        "paginasamarillas.com.mx", "paginasamarillas.cl",
        "seccionamarilla.com.mx", "seccionamarilla.com",
        "guiaempresas.com", "guiaempresarial.com",
        "directoriodeempresas.com", "directoriocomercial.com",
        "infoempresa.com", "empresas.com", "todoproductos.com",
        "tupunto.com", "negocios.com", "comercio.com",
        "jobsite.com", "jobs.com", "careers.com",
        "monster.com", "indeed.com", "biz.com",
        "mercadolibre.com", "mercadolibre.com.ar",
        "mercadolibre.com.mx", "mercadolibre.cl",
        "mercadolibre.pe", "mercadolibre.co",
        "linio.com", "amazon.com", "amazon.es",
    }:
        return True

    return False


def filter_search_results(results: List[Dict]) -> List[Dict]:
    """
    过滤搜索结果，只保留企业官网
    """
    filtered = []
    for result in results:
        website = result.get("website", "")
        if not website:
            continue
        if is_blacklisted(website):
            continue
        filtered.append(result)

    return filtered
