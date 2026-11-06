# Monitor 99Freelas

Avisa no Telegram (ou no WhatsApp) quando aparece projeto de desenvolvimento web no 99Freelas que combina com você e ainda tem pouca concorrência. Roda no GitHub Actions a cada 15 minutos, então o computador pode ficar desligado.

Ele lê só as páginas públicas, sem login, e **nunca envia proposta**. Quem decide é você.

## Que avisos chegam

- **🔔 Projeto novo:** combina com as palavras-chave, foi publicado há menos de 12h, tem até 20 propostas e já aceita o plano grátis.
- **🔓 Exclusivo que abriu:** quase todo projeto nasce exclusivo para assinantes (~24h). O monitor guarda os que combinam e avisa assim que liberam pro plano grátis, se tiverem até 50 propostas.

Os filtros ficam em `config.json`. Para mudar, edite o arquivo e faça o commit.

## Onde ficam as chaves

Em **Settings → Secrets and variables → Actions** do repositório. Ninguém consegue ver o valor, nem com o repositório público.

| Canal | Secrets |
|---|---|
| Telegram (em uso) | `TELEGRAM_TOKEN` (do @BotFather), `TELEGRAM_CHAT_ID` |
| WhatsApp via CallMeBot | `CALLMEBOT_PHONE` (ex.: `+5553999999999`), `CALLMEBOT_APIKEY` |

Se os dois estiverem configurados, o Telegram tem prioridade. Para trocar pro WhatsApp quando o CallMeBot liberar vaga (https://www.callmebot.com/blog/free-api-whatsapp-messages/), crie os secrets do CallMeBot e apague os do Telegram.

Para rodar na hora, use **Actions → Monitor 99Freelas → Run workflow**.

## Testar no computador

```bash
python3 monitor.py --teste   # mostra as mensagens no terminal, não envia nem salva nada
```
