import cv2
import numpy as np

def preprocess_image(image_path):
    """
    Pré-processa a imagem para melhorar a segmentação
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Não foi possível carregar a imagem: {image_path}")
    
    # Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar blur gaussiano para reduzir ruído
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    return img, gray, blurred

def create_binary_mask(gray_image):
    """
    Cria uma máscara binária otimizada para detectar objetos claros E escuros
    """
    # Método 1: Otsu threshold para objetos escuros
    _, otsu_dark = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Método 2: Otsu threshold para objetos claros
    _, otsu_light = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Método 3: Threshold adaptativo para objetos escuros
    adaptive_dark = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY_INV, 11, 2)
    
    # Método 4: Threshold adaptativo para objetos claros
    adaptive_light = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
    
    # Detectar bordas para capturar objetos com contraste sutil
    edges = cv2.Canny(gray_image, 50, 150)
    edges_dilated = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)
    
    # Combinar todos os métodos
    combined = cv2.bitwise_or(otsu_dark, otsu_light)
    combined = cv2.bitwise_or(combined, adaptive_dark)
    combined = cv2.bitwise_or(combined, adaptive_light)
    combined = cv2.bitwise_or(combined, edges_dilated)
    
    return combined

def remove_noise(binary_image):
    """
    Remove ruído usando operações morfológicas otimizadas
    """
    # Kernels de tamanhos diferentes para objetos variados
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    kernel_medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
    kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (6, 6))
    
    # Primeira limpeza: remover ruído muito pequeno
    opened = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel_small, iterations=1)
    
    # Segunda limpeza: preencher pequenos buracos
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_medium, iterations=1)
    
    # Terceira limpeza: suavizar bordas maiores
    final = cv2.morphologyEx(closed, cv2.MORPH_CLOSE, kernel_large, iterations=1)
    
    return final

def watershed_segmentation(binary_image, original_image):
    """
    Aplica segmentação watershed para separar objetos sobrepostos
    """
    # Encontrar área de background definitiva
    kernel = np.ones((3, 3), np.uint8)
    sure_bg = cv2.dilate(binary_image, kernel, iterations=3)
    
    # Transformada de distância
    dist_transform = cv2.distanceTransform(binary_image, cv2.DIST_L2, 5)
    
    # Encontrar área de foreground definitiva (threshold mais baixo para capturar mais objetos)
    _, sure_fg = cv2.threshold(dist_transform, 0.3 * dist_transform.max(), 255, 0)
    sure_fg = np.uint8(sure_fg)
    
    # Encontrar região desconhecida
    unknown = cv2.subtract(sure_bg, sure_fg)
    
    # Rotular marcadores
    _, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 1
    markers[unknown == 255] = 0
    
    # Aplicar watershed
    markers = cv2.watershed(original_image, markers)
    
    return markers

def count_and_draw_objects(markers, original_image, min_area=50):
    """
    Conta e desenha os objetos detectados
    """
    count = 0
    colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), 
              (0, 255, 255), (128, 0, 128), (255, 165, 0), (0, 128, 128), (128, 128, 0)]
    
    # Desenhar bordas do watershed em vermelho
    original_image[markers == -1] = [0, 0, 255]
    
    for label in np.unique(markers):
        if label <= 1:  # Ignorar background (1) e bordas (-1 já processadas)
            continue
        
        # Criar máscara para o objeto atual
        mask = np.zeros(markers.shape, dtype="uint8")
        mask[markers == label] = 255
        
        # Encontrar contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                # Desenhar contorno
                color = colors[count % len(colors)]
                cv2.drawContours(original_image, [contour], -1, color, 2)
                
                # Adicionar número do objeto
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.putText(original_image, str(count + 1), (cx-10, cy+5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                count += 1
    
    return count

def process_image(image_path, output_path):
    """
    Processa uma imagem completa aplicando técnicas otimizadas para objetos claros e escuros
    """
    print(f"\n🔍 Processando: {image_path}")
    
    # 1. Pré-processamento
    original_img, gray, blurred = preprocess_image(image_path)
    
    # 2. Processamento separado para objetos escuros e claros
    
    # Para objetos ESCUROS (chocolates escuros, sementes escuras)
    _, thresh_dark = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    clean_dark = remove_noise(thresh_dark)
    
    # Para objetos CLAROS - abordagem melhorada com detecção de bordas
    # 1. Detectar bordas sutis (objetos brancos têm bordas muito fracas)
    edges = cv2.Canny(blurred, 30, 80)
    
    # 2. Dilatar as bordas para formar regiões
    kernel_edges = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    edges_dilated = cv2.dilate(edges, kernel_edges, iterations=2)
    
    # 3. Preencher as regiões internas
    edges_filled = cv2.morphologyEx(edges_dilated, cv2.MORPH_CLOSE, 
                                   cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)), 
                                   iterations=3)
    
    # 4. Threshold mais agressivo para objetos claros
    _, thresh_light = cv2.threshold(blurred, 220, 255, cv2.THRESH_BINARY)
    thresh_light = cv2.bitwise_not(thresh_light)  # Inverter
    
    # 5. Combinar detecção de bordas com threshold para objetos claros
    light_combined = cv2.bitwise_or(edges_filled, thresh_light)
    clean_light = remove_noise(light_combined)
    
    # Combinar as duas máscaras (escuros + claros)
    combined_mask = cv2.bitwise_or(clean_dark, clean_light)
    
    # 3. Aplicar watershed na máscara combinada
    markers = watershed_segmentation(combined_mask, original_img.copy())
    
    # 4. Contar e desenhar objetos
    count = count_and_draw_objects(markers, original_img)
    
    # 5. Adicionar texto com contagem total
    cv2.putText(original_img, f'Objetos detectados: {count}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(original_img, f'Objetos detectados: {count}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1)
    
    # 6. Salvar resultado e máscaras para debug
    cv2.imwrite(output_path, original_img)
    cv2.imwrite(output_path.replace('_resultado', '_mask_combined'), combined_mask)
    cv2.imwrite(output_path.replace('_resultado', '_mask_dark'), clean_dark)
    cv2.imwrite(output_path.replace('_resultado', '_mask_light'), clean_light)
    
    print(f"✅ Resultado salvo em: {output_path}")
    print(f"📊 Total de objetos encontrados: {count}")
    
    return original_img, count

# Programa principal
if __name__ == "__main__":
    print("🚀 Iniciando contagem avançada de objetos...")
    
    # Lista de imagens para processar
    images_to_process = [
        ('images/chocolates.jpg', 'images/chocolates_resultado.jpg'),
        ('images/seeds.png', 'images/seeds_resultado.png')
    ]
    
    results = []
    
    for input_path, output_path in images_to_process:
        try:
            result_img, count = process_image(input_path, output_path)
            results.append((input_path, result_img, count))
            
            # Exibir resultado
            cv2.imshow(f'Resultado - {input_path}', result_img)
            
        except Exception as e:
            print(f"❌ Erro ao processar {input_path}: {str(e)}")
    
    # Exibir todas as imagens
    if results:
        print(f"\n📈 Resumo dos resultados:")
        for img_path, _, count in results:
            print(f"  • {img_path}: {count} objetos")
        
        print("\n💡 Pressione qualquer tecla para fechar as janelas...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        print("✨ Processamento concluído!")
    else:
        print("❌ Nenhuma imagem foi processada com sucesso.")
