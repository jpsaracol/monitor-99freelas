# Monitor 99Freelas

Avisa no WhatsApp quando aparece projeto de desenvolvimento web no 99Freelas que combina com você e ainda tem pouca concorrência. Roda no GitHub Actions a cada 15 minutos, então o computador pode ficar desligado.

Ele lê só as páginas públicas, sem login, e **nunca envia proposta**. Quem decide é você.

## Que avisos chegam

- **🔔 Projeto novo:** combina com as palavras-chave, foi publicado há menos de 12h, tem até 20 propostas e já aceita o plano grátis.
- **🔓 Exclusivo que abriu:** quase todo projeto nasce exclusivo para assinantes (~24h). O monitor guarda os que combinam e avisa assim que liberam pro plano grátis, se tiverem até 50 propostas.

Os filtros ficam em `config.json`. Para mudar, edite o arquivo e faça o commit.

## Configurar o WhatsApp (CallMeBot, grátis, só pro seu número)

1. Siga https://www.callmebot.com/blog/free-api-whatsapp-messages/: salve o número do bot e mande `I allow callmebot to send me messages`.
2. Você recebe uma **apikey** no WhatsApp.
3. No GitHub, abra o repositório e vá em **Settings → Secrets and variables → Actions → New repository secret**. Crie:
   - `CALLMEBOT_PHONE`: seu número com DDI, ex.: `+5553999999999`
   - `CALLMEBOT_APIKEY`: a chave recebida
4. Em **Actions → Monitor 99Freelas → Run workflow**, rode uma vez. Deve chegar "✅ Monitor do 99Freelas ligado".

## Testar no computador

```bash
python3 monitor.py --teste   # mostra as mensagens no terminal, não envia nem salva nada
```
