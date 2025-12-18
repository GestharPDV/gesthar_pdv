# Generated manually

from django.db import migrations, models
import customer.validators


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        # Renomear campo cpf para cpf_cnpj
        migrations.RenameField(
            model_name='customer',
            old_name='cpf',
            new_name='cpf_cnpj',
        ),
        # Alterar propriedades do campo cpf_cnpj
        migrations.AlterField(
            model_name='customer',
            name='cpf_cnpj',
            field=models.CharField(
                help_text='Informe CPF (11 dígitos) ou CNPJ (14 dígitos)',
                max_length=18,
                unique=True,
                validators=[customer.validators.validate_cpf_cnpj],
                verbose_name='CPF/CNPJ'
            ),
        ),
        # Adicionar campo size_preferences
        migrations.AddField(
            model_name='customer',
            name='size_preferences',
            field=models.CharField(
                blank=True,
                help_text='Ex: P, M, G',
                max_length=100,
                null=True,
                verbose_name='Preferências de Tamanho'
            ),
        ),
        # Atualizar verbose_name dos campos existentes
        migrations.AlterField(
            model_name='customer',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Nome Completo'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='birth_date',
            field=models.DateField(blank=True, null=True, verbose_name='Data de Nascimento'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='E-mail'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Telefone/WhatsApp'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='note',
            field=models.TextField(blank=True, null=True, verbose_name='Observações'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Cadastrado em'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Atualizado em'),
        ),
        # Atualizar verbose_name dos campos de Address
        migrations.AlterField(
            model_name='address',
            name='cep',
            field=models.CharField(max_length=10, verbose_name='CEP'),
        ),
        migrations.AlterField(
            model_name='address',
            name='state',
            field=models.CharField(max_length=100, verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='address',
            name='city',
            field=models.CharField(max_length=100, verbose_name='Cidade'),
        ),
        migrations.AlterField(
            model_name='address',
            name='neighborhood',
            field=models.CharField(max_length=100, verbose_name='Bairro'),
        ),
        migrations.AlterField(
            model_name='address',
            name='street',
            field=models.CharField(max_length=255, verbose_name='Rua'),
        ),
        migrations.AlterField(
            model_name='address',
            name='number',
            field=models.CharField(max_length=20, verbose_name='Número'),
        ),
        migrations.AlterField(
            model_name='address',
            name='complement',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Complemento'),
        ),
        migrations.AlterField(
            model_name='address',
            name='customer',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='addresses',
                to='customer.customer',
                verbose_name='Cliente'
            ),
        ),
    ]

