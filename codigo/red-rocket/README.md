# Red Rocket — Sanctuary

Mapa de exploração em primeira pessoa, inspirado no primeiro posto Red Rocket de Fallout 4. Modelo autoral no Blender e materiais fotográficos CC0 de Poly Haven e ambientCG. As partes não visíveis na referência foram estimadas; não é um modelo ou texturas extraídos do jogo original.

## Abrir o ZIP jogável

Extraia o ZIP e abra `index.html` no Chrome, Edge ou Firefox atualizado. O documento contém modelo, texturas e bibliotecas: funciona offline, sem servidor ou instalador. O primeiro carregamento depende da velocidade do computador.

WASD para caminhar, Shift para correr, mouse ou setas para olhar e Esc para pausar. F3 mostra informações de desempenho. Use **Leve** em computadores mais lentos. Ele simplifica a iluminação e reduz a resolução; no teste por software passou de 7,7 para 19,5 FPS. Isso não representa uma medição em GPU física. **Detalhado** acrescenta mapas de rugosidade e relevo.

## Código de desenvolvimento

Nesta pasta, o `index.html` modular exige um servidor estático. Execute `python3 -m http.server 8000` dentro de `red-rocket` e abra `http://localhost:8000`. Para gerar novamente o HTML offline: `python3 scripts/build_portable.py`.

A fonte nativa fica em `design/red-rocket/layout-study.blend` na raiz do pacote de fontes. Para reconstruir o modelo: `blender -b -t 4 --python-exit-code 1 --python blender/red_rocket_function_study.py`. A exportação está em `blender/export_red_rocket.py` e exige autorização vinculada ao hash da fonte e as auditorias aprovadas dessa mesma fonte.

Verificações e capturas do aplicativo carregado: `design/red-rocket/runtime/`. As imagens da pasta `renders` são estudos de autoria no Blender. O mapa anterior Oficina do Vale e o seu ZIP foram preservados separadamente.

As fontes tipográficas necessárias à receita acompanham `design/red-rocket/fonts/`, com suas licenças. Se o Blender não encontrar as fontes no seu sistema ao abrir o arquivo nativo, use Arquivo → Dados externos → Localizar arquivos ausentes e selecione essa pasta.

Licenças dos materiais: `design/red-rocket/materials/sources.json`. Biblioteca Three.js sob licença MIT: `vendor/LICENSE-three.txt`. Recriação de fã sem vínculo com Bethesda.
