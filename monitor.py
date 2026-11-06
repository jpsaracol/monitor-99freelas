"""Monitor do 99Freelas: avisa no WhatsApp quando aparece projeto bom e com pouca concorrência.

Lê só as páginas públicas (sem login), não envia proposta nenhuma.
Uso:
    python3 monitor.py            # roda uma vez e notifica (precisa das variáveis do CallMeBot)
    python3 monitor.py --teste    # só mostra no terminal o que seria enviado, sem salvar estado
"""

import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://www.99freelas.com.br"
LISTA = BASE + "/projects?categoria=web-mobile-e-software&order=mais-recentes&page={}"
PASTA = Path(__file__).resolve().parent
CONFIG = json.loads((PASTA / "config.json").read_text(encoding="utf-8"))
ESTADO = PASTA / "seen.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) monitor-99freelas/1.0"
DIAS_GUARDAR = 7


# ---------- coleta ----------

def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def tempo_em_segundos(texto):
    """'1d02h15m30s' ou '15h53m32s' -> segundos."""
    total = 0
    for valor, unidade in re.findall(r"(\d+)\s*([dhms])", texto):
        total += int(valor) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[unidade]
    return total


def ler_lista(pagina_html, agora):
    projetos = []
    blocos = re.split(r'<li class="[^"]*\bresult-item\b', pagina_html)[1:]
    for b in blocos:
        pid = re.search(r'data-id="(\d+)"', b)
        link = re.search(r'<h1 class="title">.*?<a href="([^"?]+)', b, re.S)
        titulo = re.search(r'data-nome="([^"]*)"', b)
        pub = re.search(r'Publicado:.*?cp-datetime="(\d+)"', b, re.S)
        prop = re.search(r"Propostas:\s*<b>(\d+)", b)
        if not (pid and link and titulo and pub and prop):
            continue
        desc = re.search(r'data-content="([^"]*)"', b)
        descricao = html.unescape(desc.group(1)) if desc else ""
        descricao = re.sub(r"<[^>]+>", " ", descricao)
        excl = re.search(r"Projeto Exclusivo\. Ficar[^\"]*? em ([0-9dhms]+)", html.unescape(b))
        projetos.append({
            "id": pid.group(1),
            "titulo": html.unescape(titulo.group(1)).strip(),
            "url": BASE + link.group(1),
            "publicado": int(pub.group(1)) // 1000,
            "propostas": int(prop.group(1)),
            "descricao": descricao,
            "abre_em": agora + tempo_em_segundos(excl.group(1)) if excl else None,
        })
    return projetos


def propostas_atuais(url):
    texto = re.sub(r"<[^>]+>", " ", baixar(url))
    m = re.search(r"Propostas:\s*(\d+)", texto)
    return int(m.group(1)) if m else None


# ---------- filtro ----------

