def generate_product_part(product_name):
    """
    Gera a parte do SKU referente ao produto de forma robusta.
    Regra: 3 letras da 1ª palavra, 2 da 2ª, e 1 de todas as subsequentes.
    """
    words = product_name.upper().split()
    parts = []

    if len(words) >= 1:
        parts.append(words[0][:3])

    if len(words) >= 2:
        parts.append(words[1][:2])

    if len(words) >= 3:
        for word in words[2:]:
            parts.append(word[0])

    return "".join(parts)


def _generate_color_part(color_name):
    """
    Gera a parte do SKU referente à cor.
    Regra: Primeira letra de cada palavra.
    """
    name = color_name.upper()
    if name == "N/A":
        return "NA"
    
    words = color_name.upper().split()
    return "".join([word[0] for word in words])


def generate_size_part(size_name):
    """
    Gera a parte do SKU referente ao tamanho.
    Regra: Apenas o código em maiúsculas.
    """
    name = size_name.upper()
    if name == "N/A":
        return "UN"
    
    return size_name.upper()


def generate_sku(variation):
    """
    Cria SKU final para um objeto ProductVariation.
    """
    product_part = generate_product_part(variation.product.name)
    color_part = _generate_color_part(variation.color.name)
    size_part = generate_size_part(variation.size.name)

    return f"{product_part}-{color_part}-{size_part}"
