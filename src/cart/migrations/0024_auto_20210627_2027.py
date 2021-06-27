# Generated by Django 3.1 on 2021-06-27 20:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0023_auto_20210624_2342'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='available_colours',
        ),
        migrations.RemoveField(
            model_name='product',
            name='available_sizes',
        ),
        migrations.RemoveField(
            model_name='product',
            name='datasheet_id',
        ),
        migrations.AddField(
            model_name='datasheet',
            name='product_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='datasheet_line_ids', to='cart.product'),
        ),
        migrations.AlterField(
            model_name='payupayment',
            name='name',
            field=models.CharField(blank=True, default='PAYU-PAYMENT-00216', max_length=255, null=True),
        ),
    ]