# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-03-20 19:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AUDUSD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeframe', models.IntegerField(blank=True, null=True, verbose_name='timeframe')),
                ('open', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('high', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('low', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('close', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('volume', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='price')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EURUSD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeframe', models.IntegerField(blank=True, null=True, verbose_name='timeframe')),
                ('open', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('high', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('low', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('close', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('volume', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='price')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GBPUSD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeframe', models.IntegerField(blank=True, null=True, verbose_name='timeframe')),
                ('open', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('high', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('low', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('close', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('volume', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='price')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NZDUSD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeframe', models.IntegerField(blank=True, null=True, verbose_name='timeframe')),
                ('open', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('high', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('low', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('close', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('volume', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='price')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='USDCAD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeframe', models.IntegerField(blank=True, null=True, verbose_name='timeframe')),
                ('open', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('high', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('low', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('close', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('volume', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='price')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='USDCHF',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeframe', models.IntegerField(blank=True, null=True, verbose_name='timeframe')),
                ('open', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('high', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('low', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('close', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('volume', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='price')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='USDJPY',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeframe', models.IntegerField(blank=True, null=True, verbose_name='timeframe')),
                ('open', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('high', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('low', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('close', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('volume', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='price')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='XAUUSD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeframe', models.IntegerField(blank=True, null=True, verbose_name='timeframe')),
                ('open', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('high', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('low', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('close', models.DecimalField(decimal_places=5, max_digits=8, verbose_name='price')),
                ('volume', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='price')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
