# Moldura

Estúdio local de impressão: enquadramento manual, zoom, rotação, brilho, contraste, saturação e nitidez. Nenhuma foto é enviada à internet. Os arquivos originais não são modificados.

## Abrir

Abra **Moldura-v7.exe** na pasta `dist`. A interface abre no navegador padrão e um ícone de foto aparece na bandeja do Windows, ao lado do relógio (pode ficar dentro da seta de ícones ocultos). Não precisa instalar Python, conectar uma conta ou ter internet.

Clique no ícone para abrir a interface. Com o botão direito, escolha **Abrir Moldura** ou **Encerrar Moldura**. Abrir o executável novamente reutiliza o mesmo processo e a mesma porta. O serviço escuta apenas em `127.0.0.1`: outros computadores da rede não têm acesso. As versões anteriores foram preservadas. Exporte sua sessão antiga antes de encerrá-la e passe a usar Moldura-v7.exe. A bandeja identifica esta versão como Moldura v7.

1. Clique em **Adicionar fotos** ou arraste arquivos para a área indicada.
2. Selecione uma foto na coluna esquerda. Arraste a imagem na prévia para enquadrar, use o zoom e ajuste as cores. O contorno pontilhado delimita a área visível do modelo escolhido. **Guias** mostra/oculta as marcações; **Centralizar** reposiciona sem alterar zoom ou cores. O botão **?** reúne as orientações de uso. Clique na prévia e use as setas para mover um pixel da imagem original; Shift + seta move dez pixels.
3. Digite o valor exato no campo ao lado de cada ajuste. Brilho, contraste e saturação vão de -100 a +100; nitidez de -100 a +200; zoom de 1,00 a 5,00. O botão **↺** zera somente aquele ajuste (zoom retorna a 1,00). As setas do teclado no campo numérico fazem ajustes de uma unidade. Durante o movimento, uma prévia rápida acompanha sua mão; ao soltar, a prévia final é calculada pelo mesmo processamento usado na exportação.
4. Confira as folhas abaixo; clique em uma para ampliar. O ícone de download ao lado de fechar baixa somente essa folha, em JPG na resolução final a 300 DPI. Clique em uma foto ou no espaço da lista e use ↑/↓ para selecionar a anterior/seguinte; a seleção acompanha a rolagem. Os pequenos botões de seta de cada linha continuam alterando a ordem das fotos nas folhas.
5. Clique em **Exportar** no topo da interface. Uma folha baixa como JPG; várias folhas baixam juntas em ZIP, contendo os JPGs individuais. O navegador salva na pasta de downloads ou pergunta onde salvar, conforme suas configurações.
6. Você pode fechar ou recarregar a aba e reabrir pelo ícone, usando o mesmo navegador/perfil: fotos, ajustes e ordem retornam enquanto o Moldura continuar ativo na bandeja. Os ajustes e identificadores da sessão ficam no armazenamento local do navegador; os arquivos completos ficam em uma área temporária local, removida ao excluir as fotos ou encerrar normalmente o aplicativo. Exporte antes de **Encerrar Moldura**, desligar ou reiniciar o computador. Essa recuperação não substitui um arquivo de projeto e não funciona em outro navegador/perfil. Somente uma aba edita a sessão por vez em navegadores compatíveis com Web Locks, como o Edge testado. Outra aba mostra a sessão para consulta; clique em **Usar nesta aba** para transferir a edição. A aba anterior passa a somente consulta e não sobrescreve os ajustes ao fechar.

## Modelos e organização das folhas

Escolha o modelo nos quatro botões acima do editor. O selecionado fica verde. O modelo escolhido se aplica a todas as fotos do lote; as folhas não misturam tamanhos. Ao trocar o modelo, o zoom, o enquadramento e os ajustes atuais são reaproveitados, e a prévia é recalculada.

Todas as medidas abaixo são em centímetros; nos redondos, são diâmetros.

| Modelo | Área visível | Corte total | Área segura | Por folha |
|---|---|---|---|---:|
| Button Quadrado | 5 × 5 | 7 × 7 | Foto central | 2 |
| Button Redondo G | Ø 5,8 | Ø 7,05 | Ø 4,8 a 5 | 2 |
| Button Redondo M | Ø 4,4 | Ø 5,5 | Ø 3,6 a 3,8 | 2 |
| Button Redondo P | Ø 3,2 | Ø 4,5 | Ø 2,6 a 2,8 | 6 (3 × 2) |

