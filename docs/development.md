# Desenvolvimento

O Moldura usa Python, Pillow e uma interface local em HTML, CSS e JavaScript. O navegador se conecta apenas ao servidor em `127.0.0.1`.

## Executar

Com Python 3.11 ou posterior, na raiz do projeto:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

A compilação oficial usa Python 3.14 no Windows. Não é necessário instalar ferramentas de desenvolvimento para usar o aplicativo distribuído.

## Estrutura

| Caminho | Responsabilidade |
|---|---|
| `app.py` | Servidor local e rotas da aplicação |
| `engine.py` | Medidas, enquadramento e composição para impressão |
| `photo_store.py` | Originais temporários e cache de imagens |
| `desktop.py` | Bandeja do Windows e instância única |
| `updater.py` | Download verificado e atualização ao encerrar |
| `version.py` | Versão do aplicativo e identidade da distribuição |
| `ui/` | Interface e ícones vetoriais |
| `assets/` | Recursos usados pelo aplicativo e instalador |
| `installer/` | Instalador por usuário para Windows |
| `scripts/` | Compilação e ferramentas de manutenção |
| `tests/` | Testes de processamento, API, interface e instalação |
| `docs/` | Guias, apresentação e registros anteriores |

Os módulos principais permanecem na raiz para preservar os caminhos de execução e compilação existentes.

## Testes

```powershell
python -m unittest discover -s tests -v
```

Para os testes de navegador, instale `playwright==1.59.0` e tenha o Microsoft Edge disponível. Depois de compilar:

```powershell
python tests/packaged_check.py dist/Moldura-v8.exe
python tests/installer_check.py
```

O teste de instalação usa uma pasta temporária e não prossegue se já existir uma instalação registrada do usuário. Os testes de navegador usam imagens de demonstração. Fotografias pessoais não devem entrar nos artefatos ou no Git.

## Compilar no Windows

```powershell
python -m pip install -r requirements-build.txt
./scripts/bootstrap_inno.ps1
python scripts/build_windows.py
```

O script prepara a versão portátil, o instalador, o manifesto de atualização e os checksums em `dist/`. Essa pasta, os arquivos de compilação e as ferramentas locais não são versionados.

## Funcionamento e memória

Os arquivos enviados são preservados integralmente em pastas temporárias locais. O editor usa fontes leves de até 1800 px e miniaturas de 128 px; o cache do navegador conserva até três fontes de edição. A prévia definitiva da foto e a exportação continuam usando o original completo. As prévias das folhas usam versões leves, e os JPGs finais usam os originais.

O cache do servidor tem orçamento de 160 MiB, com cotas separadas para originais e prévias. A decodificação e o processamento de originais são serializados para evitar picos multiplicados por várias solicitações simultâneas. Arquivos ZIP maiores que 8 MiB usam armazenamento temporário e envio em blocos. As pastas de cada foto acompanham suas referências: uma exportação iniciada continua válida mesmo se outra aba remover uma foto. A remoção normal limpa os arquivos quando a última operação termina. Encerramento forçado ou falta de energia podem deixar temporários no Windows; não há recuperação de projeto após reiniciar o aplicativo.

`tests/test_photo_store.py` cobre preservação dos bytes, cache limitado, separação entre original e prévia, imagens maiores que o cache e limpeza dos temporários. `tests/heavy_photo_browser_check.py URL foto1 foto2 foto3` testa 12 importações, memória, quadros durante arraste, exportação em zoom alto, todas as folhas e recuperação da aba; não grava fotos pessoais nos artefatos de teste. O script usa psutil somente no ambiente de desenvolvimento.

## Sessão local

O serviço escuta somente em 127.0.0.1, usa porta livre automaticamente e valida Host, Origin e token da sessão. Um mutex do Windows impede instâncias duplicadas; `%LOCALAPPDATA%/Moldura-Installed/runtime.json` (instalada) ou `%LOCALAPPDATA%/Moldura-v8/runtime.json` (portátil) guarda somente a URL, PID e identificador de execução para localizar a instância existente, e é removido ao encerrar. Não há telemetria, banco de dados ou envio de fotos à nuvem. A versão instalada consulta somente os arquivos de atualização do repositório oficial no GitHub, sem credenciais embutidas.

[← Documentação](README.md) · [Moldura](../README.md)
