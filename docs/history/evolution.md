# Evoluções anteriores

Registros de produto preservados da documentação original. O histórico de commits começa no snapshot da base v7.

## Refinamento da v4

Interface compacta, botões visíveis de gabarito, ícones vetoriais próprios, prévia adaptável e exportação no topo. Animações curtas em controles, avisos e janelas; o arraste não recebe atraso artificial. A preferência do sistema por movimento reduzido é respeitada.

Falhas temporárias da prévia não removem fotos da sessão; use **Tentar carregar a prévia** para repetir. Remover e reordenar funcionam também com Enter/Espaço. Uma prévia rápida atrasada não substitui a prévia definitiva. Os parâmetros de impressão e o motor de imagem são os mesmos da v3.

`tests/refinement_browser_check.py` cobre os cenários de recuperação, exclusividade/transferência entre abas, fechamento de aba antiga, teclado, guias, centralização, janelas de ajuda/conferência, posição do botão Exportar, telas de 320 a 1366 px e preferência por movimento reduzido. O teste do executável chama os quatro testes de navegador.

## Adições da v5

Somente duas funções novas: download individual na folha ampliada e navegação da lista por ↑/↓. O download usa o mesmo motor da exportação geral, preserva o modelo e os ajustes da folha exibida e mantém o número da folha no nome do arquivo. A seleção pelo teclado não altera a ordem e não interfere nas setas do enquadramento ou dos campos numéricos. O visual e os parâmetros de impressão da v4 foram preservados.

`tests/sheet_navigation_browser_check.py` verifica seleção e rolagem pelo teclado, limites da lista, preservação da ordem, independência dos campos/enquadramento, download individual com DPI, dimensões, perfil e amostragem de cor, folha incompleta do Redondo P e janela em tela estreita.

## Medidas da v6

Diâmetros de corte total atualizados: G 7,05 cm, M 5,5 cm e P 4,5 cm. Prévia, sangria, guias proporcionais e montagem das folhas usam essas medidas. Áreas visíveis/seguras, capacidades por folha, modelo Quadrado e funções da v5 mantidos.

## Otimização da v7

Os arquivos enviados são preservados integralmente em pastas temporárias locais. O editor usa fontes leves de até 1800 px e miniaturas de 128 px; o cache do navegador conserva até três fontes de edição. A prévia definitiva da foto e a exportação continuam usando o original completo. As prévias das folhas usam versões leves, e os JPGs finais usam os originais.

O cache do servidor tem orçamento de 160 MiB, com cotas separadas para originais e prévias. A decodificação e o processamento de originais são serializados para evitar picos multiplicados por várias solicitações simultâneas. Arquivos ZIP maiores que 8 MiB usam armazenamento temporário e envio em blocos. As pastas de cada foto acompanham suas referências: uma exportação iniciada continua válida mesmo se outra aba remover uma foto. A remoção normal limpa os arquivos quando a última operação termina. Encerramento forçado ou falta de energia podem deixar temporários no Windows; não há recuperação de projeto após reiniciar o aplicativo.

`tests/test_photo_store.py` cobre preservação dos bytes, cache limitado, separação entre original e prévia, imagens maiores que o cache e limpeza dos temporários. `tests/heavy_photo_browser_check.py URL foto1 foto2 foto3` testa 12 importações, memória, quadros durante arraste, exportação em zoom alto, todas as folhas e recuperação da aba; não grava fotos pessoais nos artefatos de teste. O script usa psutil somente no ambiente de desenvolvimento.

[← Registros anteriores](README.md)
