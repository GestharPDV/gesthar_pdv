# Migration corretiva para adicionar colunas faltantes
# Gerado manualmente para corrigir inconsistências do banco

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_remove_size_code_alter_size_name'),
    ]

    operations = [
        # Adicionar is_active em Supplier (se não existir)
        migrations.AddField(
            model_name='supplier',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Ativo'),
        ),
    ]

