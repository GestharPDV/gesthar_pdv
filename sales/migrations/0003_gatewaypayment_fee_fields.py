from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0002_gatewaypayment'),
    ]

    operations = [
        migrations.AddField(
            model_name='gatewaypayment',
            name='fee_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Taxa do Gateway'),
        ),
        migrations.AddField(
            model_name='gatewaypayment',
            name='payment_method_id',
            field=models.CharField(blank=True, max_length=40, verbose_name='Bandeira'),
        ),
        migrations.AddField(
            model_name='gatewaypayment',
            name='installments',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Parcelas'),
        ),
        migrations.AddField(
            model_name='gatewaypayment',
            name='buyer_pays_fee',
            field=models.BooleanField(blank=True, null=True, verbose_name='Cliente paga taxa'),
        ),
    ]
