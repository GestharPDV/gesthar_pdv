"""
Pacote de testes do módulo product.

Os testes estão organizados em arquivos separados para melhor manutenção:
- test_models.py: Testes dos modelos (Category, Color, Size, Supplier, Product, ProductVariation, ProductSupplier)
- test_managers.py: Testes dos managers customizados (ProductQuerySet, ActiveProductVariationManager)
- test_services.py: Testes dos serviços (create_category, create_supplier, etc)
- test_forms.py: Testes dos formulários e formsets
- test_views.py: Testes das views (CRUD e AJAX)
- test_utils.py: Testes das funções utilitárias (generate_sku, standardize_name)
- test_integration.py: Testes de integração e fluxos completos
"""
