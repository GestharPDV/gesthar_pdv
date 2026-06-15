from django.core.management.base import BaseCommand
from catalog.models import CatalogConfig


class Command(BaseCommand):
    help = 'Configura o CatalogConfig com dados padrão da loja'

    def handle(self, *args, **options):
        config, created = CatalogConfig.objects.get_or_create(
            pk=1,
            defaults={
                'company_name': 'Linda Gestante',
                'whatsapp_number': '5586989071613',
                'instagram_url': 'https://instagram.com/lojalindagestante',
                'catalog_visible': True,
            }
        )
        
        if not created:
            # Atualizar dados se já existir
            config.whatsapp_number = '5586989071613'
            config.instagram_url = 'https://instagram.com/lojalindagestante'
            config.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'CatalogConfig configurado com sucesso!\n'
                f'  - Empresa: {config.company_name}\n'
                f'  - WhatsApp: {config.whatsapp_number}\n'
                f'  - Instagram: {config.instagram_url}'
            )
        )
