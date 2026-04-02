# js/ — Módulos JavaScript do Atlas Kyokushin

Cada arquivo é um módulo lógico extraído de `index.html`. Todos compartilham o
namespace global (sem ES modules) para compatibilidade com o deploy de arquivo único.

## Ordem de carregamento (depende de globals anteriores)
1. `data.js`         → NT, BS, NODES, TECHS, KATA, RENRAKU, BELT_REQ, NMAP, NODE_DEGREE
2. `constellation.js`→ usa NODES, TECHS, NMAP, NT, BS, NODE_DEGREE, cvMandalMode
3. `navigation.js`   → usa TECHS, NODES, NMAP, NT, BS, SIM_NODES
4. `dict.js`         → usa NODES, NMAP
5. `kata.js`         → usa KATA, TECHS, BS, findAndShowTech→showTechDetail
6. `ido.js`          → usa RENRAKU, BELT_REQ, BS
7. `construtor.js`   → usa TECHS, NODES, NMAP, NT, ELISION_RULES
8. `math.js`         → usa TECHS, NODES, NMAP
9. `grammar.js`      → usa TECHS, NODES, NMAP, NT, BS, ELISION_RULES
10. `main.js`        → inicializa tudo, switchTab, speak(), initAutoDemo(), setMandalMode()

## Convenções
- Funções públicas: camelCase global (ex: `renderKata`, `initConstellation`)
- Constantes: UPPER_CASE global (ex: `TECHS`, `NMAP`)
- Flags de estado: camelCase com prefixo de escopo (`cvMode`, `cvMandalMode`)
