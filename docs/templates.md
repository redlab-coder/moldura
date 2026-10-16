# Gabaritos e impressão

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

## Quadrado e dimensões em pixels

- Foto central: **5 × 5 cm**, 591 × 591 px.
- Composição com bordas refletidas nas quatro laterais e nos cantos: **7 × 7 cm**, 827 × 827 px. Borda de 118 px por lado, aproximadamente 1 cm.
- Folha horizontal: **15,2 × 10,2 cm**, **1795 × 1205 px**, **300 DPI** gravados no JPG.
- Duas fotos: margens laterais e distância entre fotos de aproximadamente 0,4 cm; margens superior e inferior de aproximadamente 1,6 cm. A quantização em pixels causa no máximo 1 px de diferença nas margens.
- Uma foto: centralizada nos dois eixos. Quantidades ímpares deixam a última folha com uma foto centralizada.
- JPG: qualidade 100, sem subamostragem de cor (4:4:4), perfil sRGB incorporado. JPG é um formato com perdas mesmo na qualidade máxima.

As dimensões em centímetros não resultam em números inteiros de pixels a 300 DPI. Usa-se o inteiro mais próximo; 1795 × 1205 px equivalem a aproximadamente 15,198 × 10,202 cm. Essa diferença é inferior a 0,03 mm.

**Impressão:** escolha papel 10,2 × 15,2 cm, orientação horizontal e tamanho real / escala 100%. Desative ajustes automáticos de enquadramento e expansão de impressão sem borda quando o driver permitir. As configurações da impressora podem alterar a escala física.

[← Documentação](README.md) · [Moldura](../README.md)
