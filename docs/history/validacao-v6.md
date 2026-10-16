# Moldura v6 — 15/10/2026

Correção dos diâmetros de corte total: Redondo G 70,5 mm (833 px), M 55 mm (650 px), P 45 mm (531 px), a 300 DPI com arredondamento ao pixel mais próximo. Áreas visíveis/seguras e capacidades mantidas, assim como o Quadrado, o visual e as funções da v5.

As medidas são fornecidas pelo motor à interface: prévia, guias proporcionais, sangria e montagem da folha usam os novos valores. Folhas continuam em 1795 × 1205 px a 300 DPI, com perfil sRGB e JPG qualidade máxima.

Validação concluída:

- 20 testes de API, imagem, dimensões, composição e integração desktop aprovados. Incluem todas as quantidades parciais e completas dos redondos, sem sobreposição nem saída da folha.
- Quatro testes de navegador aprovados contra o próprio Moldura-v6.exe, no Microsoft Edge, sem erros de JavaScript.
- Conferência dos textos das novas medidas na interface e igualdade entre os pixels da prévia final e o processamento do servidor para todos os modelos.
- Exportação JPG/ZIP, download individual da folha, setas na lista, campos numéricos, enquadramento, recuperação/transferência de sessão, responsividade e movimento reduzido aprovados.
- Bandeja nativa, segunda abertura reutilizando a execução e encerramento com remoção dos metadados aprovados.

Testes usam imagens sintéticas. Versões anteriores preservadas. Executável entregue em `dist/Moldura-v6.exe` (17.813.512 bytes).
