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
    words = color_name.upper().split()
    return "".join([word[0] for word in words])


def generate_size_part(size_code):
    """
    Gera a parte do SKU referente ao tamanho.
    Regra: Apenas o código em maiúsculas.
    """
    return size_code.upper()


def generate_sku(variation):
    """
    Orquestra a criação do SKU final para um objeto ProductVariation.
    """
    product_part = generate_product_part(variation.product.name)
    color_part = _generate_color_part(variation.color.name)
    size_part = generate_size_part(variation.size.code)

    return f"{product_part}-{color_part}-{size_part}"