def normalizar(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " " + re.sub(r"[^a-z0-9#.+]+", " ", sem_acento.lower()) + " "


def tem_termo(texto_norm, termos):
    return [t for t in termos if f" {normalizar(t).strip()} " in texto_norm]


def interessa(p):
    titulo = normalizar(p["titulo"])
    if tem_termo(titulo, CONFIG["excluir_no_titulo"]):
        return False
    return bool(tem_termo(titulo + normalizar(p["descricao"]), CONFIG["palavras_chave"]))


# ---------- envio (Telegram ou WhatsApp) ----------
# As mensagens são montadas em HTML simples (<b>), que o Telegram entende.
# Para o WhatsApp, <b> vira *negrito*.

def enviar_telegram(texto, token, chat_id):
    dados = urllib.parse.urlencode({"chat_id": chat_id, "text": texto, "parse_mode": "HTML",
                                    "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=dados)
    with urllib.request.urlopen(req, timeout=30) as r:
        if not json.loads(r.read()).get("ok"):
            print("Telegram recusou a mensagem.")
    time.sleep(1)


def enviar_whatsapp(texto, fone, chave):
    texto = html.unescape(texto.replace("<b>", "*").replace("</b>", "*"))
    url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode(
        {"phone": fone, "text": texto, "apikey": chave})
    resposta = baixar(url)
    if "error" in resposta.lower() and "queued" not in resposta.lower():
        print("CallMeBot respondeu com erro:", re.sub(r"<[^>]+>", " ", resposta)[:300])
    time.sleep(4)  # o CallMeBot recusa mensagens muito seguidas


def enviar(texto, teste):
    if teste:
        print("\n----- mensagem -----\n" + texto + "\n--------------------")
        return
    env = lambda k: os.environ.get(k, "").strip()
    if env("TELEGRAM_TOKEN") and env("TELEGRAM_CHAT_ID"):
        enviar_telegram(texto, env("TELEGRAM_TOKEN"), env("TELEGRAM_CHAT_ID"))
    elif env("CALLMEBOT_PHONE") and env("CALLMEBOT_APIKEY"):
        enviar_whatsapp(texto, env("CALLMEBOT_PHONE"), env("CALLMEBOT_APIKEY"))
    else:
        sys.exit("Configure TELEGRAM_TOKEN + TELEGRAM_CHAT_ID ou CALLMEBOT_PHONE + "
                 "CALLMEBOT_APIKEY (veja o README).")


def ha_quanto(segundos):
    minutos = max(0, int(segundos // 60))
    return f"{minutos} min" if minutos < 60 else f"{minutos // 60}h{minutos % 60:02d}"


def cartao(p, agora, prefixo=""):
    return (f"{prefixo}<b>{html.escape(p['titulo'])}</b>\n"
            f"📊 {p['propostas']} propostas · publicado há {ha_quanto(agora - p['publicado'])}\n"
            f"🔗 {p['url']}")


def enviar_lote(cabecalho, cartoes, teste):
    # até 4 projetos por mensagem para não estourar o tamanho da URL
    for i in range(0, len(cartoes), 4):
        enviar(cabecalho + "\n\n" + "\n\n".join(cartoes[i:i + 4]), teste)


# ---------- principal ----------

def main():
    teste = "--teste" in sys.argv
    agora = int(time.time())
    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    primeira_vez = not estado

    projetos = []
    for pg in range(1, CONFIG["paginas_por_rodada"] + 1):
        projetos += ler_lista(baixar(LISTA.format(pg)), agora)
        time.sleep(2)
    if not projetos:
        sys.exit("Nenhum projeto lido: o layout do 99Freelas pode ter mudado.")

    novos, exclusivos_vistos = [], 0
    for p in projetos:
        if p["id"] in estado:
            continue
        bom = (interessa(p)
               and agora - p["publicado"] <= CONFIG["max_horas_publicado"] * 3600
               and p["propostas"] <= CONFIG["max_propostas"])
        registro = {"visto": agora, "titulo": p["titulo"]}
        if bom and p["abre_em"]:
            if CONFIG["avisar_exclusivos_quando_abrirem"]:
                registro.update(aguardando=True, abre_em=p["abre_em"], url=p["url"],
                                publicado=p["publicado"])
                exclusivos_vistos += 1
        elif bom:
            novos.append(p)
        estado[p["id"]] = registro

    # exclusivos que já liberaram para o plano grátis
    abertos = []
    for pid, r in estado.items():
        if r.get("aguardando") and agora >= r["abre_em"]:
            r["aguardando"] = False
            n = propostas_atuais(r["url"])
            if n is not None and n <= CONFIG["max_propostas_exclusivo_ao_abrir"]:
                abertos.append({**r, "propostas": n})
            time.sleep(2)

    if primeira_vez:
        enviar("✅ Monitor do 99Freelas ligado. A partir de agora aviso aqui "
               "quando aparecer projeto que combina com você.", teste)
    if novos:
        enviar_lote(f"🔔 <b>99Freelas: {len(novos)} projeto(s) novo(s)</b>",
                    [cartao(p, agora) for p in novos], teste)
    if abertos:
        enviar_lote("🔓 <b>Exclusivos que acabaram de abrir pro plano grátis</b>",
                    [cartao(p, agora) for p in abertos], teste)

    # limpa o que é velho
    limite = agora - DIAS_GUARDAR * 86400
    estado = {k: v for k, v in estado.items() if v["visto"] >= limite or v.get("aguardando")}
    if not teste:
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1))

    print(f"{len(projetos)} lidos · {len(novos)} novos avisados · "
          f"{exclusivos_vistos} exclusivos na fila · {len(abertos)} exclusivos abertos avisados")


if __name__ == "__main__":
    main()
