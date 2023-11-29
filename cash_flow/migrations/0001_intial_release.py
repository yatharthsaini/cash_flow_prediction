# Generated by Django 4.2.7 on 2023-11-29 06:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NbfcAndDateWiseCashFlowData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('due_date', models.DateField()),
                ('predicted_cash_inflow', models.FloatField(null=True)),
                ('collection', models.FloatField(null=True)),
                ('carry_forward', models.FloatField(null=True)),
                ('available_cash_flow', models.FloatField(null=True)),
                ('loan_booked', models.FloatField(null=True)),
                ('variance', models.FloatField(null=True)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='NbfcWiseCollectionData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nbfc', models.CharField(max_length=200)),
                ('collection_json', models.JSONField(null=True)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='UserPermissionModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_id', models.BigIntegerField()),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('role', models.CharField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserRatioData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True)),
                ('old_percentage', models.FloatField()),
                ('new_percentage', models.FloatField()),
                ('nbfc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cash_flow.nbfcanddatewisecashflowdata')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProjectionCollectionData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('due_date', models.DateField()),
                ('collection_date', models.DateField()),
                ('amount', models.FloatField()),
                ('nbfc', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='cash_flow.nbfcwisecollectiondata')),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddField(
            model_name='nbfcanddatewisecashflowdata',
            name='nbfc',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cash_flow.nbfcwisecollectiondata'),
        ),
        migrations.CreateModel(
            name='HoldCashData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True)),
                ('hold_cash', models.FloatField()),
                ('nbfc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cash_flow.nbfcanddatewisecashflowdata')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CapitalInflowData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True)),
                ('capital_inflow', models.FloatField()),
                ('nbfc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cash_flow.nbfcanddatewisecashflowdata')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
