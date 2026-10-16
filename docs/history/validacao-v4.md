# Moldura v4 — refinamento conservador

15/10/2026. Interface reduzida, botões de gabarito, leitura mais confortável, ícones consistentes e correções de sessão. Não foram adicionados projetos, histórico de edição, serviços externos ou configurações de tamanho novas.

## Entrega visual

- Quatro botões de modelo, com o ativo em verde, sem menu suspenso.
- Cabeçalho compacto e exportação sempre acessível no topo.
- Frases decorativas e medidas repetidas removidas. Ajuda curta em janela própria.
- Prévia adaptável ao espaço da janela, campos numéricos preservados e identificação visual consistente dos ajustes.
- Marca de enquadramento e círculo aplicada à interface, favicon, bandeja e executável; família vetorial local para as ações.
- Cantos arredondados e paleta verde mantidos.
- Transições de cores/estados e entradas discretas de avisos/janelas. O enquadramento responde sem animação de atraso. Movimento reduzido do sistema é respeitado.
- Guias alternáveis, centralização independente e conferência ampliada das folhas.

## Correções

1. Falhas transitórias na prévia não removem fotos ou instruções de edição. É possível tentar novamente.
2. Uma aba edita por vez no mesmo perfil em navegadores com Web Locks. As demais consultam a sessão e podem solicitar transferência explícita. O fechamento de uma aba antiga não grava um estado obsoleto.
3. Botões de mover/remover são elementos nativos separados do botão de seleção; Enter/Espaço executam a ação correta.
4. Uma imagem de fonte carregada com atraso não pode sobrepor a prévia definitiva já calculada. A revisão definitiva tem precedência sobre a aproximação interativa.
5. Download é anunciado como iniciado; não se afirma que o navegador já salvou o arquivo no disco.

A coordenação de abas usa a API nativa documentada em [MDN — LockManager.request](https://developer.mozilla.org/en-US/docs/Web/API/LockManager/request). Não requer biblioteca nova. O teste foi realizado no Microsoft Edge deste Windows. A proteção entre perfis ou navegadores distintos não representa colaboração entre usuários.

## Preservação e evidências

O arquivo `engine.py` foi comparado byte a byte com a cópia da v3 em `tests/artifacts/baseline-v3.zip`: idêntico. As dimensões, máscaras, sangria, reflexos, layout, cores e parâmetros de JPG continuam no mesmo motor.

Os 20 testes de processamento, API e Windows permanecem no conjunto de validação. Os testes de navegador cobrem também:

- Os quatro modelos e seus estados de seleção.
- Igualdade dos pixels da prévia definitiva com o processamento de Pillow.
- JPG único, múltiplos JPGs em ZIP e as saídas P de seis e sete fotos.
- 1795 × 1205 pixels e 300 × 300 DPI.
- Precisão numérica, rotação, enquadramento e recuperação do modelo.
- Falha 503 simulada na prévia, seguida de recuperação sem perda de fotos.
- Remoção por Enter e reordenação por Espaço.
- Aba secundária somente consulta, transferência, sincronização e fechamento da aba anterior.
- Guias, centralização sem alterar zoom/cores, ajuda e conferência ampliada.
- Ausência de transbordamento horizontal em 740, 600, 390 e 320 px.
- Desativação das animações com preferência por movimento reduzido.

Em 1366 × 768, a prévia medida passou de 330 para 365 px de lado e ficou inteira na tela, terminando aproximadamente em y=628. A ação de exportação termina em y=62. A captura de referência está em `tests/artifacts/v4-desktop-1366.png`.

O teste de distribuição (`tests/packaged_check.py`) executa os três testes de navegador contra o EXE e verifica janela nativa da bandeja, segunda execução reutilizando o mesmo servidor, encerramento e remoção dos metadados de execução.

## Limites

Os testes usam imagens sintéticas; não foi realizada impressão física. A escala do papel continua dependendo da impressão a 100%. A sessão ainda é temporária e exige exportação antes de encerrar o processo ou desligar o computador. Projetos em disco e desfazer/refazer continuam fora desta versão.
