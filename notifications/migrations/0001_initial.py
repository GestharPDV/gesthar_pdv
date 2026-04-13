from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customer', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=500, verbose_name='Mensagem')),
                ('milestone_key', models.CharField(
                    help_text="Ex: '35_weeks', 'post_partum'",
                    max_length=50,
                    verbose_name='Marco',
                )),
                ('is_read', models.BooleanField(default=False, verbose_name='Lida')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criada em')),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to='customer.customer',
                    verbose_name='Cliente',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Destinatário',
                )),
            ],
            options={
                'verbose_name': 'Notificação',
                'verbose_name_plural': 'Notificações',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='notification',
            constraint=models.UniqueConstraint(
                fields=['user', 'customer', 'milestone_key'],
                name='unique_notification_per_user_customer_milestone',
            ),
        ),
    ]
