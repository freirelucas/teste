# Integração com IA — Tarot CiberQuilombola

## Visão geral

O Tarot CiberQuilombola funciona **100% offline** sem nenhuma API key. A integração com a Anthropic API é um bônus opcional que enriquece as interpretações.

## Como funciona

### Modo Local (padrão)
Quando o usuário clica em "Diagnóstico Local", o sistema gera uma interpretação estruturada usando os dados das cartas (`cards.json`):
- Pergunta diagnóstica de cada carta
- Sinal algedônico
- Citações de Beer e Bispo
- Epígrafe literária

### Modo API (opcional)
Quando o usuário fornece uma API key da Anthropic:
1. A key **nunca é armazenada** — só existe na memória durante a sessão
2. A requisição é feita diretamente do browser para `api.anthropic.com`
3. O modelo usado é `claude-sonnet-4-6-20250514`
4. Se a API falhar, o fallback local é usado automaticamente

## System Prompt

O system prompt instrui Claude a:
- **Nunca fazer previsões** — apenas diagnóstico sistêmico
- Usar linguagem concreta e cibernética
- Conectar cada carta ao conceito de Beer que representa
- Trazer o pensamento quilombola de Bispo como contraponto
- Apontar contradições e loops de feedback quebrados
- Terminar com uma pergunta diagnóstica

## Para desenvolvedores

Para testar com a API localmente:
```bash
echo "VITE_ANTHROPIC_API_KEY=sk-ant-..." > .env
npm run dev
```

A variável `VITE_ANTHROPIC_API_KEY` é acessada via `import.meta.env.VITE_ANTHROPIC_API_KEY`. Se estiver definida, o botão "Diagnóstico com IA" aparece pre-preenchido.

## CORS

A Anthropic API suporta chamadas diretas do browser com o header `anthropic-dangerous-direct-browser-access: true`. Isso é adequado para uso pessoal/demo, mas para produção com muitos usuários, considere um proxy backend.
