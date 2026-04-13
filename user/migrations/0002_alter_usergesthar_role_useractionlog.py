from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usergesthar',
            name='role',
            field=models.CharField(
                choices=[('ADMIN', 'Administrador'), ('VENDEDOR', 'Vendedor')],
                default='VENDEDOR',
                max_length=20,
                verbose_name='Perfil de Acesso',
            ),
        ),
        migrations.CreateModel(
            name='UserActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=255, verbose_name='Ação')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')),
                ('user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='action_logs',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário',
                )),
            ],
            options={
                'verbose_name': 'Log de Atividade',
                'verbose_name_plural': 'Logs de Atividade',
                'ordering': ['-timestamp'],
            },
        ),
    ]