Nos redondos, o círculo externo é o corte total; o guia amarelo marca a área visível, e o verde marca o menor diâmetro da faixa segura, para manter rostos e textos mais centralizados. Os guias aparecem somente no editor e não são impressos. A arte circular fica sobre o branco da folha, com borda suavizada.

O zoom e o arraste enquadram a área visível. Na sangria dos redondos (0,625 cm por lado no G, 0,55 cm no M e 0,65 cm no P), o programa usa a continuação da própria foto, refletindo as bordas da imagem original somente onde faltam pixels. No quadrado, permanece a extensão espelhada de 1 cm por lado.

As folhas têm 15,2 × 10,2 cm, na horizontal. P usa até três colunas e duas linhas, com espaços iguais dentro de cada eixo. Nas folhas incompletas, cada linha fica centralizada; quando há somente uma linha, ela também é centralizada verticalmente. Uma foto fica centralizada nos dois eixos.

JPG único quando o lote cabe em uma folha; ZIP com JPGs quando precisa de mais folhas. Exemplos: 6 fotos P geram um JPG; 7 fotos P geram dois JPGs em ZIP. A seleção do modelo é recuperada com a sessão no mesmo navegador/perfil.

Os diâmetros de corte arredondados a 300 DPI são: G 833 px, M 650 px, P 531 px. Os diâmetros visíveis são, respectivamente, 685, 520 e 378 px. A quantização é sempre para o pixel inteiro mais próximo.

## Gabarito quadrado

- Foto central: **5 × 5 cm**, 591 × 591 px.
- Composição com bordas refletidas nas quatro laterais e nos cantos: **7 × 7 cm**, 827 × 827 px. Borda de 118 px por lado, aproximadamente 1 cm.
- Folha horizontal: **15,2 × 10,2 cm**, **1795 × 1205 px**, **300 DPI** gravados no JPG.
- Duas fotos: margens laterais e distância entre fotos de aproximadamente 0,4 cm; margens superior e inferior de aproximadamente 1,6 cm. A quantização em pixels causa no máximo 1 px de diferença nas margens.
- Uma foto: centralizada nos dois eixos. Quantidades ímpares deixam a última folha com uma foto centralizada.
- JPG: qualidade 100, sem subamostragem de cor (4:4:4), perfil sRGB incorporado. JPG é um formato com perdas mesmo na qualidade máxima.

As dimensões em centímetros não resultam em números inteiros de pixels a 300 DPI. Usa-se o inteiro mais próximo; 1795 × 1205 px equivalem a aproximadamente 15,198 × 10,202 cm. Essa diferença é inferior a 0,03 mm.

**Impressão:** escolha papel 10,2 × 15,2 cm, orientação horizontal e tamanho real / escala 100%. Desative ajustes automáticos de enquadramento e expansão de impressão sem borda quando o driver permitir. As configurações da impressora podem alterar a escala física.

Aceita JPG, PNG, WebP, BMP e TIFF (primeira página). Transparência é composta sobre branco; a orientação EXIF é corrigida. Perfis ICC válidos são convertidos a sRGB. Arquivos de até 50 MB e 60 megapixels; o lote aceita até 100 fotos e 4 GB de arquivos originais em armazenamento temporário. O cache de imagens decodificadas é limitado a 160 MiB; isso não inclui a memória transitória necessária para processar uma foto e compor a folha. É necessário espaço livre no disco temporário. HEIC e RAW devem ser convertidos antes.

## Código-fonte e validação

Com Python 3.11 ou posterior:

```powershell
python -m pip install -r requirements.txt
python app.py
python -m unittest discover -s tests -v
```

Para reconstruir o executável, instale PyInstaller e execute nesta pasta:

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Moldura-v7 --icon assets/moldura-v4.ico --add-data "ui;ui" --exclude-module numpy --exclude-module psutil --exclude-module charset_normalizer app.py
```

O serviço escuta somente em 127.0.0.1, usa porta livre automaticamente e valida Host, Origin e token da sessão. Um mutex do Windows impede instâncias duplicadas; `%LOCALAPPDATA%/Moldura-v7/runtime.json` guarda somente a URL, PID e identificador de execução para localizar a instância existente, e é removido ao encerrar. Não há recursos externos, telemetria, banco de dados ou serviço de nuvem.

Os testes de navegador estão em `tests/browser_check.py`; a validação do executável, janela nativa da bandeja, segunda abertura e encerramento está em `tests/packaged_check.py`. Esses dois scripts precisam de Playwright e Microsoft Edge instalados apenas na máquina de desenvolvimento. A distribuição não depende deles.


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
