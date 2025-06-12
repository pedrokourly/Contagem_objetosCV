    # 💡 Aula Prática: Contagem de Objetos com OpenCV

Esta atividade prática tem como objetivo aplicar técnicas de Processamento Digital de Imagens para **contar automaticamente objetos (moedas)** em uma imagem utilizando Python e a biblioteca OpenCV.

## 📌 Objetivo

Desenvolver uma aplicação capaz de:
- Realizar o pré-processamento da imagem (conversão em tons de cinza, binarização, morfologia).
- Detectar contornos dos objetos.
- Contar e exibir visualmente os objetos detectados na imagem original.

## 🛠️ Tecnologias Utilizadas

- Python 3
- OpenCV
- Google Colab (para visualização com `cv2_imshow`)

## 📸 Etapas do Código

1. **Leitura e conversão para escala de cinza**
2. **Binarização com Otsu**
3. **Remoção de ruídos com morfologia matemática**
4. **Inversão da imagem (moedas ficam brancas)**
5. **Detecção e filtragem de contornos**
6. **Desenho dos contornos e contagem de objetos**

## ▶️ Como Executar

1. Importe ou carregue uma imagem chamada `moedas.jpg` no seu ambiente Colab.
2. Execute o código passo a passo.
3. Verifique a saída visual (máscara + imagem com contornos).
4. O número de objetos detectados será impresso no console.

## 📝 Observações

- A contagem funciona melhor com moedas **separadas**.
- Para moedas **amontoadas**, considere estudar o uso do algoritmo **Watershed** para segmentação.

## 📂 Estrutura do Projeto

