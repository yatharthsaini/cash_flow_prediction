# Generated by Django 4.2.9 on 2024-03-04 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cash_flow', '0003_disbursal_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='loandetail',
            name='age',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='nbfceligibilitycashflowhead',
            name='max_age',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='nbfceligibilitycashflowhead',
            name='min_age',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='nbfceligibilitycashflowhead',
            name='should_assign',
            field=models.BooleanField(default=True),
        ),
    ]
