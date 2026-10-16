# Validação da Moldura v5 — 15/10/2026

Mudanças restritas ao download da folha ampliada e à seleção de fotos por ↑/↓ na lista. Layout, paleta, ícones existentes, motor de imagem e medidas dos quatro modelos preservados. O botão de download usa o mesmo motor da exportação geral, com o modelo e os ajustes da prévia exibida. Durante o recálculo, a folha aguarda a nova prévia antes de permitir sua abertura.

- 20 testes automatizados de API, composição, dimensões, sangria, reflexos, JPG e integração desktop: aprovados.
- Quatro verificações de navegador executadas contra o próprio `dist/Moldura-v5.exe`, no Microsoft Edge: aprovadas, sem erros de JavaScript.
- Download individual da folha 2 quadrada: número correto no nome, fotos corretas, 1795 × 1205 px, 300 DPI, sRGB incorporado e cor 4:4:4.
- Download da última folha incompleta do Redondo P: somente a foto correspondente, centralizada, com o mesmo tamanho final e DPI.
- ↑/↓: seleção anterior/seguinte, limites sem dar a volta, rolagem acompanhando a seleção e ordem das fotos preservada. Setas do enquadramento e campos numéricos preservadas.
- Regressão: quatro modelos, exportação JPG/ZIP, recuperação de sessão, transferência entre abas, falhas temporárias, guias, centralização, telas de 320 a 1366 px e preferência por movimento reduzido.
- Executável: bandeja nativa encontrada, segunda abertura reutiliza a execução e encerramento autenticado remove os metadados da instância de teste.

Executável: 17.812.990 bytes. SHA-256: `6872C80BDB71FFAC14FD9C4164FDB75ADC0640A70CBF294C08564F7413B1992A`.

Testes de navegador usam fotos sintéticas. As versões anteriores e as sessões do usuário foram preservadas. A escala física final continua dependendo da impressão em tamanho real / 100%.
